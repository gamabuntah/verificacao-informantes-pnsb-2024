import os
from flask import Flask
from flask_migrate import Migrate

from .db import db
from .config.security import SecurityConfig
from .utils.error_handlers import ErrorHandler
from .routes import register_blueprints


def create_app(config_name='development'):
    """Factory function para criar aplicação Flask"""
    
    app = Flask(__name__, template_folder='templates')
    
    # Configurar aplicação
    configure_app(app, config_name)
    
    # Inicializar extensões
    initialize_extensions(app)
    
    # Configurar tratamento de erros
    setup_error_handling(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Criar tabelas do banco
    with app.app_context():
        db.create_all()
    
    # Validar configuração
    validate_configuration()
    
    return app


def configure_app(app, config_name):
    """Configurar aplicação Flask"""
    
    # Diretório base
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Configurações básicas
    app.config['SECRET_KEY'] = SecurityConfig.get_secret_key()
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuração do banco de dados
    db_path = os.path.join(basedir, 'gestao_visitas.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    
    # Garantir que diretório do banco existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Configurações específicas por ambiente
    if config_name == 'development':
        app.config['DEBUG'] = True
        app.config['TESTING'] = False
    elif config_name == 'testing':
        app.config['DEBUG'] = True
        app.config['TESTING'] = True
        # Usar banco em memória para testes
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    elif config_name == 'production':
        app.config['DEBUG'] = False
        app.config['TESTING'] = False
        # Configurações adicionais de produção
        app.config['SESSION_COOKIE_SECURE'] = True
        app.config['SESSION_COOKIE_HTTPONLY'] = True
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    
    # Configurações de uploads
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    
    # Criar diretório de uploads se não existir
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def initialize_extensions(app):
    """Inicializar extensões Flask"""
    
    # SQLAlchemy
    db.init_app(app)
    
    # Migrations
    migrate = Migrate(app, db)
    
    # Armazenar referências para uso posterior
    app.extensions['migrate'] = migrate


def setup_error_handling(app):
    """Configurar tratamento de erros"""
    
    error_handler = ErrorHandler(app)
    
    # Configurar logging
    ErrorHandler.setup_logging(app)
    
    # Adicionar middleware de logging de requests
    @app.before_request
    def log_request_info():
        if not app.debug:
            app.logger.info(f"Request: {request.method} {request.url}")
    
    @app.after_request
    def log_response_info(response):
        if not app.debug:
            app.logger.info(f"Response: {response.status_code}")
        return response


def validate_configuration():
    """Validar configuração da aplicação"""
    
    print("🔧 Validando configuração da aplicação...")
    
    # Validar variáveis de ambiente
    if not SecurityConfig.validate_environment():
        print("⚠️  Algumas configurações estão ausentes, mas a aplicação pode funcionar com funcionalidades limitadas.")
    
    print("✅ Aplicação configurada com sucesso!")


class Config:
    """Classe base para configurações"""
    
    SECRET_KEY = SecurityConfig.get_secret_key()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB


class DevelopmentConfig(Config):
    """Configurações para desenvolvimento"""
    
    DEBUG = True
    TESTING = False
    
    @staticmethod
    def init_app(app):
        print("🔧 Modo: Desenvolvimento")


class TestingConfig(Config):
    """Configurações para testes"""
    
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    @staticmethod
    def init_app(app):
        print("🧪 Modo: Testes")


class ProductionConfig(Config):
    """Configurações para produção"""
    
    DEBUG = False
    TESTING = False
    
    # Configurações de segurança
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    @staticmethod
    def init_app(app):
        print("🚀 Modo: Produção")
        
        # Log para syslog em produção
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


# Mapeamento de configurações
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}