from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
from config import Config
from flask_mail import Mail
import os
import shutil

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Por favor, faça login para acessar esta página."
mail = Mail()


def format_currency(value):
    """Format a number as currency with comma as decimal separator"""
    if value is None:
        return "0,00"
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ensure_backup_exists():
    """Ensure that a backup of the database exists at C:\backup\bk_flask.db"""
    backup_dir = r"C:\backup"
    backup_file = os.path.join(backup_dir, "bk_flask.db")
    db_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.db")

    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    # If backup doesn't exist or is older than the main db, create/update it
    if not os.path.exists(backup_file) or (
        os.path.exists(db_file)
        and os.path.getmtime(db_file) > os.path.getmtime(backup_file)
    ):
        if os.path.exists(db_file):
            shutil.copy2(db_file, backup_file)
            print(f"Backup criado/atualizado em: {backup_file}")


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config.from_mapping(DEBUG=True)

    # Add custom filter for currency formatting
    app.jinja_env.filters["currency"] = format_currency

    # Ensure backup exists before initializing the database
    ensure_backup_exists()

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)

    # Add a signal handler to update backup after database changes
    @app.after_request
    def after_request(response):
        if response.status_code < 400:  # Only backup on successful requests
            ensure_backup_exists()
        return response

    from app.routes import main_bp, auth_bp, transaction_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(transaction_bp, url_prefix="/transactions")

    # Adicione o context processor dentro da função create_app
    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow()}

    with app.app_context():
        db.create_all()

        # Importar Category aqui para evitar importação circular
        from app.models import Category, PaymentMethod, Expense

        # Adicionar categorias padrão
        categories_data = [
            {"name": "Salário", "type": "receita", "exclusive": True},
            {"name": "Freelance", "type": "receita", "exclusive": True},
            {"name": "Investimentos", "type": "receita", "exclusive": True},
            {"name": "Outros Rendimentos", "type": "receita", "exclusive": True},
            {"name": "Alimentação", "type": "despesa", "exclusive": True},
            {"name": "Moradia", "type": "despesa", "exclusive": True},
            {"name": "Transporte", "type": "despesa", "exclusive": True},
            {"name": "Lazer", "type": "despesa", "exclusive": True},
            {"name": "Saúde", "type": "despesa", "exclusive": True},
            {"name": "Educação", "type": "despesa", "exclusive": True},
            {"name": "Serviços", "type": "despesa", "exclusive": True},
            {"name": "Compras", "type": "despesa", "exclusive": True},
            {
                "name": "Outros",
                "type": "receita",
                "exclusive": False,
            },  # Categoria genérica para ambos
            {
                "name": "Diversos",
                "type": "despesa",
                "exclusive": False,
            },  # Categoria genérica para ambos
        ]

        for category_data in categories_data:
            category = Category.query.filter_by(
                name=category_data["name"], type=category_data["type"]
            ).first()
            if not category:
                category = Category(**category_data)
                db.session.add(category)

        # Adicionar formas de pagamento padrão
        payments_data = [
            {"name": "Dinheiro", "is_active": True},
            {"name": "Pix", "is_active": True},
            {"name": "Cartão Débito", "is_active": True},
            {"name": "Cartão Crédito", "is_active": True},
            {"name": "Boleto", "is_active": True},
            {"name": "Cheque", "is_active": True},
            {"name": "Crediário", "is_active": True},
        ]

        for payment_data in payments_data:
            exists = PaymentMethod.query.filter_by(
                name=payment_data["name"], is_active=True
            ).first()
            if not exists:
                db.session.add(PaymentMethod(**payment_data))

        # Adicionar despesas padrão
        expensives_data = [
            {"name": "CDB", "category_id": "Investimentos"},
            {"name": "Supermercado", "category_id": "Alimentação"},
            {"name": "Aluguel", "category_id": "Moradia"},
            {"name": "Combustível", "category_id": "Transporte"},
            {"name": "Farmácia", "category_id": "Saúde"},
            {"name": "Curso", "category_id": "Educação"},
        ]

        for expensive_data in expensives_data:
            category = Category.query.filter_by(
                name=expensive_data["category_id"]
            ).first()
            if not category:
                continue  # ou você pode lançar erro/logar se quiser

            expense = Expense.query.filter_by(
                name=expensive_data["name"], category_id=category.id
            ).first()

            if not expense:
                expense = Expense(name=expensive_data["name"], category_id=category.id)
                db.session.add(expense)

        db.session.commit()

    return app
