#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exemplo de como usar os caminhos dinâmicos no Sistema de Finanças Pessoais
Este arquivo demonstra como todos os caminhos agora apontam para o diretório do usuário logado
"""

import sys
from pathlib import Path

# Adicionar o diretório atual ao path para importar path_config
sys.path.append(str(Path(__file__).parent))

try:
    from path_config import (
        get_user_install_directory,
        get_user_desktop_path,
        get_database_path,
        get_instance_path,
        get_icon_path,
        get_executable_path,
        get_shortcut_path,
        print_paths
    )
except ImportError:
    print("Erro: Arquivo path_config.py não encontrado!")
    print("Execute este script a partir do diretório do projeto.")
    sys.exit(1)

def main():
    print("=" * 60)
    print("    SISTEMA DE FINANÇAS PESSOAIS - CAMINHOS DINÂMICOS")
    print("    DETECÇÃO AUTOMÁTICA DE USUÁRIO LOCAL")
    print("=" * 60)
    print()
    print("Este script demonstra como todos os caminhos agora")
    print("apontam para o diretório do usuário LOCAL do sistema:")
    print()
    
    # Mostrar informações do usuário atual
    import getpass
    current_user = getpass.getuser()
    print(f"👤 Usuário atual do sistema: {current_user}")
    
    # Imprimir todos os caminhos
    print_paths()
    
    print()
    print("VANTAGENS DOS CAMINHOS DINÂMICOS:")
    print("✓ Funciona em QUALQUER computador automaticamente")
    print("✓ Detecta o usuário LOCAL do sistema onde está instalando")
    print("✓ Não requer privilégios de administrador")
    print("✓ Instala no diretório do usuário logado")
    print("✓ Detecta automaticamente a área de trabalho")
    print("✓ Compatível com OneDrive e outras configurações")
    print("✓ Multi-usuário: cada usuário tem sua própria instalação")
    print()
    
    # Verificar se os diretórios existem
    print("VERIFICAÇÃO DE EXISTÊNCIA:")
    install_dir = get_user_install_directory()
    print(f"Diretório de instalação existe: {install_dir.exists()}")
    
    desktop = get_user_desktop_path()
    print(f"Área de trabalho existe: {desktop.exists()}")
    print(f"Área de trabalho: {desktop}")
    
    print()
    print("COMO USAR:")
    print("1. Execute: python testar_usuario_local.py (para testar)")
    print("2. Execute: python instalar_sistema.py (para instalar)")
    print("3. O sistema será instalado em:", install_dir)
    print("4. O atalho será criado em:", desktop)
    print()
    
    # Exemplo de uso programático
    print("EXEMPLO DE USO PROGRAMÁTICO:")
    print("```python")
    print("from path_config import get_user_install_directory")
    print("import getpass")
    print("")
    print("# Detecta automaticamente o usuário atual do sistema")
    print("current_user = getpass.getuser()")
    print("install_dir = get_user_install_directory()")
    print("print(f'Usuário: {current_user}')")
    print("print(f'Sistema instalado em: {install_dir}')")
    print("```")
    print()
    
    print("🔧 TESTE DE COMPATIBILIDADE:")
    print("Execute 'python testar_usuario_local.py' para verificar")
    print("se a detecção de usuário está funcionando corretamente")
    print("em seu computador específico.")
    print()
    
    return True

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Erro: {e}")
        sys.exit(1)
