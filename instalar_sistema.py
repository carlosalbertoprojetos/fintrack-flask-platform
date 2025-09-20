#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador do Sistema de Finanças Pessoais v2.0.0
Cria o ambiente virtual, instala dependências e configura o sistema
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import platform

def print_step(step, message):
    """Imprime uma etapa da instalação"""
    print(f"[{step}] {message}")

def get_desktop_path():
    """
    Detecta o caminho da área de trabalho do usuário LOCAL do sistema
    Funciona em qualquer computador, detectando automaticamente o usuário atual
    """
    system = platform.system().lower()
    
    # Windows
    if system == "windows":
        # Obter o diretório do usuário atual usando variáveis de ambiente
        user_profile = os.environ.get('USERPROFILE', '')
        
        if user_profile:
            user_home = Path(user_profile)
        else:
            user_home = Path.home()
        
        # Tentar múltiplas localizações comuns para o usuário atual
        possible_paths = [
            # OneDrive (mais comum no Windows 10/11)
            user_home / "OneDrive" / "Área de Trabalho",
            user_home / "OneDrive" / "Desktop",
            
            # Área de trabalho tradicional
            user_home / "Área de Trabalho",
            user_home / "Desktop",
        ]
        
        # Tentar PowerShell para detectar automaticamente o usuário atual
        try:
            result = subprocess.run([
                "powershell", "-Command", "[Environment]::GetFolderPath('Desktop')"
            ], capture_output=True, text=True, shell=True, timeout=10)
            
            if result.returncode == 0:
                ps_desktop = Path(result.stdout.strip())
                if ps_desktop.exists():
                    return ps_desktop
        except:
            pass
        
        # Verificar caminhos possíveis
        for path in possible_paths:
            if path and path.exists():
                return path
                
        # Fallback: usar Desktop padrão do usuário atual
        return user_home / "Desktop"
    
    # Linux
    elif system == "linux":
        # Verificar variáveis de ambiente
        desktop_env = os.environ.get("XDG_DESKTOP_DIR")
        if desktop_env:
            return Path(desktop_env)
        
        # Caminhos padrão do Linux
        possible_paths = [
            Path.home() / "Desktop",
            Path.home() / "Área de Trabalho",
            Path.home() / "Área de trabalho",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # Fallback
        return Path.home() / "Desktop"
    
    # macOS
    elif system == "darwin":
        return Path.home() / "Desktop"
    
    # Sistema desconhecido - fallback
    else:
        return Path.home() / "Desktop"

def run_command(command, description=""):
    """Executa um comando e retorna True se bem-sucedido"""
    try:
        if description:
            print(f"  → {description}")
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erro: {e}")
        if e.stdout:
            print(f"  Saída: {e.stdout}")
        if e.stderr:
            print(f"  Erro: {e.stderr}")
        return False

def check_python_version():
    """Verifica se a versão do Python é compatível"""
    version = sys.version_info
    print(f"🐍 Python detectado: {version.major}.{version.minor}.{version.micro}")
    
    # Python 3.13 tem problemas de compatibilidade com SQLAlchemy
    if version.major == 3 and version.minor == 13:
        print("⚠️  AVISO: Python 3.13 detectado!")
        print("   Esta versão pode ter problemas de compatibilidade com SQLAlchemy.")
        print("   Recomendamos usar Python 3.11 ou 3.12 para melhor compatibilidade.")
        print()
        
        resposta = input("Deseja continuar mesmo assim? (s/N): ").strip().lower()
        if resposta not in ['s', 'sim', 'y', 'yes']:
            print("❌ Instalação cancelada.")
            print("💡 Sugestão: Instale Python 3.11 ou 3.12 do site oficial:")
            print("   https://www.python.org/downloads/")
            return False
    
    # Versões muito antigas
    elif version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ ERRO: Python 3.8 ou superior é necessário!")
        print(f"   Versão atual: {version.major}.{version.minor}.{version.micro}")
        print("   Baixe uma versão compatível em: https://www.python.org/downloads/")
        return False
    
    print("✅ Versão do Python compatível!")
    print()
    return True

def main():
    print("=" * 50)
    print("    INSTALADOR FINANÇAS PESSOAIS v2.0.0")
    print("=" * 50)
    print()
    
    # Verificar versão do Python
    if not check_python_version():
        return False
    
    # Diretório de instalação no diretório do usuário LOCAL do sistema
    import getpass
    
    # No Windows, usar USERPROFILE que sempre aponta para o usuário atual
    if os.name == 'nt':  # Windows
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            user_home = Path(user_profile)
        else:
            user_home = Path.home()
    else:  # Linux/Mac
        user_home = Path.home()
    
    install_dir = user_home / "Financas_Pessoais"
    current_dir = Path.cwd()
    
    print(f"Usuário atual do sistema: {getpass.getuser()}")
    print(f"Diretório do usuário: {user_home}")
    print(f"Diretório de instalação: {install_dir}")
    
    print_step(1, "Preparando instalação...")
    
    # Cria diretório de instalação
    try:
        install_dir.mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Diretório de instalação: {install_dir}")
    except Exception as e:
        print(f"  ❌ Erro ao criar diretório: {e}")
        return False
    
    print_step(2, "Copiando arquivos do sistema...")
    
    # Lista de arquivos e diretórios para copiar
    items_to_copy = [
        "app",
        "routes", 
        "migrations",
        "instance",
        "run.py",
        "config.py",
        "path_config.py",
        "requirements.txt",
        "iconFP.ico",
        "iconFP.png",
        "start_flask.bat",
        "criar_atalho_desktop.py"
    ]
    
    for item in items_to_copy:
        src = current_dir / item
        dst = install_dir / item
        
        try:
            if src.is_file():
                shutil.copy2(src, dst)
                print(f"  ✅ Copiado: {item}")
            elif src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                print(f"  ✅ Copiado: {item}/")
            else:
                print(f"  ⚠️  Não encontrado: {item}")
        except Exception as e:
            print(f"  ❌ Erro ao copiar {item}: {e}")
            return False
    
    print_step(3, "Criando ambiente virtual...")
    
    # Muda para o diretório de instalação
    os.chdir(install_dir)
    
    # Cria ambiente virtual
    if not run_command("python -m venv venv", "Criando ambiente virtual"):
        return False
    
    print_step(4, "Instalando dependências...")
    
    # Instala dependências usando o pip do sistema (mais confiável)
    if not run_command(f'pip install -r requirements.txt', "Instalando dependências"):
        print("  ⚠️  Tentando instalação alternativa...")
        # Fallback: instalar dependências principais manualmente
        dependencies = [
            "Flask==2.3.3",
            "Flask-SQLAlchemy==3.1.1", 
            "Flask-Migrate==4.0.5",
            "Flask-Login==0.6.2",
            "Flask-WTF==1.2.1",
            "Flask-Mail==0.9.1",
            "Werkzeug==2.3.7",
            "SQLAlchemy>=2.0.25,<3.0.0",
            "WTForms==3.1.1",
            "email-validator==2.1.0",
            "python-dotenv==1.0.0",
            "psutil==5.9.5"
        ]
        
        for dep in dependencies:
            if not run_command(f'pip install {dep}', f"Instalando {dep.split('==')[0]}"):
                print(f"  ⚠️  Erro ao instalar {dep}, continuando...")
        
        print("  ✅ Instalação de dependências concluída (com avisos)")
    
    print_step(5, "Inicializando banco de dados...")
    
    # Inicializa o banco de dados usando Python do sistema
    if not run_command(f'python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all(); print(\'Banco inicializado\')"', 
                      "Criando tabelas do banco"):
        print("  ⚠️  Erro na inicialização do banco, tentando método alternativo...")
        # Fallback: executar diretamente
        try:
            import sys
            sys.path.insert(0, str(install_dir))
            from app import create_app, db
            app = create_app()
            with app.app_context():
                db.create_all()
            print("  ✅ Banco inicializado com método alternativo")
        except Exception as e:
            print(f"  ❌ Erro na inicialização alternativa: {e}")
            return False
    
    print_step(6, "Criando atalho na área de trabalho...")
    
    # Detectar área de trabalho automaticamente
    desktop_path = get_desktop_path()
    print(f"  📍 Área de trabalho detectada: {desktop_path}")
    
    # Cria atalho na área de trabalho com ícone
    try:
        # Executar script de criação de atalho a partir do diretório de instalação
        script_path = install_dir / "criar_atalho_desktop.py"
        result = run_command(f'python "{script_path}"', "Criando atalho com ícone iconFP.ico")
        if result:
            print("  ✅ Atalho criado com ícone iconFP.ico na área de trabalho")
        else:
            print("  AVISO: Erro ao criar atalho, criando versao simples...")
            # Fallback: criar atalho simples
            try:
                shortcut_path = desktop_path / "Financas Pessoais.bat"
                shortcut_content = f'''@echo off
title Financas Pessoais v2.0.0
color 0A
echo.
echo ================================================
echo    FINANCAS PESSOAIS v2.0.0
echo ================================================
echo.
echo Iniciando sistema...
echo.
cd /d "{install_dir}"
echo.
echo Iniciando servidor Flask...
echo.
echo Acesse: http://127.0.0.1:5000
echo Usuario: admin
echo Senha: admin123
echo.
echo Abrindo navegador automaticamente...
start http://127.0.0.1:5000
echo.
echo Pressione Ctrl+C para parar o servidor
echo.
python run.py
echo.
echo Sistema encerrado.
pause
'''
                with open(shortcut_path, 'w', encoding='utf-8') as f:
                    f.write(shortcut_content)
                print(f"  ✅ Atalho simples criado: {shortcut_path}")
            except Exception as fallback_error:
                print(f"  ❌ ERRO: Nao foi possivel criar atalho simples: {fallback_error}")
    except Exception as e:
        print(f"  ⚠️  Erro ao criar atalho: {e}")
    
    print()
    print("=" * 50)
    print("    INSTALAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 50)
    print()
    print("🎉 O sistema foi instalado em:")
    print(f"   📍 {install_dir}")
    print()
    print("🌐 Para usar o sistema:")
    print("   1. Use o atalho 'Finanças Pessoais' na área de trabalho")
    print("   2. Ou execute: start_flask.bat")
    print("   3. Acesse: http://127.0.0.1:5000")
    print()
    print("👤 Usuário padrão: admin")
    print("🔑 Senha padrão: admin123")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Instalação falhou!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)
