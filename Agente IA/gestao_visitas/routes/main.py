from flask import Blueprint, render_template

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página principal - Dashboard"""
    return render_template('dashboard.html')

@main_bp.route('/calendario')
def calendario():
    """Página do calendário"""
    return render_template('calendario.html')

@main_bp.route('/visitas')
def pagina_visitas():
    """Página de gerenciamento de visitas"""
    return render_template('visitas.html')

@main_bp.route('/relatorios')
def relatorios():
    """Página de relatórios"""
    return render_template('relatorios.html')

@main_bp.route('/contatos')
def contatos():
    """Página de contatos"""
    return render_template('contatos.html')

@main_bp.route('/checklist')
def checklist():
    """Página de checklist"""
    return render_template('checklist.html')

@main_bp.route('/material-apoio')
def material_apoio():
    """Página de Material de Apoio PNSB"""
    return render_template('material_apoio.html')