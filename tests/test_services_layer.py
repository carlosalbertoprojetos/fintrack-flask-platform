from datetime import date, datetime
from decimal import Decimal

import pytest

from app import db
from app.models import (
    Category,
    Conta,
    LedgerEntry,
    MonthlyClosure,
    MovimentacaoInvestimento,
    PaymentMethod,
    TipoConta,
    TipoInvestimento,
    Transaction,
    User,
)
from services.ai_classification_service import AIClassificationService
from services.anomaly_detection_service import AnomalyDetectionService
from services.closure_service import ClosureService
from services.data_quality_service import DataQualityService
from services.investment_service import InvestmentService
from services.ledger_service import LedgerService
from services.projection_service import ProjectionService
from services.report_service import ReportService
from services.transaction_service import TransactionService


def _seed_user_and_accounts(username: str, email: str):
    user = User(username=username, email=email)
    user.set_password("secret123")
    db.session.add(user)
    db.session.flush()

    tipo = TipoConta(nome=f"Banco-{username}", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo)
    db.session.flush()

    conta_1 = Conta(
        nome=f"Conta-{username}-1",
        tipo_id=tipo.id,
        saldo_inicial=1000.0,
        saldo_atual=1000.0,
        user_id=user.id,
    )
    conta_2 = Conta(
        nome=f"Conta-{username}-2",
        tipo_id=tipo.id,
        saldo_inicial=1000.0,
        saldo_atual=1000.0,
        user_id=user.id,
    )
    db.session.add_all([conta_1, conta_2])

    cat_receita = Category(name=f"Receita-{username}", type="receita", exclusive=True, user_id=user.id)
    cat_despesa = Category(name=f"Despesa-{username}", type="despesa", exclusive=True, user_id=user.id)
    pagamento = PaymentMethod(name=f"Pix-{username}", is_active=True, user_id=user.id)
    tipo_inv = TipoInvestimento(nome=f"CDB-{username}", descricao="Renda fixa", ativo=True, user_id=user.id)
    db.session.add_all([cat_receita, cat_despesa, pagamento, tipo_inv])
    db.session.commit()

    return user, conta_1, conta_2, cat_receita, cat_despesa, pagamento, tipo_inv


def _tx_payload(conta_id, category_id, payment_method_id, tx_type="despesa", amount=100.0, discount=0.0, paid=True):
    when = datetime(2025, 1, 15, 12, 0, 0)
    return {
        "type": tx_type,
        "date": when,
        "due_date": when,
        "payment_date": when,
        "amount": amount,
        "discount": discount,
        "paid": paid,
        "category_id": category_id,
        "expense_id": None,
        "description": "Lancamento teste",
        "payment_method_id": payment_method_id,
        "recurrence": "none",
        "details": "detalhes",
        "notes": "notas",
        "conta_id": conta_id,
    }


def test_ledger_integrity_and_tamper_detection(app_ctx):
    user, conta_1, _, _, _, _, _ = _seed_user_and_accounts("svc-ledger", "svc-ledger@example.com")

    LedgerService.append_entry(
        user_id=user.id,
        account_id=conta_1.id,
        reference_type="manual",
        reference_id=1,
        amount=Decimal("10.00"),
    )
    LedgerService.append_entry(
        user_id=user.id,
        account_id=conta_1.id,
        reference_type="manual",
        reference_id=2,
        amount=Decimal("-3.00"),
    )
    db.session.commit()

    ok, _ = LedgerService.validate_integrity(user_id=user.id, account_id=conta_1.id)
    assert ok is True

    first = LedgerEntry.query.filter_by(user_id=user.id, account_id=conta_1.id).order_by(LedgerEntry.id.asc()).first()
    first.current_hash = "tampered-hash"
    db.session.commit()

    ok, msg = LedgerService.validate_integrity(user_id=user.id, account_id=conta_1.id)
    assert ok is False
    assert "Invalid current hash" in msg


def test_backfill_and_report_summary(app_ctx):
    user, conta_1, _, cat_receita, cat_despesa, pagamento, _ = _seed_user_and_accounts(
        "svc-backfill",
        "svc-backfill@example.com",
    )

    db.session.add_all(
        [
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_receita.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 1, 2),
                payment_date=datetime(2025, 1, 2),
                amount=300.0,
                discount=0.0,
                type="receita",
                paid=True,
            ),
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_despesa.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 1, 3),
                due_date=datetime(2025, 1, 3),
                payment_date=datetime(2025, 1, 3),
                amount=100.0,
                discount=10.0,
                type="despesa",
                paid=True,
            ),
        ]
    )
    db.session.commit()

    LedgerService.backfill_account_ledger(user_id=user.id, account_id=conta_1.id)
    assert LedgerEntry.query.filter_by(user_id=user.id, account_id=conta_1.id).count() == 2

    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 1210.0

    summary = ReportService.account_period_summary(user_id=user.id, account_id=conta_1.id, year=2025, month=1)
    assert float(summary["receitas"]) == 300.0
    assert float(summary["despesas"]) == 90.0
    assert float(summary["balance"]) == 210.0


def test_monthly_closure_lock_unlock_and_consistency(app_ctx):
    user, conta_1, _, _, _, _, _ = _seed_user_and_accounts("svc-close", "svc-close@example.com")

    LedgerService.append_entry(
        user_id=user.id,
        account_id=conta_1.id,
        reference_type="jan-receita",
        reference_id=1,
        amount=100.0,
        created_at=datetime(2025, 1, 10),
    )
    LedgerService.append_entry(
        user_id=user.id,
        account_id=conta_1.id,
        reference_type="jan-despesa",
        reference_id=2,
        amount=-40.0,
        created_at=datetime(2025, 1, 20),
    )
    db.session.commit()

    closure = ClosureService.close_month(user_id=user.id, account_id=conta_1.id, year=2025, month=1)
    assert isinstance(closure, MonthlyClosure)
    assert closure.locked is True
    assert float(closure.total_receitas) == 100.0
    assert float(closure.total_despesas) == 40.0
    assert closure.ledger_hash_snapshot

    with pytest.raises(ValueError, match="Periodo fechado"):
        ClosureService.ensure_period_open(user_id=user.id, account_id=conta_1.id, date_value=date(2025, 1, 15))

    dq = DataQualityService.closure_consistency(user_id=user.id, account_id=conta_1.id, year=2025, month=1)
    assert dq["ok"] is True

    ClosureService.unlock_month(user_id=user.id, account_id=conta_1.id, year=2025, month=1)
    ClosureService.ensure_period_open(user_id=user.id, account_id=conta_1.id, date_value=date(2025, 1, 15))

    with pytest.raises(ValueError, match="Data invalida"):
        ClosureService.ensure_period_open(user_id=user.id, account_id=conta_1.id, date_value="2025-01-15")


def test_transaction_service_create_update_delete_and_transfer(app_ctx):
    user, conta_1, conta_2, cat_receita, cat_despesa, pagamento, _ = _seed_user_and_accounts(
        "svc-tx",
        "svc-tx@example.com",
    )

    tx = TransactionService.create_transaction(
        user_id=user.id,
        payload=_tx_payload(
            conta_id=conta_1.id,
            category_id=cat_despesa.id,
            payment_method_id=pagamento.id,
            tx_type="despesa",
            amount=120.0,
            discount=20.0,
            paid=True,
        ),
    )
    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 900.0

    update_payload = _tx_payload(
        conta_id=conta_1.id,
        category_id=cat_despesa.id,
        payment_method_id=pagamento.id,
        tx_type="despesa",
        amount=200.0,
        discount=0.0,
        paid=True,
    )
    TransactionService.update_transaction(user_id=user.id, tx=tx, payload=update_payload)
    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 800.0

    transfer_payload = _tx_payload(
        conta_id=conta_2.id,
        category_id=cat_receita.id,
        payment_method_id=pagamento.id,
        tx_type="receita",
        amount=150.0,
        discount=0.0,
        paid=True,
    )
    TransactionService.update_transaction(user_id=user.id, tx=tx, payload=transfer_payload)
    db.session.refresh(conta_1)
    db.session.refresh(conta_2)
    assert conta_1.saldo_atual == 1000.0
    assert conta_2.saldo_atual == 1150.0

    TransactionService.delete_transaction(user_id=user.id, tx=tx)
    db.session.refresh(conta_2)
    assert conta_2.saldo_atual == 1000.0

    with pytest.raises(ValueError, match="Conta obrigatoria"):
        TransactionService.create_transaction(user_id=user.id, payload={"type": "receita"})


def test_transaction_service_rejects_foreign_user(app_ctx):
    user_a, conta_a, _, _, cat_despesa, pagamento, _ = _seed_user_and_accounts("svc-own-a", "svc-own-a@example.com")
    user_b, _, _, _, _, _, _ = _seed_user_and_accounts("svc-own-b", "svc-own-b@example.com")

    tx = TransactionService.create_transaction(
        user_id=user_a.id,
        payload=_tx_payload(
            conta_id=conta_a.id,
            category_id=cat_despesa.id,
            payment_method_id=pagamento.id,
        ),
    )

    with pytest.raises(ValueError, match="nao pertence"):
        TransactionService.update_transaction(
            user_id=user_b.id,
            tx=tx,
            payload=_tx_payload(conta_id=conta_a.id, category_id=cat_despesa.id, payment_method_id=pagamento.id),
        )

    with pytest.raises(ValueError, match="nao pertence"):
        TransactionService.delete_transaction(user_id=user_b.id, tx=tx)




def test_transaction_service_rejects_foreign_lookup_ids(app_ctx):
    user_a, conta_a, _, _, cat_despesa_a, pagamento_a, _ = _seed_user_and_accounts(
        "svc-scope-a",
        "svc-scope-a@example.com",
    )
    user_b, _, _, _, cat_despesa_b, pagamento_b, _ = _seed_user_and_accounts(
        "svc-scope-b",
        "svc-scope-b@example.com",
    )

    with pytest.raises(ValueError, match="Categoria nao pertence"):
        TransactionService.create_transaction(
            user_id=user_a.id,
            payload=_tx_payload(
                conta_id=conta_a.id,
                category_id=cat_despesa_b.id,
                payment_method_id=pagamento_a.id,
            ),
        )

    with pytest.raises(ValueError, match="Forma de pagamento nao pertence"):
        TransactionService.create_transaction(
            user_id=user_a.id,
            payload=_tx_payload(
                conta_id=conta_a.id,
                category_id=cat_despesa_a.id,
                payment_method_id=pagamento_b.id,
            ),
        )

def test_investment_service_lifecycle_and_permissions(app_ctx):
    user, conta_1, _, _, _, _, tipo_inv = _seed_user_and_accounts("svc-inv", "svc-inv@example.com")
    other, _, _, _, _, _, _ = _seed_user_and_accounts("svc-inv-other", "svc-inv-other@example.com")

    inv = InvestmentService.create_investment(
        user_id=user.id,
        tipo_investimento_id=tipo_inv.id,
        conta_id=conta_1.id,
    )
    assert inv.id is not None
    assert MovimentacaoInvestimento.query.filter_by(investimento_id=inv.id).count() == 1

    mov = InvestmentService.create_movement(
        user_id=user.id,
        investimento=inv,
        conta_id=conta_1.id,
        data_movimentacao=date(2025, 1, 10),
        tipo_movimentacao="aplicacao",
        valor=100.0,
        observacoes="aporte",
    )
    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 900.0

    InvestmentService.update_movement(
        user_id=user.id,
        mov=mov,
        data_movimentacao=date(2025, 1, 11),
        valor=150.0,
        observacoes="aporte ajustado",
    )
    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 850.0

    with pytest.raises(ValueError, match="nao pertence"):
        InvestmentService.update_movement(
            user_id=other.id,
            mov=mov,
            data_movimentacao=date(2025, 1, 11),
            valor=150.0,
            observacoes="x",
        )

    InvestmentService.delete_movement(user_id=user.id, mov=mov)
    db.session.refresh(conta_1)
    assert conta_1.saldo_atual == 1000.0
    assert InvestmentService.recalculate_movement_balances(investimento_id=999999) is False

    remaining = MovimentacaoInvestimento.query.filter_by(investimento_id=inv.id).first()
    with pytest.raises(ValueError, match="nao pertence"):
        InvestmentService.delete_movement(user_id=other.id, mov=remaining)


def test_data_quality_and_projection_and_simulation(app_ctx, tmp_path):
    user, conta_1, _, cat_receita, cat_despesa, pagamento, _ = _seed_user_and_accounts(
        "svc-ai",
        "svc-ai@example.com",
    )

    # AI classification
    AIClassificationService.MODEL_DIR = tmp_path / "models"
    assert AIClassificationService.classify(user_id=user.id, text="salario mensal") is None

    db.session.add_all(
        [
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_receita.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 1, 5),
                payment_date=datetime(2025, 1, 5),
                amount=100.0,
                discount=0.0,
                type="receita",
                paid=True,
                description="salario mensal",
            ),
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_despesa.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 2, 5),
                payment_date=datetime(2025, 2, 5),
                amount=50.0,
                discount=0.0,
                type="despesa",
                paid=True,
                description="mercado casa",
            ),
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_receita.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 3, 5),
                payment_date=datetime(2025, 3, 5),
                amount=300.0,
                discount=0.0,
                type="receita",
                paid=True,
                description="bonus salario",
            ),
        ]
    )
    db.session.commit()

    metadata = AIClassificationService.train_user_model(user_id=user.id)
    assert metadata.model_type == "transaction_classifier"
    predicted = AIClassificationService.classify(user_id=user.id, text="bonus salario")
    assert predicted in {cat_receita.id, cat_despesa.id}

    # Anomaly detection branches
    assert AnomalyDetectionService.detect_user_transaction_anomalies(user_id=user.id, threshold=99) == []
    db.session.add_all(
        [
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_receita.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 4, 1),
                payment_date=datetime(2025, 4, 1),
                amount=101.0,
                discount=0.0,
                type="receita",
                paid=True,
            ),
            Transaction(
                user_id=user.id,
                conta_id=conta_1.id,
                category_id=cat_receita.id,
                payment_method_id=pagamento.id,
                date=datetime(2025, 5, 1),
                payment_date=datetime(2025, 5, 1),
                amount=10000.0,
                discount=0.0,
                type="receita",
                paid=True,
            ),
        ]
    )
    db.session.commit()
    anomalies = AnomalyDetectionService.detect_user_transaction_anomalies(user_id=user.id, threshold=1.8)
    assert any(a["amount"] == 10000.0 for a in anomalies)

    # Projection + health score
    projection = ProjectionService.project_next_month(user_id=user.id, account_id=conta_1.id, lookback_months=3)
    assert "projected_balance" in projection
    assert projection["lookback_months"] == 3
    assert 0.0 <= projection["confidence"] <= 1.0

    health = ProjectionService.financial_health_score(user_id=user.id, account_id=conta_1.id)
    assert health["status"] in {"healthy", "stable", "attention", "critical", "neutral"}
    assert 0 <= health["score"] <= 100

    # Simulation isolation
    session = ProjectionService.start_simulation(user_id=user.id, account_id=conta_1.id, name="cenario")
    ProjectionService.simulate_monthly_change(simulation_session_id=session.id, amount=50.0, reference_id=1)
    sim_balance = ProjectionService.simulation_balance(simulation_session_id=session.id)
    assert float(sim_balance) >= 1050.0

    ok, _ = LedgerService.validate_simulation_integrity(simulation_session_id=session.id)
    assert ok is True

    LedgerService.close_simulation_session(simulation_session_id=session.id)
    with pytest.raises(ValueError, match="nao esta ativa"):
        ProjectionService.simulate_monthly_change(simulation_session_id=session.id, amount=10.0)

    with pytest.raises(ValueError, match="nao encontrada"):
        ProjectionService.simulation_balance(simulation_session_id=999999)

    # Data quality
    bad_tx = Transaction(
        user_id=user.id,
        conta_id=None,
        category_id=cat_receita.id,
        payment_method_id=pagamento.id,
        date=datetime(2025, 6, 1),
        payment_date=None,
        amount=0.0,
        discount=0.0,
        type="foo",
        paid=True,
    )
    db.session.add(bad_tx)
    db.session.commit()

    issues = DataQualityService.transaction_issues(user_id=user.id)
    issue_types = {i["type"] for i in issues if i["transaction_id"] == bad_tx.id}
    assert "invalid_amount" in issue_types
    assert "missing_account" in issue_types
    assert "paid_without_payment_date" in issue_types
    assert "invalid_type" in issue_types

    report = DataQualityService.ledger_integrity_report(user_id=user.id, account_id=conta_1.id)
    assert "ok" in report and "entries" in report

    missing = DataQualityService.closure_consistency(user_id=user.id, account_id=conta_1.id, year=2025, month=12)
    assert missing["ok"] is False
    assert missing["message"] == "closure_not_found"


def test_additional_service_branches_for_full_coverage(app_ctx, tmp_path, monkeypatch):
    user, conta_1, _, cat_receita, cat_despesa, pagamento, tipo_inv = _seed_user_and_accounts(
        "svc-branches",
        "svc-branches@example.com",
    )

    # TransactionService._effective_date fallback branch
    tx_no_dates = Transaction(
        user_id=user.id,
        conta_id=conta_1.id,
        category_id=cat_receita.id,
        payment_method_id=pagamento.id,
        date=None,
        due_date=None,
        payment_date=None,
        amount=10.0,
        discount=0.0,
        type="receita",
        paid=False,
    )
    assert isinstance(TransactionService._effective_date(tx_no_dates), datetime)

    # AI classify with model but no matching tokens -> no scores path
    AIClassificationService.MODEL_DIR = tmp_path / "models-2"
    db.session.add(
        Transaction(
            user_id=user.id,
            conta_id=conta_1.id,
            category_id=cat_receita.id,
            payment_method_id=pagamento.id,
            date=datetime(2025, 7, 1),
            payment_date=datetime(2025, 7, 1),
            amount=100.0,
            discount=0.0,
            type="receita",
            paid=True,
            description="salario",
        )
    )
    db.session.commit()
    AIClassificationService.train_user_model(user_id=user.id)
    assert AIClassificationService.classify(user_id=user.id, text="token-inexistente") is None

    # Anomaly sigma==0 branch
    user2, conta2, _, cat2, _, pay2, _ = _seed_user_and_accounts("svc-sigma", "svc-sigma@example.com")
    for i in range(5):
        db.session.add(
            Transaction(
                user_id=user2.id,
                conta_id=conta2.id,
                category_id=cat2.id,
                payment_method_id=pay2.id,
                date=datetime(2025, 1, i + 1),
                payment_date=datetime(2025, 1, i + 1),
                amount=50.0,
                discount=0.0,
                type="receita",
                paid=True,
            )
        )
    db.session.commit()
    assert AnomalyDetectionService.detect_user_transaction_anomalies(user_id=user2.id) == []

    # Projection branches: empty series + neutral/critical status
    user3, conta3, _, cat3, _, pay3, _ = _seed_user_and_accounts("svc-proj", "svc-proj@example.com")
    monkeypatch.setattr(ProjectionService, "_cashflow_points", lambda **kwargs: [])
    assert ProjectionService.project_next_month(user_id=user3.id)["projected_balance"] == 0.0
    assert ProjectionService.financial_health_score(user_id=user3.id)["status"] == "neutral"

    # restore real method behavior
    monkeypatch.undo()

    # force critical branch
    db.session.add_all(
        [
            Transaction(
                user_id=user3.id,
                conta_id=conta3.id,
                category_id=cat3.id,
                payment_method_id=pay3.id,
                date=datetime(2025, 1, 1),
                payment_date=datetime(2025, 1, 1),
                amount=10.0,
                discount=0.0,
                type="despesa",
                paid=True,
            ),
            Transaction(
                user_id=user3.id,
                conta_id=conta3.id,
                category_id=cat3.id,
                payment_method_id=pay3.id,
                date=datetime(2025, 2, 1),
                payment_date=datetime(2025, 2, 1),
                amount=20.0,
                discount=0.0,
                type="despesa",
                paid=True,
            ),
            Transaction(
                user_id=user3.id,
                conta_id=conta3.id,
                category_id=cat3.id,
                payment_method_id=pay3.id,
                date=datetime(2025, 3, 1),
                payment_date=datetime(2025, 3, 1),
                amount=30.0,
                discount=0.0,
                type="despesa",
                paid=True,
            ),
        ]
    )
    db.session.commit()
    assert ProjectionService.financial_health_score(user_id=user3.id)["status"] in {"critical", "attention", "stable"}

    # explicit branch forcing for stable / attention / critical
    monkeypatch.setattr(
        ProjectionService,
        "project_next_month",
        lambda **kwargs: {"series": [{"balance": 50}, {"balance": 40}, {"balance": 35}]},
    )
    assert ProjectionService.financial_health_score(user_id=user3.id)["status"] == "stable"

    monkeypatch.setattr(
        ProjectionService,
        "project_next_month",
        lambda **kwargs: {"series": [{"balance": -60}, {"balance": -50}, {"balance": -30}]},
    )
    assert ProjectionService.financial_health_score(user_id=user3.id)["status"] == "attention"

    monkeypatch.setattr(
        ProjectionService,
        "project_next_month",
        lambda **kwargs: {"series": [{"balance": -3000}, {"balance": -2800}, {"balance": -2500}]},
    )
    assert ProjectionService.financial_health_score(user_id=user3.id)["status"] == "critical"

    # ReportService month==12 branch
    summary_dec = ReportService.account_period_summary(user_id=user3.id, account_id=conta3.id, year=2025, month=12)
    assert summary_dec["month"] == 12

    # InvestmentService branches: resgate/rendimento
    inv = InvestmentService.create_investment(user_id=user.id, tipo_investimento_id=tipo_inv.id, conta_id=conta_1.id)
    mov_aplic = InvestmentService.create_movement(
        user_id=user.id,
        investimento=inv,
        conta_id=conta_1.id,
        data_movimentacao=date(2025, 1, 1),
        tipo_movimentacao="aplicacao",
        valor=100.0,
        observacoes="aplic",
    )
    InvestmentService.create_movement(
        user_id=user.id,
        investimento=inv,
        conta_id=conta_1.id,
        data_movimentacao=date(2025, 1, 2),
        tipo_movimentacao="resgate",
        valor=50.0,
        observacoes="resg",
    )
    mov_rend = InvestmentService.create_movement(
        user_id=user.id,
        investimento=inv,
        conta_id=conta_1.id,
        data_movimentacao=date(2025, 1, 3),
        tipo_movimentacao="rendimento",
        valor=10.0,
        observacoes="rend",
    )
    InvestmentService.recalculate_movement_balances(investimento_id=inv.id)
    assert mov_rend.tipo_movimentacao == "rendimento"
    assert mov_aplic.tipo_movimentacao == "aplicacao"

    # DataQuality month==12 end boundary branch with existing closure
    LedgerService.append_entry(
        user_id=user.id,
        account_id=conta_1.id,
        reference_type="dec-entry",
        reference_id=1,
        amount=20.0,
        created_at=datetime(2025, 12, 15, 10, 0, 0),
    )
    db.session.commit()
    ClosureService.close_month(user_id=user.id, account_id=conta_1.id, year=2025, month=12)
    dq_dec = DataQualityService.closure_consistency(user_id=user.id, account_id=conta_1.id, year=2025, month=12)
    assert "difference" in dq_dec

    # LedgerService remaining branches
    assert LedgerService.get_account_balance(user_id=user.id, account_id=999999) == Decimal("0.00")
    LedgerService.rebuild_account_balances(user_id=user.id)

    # backfill movement else branch (tipo desconhecido)
    inv_legacy = InvestmentService.create_investment(user_id=user.id, tipo_investimento_id=tipo_inv.id, conta_id=conta_1.id)
    db.session.add(
        MovimentacaoInvestimento(
            investimento_id=inv_legacy.id,
            data_movimentacao=date(2025, 2, 1),
            tipo_movimentacao="desconhecido",
            valor=12.0,
            saldo_anterior=0.0,
            saldo_atual=12.0,
            observacoes="legacy",
            user_id=user.id,
            conta_id=conta_1.id,
        )
    )
    db.session.commit()
    LedgerService.backfill_account_ledger(user_id=user.id, account_id=conta_1.id, clear_existing=False)

    sim = LedgerService.create_simulation_session(user_id=user.id, account_id=conta_1.id, name="tamper")
    entry = LedgerService.append_simulation_entry_for_session(
        simulation_session_id=sim.id,
        reference_type="x",
        reference_id=1,
        amount=10.0,
    )
    entry.previous_hash = "invalid-prev"
    db.session.commit()
    ok, msg = LedgerService.validate_simulation_integrity(simulation_session_id=sim.id)
    assert ok is False
    assert "Invalid previous hash" in msg

    sim2 = LedgerService.create_simulation_session(user_id=user.id, account_id=conta_1.id, name="tamper-current")
    entry2 = LedgerService.append_simulation_entry_for_session(
        simulation_session_id=sim2.id,
        reference_type="x",
        reference_id=1,
        amount=10.0,
    )
    entry2.current_hash = "invalid-current"
    db.session.commit()
    ok2, msg2 = LedgerService.validate_simulation_integrity(simulation_session_id=sim2.id)
    assert ok2 is False
    assert "Invalid current hash" in msg2

    with pytest.raises(ValueError, match="nao encontrada"):
        LedgerService.append_simulation_entry_for_session(
            simulation_session_id=999999,
            reference_type="x",
            reference_id=None,
            amount=1.0,
        )
    with pytest.raises(ValueError, match="nao encontrada"):
        LedgerService.close_simulation_session(simulation_session_id=999999)
