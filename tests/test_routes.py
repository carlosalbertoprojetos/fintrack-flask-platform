from datetime import datetime
from urllib.parse import parse_qs, urlparse

from app import db
from app.models import Category, Conta, Expense, PaymentMethod, TipoConta, Transaction, User
from conftest import login_client


def _create_user(username="tester", email="tester@example.com"):
    user = User(username=username, email=email)
    user.set_password("secret123")
    db.session.add(user)
    db.session.flush()
    return user


def _create_account_for_user(user):
    tipo = TipoConta(nome="Banco", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo)
    db.session.flush()

    conta = Conta(nome="Conta Teste", tipo_id=tipo.id, saldo_inicial=0.0, saldo_atual=0.0, user_id=user.id)
    db.session.add(conta)
    db.session.flush()
    return conta


def test_index_anonymous_returns_home(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_authenticated_redirects_to_dashboard(client, app_ctx):
    user = _create_user("u1", "u1@example.com")
    db.session.commit()
    login_client(client, user)

    response = client.get("/")

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_dashboard_without_account_redirects_to_contas(client, app_ctx):
    user = _create_user("u2", "u2@example.com")
    db.session.commit()
    login_client(client, user)

    response = client.get("/dashboard")

    assert response.status_code == 302
    assert response.location.endswith("/conta/contas")


def test_get_expenses_requires_login(client):
    response = client.get("/transactions/expenses/by-category/1")
    assert response.status_code == 302
    assert "/auth/login" in response.location


def test_get_expenses_returns_json_for_authenticated_user(client, app_ctx):
    user = _create_user("u3", "u3@example.com")
    category = Category(name="Alimentacao", type="despesa", exclusive=True)
    db.session.add(category)
    db.session.flush()

    expense = Expense(name="Supermercado", category_id=category.id)
    db.session.add(expense)
    db.session.commit()
    login_client(client, user)

    response = client.get(f"/transactions/expenses/by-category/{category.id}")

    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert data[0]["name"] == "Supermercado"


def test_get_categories_by_type_includes_non_exclusive(client, app_ctx):
    user = _create_user("u4", "u4@example.com")
    db.session.add_all(
        [
            Category(name="Salario", type="receita", exclusive=True),
            Category(name="Diversos", type="despesa", exclusive=False),
        ]
    )
    db.session.commit()
    login_client(client, user)

    response = client.get("/transactions/categories/by-type/receita")

    assert response.status_code == 200
    names = [item["name"] for item in response.get_json()]
    assert "Salario" in names
    assert "Diversos" in names


def test_replicate_transaction_redirects_with_prefilled_query(client, app_ctx):
    user = _create_user("u5", "u5@example.com")
    conta = _create_account_for_user(user)
    category = Category(name="Mercado", type="despesa", exclusive=True)
    payment = PaymentMethod(name="Pix", is_active=True)
    db.session.add_all([category, payment])
    db.session.flush()

    tx = Transaction(
        user_id=user.id,
        category_id=category.id,
        expense_id=None,
        payment_method_id=payment.id,
        conta_id=conta.id,
        date=datetime(2025, 1, 10),
        due_date=datetime(2025, 1, 15),
        payment_date=datetime(2025, 1, 20),
        amount=123.45,
        discount=3.45,
        type="despesa",
        paid=True,
        recurrence="none",
        description="Compra teste",
        details="Detalhes",
        notes="Notas",
    )
    db.session.add(tx)
    db.session.commit()
    login_client(client, user)

    response = client.get(f"/transactions/transactions/replicate/{tx.id}")

    assert response.status_code == 302
    parsed = urlparse(response.location)
    assert parsed.path == "/transactions/transactions/add"

    params = parse_qs(parsed.query)
    assert params["type"][0] == "despesa"
    assert params["paid"][0] == "0"
    assert params["conta_id"][0] == str(conta.id)
