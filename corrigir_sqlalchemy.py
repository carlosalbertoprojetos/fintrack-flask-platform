#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas de compatibilidade SQLAlchemy + Python 3.13
Execute este script se encontrar erros de instalação
"""

import sys
import subprocess
import os

def print_step(step, message):
    """Imprime uma etapa da correção"""
    print(f"[{step}] {message}")

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
        if e.stderr:
            print(f"  Erro: {e.stderr}")
        return False

def main():
    print("=" * 60)
    print("    CORRETOR SQLALCHEMY + PYTHON 3.13")
    print("=" * 60)
    print()
    
    # Verificar versão do Python
    version = sys.version_info
    print(f"🐍 Python detectado: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor == 13:
        print("⚠️  Python 3.13 detectado - aplicando correções...")
    else:
        print("ℹ️  Versão do Python diferente de 3.13 - aplicando correções preventivas...")
    
    print()
    
    print_step(1, "Atualizando pip...")
    if not run_command("python -m pip install --upgrade pip", "Atualizando pip"):
        print("  ⚠️  Erro ao atualizar pip, continuando...")
    
    print_step(2, "Desinstalando SQLAlchemy antigo...")
    run_command("pip uninstall -y SQLAlchemy", "Removendo versão antiga do SQLAlchemy")
    
    print_step(3, "Instalando SQLAlchemy compatível...")
    if not run_command("pip install 'SQLAlchemy>=2.0.25,<3.0.0'", "Instalando SQLAlchemy >= 2.0.25"):
        print("  ⚠️  Tentando instalação da versão mais recente...")
        run_command("pip install --upgrade SQLAlchemy", "Instalando última versão do SQLAlchemy")
    
    print_step(4, "Testando compatibilidade...")
    try:
        import sqlalchemy
        print(f"  ✅ SQLAlchemy {sqlalchemy.__version__} instalado com sucesso!")
    except ImportError as e:
        print(f"  ❌ Erro ao importar SQLAlchemy: {e}")
        return False
    
    print_step(5, "Testando inicialização do banco...")
    try:
        # Mudar para o diretório do projeto
        current_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(current_dir)
        
        # Testar importação do app
        sys.path.insert(0, current_dir)
        from app import create_app, db
        
        app = create_app()
        with app.app_context():
            db.create_all()
        
        print("  ✅ Banco de dados inicializado com sucesso!")
        print("  ✅ Problema de compatibilidade resolvido!")
        
    except Exception as e:
        print(f"  ❌ Erro ao testar banco: {e}")
        print("  💡 Tente executar o instalador novamente")
        return False
    
    print()
    print("=" * 60)
    print("    CORREÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 60)
    print()
    print("✅ O problema de compatibilidade foi resolvido!")
    print("✅ Agora você pode executar o instalador normalmente.")
    print()
    print("🚀 Próximos passos:")
    print("   1. Execute: python instalar_sistema.py")
    print("   2. Ou use: INSTALAR.bat")
    print()
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Correção falhou!")
            print("💡 Recomendação: Instale Python 3.11 ou 3.12")
            print("   https://www.python.org/downloads/")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Correção cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        sys.exit(1)

