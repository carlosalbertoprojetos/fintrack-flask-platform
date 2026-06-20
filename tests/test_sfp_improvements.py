from datetime import datetime

import pytest

from app import db
from app.forms import ContaForm
from app.models import Category, Conta, Expense, PaymentMethod, TipoConta, Transaction, User
from app.routes import _create_installments
from app.utils import parse_decimal_input
from services.initial_balance_service import InitialBalanceService
from services.ledger_service import LedgerService
from conftest import login_client


def _seed(username, email):
    user = User(username=username, email=email)
    user.set_password("secret123")
    db.session.add(user)
    db.session.flush()

    tipo = TipoConta(nome="Banco", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo)
    db.session.flush()

    conta = Conta(nome="Conta Corrente", tipo_id=tipo.id, saldo_inicial=0.0, saldo_atual=0.0, user_id=user.id)
    cat_receita = Category(name="Salario", type="receita", exclusive=True, user_id=user.id)
    cat_outros = Category(name="Outros", type="receita", exclusive=False, user_id=user.id)
    payment = PaymentMethod(name="Pix", is_active=True, user_id=user.id)
    db.session.add_all([conta, cat_receita, cat_outros, payment])
    db.session.commit()

    return user, tipo, conta, cat_receita, cat_outros, payment


# --------------------------------------------------------------------------- #
# Implementacao 2 - parsing de saldo inicial com virgula
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "entrada,esperado",
    [
        ("1000,50", 1000.5),
        ("10,00", 10.0),
        ("150,75", 150.75),
        ("1.000,50", 1000.5),
        ("1.000.000,00", 1000000.0),
        ("150.75", 150.75),  # compatibilidade com ponto
        ("1000", 1000.0),
        ("R$ 2.500,90", 2500.9),
        (1234.5, 1234.5),
        ("", None),
        ("   ", None),
        (None, None),
    ],
)
def test_parse_decimal_input(entrada, esperado):
    assert parse_decimal_input(entrada) == esperado


def test_parse_decimal_input_invalid_raises():
    with pytest.raises(ValueError):
        parse_decimal_input("abc")


def test_conta_form_accepts_comma(app):
    from werkzeug.datastructures import MultiDict

    with app.test_request_context():
        user, tipo, *_ = _seed("forma", "forma@example.com")
        form = ContaForm(
            formdata=MultiDict({"nome": "Nova", "tipo_id": str(tipo.id), "saldo_inicial": "1000,50"})
        )
        form.tipo_id.choices = [(tipo.id, tipo.nome)]
        assert form.validate() is True
        assert form.saldo_inicial.data == 1000.5


# --------------------------------------------------------------------------- #
# Implementacao 1 - parcelamento
# --------------------------------------------------------------------------- #
def _base_payload(conta_id, category_id, payment_method_id, description="Compra Mercado"):
    base = datetime(2025, 1, 1)
    return {
        "type": "receita",
        "date": base,
        "due_date": None,
        "payment_date": base,
        "amount": 300.0,
        "discount": 0.0,
        "paid": True,
        "category_id": category_id,
        "expense_id": None,
        "description": description,
        "payment_method_id": payment_method_id,
        "recurrence": "none",
        "details": "detalhe",
        "notes": None,
        "conta_id": conta_id,
    }


def test_parcelamento_cria_n_transacoes_com_datas_e_descricao(app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("parc", "parc@example.com")

    criadas = _create_installments(
        user_id=user.id,
        base_payload=_base_payload(conta.id, cat_receita.id, payment.id),
        parcelas=3,
    )

    assert len(criadas) == 3

    txs = (
        Transaction.query.filter_by(user_id=user.id, conta_id=conta.id)
        .order_by(Transaction.payment_date.asc())
        .all()
    )
    assert len(txs) == 3

    # Datas: 01/01, 31/01 (+30), 02/03 (+60)
    assert txs[0].payment_date == datetime(2025, 1, 1)
    assert txs[1].payment_date == datetime(2025, 1, 31)
    assert txs[2].payment_date == datetime(2025, 3, 2)

    assert txs[0].date == datetime(2025, 1, 1)
    assert txs[1].date == datetime(2025, 1, 31)

    # Descricoes com sufixo (n/total)
    descricoes = {tx.description for tx in txs}
    assert descricoes == {
        "Compra Mercado (1/3)",
        "Compra Mercado (2/3)",
        "Compra Mercado (3/3)",
    }

    # Valor total dividido entre as parcelas (300 / 3 = 100 cada)
    assert [tx.amount for tx in txs] == [100.0, 100.0, 100.0]
    assert round(sum(tx.amount for tx in txs), 2) == 300.0


def test_parcelamento_divide_valor_com_arredondamento(app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("parcdiv", "parcdiv@example.com")

    payload = _base_payload(conta.id, cat_receita.id, payment.id)
    payload["amount"] = 100.0
    _create_installments(user_id=user.id, base_payload=payload, parcelas=3)

    valores = sorted(tx.amount for tx in Transaction.query.filter_by(user_id=user.id).all())
    # 100 / 3 = 33.33, 33.33, 33.34 (a ultima absorve a diferenca)
    assert valores == [33.33, 33.33, 33.34]
    assert round(sum(valores), 2) == 100.0


def test_parcelamento_descricao_vazia(app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("parc2", "parc2@example.com")

    _create_installments(
        user_id=user.id,
        base_payload=_base_payload(conta.id, cat_receita.id, payment.id, description=""),
        parcelas=2,
    )
    descricoes = {tx.description for tx in Transaction.query.filter_by(user_id=user.id).all()}
    assert descricoes == {"(1/2)", "(2/2)"}


def test_add_transaction_route_parcelado(client, app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("parcrt", "parcrt@example.com")
    login_client(client, user)

    resp = client.post(
        f"/transactions/transactions/add?conta_id={conta.id}",
        data={
            "type": "receita",
            "category_id": str(cat_receita.id),
            "expense_id": "0",
            "amount": "100.00",
            "discount": "0.00",
            "payment_method_id": str(payment.id),
            "payment_date": "2025-01-01",
            "date": "2025-01-01",
            "recurrence": "nenhuma",
            "description": "Assinatura",
            "conta_id": str(conta.id),
            "parcelado": "y",
            "numero_parcelas": "4",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    txs = Transaction.query.filter_by(user_id=user.id, conta_id=conta.id).all()
    assert len(txs) == 4
    # 100,00 dividido em 4 parcelas de 25,00
    assert [tx.amount for tx in txs] == [25.0, 25.0, 25.0, 25.0]


# --------------------------------------------------------------------------- #
# Implementacao 4 - receita automatica de saldo inicial
# --------------------------------------------------------------------------- #
def test_saldo_inicial_gera_receita_automatica(client, app_ctx):
    user, tipo, conta, *_ = _seed("auto", "auto@example.com")
    login_client(client, user)

    resp = client.post(
        "/conta/contas/add",
        data={"nome": "Conta Corrente", "tipo_id": str(tipo.id), "saldo_inicial": "5000,00"},
        follow_redirects=False,
    )
    assert resp.status_code == 302

    nova = Conta.query.filter_by(user_id=user.id, nome="Conta Corrente").order_by(Conta.id.desc()).first()
    receita = InitialBalanceService.find_existing(user_id=user.id, conta_id=nova.id)

    assert receita is not None
    assert receita.is_saldo_inicial is True
    assert receita.type == "receita"
    assert receita.paid is True
    assert receita.amount == 5000.0
    assert receita.description == "Saldo inicial"
    assert receita.details == "Saldo Inicial da conta Conta Corrente"

    categoria = db.session.get(Category, receita.category_id)
    assert categoria.name == "Outros"

    # Saldo consistente: nao deve contar em dobro.
    db.session.refresh(nova)
    assert nova.saldo_atual == 5000.0
    assert LedgerService.get_account_balance(user_id=user.id, account_id=nova.id) == 5000


def test_saldo_inicial_nao_duplica_na_edicao(client, app_ctx):
    user, tipo, conta, *_ = _seed("dup", "dup@example.com")
    login_client(client, user)

    client.post(
        "/conta/contas/add",
        data={"nome": "Conta X", "tipo_id": str(tipo.id), "saldo_inicial": "1000,00"},
        follow_redirects=False,
    )
    nova = Conta.query.filter_by(user_id=user.id, nome="Conta X").order_by(Conta.id.desc()).first()

    # Edita o saldo inicial -> nao deve criar uma segunda receita
    client.post(
        f"/conta/conta/editar/{nova.id}",
        data={"nome": "Conta X", "tipo_id": str(tipo.id), "saldo_inicial": "2500,75"},
        follow_redirects=False,
    )

    receitas = Transaction.query.filter_by(user_id=user.id, conta_id=nova.id, is_saldo_inicial=True).all()
    assert len(receitas) == 1
    assert receitas[0].amount == 2500.75

    db.session.refresh(nova)
    assert nova.saldo_atual == 2500.75


def test_saldo_inicial_zero_remove_receita(client, app_ctx):
    user, tipo, conta, *_ = _seed("zero", "zero@example.com")
    login_client(client, user)

    client.post(
        "/conta/contas/add",
        data={"nome": "Conta Z", "tipo_id": str(tipo.id), "saldo_inicial": "800,00"},
        follow_redirects=False,
    )
    nova = Conta.query.filter_by(user_id=user.id, nome="Conta Z").order_by(Conta.id.desc()).first()
    assert InitialBalanceService.find_existing(user_id=user.id, conta_id=nova.id) is not None

    client.post(
        f"/conta/conta/editar/{nova.id}",
        data={"nome": "Conta Z", "tipo_id": str(tipo.id), "saldo_inicial": "0,00"},
        follow_redirects=False,
    )
    assert InitialBalanceService.find_existing(user_id=user.id, conta_id=nova.id) is None

    db.session.refresh(nova)
    assert nova.saldo_atual == 0.0


def test_saldo_inicial_com_expense_sugerido(app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("exp", "exp@example.com")
    expense = Expense(name="Saldo inicial", category_id=cat_outros.id, user_id=user.id)
    db.session.add(expense)
    conta.saldo_inicial = 1500.0
    db.session.commit()

    receita = InitialBalanceService.sync_for_account(user_id=user.id, conta=conta)
    assert receita.expense_id == expense.id
    assert receita.amount == 1500.0


def test_saldo_inicial_receita_participa_do_relatorio(app_ctx):
    user, tipo, conta, cat_receita, cat_outros, payment = _seed("rel", "rel@example.com")
    conta.saldo_inicial = 3000.0
    db.session.commit()

    InitialBalanceService.sync_for_account(user_id=user.id, conta=conta)

    from services.report_service import ReportService

    hoje = datetime.now()
    summary = ReportService.account_period_summary(
        user_id=user.id, account_id=conta.id, year=hoje.year, month=hoje.month
    )
    # A receita de saldo inicial nao entra no ledger, portanto nao afeta o
    # balance do periodo, mas existe como transacao consultavel em relatorios.
    receitas_tx = Transaction.query.filter_by(
        user_id=user.id, conta_id=conta.id, type="receita"
    ).all()
    assert any(tx.is_saldo_inicial and tx.amount == 3000.0 for tx in receitas_tx)
    assert "balance" in summary
