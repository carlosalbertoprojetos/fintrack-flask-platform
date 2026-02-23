import os
import sys
import webbrowser
import time
import threading
import signal
import atexit
from app import create_app, db, create_backup
from flask_migrate import Migrate

MIN_PYTHON = (3, 10)


def check_python_version():
    """Valida se a versao minima do Python foi atendida."""
    if sys.version_info < MIN_PYTHON:
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        required = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        print(f"[ERRO] Python {required}+ e obrigatorio. Versao atual: {current}")
        sys.exit(1)

def minimize_console():
    """Minimiza a janela do console"""
    try:
        import ctypes
        from ctypes import wintypes
        
        # Obter handle da janela do console
        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32
        
        # Encontrar a janela do console atual
        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            # Tentar minimizar usando ShowWindow
            result = user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE = 6
            if result:
                return True
            
            # Se ShowWindow não funcionou, tentar IsIconic e depois ShowWindow
            is_minimized = user32.IsIconic(hwnd)
            if not is_minimized:
                # Forçar minimização
                user32.ShowWindow(hwnd, 2)  # SW_MINIMIZE = 2 (alternativa)
                time.sleep(0.1)
                user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE = 6
                return True
    except Exception as e:
        print(f"[DEBUG] Erro no método ctypes: {e}")
    
    # Método alternativo: encontrar janela pelo título
    try:
        import ctypes
        from ctypes import wintypes
        
        def enum_windows_callback(hwnd, lParam):
            window_text = ctypes.create_unicode_buffer(512)
            user32 = ctypes.windll.user32
            user32.GetWindowTextW(hwnd, window_text, 512)
            if "Sistema de Finanças Pessoais" in window_text.value:
                user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
                return False
            return True
        
        EnumWindows = ctypes.windll.user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        EnumWindows(EnumWindowsProc(enum_windows_callback), 0)
        return True
    except Exception as e:
        print(f"[DEBUG] Erro no método EnumWindows: {e}")
    
    # Último recurso: usar PowerShell com método mais direto
    try:
        import subprocess
        script = '''
        Add-Type @"
        using System;
        using System.Runtime.InteropServices;
        public class Win32 {
            [DllImport("user32.dll")]
            public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
            [DllImport("kernel32.dll")]
            public static extern IntPtr GetConsoleWindow();
        }
"@
        $hwnd = [Win32]::GetConsoleWindow()
        if ($hwnd -ne [IntPtr]::Zero) {
            [Win32]::ShowWindow($hwnd, 6)
        }
        '''
        subprocess.run(
            ['powershell', '-Command', script],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=2
        )
        return True
    except Exception as e:
        print(f"[DEBUG] Erro no método PowerShell: {e}")
    
    return False

def minimize_and_open_browser():
    """Minimiza a janela do CMD e depois abre o navegador"""
    # Aguardar tempo suficiente para Flask exibir todas as mensagens de inicialização
    time.sleep(5)  # Aguardar servidor iniciar completamente e exibir todas as mensagens
    
    # Primeiro: Minimizar janela do CMD
    print("[INFO] Minimizando janela do CMD...")
    minimized = False
    for attempt in range(3):
        if minimize_console():
            print("[OK] Janela do CMD minimizada")
            minimized = True
            break
        time.sleep(0.3)
    
    if not minimized:
        print("[AVISO] Não foi possível minimizar a janela automaticamente")
    
    # Aguardar um pouco para garantir que a minimização foi processada
    time.sleep(0.5)
    
    # Depois: Abrir navegador
    try:
        # Abrir diretamente na página de login
        webbrowser.open('http://127.0.0.1:5000/auth/login')
        print("[OK] Navegador aberto automaticamente na tela de login")
    except Exception as e:
        print(f"[AVISO] Não foi possível abrir o navegador automaticamente: {e}")
        print("[INFO] Acesse manualmente: http://127.0.0.1:5000/auth/login")

def backup_on_exit():
    """Função chamada ao encerrar o sistema para fazer backup"""
    print()
    print("[INFO] Criando backup do banco de dados...")
    if create_backup():
        print("[OK] Backup concluído com sucesso!")
    else:
        print("[AVISO] Não foi possível criar backup automaticamente")
    print()

if __name__ == "__main__":
    check_python_version()
    # Registrar função de backup para diferentes formas de encerramento
    atexit.register(backup_on_exit)
    
    # Registrar handlers de sinal para capturar Ctrl+C e outros sinais
    def signal_handler(signum, frame):
        backup_on_exit()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
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
        
        # Minimizar CMD e abrir navegador em thread separada
        browser_thread = threading.Thread(target=minimize_and_open_browser, daemon=True)
        browser_thread.start()
        
        # Iniciar servidor Flask
        # Nota: app.run() é bloqueante, então a minimização acontecerá na thread do navegador
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=False,
            use_reloader=False  # Desabilitar reloader para evitar duplicação
        )
        
    except KeyboardInterrupt:
        print()
        print("[INFO] Encerrando sistema...")
        backup_on_exit()
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
        # Tentar fazer backup mesmo em caso de erro
        try:
            backup_on_exit()
        except:
            pass
        print("[INFO] Pressione Enter para sair...")
        input()
        sys.exit(1)
