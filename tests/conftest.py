from pathlib import Path

import pytest
from flask import Flask

from app import db, format_currency, login_manager
from app.routes import auth_bp, main_bp, transaction_bp
from routes.conta import conta_bp
from routes.investimento import investimento_bp
from routes.tipo_conta import tipo_conta_bp
from routes.tipo_investimento import tipo_investimento_bp
from routes.transactions import transactions as legacy_transactions_bp


@pytest.fixture()
def app():
    project_root = Path(__file__).resolve().parents[1]
    templates_dir = project_root / "app" / "templates"
    static_dir = project_root / "app" / "static"

    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir),
    )
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
    )

    db.init_app(app)
    login_manager.init_app(app)
    app.jinja_env.filters["currency"] = format_currency

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(transaction_bp, url_prefix="/transactions", name="transaction")
    app.register_blueprint(conta_bp, url_prefix="/conta")
    app.register_blueprint(investimento_bp, url_prefix="/investimento")
    app.register_blueprint(tipo_investimento_bp, url_prefix="/tipo-investimento")
    app.register_blueprint(tipo_conta_bp, url_prefix="/tipo-conta")
    app.register_blueprint(legacy_transactions_bp, url_prefix="/legacy")

    @app.route("/shutdown")
    def shutdown_stub():
        return "ok", 200

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def app_ctx(app):
    with app.app_context():
        yield


@pytest.fixture()
def client(app):
    return app.test_client()


def login_client(client, user):
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user.id)
        sess["_fresh"] = True


def set_legacy_session_user(client, user):
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
