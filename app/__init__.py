from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config.from_mapping(DEBUG=True)   

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

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
