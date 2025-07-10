"""
APIs para Sistema de Alertas Críticos PNSB 2024
Endpoints específicos para gestão avançada de alertas
"""

from flask import Blueprint, request, jsonify
from gestao_visitas.services.critical_alerts_service import CriticalAlertsService, AlertLevel, AlertType
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

critical_alerts_bp = Blueprint('critical_alerts', __name__)

# Instância global do serviço
alerts_service = None

def init_critical_alerts_service(app):
    """Inicializa o serviço de alertas críticos"""
    global alerts_service
    
    with app.app_context():
        alerts_service = CriticalAlertsService(db)
        logger.info("CriticalAlertsService inicializado")

@critical_alerts_bp.route('/api/alertas/por-municipio/<municipio>', methods=['GET'])
def get_alertas_por_municipio(municipio):
    """Retorna alertas específicos de um município"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Validar município
        if municipio not in MUNICIPIOS and municipio not in ['TODOS', 'GERAL', 'MULTIPLOS']:
            return jsonify({
                'error': f'Município {municipio} não é válido',
                'success': False,
                'valid_municipalities': MUNICIPIOS
            }), 400
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        
        # Filtrar alertas do município
        alertas_municipio = [
            alert for alert in all_alerts['alertas'] 
            if alert['municipio'] == municipio or alert['municipio'] in ['TODOS', 'GERAL', 'MULTIPLOS']
        ]
        
        # Gerar resumo específico
        resumo_municipio = {
            'municipio': municipio,
            'total_alertas': len(alertas_municipio),
            'criticos': len([a for a in alertas_municipio if a['nivel'] == 'critico']),
            'urgentes': len([a for a in alertas_municipio if a['nivel'] == 'urgente']),
            'atencao': len([a for a in alertas_municipio if a['nivel'] == 'atencao']),
            'status': 'critico' if any(a['nivel'] == 'critico' for a in alertas_municipio) else 'normal'
        }
        
        return jsonify({
            'success': True,
            'data': {
                'alertas': alertas_municipio,
                'resumo': resumo_municipio,
                'timestamp': datetime.now().isoformat()
            },
            'message': f'Alertas para {municipio}: {len(alertas_municipio)} encontrados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas do município {municipio}: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/por-nivel/<nivel>', methods=['GET'])
def get_alertas_por_nivel(nivel):
    """Retorna alertas de um nível específico"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Validar nível
        niveis_validos = ['critico', 'urgente', 'atencao', 'info']
        if nivel not in niveis_validos:
            return jsonify({
                'error': f'Nível {nivel} não é válido',
                'success': False,
                'valid_levels': niveis_validos
            }), 400
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        
        # Filtrar alertas por nível
        alertas_nivel = [
            alert for alert in all_alerts['alertas'] 
            if alert['nivel'] == nivel
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'alertas': alertas_nivel,
                'nivel_filtrado': nivel,
                'total_encontrados': len(alertas_nivel),
                'timestamp': datetime.now().isoformat()
            },
            'message': f'Alertas nível {nivel}: {len(alertas_nivel)} encontrados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas do nível {nivel}: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/por-tipo/<tipo>', methods=['GET'])
def get_alertas_por_tipo(tipo):
    """Retorna alertas de um tipo específico"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Validar tipo
        tipos_validos = [t.value for t in AlertType]
        if tipo not in tipos_validos:
            return jsonify({
                'error': f'Tipo {tipo} não é válido',
                'success': False,
                'valid_types': tipos_validos
            }), 400
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        
        # Filtrar alertas por tipo
        alertas_tipo = [
            alert for alert in all_alerts['alertas'] 
            if alert['tipo'] == tipo
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'alertas': alertas_tipo,
                'tipo_filtrado': tipo,
                'total_encontrados': len(alertas_tipo),
                'timestamp': datetime.now().isoformat()
            },
            'message': f'Alertas tipo {tipo}: {len(alertas_tipo)} encontrados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter alertas do tipo {tipo}: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/dashboard-summary', methods=['GET'])
def get_dashboard_summary():
    """Retorna resumo consolidado para dashboard"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        resumo = all_alerts['resumo']
        
        # Calcular métricas específicas para dashboard
        alertas = all_alerts['alertas']
        
        # Top 5 municípios com mais alertas
        municipios_count = {}
        for alert in alertas:
            municipio = alert['municipio']
            if municipio not in ['TODOS', 'GERAL', 'MULTIPLOS', 'PROJETO', 'EQUIPE', 'SISTEMA']:
                municipios_count[municipio] = municipios_count.get(municipio, 0) + 1
        
        top_municipios = sorted(municipios_count.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Alertas por tipo
        tipos_count = {}
        for alert in alertas:
            tipo = alert['tipo']
            tipos_count[tipo] = tipos_count.get(tipo, 0) + 1
        
        # Alertas críticos recentes (últimas 24h)
        alertas_recentes = [
            alert for alert in alertas 
            if alert['nivel'] == 'critico'
        ][:5]  # Top 5 mais críticos
        
        dashboard_data = {
            'overview': {
                'total_alertas': resumo['total_alertas'],
                'criticos': resumo['criticos'],
                'urgentes': resumo['urgentes'],
                'atencao': resumo['atencao'],
                'status_sistema': resumo['status_sistema'],
                'dias_deadline_visitas': resumo['dias_ate_deadline_visitas'],
                'dias_deadline_questionarios': resumo['dias_ate_deadline_questionarios']
            },
            'distribuicao': {
                'por_tipo': tipos_count,
                'por_municipio': dict(top_municipios),
                'total_municipios_afetados': resumo.get('municipios_com_alertas', 0)
            },
            'alertas_criticos_recentes': alertas_recentes,
            'tendencias': {
                'risco_geral': 'alto' if resumo['criticos'] > 5 else 'medio' if resumo['criticos'] > 0 else 'baixo',
                'necessita_acao_imediata': resumo['criticos'] > 0,
                'total_tipos_ativos': len(tipos_count)
            }
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat(),
            'message': 'Dashboard summary gerado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard summary: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/municipios-criticos', methods=['GET'])
def get_municipios_criticos():
    """Retorna municípios com alertas críticos"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        alertas = all_alerts['alertas']
        
        # Analisar municípios com alertas críticos
        municipios_criticos = {}
        
        for alert in alertas:
            municipio = alert['municipio']
            if municipio not in ['TODOS', 'GERAL', 'MULTIPLOS', 'PROJETO', 'EQUIPE', 'SISTEMA']:
                if municipio not in municipios_criticos:
                    municipios_criticos[municipio] = {
                        'municipio': municipio,
                        'total_alertas': 0,
                        'criticos': 0,
                        'urgentes': 0,
                        'atencao': 0,
                        'alertas_detalhes': []
                    }
                
                municipios_criticos[municipio]['total_alertas'] += 1
                municipios_criticos[municipio]['alertas_detalhes'].append({
                    'id': alert['id'],
                    'nivel': alert['nivel'],
                    'titulo': alert['titulo'],
                    'tipo': alert['tipo']
                })
                
                if alert['nivel'] == 'critico':
                    municipios_criticos[municipio]['criticos'] += 1
                elif alert['nivel'] == 'urgente':
                    municipios_criticos[municipio]['urgentes'] += 1
                elif alert['nivel'] == 'atencao':
                    municipios_criticos[municipio]['atencao'] += 1
        
        # Calcular prioridade (municípios com mais alertas críticos primeiro)
        municipios_ordenados = sorted(
            municipios_criticos.values(), 
            key=lambda x: (x['criticos'], x['urgentes'], x['total_alertas']), 
            reverse=True
        )
        
        # Filtrar apenas municípios que realmente têm problemas
        municipios_com_problemas = [
            m for m in municipios_ordenados 
            if m['criticos'] > 0 or m['urgentes'] > 1
        ]
        
        return jsonify({
            'success': True,
            'data': {
                'municipios_criticos': municipios_com_problemas,
                'total_municipios_afetados': len(municipios_com_problemas),
                'total_municipios_projeto': len(MUNICIPIOS),
                'percentual_afetado': (len(municipios_com_problemas) / len(MUNICIPIOS)) * 100
            },
            'message': f'{len(municipios_com_problemas)} municípios com problemas críticos identificados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter municípios críticos: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/marcar-visto', methods=['POST'])
def marcar_alerta_visto():
    """Marca um alerta como visto (funcionalidade futura)"""
    try:
        data = request.get_json()
        if not data or 'alert_id' not in data:
            return jsonify({
                'error': 'ID do alerta é obrigatório',
                'success': False
            }), 400
        
        alert_id = data['alert_id']
        usuario = data.get('usuario', 'anonimo')
        
        # Por enquanto, apenas simular a marcação
        # Em uma implementação completa, salvaria no banco de dados
        
        return jsonify({
            'success': True,
            'message': f'Alerta {alert_id} marcado como visto por {usuario}',
            'data': {
                'alert_id': alert_id,
                'visto_por': usuario,
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao marcar alerta como visto: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/configuracao', methods=['GET', 'POST'])
def gerenciar_configuracao_alertas():
    """Gerencia configurações do sistema de alertas"""
    try:
        if request.method == 'GET':
            # Retornar configurações atuais
            config = {
                'deadlines': {
                    'visitas_p1_p2': '2025-09-19',
                    'questionarios': '2025-10-17',
                    'finalizacao': '2025-12-15'
                },
                'thresholds': {
                    'dias_critico_visitas': 30,
                    'dias_urgente_visitas': 60,
                    'progresso_baixo_pct': 50,
                    'dias_sem_atualizacao_followup': 7
                },
                'tipos_alertas_ativos': [t.value for t in AlertType],
                'municipios_monitorados': MUNICIPIOS
            }
            
            return jsonify({
                'success': True,
                'data': config,
                'message': 'Configurações atuais do sistema de alertas'
            })
        
        elif request.method == 'POST':
            # Atualizar configurações (funcionalidade futura)
            data = request.get_json()
            
            return jsonify({
                'success': True,
                'message': 'Configurações atualizadas (funcionalidade em desenvolvimento)',
                'data': data
            })
            
    except Exception as e:
        logger.error(f"Erro ao gerenciar configurações: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@critical_alerts_bp.route('/api/alertas/estatisticas', methods=['GET'])
def get_estatisticas_alertas():
    """Retorna estatísticas detalhadas dos alertas"""
    try:
        if not alerts_service:
            return jsonify({
                'error': 'Serviço de alertas não inicializado',
                'success': False
            }), 503
        
        # Obter todos os alertas
        all_alerts = alerts_service.get_all_critical_alerts()
        alertas = all_alerts['alertas']
        resumo = all_alerts['resumo']
        
        # Calcular estatísticas detalhadas
        stats = {
            'totais': {
                'alertas_ativos': len(alertas),
                'tipos_diferentes': len(set([a['tipo'] for a in alertas])),
                'municipios_afetados': len(set([a['municipio'] for a in alertas if a['municipio'] not in ['TODOS', 'GERAL', 'MULTIPLOS', 'PROJETO', 'EQUIPE', 'SISTEMA']])),
                'alertas_com_deadline': len([a for a in alertas if a['dias_restantes'] is not None])
            },
            'distribuicao_nivel': {
                'criticos': resumo['criticos'],
                'urgentes': resumo['urgentes'],
                'atencao': resumo['atencao'],
                'info': resumo.get('info', 0)
            },
            'distribuicao_tipo': resumo.get('alertas_por_tipo', {}),
            'deadlines': {
                'dias_visitas': resumo['dias_ate_deadline_visitas'],
                'dias_questionarios': resumo['dias_ate_deadline_questionarios'],
                'status_visitas': 'critico' if resumo['dias_ate_deadline_visitas'] <= 30 else 'urgente' if resumo['dias_ate_deadline_visitas'] <= 60 else 'normal',
                'status_questionarios': 'critico' if resumo['dias_ate_deadline_questionarios'] <= 45 else 'urgente' if resumo['dias_ate_deadline_questionarios'] <= 90 else 'normal'
            },
            'tendencias': {
                'risco_geral': resumo['status_sistema'],
                'necessita_acao_imediata': resumo['criticos'] > 0,
                'municipios_problema_pct': (resumo.get('municipios_com_alertas', 0) / len(MUNICIPIOS)) * 100 if len(MUNICIPIOS) > 0 else 0
            }
        }
        
        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat(),
            'message': 'Estatísticas detalhadas geradas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500