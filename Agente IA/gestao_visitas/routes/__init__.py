from .api import api_bp
from .main import main_bp
from .melhorias_api import melhorias_bp
from .funcionalidades_pnsb_api import funcionalidades_pnsb_bp

def register_blueprints(app):
    """Registra todos os blueprints no app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(melhorias_bp, url_prefix='/api/melhorias')
    app.register_blueprint(funcionalidades_pnsb_bp, url_prefix='/api/pnsb')