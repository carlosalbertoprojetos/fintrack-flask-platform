import atexit
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from pathlib import Path

from app import create_app, create_backup, db
from flask_migrate import Migrate

MIN_PYTHON = (3, 10)
DEFAULT_APP_URL = "http://127.0.0.1:5000/auth/login"
BROWSER_RUNTIME_FILE = "browser_runtime.json"
WINDOWS_BROWSER_PATHS = (
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)


def check_python_version():
    """Valida se a versao minima do Python foi atendida."""
    if sys.version_info < MIN_PYTHON:
        current = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        required = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
        print(f"[ERRO] Python {required}+ e obrigatorio. Versao atual: {current}")
        sys.exit(1)


def get_project_dir():
    return Path(__file__).resolve().parent


def get_runtime_dir(base_dir=None):
    root_dir = Path(base_dir) if base_dir else get_project_dir() / "instance" / "runtime"
    root_dir.mkdir(parents=True, exist_ok=True)
    return root_dir


def get_browser_runtime_file(base_dir=None):
    return get_runtime_dir(base_dir) / BROWSER_RUNTIME_FILE


def read_browser_runtime(runtime_file=None):
    runtime_path = Path(runtime_file) if runtime_file else get_browser_runtime_file()
    if not runtime_path.exists():
        return None

    try:
        return json.loads(runtime_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def write_browser_runtime(runtime_file, browser_path, pid, profile_dir, url):
    runtime_path = Path(runtime_file)
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "browser_path": str(browser_path),
        "pid": int(pid),
        "profile_dir": str(profile_dir),
        "url": url,
    }
    runtime_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def cleanup_browser_runtime(runtime_file=None):
    runtime_path = Path(runtime_file) if runtime_file else get_browser_runtime_file()
    metadata = read_browser_runtime(runtime_path)

    if metadata:
        profile_dir = metadata.get("profile_dir")
        if profile_dir:
            shutil.rmtree(profile_dir, ignore_errors=True)

    try:
        runtime_path.unlink(missing_ok=True)
    except OSError:
        pass


def find_supported_browser():
    configured_browser = os.environ.get("SFP_BROWSER_PATH")
    if configured_browser and Path(configured_browser).exists():
        return configured_browser

    for executable in ("msedge.exe", "msedge", "chrome.exe", "chrome"):
        found = shutil.which(executable)
        if found:
            return found

    for candidate in WINDOWS_BROWSER_PATHS:
        if Path(candidate).exists():
            return candidate

    return None


def build_browser_launch_command(browser_path, url, profile_dir):
    profile_path = str(profile_dir)
    browser_name = Path(browser_path).name.lower()
    command = [
        str(browser_path),
        "--new-window",
        f"--app={url}",
        f"--user-data-dir={profile_path}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-session-crashed-bubble",
        "--disable-extensions",
        "--disable-sync",
        "--guest",
    ]

    if "msedge" in browser_name:
        command.extend([
            "--inprivate",
            "--disable-features=msImplicitSignin,EdgeIdentitySyncPromo",
        ])

    return command


def terminate_managed_browser(runtime_file=None):
    runtime_path = Path(runtime_file) if runtime_file else get_browser_runtime_file()
    metadata = read_browser_runtime(runtime_path)
    if not metadata:
        return False

    pid = int(metadata.get("pid") or 0)
    closed = False

    if pid > 0:
        try:
            if os.name == "nt":
                result = subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=False,
                )
                closed = result.returncode == 0
            else:
                os.kill(pid, signal.SIGTERM)
                closed = True
        except Exception:
            closed = False

    cleanup_browser_runtime(runtime_path)
    return closed


def minimize_console():
    """Minimiza a janela do console"""
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        hwnd = kernel32.GetConsoleWindow()
        if hwnd:
            result = user32.ShowWindow(hwnd, 6)
            if result:
                return True

            is_minimized = user32.IsIconic(hwnd)
            if not is_minimized:
                user32.ShowWindow(hwnd, 2)
                time.sleep(0.1)
                user32.ShowWindow(hwnd, 6)
                return True
    except Exception as e:
        print(f"[DEBUG] Erro no metodo ctypes: {e}")

    try:
        import ctypes

        def enum_windows_callback(hwnd, lParam):
            window_text = ctypes.create_unicode_buffer(512)
            user32 = ctypes.windll.user32
            user32.GetWindowTextW(hwnd, window_text, 512)
            if "Sistema de Financas Pessoais" in window_text.value:
                user32.ShowWindow(hwnd, 6)
                return False
            return True

        enum_windows = ctypes.windll.user32.EnumWindows
        enum_windows_proc = ctypes.WINFUNCTYPE(
            ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
        )
        enum_windows(enum_windows_proc(enum_windows_callback), 0)
        return True
    except Exception as e:
        print(f"[DEBUG] Erro no metodo EnumWindows: {e}")

    try:
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
            ["powershell", "-Command", script],
            creationflags=subprocess.CREATE_NO_WINDOW,
            timeout=2,
        )
        return True
    except Exception as e:
        print(f"[DEBUG] Erro no metodo PowerShell: {e}")

    return False


def launch_managed_browser(url):
    runtime_file = get_browser_runtime_file()
    cleanup_browser_runtime(runtime_file)

    browser_path = find_supported_browser()
    if not browser_path:
        return False

    profile_dir = Path(tempfile.mkdtemp(prefix="sfp-browser-", dir=str(get_runtime_dir())))
    command = build_browser_launch_command(browser_path, url, profile_dir)

    try:
        creationflags = 0
        if os.name == "nt":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP

        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags,
        )
        write_browser_runtime(runtime_file, browser_path, process.pid, profile_dir, url)
        return True
    except Exception as exc:
        print(f"[AVISO] Falha ao abrir navegador dedicado: {exc}")
        cleanup_browser_runtime(runtime_file)
        return False


def minimize_and_open_browser():
    """Minimiza a janela do CMD e depois abre o navegador"""
    time.sleep(5)

    print("[INFO] Minimizando janela do CMD...")
    minimized = False
    for _ in range(3):
        if minimize_console():
            print("[OK] Janela do CMD minimizada")
            minimized = True
            break
        time.sleep(0.3)

    if not minimized:
        print("[AVISO] Nao foi possivel minimizar a janela automaticamente")

    time.sleep(0.5)

    try:
        if launch_managed_browser(DEFAULT_APP_URL):
            print("[OK] Navegador dedicado aberto automaticamente na tela de login")
        else:
            webbrowser.open(DEFAULT_APP_URL)
            print("[OK] Navegador aberto automaticamente na tela de login")
    except Exception as e:
        print(f"[AVISO] Nao foi possivel abrir o navegador automaticamente: {e}")
        print(f"[INFO] Acesse manualmente: {DEFAULT_APP_URL}")


def backup_on_exit():
    """Funcao chamada ao encerrar o sistema para fazer backup"""
    terminate_managed_browser()
    print()
    print("[INFO] Criando backup do banco de dados...")
    if create_backup():
        print("[OK] Backup concluido com sucesso!")
    else:
        print("[AVISO] Nao foi possivel criar backup automaticamente")
    print()


if __name__ == "__main__":
    check_python_version()
    atexit.register(backup_on_exit)

    def signal_handler(signum, frame):
        backup_on_exit()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        print("=" * 60)
        print("  SISTEMA DE FINANCAS PESSOAIS")
        print("=" * 60)
        print()
        print("[INFO] Inicializando aplicacao...")

        app = create_app()
        migrate = Migrate(app, db)

        with app.app_context():
            try:
                print("[INFO] Verificando banco de dados...")
                db.create_all()

                from app.models import Category, Conta, Expense, PaymentMethod, User

                user_count = User.query.count()
                print(f"[INFO] Usuarios cadastrados: {user_count}")

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
                        print(f"[AVISO] Nao foi possivel recalcular saldos: {e}")

                print("[OK] Banco de dados verificado e pronto")

            except Exception as e:
                print(f"[ERRO] Falha ao verificar banco de dados: {e}")
                print("[INFO] Tentando continuar...")

        print()
        print("[OK] Aplicacao inicializada com sucesso!")
        print()
        print("=" * 60)
        print("  SERVIDOR INICIADO")
        print("=" * 60)
        print()
        print("  URL: http://127.0.0.1:5000")
        print()
        print("  Credenciais padrao (se for o primeiro acesso):")
        print("    Usuario: admin")
        print("    Senha: admin123")
        print()
        print("  Para encerrar o sistema:")
        print("    - Pressione Ctrl+C nesta janela, ou")
        print("    - Use o botao 'Encerrar Sistema' na interface")
        print()
        print("=" * 60)
        print()

        browser_thread = threading.Thread(target=minimize_and_open_browser, daemon=True)
        browser_thread.start()

        app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

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
        try:
            backup_on_exit()
        except Exception:
            pass
        print("[INFO] Pressione Enter para sair...")
        input()
        sys.exit(1)
