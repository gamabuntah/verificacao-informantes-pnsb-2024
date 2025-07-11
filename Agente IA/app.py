from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from gestao_visitas.db import db
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️ python-dotenv não disponível. Usando variáveis de ambiente do sistema.")
import requests
from flask_migrate import Migrate
try:
    from flask_compress import Compress
    COMPRESS_AVAILABLE = True
except ImportError:
    print("⚠️ Flask-Compress não disponível. Compressão desabilitada.")
    COMPRESS_AVAILABLE = False
from gestao_visitas.services.maps import MapaService
from gestao_visitas.utils.error_handlers import ErrorHandler, APIResponse
from sqlalchemy import or_
import pandas as pd
import csv

print("=== INICIANDO APP.PY CORRETO ===")

app = Flask(__name__, 
           template_folder='gestao_visitas/templates',
           static_folder='gestao_visitas/static')

# Configuração do banco de dados com caminho absoluto
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'gestao_visitas', 'gestao_visitas.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave_secreta_pnsb_2024_gestao_visitas')
google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
app.config['GOOGLE_MAPS_API_KEY'] = google_maps_key
print(f"🔍 Debug: Configurando GOOGLE_MAPS_API_KEY = '{google_maps_key}' (length: {len(google_maps_key or '')})")

# Configurações de segurança adiccionais
app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hora
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Garantir que o diretório do banco de dados existe
os.makedirs(os.path.dirname(db_path), exist_ok=True)

# Inicializar o banco de dados
db.init_app(app)
migrate = Migrate(app, db)

# Configurar compressão (se disponível)
if COMPRESS_AVAILABLE:
    compress = Compress(app)
    print("✅ Compressão Flask-Compress ativada")
else:
    print("ℹ️ Rodando sem compressão (performance pode ser menor)")

# Configurar tratamento de erros
error_handler = ErrorHandler(app)
ErrorHandler.setup_logging(app)

# Criar todas as tabelas
with app.app_context():
    db.create_all()

# Import models
from gestao_visitas.models.agendamento import Visita, Calendario
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.contatos import Contato, TipoEntidade, FonteInformacao
from gestao_visitas.models.questionarios_obrigatorios import QuestionarioObrigatorio, EntidadeIdentificada, ProgressoQuestionarios, EntidadePrioritariaUF

# Import blueprints
from gestao_visitas.routes.ibge_api import ibge_bp
from gestao_visitas.routes.auto_scheduler_api import auto_scheduler_bp
from gestao_visitas.routes.strategy_assistant_api import strategy_assistant_bp
from gestao_visitas.routes.critical_alerts_api import critical_alerts_bp
from gestao_visitas.routes.timeline_api import timeline_bp
from gestao_visitas.routes.google_maps_api import google_maps_bp

# Import services
from gestao_visitas.services.relatorios import RelatorioService
from gestao_visitas.services.rotas import RotaService
from gestao_visitas.services.checklist import get_campos_etapa
from collections import defaultdict, deque
import time

# Simple rate limiter
class SimpleRateLimiter:
    def __init__(self, max_requests=100, window_minutes=1):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests = defaultdict(deque)
    
    def is_allowed(self, client_ip):
        now = time.time()
        client_requests = self.requests[client_ip]
        
        # Remove requests outside the window
        while client_requests and client_requests[0] < now - self.window_seconds:
            client_requests.popleft()
        
        # Check if limit exceeded
        if len(client_requests) >= self.max_requests:
            return False
        
        # Add current request
        client_requests.append(now)
        return True

rate_limiter = SimpleRateLimiter(max_requests=100, window_minutes=1)

@app.before_request
def rate_limit_check():
    """Check rate limiting for API endpoints"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
    
    # Apply rate limiting only to API endpoints
    if request.path.startswith('/api/'):
        if not rate_limiter.is_allowed(client_ip):
            return jsonify({'error': 'Rate limit exceeded'}), 429

# Security and performance middleware
@app.after_request
def add_security_headers(response):
    """Add security headers and caching to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Add caching headers for static assets
    if request.path.startswith('/static/'):
        response.headers['Cache-Control'] = 'public, max-age=31536000'  # 1 year
        response.headers['Expires'] = datetime.fromtimestamp(time.time() + 31536000).strftime('%a, %d %b %Y %H:%M:%S GMT')
    elif request.path.startswith('/api/'):
        # API responses should not be cached by default
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    
    
    # Additional security headers
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
    
    # Content Security Policy - relaxado para desenvolvimento com Google Maps
    if os.getenv('FLASK_ENV') == 'development':
        # CSP mais permissivo para desenvolvimento
        csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https: data:; style-src 'self' 'unsafe-inline' https: data:; img-src 'self' data: https: blob:; font-src 'self' data: https:; connect-src 'self' https: data:; frame-src 'self' https:"
    else:
        # CSP mais restritivo para produção
        csp = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://maps.googleapis.com *.googleapis.com; style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com *.googleapis.com; img-src 'self' data: https: https://maps.gstatic.com https://maps.googleapis.com *.gstatic.com *.googleapis.com; font-src 'self' data: https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://fonts.gstatic.com; connect-src 'self' https://servicodados.ibge.gov.br https://maps.googleapis.com *.googleapis.com"
    
    response.headers['Content-Security-Policy'] = csp
    
    return response

# Initialize services
api_key = os.getenv('GOOGLE_MAPS_API_KEY')
mapa_service = None

if api_key and api_key != 'your_google_maps_api_key_here' and len(api_key) > 10:
    try:
        mapa_service = MapaService(api_key)
        print("✅ Google Maps API configurado com sucesso")
    except Exception as e:
        print(f"⚠️  Erro ao configurar Google Maps API: {e}")
        print("   Sistema funcionará sem otimização de rotas")
        mapa_service = None
else:
    print("⚠️  Google Maps API Key não configurada. Sistema funcionará sem otimização de rotas.")
relatorio_service = RelatorioService()
rota_service = RotaService(mapa_service)

# Inicializar sistema de backup automático
from gestao_visitas.services.backup_service import inicializar_backup_service, obter_backup_service
inicializar_backup_service()
print("🔒 Sistema de backup automático ativado - suas visitas estão protegidas!")

GOOGLE_API_KEY = os.getenv('GOOGLE_GEMINI_API_KEY')
CHAT_IA_HABILITADO = os.getenv('CHAT_IA_HABILITADO', 'false').lower() == 'true'

if not GOOGLE_API_KEY:
    print("⚠️  ATENÇÃO: Google Gemini API Key não configurada! Chat IA não funcionará.")
    GOOGLE_API_KEY = None
    CHAT_IA_HABILITADO = False
elif not CHAT_IA_HABILITADO:
    print("💰 Chat IA desabilitado para economizar custos. Defina CHAT_IA_HABILITADO=true para habilitar.")

# Routes
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/calendario')
def calendario():
    google_maps_api_key = app.config.get('GOOGLE_MAPS_API_KEY', '')
    print(f"🔍 Debug: API Key no calendário = '{google_maps_api_key}' (length: {len(google_maps_api_key)})")
    return render_template('calendario_moderno.html', google_maps_api_key=google_maps_api_key)

@app.route('/visitas')
def pagina_visitas():
    return render_template('visitas.html')

@app.route('/relatorios')
def relatorios():
    return render_template('relatorios.html')

@app.route('/whatsapp')
def whatsapp_config():
    return render_template('whatsapp_config.html')

@app.route('/contatos')
def contatos():
    return render_template('contatos_moderno.html')

@app.route('/questionarios-obrigatorios')
def questionarios_obrigatorios():
    return render_template('questionarios_obrigatorios.html')

@app.route('/configuracoes')
def configuracoes():
    return render_template('configuracoes.html')

@app.route('/produtividade')
def produtividade():
    return render_template('produtividade.html')

@app.route('/mapa-progresso')
def mapa_progresso():
    google_maps_api_key = app.config.get('GOOGLE_MAPS_API_KEY', '')
    print(f"🔍 Debug: API Key no route = '{google_maps_api_key}' (length: {len(google_maps_api_key)})")
    return render_template('mapa_progresso.html', google_maps_api_key=google_maps_api_key)

@app.route('/assistente-abordagem')
def assistente_abordagem():
    return render_template('assistente_abordagem.html')

@app.route('/analise-resistencia')
def analise_resistencia():
    return render_template('analise_resistencia.html')

@app.route('/sistema-alertas')
def sistema_alertas():
    return render_template('sistema_alertas.html')

@app.route('/material-apoio')
def material_apoio():
    return render_template('material_apoio.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    return redirect(url_for('login'))

@app.route('/teste-mapa-progresso')
def teste_mapa_progresso():
    return send_from_directory('.', 'teste_mapa_progresso.html')

@app.route('/offline')
def offline():
    return render_template('offline.html')

@app.route('/dashboard-offline')
def dashboard_offline():
    """Dashboard completo para gerenciamento do sistema offline"""
    return render_template('dashboard_offline.html')

@app.route('/entidades-offline')
def entidades_offline():
    """Visualização de entidades disponíveis para modo offline"""
    return render_template('entidades_offline.html')

@app.route('/sync-monitor')
def sync_monitor():
    """Monitor de sincronização em tempo real"""
    return render_template('sync_monitor.html')

@app.route('/otimizador-rotas')
def route_optimizer():
    """Otimizador inteligente de rotas"""
    return render_template('route_optimizer.html')


@app.route('/analytics-dashboard')
def analytics_dashboard():
    """Dashboard de Analytics Avançados"""
    return render_template('analytics_dashboard.html')


@app.route('/business-intelligence')
def business_intelligence():
    """Dashboard de Business Intelligence Automatizado"""
    return render_template('business_intelligence.html')

@app.route('/clear-cache')
def clear_cache():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'clear_pwa_cache.html')

@app.route('/force-update')
def force_update():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'force_pwa_update.html')

@app.route('/sw.js')
def service_worker():
    from flask import make_response
    response = make_response(send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'sw.js'))
    response.headers['Content-Type'] = 'text/javascript'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

# API Routes
@app.route('/api/visitas', methods=['GET'])
def get_visitas():
    """Retorna a lista de visitas ordenada por data e hora_inicio (mais próximas primeiro)."""
    try:
        print('--- INICIANDO GET /api/visitas ---')
        
        # Limit results for performance and add pagination if needed
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Use eager loading to prevent N+1 queries if there are relationships
        query = Visita.query.order_by(Visita.data.asc(), Visita.hora_inicio.asc())
        
        # Apply limit and offset
        if limit > 0:
            query = query.offset(offset).limit(min(limit, 500))  # Cap at 500 for safety
        
        visitas = query.all()
        print(f'Qtd visitas encontradas: {len(visitas)}')
        
        visitas_dict = []
        for v in visitas:
            try:
                visitas_dict.append(v.to_dict())
            except Exception as e:
                print(f'Erro ao converter visita id={getattr(v, "id", None)} para dict: {e}')
        
        print('--- FIM GET /api/visitas ---')
        
        # Return with pagination metadata
        return jsonify({
            'data': visitas_dict,
            'pagination': {
                'offset': offset,
                'limit': limit,
                'total': len(visitas_dict)
            }
        })
    except Exception as e:
        import traceback
        print('ERRO GERAL NO GET /api/visitas:', str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def _validate_input_data(data, required_fields):
    """Validate input data for security and completeness"""
    if not data:
        raise ValueError("No data provided")
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            raise ValueError(f"Campo obrigatório ausente: {field}")
    
    # Sanitize string inputs
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            data[key] = value.strip()[:500]  # Limit length to prevent DoS
    
    return data

@app.route('/api/visitas', methods=['POST'])
def criar_visita():
    """Cria uma nova visita."""
    try:
        print("Recebendo POST em /api/visitas")
        print("request.json:", request.json)
        
        # Validate and sanitize input
        required_fields = ['municipio', 'data', 'hora_inicio', 'local']
        data = _validate_input_data(request.json, required_fields)
        from datetime import datetime, date, time
        # Converter strings para objetos datetime/date/time
        data_visita = datetime.strptime(data['data'], '%Y-%m-%d').date()
        hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        # hora_fim é opcional, será calculada automaticamente se não fornecida
        hora_fim = None
        if 'hora_fim' in data and data['hora_fim']:
            hora_fim = datetime.strptime(data['hora_fim'], '%H:%M').time()
        visita = Visita(
            municipio=data['municipio'],
            data=data_visita,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            local=data['local'],
            tipo_pesquisa=data.get('tipo_pesquisa', 'MRS'),
            tipo_informante=data.get('tipo_informante', 'prefeitura'),
            observacoes=data.get('observacoes', ''),
            status='agendada',
            # Novos campos de entidade
            entidade_nome=data.get('entidade_nome'),
            entidade_cnpj=data.get('entidade_cnpj'),
            entidade_categoria=data.get('entidade_categoria'),
            responsavel_cargo=data.get('responsavel_cargo'),
            entidade_endereco=data.get('entidade_endereco'),
            entidade_servicos=data.get('entidade_servicos')
        )
        
        # Adicionar telefone se fornecido
        if 'telefone' in data and data['telefone']:
            visita.telefone_responsavel = data['telefone']
        db.session.add(visita)
        db.session.commit()  # Gera o ID da visita
        
        # Backup automático após criar visita crítica
        backup_service = obter_backup_service()
        backup_service.criar_backup_agora()
        checklist = Checklist(visita_id=visita.id)
        db.session.add(checklist)
        db.session.commit()
        visita.checklist_id = checklist.id
        db.session.add(visita)
        db.session.commit()
        
        # CRIAR QUESTIONÁRIOS AUTOMATICAMENTE PARA A VISITA
        from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
        questionarios_criados = EntidadeIdentificada.criar_questionarios_para_visita(
            visita.id, 
            visita.municipio, 
            visita.tipo_pesquisa, 
            visita.local
        )
        
        # Tentar enviar WhatsApp automaticamente se configurado
        try:
            from gestao_visitas.services.whatsapp_business import whatsapp_service
            
            # Verificar se há telefone nos dados
            telefone = data.get('telefone') or data.get('contato')
            if telefone and whatsapp_service.access_token:
                visita_dict = visita.to_dict()
                visita_dict['telefone'] = telefone
                visita_dict['pesquisador_responsavel'] = data.get('pesquisador_responsavel', 'Pesquisador IBGE')
                
                resultado_whats = whatsapp_service.enviar_agendamento_automatico(visita_dict)
                
                if resultado_whats.get('sucesso'):
                    # Adicionar nas observações que WhatsApp foi enviado
                    obs_atual = visita.observacoes or ''
                    nova_obs = f"{obs_atual}\n[WhatsApp] Agendamento enviado automaticamente em {resultado_whats.get('timestamp', '')}"
                    visita.observacoes = nova_obs.strip()
                    db.session.commit()
                    
                    print(f"WhatsApp enviado automaticamente para visita {visita.id}")
                else:
                    print(f"Falha ao enviar WhatsApp para visita {visita.id}: {resultado_whats.get('erro', 'Erro desconhecido')}")
            
        except Exception as whats_error:
            print(f"Erro na integração WhatsApp: {whats_error}")
            # Não falhar a criação da visita por causa do WhatsApp
        
        return jsonify(visita.to_dict()), 201
    except Exception as e:
        import traceback
        db.session.rollback()
        print("Erro ao criar visita:", str(e))
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visitas/<int:visita_id>/status', methods=['POST'])
def atualizar_status_visita(visita_id):
    try:
        data = request.get_json()
        novo_status = data.get('status')
        
        if not novo_status:
            return jsonify({'error': 'Status não informado'}), 400
            
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
            
        try:
            visita.atualizar_status(novo_status)
            db.session.commit()
            
            # SINCRONIZAR QUESTIONÁRIOS COM STATUS DA VISITA
            from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
            entidades_sincronizadas = EntidadeIdentificada.sincronizar_entidades_por_visita(visita_id)
            
            # Recalcular progresso do município se há entidades vinculadas
            if entidades_sincronizadas > 0:
                from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
                ProgressoQuestionarios.calcular_progresso_municipio(visita.municipio)
            
            return jsonify({
                'message': 'Status atualizado e questionários sincronizados',
                'status': visita.status,
                'data_atualizacao': visita.data_atualizacao.strftime('%d/%m/%Y %H:%M'),
                'entidades_sincronizadas': entidades_sincronizadas
            })
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
            
    except Exception as e:
        db.session.rollback()
        print(f'Erro ao atualizar status: {str(e)}')
        return jsonify({'error': f'Erro ao atualizar status: {str(e)}'}), 500

@app.route('/api/visitas/<int:visita_id>', methods=['DELETE'])
def excluir_visita(visita_id):
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
            
        if not visita.pode_ser_excluida():
            return jsonify({'error': 'Esta visita não pode ser excluída no status atual'}), 400
            
        if Visita.excluir_visita(visita_id):
            return jsonify({'message': 'Visita excluída com sucesso'})
        else:
            return jsonify({'error': 'Erro ao excluir visita'}), 500
            
    except Exception as e:
        db.session.rollback()
        print(f'Erro ao excluir visita: {str(e)}')
        return jsonify({'error': f'Erro ao excluir visita: {str(e)}'}), 500

@app.route('/api/visitas/<int:visita_id>/status-inteligente', methods=['GET'])
def get_status_inteligente(visita_id):
    """Endpoint para obter status inteligente da visita com detalhes completos."""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
        
        # Obter informações detalhadas do status inteligente
        status_inteligente = visita.calcular_status_inteligente()
        progresso_checklist = visita.obter_progresso_checklist()
        status_questionarios = visita.obter_status_questionarios()
        proxima_acao = visita.recomendar_proxima_acao()
        progresso_completo = visita.calcular_progresso_completo()
        
        return jsonify({
            'visita_id': visita_id,
            'status_atual': visita.status,
            'status_inteligente': status_inteligente,
            'progresso_checklist': progresso_checklist,
            'status_questionarios': status_questionarios,
            'proxima_acao': proxima_acao,
            'progresso_completo': progresso_completo,
            'municipio': visita.municipio,
            'tipo_pesquisa': visita.tipo_pesquisa,
            'data_visita': visita.data.strftime('%Y-%m-%d') if visita.data else None,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f'Erro ao obter status inteligente: {str(e)}')
        return jsonify({'error': f'Erro ao obter status inteligente: {str(e)}'}), 500

@app.route('/api/visitas/dashboard-inteligente', methods=['GET'])
def get_dashboard_inteligente():
    """Endpoint para dashboard com análise inteligente de todas as visitas + visitas obrigatórias."""
    try:
        municipio = request.args.get('municipio')
        tipo_pesquisa = request.args.get('tipo_pesquisa')
        
        # Filtrar visitas conforme parâmetros
        query = Visita.query
        if municipio:
            query = query.filter_by(municipio=municipio)
        if tipo_pesquisa:
            query = query.filter_by(tipo_pesquisa=tipo_pesquisa)
        
        visitas = query.all()
        
        # Estatísticas gerais
        total_visitas = len(visitas)
        estatisticas = {
            'total_visitas': total_visitas,
            'por_status': {},
            'por_status_inteligente': {},
            'progresso_medio': 0,
            'questionnaire_completion': {
                'mrs': {'respondido': 0, 'validado': 0},
                'map': {'respondido': 0, 'validado': 0}
            },
            'checklist_progress': {
                'preparacao': 0,
                'execucao': 0,
                'finalizacao': 0
            },
            'proximas_acoes': {}
        }
        
        soma_progresso = 0
        for visita in visitas:
            # Status atual
            status_atual = visita.status
            if status_atual not in estatisticas['por_status']:
                estatisticas['por_status'][status_atual] = 0
            estatisticas['por_status'][status_atual] += 1
            
            # Status inteligente
            status_inteligente = visita.calcular_status_inteligente()
            if status_inteligente not in estatisticas['por_status_inteligente']:
                estatisticas['por_status_inteligente'][status_inteligente] = 0
            estatisticas['por_status_inteligente'][status_inteligente] += 1
            
            # Progresso
            progresso = visita.calcular_progresso_completo()
            soma_progresso += progresso['progresso_total']
            
            # Estatísticas de questionários
            status_quest = visita.obter_status_questionarios()
            estatisticas['questionnaire_completion']['mrs']['respondido'] += status_quest['mrs']['respondido']
            estatisticas['questionnaire_completion']['mrs']['validado'] += status_quest['mrs']['validado_concluido']
            estatisticas['questionnaire_completion']['map']['respondido'] += status_quest['map']['respondido']
            estatisticas['questionnaire_completion']['map']['validado'] += status_quest['map']['validado_concluido']
            
            # Progresso checklist
            progresso_checklist = visita.obter_progresso_checklist()
            estatisticas['checklist_progress']['preparacao'] += progresso_checklist['antes']
            estatisticas['checklist_progress']['execucao'] += progresso_checklist['durante']
            estatisticas['checklist_progress']['finalizacao'] += progresso_checklist['apos']
            
            # Próximas ações
            proxima_acao = visita.recomendar_proxima_acao()
            if proxima_acao not in estatisticas['proximas_acoes']:
                estatisticas['proximas_acoes'][proxima_acao] = 0
            estatisticas['proximas_acoes'][proxima_acao] += 1
        
        # Calcular médias
        if total_visitas > 0:
            estatisticas['progresso_medio'] = soma_progresso / total_visitas
            estatisticas['checklist_progress']['preparacao'] /= total_visitas
            estatisticas['checklist_progress']['execucao'] /= total_visitas
            estatisticas['checklist_progress']['finalizacao'] /= total_visitas
        
        # === NOVO: INFORMAÇÕES DE VISITAS OBRIGATÓRIAS ===
        try:
            from gestao_visitas.models.visitas_obrigatorias import StatusVisitasObrigatorias
            from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
            
            visitas_obrigatorias_info = {}
            
            if municipio and municipio in MUNICIPIOS_PNSB:
                # Status específico do município
                status_vo = StatusVisitasObrigatorias.query.filter_by(municipio=municipio).first()
                if status_vo:
                    visitas_obrigatorias_info = {
                        'municipio_especifico': status_vo.to_dict(),
                        'resumo_integrado': {
                            'visitas_obrigatorias_concluidas': f"{status_vo.concluidas}/{status_vo.total_obrigatorias}",
                            'visitas_pendentes': status_vo.nao_agendadas + status_vo.agendadas,
                            'percentual_visitas': status_vo.percentual_conclusao,
                            'tem_urgencias': status_vo.visitas_urgentes > 0,
                            'status_integrado': f"Questionários: {estatisticas.get('questionnaire_completion', {}).get('total_validados', 0)} validados | Visitas: {status_vo.concluidas} concluídas"
                        }
                    }
            else:
                # Resumo geral de todos os municípios
                todos_status = StatusVisitasObrigatorias.query.all()
                if todos_status:
                    total_vo = sum(s.total_obrigatorias for s in todos_status)
                    total_concluidas = sum(s.concluidas for s in todos_status)
                    total_urgentes = sum(s.visitas_urgentes for s in todos_status)
                    
                    visitas_obrigatorias_info = {
                        'resumo_geral': {
                            'total_visitas_obrigatorias': total_vo,
                            'total_concluidas': total_concluidas,
                            'percentual_geral': (total_concluidas / total_vo * 100) if total_vo > 0 else 0,
                            'municipios_completos': sum(1 for s in todos_status if s.percentual_p1 == 100.0),
                            'total_urgentes': total_urgentes,
                            'municipios_com_urgencias': sum(1 for s in todos_status if s.visitas_urgentes > 0)
                        },
                        'por_municipio': [s.to_dict() for s in todos_status[:5]]  # Primeiros 5 para exemplo
                    }
            
        except Exception as e:
            visitas_obrigatorias_info = {'erro': f'Erro ao buscar visitas obrigatórias: {str(e)}'}

        return jsonify({
            'estatisticas': estatisticas,
            'visitas_obrigatorias': visitas_obrigatorias_info,  # NOVO CAMPO
            'filtros': {
                'municipio': municipio,
                'tipo_pesquisa': tipo_pesquisa
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f'Erro ao obter dashboard inteligente: {str(e)}')
        return jsonify({'error': f'Erro ao obter dashboard inteligente: {str(e)}'}), 500

@app.route('/api/checklist', methods=['GET'])
def get_checklist():
    checklist = Checklist.query.first()
    return jsonify(checklist.to_dict() if checklist else None)

@app.route('/api/checklist', methods=['POST'])
def atualizar_checklist():
    data = request.json
    checklist = Checklist.query.first()
    if not checklist:
        checklist = Checklist()
        db.session.add(checklist)
    
    for categoria in ['materiais', 'documentos', 'equipamentos']:
        for item, status in data[categoria].items():
            checklist.atualizar_status(categoria, item, status['status'])
    
    db.session.commit()
    return jsonify(checklist.to_dict())

@app.route('/api/relatorios/<periodo>', methods=['GET'])
def get_relatorio(periodo):
    try:
        if periodo == 'hoje':
            data_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        elif periodo == 'semana':
            data_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            data_fim = data_inicio + timedelta(days=7)
        elif periodo == 'mes':
            data_inicio = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if data_inicio.month == 12:
                data_fim = datetime(data_inicio.year + 1, 1, 1) - timedelta(days=1)
            else:
                data_fim = datetime(data_inicio.year, data_inicio.month + 1, 1) - timedelta(days=1)
        else:
            inicio_param = request.args.get('inicio')
            fim_param = request.args.get('fim')
            if not inicio_param or not fim_param:
                return jsonify({'error': 'Parâmetros inicio e fim são obrigatórios'}), 400
            data_inicio = datetime.strptime(inicio_param, '%Y-%m-%d')
            data_fim = datetime.strptime(fim_param, '%Y-%m-%d')
        
        # Buscar visitas do período
        visitas = Visita.query.filter(
            Visita.data >= data_inicio.date() if hasattr(data_inicio, 'date') else data_inicio,
            Visita.data <= data_fim.date() if hasattr(data_fim, 'date') else data_fim
        ).all()
        
        try:
            relatorio = relatorio_service.gerar_relatorio_periodo(visitas, data_inicio, data_fim)
            return jsonify(relatorio)
        except Exception as service_error:
            print(f"Erro no RelatorioService: {service_error}")
            # Fallback com dados básicos
            return jsonify({
                'id': f"rel_fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'tipo': 'periodo',
                'data_geracao': datetime.now().isoformat(),
                'periodo': {
                    'inicio': data_inicio.isoformat(),
                    'fim': data_fim.isoformat()
                },
                'resumo': {
                    'total_visitas': len(visitas),
                    'por_status': {},
                    'por_municipio': {}
                },
                'fallback': True,
                'erro': str(service_error)
            })
            
    except Exception as e:
        print(f"Erro geral em get_relatorio: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Erro ao gerar relatório: {str(e)}'}), 500

@app.route('/api/rota', methods=['POST'])
def calcular_rota():
    data = request.json
    resultado = mapa_service.calcular_rota(data['origem'], data['destino'])
    return jsonify(resultado)

# Cache simples para respostas comuns e rate limiting
CHAT_CACHE = {}
CHAT_REQUESTS = defaultdict(deque)  # Rate limiting por IP
MAX_CHAT_REQUESTS_PER_HOUR = 10

RESPOSTAS_PREDEFINIDAS = {
    'como agendar visita': 'Para agendar uma visita, acesse o menu "Visitas" e clique em "Agendar Nova Visita". Preencha os dados do município, data e observações.',
    'como funciona o sistema': 'Este é o Sistema PNSB 2024 para gestão de visitas de campo em 11 municípios de SC. Inclui agendamento, checklists, questionários obrigatórios e relatórios.',
    'quais municipios': 'O sistema cobre 11 municípios: Balneário Camboriú, Balneário Piçarras, Bombinhas, Camboriú, Itajaí, Itapema, Luiz Alves, Navegantes, Penha, Porto Belo e Ilhota.',
    'questionarios obrigatorios': 'Existem questionários MRS (Manejo de Resíduos Sólidos) e MAP (Manejo de Águas Pluviais) com sistema de prioridades P1/P2/P3.',
    'sistema prioridades': 'P1: Crítica (Prefeituras + Lista UF), P2: Importante (Identificadas em campo), P3: Opcional (Recursos disponíveis).',
    'como usar mapa': 'O mapa de progresso mostra o status das visitas por município com cores: verde (concluído), amarelo (em andamento), vermelho (pendente).',
    'backup dados': 'O sistema faz backup automático a cada 5 minutos. Os backups ficam em gestao_visitas/backups_automaticos/',
    'relatorios': 'Acesse "Relatórios" para ver estatísticas de visitas, progresso por município e exportar dados em CSV/Excel.'
}

@app.route('/api/chat', methods=['POST'])
def chat_ia():
    """
    Chat IA otimizado com cache, respostas predefinidas e rate limiting para reduzir custos
    """
    # Rate limiting por IP
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', '127.0.0.1'))
    now = time.time()
    
    # Limpar requisições antigas (mais de 1 hora)
    user_requests = CHAT_REQUESTS[client_ip]
    while user_requests and user_requests[0] < now - 3600:
        user_requests.popleft()
    
    # Verificar limite de requisições
    if len(user_requests) >= MAX_CHAT_REQUESTS_PER_HOUR:
        return jsonify({
            'error': f'Limite de {MAX_CHAT_REQUESTS_PER_HOUR} perguntas por hora atingido.',
            'message': 'Use as funcionalidades do sistema ou consulte a documentação.',
            'reset_time': 'Limite resetado a cada hora'
        }), 429
    
    data = request.json
    user_message = data.get('message', '').strip().lower()
    
    if not user_message:
        return jsonify({'error': 'Mensagem não enviada'}), 400
    
    # 1. Verificar cache de respostas
    if user_message in CHAT_CACHE:
        return jsonify({'response': CHAT_CACHE[user_message], 'source': 'cache'})
    
    # 2. Verificar respostas predefinidas (evita API)
    for pergunta, resposta in RESPOSTAS_PREDEFINIDAS.items():
        if pergunta in user_message:
            CHAT_CACHE[user_message] = resposta
            return jsonify({'response': resposta, 'source': 'predefinida'})
    
    # 3. Verificar se Chat IA está habilitado
    if not CHAT_IA_HABILITADO:
        return jsonify({
            'error': 'Chat IA desabilitado para economizar custos',
            'message': 'Use o menu de navegação ou consulte a documentação do sistema.',
            'suggestions': [
                'Acesse "Visitas" para agendar',
                'Use "Mapa de Progresso" para acompanhar',
                'Consulte "Questionários Obrigatórios"',
                'Verifique "Relatórios" para estatísticas'
            ]
        }), 503
    
    # 4. Verificar se API está disponível
    if not GOOGLE_API_KEY:
        return jsonify({
            'error': 'Chat IA temporariamente indisponível',
            'suggestions': [
                'Consulte a documentação PNSB',
                'Use as funcionalidades do menu lateral',
                'Verifique o mapa de progresso'
            ]
        }), 503
    
    # 4. Limitar tamanho da mensagem (reduzir tokens)
    if len(user_message) > 500:
        return jsonify({'error': 'Mensagem muito longa. Use no máximo 500 caracteres.'}), 400
    
    # 5. Usar modelo mais barato (gemini-1.5-flash em vez de pro)
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"Responda em português, de forma concisa (máximo 200 palavras) sobre o sistema PNSB: {user_message}"}]}
        ],
        "generationConfig": {
            "maxOutputTokens": 150,  # Limitar tokens de saída
            "temperature": 0.3       # Menor criatividade = mais eficiente
        }
    }
    
    # Usar modelo flash (mais barato)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GOOGLE_API_KEY}"
    
    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()
        result = response.json()
        resposta = result['candidates'][0]['content']['parts'][0]['text']
        
        # Registrar uso da API para rate limiting
        user_requests.append(now)
        
        # Cache a resposta para futuras consultas
        CHAT_CACHE[user_message] = resposta
        
        # Limitar cache a 100 entradas
        if len(CHAT_CACHE) > 100:
            CHAT_CACHE.clear()
        
        return jsonify({
            'response': resposta, 
            'source': 'gemini-flash',
            'requests_remaining': MAX_CHAT_REQUESTS_PER_HOUR - len(user_requests)
        })
        
    except requests.exceptions.RequestException as e:
        print(f"Erro de rede no /api/chat: {e}")
        return jsonify({
            'error': 'Serviço temporariamente indisponível',
            'fallback': 'Consulte a documentação do sistema ou use o menu de navegação.'
        }), 502
    except KeyError as e:
        print(f"Erro de formato na resposta da API: {e}")
        return jsonify({'error': 'Resposta inválida do serviço de IA'}), 502
    except Exception as e:
        print(f"Erro inesperado no /api/chat: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/checklist/<int:visita_id>', methods=['GET'])
def get_checklist_por_visita(visita_id):
    try:
        checklist = Checklist.query.filter_by(visita_id=visita_id).first()
        if not checklist:
            # Cria checklist se não existir
            checklist = Checklist(visita_id=visita_id)
            db.session.add(checklist)
            db.session.commit()
        return jsonify(checklist.to_dict())
    except Exception as e:
        print(f"Erro ao buscar checklist da visita {visita_id}: {e}")
        return jsonify({'error': f'Erro ao buscar checklist: {str(e)}'}), 500

@app.route('/api/checklist/<int:visita_id>', methods=['POST'])
def salvar_checklist(visita_id):
    visita = Visita.query.get(visita_id)
    if not visita:
        return jsonify({'error': 'Visita não encontrada'}), 404
    dados = request.json.get('dados', {})
    etapa = request.json.get('etapa')
    if not etapa:
        return jsonify({'error': 'Etapa não informada'}), 400
    checklist = visita.checklist or Checklist()
    campos_etapa = get_campos_etapa(etapa)
    for campo in campos_etapa:
        if campo in dados:
            setattr(checklist, campo, dados[campo])
    # Salvar observações por etapa
    if etapa == 'Antes da Visita' and 'observacoes_0' in dados:
        checklist.observacoes_antes = dados['observacoes_0']
    if etapa == 'Durante a Visita' and 'observacoes_1' in dados:
        checklist.observacoes_durante = dados['observacoes_1']
    if etapa == 'Após a Visita' and 'observacoes_2' in dados:
        checklist.observacoes_apos = dados['observacoes_2']
    # Salvar itens marcados separadamente para cada checklist
    if 'itens_marcados' in dados:
        checklist.itens_marcados = dados['itens_marcados']
    visita.checklist = checklist
    db.session.add(visita)
    db.session.commit()
    return jsonify({'message': 'Checklist salvo com sucesso'})

def get_campos_etapa(etapa):
    if etapa == 'Antes da Visita':
        return ['cracha_ibge', 'recibo_entrega', 'questionario_mrs_impresso', 'questionario_map_impresso',
                'carta_oficial', 'questionario_mrs_digital', 'questionario_map_digital', 'manual_pnsb',
                'guia_site_externo', 'card_contato', 'audio_explicativo', 'planejamento_rota', 'agenda_confirmada']
    elif etapa == 'Durante a Visita':
        return ['apresentacao_ibge', 'explicacao_objetivo', 'explicacao_estrutura', 'explicacao_data_referencia',
                'explicacao_prestador', 'explicacao_servicos', 'explicacao_site_externo', 'explicacao_pdf_editavel',
                'validacao_prestadores', 'registro_contatos', 'assinatura_informante', 'observacoes_durante']
    elif etapa == 'Após a Visita':
        return ['devolucao_materiais', 'registro_followup', 'combinacao_entrega', 'combinacao_acompanhamento', 'observacoes_finais']
    return []

@app.route('/api/visitas/<int:visita_id>', methods=['GET', 'PUT'])
def visita_detail(visita_id):
    if request.method == 'GET':
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
        return jsonify(visita.to_dict()), 200
    
    # PUT
    try:
        print(f'Recebido PUT para visita_id={visita_id}')
        # Validar dados recebidos
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400

        # Validar campos obrigatórios
        campos_obrigatorios = ['municipio', 'data', 'hora_inicio', 'local', 'tipo_pesquisa']
        for campo in campos_obrigatorios:
            if not data.get(campo):
                return jsonify({'error': f'Campo {campo} é obrigatório'}), 400

        # Validar formato da data (sem restrição de data passada)
        try:
            data_visita = datetime.strptime(data['data'], '%Y-%m-%d').date()
            print(f'Data da visita válida: {data_visita}')
        except ValueError:
            return jsonify({'error': 'Formato de data inválido. Use YYYY-MM-DD'}), 400

        # Validar formato da hora
        try:
            hora_inicio = datetime.strptime(data['hora_inicio'], '%H:%M').time()
        except ValueError:
            return jsonify({'error': 'Formato de hora inválido. Use HH:MM'}), 400

        # Validar tipo de pesquisa
        if data['tipo_pesquisa'] not in ['MRS', 'MAP', 'ambos']:
            return jsonify({'error': 'Tipo de pesquisa inválido. Use MRS, MAP ou ambos'}), 400

        # Validar município
        municipios_validos = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        if data['municipio'] not in municipios_validos:
            return jsonify({'error': 'Município inválido'}), 400

        # Buscar visita no banco
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404

        # Verificar se a visita pode ser editada
        if not visita.pode_ser_editada():
            return jsonify({'error': 'Esta visita não pode ser editada no status atual'}), 400

        # Atualizar dados
        visita.municipio = data['municipio']
        visita.data = data_visita
        visita.hora_inicio = hora_inicio
        visita.hora_fim = hora_inicio  # Mantendo o mesmo horário para início e fim
        visita.local = data['local']
        visita.tipo_pesquisa = data['tipo_pesquisa']
        visita.tipo_informante = data.get('tipo_informante', 'prefeitura')
        visita.observacoes = data.get('observacoes', '')
        
        # Atualizar telefone se fornecido
        if 'telefone' in data:
            visita.telefone_responsavel = data.get('telefone')
        
        visita.data_atualizacao = datetime.now()

        # Salvar alterações
        db.session.commit()
        
        # Backup automático após editar visita
        backup_service = obter_backup_service()
        backup_service.criar_backup_agora()

        return jsonify(visita.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        print(f'Erro ao atualizar visita: {str(e)}')
        return jsonify({'error': f'Erro ao atualizar visita: {str(e)}'}), 500

@app.route('/api/contatos', methods=['GET'])
def listar_contatos():
    try:
        contatos = Contato.query.all()
        return jsonify([contato.to_dict() for contato in contatos])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/contatos/importar', methods=['POST'])
def importar_contatos():
    try:
        if 'arquivo' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        arquivo = request.files['arquivo']
        if arquivo.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if not arquivo.filename.endswith('.csv'):
            return jsonify({'error': 'Arquivo deve ser CSV'}), 400
        
        # Ler arquivo CSV
        df = pd.read_csv(arquivo)
        
        # Processar cada linha
        for _, row in df.iterrows():
            municipio = row['Município']
            campo = row['Campo']
            
            # Criar ou atualizar contato
            contato = Contato.query.filter_by(
                municipio=municipio,
                tipo_pesquisa='MRS' if 'MRS' in arquivo.filename else 'MAP'
            ).first()
            
            if not contato:
                contato = Contato(
                    municipio=municipio,
                    tipo_pesquisa='MRS' if 'MRS' in arquivo.filename else 'MAP',
                    tipo_entidade=TipoEntidade.PREFEITURA.value
                )
            
            # Atualizar campos
            if campo == 'Local':
                contato.local = row['Mais provável']
                contato.fonte_local = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Responsavel':
                contato.responsavel = row['Mais provável']
                contato.fonte_responsavel = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Endereco':
                contato.endereco = row['Mais provável']
                contato.fonte_endereco = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Contato':
                contato.contato = row['Mais provável']
                contato.fonte_contato = FonteInformacao.MAIS_PROVAVEL.value
            elif campo == 'Horario':
                contato.horario = row['Mais provável']
                contato.fonte_horario = FonteInformacao.MAIS_PROVAVEL.value
            
            db.session.add(contato)
        
        db.session.commit()
        return jsonify({'message': 'Contatos importados com sucesso'})
    
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Erro ao importar contatos: {str(e)}")
        return jsonify({'error': 'Erro ao importar contatos'}), 500

@app.route('/api/contatos_csv')
def contatos_csv():
    arquivos = [
        ('MAP', os.path.join(os.path.dirname(__file__), 'gestao_visitas', 'pesquisa_contatos_prefeituras', 'Comparacao_MAP.csv')),
        ('MRS', os.path.join(os.path.dirname(__file__), 'gestao_visitas', 'pesquisa_contatos_prefeituras', 'Comparacao_MRS.csv'))
    ]
    linhas = []
    
    for tipo, caminho in arquivos:
        try:
            # Tentar múltiplas encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content = None
            
            for encoding in encodings:
                try:
                    with open(caminho, encoding=encoding, errors='strict') as f:
                        content = f.read()
                        break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Fallback com replacement
                with open(caminho, encoding='utf-8', errors='replace') as f:
                    content = f.read()
            
            # Parse CSV content
            import io
            reader = csv.DictReader(io.StringIO(content))
            
            for row in reader:
                municipio = row.get('Município', '').strip()
                campo = row.get('Campo', '').strip()
                chatgpt = row.get('ChatGPT', '').strip()
                gemini = row.get('Gemini', '').strip()
                grok = row.get('Grok', '').strip()
                mais_provavel = row.get('Mais provável', '').strip()
                
                # Pular linhas vazias ou com dados inválidos
                if not municipio or not campo or not any([chatgpt, gemini, grok, mais_provavel]):
                    continue
                
                # Normalizar valores vazios
                def clean_value(value):
                    if value and value.strip():
                        return value.strip()
                    return ''
                
                linha = {
                    'municipio': clean_value(municipio),
                    'campo': clean_value(campo),
                    'chatgpt': clean_value(chatgpt),
                    'gemini': clean_value(gemini),
                    'grok': clean_value(grok),
                    'mais_provavel': clean_value(mais_provavel),
                    'tipo_pesquisa': tipo,
                    'tipo_informante': 'prefeitura'
                }
                
                linhas.append(linha)
                
        except Exception as e:
            app.logger.error(f"Erro ao ler arquivo {caminho}: {str(e)}")
            continue
    
    return jsonify(linhas)

# Registrar todos os blueprints
from gestao_visitas.routes.whatsapp_api import whatsapp_bp
from gestao_visitas.routes.funcionalidades_pnsb_api import funcionalidades_pnsb_bp
from gestao_visitas.routes.melhorias_api import melhorias_bp
from gestao_visitas.routes.api import api_bp
from gestao_visitas.routes.material_apoio_api import material_apoio_bp
from gestao_visitas.routes.questionarios_api import questionarios_bp
from gestao_visitas.routes.geocodificacao_api import geocodificacao_bp
from gestao_visitas.routes.offline_maps_api import offline_maps_bp
from gestao_visitas.routes.route_optimization_api import route_optimization_bp
from gestao_visitas.routes.advanced_analytics_api import advanced_analytics_bp
from gestao_visitas.routes.business_intelligence_api import business_intelligence_bp
from gestao_visitas.routes.backup_sync_api import backup_sync_bp
from gestao_visitas.routes.visitas_obrigatorias_api import visitas_obrigatorias_bp

app.register_blueprint(whatsapp_bp)
app.register_blueprint(funcionalidades_pnsb_bp, url_prefix='/api/pnsb')
app.register_blueprint(melhorias_bp, url_prefix='/api/melhorias')
app.register_blueprint(api_bp, url_prefix='/api/extended')
app.register_blueprint(material_apoio_bp, url_prefix='/api/material-apoio')
app.register_blueprint(questionarios_bp, url_prefix='/api/questionarios')
app.register_blueprint(geocodificacao_bp, url_prefix='/api/geocodificacao')
app.register_blueprint(offline_maps_bp, url_prefix='/api/offline')
app.register_blueprint(route_optimization_bp, url_prefix='/api/routes')
app.register_blueprint(advanced_analytics_bp, url_prefix='/api/analytics')
app.register_blueprint(business_intelligence_bp, url_prefix='/api/bi')
app.register_blueprint(backup_sync_bp, url_prefix='/api/backup')
app.register_blueprint(visitas_obrigatorias_bp, url_prefix='/api/visitas-obrigatorias')


@app.route('/debug')
def debug_visitas():
    return render_template('debug_visitas.html')


@app.route('/api/visitas/progresso-mapa', methods=['GET'])
def get_progresso_mapa():
    """
    API específica para o Mapa de Progresso com dados reais das visitas
    Retorna dados agregados por município focado no follow-up dos questionários
    Agora inclui informações dos questionários obrigatórios (MRS/MAP)
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        
        # Todos os municípios PNSB
        municipios_pnsb = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas',
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves',
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        resultado = []
        
        for municipio in municipios_pnsb:
            # USAR NOVO CÁLCULO DINÂMICO DE PROGRESSO
            progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            # Buscar todas as visitas do município
            visitas = Visita.query.filter_by(municipio=municipio).all()
            
            # Agrupar visitas por tipo de entidade
            entidades_municipio = {}
            for visita in visitas:
                tipo_entidade = visita.tipo_informante or 'prefeitura'
                if tipo_entidade not in entidades_municipio:
                    entidades_municipio[tipo_entidade] = []
                entidades_municipio[tipo_entidade].append(visita)
            
            # Calcular métricas gerais
            total_visitas = len(visitas)
            visitas_agendadas = len([v for v in visitas if v.status in ['agendada', 'em preparação']])
            visitas_executadas = len([v for v in visitas if v.status in ['realizada', 'em follow-up', 'verificação whatsapp', 'finalizada']])
            visitas_em_followup = len([v for v in visitas if v.status in ['em follow-up', 'verificação whatsapp']])
            visitas_finalizadas = len([v for v in visitas if v.status == 'finalizada'])
            
            # Status predominante do município
            if visitas_finalizadas > 0:
                status_municipio = 'finalizado'
                cor_status = '#28a745'  # Verde
            elif visitas_em_followup > 0:
                status_municipio = 'em_followup'
                cor_status = '#ffc107'  # Amarelo
            elif visitas_executadas > 0:
                status_municipio = 'executado'
                cor_status = '#17a2b8'  # Azul
            elif visitas_agendadas > 0:
                status_municipio = 'agendado'
                cor_status = '#6c757d'  # Cinza
            else:
                status_municipio = 'sem_visita'
                cor_status = '#dc3545'  # Vermelho
            
            # Calcular percentual de conclusão
            if total_visitas > 0:
                percentual_conclusao = (visitas_finalizadas / total_visitas) * 100
            else:
                percentual_conclusao = 0
            
            # Calcular tempo desde última atividade
            ultima_atividade = None
            dias_sem_atividade = 0
            if visitas:
                visita_mais_recente = max(visitas, key=lambda v: v.data_atualizacao or v.data_criacao)
                ultima_atividade = visita_mais_recente.data_atualizacao or visita_mais_recente.data_criacao
                dias_sem_atividade = (datetime.now() - ultima_atividade).days
            
            # Alertas de follow-up baseados em critérios PNSB
            alertas = []
            alertas_detalhes = []
            
            # Verificar visitas em follow-up há mais de 7 dias
            if visitas_em_followup > 0 and dias_sem_atividade > 7:
                alertas.append('Follow-up atrasado')
                alertas_detalhes.append({
                    'tipo': 'follow_up_atrasado',
                    'prioridade': 'alta',
                    'dias': dias_sem_atividade,
                    'visitas_afetadas': visitas_em_followup
                })
            
            # Verificar questionários não iniciados após visita executada
            if visitas_executadas > 0 and visitas_finalizadas == 0 and dias_sem_atividade > 14:
                alertas.append('Questionário não iniciado')
                alertas_detalhes.append({
                    'tipo': 'questionario_pendente',
                    'prioridade': 'critica',
                    'dias': dias_sem_atividade,
                    'visitas_afetadas': visitas_executadas
                })
            
            # Verificar municípios sem visitas agendadas
            if total_visitas == 0:
                alertas.append('Sem visitas agendadas')
                alertas_detalhes.append({
                    'tipo': 'sem_agenda',
                    'prioridade': 'media',
                    'acao_recomendada': 'Agendar visita inicial'
                })
            
            # Verificar follow-up muito antigo (mais de 30 dias)
            if visitas_em_followup > 0 and dias_sem_atividade > 30:
                alertas.append('Follow-up crítico - mais de 30 dias')
                alertas_detalhes.append({
                    'tipo': 'follow_up_critico',
                    'prioridade': 'critica',
                    'dias': dias_sem_atividade,
                    'acao_recomendada': 'Contato urgente com informante'
                })
            
            # Progresso do checklist (se existir)
            progresso_checklist = {'preparacao': 0, 'execucao': 0, 'resultados': 0}
            if visitas:
                # Pegar checklist da visita mais avançada
                visita_principal = visitas[0]
                if hasattr(visita_principal, 'checklist') and visita_principal.checklist:
                    checklist = visita_principal.checklist
                    progresso_checklist = {
                        'preparacao': checklist.calcular_progresso_preparacao(),
                        'execucao': checklist.calcular_progresso_execucao(),
                        'resultados': checklist.calcular_progresso_resultados()
                    }
            
            # Buscar informações dos questionários obrigatórios com novo sistema de prioridades
            questionarios_obrigatorios = QuestionarioObrigatorio.get_questionarios_municipio(municipio)
            entidades_identificadas = EntidadeIdentificada.query.filter_by(municipio=municipio).all()
            
            
            # Buscar dados de progresso consolidado (com prioridades)
            progresso_questionarios = ProgressoQuestionarios.query.filter_by(municipio=municipio).first()
            if not progresso_questionarios:
                progresso_questionarios = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            # Separar entidades por prioridade
            entidades_p1 = [e for e in entidades_identificadas if e.prioridade == 1]  # Crítica
            entidades_p2 = [e for e in entidades_identificadas if e.prioridade == 2]  # Importante  
            entidades_p3 = [e for e in entidades_identificadas if e.prioridade == 3]  # Opcional
            
            # USAR LÓGICA CORRIGIDA - APENAS P1 + P2 (OBRIGATÓRIOS PARA METAS PNSB)
            # P3 não conta para cálculos de metas/deadlines
            entidades_obrigatorias = entidades_p1 + entidades_p2  # Apenas P1 + P2
            
            # USAR NOVO CÁLCULO DINÂMICO DE PROGRESSO (linha 989)
            # Substituir lógica antiga por dados do novo sistema
            total_mrs_obrigatorios = progresso.total_mrs_obrigatorios
            total_map_obrigatorios = progresso.total_map_obrigatorios
            total_questionarios_obrigatorios = total_mrs_obrigatorios + total_map_obrigatorios
            
            # Usar dados do novo sistema de progresso
            mrs_respondidos = progresso.mrs_concluidos
            map_respondidos = progresso.map_concluidos
            mrs_validados = progresso.mrs_validados
            map_validados = progresso.map_validados
            
            # Total concluídos (para relatórios) = respondidos + validados
            mrs_concluidos = mrs_respondidos + mrs_validados
            map_concluidos = map_respondidos + map_validados
            
            # Calcular percentuais baseados nos totais esperados dinâmicos
            percentual_mrs = progresso.percentual_mrs
            percentual_map = progresso.percentual_map
            percentual_questionarios = progresso.percentual_geral
            
            # Métricas específicas do novo sistema de prioridades usando dados dinâmicos
            prioridades_info = {
                'p1': {
                    'total_entidades': len(entidades_p1),
                    'mrs_respondidos': sum(1 for e in entidades_p1 if e.status_mrs == 'respondido'),
                    'map_respondidos': sum(1 for e in entidades_p1 if e.status_map == 'respondido'),
                    'mrs_validados': sum(1 for e in entidades_p1 if e.status_mrs == 'validado_concluido'),
                    'map_validados': sum(1 for e in entidades_p1 if e.status_map == 'validado_concluido'),
                    'mrs_concluidos': sum(1 for e in entidades_p1 if e.status_mrs in ['respondido', 'validado_concluido']),
                    'map_concluidos': sum(1 for e in entidades_p1 if e.status_map in ['respondido', 'validado_concluido']),
                    'percentual_conclusao': progresso.p1_percentual_conclusao,
                    'status': progresso.status_p1,
                    'descricao': 'Crítica (Prefeituras + Lista UF)',
                    'cor': '#dc3545' if progresso.p1_percentual_conclusao < 50 else '#ffc107' if progresso.p1_percentual_conclusao < 100 else '#28a745'
                },
                'p2': {
                    'total_entidades': len(entidades_p2),
                    'mrs_respondidos': sum(1 for e in entidades_p2 if e.status_mrs == 'respondido'),
                    'map_respondidos': sum(1 for e in entidades_p2 if e.status_map == 'respondido'),
                    'mrs_validados': sum(1 for e in entidades_p2 if e.status_mrs == 'validado_concluido'),
                    'map_validados': sum(1 for e in entidades_p2 if e.status_map == 'validado_concluido'),
                    'mrs_concluidos': sum(1 for e in entidades_p2 if e.status_mrs in ['respondido', 'validado_concluido']),
                    'map_concluidos': sum(1 for e in entidades_p2 if e.status_map in ['respondido', 'validado_concluido']),
                    'percentual_conclusao': progresso.p2_percentual_conclusao,
                    'descricao': 'Importante (Identificadas em campo)',
                    'cor': '#dc3545' if progresso.p2_percentual_conclusao < 50 else '#ffc107' if progresso.p2_percentual_conclusao < 100 else '#28a745'
                },
                'p3': {
                    'total_entidades': len(entidades_p3),
                    'mrs_respondidos': sum(1 for e in entidades_p3 if e.status_mrs == 'respondido'),
                    'map_respondidos': sum(1 for e in entidades_p3 if e.status_map == 'respondido'),
                    'mrs_validados': sum(1 for e in entidades_p3 if e.status_mrs == 'validado_concluido'),
                    'map_validados': sum(1 for e in entidades_p3 if e.status_map == 'validado_concluido'),
                    'mrs_concluidos': sum(1 for e in entidades_p3 if e.status_mrs in ['respondido', 'validado_concluido']),
                    'map_concluidos': sum(1 for e in entidades_p3 if e.status_map in ['respondido', 'validado_concluido']),
                    'percentual_conclusao': progresso.p3_percentual_conclusao,
                    'descricao': 'Opcional (Trabalho completo se houver tempo)',
                    'cor': '#6c757d',  # Sempre cinza (informativo, não crítico)
                    'informativo': True,
                    'observacao': 'Não conta para metas PNSB obrigatórias'
                }
            }
            
            # Alertas específicos de prioridades usando dados dinâmicos
            alertas_prioridades = []
            if len(entidades_p1) > 0 and progresso.p1_percentual_conclusao < 100:
                alertas_prioridades.append(f'P1 Crítica: {progresso.p1_percentual_conclusao:.0f}% concluída')
            if len(entidades_p2) > 0 and progresso.p2_percentual_conclusao < 80:
                alertas_prioridades.append(f'P2 Importante: {progresso.p2_percentual_conclusao:.0f}% concluída')
            
            # Agregar alertas de prioridades aos alertas gerais
            alertas.extend(alertas_prioridades)
            
            
            questionarios_info = {
                # MÉTRICAS OBRIGATÓRIAS - APENAS P1 + P2 (BASE PARA METAS PNSB) - USANDO DADOS DINÂMICOS
                'total_mrs_obrigatorios': total_mrs_obrigatorios,
                'total_map_obrigatorios': total_map_obrigatorios,
                'mrs_concluidos': mrs_concluidos,
                'map_concluidos': map_concluidos,
                'percentual_mrs': round(percentual_mrs, 1),
                'percentual_map': round(percentual_map, 1),
                'percentual_questionarios': round(percentual_questionarios, 1),
                'entidades_obrigatorias': len(entidades_p1) + len(entidades_p2),
                'entidades_obrigatorias_pendentes': len([e for e in entidades_p1 + entidades_p2 if e.status_mrs != 'concluido' or e.status_map != 'concluido']),
                
                # MÉTRICAS INFORMATIVAS - P3 (TRABALHO COMPLETO)
                'p3_total_entidades': len(entidades_p3),
                'p3_mrs_concluidos': sum(1 for e in entidades_p3 if e.status_mrs in ['respondido', 'validado_concluido']),
                'p3_map_concluidos': sum(1 for e in entidades_p3 if e.status_map in ['respondido', 'validado_concluido']),
                'p3_percentual': progresso.p3_percentual_conclusao,
                
                # Sistema de prioridades
                'prioridades': prioridades_info,
                'sistema_prioridades_ativo': True,
                'status_p1': progresso.status_p1,
                'percentual_p1': progresso.p1_percentual_conclusao,
                'percentual_p2': progresso.p2_percentual_conclusao,
                'percentual_p3': progresso.p3_percentual_conclusao,
                
                # Clarificação para interface
                'observacao': 'Métricas principais baseadas em P1+P2 (obrigatórios). P3 é informativo para trabalho completo.'
            }
            
            resultado.append({
                'municipio': municipio,
                'status': status_municipio,
                'cor_status': cor_status,
                'resumo': {
                    'total_visitas': total_visitas,
                    'agendadas': visitas_agendadas,
                    'executadas': visitas_executadas,
                    'em_followup': visitas_em_followup,
                    'finalizadas': visitas_finalizadas,
                    'percentual_conclusao': round(percentual_conclusao, 1)
                },
                'timing': {
                    'ultima_atividade': ultima_atividade.isoformat() if ultima_atividade else None,
                    'dias_sem_atividade': dias_sem_atividade,
                    'precisa_followup': dias_sem_atividade > 7 and visitas_em_followup > 0
                },
                'alertas': alertas,
                'alertas_detalhes': alertas_detalhes,
                'progresso_checklist': progresso_checklist,
                'questionarios': questionarios_info,  # Informações dos questionários obrigatórios
                'entidades': {k: len(v) for k, v in entidades_municipio.items()},  # Contagem por tipo de entidade
                'total_entidades': len(entidades_municipio),  # Quantas entidades diferentes
                'coords': get_coordenadas_municipio(municipio)  # Para posicionar no mapa
            })
        
        # Estatísticas gerais
        total_municipios = len(municipios_pnsb)
        municipios_finalizados = len([m for m in resultado if m['status'] == 'finalizado'])
        municipios_em_followup = len([m for m in resultado if m['status'] == 'em_followup'])
        municipios_sem_visita = len([m for m in resultado if m['status'] == 'sem_visita'])
        
        estatisticas_gerais = {
            'total_municipios': total_municipios,
            'finalizados': municipios_finalizados,
            'em_followup': municipios_em_followup,
            'sem_visita': municipios_sem_visita,
            'percentual_conclusao_geral': round((municipios_finalizados / total_municipios) * 100, 1),
            'alertas_ativos': sum(len(m['alertas']) for m in resultado)
        }
        
        return jsonify({
            'success': True,
            'data': resultado,
            'estatisticas': estatisticas_gerais,
            'ultima_atualizacao': datetime.now().isoformat(),
            'message': 'Dados de progresso obtidos com sucesso'
        })
        
    except Exception as e:
        import traceback
        print("Erro ao buscar progresso do mapa:", str(e))
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar dados de progresso'
        }), 500

def get_coordenadas_municipio(municipio):
    """Retorna coordenadas básicas dos municípios PNSB"""
    coordenadas = {
        'Itajaí': [-26.9077, -48.6658],
        'Balneário Camboriú': [-26.9924, -48.6234],
        'Navegantes': [-26.8986, -48.6542],
        'Camboriú': [-27.0236, -48.6581],
        'Itapema': [-27.0890, -48.6114],
        'Penha': [-26.7725, -48.6540],
        'Porto Belo': [-27.1580, -48.5397],
        'Bombinhas': [-27.1339, -48.4817],
        'Balneário Piçarras': [-26.7597, -48.6719],
        'Luiz Alves': [-26.7158, -48.9375],
        'Ilhota': [-26.8997, -48.8231]
    }
    return coordenadas.get(municipio, [-26.9, -48.65])  # Centro aproximado da região

@app.route('/api/entidades/tipos', methods=['GET'])
def get_tipos_entidades():
    """
    Retorna todos os tipos de entidades disponíveis com suas configurações
    """
    try:
        # Importar das configurações locais
        import os
        import sys
        config_path = os.path.join(os.path.dirname(__file__), 'gestao_visitas', 'config.py')
        if os.path.exists(config_path):
            # Executar o arquivo de config para carregar as variáveis
            with open(config_path, 'r', encoding='utf-8') as f:
                config_code = f.read()
            config_vars = {}
            exec(config_code, config_vars)
            TIPOS_ENTIDADE = config_vars.get('TIPOS_ENTIDADE', {})
            CATEGORIAS_ENTIDADE = config_vars.get('CATEGORIAS_ENTIDADE', {})
        else:
            # Fallback para configurações básicas
            TIPOS_ENTIDADE = {
                'prefeitura': {'nome': 'Prefeitura Municipal', 'icone': 'fas fa-university'},
                'empresa_terceirizada': {'nome': 'Empresa Terceirizada', 'icone': 'fas fa-building'},
                'entidade_catadores': {'nome': 'Entidade de Catadores', 'icone': 'fas fa-recycle'},
                'empresa_nao_vinculada': {'nome': 'Empresa Não Vinculada', 'icone': 'fas fa-industry'}
            }
            CATEGORIAS_ENTIDADE = {}
        
        return jsonify({
            'success': True,
            'tipos_entidade': TIPOS_ENTIDADE,
            'categorias': CATEGORIAS_ENTIDADE,
            'message': 'Tipos de entidades obtidos com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar tipos de entidades'
        }), 500

@app.route('/api/entidades/municipio/<municipio>', methods=['GET'])
def get_entidades_municipio(municipio):
    """
    Retorna todas as entidades de um município específico
    """
    try:
        visitas = Visita.query.filter_by(municipio=municipio).all()
        
        # Agrupar por entidade
        entidades = {}
        for visita in visitas:
            tipo_entidade = visita.tipo_informante or 'prefeitura'
            
            # Criar chave única para a entidade
            if visita.entidade_nome:
                chave_entidade = f"{tipo_entidade}_{visita.entidade_nome}"
            else:
                chave_entidade = f"{tipo_entidade}_principal"
            
            if chave_entidade not in entidades:
                entidades[chave_entidade] = {
                    'tipo': tipo_entidade,
                    'nome': visita.entidade_nome or f"{tipo_entidade.title()} Principal",
                    'cnpj': visita.entidade_cnpj,
                    'categoria': visita.entidade_categoria,
                    'endereco': visita.entidade_endereco,
                    'servicos': visita.entidade_servicos,
                    'responsavel_cargo': visita.responsavel_cargo,
                    'telefone': visita.telefone_responsavel,
                    'visitas': [],
                    'progresso': {
                        'total': 0,
                        'agendadas': 0,
                        'executadas': 0,
                        'em_followup': 0,
                        'finalizadas': 0
                    }
                }
            
            # Adicionar visita à entidade
            entidades[chave_entidade]['visitas'].append(visita.to_dict())
            
            # Atualizar contadores
            entidades[chave_entidade]['progresso']['total'] += 1
            
            if visita.status in ['agendada', 'em preparação']:
                entidades[chave_entidade]['progresso']['agendadas'] += 1
            elif visita.status in ['realizada', 'em follow-up', 'verificação whatsapp', 'finalizada']:
                entidades[chave_entidade]['progresso']['executadas'] += 1
            
            if visita.status in ['em follow-up', 'verificação whatsapp']:
                entidades[chave_entidade]['progresso']['em_followup'] += 1
            elif visita.status == 'finalizada':
                entidades[chave_entidade]['progresso']['finalizadas'] += 1
        
        return jsonify({
            'success': True,
            'municipio': municipio,
            'entidades': entidades,
            'total_entidades': len(entidades),
            'message': f'Entidades de {municipio} obtidas com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': f'Erro ao buscar entidades de {municipio}'
        }), 500

@app.route('/backup')
def backup_status_page():
    return render_template('backup_status.html')

@app.route('/api/backup/status')
def backup_status():
    """Retorna o status do sistema de backup."""
    backup_service = obter_backup_service()
    return jsonify(backup_service.obter_estatisticas())

@app.route('/api/backup/emergencial', methods=['POST'])
def backup_emergencial():
    """Cria um backup de emergência."""
    backup_service = obter_backup_service()
    sucesso = backup_service.backup_emergencial()
    if sucesso:
        return jsonify({'message': 'Backup de emergência criado com sucesso', 'sucesso': True})
    else:
        return jsonify({'error': 'Erro ao criar backup de emergência', 'sucesso': False}), 500

# API para otimização de rotas com Google Maps
@app.route('/api/google-maps-config', methods=['GET'])
def get_google_maps_config():
    """Retorna configuração para Google Maps (sem expor a chave diretamente)."""
    try:
        api_key = app.config.get('GOOGLE_MAPS_API_KEY')
        
        # Verificar se GoogleMaps package está disponível
        try:
            import googlemaps
            package_available = True
        except ImportError:
            package_available = False
        
        disponivel = bool(api_key) and package_available
        
        return jsonify({
            'disponivel': disponivel,
            'maps_available': disponivel,  # Compatibilidade
            'google_maps_ready': disponivel,
            'nivel_disponivel': 3 if disponivel else 1,  # Nível 3 com Places API
            'maps_features': {
                'directions': disponivel,
                'distance_matrix': disponivel,
                'geocoding': disponivel,
                'traffic': disponivel,
                'places_api': disponivel,  # Para horários reais
                'business_hours': disponivel
            },
            'status': 'Disponível' if disponivel else 'Não disponível',
            'nivel_otimizacao': 'Nível 3 (Google Maps + Places API)' if disponivel else 'Nível 1 (Algoritmo Local)',
            'recursos_avancados': {
                'horarios_reais': disponivel,
                'transito_tempo_real': disponivel,
                'direcoes_detalhadas': disponivel
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': str(e), 
            'disponivel': False,
            'maps_available': False,
            'nivel_disponivel': 1
        }), 500

@app.route('/api/otimizar-rotas', methods=['POST'])
def otimizar_rotas_api():
    """API para otimização de rotas com Google Maps - Nível 2/3."""
    try:
        data = request.get_json()
        
        if not data or 'visitas' not in data:
            return jsonify({'error': 'Dados de visitas são obrigatórios', 'sucesso': False}), 400
        
        visitas = data['visitas']
        data_jornada = data.get('data_jornada')
        horario_inicio = data.get('horario_inicio', '08:00')
        horario_fim = data.get('horario_fim', '18:00')
        incluir_horarios_reais = data.get('incluir_horarios_reais', True)  # Nível 3
        
        # Importar e usar serviço de otimização
        from gestao_visitas.services.route_optimizer import RouteOptimizer, RoutePoint
        
        print(f"🔧 Iniciando otimização para {len(visitas)} visitas")
        optimizer = RouteOptimizer()
        print(f"✅ RouteOptimizer inicializado. Google Maps disponível: {optimizer.is_google_maps_available()}")
        
        # Converter visitas para RoutePoint
        pontos_rota = []
        for visita in visitas:
            # Obter coordenadas do município
            coordenadas = {
                'Balneário Camboriú': (-26.9906, -48.6349),
                'Balneário Piçarras': (-26.7574, -48.6717),
                'Bombinhas': (-27.1433, -48.4884),
                'Camboriú': (-27.0248, -48.6583),
                'Itajaí': (-26.9076, -48.6619),
                'Itapema': (-27.0890, -48.6114),
                'Luiz Alves': (-26.7169, -48.9357),
                'Navegantes': (-26.8968, -48.6565),
                'Penha': (-26.7711, -48.6506),
                'Porto Belo': (-27.1588, -48.5552),
                'Ilhota': (-26.8984, -48.8269)
            }
            
            municipio = visita.get('municipio', '')
            lat, lng = coordenadas.get(municipio, (-26.9, -48.6))  # Fallback para centro da região
            
            ponto = RoutePoint(
                id=str(visita.get('id', f"ponto_{len(pontos_rota)}")),
                name=f"{municipio} - {visita.get('local', visita.get('informante', 'Entidade'))}",
                lat=lat,
                lng=lng,
                municipality=municipio,
                priority={'p1': 1, 'p2': 2, 'p3': 3}.get(visita.get('prioridade', 'p3'), 3),
                estimated_duration=visita.get('duracao_estimada', 90),
                visit_type=visita.get('tipo_informante', 'standard'),
                time_window_start=visita.get('hora_inicio'),
                time_window_end=visita.get('hora_fim')
            )
            
            # Adicionar informações adicionais para busca no Google Places
            if 'local' in visita:
                ponto.entity_name = visita['local']
            if 'tipo_informante' in visita:
                ponto.entity_type = visita['tipo_informante']
            
            pontos_rota.append(ponto)
        
        print(f"📍 Pontos convertidos: {len(pontos_rota)}")
        for i, ponto in enumerate(pontos_rota[:3]):  # Mostrar apenas os primeiros 3
            print(f"   {i+1}. {ponto.municipality} - {ponto.name}")
        
        # Tentar otimização Nível 2/3 com Google Maps
        print(f"🚀 Iniciando otimização com Google Maps...")
        resultado = optimizer.optimize_route_with_google_maps(
            pontos_rota, 
            target_date=data_jornada,
            start_time=horario_inicio,
            end_time=horario_fim,
            include_business_hours=incluir_horarios_reais
        )
        
        print(f"✅ Resultado da otimização: sucesso={resultado.get('sucesso', False)}")
        if not resultado.get('sucesso', False):
            print(f"❌ Erro: {resultado.get('erro', 'Desconhecido')}")
        
        return jsonify(resultado)
        
    except Exception as e:
        import traceback
        print('Erro na otimização de rotas Nível 2:', str(e))
        traceback.print_exc()
        return jsonify({
            'sucesso': False,
            'error': str(e), 
            'fallback_to_level1': True
        }), 500

# APIs para Verificação por WhatsApp
@app.route('/api/visitas/<int:visita_id>/registrar-email', methods=['POST'])
def registrar_email_enviado(visita_id):
    """Registra que o e-mail foi enviado pelo sistema IBGE."""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
            
        data = request.get_json() or {}
        data_envio = data.get('data_envio')
        
        if data_envio:
            from datetime import datetime
            data_envio = datetime.fromisoformat(data_envio.replace('Z', '+00:00'))
        
        visita.registrar_email_enviado(data_envio)
        db.session.commit()
        
        return jsonify({
            'message': 'E-mail registrado com sucesso',
            'data_envio': visita.email_enviado_em.isoformat() if visita.email_enviado_em else None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visitas/<int:visita_id>/verificacao-whatsapp', methods=['POST'])
def enviar_verificacao_whatsapp(visita_id):
    """Envia verificação por WhatsApp se responsável recebeu e-mail."""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
            
        from gestao_visitas.services.verificacao_whatsapp_service import verificacao_service
        
        sucesso, mensagem = verificacao_service.enviar_verificacao_email(visita)
        
        if sucesso:
            db.session.commit()
            return jsonify({
                'message': mensagem,
                'sucesso': True,
                'status_verificacao': visita.obter_status_verificacao()
            })
        else:
            return jsonify({
                'error': mensagem,
                'sucesso': False
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/visitas/<int:visita_id>/confirmar-email', methods=['POST'])
def confirmar_recebimento_email(visita_id):
    """Confirma se o responsável recebeu o e-mail."""
    try:
        visita = Visita.query.get(visita_id)
        if not visita:
            return jsonify({'error': 'Visita não encontrada'}), 404
            
        data = request.get_json()
        email_recebido = data.get('email_recebido', True)
        
        from gestao_visitas.services.verificacao_whatsapp_service import verificacao_service
        
        sucesso, mensagem = verificacao_service.confirmar_recebimento_email(visita, email_recebido)
        
        if sucesso:
            db.session.commit()
            return jsonify({
                'message': mensagem,
                'sucesso': True,
                'status_verificacao': visita.obter_status_verificacao(),
                'novo_status': visita.status
            })
        else:
            return jsonify({
                'error': mensagem,
                'sucesso': False
            }), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/verificacao-whatsapp/estatisticas')
def estatisticas_verificacao():
    """Retorna estatísticas das verificações por WhatsApp."""
    try:
        from gestao_visitas.services.verificacao_whatsapp_service import verificacao_service
        
        estatisticas = verificacao_service.obter_estatisticas_verificacao()
        return jsonify(estatisticas)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verificacao-whatsapp/pendentes')
def visitas_pendentes_verificacao():
    """Retorna visitas que precisam de verificação."""
    try:
        from gestao_visitas.services.verificacao_whatsapp_service import verificacao_service
        
        visitas_pendentes = verificacao_service.obter_visitas_para_verificacao()
        
        resultado = []
        for item in visitas_pendentes:
            visita = item['visita']
            resultado.append({
                'id': visita.id,
                'municipio': visita.municipio,
                'data': visita.data.strftime('%d/%m/%Y'),
                'telefone': visita.telefone_responsavel,
                'email_enviado_em': visita.email_enviado_em.strftime('%d/%m/%Y %H:%M') if visita.email_enviado_em else None,
                'motivo': item['motivo'],
                'status_verificacao': visita.obter_status_verificacao()
            })
            
        return jsonify(resultado)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# === SISTEMA DE ALERTAS CRÍTICOS ===

@app.route('/api/alertas/criticos', methods=['GET'])
def get_alertas_criticos():
    """Retorna alertas críticos do sistema PNSB 2024 - VERSÃO FUNCIONAL"""
    try:
        from gestao_visitas.services.critical_alerts_service import CriticalAlertsService
        
        # Inicializar serviço de alertas críticos
        alerts_service = CriticalAlertsService(db)
        
        # Obter todos os alertas críticos
        result = alerts_service.get_all_critical_alerts()
        
        # Adaptar formato para compatibilidade com frontend existente
        alertas_adaptados = []
        for alerta in result['alertas']:
            alertas_adaptados.append({
                'id': alerta['id'],
                'nivel': alerta['nivel'],
                'titulo': alerta['titulo'],
                'descricao': alerta['descricao'],
                'municipio': alerta['municipio'],
                'entidade': alerta['entidade'],
                'acao_recomendada': alerta['acao_recomendada'],
                'dias_restantes': alerta['dias_restantes'],
                'timestamp': alerta['timestamp']
            })
        
        # Manter estrutura de resumo compatível
        resumo = result['resumo']
        resumo_adaptado = {
            'total_alertas': resumo['total_alertas'],
            'criticos': resumo['criticos'],
            'urgentes': resumo['urgentes'],
            'atencao': resumo['atencao'],
            'dias_ate_deadline_visitas': resumo['dias_ate_deadline_visitas'],
            'dias_ate_deadline_questionarios': resumo['dias_ate_deadline_questionarios'],
            'status_sistema': resumo['status_sistema']
        }
        
        return jsonify({
            'success': True,
            'data': {
                'alertas': alertas_adaptados,
                'resumo': resumo_adaptado,
                'timestamp_consulta': result['timestamp_consulta'],
                'sistema_avancado': True,  # Indicador de sistema funcional
                'total_tipos_alertas': len(resumo.get('alertas_por_tipo', {})),
                'municipios_com_alertas': resumo.get('municipios_com_alertas', 0)
            },
            'message': f"Alertas avançados carregados: {len(alertas_adaptados)} encontrados ({resumo['criticos']} críticos)"
        })
        
    except Exception as e:
        logger.error(f"Erro no sistema avançado de alertas: {e}")
        
        # Fallback para sistema básico em caso de erro
        try:
            from datetime import timedelta
            
            hoje = datetime.now()
            deadline_visitas = datetime(2025, 9, 19)
            deadline_questionarios = datetime(2025, 10, 17)
            
            dias_visitas = (deadline_visitas - hoje).days
            dias_questionarios = (deadline_questionarios - hoje).days
            
            alertas_basicos = []
            
            if dias_visitas <= 60:
                nivel = 'critico' if dias_visitas <= 30 else 'urgente'
                alertas_basicos.append({
                    'id': f'deadline_visitas_{nivel}',
                    'nivel': nivel,
                    'titulo': f'🚨 DEADLINE VISITAS: {dias_visitas} dias restantes',
                    'descricao': 'Prazo crítico para visitas P1+P2',
                    'municipio': 'TODOS',
                    'entidade': None,
                    'acao_recomendada': 'Acelerar execução imediatamente',
                    'dias_restantes': dias_visitas,
                    'timestamp': hoje.isoformat()
                })
            
            resumo_basico = {
                'total_alertas': len(alertas_basicos),
                'criticos': len([a for a in alertas_basicos if a['nivel'] == 'critico']),
                'urgentes': len([a for a in alertas_basicos if a['nivel'] == 'urgente']),
                'atencao': 0,
                'dias_ate_deadline_visitas': dias_visitas,
                'dias_ate_deadline_questionarios': dias_questionarios,
                'status_sistema': 'critico' if any(a['nivel'] == 'critico' for a in alertas_basicos) else 'normal'
            }
            
            return jsonify({
                'success': True,
                'data': {
                    'alertas': alertas_basicos,
                    'resumo': resumo_basico,
                    'timestamp_consulta': hoje.isoformat(),
                    'sistema_avancado': False,  # Indicador de fallback
                    'fallback_reason': str(e)
                },
                'message': f"Alertas básicos (fallback): {len(alertas_basicos)} encontrados"
            })
            
        except Exception as fallback_error:
            return jsonify({
                'success': False,
                'error': f"Erro crítico no sistema de alertas: {str(fallback_error)}"
            }), 500

# Registrar blueprints
app.register_blueprint(ibge_bp)
app.register_blueprint(auto_scheduler_bp)
app.register_blueprint(strategy_assistant_bp)
app.register_blueprint(critical_alerts_bp)
app.register_blueprint(timeline_bp)
app.register_blueprint(google_maps_bp)

# Inicializar serviços
from gestao_visitas.routes.auto_scheduler_api import init_auto_scheduler_service
from gestao_visitas.routes.strategy_assistant_api import init_strategy_assistant_service
from gestao_visitas.routes.critical_alerts_api import init_critical_alerts_service
from gestao_visitas.routes.timeline_api import init_timeline_service
from gestao_visitas.routes.google_maps_api import init_google_maps_service

init_auto_scheduler_service(app)
init_strategy_assistant_service(app)
init_critical_alerts_service(app)
init_timeline_service(app)
init_google_maps_service(app)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    # Configuração de rede compatível com Windows
    import os
    import socket
    
    # Tentar determinar o melhor host
    host = '0.0.0.0'  # Permitir conexões de qualquer interface
    port = 5000
    
    # Verificar se a porta está disponível
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"⚠️ Porta {port} já está em uso. Tentando porta alternativa...")
            port = 5001
    except:
        pass
    
    print(f"🚀 Iniciando servidor Flask em http://{host}:{port}")
    print(f"📱 Acesse o sistema no seu navegador: http://{host}:{port}")
    print(f"🛑 Para parar o servidor: Pressione CTRL+C")
    print("=" * 60)
    
    try:
        # Configurações específicas para Windows
        app.run(
            host=host, 
            port=port, 
            debug=True,
            threaded=True,
            use_reloader=False  # Evita problemas de permissão no Windows
        )
    except OSError as e:
        if "WinError 10013" in str(e) or "Access is denied" in str(e):
            print("\n❌ ERRO DE PERMISSÃO DE REDE")
            print("=" * 50)
            print("💡 SOLUÇÕES:")
            print("   1. Execute como Administrador")
            print("   2. Verifique o Windows Firewall") 
            print("   3. Use executar_projeto_corrigido.bat")
            print("   4. Consulte SOLUCAO_PROBLEMAS.md")
            print("=" * 50)
        else:
            print(f"\n❌ Erro de rede: {e}")
        raise
    except KeyboardInterrupt:
        print("\n✅ Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro inesperado: {e}")
        raise 