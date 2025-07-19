"""
API para configurações da equipe PNSB 2024
Fornece informações sobre a equipe, horários de trabalho e capacidade
"""

from flask import Blueprint, jsonify
from datetime import datetime
import sys
import os

# Adicionar o diretório pai ao path para importar team_config
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

try:
    from config.team_config import get_team_summary, get_dias_restantes_visitas, get_dias_restantes_questionarios, calcular_capacidade_restante
    from config.team_config import NUM_PESQUISADORES, VISITAS_MAX_POR_DIA, CAPACIDADE_TOTAL_DIA
    from config.team_config import DEADLINE_VISITAS, DEADLINE_QUESTIONARIOS, HORARIO_INICIO, HORARIO_FIM
except ImportError as e:
    print(f"Erro ao importar team_config: {e}")
    # Fallback com valores padrão
    NUM_PESQUISADORES = 1
    VISITAS_MAX_POR_DIA = 8
    CAPACIDADE_TOTAL_DIA = 8
    DEADLINE_VISITAS = datetime(2025, 9, 19)
    DEADLINE_QUESTIONARIOS = datetime(2025, 10, 17)
    HORARIO_INICIO = "08:00"
    HORARIO_FIM = "18:00"

team_config_bp = Blueprint('team_config_api', __name__, url_prefix='/api')

@team_config_bp.route('/team-config', methods=['GET'])
def get_team_config():
    """
    Retorna as configurações da equipe para uso no frontend
    """
    try:
        # Tentar usar a função do team_config
        if 'get_team_summary' in globals():
            config = get_team_summary()
        else:
            # Fallback manual
            hoje = datetime.now()
            dias_visitas = (DEADLINE_VISITAS - hoje).days
            dias_questionarios = (DEADLINE_QUESTIONARIOS - hoje).days
            
            config = {
                'num_pesquisadores': NUM_PESQUISADORES,
                'pesquisador_principal': "Pesquisador PNSB 1",
                'horario_inicio': str(HORARIO_INICIO),
                'horario_fim': str(HORARIO_FIM),
                'horas_trabalho_dia': 10,
                'minutos_por_visita': 60,
                'visitas_max_dia': VISITAS_MAX_POR_DIA,
                'capacidade_total_dia': CAPACIDADE_TOTAL_DIA,
                'deadline_visitas': DEADLINE_VISITAS.strftime('%d/%m/%Y'),
                'deadline_questionarios': DEADLINE_QUESTIONARIOS.strftime('%d/%m/%Y'),
                'dias_restantes_visitas': dias_visitas,
                'dias_restantes_questionarios': dias_questionarios,
                'capacidade_restante': int(dias_visitas * (5/7) * CAPACIDADE_TOTAL_DIA)
            }
        
        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao carregar configuração da equipe: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@team_config_bp.route('/team-capacity', methods=['GET'])
def get_team_capacity():
    """
    Retorna informações específicas sobre capacidade da equipe
    """
    try:
        hoje = datetime.now()
        dias_visitas = (DEADLINE_VISITAS - hoje).days
        dias_uteis = int(dias_visitas * (5/7))  # 5 dias úteis por semana
        
        capacidade_info = {
            'pesquisadores_ativos': NUM_PESQUISADORES,
            'visitas_por_dia_por_pesquisador': VISITAS_MAX_POR_DIA,
            'capacidade_total_dia': CAPACIDADE_TOTAL_DIA,
            'dias_restantes': dias_visitas,
            'dias_uteis_restantes': dias_uteis,
            'capacidade_total_restante': dias_uteis * CAPACIDADE_TOTAL_DIA,
            'data_limite_visitas': DEADLINE_VISITAS.strftime('%Y-%m-%d'),
            'data_limite_questionarios': DEADLINE_QUESTIONARIOS.strftime('%Y-%m-%d')
        }
        
        return jsonify({
            'success': True,
            'data': capacidade_info,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao calcular capacidade: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

@team_config_bp.route('/team-status', methods=['GET'])
def get_team_status():
    """
    Retorna status atual da equipe e alertas de capacidade
    """
    try:
        hoje = datetime.now()
        dias_visitas = (DEADLINE_VISITAS - hoje).days
        dias_questionarios = (DEADLINE_QUESTIONARIOS - hoje).days
        
        # Calcular alertas
        alertas = []
        
        if dias_visitas <= 30:
            alertas.append({
                'tipo': 'critico',
                'mensagem': f'CRÍTICO: Apenas {dias_visitas} dias restantes para deadline das visitas',
                'deadline': 'visitas'
            })
        elif dias_visitas <= 60:
            alertas.append({
                'tipo': 'urgente',
                'mensagem': f'URGENTE: {dias_visitas} dias restantes para deadline das visitas',
                'deadline': 'visitas'
            })
        
        if dias_questionarios <= 30:
            alertas.append({
                'tipo': 'critico',
                'mensagem': f'CRÍTICO: Apenas {dias_questionarios} dias restantes para deadline dos questionários',
                'deadline': 'questionarios'
            })
        elif dias_questionarios <= 60:
            alertas.append({
                'tipo': 'urgente',
                'mensagem': f'URGENTE: {dias_questionarios} dias restantes para deadline dos questionários',
                'deadline': 'questionarios'
            })
        
        status = {
            'equipe_ativa': True,
            'pesquisadores_disponiveis': NUM_PESQUISADORES,
            'status_cronograma': 'em_andamento',
            'alertas': alertas,
            'ultima_atualizacao': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao obter status da equipe: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500