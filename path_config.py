#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração centralizada de caminhos para o Sistema de Finanças Pessoais
Garante que todos os caminhos apontem para o diretório do usuário logado
"""

import os
from pathlib import Path
import platform
import subprocess

def _get_desktop_via_powershell():
    """
    Detecta o caminho da área de trabalho usando PowerShell
    Retorna o caminho correto para o usuário atual do sistema
    """
    try:
        result = subprocess.run([
            "powershell", "-Command", "[Environment]::GetFolderPath('Desktop')"
        ], capture_output=True, text=True, shell=True, timeout=10)
        
        if result.returncode == 0:
            desktop_path = Path(result.stdout.strip())
            if desktop_path.exists():
                return desktop_path
    except:
        pass
    return None

def get_user_install_directory():
    """
    Retorna o diretório de instalação no diretório do usuário LOCAL do sistema
    Detecta automaticamente o usuário logado no computador atual
    """
    # Usar getpass para obter o usuário atual do sistema
    import getpass
    current_user = getpass.getuser()
    
    # No Windows, usar USERPROFILE que sempre aponta para o usuário atual
    if os.name == 'nt':  # Windows
        user_profile = os.environ.get('USERPROFILE', '')
        if user_profile:
            user_home = Path(user_profile)
        else:
            # Fallback: usar Path.home() que também detecta o usuário atual
            user_home = Path.home()
    else:  # Linux/Mac
        user_home = Path.home()
    
    install_dir = user_home / "Financas_Pessoais"
    return install_dir

def get_user_desktop_path():
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
            
            # Tentar detectar via PowerShell (mais confiável)
            _get_desktop_via_powershell(),
        ]
        
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

def get_database_path():
    """
    Retorna o caminho do banco de dados no diretório do usuário
    """
    install_dir = get_user_install_directory()
    return install_dir / "app.db"

def get_instance_path():
    """
    Retorna o caminho da pasta instance no diretório do usuário
    """
    install_dir = get_user_install_directory()
    return install_dir / "instance"

def get_icon_path():
    """
    Retorna o caminho do ícone no diretório do usuário
    """
    install_dir = get_user_install_directory()
    return install_dir / "iconFP.ico"

def get_executable_path():
    """
    Retorna o caminho do script executável no diretório do usuário
    """
    install_dir = get_user_install_directory()
    return install_dir / "executar_sistema.bat"

def get_shortcut_path():
    """
    Retorna o caminho onde o atalho deve ser criado na área de trabalho
    """
    desktop = get_user_desktop_path()
    return desktop / "Financas Pessoais.lnk"

def print_paths():
    """
    Imprime todos os caminhos configurados para debug
    """
    print("=" * 50)
    print("    CONFIGURAÇÃO DE CAMINHOS")
    print("=" * 50)
    print(f"Diretório de instalação: {get_user_install_directory()}")
    print(f"Área de trabalho: {get_user_desktop_path()}")
    print(f"Banco de dados: {get_database_path()}")
    print(f"Pasta instance: {get_instance_path()}")
    print(f"Ícone: {get_icon_path()}")
    print(f"Executável: {get_executable_path()}")
    print(f"Atalho: {get_shortcut_path()}")
    print("=" * 50)

if __name__ == "__main__":
    print_paths()
