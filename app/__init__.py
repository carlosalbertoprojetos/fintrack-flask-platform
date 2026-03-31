from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime
from config import Config
from flask_mail import Mail
import json
import logging
import os
from pathlib import Path
import shutil
from sqlalchemy import inspect, text

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()


class JsonLogFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(app: Flask):
    level_name = str(app.config.get("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    app.logger.handlers.clear()
    app.logger.setLevel(level)

    handler = logging.StreamHandler()
    if app.config.get("JSON_LOGS", True):
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s"))

    app.logger.addHandler(handler)
    app.logger.propagate = False


def format_currency(value):
    """Format a number as currency in Brazilian format (R$ 0,00)"""
    if value is None:
        return "0,00"

    # Convert to float if it's a string
    try:
        if isinstance(value, str):
            # Remove espaços e caracteres não numéricos exceto vírgula e ponto
            value = value.replace(" ", "").replace("R$", "").strip()
            # Se contém vírgula, assumir formato brasileiro
            if "," in value:
                value = value.replace(".", "").replace(",", ".")
            value = float(value)
        
        # Formatar com 2 casas decimais
        # Usar abs para valores negativos
        abs_value = abs(value)
        integer_part = int(abs_value)
        decimal_part = int(round((abs_value - integer_part) * 100))
        
        # Formatar parte inteira com separador de milhar (ponto)
        integer_str = f"{integer_part:,}".replace(",", ".")
        
        # Formatar parte decimal sempre com 2 dígitos
        decimal_str = f"{decimal_part:02d}"
        
        # Combinar
        formatted = f"{integer_str},{decimal_str}"
        
        # Adicionar sinal negativo se necessário
        if value < 0:
            formatted = f"-{formatted}"
        
        return formatted
    except (ValueError, TypeError):
        return "0,00"


def initialize_user_default_data(user):
    """Inicializa dados padrao isolados por usuario."""
    try:
        from app.models import TipoConta, TipoInvestimento, Conta, Category, PaymentMethod, Expense

        categories_data = [
            {"name": "Salário", "type": "receita", "exclusive": True, "icon": "bx-money", "color": "#28a745"},
            {"name": "Freelance", "type": "receita", "exclusive": True, "icon": "bx-briefcase", "color": "#17a2b8"},
            {"name": "Investimentos", "type": "receita", "exclusive": True, "icon": "bx-trending-up", "color": "#20c997"},
            {"name": "Outros Rendimentos", "type": "receita", "exclusive": True, "icon": "bx-plus-circle", "color": "#6f42c1"},
            {"name": "Alimentação", "type": "despesa", "exclusive": True, "icon": "bx-food-menu", "color": "#dc3545"},
            {"name": "Moradia", "type": "despesa", "exclusive": True, "icon": "bx-home", "color": "#fd7e14"},
            {"name": "Transporte", "type": "despesa", "exclusive": True, "icon": "bx-car", "color": "#ffc107"},
            {"name": "Lazer", "type": "despesa", "exclusive": True, "icon": "bx-game", "color": "#e83e8c"},
            {"name": "Saúde", "type": "despesa", "exclusive": True, "icon": "bx-heart", "color": "#6f42c1"},
            {"name": "Educação", "type": "despesa", "exclusive": True, "icon": "bx-book", "color": "#17a2b8"},
            {"name": "Serviços", "type": "despesa", "exclusive": True, "icon": "bx-wrench", "color": "#20c997"},
            {"name": "Compras", "type": "despesa", "exclusive": True, "icon": "bx-shopping-bag", "color": "#28a745"},
            {"name": "Outros", "type": "receita", "exclusive": False, "icon": "bx-plus", "color": "#6c757d"},
            {"name": "Diversos", "type": "despesa", "exclusive": False, "icon": "bx-dots-horizontal-rounded", "color": "#6c757d"},
        ]
        for category_data in categories_data:
            existing_category = Category.query.filter_by(user_id=user.id, name=category_data["name"]).first()
            if not existing_category:
                db.session.add(Category(user_id=user.id, **category_data))

        payments_data = [
            {"name": "Dinheiro", "is_active": True},
            {"name": "Pix", "is_active": True},
            {"name": "Cartão Débito", "is_active": True},
            {"name": "Cartão Crédito", "is_active": True},
            {"name": "Boleto", "is_active": True},
            {"name": "Cheque", "is_active": True},
            {"name": "Crediário", "is_active": True},
            {"name": "Transferência", "is_active": True},
            {"name": "Outros", "is_active": True},
        ]
        for payment_data in payments_data:
            existing_payment = PaymentMethod.query.filter_by(user_id=user.id, name=payment_data["name"]).first()
            if not existing_payment:
                db.session.add(PaymentMethod(user_id=user.id, **payment_data))

        db.session.flush()

        categories_by_name = {
            item.name: item for item in Category.query.filter_by(user_id=user.id).all()
        }
        expenses_data = [
            {"name": "CDB", "category_name": "Investimentos"},
            {"name": "Ações", "category_name": "Investimentos"},
            {"name": "Fundos", "category_name": "Investimentos"},
            {"name": "Supermercado", "category_name": "Alimentação"},
            {"name": "Restaurante", "category_name": "Alimentação"},
            {"name": "Aluguel", "category_name": "Moradia"},
            {"name": "Condomínio", "category_name": "Moradia"},
            {"name": "IPTU", "category_name": "Moradia"},
            {"name": "Combustível", "category_name": "Transporte"},
            {"name": "Manutenção", "category_name": "Transporte"},
            {"name": "Farmácia", "category_name": "Saúde"},
            {"name": "Médico", "category_name": "Saúde"},
            {"name": "Curso", "category_name": "Educação"},
            {"name": "Material", "category_name": "Educação"},
            {"name": "Internet", "category_name": "Serviços"},
            {"name": "Telefone", "category_name": "Serviços"},
            {"name": "Energia", "category_name": "Serviços"},
            {"name": "Água", "category_name": "Serviços"},
            {"name": "Gás", "category_name": "Serviços"},
            {"name": "Roupas", "category_name": "Compras"},
            {"name": "Eletrônicos", "category_name": "Compras"},
        ]
        for expense_data in expenses_data:
            existing_expense = Expense.query.filter_by(user_id=user.id, name=expense_data["name"]).first()
            if existing_expense:
                continue
            category = categories_by_name.get(expense_data["category_name"])
            if category:
                db.session.add(Expense(user_id=user.id, name=expense_data["name"], category_id=category.id))

        tipos_conta_data = [
            {"nome": "Banco Físico", "descricao": "Físico", "ativo": True},
            {"nome": "Banco Virtual", "descricao": "Virtual", "ativo": True},
            {"nome": "Investimento", "descricao": "Corretora", "ativo": True},
        ]
        for tipo_data in tipos_conta_data:
            existing_tipo = TipoConta.query.filter_by(nome=tipo_data["nome"], user_id=user.id).first()
            if not existing_tipo:
                db.session.add(TipoConta(user_id=user.id, **tipo_data))

        tipos_investimento_data = [
            {"nome": "CDB", "descricao": "Certificado de Depósito Bancário", "ativo": True},
            {"nome": "Ações", "descricao": "Investimento em ações", "ativo": True},
            {"nome": "Fundos", "descricao": "Fundos de investimento", "ativo": True},
            {"nome": "Tesouro Direto", "descricao": "Títulos públicos", "ativo": True},
            {"nome": "Poupança", "descricao": "Conta poupança", "ativo": True},
        ]
        for tipo_data in tipos_investimento_data:
            existing_tipo = TipoInvestimento.query.filter_by(nome=tipo_data["nome"], user_id=user.id).first()
            if not existing_tipo:
                db.session.add(TipoInvestimento(user_id=user.id, **tipo_data))

        db.session.commit()

        if Conta.query.filter_by(user_id=user.id).count() == 0:
            tipo_banco_fisico = TipoConta.query.filter_by(nome="Banco Físico", user_id=user.id).first()
            tipo_banco_virtual = TipoConta.query.filter_by(nome="Banco Virtual", user_id=user.id).first()
            contas_data = [
                {"nome": "Inter", "tipo_id": tipo_banco_virtual.id if tipo_banco_virtual else None, "saldo_inicial": 0.0, "saldo_atual": 0.0},
                {"nome": "Banco do Brasil", "tipo_id": tipo_banco_fisico.id if tipo_banco_fisico else None, "saldo_inicial": 0.0, "saldo_atual": 0.0},
            ]
            for conta_data in contas_data:
                if not conta_data["tipo_id"]:
                    continue
                existing_conta = Conta.query.filter_by(nome=conta_data["nome"], user_id=user.id).first()
                if not existing_conta:
                    db.session.add(Conta(user_id=user.id, **conta_data))

        db.session.commit()
        print(f"TODOS os dados padrao criados com sucesso para o usuario {user.username}!")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar dados padrao para o usuario {user.username}: {str(e)}")
        return False


def _ensure_user_scoped_lookup_columns():
    inspector = inspect(db.engine)
    required_columns = {
        "categories": "ALTER TABLE categories ADD COLUMN user_id INTEGER",
        "expenses": "ALTER TABLE expenses ADD COLUMN user_id INTEGER",
        "payment_method": "ALTER TABLE payment_method ADD COLUMN user_id INTEGER",
    }
    for table_name, ddl in required_columns.items():
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if "user_id" not in columns:
            db.session.execute(text(ddl))
    db.session.commit()


def _migrate_lookup_records_to_user_scope():
    from app.models import User, Category, Expense, PaymentMethod, Transaction

    users = User.query.order_by(User.id).all()
    if not users:
        return False

    def owner_ids_for_transaction_field(field_name, value):
        rows = (
            db.session.query(Transaction.user_id)
            .filter(getattr(Transaction, field_name) == value)
            .distinct()
            .order_by(Transaction.user_id)
            .all()
        )
        owner_ids = [row[0] for row in rows if row[0] is not None]
        return owner_ids or [users[0].id]

    category_map = {}
    for category in Category.query.order_by(Category.id).all():
        owner_ids = owner_ids_for_transaction_field("category_id", category.id)
        original_id = category.id
        base_owner_id = owner_ids[0]
        category.user_id = base_owner_id
        category_map[(original_id, base_owner_id)] = category.id
        for owner_id in owner_ids[1:]:
            clone = Category.query.filter_by(
                user_id=owner_id,
                name=category.name,
                type=category.type,
                exclusive=category.exclusive,
            ).first()
            if clone is None:
                clone = Category(
                    user_id=owner_id,
                    name=category.name,
                    type=category.type,
                    exclusive=category.exclusive,
                    icon=category.icon,
                    color=category.color,
                )
                db.session.add(clone)
                db.session.flush()
            Transaction.query.filter_by(category_id=original_id, user_id=owner_id).update(
                {"category_id": clone.id}, synchronize_session=False
            )
            category_map[(original_id, owner_id)] = clone.id

    for expense in Expense.query.order_by(Expense.id).all():
        original_id = expense.id
        original_category_id = expense.category_id
        owner_ids = owner_ids_for_transaction_field("expense_id", original_id)
        base_owner_id = owner_ids[0]
        expense.user_id = base_owner_id
        expense.category_id = category_map.get((original_category_id, base_owner_id), original_category_id)
        for owner_id in owner_ids[1:]:
            scoped_category_id = category_map.get((original_category_id, owner_id), original_category_id)
            clone = Expense.query.filter_by(
                user_id=owner_id,
                name=expense.name,
                category_id=scoped_category_id,
            ).first()
            if clone is None:
                clone = Expense(user_id=owner_id, name=expense.name, category_id=scoped_category_id)
                db.session.add(clone)
                db.session.flush()
            Transaction.query.filter_by(expense_id=original_id, user_id=owner_id).update(
                {"expense_id": clone.id}, synchronize_session=False
            )

    for payment_method in PaymentMethod.query.order_by(PaymentMethod.id).all():
        original_id = payment_method.id
        owner_ids = owner_ids_for_transaction_field("payment_method_id", original_id)
        base_owner_id = owner_ids[0]
        payment_method.user_id = base_owner_id
        for owner_id in owner_ids[1:]:
            clone = PaymentMethod.query.filter_by(user_id=owner_id, name=payment_method.name).first()
            if clone is None:
                clone = PaymentMethod(user_id=owner_id, name=payment_method.name, is_active=payment_method.is_active)
                db.session.add(clone)
                db.session.flush()
            Transaction.query.filter_by(payment_method_id=original_id, user_id=owner_id).update(
                {"payment_method_id": clone.id}, synchronize_session=False
            )

    db.session.commit()
    return True


def repair_default_lookup_data():
    """Corrige cadastros padrao afetados por problemas antigos de encoding."""
    from app.models import Category, Conta, Expense, Investimento, PaymentMethod, TipoConta, TipoInvestimento, Transaction

    def _legacy_mojibake(value):
        return value.encode("utf-8").decode("latin1")

    category_name_map = {
        _legacy_mojibake("Salário"): "Salário",
        _legacy_mojibake("Alimentação"): "Alimentação",
        _legacy_mojibake("Saúde"): "Saúde",
        _legacy_mojibake("Educação"): "Educação",
        _legacy_mojibake("Serviços"): "Serviços",
    }
    payment_name_map = {
        _legacy_mojibake("Cartão Débito"): "Cartão Débito",
        _legacy_mojibake("Cartão Crédito"): "Cartão Crédito",
        _legacy_mojibake("Crediário"): "Crediário",
        _legacy_mojibake("Transferência"): "Transferência",
    }
    expense_name_map = {
        _legacy_mojibake("Ações"): "Ações",
        _legacy_mojibake("Condomínio"): "Condomínio",
        _legacy_mojibake("Combustível"): "Combustível",
        _legacy_mojibake("Manutenção"): "Manutenção",
        _legacy_mojibake("Farmácia"): "Farmácia",
        _legacy_mojibake("Médico"): "Médico",
        _legacy_mojibake("Água"): "Água",
        _legacy_mojibake("Gás"): "Gás",
        _legacy_mojibake("Eletrônicos"): "Eletrônicos",
        "Eletrúnicos": "Eletrônicos",
    }
    tipo_conta_name_map = {
        _legacy_mojibake("Banco Físico"): "Banco Físico",
    }
    tipo_conta_description_map = {
        _legacy_mojibake("Físico"): "Físico",
    }
    tipo_investimento_name_map = {
        _legacy_mojibake("Ações"): "Ações",
        _legacy_mojibake("Poupança"): "Poupança",
    }
    tipo_investimento_description_map = {
        _legacy_mojibake("Certificado de Depósito Bancário"): "Certificado de Depósito Bancário",
        _legacy_mojibake("Investimento em ações"): "Investimento em ações",
        _legacy_mojibake("Títulos públicos"): "Títulos públicos",
        _legacy_mojibake("Conta poupança"): "Conta poupança",
    }

    for category in Category.query.all():
        corrected_name = category_name_map.get(category.name)
        if not corrected_name:
            continue
        target = Category.query.filter_by(
            user_id=category.user_id,
            name=corrected_name,
            type=category.type,
            exclusive=category.exclusive,
        ).first()
        if target and target.id != category.id:
            Expense.query.filter_by(category_id=category.id, user_id=category.user_id).update({"category_id": target.id}, synchronize_session=False)
            Transaction.query.filter_by(category_id=category.id, user_id=category.user_id).update({"category_id": target.id}, synchronize_session=False)
            db.session.delete(category)
        else:
            category.name = corrected_name

    for payment in PaymentMethod.query.all():
        corrected_name = payment_name_map.get(payment.name)
        if not corrected_name:
            continue
        target = PaymentMethod.query.filter_by(user_id=payment.user_id, name=corrected_name).first()
        if target and target.id != payment.id:
            Transaction.query.filter_by(payment_method_id=payment.id, user_id=payment.user_id).update({"payment_method_id": target.id}, synchronize_session=False)
            db.session.delete(payment)
        else:
            payment.name = corrected_name

    for tipo in TipoConta.query.all():
        corrected_name = tipo_conta_name_map.get(tipo.nome, tipo.nome)
        corrected_description = tipo_conta_description_map.get(tipo.descricao, tipo.descricao)
        if corrected_name == tipo.nome and corrected_description == tipo.descricao:
            continue
        target = TipoConta.query.filter_by(nome=corrected_name, user_id=tipo.user_id).first()
        if target and target.id != tipo.id:
            Conta.query.filter_by(tipo_id=tipo.id, user_id=tipo.user_id).update({"tipo_id": target.id}, synchronize_session=False)
            if not target.descricao:
                target.descricao = corrected_description
            db.session.delete(tipo)
        else:
            tipo.nome = corrected_name
            tipo.descricao = corrected_description

    for tipo in TipoInvestimento.query.all():
        corrected_name = tipo_investimento_name_map.get(tipo.nome, tipo.nome)
        corrected_description = tipo_investimento_description_map.get(tipo.descricao, tipo.descricao)
        if corrected_name == tipo.nome and corrected_description == tipo.descricao:
            continue
        target = TipoInvestimento.query.filter_by(nome=corrected_name, user_id=tipo.user_id).first()
        if target and target.id != tipo.id:
            Investimento.query.filter_by(tipo_investimento_id=tipo.id).update({"tipo_investimento_id": target.id}, synchronize_session=False)
            if not target.descricao:
                target.descricao = corrected_description
            db.session.delete(tipo)
        else:
            tipo.nome = corrected_name
            tipo.descricao = corrected_description

    db.session.flush()

    for expense in Expense.query.all():
        corrected_name = expense_name_map.get(expense.name, expense.name)
        if corrected_name == expense.name:
            continue
        target = Expense.query.filter_by(user_id=expense.user_id, name=corrected_name, category_id=expense.category_id).first()
        if target and target.id != expense.id:
            Transaction.query.filter_by(expense_id=expense.id, user_id=expense.user_id).update({"expense_id": target.id}, synchronize_session=False)
            db.session.delete(expense)
        else:
            expense.name = corrected_name

    db.session.commit()
    return True


def _repair_mojibake_text(value):
    if not isinstance(value, str) or not any(marker in value for marker in ("Ã", "Â", "�")):
        return value

    candidate = value
    for _ in range(3):
        try:
            repaired = candidate.encode("latin1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            break
        if repaired == candidate:
            break
        candidate = repaired

    return candidate


def repair_user_visible_text_data():
    """Corrige mojibake em campos textuais exibidos ao usu?rio."""
    from app.models import Category, Conta, Expense, MovimentacaoInvestimento, PaymentMethod, TipoConta, TipoInvestimento, Transaction

    model_fields = [
        (Category, ("name",)),
        (Expense, ("name",)),
        (PaymentMethod, ("name",)),
        (TipoConta, ("nome", "descricao")),
        (TipoInvestimento, ("nome", "descricao")),
        (Conta, ("nome",)),
        (Transaction, ("description", "details", "notes")),
        (MovimentacaoInvestimento, ("observacoes",)),
    ]

    changed = False
    for model, fields in model_fields:
        for record in model.query.all():
            for field in fields:
                current_value = getattr(record, field, None)
                repaired_value = _repair_mojibake_text(current_value)
                if repaired_value != current_value:
                    setattr(record, field, repaired_value)
                    changed = True

    if changed:
        db.session.commit()

    return changed


def get_database_path():
    """Retorna o caminho do banco de dados"""
    from config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        return db_path
    return None


def get_backup_dir():
    """Retorna o diretorio de backup configurado para o ambiente."""
    configured = Config.BACKUP_DIR or str(Path.home() / "Financas_Pessoais" / "backup")
    return configured


def get_quarter_info():
    """Retorna informações sobre o trimestre atual"""
    from datetime import datetime
    now = datetime.now()
    month = now.month
    year = now.year
    
    # Mapeamento de trimestres
    # 1º trimestre: janeiro(1), fevereiro(2), março(3) -> finaliza em março
    # 2º trimestre: abril(4), maio(5), junho(6) -> finaliza em junho
    # 3º trimestre: julho(7), agosto(8), setembro(9) -> finaliza em setembro
    # 4º trimestre: outubro(10), novembro(11), dezembro(12) -> finaliza em dezembro
    
    if month <= 3:
        quarter = 1
        month_name = "março"
    elif month <= 6:
        quarter = 2
        month_name = "junho"
    elif month <= 9:
        quarter = 3
        month_name = "setembro"
    else:
        quarter = 4
        month_name = "dezembro"
    
    return {
        "quarter": quarter,
        "month_name": month_name,
        "year": year
    }

def create_backup():
    """Cria um backup do banco de dados com nomenclatura por trimestre"""
    try:
        if not Config.ENABLE_AUTO_BACKUP:
            return False

        db_path = get_database_path()
        if not db_path or not os.path.exists(db_path):
            print("[AVISO] Banco de dados não encontrado para backup")
            return False
        
        # Criar diretório de backup
        backup_dir = get_backup_dir()
        if not os.path.exists(backup_dir):
            try:
                os.makedirs(backup_dir)
            except Exception as e:
                print(f"[ERRO] Não foi possível criar diretório de backup: {e}")
                return False
        
        # Obter informações do trimestre atual
        quarter_info = get_quarter_info()
        quarter = quarter_info["quarter"]
        month_name = quarter_info["month_name"]
        year = quarter_info["year"]
        
        # Criar nome do arquivo de backup no formato: mês_ano_trimestretrimestre.db
        backup_filename = f"{month_name}_{year}_{quarter}ºtrimestre.db"
        backup_file = os.path.join(backup_dir, backup_filename)
        
        # Fazer backup (sobrescreve o arquivo anterior do mesmo trimestre)
        try:
            shutil.copy2(db_path, backup_file)
            print(f"[OK] Backup criado com sucesso:")
            print(f"     - {backup_file}")
            print(f"     - Trimestre: {quarter}º ({month_name} {year})")
            return True
        except Exception as e:
            print(f"[ERRO] Falha ao criar backup: {e}")
            return False
    except Exception as e:
        print(f"[ERRO] Erro ao criar backup: {e}")
        return False

def ensure_backup_exists():
    """Ensure that a backup of the database exists with quarterly naming"""
    if not Config.ENABLE_AUTO_BACKUP:
        return

    backup_dir = get_backup_dir()
    db_path = get_database_path()

    # Create backup directory if it doesn't exist
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except Exception as e:
            print(f"[AVISO] Não foi possível criar diretório de backup: {e}")
            return

    # If database exists, create/update backup using quarterly naming
    if db_path and os.path.exists(db_path):
        # Obter informações do trimestre atual
        quarter_info = get_quarter_info()
        quarter = quarter_info["quarter"]
        month_name = quarter_info["month_name"]
        year = quarter_info["year"]
        
        # Criar nome do arquivo de backup no formato: mês_ano_trimestretrimestre.db
        backup_filename = f"{month_name}_{year}_{quarter}ºtrimestre.db"
        backup_file = os.path.join(backup_dir, backup_filename)
        
        # Se o backup não existe ou o banco foi modificado, criar/atualizar
        if not os.path.exists(backup_file) or (
            os.path.getmtime(db_path) > os.path.getmtime(backup_file)
        ):
            try:
                shutil.copy2(db_path, backup_file)
                print(f"[OK] Backup criado/atualizado em: {backup_file}")
            except Exception as e:
                print(f"[AVISO] Não foi possível criar backup: {e}")


def create_app(config_class=Config):
    if hasattr(config_class, "validate") and callable(getattr(config_class, "validate")):
        config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)



    # Add custom filter for currency formatting
    app.jinja_env.filters["currency"] = format_currency
    configure_logging(app)

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
    from routes.conta import conta_bp
    from routes.investimento import investimento_bp
    from routes.tipo_investimento import tipo_investimento_bp
    from routes.tipo_conta import tipo_conta_bp
    
    # Importar e aplicar middleware de compatibilidade entre navegadores
    try:
        from app.middleware import browser_compatibility_middleware
        app = browser_compatibility_middleware(app)
        print("[OK] Middleware de compatibilidade entre navegadores aplicado")
    except ImportError:
        print("[AVISO] Middleware de compatibilidade não encontrado, continuando...")

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(transaction_bp, url_prefix="/transactions", name="transaction")
    app.register_blueprint(conta_bp, url_prefix="/conta")
    app.register_blueprint(investimento_bp, url_prefix="/investimento")
    app.register_blueprint(tipo_investimento_bp, url_prefix="/tipo-investimento")
    app.register_blueprint(tipo_conta_bp, url_prefix="/tipo-conta")

    # Rota de debug para compatibilidade entre navegadores
    @app.route("/debug/browser")
    def debug_browser():
        """Rota para debug de compatibilidade entre navegadores"""
        from flask import request, session, jsonify
        import re
        
        user_agent = request.headers.get('User-Agent', '')
        browser_info = {
            'user_agent': user_agent,
            'browser': 'unknown',
            'version': 'unknown',
            'os': 'unknown',
            'cookies_enabled': request.cookies is not None,
            'session_active': 'user_id' in session,
            'flask_login_active': False
        }
        
        # Detectar navegador
        if 'Firefox' in user_agent:
            browser_info['browser'] = 'Firefox'
            match = re.search(r'Firefox/(\d+)', user_agent)
            if match:
                browser_info['browser_version'] = match.group(1)
        elif 'Chrome' in user_agent:
            browser_info['browser'] = 'Chrome'
            match = re.search(r'Chrome/(\d+)', user_agent)
            if match:
                browser_info['browser_version'] = match.group(1)
        elif 'Edge' in user_agent:
            browser_info['browser'] = 'Edge'
            match = re.search(r'Edge/(\d+)', user_agent)
            if match:
                browser_info['browser_version'] = match.group(1)
        
        # Detectar sistema operacional
        if 'Windows' in user_agent:
            browser_info['os'] = 'Windows'
        elif 'Mac' in user_agent:
            browser_info['os'] = 'macOS'
        elif 'Linux' in user_agent:
            browser_info['os'] = 'Linux'
        
        return jsonify(browser_info)

    # Rotas específicas para favicon
    @app.route('/favicon.ico')
    def favicon():
        from flask import Response, send_file
        import os
        try:
            favicon_path = os.path.join(app.static_folder, 'img', 'favicon', 'favicon.ico')
            if os.path.exists(favicon_path):
                response = send_file(favicon_path, mimetype='image/x-icon')
                response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 ano
                return response
            else:
                return Response(status=404)
        except Exception as e:
            print(f"Erro ao servir favicon: {e}")
            return Response(status=404)
    
    @app.route('/static/img/favicon/favicon.ico')
    def favicon_static():
        from flask import Response, send_file
        import os
        try:
            favicon_path = os.path.join(app.static_folder, 'img', 'favicon', 'favicon.ico')
            if os.path.exists(favicon_path):
                response = send_file(favicon_path, mimetype='image/x-icon')
                response.headers['Cache-Control'] = 'public, max-age=31536000'  # Cache por 1 ano
                return response
            else:
                return Response(status=404)
        except Exception as e:
            print(f"Erro ao servir favicon estático: {e}")
            return Response(status=404)

    # Rota para encerrar o servidor
    @app.route("/shutdown", methods=["GET"])
    def shutdown():
        """Rota para encerrar o sistema com backup automático"""
        # Criar backup antes de encerrar
        try:
            print("[INFO] Criando backup do banco de dados antes de encerrar...")
            if create_backup():
                print("[OK] Backup criado com sucesso!")
            else:
                print("[AVISO] Não foi possível criar backup automaticamente")
        except Exception as e:
            print(f"[AVISO] Erro ao criar backup: {e}")
        """Rota para encerrar o servidor"""
        try:
            # Retornar resposta primeiro para permitir que o navegador feche
            from flask import jsonify
            response = jsonify({"message": "Encerrando o servidor...", "status": "ok"})
            
            # Agendar o shutdown para depois da resposta ser enviada
            # Aguardar mais tempo para dar chance do navegador fechar primeiro
            def delayed_shutdown():
                import time
                import os
                import signal
                import subprocess
                
                # Tentar importar psutil, se não estiver disponível usar métodos alternativos
                try:
                    import psutil
                    psutil_available = True
                except ImportError:
                    psutil_available = False
                    print("psutil não disponível, usando métodos alternativos...")
                
                browser_runtime_file = os.path.join(app.instance_path, 'runtime', 'browser_runtime.json')

                def close_tracked_browser():
                    import json
                    import shutil

                    if not os.path.exists(browser_runtime_file):
                        print('[INFO] Nenhum navegador gerenciado para encerrar.')
                        return

                    try:
                        with open(browser_runtime_file, 'r', encoding='utf-8') as runtime_handle:
                            metadata = json.load(runtime_handle)
                    except Exception as browser_read_error:
                        print(f'[AVISO] Nao foi possivel ler dados do navegador gerenciado: {browser_read_error}')
                        metadata = {}

                    browser_pid = int(metadata.get('pid') or 0)
                    profile_dir = metadata.get('profile_dir')

                    if browser_pid > 0:
                        try:
                            print(f'[INFO] Fechando navegador gerenciado (PID {browser_pid})...')
                            if os.name == 'nt':
                                subprocess.run(
                                    ['taskkill', '/F', '/T', '/PID', str(browser_pid)],
                                    capture_output=True,
                                    timeout=5,
                                    shell=False,
                                )
                            else:
                                os.kill(browser_pid, signal.SIGTERM)
                            print('[OK] Navegador encerrado com sucesso')
                        except Exception as browser_kill_error:
                            print(f'[AVISO] Nao foi possivel encerrar o navegador gerenciado: {browser_kill_error}')

                    if profile_dir:
                        shutil.rmtree(profile_dir, ignore_errors=True)

                    try:
                        os.remove(browser_runtime_file)
                    except OSError:
                        pass

                time.sleep(0.5)  # Aguardar a resposta HTTP sair
                close_tracked_browser()
                print("[INFO] Fechando CMD...")
                time.sleep(0.2)

                print("Encerrando o servidor...")
                
                # No Windows, fechar o CMD de forma rápida e direta
                if os.name == 'nt':  # Windows
                    try:
                        # Estratégia RÁPIDA: Fechar CMD pai diretamente
                        try:
                            if psutil_available:
                                current_process = psutil.Process()
                                parent = current_process.parent()
                                
                                if parent and 'cmd.exe' in parent.name().lower():
                                    print(f"Fechando CMD pai (PID {parent.pid})...")
                                    # Fechar diretamente sem esperar
                                    try:
                                        parent.kill()  # Usar kill diretamente para ser mais rápido
                                        print("CMD fechado com sucesso")
                                    except Exception as e:
                                        print(f"Erro ao fechar CMD: {e}")
                            else:
                                # Método alternativo sem psutil - usar taskkill diretamente
                                parent_pid = os.getppid()
                                if parent_pid > 0:
                                    print(f"Fechando CMD pai (PID {parent_pid})...")
                                    try:
                                        # Usar taskkill /f diretamente para fechar rapidamente
                                        subprocess.run(['taskkill', '/f', '/pid', str(parent_pid)], 
                                                      capture_output=True, shell=True, timeout=1)
                                        print("CMD fechado com sucesso")
                                    except Exception as e:
                                        print(f"Erro ao fechar CMD: {e}")
                        except Exception as e:
                            print(f"Erro ao fechar CMD pai: {e}")
                        
                        # Estratégia RÁPIDA 2: Se a primeira falhou, usar taskkill direto
                        try:
                            # Fechar diretamente todos os CMDs relacionados ao Python
                            subprocess.run(['taskkill', '/f', '/im', 'cmd.exe'], 
                                          capture_output=True, shell=True, timeout=0.5)
                        except Exception as e:
                            pass  # Ignorar erros silenciosamente
                        
                        # Forçar saída imediata
                        os._exit(0)
                            
                    except Exception as e:
                        print(f"Erro geral no shutdown: {e}")
                        os._exit(0)
                
                # Para outros sistemas
                else:
                    print("Sistema não Windows, encerrando...")
                    os._exit(0)
            
            # Executar shutdown em thread separada
            import threading
            shutdown_thread = threading.Thread(target=delayed_shutdown)
            shutdown_thread.daemon = True
            shutdown_thread.start()
            
            return response, 200
        except Exception as e:
            print(f"Erro na rota shutdown: {e}")
            return jsonify({"error": str(e)}), 500

    # Adicione o context processor dentro da função create_app
    @app.context_processor
    def inject_now():
        return {"now": datetime.utcnow(), "datetime": datetime}

    with app.app_context():
        db.create_all()
        _ensure_user_scoped_lookup_columns()

        from app.models import User

        if User.query.count() == 0:
            admin_user = User(
                username="admin",
                email="admin@sistema.com",
                password_hash="pbkdf2:sha256:260000$dummy$dummy",
            )
            admin_user.set_password("admin123")
            db.session.add(admin_user)
            print("Usuário admin criado com sucesso!")

        try:
            db.session.commit()
            print("Usuário admin commitado com sucesso!")
        except Exception as e:
            print(f"Erro ao commitar usuário admin: {str(e)}")
            db.session.rollback()

        _migrate_lookup_records_to_user_scope()

        users = User.query.all()
        for user in users:
            initialize_user_default_data(user)

        repair_user_visible_text_data()
        repair_default_lookup_data()

    return app


