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
        """Rota para encerrar o servidor"""
        try:
            # Retornar resposta primeiro
            from flask import jsonify
            response = jsonify({"message": "Encerrando o servidor..."})
            
            # Agendar o shutdown para depois da resposta ser enviada
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
                
                time.sleep(1)  # Aguardar 1 segundo
                
                print("Encerrando o servidor...")
                
                # No Windows, fechar o CMD
                if os.name == 'nt':  # Windows
                    try:
                        print("Tentando fechar o CMD...")
                        
                        # Estratégia 1: Identificar e fechar o CMD pai
                        try:
                            print("Estratégia 1: Identificando CMD pai...")
                            
                            if psutil_available:
                                current_process = psutil.Process()
                                parent = current_process.parent()
                                
                                if parent and 'cmd.exe' in parent.name().lower():
                                    print(f"CMD pai encontrado: PID {parent.pid}")
                                    
                                    # Tentar fechar o CMD pai graciosamente
                                    try:
                                        parent.terminate()
                                        parent.wait(timeout=3)
                                        print("CMD pai fechado com sucesso")
                                    except psutil.TimeoutExpired:
                                        print("Timeout ao fechar CMD pai, forçando...")
                                        parent.kill()
                                    except Exception as e:
                                        print(f"Erro ao fechar CMD pai: {e}")
                                        parent.kill()
                            else:
                                # Método alternativo sem psutil
                                parent_pid = os.getppid()
                                if parent_pid > 0:
                                    print(f"Tentando fechar processo pai PID: {parent_pid}")
                                    try:
                                        os.kill(parent_pid, signal.SIGTERM)
                                        time.sleep(2)
                                        # Se ainda estiver rodando, forçar
                                        os.kill(parent_pid, signal.SIGKILL)
                                    except Exception as e:
                                        print(f"Erro ao fechar processo pai: {e}")
                                    
                        except Exception as e:
                            print(f"Erro na estratégia 1: {e}")
                        
                        # Estratégia 2: Fechar todos os CMDs relacionados
                        try:
                            print("Estratégia 2: Fechando CMDs relacionados...")
                            
                            if psutil_available:
                                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                                    try:
                                        if 'cmd.exe' in proc.info['name'].lower():
                                            # Verificar se é o CMD que iniciou nossa aplicação
                                            cmdline = proc.info['cmdline']
                                            if cmdline and any('python' in arg.lower() for arg in cmdline):
                                                print(f"Fechando CMD da aplicação: PID {proc.info['pid']}")
                                                proc.terminate()
                                                proc.wait(timeout=2)
                                            elif proc.info['pid'] != os.getppid():
                                                print(f"Fechando CMD órfão: PID {proc.info['pid']}")
                                                proc.terminate()
                                                proc.wait(timeout=1)
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                                        continue
                                    except Exception as e:
                                        print(f"Erro ao processar processo: {e}")
                            else:
                                # Método alternativo sem psutil - usar taskkill mais agressivo
                                print("Usando taskkill AGGRESSIVO para fechar CMDs...")
                                try:
                                    # Primeiro: fechar CMDs específicos que executam Python
                                    result = subprocess.run(['tasklist', '/fi', 'imagename eq cmd.exe', '/fo', 'csv'], 
                                                          capture_output=True, shell=True, timeout=5, text=True)
                                    
                                    if result.returncode == 0:
                                        lines = result.stdout.strip().split('\n')[1:]  # Pular cabeçalho
                                        for line in lines:
                                            if line.strip():
                                                parts = line.split(',')
                                                if len(parts) >= 2:
                                                    pid = parts[1].strip('"')
                                                    try:
                                                        # Verificar se o CMD executa Python
                                                        cmd_check = subprocess.run(['tasklist', '/fi', f'pid eq {pid}', '/fo', 'csv'], 
                                                                                capture_output=True, shell=True, timeout=2, text=True)
                                                        if 'python' in cmd_check.stdout.lower():
                                                            print(f"Fechando CMD Python PID: {pid}")
                                                            subprocess.run(['taskkill', '/f', '/pid', pid], 
                                                                          capture_output=True, shell=True, timeout=3)
                                                    except:
                                                        continue
                                    
                                    # Segundo: fechar TODOS os CMDs restantes
                                    print("Fechando TODOS os CMDs restantes...")
                                    subprocess.run(['taskkill', '/f', '/im', 'cmd.exe'], 
                                                  capture_output=True, shell=True, timeout=5)
                                    print("CMDs fechados via taskkill agressivo")
                                except Exception as e:
                                    print(f"Erro ao usar taskkill agressivo: {e}")
                                    
                        except Exception as e:
                            print(f"Erro na estratégia 2: {e}")
                        
                        # Estratégia 3: Fechar consoles relacionados
                        try:
                            print("Estratégia 3: Fechando consoles relacionados...")
                            
                            if psutil_available:
                                for proc in psutil.process_iter(['pid', 'name']):
                                    try:
                                        if 'conhost.exe' in proc.info['name'].lower():
                                            # Verificar se está relacionado ao nosso processo
                                            if proc.parent() and proc.parent().pid == os.getppid():
                                                print(f"Fechando console relacionado: PID {proc.info['pid']}")
                                                proc.terminate()
                                                proc.wait(timeout=1)
                                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.TimeoutExpired):
                                        continue
                                    except Exception as e:
                                        print(f"Erro ao processar console: {e}")
                            else:
                                # Método alternativo sem psutil
                                print("Usando taskkill para fechar consoles...")
                                try:
                                    subprocess.run(['taskkill', '/f', '/im', 'conhost.exe'], 
                                                  capture_output=True, shell=True, timeout=5)
                                    print("Consoles fechados via taskkill")
                                except Exception as e:
                                    print(f"Erro ao fechar consoles: {e}")
                                    
                        except Exception as e:
                            print(f"Erro na estratégia 3: {e}")
                        
                        # Estratégia 4: Script batch otimizado e mais agressivo
                        try:
                            print("Estratégia 4: Executando script final agressivo...")
                            batch_script = '''@echo off
title FECHANDO SISTEMA - AGUARDE
color 0C
cls
echo.
echo ========================================
echo    FECHANDO SISTEMA FINANCAS PESSOAIS
echo ========================================
echo.
echo Fechando CMD e processos Python...
echo.

REM Aguardar um momento para o servidor processar
timeout /t 1 /nobreak >nul

REM ESTRATÉGIA AGRESSIVA: Fechar TODOS os CMDs que executam Python
echo [1/4] Fechando CMDs da aplicacao...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq cmd.exe" /fo table /nh 2^>nul') do (
    echo Verificando CMD PID: %%i
    tasklist /fi "pid eq %%i" /fo table /nh 2^>nul | findstr /i "python" >nul 2^>nul
    if not errorlevel 1 (
        echo [FORÇANDO] Fechando CMD da aplicacao: PID %%i
        taskkill /f /pid %%i >nul 2>&1
        if errorlevel 1 (
            echo [ERRO] Nao foi possivel fechar PID %%i
        ) else (
            echo [SUCESSO] CMD PID %%i fechado
        )
    )
)

REM Fechar TODOS os processos Python (mais agressivo)
echo.
echo [2/4] Fechando TODOS os processos Python...
taskkill /f /im python.exe >nul 2>&1
if errorlevel 1 (
    echo [SUCESSO] Processos Python encerrados
) else (
    echo [INFO] Nenhum processo Python encontrado
)

REM Fechar TODOS os consoles relacionados
echo.
echo [3/4] Fechando TODOS os consoles...
taskkill /f /im conhost.exe >nul 2>&1
if errorlevel 1 (
    echo [SUCESSO] Consoles encerrados
) else (
    echo [INFO] Nenhum console encontrado
)

REM Estratégia adicional: Fechar navegadores
echo.
echo [4/6] Fechando navegadores...
echo Fechando Chrome...
taskkill /im chrome.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im chrome.exe >nul 2>&1

echo Fechando Firefox...
taskkill /im firefox.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im firefox.exe >nul 2>&1

echo Fechando Edge...
taskkill /im msedge.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im msedge.exe >nul 2>&1

echo Fechando Internet Explorer...
taskkill /im iexplore.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im iexplore.exe >nul 2>&1

echo Fechando Opera...
taskkill /im opera.exe >nul 2>&1
timeout /t 1 /nobreak >nul
taskkill /f /im opera.exe >nul 2>&1

REM ESTRATÉGIA FINAL: Forçar fechamento de qualquer CMD restante
echo.
echo [5/6] Estrategia final: fechando CMDs restantes...
taskkill /f /im cmd.exe >nul 2>&1

REM Limpeza final de processos órfãos
echo.
echo [6/6] Limpeza final de processos...
taskkill /f /im conhost.exe >nul 2>&1

REM Limpar arquivo temporário
echo.
echo Limpando arquivos temporarios...
del "%~f0" >nul 2>&1

echo.
echo ========================================
echo    SISTEMA ENCERRADO COM SUCESSO!
echo ========================================
echo.
echo Fechando esta janela automaticamente...
timeout /t 2 /nobreak >nul

REM Forçar fechamento da janela atual
exit
'''
                            with open("FECHAR_SISTEMA.bat", "w", encoding='utf-8') as f:
                                f.write(batch_script)
                            
                            # Executar script com privilégios elevados se possível
                            try:
                                # Tentar executar como administrador
                                subprocess.Popen(["FECHAR_SISTEMA.bat"], 
                                               shell=True, 
                                               creationflags=subprocess.CREATE_NEW_CONSOLE | subprocess.HIGH_PRIORITY_CLASS)
                                print("Script de fechamento executado com alta prioridade")
                            except:
                                # Fallback: executar normalmente
                                subprocess.Popen(["FECHAR_SISTEMA.bat"], 
                                               shell=True, 
                                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                                print("Script de fechamento executado normalmente")
                            
                            # Aguardar mais tempo para o script executar
                            time.sleep(5)
                            try:
                                os.remove("FECHAR_SISTEMA.bat")
                            except:
                                pass
                                
                        except Exception as e:
                            print(f"Erro na estratégia 4: {e}")
                        
                        # Estratégia 5: Usar script PowerShell dedicado para navegadores
                        try:
                            print("Estratégia 5: Usando script PowerShell para navegadores...")
                            
                            # Verificar se o script existe
                            if os.path.exists("FECHAR_NAVEGADORES.ps1"):
                                # Executar script PowerShell com privilégios elevados
                                subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'FECHAR_NAVEGADORES.ps1'], 
                                              capture_output=True, shell=True, timeout=15)
                                print("Script de navegadores executado")
                            else:
                                print("Script FECHAR_NAVEGADORES.ps1 não encontrado")
                                
                        except Exception as e:
                            print(f"Erro na estratégia 5: {e}")
                        
                        # Estratégia 5.5: Método alternativo usando PowerShell inline
                        try:
                            print("Estratégia 5.5: Usando PowerShell inline para fechar CMD...")
                            powershell_script = '''
Get-Process | Where-Object {$_.ProcessName -eq "cmd" -or $_.ProcessName -eq "conhost"} | ForEach-Object {
    try {
        $_.Kill()
        Write-Host "Processo $($_.ProcessName) PID $($_.Id) fechado"
    } catch {
        Write-Host "Erro ao fechar $($_.ProcessName) PID $($_.Id): $_"
    }
}
Get-Process | Where-Object {$_.ProcessName -eq "python"} | ForEach-Object {
    try {
        $_.Kill()
        Write-Host "Processo Python PID $($_.Id) fechado"
    } catch {
        Write-Host "Erro ao fechar Python PID $($_.Id): $_"
    }
}
'''
                            with open("FECHAR_POWERSHELL.ps1", "w", encoding='utf-8') as f:
                                f.write(powershell_script)
                            
                            # Executar PowerShell
                            subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', 'FECHAR_POWERSHELL.ps1'], 
                                          capture_output=True, shell=True, timeout=10)
                            
                            # Limpar arquivo
                            try:
                                os.remove("FECHAR_POWERSHELL.ps1")
                            except:
                                pass
                                
                        except Exception as e:
                            print(f"Erro na estratégia 5.5: {e}")
                        
                        # Estratégia 6: Usar script batch dedicado para navegadores
                        try:
                            print("Estratégia 6: Usando script batch para navegadores...")
                            
                            # Verificar se o script existe
                            if os.path.exists("FECHAR_NAVEGADORES.bat"):
                                # Executar script batch
                                subprocess.Popen(["FECHAR_NAVEGADORES.bat"], 
                                               shell=True, 
                                               creationflags=subprocess.CREATE_NEW_CONSOLE)
                                print("Script batch de navegadores executado")
                                time.sleep(3)  # Aguardar execução
                            else:
                                print("Script FECHAR_NAVEGADORES.bat não encontrado")
                                
                        except Exception as e:
                            print(f"Erro na estratégia 6: {e}")
                        
                        # Estratégia 6.5: Fechar janelas do navegador manualmente
                        try:
                            print("Estratégia 6.5: Fechando janelas do navegador manualmente...")
                            
                            # Lista de navegadores comuns
                            browsers = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'iexplore.exe', 'opera.exe', 'brave.exe', 'vivaldi.exe']
                            
                            for browser in browsers:
                                try:
                                    # Verificar se o navegador está rodando
                                    result = subprocess.run(['tasklist', '/fi', f'imagename eq {browser}', '/fo', 'csv'], 
                                                          capture_output=True, shell=True, timeout=3, text=True)
                                    
                                    if result.returncode == 0 and browser in result.stdout.lower():
                                        print(f"Fechando {browser}...")
                                        
                                        # Tentar fechar graciosamente primeiro
                                        subprocess.run(['taskkill', '/im', browser], 
                                                      capture_output=True, shell=True, timeout=5)
                                        
                                        # Aguardar um pouco
                                        time.sleep(2)
                                        
                                        # Se ainda estiver rodando, forçar fechamento
                                        subprocess.run(['taskkill', '/f', '/im', browser], 
                                                      capture_output=True, shell=True, timeout=5)
                                        
                                        print(f"{browser} fechado")
                                        
                                except Exception as e:
                                    print(f"Erro ao fechar {browser}: {e}")
                                    continue
                                    
                        except Exception as e:
                            print(f"Erro na estratégia 6.5: {e}")
                        
                        # Estratégia 7: Forçar saída final
                        try:
                            print("Estratégia 7: Finalizando processo...")
                            time.sleep(3)
                            
                            # Última tentativa: usar taskkill diretamente
                            subprocess.run(['taskkill', '/f', '/im', 'cmd.exe'], 
                                          capture_output=True, shell=True, timeout=5)
                            
                            os._exit(0)
                        except Exception as e:
                            print(f"Erro na estratégia 7: {e}")
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
