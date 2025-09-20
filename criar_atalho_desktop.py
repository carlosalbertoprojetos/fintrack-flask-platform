#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar atalho na área de trabalho com ícone personalizado
"""

import os
import sys
from pathlib import Path
import subprocess
import platform

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

def create_desktop_shortcut():
    """Cria atalho na área de trabalho com ícone personalizado"""
    
    # Diretórios no diretório do usuário LOCAL do sistema
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
    icon_path = install_dir / "iconFP.ico"
    batch_path = install_dir / "executar_sistema.bat"
    
    print(f"Usuário atual do sistema: {getpass.getuser()}")
    print(f"Diretório do usuário: {user_home}")
    print(f"Diretório de instalação: {install_dir}")
    
    print("Criando atalho na área de trabalho...")
    
    # Verificar se o diretório de instalação existe
    if not install_dir.exists():
        print(f"ERRO: Diretorio de instalacao nao encontrado: {install_dir}")
        return False
    
    # Verificar se o ícone existe
    if not icon_path.exists():
        print(f"AVISO: Icone nao encontrado: {icon_path}")
        print("   Criando atalho sem icone personalizado...")
        icon_path = None
    
    # Detectar área de trabalho automaticamente
    desktop = get_desktop_path()
    print(f"Área de trabalho detectada: {desktop}")
    print(f"Desktop existe: {desktop.exists()}")
    
    # Criar script de execução se não existir
    if not batch_path.exists():
        print("Criando script de execução...")
        batch_content = f"""@echo off
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
"""
        try:
            with open(batch_path, "w", encoding="utf-8") as f:
                f.write(batch_content)
            print(f"OK: Script de execução criado: {batch_path}")
        except Exception as e:
            print(f"ERRO: Erro ao criar script de execução: {e}")
            return False
    
    # Caminho do atalho
    shortcut_path = desktop / "Financas Pessoais.lnk"
    
    # Criar atalho usando PowerShell
    try:
        print("Criando atalho com PowerShell...")
        
        # MÉTODO 1: Usar comando direto do Windows (mais confiável)
        cmd = f'''powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('{shortcut_path}'); $Shortcut.TargetPath = '{batch_path}'; $Shortcut.WorkingDirectory = '{install_dir}'; $Shortcut.Description = 'Sistema de Financas Pessoais v2.0.0'; $Shortcut.IconLocation = '{icon_path}'; $Shortcut.Save(); Write-Host 'Atalho criado!'"'''
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0 and shortcut_path.exists():
            print("OK: Atalho .lnk criado com comando direto!")
            if icon_path and icon_path.exists():
                print(f"Icone configurado: {icon_path}")
            return True
        else:
            print(f"Falha no comando direto: {result.stderr}")
            
    except Exception as e:
        print(f"Erro no comando direto: {e}")
    
    # MÉTODO 2: Usar arquivo PowerShell como fallback
    try:
        print("Tentativa 2: Usando arquivo PowerShell...")
        
        # Usar aspas duplas e escapar caracteres especiais
        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{batch_path}"
$Shortcut.WorkingDirectory = "{install_dir}"
$Shortcut.Description = "Sistema de Financas Pessoais v2.0.0"
'''
        
        if icon_path and icon_path.exists():
            ps_script += f'$Shortcut.IconLocation = "{icon_path}"\n'
        
        ps_script += '''
$Shortcut.Save()
Write-Host "Atalho .lnk criado com sucesso!"
'''
        
        # Salvar script PowerShell em arquivo temporário
        ps_file = install_dir / "create_shortcut.ps1"
        with open(ps_file, "w", encoding="utf-8") as f:
            f.write(ps_script)
        
        # Executar script PowerShell
        result = subprocess.run([
            "powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps_file)
        ], capture_output=True, text=True, shell=True)
        
        # Remover arquivo temporário
        try:
            ps_file.unlink()
        except:
            pass
        
        if result.returncode == 0 and shortcut_path.exists():
            print("OK: Atalho .lnk criado com arquivo PowerShell!")
            if icon_path and icon_path.exists():
                print(f"Icone configurado: {icon_path}")
            return True
        else:
            print(f"Falha no arquivo PowerShell: {result.stderr}")
            
    except Exception as e:
        print(f"Erro no arquivo PowerShell: {e}")
    
    # Fallback: criar arquivo .bat na área de trabalho
    try:
        print("Criando atalho alternativo (.bat)...")
        alt_shortcut = desktop / "Financas Pessoais.bat"
        
        alt_content = f"""@echo off
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
"""
        
        with open(alt_shortcut, "w", encoding="utf-8") as f:
            f.write(alt_content)
        
        if alt_shortcut.exists():
            print(f"OK: Atalho .bat criado: {alt_shortcut}")
            return True
        else:
            print("ERRO: Falha ao criar atalho .bat")
            return False
            
    except Exception as e:
        print(f"ERRO ao criar atalho .bat: {e}")
        return False

if __name__ == "__main__":
    success = create_desktop_shortcut()
    if success:
        print("\nSUCESSO: Atalho criado com sucesso na area de trabalho!")
    else:
        print("\nERRO: Falha ao criar atalho!")
        sys.exit(1)



