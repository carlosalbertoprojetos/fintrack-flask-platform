from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from datetime import datetime, timedelta
from config import Config
from flask_mail import Mail
import os
import shutil

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
mail = Mail()


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
    """Inicializa TODOS os dados padrão para um novo usuário"""
    try:
        from app.models import TipoConta, TipoInvestimento, Conta, Category, PaymentMethod, Expense
        
        # 1. CRIAR CATEGORIAS PADRÃO (se não existirem globalmente)
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
            # Verificar se a categoria já existe globalmente
            existing_category = Category.query.filter_by(name=category_data["name"]).first()
            if not existing_category:
                category = Category(**category_data)
                db.session.add(category)
        
        # 2. CRIAR FORMAS DE PAGAMENTO PADRÃO (se não existirem globalmente)
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
            # Verificar se a forma de pagamento já existe globalmente
            existing_payment = PaymentMethod.query.filter_by(name=payment_data["name"]).first()
            if not existing_payment:
                payment = PaymentMethod(**payment_data)
                db.session.add(payment)
        
        # 3. CRIAR DESPESAS PADRÃO (se não existirem globalmente)
        expensives_data = [
            {"name": "CDB", "category_id": "Investimentos"},
            {"name": "Ações", "category_id": "Investimentos"},
            {"name": "Fundos", "category_id": "Investimentos"},
            {"name": "Supermercado", "category_id": "Alimentação"},
            {"name": "Restaurante", "category_id": "Alimentação"},
            {"name": "Aluguel", "category_id": "Moradia"},
            {"name": "Condomínio", "category_id": "Moradia"},
            {"name": "IPTU", "category_id": "Moradia"},
            {"name": "Combustível", "category_id": "Transporte"},
            {"name": "Manutenção", "category_id": "Transporte"},
            {"name": "Farmácia", "category_id": "Saúde"},
            {"name": "Médico", "category_id": "Saúde"},
            {"name": "Curso", "category_id": "Educação"},
            {"name": "Material", "category_id": "Educação"},
            {"name": "Internet", "category_id": "Serviços"},
            {"name": "Telefone", "category_id": "Serviços"},
            {"name": "Energia", "category_id": "Serviços"},
            {"name": "Água", "category_id": "Serviços"},
            {"name": "Gás", "category_id": "Serviços"},
            {"name": "Roupas", "category_id": "Compras"},
            {"name": "Eletrônicos", "category_id": "Compras"},
        ]
        
        for expensive_data in expensives_data:
            # Verificar se a despesa já existe globalmente
            existing_expense = Expense.query.filter_by(name=expensive_data["name"]).first()
            if not existing_expense:
                category = Category.query.filter_by(name=expensive_data["category_id"]).first()
                if category:
                    expense = Expense(name=expensive_data["name"], category_id=category.id)
                    db.session.add(expense)
        
        # 4. CRIAR TIPOS DE CONTA PARA O USUÁRIO
        tipos_conta_data = [
            {"nome": "Banco Físico", "descricao": "Físico", "ativo": True},
            {"nome": "Banco Virtual", "descricao": "Virtual", "ativo": True},
            {"nome": "Investimento", "descricao": "Corretora", "ativo": True},
        ]
        
        for tipo_data in tipos_conta_data:
            # Verificar se o tipo já existe para este usuário
            existing_tipo = TipoConta.query.filter_by(
                nome=tipo_data["nome"], 
                user_id=user.id
            ).first()
            
            if not existing_tipo:
                tipo_conta = TipoConta(
                    nome=tipo_data["nome"],
                    descricao=tipo_data["descricao"],
                    ativo=tipo_data["ativo"],
                    user_id=user.id
                )
                db.session.add(tipo_conta)
        
        # 5. CRIAR TIPOS DE INVESTIMENTO PARA O USUÁRIO
        tipos_investimento_data = [
            {"nome": "CDB", "descricao": "Certificado de Depósito Bancário", "ativo": True},
            {"nome": "Ações", "descricao": "Investimento em ações", "ativo": True},
            {"nome": "Fundos", "descricao": "Fundos de investimento", "ativo": True},
            {"nome": "Tesouro Direto", "descricao": "Títulos públicos", "ativo": True},
            {"nome": "Poupança", "descricao": "Conta poupança", "ativo": True},
        ]
        
        for tipo_data in tipos_investimento_data:
            # Verificar se o tipo já existe para este usuário
            existing_tipo = TipoInvestimento.query.filter_by(
                nome=tipo_data["nome"], 
                user_id=user.id
            ).first()
            
            if not existing_tipo:
                tipo_investimento = TipoInvestimento(
                    nome=tipo_data["nome"],
                    descricao=tipo_data["descricao"],
                    ativo=tipo_data["ativo"],
                    user_id=user.id
                )
                db.session.add(tipo_investimento)
        
        # Fazer commit dos tipos e dados globais
        db.session.commit()
        
        # 6. CRIAR CONTAS PADRÃO PARA O USUÁRIO (apenas se não houver nenhuma conta)
        # Verificar se o usuário já tem alguma conta
        existing_contas_count = Conta.query.filter_by(user_id=user.id).count()
        
        # Só criar contas padrão se o usuário não tiver nenhuma conta
        if existing_contas_count == 0:
            tipo_banco_fisico = TipoConta.query.filter_by(
                nome="Banco Físico", 
                user_id=user.id
            ).first()
            
            tipo_banco_virtual = TipoConta.query.filter_by(
                nome="Banco Virtual", 
                user_id=user.id
            ).first()
            
            contas_data = [
                {
                    "nome": "Inter", 
                    "tipo_id": tipo_banco_virtual.id if tipo_banco_virtual else None,
                    "saldo_inicial": 0.00,
                    "saldo_atual": 0.00
                },
                {
                    "nome": "Banco do Brasil", 
                    "tipo_id": tipo_banco_fisico.id if tipo_banco_fisico else None,
                    "saldo_inicial": 0.00,
                    "saldo_atual": 0.00
                },
            ]
            
            for conta_data in contas_data:
                if conta_data["tipo_id"]:
                    # Verificar se a conta já existe para este usuário (verificação adicional)
                    existing_conta = Conta.query.filter_by(
                        nome=conta_data["nome"], 
                        user_id=user.id
                    ).first()
                    
                    if not existing_conta:
                        conta = Conta(
                            nome=conta_data["nome"],
                            tipo_id=conta_data["tipo_id"],
                            saldo_inicial=conta_data["saldo_inicial"],
                            saldo_atual=conta_data["saldo_atual"],
                            user_id=user.id
                        )
                        db.session.add(conta)
        
        # Commit final
        db.session.commit()
        print(f"TODOS os dados padrão criados com sucesso para o usuário {user.username}!")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar dados padrão para o usuário {user.username}: {str(e)}")
        return False


def get_database_path():
    """Retorna o caminho do banco de dados"""
    from config import Config
    db_uri = Config.SQLALCHEMY_DATABASE_URI
    if db_uri.startswith('sqlite:///'):
        db_path = db_uri.replace('sqlite:///', '')
        return db_path
    return None

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
        db_path = get_database_path()
        if not db_path or not os.path.exists(db_path):
            print("[AVISO] Banco de dados não encontrado para backup")
            return False
        
        # Criar diretório de backup
        backup_dir = r"C:\backup"
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
    backup_dir = r"C:\backup"
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
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.config.from_mapping(DEBUG=True)
    # Configurações de sessão para compatibilidade entre navegadores
    app.config['SESSION_COOKIE_SECURE'] = False  # True apenas se usar HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
    
    # Configurações de cookies para compatibilidade
    app.config['REMEMBER_COOKIE_SECURE'] = False  # True apenas se usar HTTPS
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True


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
                
                print("[INFO] Fechando CMD...")
                time.sleep(0.5)  # Aguardar apenas 0.5 segundos
                
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

        # Importar Category aqui para evitar importação circular
        from app.models import Category, PaymentMethod, Expense

        # Adicionar categorias padrão apenas se não houver nenhuma
        if Category.query.count() == 0:
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
                category = Category(**category_data)
                db.session.add(category)

        # Adicionar formas de pagamento padrão apenas se não houver nenhuma
        if PaymentMethod.query.count() == 0:
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
                db.session.add(PaymentMethod(**payment_data))

        # Adicionar despesas padrão apenas se não houver nenhuma
        if Expense.query.count() == 0:
            expensives_data = [
                {"name": "CDB", "category_id": "Investimentos"},
                {"name": "Ações", "category_id": "Investimentos"},
                {"name": "Fundos", "category_id": "Investimentos"},
                {"name": "Supermercado", "category_id": "Alimentação"},
                {"name": "Restaurante", "category_id": "Alimentação"},
                {"name": "Aluguel", "category_id": "Moradia"},
                {"name": "Condomínio", "category_id": "Moradia"},
                {"name": "IPTU", "category_id": "Moradia"},
                {"name": "Combustível", "category_id": "Transporte"},
                {"name": "Manutenção", "category_id": "Transporte"},
                {"name": "Farmácia", "category_id": "Saúde"},
                {"name": "Médico", "category_id": "Saúde"},
                {"name": "Curso", "category_id": "Educação"},
                {"name": "Material", "category_id": "Educação"},
                {"name": "Internet", "category_id": "Serviços"},
                {"name": "Telefone", "category_id": "Serviços"},
                {"name": "Energia", "category_id": "Serviços"},
                {"name": "Água", "category_id": "Serviços"},
                {"name": "Gás", "category_id": "Serviços"},
                {"name": "Roupas", "category_id": "Compras"},
                {"name": "Eletrônicos", "category_id": "Compras"},
            ]
            for expensive_data in expensives_data:
                category = Category.query.filter_by(name=expensive_data["category_id"]).first()
                if not category:
                    continue
                expense = Expense(name=expensive_data["name"], category_id=category.id)
                db.session.add(expense)

        # Criar usuário padrão se não existir nenhum
        from app.models import User
        if User.query.count() == 0:
            admin_user = User(
                username="admin",
                email="admin@sistema.com",
                password_hash="pbkdf2:sha256:260000$dummy$dummy"  # Senha temporária
            )
            admin_user.set_password("admin123")  # Senha padrão
            db.session.add(admin_user)
            print("Usuário admin criado com sucesso!")

        # Fazer commit do usuário primeiro para garantir que ele existe
        try:
            db.session.commit()
            print("Usuário admin commitado com sucesso!")
        except Exception as e:
            print(f"Erro ao commitar usuário admin: {str(e)}")
            db.session.rollback()

        # Inicializar dados padrão para usuários existentes (apenas na primeira execução)
        users = User.query.all()
        for user in users:
            initialize_user_default_data(user)

    return app
