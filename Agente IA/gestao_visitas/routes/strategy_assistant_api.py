"""
APIs para o Assistente de Estratégia Local
Endpoints para análise de municípios e geração de estratégias
"""

from flask import Blueprint, request, jsonify
from gestao_visitas.services.strategy_assistant import StrategyAssistantService
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS
import logging

logger = logging.getLogger(__name__)

strategy_assistant_bp = Blueprint('strategy_assistant', __name__)

# Instância global do serviço
strategy_service = None

def init_strategy_assistant_service(app):
    """Inicializa o serviço de assistente de estratégia"""
    global strategy_service
    
    with app.app_context():
        strategy_service = StrategyAssistantService(db)
        logger.info("StrategyAssistantService inicializado")

@strategy_assistant_bp.route('/api/strategy-assistant/municipality/<municipio>', methods=['GET'])
def analyze_municipality(municipio):
    """Analisa um município específico e retorna estratégias personalizadas"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        # Validar município
        if municipio not in MUNICIPIOS:
            return jsonify({
                'error': f'Município {municipio} não está na lista do PNSB',
                'success': False,
                'valid_municipalities': MUNICIPIOS
            }), 400
        
        # Executar análise
        analysis = strategy_service.analyze_municipality(municipio)
        
        return jsonify({
            'success': True,
            'data': analysis,
            'message': f'Análise concluída para {municipio}'
        })
        
    except Exception as e:
        logger.error(f"Erro na análise do município {municipio}: {e}")
        return jsonify({
            'error': f'Erro interno na análise: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/all-municipalities', methods=['GET'])
def analyze_all_municipalities():
    """Analisa todos os municípios e retorna relatório consolidado"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        # Executar análise de todos os municípios
        analysis = strategy_service.analyze_all_municipalities()
        
        return jsonify({
            'success': True,
            'data': analysis,
            'message': f'Análise concluída para {len(MUNICIPIOS)} municípios'
        })
        
    except Exception as e:
        logger.error(f"Erro na análise de todos os municípios: {e}")
        return jsonify({
            'error': f'Erro interno na análise: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/quick-analysis/<municipio>', methods=['GET'])
def quick_municipality_analysis(municipio):
    """Análise rápida de um município (apenas métricas básicas)"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        # Validar município
        if municipio not in MUNICIPIOS:
            return jsonify({
                'error': f'Município {municipio} não está na lista do PNSB',
                'success': False
            }), 400
        
        # Executar análise rápida (apenas perfil e métricas)
        profile = strategy_service._get_municipality_profile(municipio)
        progress_metrics = strategy_service._calculate_progress_metrics(municipio)
        
        result = {
            'municipio': municipio,
            'profile_summary': {
                'taxa_sucesso': profile.taxa_sucesso,
                'total_visitas': profile.total_visitas,
                'contatos_disponiveis': profile.contatos_disponiveis,
                'risco_atual': profile.risco_atual,
                'nivel_cooperacao': profile.nivel_cooperacao
            },
            'progress_metrics': progress_metrics,
            'generated_at': profile.__dict__.get('generated_at', 'now')
        }
        
        return jsonify({
            'success': True,
            'data': result,
            'message': f'Análise rápida concluída para {municipio}'
        })
        
    except Exception as e:
        logger.error(f"Erro na análise rápida do município {municipio}: {e}")
        return jsonify({
            'error': f'Erro interno na análise: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/strategy-report', methods=['POST'])
def generate_strategy_report():
    """Gera relatório de estratégias personalizado"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        data = request.get_json() or {}
        
        # Parâmetros opcionais
        municipalities = data.get('municipalities', MUNICIPIOS)
        include_details = data.get('include_details', True)
        focus_area = data.get('focus_area', 'all')  # 'contact', 'timing', 'approach', 'all'
        
        # Validar municípios
        invalid_municipalities = [m for m in municipalities if m not in MUNICIPIOS]
        if invalid_municipalities:
            return jsonify({
                'error': f'Municípios inválidos: {invalid_municipalities}',
                'success': False
            }), 400
        
        # Gerar relatório customizado
        report_data = {
            'municipalities_analyzed': [],
            'summary_metrics': {
                'total_municipalities': len(municipalities),
                'high_risk': 0,
                'medium_risk': 0,
                'low_risk': 0,
                'total_strategies': 0
            },
            'recommendations': [],
            'generated_at': None
        }
        
        for municipio in municipalities:
            try:
                if include_details:
                    analysis = strategy_service.analyze_municipality(municipio)
                    report_data['municipalities_analyzed'].append(analysis)
                else:
                    # Análise simplificada
                    profile = strategy_service._get_municipality_profile(municipio)
                    simple_analysis = {
                        'municipio': municipio,
                        'risco': profile.risco_atual,
                        'taxa_sucesso': profile.taxa_sucesso,
                        'cooperacao': profile.nivel_cooperacao
                    }
                    report_data['municipalities_analyzed'].append(simple_analysis)
                
                # Atualizar métricas resumo
                if include_details:
                    risk_level = analysis['profile']['risco_atual']
                else:
                    risk_level = profile.risco_atual
                
                if 'Alto' in risk_level:
                    report_data['summary_metrics']['high_risk'] += 1
                elif 'Médio' in risk_level:
                    report_data['summary_metrics']['medium_risk'] += 1
                else:
                    report_data['summary_metrics']['low_risk'] += 1
                
                if include_details:
                    report_data['summary_metrics']['total_strategies'] += len(analysis['strategies'])
                    
            except Exception as e:
                logger.error(f"Erro ao analisar {municipio} no relatório: {e}")
                continue
        
        # Gerar recomendações gerais
        if len(report_data['municipalities_analyzed']) > 0:
            full_analysis = {m['municipio']: m for m in report_data['municipalities_analyzed'] if 'profile' in m}
            if full_analysis:
                report_data['recommendations'] = strategy_service._generate_general_recommendations(full_analysis)
        
        report_data['generated_at'] = strategy_service._get_current_timestamp()
        
        return jsonify({
            'success': True,
            'data': report_data,
            'message': f'Relatório gerado para {len(municipalities)} municípios'
        })
        
    except Exception as e:
        logger.error(f"Erro na geração do relatório de estratégias: {e}")
        return jsonify({
            'error': f'Erro interno na geração do relatório: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/municipalities', methods=['GET'])
def get_municipalities_list():
    """Retorna lista de municípios disponíveis para análise"""
    try:
        # Obter informações básicas de cada município
        municipalities_info = []
        
        for municipio in MUNICIPIOS:
            try:
                if strategy_service:
                    profile = strategy_service._get_municipality_profile(municipio)
                    info = {
                        'nome': municipio,
                        'codigo': municipio.lower().replace(' ', '-'),
                        'taxa_sucesso': profile.taxa_sucesso,
                        'total_visitas': profile.total_visitas,
                        'risco': profile.risco_atual,
                        'cooperacao': profile.nivel_cooperacao
                    }
                else:
                    info = {
                        'nome': municipio,
                        'codigo': municipio.lower().replace(' ', '-'),
                        'taxa_sucesso': 0,
                        'total_visitas': 0,
                        'risco': 'Desconhecido',
                        'cooperacao': 'Desconhecido'
                    }
                
                municipalities_info.append(info)
                
            except Exception as e:
                logger.error(f"Erro ao obter info do município {municipio}: {e}")
                # Adicionar info básica mesmo com erro
                municipalities_info.append({
                    'nome': municipio,
                    'codigo': municipio.lower().replace(' ', '-'),
                    'taxa_sucesso': 0,
                    'total_visitas': 0,
                    'risco': 'Erro',
                    'cooperacao': 'Erro'
                })
        
        return jsonify({
            'success': True,
            'data': {
                'municipalities': municipalities_info,
                'total_count': len(municipalities_info)
            },
            'message': f'{len(municipalities_info)} municípios disponíveis'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter lista de municípios: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/high-priority', methods=['GET'])
def get_high_priority_municipalities():
    """Retorna municípios que requerem atenção prioritária"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        high_priority = []
        
        for municipio in MUNICIPIOS:
            try:
                profile = strategy_service._get_municipality_profile(municipio)
                
                # Critérios de alta prioridade
                is_high_priority = (
                    profile.risco_atual == 'Alto' or
                    profile.taxa_sucesso < 50 or
                    profile.contatos_disponiveis < 2 or
                    'resistencia_inicial' in profile.desafios_identificados
                )
                
                if is_high_priority:
                    priority_info = {
                        'municipio': municipio,
                        'motivos': [],
                        'taxa_sucesso': profile.taxa_sucesso,
                        'risco': profile.risco_atual,
                        'contatos': profile.contatos_disponiveis,
                        'desafios': profile.desafios_identificados
                    }
                    
                    # Identificar motivos específicos
                    if profile.risco_atual == 'Alto':
                        priority_info['motivos'].append('Alto risco identificado')
                    if profile.taxa_sucesso < 50:
                        priority_info['motivos'].append(f'Taxa de sucesso baixa ({profile.taxa_sucesso:.1f}%)')
                    if profile.contatos_disponiveis < 2:
                        priority_info['motivos'].append('Poucos contatos disponíveis')
                    if 'resistencia_inicial' in profile.desafios_identificados:
                        priority_info['motivos'].append('Resistência inicial identificada')
                    
                    high_priority.append(priority_info)
                    
            except Exception as e:
                logger.error(f"Erro ao avaliar prioridade do município {municipio}: {e}")
                continue
        
        # Ordenar por número de motivos (mais críticos primeiro)
        high_priority.sort(key=lambda x: len(x['motivos']), reverse=True)
        
        return jsonify({
            'success': True,
            'data': {
                'high_priority_municipalities': high_priority,
                'total_count': len(high_priority),
                'criteria': [
                    'Risco alto',
                    'Taxa de sucesso < 50%',
                    'Menos de 2 contatos disponíveis',
                    'Resistência inicial identificada'
                ]
            },
            'message': f'{len(high_priority)} municípios de alta prioridade identificados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter municípios de alta prioridade: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@strategy_assistant_bp.route('/api/strategy-assistant/dashboard-data', methods=['GET'])
def get_dashboard_data():
    """Retorna dados resumidos para dashboard do assistente"""
    try:
        if not strategy_service:
            return jsonify({
                'error': 'Serviço de estratégia não inicializado',
                'success': False
            }), 503
        
        dashboard_data = {
            'overview': {
                'total_municipalities': len(MUNICIPIOS),
                'analyzed_municipalities': 0,
                'high_risk_count': 0,
                'medium_risk_count': 0,
                'low_risk_count': 0,
                'avg_success_rate': 0
            },
            'top_challenges': {},
            'recent_analysis': [],
            'recommendations_summary': []
        }
        
        success_rates = []
        challenge_counts = {}
        
        for municipio in MUNICIPIOS:
            try:
                profile = strategy_service._get_municipality_profile(municipio)
                dashboard_data['overview']['analyzed_municipalities'] += 1
                
                # Contabilizar riscos
                if profile.risco_atual == 'Alto':
                    dashboard_data['overview']['high_risk_count'] += 1
                elif profile.risco_atual == 'Médio':
                    dashboard_data['overview']['medium_risk_count'] += 1
                else:
                    dashboard_data['overview']['low_risk_count'] += 1
                
                # Coletar taxas de sucesso
                success_rates.append(profile.taxa_sucesso)
                
                # Contabilizar desafios
                for challenge in profile.desafios_identificados:
                    challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1
                
                # Adicionar à análise recente (limitado aos primeiros 5)
                if len(dashboard_data['recent_analysis']) < 5:
                    dashboard_data['recent_analysis'].append({
                        'municipio': municipio,
                        'taxa_sucesso': profile.taxa_sucesso,
                        'risco': profile.risco_atual,
                        'timestamp': 'Agora'  # Poderia ser mais preciso
                    })
                    
            except Exception as e:
                logger.error(f"Erro ao processar {municipio} para dashboard: {e}")
                continue
        
        # Calcular taxa média de sucesso
        if success_rates:
            dashboard_data['overview']['avg_success_rate'] = round(sum(success_rates) / len(success_rates), 1)
        
        # Top 3 desafios mais comuns
        sorted_challenges = sorted(challenge_counts.items(), key=lambda x: x[1], reverse=True)
        dashboard_data['top_challenges'] = dict(sorted_challenges[:3])
        
        # Recomendações resumidas
        dashboard_data['recommendations_summary'] = [
            f"Focar nos {dashboard_data['overview']['high_risk_count']} municípios de alto risco",
            f"Taxa média de sucesso atual: {dashboard_data['overview']['avg_success_rate']}%",
            "Implementar estratégias de contato otimizadas"
        ]
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'message': 'Dados do dashboard carregados com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao carregar dados do dashboard: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

# Método auxiliar para adicionar ao serviço
def _add_timestamp_method():
    """Adiciona método de timestamp ao serviço"""
    def get_current_timestamp(self):
        from datetime import datetime
        return datetime.now().isoformat()
    
    StrategyAssistantService._get_current_timestamp = get_current_timestamp

# Executar ao importar
_add_timestamp_method()