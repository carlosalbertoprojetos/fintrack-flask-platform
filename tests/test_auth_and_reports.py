from datetime import datetime

from app import db
from app.models import Category, Conta, PaymentMethod, TipoConta, Transaction, User
from conftest import login_client


def _create_user(username, email, password="secret123"):
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    return user


def _create_account(user):
    tipo = TipoConta(nome="Banco", descricao="Conta", ativo=True, user_id=user.id)
    db.session.add(tipo)
    db.session.flush()

    conta = Conta(nome="Conta Teste", tipo_id=tipo.id, saldo_inicial=100.0, saldo_atual=100.0, user_id=user.id)
    db.session.add(conta)
    db.session.flush()
    return conta


def _seed_transactions(user, conta):
    receita = Category(name="Salario", type="receita", exclusive=True)
    despesa = Category(name="Mercado", type="despesa", exclusive=True)
    pagamento = PaymentMethod(name="Pix", is_active=True)
    db.session.add_all([receita, despesa, pagamento])
    db.session.flush()

    db.session.add_all(
        [
            Transaction(
                user_id=user.id,
                category_id=receita.id,
                payment_method_id=pagamento.id,
                conta_id=conta.id,
                date=datetime.now(),
                payment_date=datetime.now(),
                amount=1500.0,
                discount=0.0,
                type="receita",
                paid=True,
            ),
            Transaction(
                user_id=user.id,
                category_id=despesa.id,
                payment_method_id=pagamento.id,
                conta_id=conta.id,
                date=datetime.now(),
                due_date=datetime.now(),
                payment_date=datetime.now(),
                amount=300.0,
                discount=25.0,
                type="despesa",
                paid=True,
            ),
        ]
    )
    db.session.commit()


def test_login_success_redirects_dashboard(client, app_ctx):
    _create_user("auth1", "auth1@example.com", "abc12345")
    db.session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "auth1", "password": "abc12345", "remember_me": "y"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_login_accepts_email_and_case_insensitive_identifier(client, app_ctx):
    _create_user("AuthCase", "AuthCase@Example.com", "abc12345")
    db.session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "  authcase@example.COM  ", "password": "abc12345"},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location.endswith("/dashboard")


def test_login_invalid_credentials_renders_login(client, app_ctx):
    _create_user("auth2", "auth2@example.com", "abc12345")
    db.session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "auth2", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code == 200


def test_register_creates_user_and_redirects(monkeypatch, client, app_ctx):
    import app as app_pkg

    monkeypatch.setattr(app_pkg, "initialize_user_default_data", lambda user: True)

    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "abc12345",
            "password2": "abc12345",
        },
        follow_redirects=False,
    )

    created = User.query.filter_by(username="newuser").first()
    assert created is not None
    assert response.status_code == 302
    assert response.location.endswith("/conta/contas")


def test_profile_updates_email_and_password(client, app_ctx):
    user = _create_user("auth3", "auth3@example.com", "oldpass")
    db.session.commit()
    login_client(client, user)

    response = client.post(
        "/auth/profile",
        data={
            "email": "changed@example.com",
            "current_password": "oldpass",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
        follow_redirects=False,
    )

    db.session.refresh(user)
    assert response.status_code == 302
    assert response.location.endswith("/auth/profile")
    assert user.email == "changed@example.com"
    assert user.check_password("newpass123") is True


def test_reset_request_valid_email_redirects_login(monkeypatch, client, app_ctx):
    user = _create_user("auth4", "auth4@example.com")
    db.session.commit()

    import app.routes as routes_module

    monkeypatch.setattr(routes_module, "send_reset_email", lambda u: None)

    response = client.post(
        "/auth/reset_request",
        data={"email": user.email},
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.location.endswith("/auth/login")


def test_reset_token_invalid_redirects_to_request(client):
    response = client.get("/auth/reset_password/token-invalido", follow_redirects=False)

    assert response.status_code == 302
    assert response.location.endswith("/auth/reset_request")


def test_reset_token_valid_updates_password(client, app_ctx):
    user = _create_user("auth5", "auth5@example.com", "oldpass")
    db.session.commit()

    token = user.get_reset_token()
    response = client.post(
        f"/auth/reset_password/{token}",
        data={"password": "newpass123", "password2": "newpass123"},
        follow_redirects=False,
    )

    db.session.refresh(user)
    assert response.status_code == 302
    assert response.location.endswith("/auth/login")
    assert user.check_password("newpass123") is True


def test_reports_routes_return_200_for_authenticated_user(client, app_ctx):
    user = _create_user("rep1", "rep1@example.com")
    conta = _create_account(user)
    _seed_transactions(user, conta)
    login_client(client, user)

    response_reports = client.get("/transactions/reports")
    response_pm = client.get("/transactions/reports/payment_method")
    response_discounts = client.get("/transactions/reports/discounts")
    response_pm_exp = client.get("/transactions/reports/payment_method_expenses")

    assert response_reports.status_code == 200
    assert response_pm.status_code == 200
    assert response_discounts.status_code == 200
    assert response_pm_exp.status_code == 200
