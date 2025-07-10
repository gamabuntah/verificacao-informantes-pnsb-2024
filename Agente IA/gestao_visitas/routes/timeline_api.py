"""
APIs para Sistema de Timeline de Progresso PNSB 2024
Endpoints específicos para métricas temporais e milestones
"""

from flask import Blueprint, request, jsonify
from gestao_visitas.services.timeline_service import TimelineService
from gestao_visitas.db import db
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

timeline_bp = Blueprint('timeline', __name__)

# Instância global do serviço
timeline_service = None

def init_timeline_service(app):
    """Inicializa o serviço de timeline"""
    global timeline_service
    
    with app.app_context():
        timeline_service = TimelineService(db)
        logger.info("TimelineService inicializado")

@timeline_bp.route('/api/timeline/metrics', methods=['GET'])
def get_timeline_metrics():
    """Retorna métricas completas do timeline PNSB"""
    try:
        if not timeline_service:
            return jsonify({
                'error': 'Serviço de timeline não inicializado',
                'success': False
            }), 503
        
        # Obter métricas do timeline
        metrics = timeline_service.get_timeline_metrics()
        
        # Converter para formato JSON serializável
        metrics_dict = {
            'progresso_atual': round(metrics.progresso_atual, 1),
            'progresso_esperado': round(metrics.progresso_esperado, 1),
            'dias_decorridos': metrics.dias_decorridos,
            'dias_restantes_visitas': metrics.dias_restantes_visitas,
            'dias_restantes_questionarios': metrics.dias_restantes_questionarios,
            'velocidade_diaria': round(metrics.velocidade_diaria, 2),
            'velocidade_semanal': round(metrics.velocidade_semanal, 1),
            'previsao_conclusao': metrics.previsao_conclusao.isoformat(),
            'status_geral': metrics.status_geral,
            'fase_atual': {
                'nome': metrics.fase_atual.value,
                'descricao': timeline_service.get_phase_description(metrics.fase_atual)
            },
            'atraso_dias': metrics.atraso_dias,
            'risco_nivel': metrics.risco_nivel
        }
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': metrics_dict,
                'timestamp': datetime.now().isoformat()
            },
            'message': 'Métricas do timeline calculadas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter métricas do timeline: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@timeline_bp.route('/api/timeline/milestones', methods=['GET'])
def get_timeline_milestones():
    """Retorna milestones atualizados do projeto"""
    try:
        if not timeline_service:
            return jsonify({
                'error': 'Serviço de timeline não inicializado',
                'success': False
            }), 503
        
        # Obter milestones atualizados
        milestones = timeline_service.get_updated_milestones()
        
        # Calcular estatísticas dos milestones
        total_milestones = len(milestones)
        concluidos = len([m for m in milestones if m['status'] == 'concluido'])
        em_andamento = len([m for m in milestones if m['status'] == 'em_andamento'])
        atrasados = len([m for m in milestones if m['status'] == 'atrasado'])
        
        return jsonify({
            'success': True,
            'data': {
                'milestones': milestones,
                'estatisticas': {
                    'total': total_milestones,
                    'concluidos': concluidos,
                    'em_andamento': em_andamento,
                    'atrasados': atrasados,
                    'percentual_conclusao': (concluidos / total_milestones * 100) if total_milestones > 0 else 0
                },
                'timestamp': datetime.now().isoformat()
            },
            'message': f'{total_milestones} milestones processados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter milestones: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@timeline_bp.route('/api/timeline/weekly-breakdown', methods=['GET'])
def get_weekly_breakdown():
    """Retorna breakdown semanal do progresso"""
    try:
        if not timeline_service:
            return jsonify({
                'error': 'Serviço de timeline não inicializado',
                'success': False
            }), 503
        
        # Obter breakdown semanal
        breakdown = timeline_service.get_weekly_breakdown()
        
        return jsonify({
            'success': True,
            'data': {
                'breakdown_semanal': breakdown,
                'timestamp': datetime.now().isoformat()
            },
            'message': 'Breakdown semanal calculado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter breakdown semanal: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@timeline_bp.route('/api/timeline/dashboard', methods=['GET'])
def get_timeline_dashboard():
    """Retorna dados completos para o dashboard do timeline"""
    try:
        if not timeline_service:
            return jsonify({
                'error': 'Serviço de timeline não inicializado',
                'success': False
            }), 503
        
        # Obter todas as métricas necessárias
        metrics = timeline_service.get_timeline_metrics()
        milestones = timeline_service.get_updated_milestones()
        breakdown_semanal = timeline_service.get_weekly_breakdown()
        
        # Calcular alertas do timeline
        alertas_timeline = []
        
        # Alerta de atraso crítico
        if metrics.atraso_dias > 14:
            alertas_timeline.append({
                'tipo': 'atraso_critico',
                'nivel': 'critico',
                'titulo': f'Projeto atrasado em {metrics.atraso_dias} dias',
                'descricao': 'Ações urgentes necessárias para recuperar cronograma'
            })
        
        # Alerta de velocidade baixa
        if metrics.velocidade_semanal < 5 and metrics.progresso_atual < 50:
            alertas_timeline.append({
                'tipo': 'velocidade_baixa',
                'nivel': 'urgente',
                'titulo': f'Velocidade baixa: {metrics.velocidade_semanal:.1f}%/semana',
                'descricao': 'Necessário acelerar ritmo de trabalho'
            })
        
        # Alerta de deadline próximo
        if metrics.dias_restantes_visitas <= 30:
            alertas_timeline.append({
                'tipo': 'deadline_proximo',
                'nivel': 'urgente',
                'titulo': f'Deadline visitas em {metrics.dias_restantes_visitas} dias',
                'descricao': 'Foco total nas visitas prioritárias P1+P2'
            })
        
        # Status do projeto
        if metrics.progresso_atual >= 100:
            status_projeto = "🏆 Projeto Concluído"
            cor_status = "#28a745"
        elif metrics.risco_nivel == "critico":
            status_projeto = "🚨 Situação Crítica"
            cor_status = "#dc3545"
        elif metrics.risco_nivel == "alto":
            status_projeto = "⚠️ Atenção Necessária"
            cor_status = "#ffc107"
        elif metrics.progresso_atual > metrics.progresso_esperado:
            status_projeto = "🚀 Adiantado"
            cor_status = "#17a2b8"
        else:
            status_projeto = "📊 No Cronograma"
            cor_status = "#6f42c1"
        
        dashboard_data = {
            'visao_geral': {
                'progresso_atual': round(metrics.progresso_atual, 1),
                'progresso_esperado': round(metrics.progresso_esperado, 1),
                'status_projeto': status_projeto,
                'cor_status': cor_status,
                'fase_atual': {
                    'nome': metrics.fase_atual.value,
                    'descricao': timeline_service.get_phase_description(metrics.fase_atual)
                },
                'risco_nivel': metrics.risco_nivel
            },
            'tempo': {
                'dias_decorridos': metrics.dias_decorridos,
                'dias_restantes_visitas': metrics.dias_restantes_visitas,
                'dias_restantes_questionarios': metrics.dias_restantes_questionarios,
                'previsao_conclusao': metrics.previsao_conclusao.strftime('%d/%m/%Y'),
                'atraso_dias': metrics.atraso_dias
            },
            'velocidade': {
                'diaria': round(metrics.velocidade_diaria, 2),
                'semanal': round(metrics.velocidade_semanal, 1),
                'necessaria_semanal': round(breakdown_semanal.get('progresso_semanal_necessario', 0), 1),
                'eficiencia': round(breakdown_semanal.get('eficiencia_semanal', 0), 1)
            },
            'milestones': {
                'proximos': [m for m in milestones if m['status'] in ['pendente', 'em_andamento']][:3],
                'atrasados': [m for m in milestones if m['status'] == 'atrasado'],
                'percentual_conclusao': (len([m for m in milestones if m['status'] == 'concluido']) / len(milestones) * 100) if milestones else 0
            },
            'alertas': alertas_timeline,
            'breakdown_semanal': breakdown_semanal
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data,
            'timestamp': datetime.now().isoformat(),
            'message': 'Dashboard do timeline gerado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard do timeline: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@timeline_bp.route('/api/timeline/forecast', methods=['GET'])
def get_timeline_forecast():
    """Retorna previsões e cenários do timeline"""
    try:
        if not timeline_service:
            return jsonify({
                'error': 'Serviço de timeline não inicializado',
                'success': False
            }), 503
        
        metrics = timeline_service.get_timeline_metrics()
        
        # Calcular cenários
        cenarios = []
        
        # Cenário atual
        cenarios.append({
            'nome': 'Ritmo Atual',
            'tipo': 'atual',
            'velocidade_semanal': metrics.velocidade_semanal,
            'previsao_conclusao': metrics.previsao_conclusao.strftime('%d/%m/%Y'),
            'probabilidade_sucesso': 70 if metrics.velocidade_semanal > 3 else 40,
            'descricao': 'Mantendo velocidade atual'
        })
        
        # Cenário otimista
        velocidade_otimista = metrics.velocidade_semanal * 1.5
        dias_otimista = int((100 - metrics.progresso_atual) / (velocidade_otimista / 7)) if velocidade_otimista > 0 else 90
        previsao_otimista = datetime.now() + timedelta(days=dias_otimista)
        
        cenarios.append({
            'nome': 'Cenário Otimista',
            'tipo': 'otimista',
            'velocidade_semanal': round(velocidade_otimista, 1),
            'previsao_conclusao': previsao_otimista.strftime('%d/%m/%Y'),
            'probabilidade_sucesso': 85,
            'descricao': 'Com aceleração de 50% no ritmo'
        })
        
        # Cenário pessimista
        velocidade_pessimista = metrics.velocidade_semanal * 0.7
        dias_pessimista = int((100 - metrics.progresso_atual) / (velocidade_pessimista / 7)) if velocidade_pessimista > 0 else 120
        previsao_pessimista = datetime.now() + timedelta(days=dias_pessimista)
        
        cenarios.append({
            'nome': 'Cenário Pessimista',
            'tipo': 'pessimista',
            'velocidade_semanal': round(velocidade_pessimista, 1),
            'previsao_conclusao': previsao_pessimista.strftime('%d/%m/%Y'),
            'probabilidade_sucesso': 30,
            'descricao': 'Com redução de 30% no ritmo'
        })
        
        return jsonify({
            'success': True,
            'data': {
                'cenarios': cenarios,
                'recomendacoes': [
                    'Monitorar velocidade semanal constantemente',
                    'Focar em questionários com maior impacto',
                    'Redistribuir recursos se necessário',
                    'Manter comunicação constante com equipe'
                ],
                'timestamp': datetime.now().isoformat()
            },
            'message': 'Previsões calculadas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular previsões: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500