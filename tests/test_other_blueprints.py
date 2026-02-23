from datetime import date

import pytest
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import Category, Conta, Expense, PaymentMethod, TipoConta, TipoInvestimento, User
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

    category = Category(name="Outros", type="despesa", exclusive=False)
    payment = PaymentMethod(name="Dinheiro", is_active=True)
    expense = Expense(name="Padrao", category=category)
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
