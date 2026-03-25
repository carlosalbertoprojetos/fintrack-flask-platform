from datetime import date, datetime

import pytest
from sqlalchemy.exc import IntegrityError

from app import db, repair_default_lookup_data
from app.models import Category, Conta, Expense, Investimento, PaymentMethod, TipoConta, TipoInvestimento, Transaction, User
from conftest import login_client, set_legacy_session_user


def _create_user(username, email):
    user = User(username=username, email=email)
    user.set_password("secret123")
    db.session.add(user)
    db.session.flush()
    return user


def _create_account(user, nome="Conta Base"):
    tipo = TipoConta(nome="Banco", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo)
    db.session.flush()
    conta = Conta(nome=nome, tipo_id=tipo.id, saldo_inicial=1000.0, saldo_atual=1000.0, user_id=user.id)
    db.session.add(conta)
    db.session.flush()
    return conta, tipo


def test_repair_default_lookup_data_merges_corrupted_lookups(app_ctx):
    user = _create_user("repair1", "repair1@example.com")

    good_category = Category(name="Serviços", type="despesa", exclusive=True, user_id=user.id)
    bad_category = Category(name="Serviços".encode("utf-8").decode("latin1"), type="despesa", exclusive=True, user_id=user.id)
    good_payment = PaymentMethod(name="Transferência", is_active=True, user_id=user.id)
    bad_payment = PaymentMethod(name="Transferência".encode("utf-8").decode("latin1"), is_active=True, user_id=user.id)
    good_tipo = TipoConta(nome="Banco Físico", descricao="Físico", ativo=True, user_id=user.id)
    bad_tipo = TipoConta(
        nome="Banco Físico".encode("utf-8").decode("latin1"),
        descricao="Físico".encode("utf-8").decode("latin1"),
        ativo=True,
        user_id=user.id,
    )
    good_tipo_inv = TipoInvestimento(nome="Ações", descricao="Investimento em ações", ativo=True, user_id=user.id)
    bad_tipo_inv = TipoInvestimento(
        nome="Ações".encode("utf-8").decode("latin1"),
        descricao="Investimento em ações".encode("utf-8").decode("latin1"),
        ativo=True,
        user_id=user.id,
    )
    db.session.add_all([good_category, bad_category, good_payment, bad_payment, good_tipo, bad_tipo, good_tipo_inv, bad_tipo_inv])
    db.session.flush()

    good_expense = Expense(name="Eletrônicos", category_id=good_category.id, user_id=user.id)
    bad_expense = Expense(name="Eletrúnicos", category_id=bad_category.id, user_id=user.id)
    conta = Conta(nome="Conta Reparo", tipo_id=bad_tipo.id, saldo_inicial=100.0, saldo_atual=100.0, user_id=user.id)
    investimento = Investimento(tipo_investimento_id=bad_tipo_inv.id, data_abertura=date.today())
    db.session.add_all([good_expense, bad_expense, conta, investimento])
    db.session.flush()

    tx = Transaction(
        date=datetime.utcnow(),
        amount=50.0,
        type="despesa",
        paid=True,
        recurrence="none",
        description="Compra de teste",
        conta_id=conta.id,
        user_id=user.id,
        category_id=bad_category.id,
        expense_id=bad_expense.id,
        payment_method_id=bad_payment.id,
    )
    db.session.add(tx)
    db.session.commit()

    repair_default_lookup_data()

    repaired_tx = db.session.get(Transaction, tx.id)
    repaired_conta = db.session.get(Conta, conta.id)
    repaired_investimento = db.session.get(Investimento, investimento.id)

    assert Category.query.filter_by(name="Serviços".encode("utf-8").decode("latin1")).count() == 0
    assert PaymentMethod.query.filter_by(name="Transferência".encode("utf-8").decode("latin1")).count() == 0
    assert TipoConta.query.filter_by(nome="Banco Físico".encode("utf-8").decode("latin1"), user_id=user.id).count() == 0
    assert TipoInvestimento.query.filter_by(nome="Ações".encode("utf-8").decode("latin1"), user_id=user.id).count() == 0
    assert Expense.query.filter_by(name="Eletrúnicos").count() == 0

    assert repaired_tx.category_id == good_category.id
    assert repaired_tx.expense_id == good_expense.id
    assert repaired_tx.payment_method_id == good_payment.id
    assert repaired_conta.tipo_id == good_tipo.id
    assert repaired_investimento.tipo_investimento_id == good_tipo_inv.id


def test_tipo_conta_crud_routes(client, app_ctx):
    user = _create_user("tc1", "tc1@example.com")
    db.session.commit()
    login_client(client, user)

    r_get = client.get("/tipo-conta/tipo-conta/novo")
    assert r_get.status_code == 200

    r_create = client.post(
        "/tipo-conta/tipo-conta/novo",
        data={"nome": "Carteira", "descricao": "Fisica", "ativo": "y"},
        follow_redirects=False,
    )
    assert r_create.status_code == 302

    created = TipoConta.query.filter_by(user_id=user.id, nome="Carteira").first()
    assert created is not None

    r_edit = client.post(
        f"/tipo-conta/tipo-conta/editar/{created.id}",
        data={"nome": "Carteira 2", "descricao": "Editada", "ativo": "y"},
        follow_redirects=False,
    )
    assert r_edit.status_code == 302

    db.session.refresh(created)
    assert created.nome == "Carteira 2"


def test_tipo_investimento_routes_and_inline_update(client, app_ctx):
    user = _create_user("ti1", "ti1@example.com")
    db.session.commit()
    login_client(client, user)

    r_new = client.post(
        "/tipo-investimento/tipo-investimento/novo",
        data={"nome": "CDB", "descricao": "Renda fixa", "ativo": "y"},
        follow_redirects=False,
    )
    assert r_new.status_code == 302

    tipo = TipoInvestimento.query.filter_by(user_id=user.id, nome="CDB").first()
    assert tipo is not None

    r_nome = client.post(
        f"/tipo-investimento/tipo-investimento/editar-nome/{tipo.id}",
        json={"nome": "CDB Pos"},
    )
    assert r_nome.status_code == 200
    assert r_nome.get_json()["success"] is True

    r_desc = client.post(
        f"/tipo-investimento/tipo-investimento/editar-descricao/{tipo.id}",
        json={"descricao": "Descricao alterada"},
    )
    assert r_desc.status_code == 200
    assert r_desc.get_json()["success"] is True


def test_conta_inline_name_update_and_delete_guard(client, app_ctx):
    user = _create_user("co1", "co1@example.com")
    conta, _ = _create_account(user)
    db.session.commit()
    login_client(client, user)

    r_inline = client.post(f"/conta/conta/editar-nome/{conta.id}", json={"nome": "Conta Renomeada"})
    assert r_inline.status_code == 200
    assert r_inline.get_json()["success"] is True

    db.session.refresh(conta)
    assert conta.nome == "Conta Renomeada"

    # Nao deve excluir a unica conta do usuario
    r_delete = client.post(f"/conta/conta/excluir/{conta.id}", follow_redirects=False)
    assert r_delete.status_code == 302




def test_foreign_admin_objects_return_404(client, app_ctx):
    owner = _create_user("owner1", "owner1@example.com")
    intruder = _create_user("intruder1", "intruder1@example.com")

    conta, tipo = _create_account(owner, "Conta Protegida")
    tipo_inv = TipoInvestimento(nome="Protegido", descricao="Escopo", ativo=True, user_id=owner.id)
    db.session.add(tipo_inv)
    db.session.commit()

    login_client(client, intruder)

    assert client.get(f"/conta/conta/editar/{conta.id}").status_code == 404
    assert client.get(f"/tipo-conta/tipo-conta/editar/{tipo.id}").status_code == 404
    assert client.get(f"/tipo-investimento/tipo-investimento/editar/{tipo_inv.id}").status_code == 404

def test_investimento_list_and_create_routes(client, app_ctx):
    user = _create_user("inv1", "inv1@example.com")
    conta, _ = _create_account(user)
    tipo_inv = TipoInvestimento(nome="Tesouro", descricao="Publico", ativo=True, user_id=user.id)
    db.session.add(tipo_inv)
    db.session.commit()

    login_client(client, user)

    r_list = client.get(f"/investimento/investimentos?conta_id={conta.id}")
    assert r_list.status_code == 200

    r_create = client.post(
        "/investimento/investimentos/novo",
        data={"tipo_investimento_id": tipo_inv.id},
        follow_redirects=False,
    )
    assert r_create.status_code == 302


def test_legacy_transactions_blueprint_basic_flows(client, app_ctx):
    user = _create_user("leg1", "leg1@example.com")
    conta, _ = _create_account(user, "Conta Legacy")

    category = Category(name="Outros", type="despesa", exclusive=False, user_id=user.id)
    payment = PaymentMethod(name="Dinheiro", is_active=True, user_id=user.id)
    expense = Expense(name="Padrao", category=category, user_id=user.id)
    db.session.add_all([category, payment, expense])
    db.session.commit()

    set_legacy_session_user(client, user)
    login_client(client, user)

    r_index = client.get("/legacy/")
    assert r_index.status_code == 200

    r_new_get = client.get("/legacy/transactions/new")
    assert r_new_get.status_code == 200

    # Comportamento atual do legado: POST falha por nao preencher Transaction.type.
    with pytest.raises(IntegrityError):
        client.post(
            "/legacy/transactions/new",
            data={
                "amount": "100.00",
                "discount": "0.00",
                "type": "despesa",
                "category_id": category.id,
                "expense_id": expense.id,
                "payment_method_id": payment.id,
                "description": "Compra legacy",
                "conta_id": conta.id,
                "date": date.today().isoformat(),
            },
            follow_redirects=False,
        )
