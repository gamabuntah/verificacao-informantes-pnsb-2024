from .api import api_bp
from .main import main_bp
from .melhorias_api import melhorias_bp
from .funcionalidades_pnsb_api import funcionalidades_pnsb_bp
from .team_config_api import team_config_bp

def register_blueprints(app):
    """Registra todos os blueprints essenciais no app"""
    print("🔗 Registrando blueprints principais...")
    
    # Core blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Feature blueprints  
    app.register_blueprint(melhorias_bp, url_prefix='/api/melhorias')
    app.register_blueprint(funcionalidades_pnsb_bp, url_prefix='/api/pnsb')
    app.register_blueprint(team_config_bp)  # Já tem url_prefix='/api' definido no blueprint
    
    print("✅ Blueprints principais registrados")