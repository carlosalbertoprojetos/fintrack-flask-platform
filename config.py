import os
from datetime import timedelta
from pathlib import Path

# Usar caminhos dinâmicos baseados no usuário LOCAL do sistema
def get_user_install_dir():
    """Retorna o diretório de instalação no diretório do usuário LOCAL do sistema"""
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
    
    return user_home / "Financas_Pessoais"

# Diretório base dinâmico
user_install_dir = get_user_install_dir()
basedir = str(user_install_dir) if user_install_dir.exists() else os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "chave-secreta-padrao"
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configurações de Sessão para compatibilidade entre navegadores
    SESSION_COOKIE_SECURE = False  # True apenas se usar HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Previne acesso via JavaScript
    SESSION_COOKIE_SAMESITE = 'Lax'  # Compatível com navegadores modernos
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Configurações de Cookies para compatibilidade
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = False  # True apenas se usar HTTPS
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_REFRESH_EACH_REQUEST = True
    
    # Configurações de Email
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", True)
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get(
        "MAIL_DEFAULT_SENDER", "noreply@financaspessoais.com"
    )

    # Configuração para mostrar emails no console
    MAIL_SUPPRESS_SEND = True  # Não envia emails realmente
    MAIL_DEBUG = True  # Mostra informações de debug
    MAIL_BACKEND = "console"  # Usa o backend de console


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True


# Configuração padrão
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
