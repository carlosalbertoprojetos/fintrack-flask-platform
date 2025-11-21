import os
import sys
import webbrowser
import time
import threading
from app import create_app, db
from flask_migrate import Migrate

def open_browser():
    """Abre o navegador após o servidor iniciar"""
    time.sleep(2)  # Aguarda 2 segundos para o servidor iniciar
    try:
        webbrowser.open('http://127.0.0.1:5000')
        print("[OK] Navegador aberto automaticamente")
    except Exception as e:
        print(f"[AVISO] Não foi possível abrir o navegador automaticamente: {e}")
        print("[INFO] Acesse manualmente: http://127.0.0.1:5000")

if __name__ == "__main__":
    try:
        print("=" * 60)
        print("  SISTEMA DE FINANÇAS PESSOAIS")
        print("=" * 60)
        print()
        print("[INFO] Inicializando aplicação...")
        
        # Criar aplicação
        app = create_app()
        
        # Configurar Migrate
        migrate = Migrate(app, db)
        
        # Verificar e inicializar banco de dados
        with app.app_context():
            try:
                print("[INFO] Verificando banco de dados...")
                
                # Criar todas as tabelas
                db.create_all()
                
                # Importar modelos necessários
                from app.models import User, Conta, Category, PaymentMethod, Expense
                
                # Verificar se há usuários no sistema
                user_count = User.query.count()
                print(f"[INFO] Usuários cadastrados: {user_count}")
                
                # Se houver usuários, tentar recalcular saldos das contas
                if user_count > 0:
                    try:
                        conta_count = Conta.query.count()
                        if conta_count > 0:
                            print(f"[INFO] Recalculando saldos de {conta_count} contas...")
                            Conta.recalcular_saldos()
                            print("[OK] Saldos recalculados com sucesso")
                        else:
                            print("[INFO] Nenhuma conta encontrada para recalcular")
                    except Exception as e:
                        print(f"[AVISO] Não foi possível recalcular saldos: {e}")
                
                print("[OK] Banco de dados verificado e pronto")
                
            except Exception as e:
                print(f"[ERRO] Falha ao verificar banco de dados: {e}")
                print("[INFO] Tentando continuar...")
        
        print()
        print("[OK] Aplicação inicializada com sucesso!")
        print()
        print("=" * 60)
        print("  SERVIDOR INICIADO")
        print("=" * 60)
        print()
        print("  URL: http://127.0.0.1:5000")
        print()
        print("  Credenciais padrão (se for o primeiro acesso):")
        print("    Usuário: admin")
        print("    Senha: admin123")
        print()
        print("  Para encerrar o sistema:")
        print("    - Pressione Ctrl+C nesta janela, ou")
        print("    - Use o botão 'Encerrar Sistema' na interface")
        print()
        print("=" * 60)
        print()
        
        # Abrir navegador em thread separada
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
        
        # Iniciar servidor Flask
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False  # Desabilitar reloader para evitar duplicação
        )
        
    except KeyboardInterrupt:
        print()
        print("[INFO] Encerrando sistema...")
        print("[OK] Sistema encerrado com sucesso!")
        sys.exit(0)
        
    except Exception as e:
        print()
        print(f"[ERRO] Erro ao iniciar sistema: {e}")
        print()
        print("[INFO] Detalhes do erro:")
        import traceback
        traceback.print_exc()
        print()
        print("[INFO] Pressione Enter para sair...")
        input()
        sys.exit(1)
