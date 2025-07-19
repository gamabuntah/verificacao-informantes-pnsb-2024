"""
API para Dashboard Preditivo PNSB 2024
Endpoints para análise preditiva, projeções e alertas inteligentes
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
from ..services.dashboard_preditivo import DashboardPreditivo
from .. import db
import logging

logger = logging.getLogger(__name__)

# Criar blueprint
dashboard_preditivo_bp = Blueprint('dashboard_preditivo', __name__, url_prefix='/api/dashboard-preditivo')

# Inicializar serviço
dashboard_preditivo_service = DashboardPreditivo()

@dashboard_preditivo_bp.route('/completo', methods=['GET'])
def obter_dashboard_completo():
    """Retorna dashboard preditivo completo com todas as análises"""
    try:
        dashboard = dashboard_preditivo_service.gerar_dashboard_completo()
        
        return jsonify({
            'success': True,
            'data': dashboard,
            'message': 'Dashboard preditivo gerado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar dashboard preditivo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/analise-prazos', methods=['GET'])
def obter_analise_prazos():
    """Retorna análise detalhada de prazos e projeções"""
    try:
        analise = dashboard_preditivo_service._analisar_prazos()
        
        return jsonify({
            'success': True,
            'data': analise,
            'message': 'Análise de prazos gerada com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao analisar prazos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/riscos', methods=['GET'])
def obter_riscos():
    """Retorna riscos identificados no projeto"""
    try:
        riscos = dashboard_preditivo_service._identificar_riscos()
        
        # Filtrar por nível se especificado
        nivel = request.args.get('nivel')
        if nivel:
            riscos = [r for r in riscos if r['nivel'] == nivel]
        
        return jsonify({
            'success': True,
            'data': riscos,
            'total': len(riscos),
            'message': f'{len(riscos)} riscos identificados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao identificar riscos: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/projecoes', methods=['GET'])
def obter_projecoes():
    """Retorna projeções de progresso futuro"""
    try:
        projecoes = dashboard_preditivo_service._projetar_progresso()
        
        return jsonify({
            'success': True,
            'data': projecoes,
            'message': 'Projeções geradas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar projeções: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/alertas-criticos', methods=['GET'])
def obter_alertas_criticos():
    """Retorna alertas críticos que requerem ação imediata"""
    try:
        alertas = dashboard_preditivo_service._gerar_alertas_criticos()
        
        # Filtrar por tipo se especificado
        tipo = request.args.get('tipo')
        if tipo:
            alertas = [a for a in alertas if a['tipo'] == tipo]
        
        return jsonify({
            'success': True,
            'data': alertas,
            'total': len(alertas),
            'criticos': len([a for a in alertas if a['nivel'] == 'critico']),
            'message': f'{len(alertas)} alertas ativos'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar alertas: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/velocidade', methods=['GET'])
def obter_velocidade_progresso():
    """Retorna métricas de velocidade de progresso"""
    try:
        velocidade = dashboard_preditivo_service._calcular_velocidade_progresso()
        
        return jsonify({
            'success': True,
            'data': velocidade,
            'message': 'Velocidade de progresso calculada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular velocidade: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/previsao-conclusao', methods=['GET'])
def obter_previsao_conclusao():
    """Retorna previsão de conclusão do projeto"""
    try:
        previsao = dashboard_preditivo_service._prever_conclusao()
        
        return jsonify({
            'success': True,
            'data': previsao,
            'message': 'Previsão de conclusão gerada'
        })
        
    except Exception as e:
        logger.error(f"Erro ao prever conclusão: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/analise-municipios', methods=['GET'])
def obter_analise_municipios():
    """Retorna análise detalhada por município"""
    try:
        analise = dashboard_preditivo_service._analisar_municipios()
        
        # Filtrar por município se especificado
        municipio = request.args.get('municipio')
        if municipio:
            analise = [a for a in analise if a['municipio'] == municipio]
        
        return jsonify({
            'success': True,
            'data': analise,
            'total': len(analise),
            'message': f'Análise de {len(analise)} municípios'
        })
        
    except Exception as e:
        logger.error(f"Erro ao analisar municípios: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/score-saude', methods=['GET'])
def obter_score_saude():
    """Retorna score de saúde geral do projeto"""
    try:
        score = dashboard_preditivo_service._calcular_score_saude()
        
        return jsonify({
            'success': True,
            'data': score,
            'message': f'Score de saúde: {score["score_final"]} - {score["classificacao"]}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular score: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/recomendacoes', methods=['GET'])
def obter_recomendacoes():
    """Retorna recomendações baseadas na análise preditiva"""
    try:
        # Gerar análise completa primeiro
        dashboard = dashboard_preditivo_service.gerar_dashboard_completo()
        
        recomendacoes = dashboard.get('recomendacoes', [])
        
        return jsonify({
            'success': True,
            'data': {
                'recomendacoes': recomendacoes,
                'score_saude': dashboard.get('score_saude', {}),
                'riscos_principais': dashboard.get('riscos_identificados', [])[:3]
            },
            'message': f'{len(recomendacoes)} recomendações geradas'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar recomendações: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/resumo-executivo', methods=['GET'])
def obter_resumo_executivo():
    """Retorna resumo executivo para tomada de decisão rápida"""
    try:
        dashboard = dashboard_preditivo_service.gerar_dashboard_completo()
        
        # Extrair informações principais
        resumo = {
            'status_geral': dashboard['score_saude']['classificacao'],
            'score_saude': dashboard['score_saude']['score_final'],
            'velocidade_atual': dashboard['velocidade_atual']['geral'],
            'riscos_criticos': len([r for r in dashboard['riscos_identificados'] if r['nivel'] == 'critico']),
            'alertas_criticos': len([a for a in dashboard['alertas_criticos'] if a['nivel'] == 'critico']),
            'previsao_conclusao': dashboard['previsao_conclusao']['previsao_atual'],
            'principais_problemas': [],
            'acoes_urgentes': []
        }
        
        # Identificar principais problemas
        if resumo['velocidade_atual'] < 0.5:
            resumo['principais_problemas'].append('Velocidade crítica de progresso')
        
        if resumo['riscos_criticos'] > 0:
            resumo['principais_problemas'].append(f'{resumo["riscos_criticos"]} riscos críticos identificados')
        
        if not dashboard['previsao_conclusao']['previsao_atual']['p1_p2']['dentro_prazo']:
            resumo['principais_problemas'].append('Prazo P1/P2 em risco')
        
        # Ações urgentes
        for alerta in dashboard['alertas_criticos'][:3]:
            if alerta['nivel'] == 'critico':
                resumo['acoes_urgentes'].append(alerta['acao_necessaria'])
        
        return jsonify({
            'success': True,
            'data': resumo,
            'timestamp': datetime.now().isoformat(),
            'message': 'Resumo executivo gerado'
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar resumo executivo: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@dashboard_preditivo_bp.route('/config', methods=['GET'])
def obter_configuracao():
    """Retorna configuração atual do dashboard preditivo"""
    try:
        config = {
            'prazos': {
                'final_pnsb': dashboard_preditivo_service.prazo_final_pnsb.strftime('%d/%m/%Y'),
                'p1_p2': dashboard_preditivo_service.prazo_p1_p2.strftime('%d/%m/%Y'),
                'questionarios': dashboard_preditivo_service.prazo_questionarios.strftime('%d/%m/%Y')
            },
            'municipios': dashboard_preditivo_service.municipios_sc,
            'thresholds': {
                'velocidade_minima': 1.0,
                'score_saude_minimo': 60,
                'dias_alerta_prazo': 30
            },
            'features': {
                'analise_prazos': True,
                'identificacao_riscos': True,
                'projecoes_ia': True,
                'alertas_criticos': True,
                'analise_municipios': True
            }
        }
        
        return jsonify({
            'success': True,
            'data': config,
            'message': 'Configuração do dashboard preditivo'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500