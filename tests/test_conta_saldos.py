from datetime import datetime, date

from app import db
from app.models import (
    Category,
    Conta,
    MovimentacaoInvestimento,
    PaymentMethod,
    TipoConta,
    TipoInvestimento,
    Transaction,
    User,
    Investimento,
)


def _base_entities(username="carol", email="carol@example.com"):
    user = User(username=username, email=email)
    user.set_password("123456")
    db.session.add(user)
    db.session.flush()

    tipo_conta = TipoConta(nome="Banco", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo_conta)
    db.session.flush()

    conta = Conta(nome="Conta", tipo_id=tipo_conta.id, saldo_inicial=1000.0, saldo_atual=1000.0, user_id=user.id)
    db.session.add(conta)

    category_receita = Category(name="Salario", type="receita", exclusive=True)
    category_despesa = Category(name="Mercado", type="despesa", exclusive=True)
    payment = PaymentMethod(name="Pix", is_active=True)
    db.session.add_all([category_receita, category_despesa, payment])

    tipo_inv = TipoInvestimento(nome="CDB", descricao="CDB", ativo=True, user_id=user.id)
    db.session.add(tipo_inv)
    db.session.flush()

    investimento = Investimento(tipo_investimento_id=tipo_inv.id, data_abertura=date(2025, 1, 1))
    db.session.add(investimento)
    db.session.flush()

    return user, conta, category_receita, category_despesa, payment, investimento


def test_atualizar_saldo_investimento_rules(app_ctx):
    _, conta, *_ = _base_entities()
    db.session.commit()

    conta.atualizar_saldo_investimento("aplicacao", 100.0, "adicionar")
    assert conta.saldo_atual == 900.0

    conta.atualizar_saldo_investimento("resgate", 50.0, "adicionar")
    assert conta.saldo_atual == 950.0

    conta.atualizar_saldo_investimento("rendimento", 500.0, "adicionar")
    assert conta.saldo_atual == 950.0

    conta.atualizar_saldo_investimento("aplicacao", 2000.0, "adicionar")
    assert conta.saldo_atual == 0.0


def test_recalcular_saldos_considers_paid_transactions_and_investments(app_ctx):
    user, conta, cat_rec, cat_desp, payment, investimento = _base_entities("dave", "dave@example.com")
    db.session.flush()

    db.session.add_all(
        [
            Transaction(
                user_id=user.id,
                category_id=cat_rec.id,
                expense_id=None,
                payment_method_id=payment.id,
                conta_id=conta.id,
                date=datetime(2025, 1, 2),
                payment_date=datetime(2025, 1, 2),
                amount=300.0,
                discount=0.0,
                type="receita",
                paid=True,
            ),
            Transaction(
                user_id=user.id,
                category_id=cat_desp.id,
                expense_id=None,
                payment_method_id=payment.id,
                conta_id=conta.id,
                date=datetime(2025, 1, 3),
                due_date=datetime(2025, 1, 3),
                payment_date=datetime(2025, 1, 3),
                amount=100.0,
                discount=10.0,
                type="despesa",
                paid=True,
            ),
            Transaction(
                user_id=user.id,
                category_id=cat_desp.id,
                expense_id=None,
                payment_method_id=payment.id,
                conta_id=conta.id,
                date=datetime(2025, 1, 4),
                due_date=datetime(2025, 1, 4),
                payment_date=datetime(2025, 1, 4),
                amount=999.0,
                discount=0.0,
                type="despesa",
                paid=False,
            ),
        ]
    )

    db.session.add_all(
        [
            MovimentacaoInvestimento(
                investimento_id=investimento.id,
                data_movimentacao=date(2025, 1, 10),
                tipo_movimentacao="aplicacao",
                valor=200.0,
                saldo_anterior=0.0,
                saldo_atual=200.0,
                user_id=user.id,
                conta_id=conta.id,
            ),
            MovimentacaoInvestimento(
                investimento_id=investimento.id,
                data_movimentacao=date(2025, 1, 20),
                tipo_movimentacao="resgate",
                valor=50.0,
                saldo_anterior=200.0,
                saldo_atual=150.0,
                user_id=user.id,
                conta_id=conta.id,
            ),
        ]
    )
    db.session.commit()

    Conta.recalcular_saldos(conta.id)
    db.session.refresh(conta)

    assert conta.saldo_atual == 1060.0
