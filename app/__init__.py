from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
from config import Config

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    from app.routes import main_bp, auth_bp, transaction_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(transaction_bp, url_prefix='/transactions')
    
    # Adicione o context processor dentro da função create_app
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}
    
    with app.app_context():
        db.create_all()
        
        # Importar Category aqui para evitar importação circular
        from app.models import Category
        
        # Adicionar categorias padrão
        categories_data = [
            {'name': 'Salário', 'type': 'income', 'exclusive': 'income'},
            {'name': 'Freelance', 'type': 'income', 'exclusive': 'income'},
            {'name': 'Investimentos', 'type': 'income', 'exclusive': 'income'},
            {'name': 'Outros Rendimentos', 'type': 'income', 'exclusive': 'income'},
            {'name': 'Alimentação', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Moradia', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Transporte', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Lazer', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Saúde', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Educação', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Serviços', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Compras', 'type': 'expense', 'exclusive': 'expense'},
            {'name': 'Outros', 'type': 'income', 'exclusive': ''},  # Categoria genérica para ambos
            {'name': 'Diversos', 'type': 'expense', 'exclusive': ''}  # Categoria genérica para ambos
        ]
        
        for category_data in categories_data:
            category = Category.query.filter_by(name=category_data['name'], type=category_data['type']).first()
            if not category:
                category = Category(**category_data)
                db.session.add(category)
        
        db.session.commit()
    
    return app
