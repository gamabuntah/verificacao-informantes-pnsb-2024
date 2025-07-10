"""
APIs para Sistema de Google Maps PNSB 2024
Endpoints para dados do mapa, marcadores e rotas
"""

from flask import Blueprint, request, jsonify, current_app
from gestao_visitas.services.google_maps_service import GoogleMapsService
from gestao_visitas.db import db
import logging
from datetime import datetime
import os

logger = logging.getLogger(__name__)

google_maps_bp = Blueprint('google_maps', __name__)

# Instância global do serviço
maps_service = None

def init_google_maps_service(app):
    """Inicializa o serviço do Google Maps"""
    global maps_service
    
    with app.app_context():
        maps_service = GoogleMapsService(db)
        logger.info("GoogleMapsService inicializado")

@google_maps_bp.route('/api/maps/data', methods=['GET'])
def get_map_data():
    """Retorna todos os dados necessários para renderizar o mapa"""
    try:
        if not maps_service:
            return jsonify({
                'error': 'Serviço de mapas não inicializado',
                'success': False
            }), 503
        
        # Obter filtros da query string
        filtro_status = request.args.get('status')
        filtro_tipo = request.args.get('tipo')
        filtro_prioridade = request.args.get('prioridade')
        filtro_municipio = request.args.get('municipio')
        
        # Obter dados completos do mapa
        map_data = maps_service.get_map_data()
        
        # Aplicar filtros se fornecidos
        marcadores_filtrados = map_data['marcadores']
        
        if filtro_status:
            marcadores_filtrados = [m for m in marcadores_filtrados if m['status'] == filtro_status]
        
        if filtro_tipo:
            marcadores_filtrados = [m for m in marcadores_filtrados if m['tipo'] == filtro_tipo]
        
        if filtro_prioridade:
            marcadores_filtrados = [m for m in marcadores_filtrados if m['prioridade'] == filtro_prioridade]
        
        if filtro_municipio:
            marcadores_filtrados = [m for m in marcadores_filtrados if m['municipio'] == filtro_municipio]
        
        # Atualizar dados com marcadores filtrados
        map_data['marcadores'] = marcadores_filtrados
        
        return jsonify({
            'success': True,
            'data': map_data,
            'timestamp': datetime.now().isoformat(),
            'message': f'{len(marcadores_filtrados)} marcadores carregados'
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter dados do mapa: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/config', methods=['GET'])
def get_maps_config():
    """Retorna configuração do Google Maps incluindo API key"""
    try:
        api_key = current_app.config.get('GOOGLE_MAPS_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
        
        if not api_key:
            return jsonify({
                'error': 'Google Maps API key não configurada',
                'success': False,
                'fallback': True,
                'message': 'Usando mapa alternativo (OpenStreetMap)'
            }), 200
        
        return jsonify({
            'success': True,
            'data': {
                'apiKey': api_key,
                'libraries': ['places', 'geometry', 'visualization', 'drawing'],
                'language': 'pt-BR',
                'region': 'BR',
                'mapOptions': {
                    'center': {'lat': -26.9, 'lng': -48.65},
                    'zoom': 10,
                    'mapTypeId': 'roadmap',
                    'mapTypeControl': True,
                    'streetViewControl': True,
                    'fullscreenControl': True,
                    'zoomControl': True
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração do Maps: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/markers/<marker_id>', methods=['GET'])
def get_marker_details(marker_id):
    """Retorna detalhes completos de um marcador específico"""
    try:
        if not maps_service:
            return jsonify({
                'error': 'Serviço de mapas não inicializado',
                'success': False
            }), 503
        
        # Obter todos os dados do mapa
        map_data = maps_service.get_map_data()
        
        # Encontrar marcador específico
        marcador = next((m for m in map_data['marcadores'] if m['id'] == marker_id), None)
        
        if not marcador:
            return jsonify({
                'error': 'Marcador não encontrado',
                'success': False
            }), 404
        
        # Adicionar informações detalhadas
        from gestao_visitas.models.agendamento import Visita
        municipio = marcador['municipio']
        
        # Buscar visitas relacionadas
        visitas = Visita.query.filter_by(municipio=municipio).all()
        
        visitas_detalhadas = []
        for visita in visitas[:5]:  # Limitar a 5 visitas mais recentes
            visitas_detalhadas.append({
                'id': visita.id,
                'data': visita.data.isoformat() if visita.data else None,
                'status': visita.status,
                'tipo_informante': visita.tipo_informante,
                'local': visita.local,
                'pesquisador': visita.pesquisador_responsavel
            })
        
        marcador['visitas_recentes'] = visitas_detalhadas
        marcador['total_visitas_municipio'] = len(visitas)
        
        return jsonify({
            'success': True,
            'data': marcador,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter detalhes do marcador: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/route', methods=['POST'])
def calculate_route():
    """Calcula rota otimizada entre múltiplos pontos"""
    try:
        data = request.get_json()
        
        if not data or 'pontos' not in data:
            return jsonify({
                'error': 'Pontos de rota são obrigatórios',
                'success': False
            }), 400
        
        pontos = data['pontos']
        if len(pontos) < 2:
            return jsonify({
                'error': 'Mínimo de 2 pontos necessários',
                'success': False
            }), 400
        
        # Por enquanto, retornar rota simulada
        # Em produção, integrar com Google Directions API
        rota = {
            'id': f'route_{datetime.now().timestamp()}',
            'origem': pontos[0],
            'destino': pontos[-1],
            'waypoints': pontos[1:-1] if len(pontos) > 2 else [],
            'distancia_total_km': len(pontos) * 15,  # Simulado
            'tempo_total_minutos': len(pontos) * 25,  # Simulado
            'polyline': None,  # Seria a polyline codificada do Google
            'instrucoes': [
                f'Siga para {p["municipio"]}' for p in pontos
            ]
        }
        
        return jsonify({
            'success': True,
            'data': rota,
            'timestamp': datetime.now().isoformat(),
            'message': 'Rota calculada (simulada)'
        })
        
    except Exception as e:
        logger.error(f"Erro ao calcular rota: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/heatmap', methods=['GET'])
def get_heatmap_data():
    """Retorna dados específicos para o heatmap"""
    try:
        if not maps_service:
            return jsonify({
                'error': 'Serviço de mapas não inicializado',
                'success': False
            }), 503
        
        # Tipo de heatmap solicitado
        tipo_heatmap = request.args.get('tipo', 'progresso')
        
        # Obter dados do mapa
        map_data = maps_service.get_map_data()
        heatmap_base = map_data['heatmap']
        
        # Ajustar dados baseado no tipo
        if tipo_heatmap == 'urgencia':
            # Inverter pesos para mostrar urgência
            for point in heatmap_base['points']:
                point['weight'] = 1 - point['weight']
        elif tipo_heatmap == 'densidade':
            # Mostrar densidade de visitas
            from gestao_visitas.models.agendamento import Visita
            for point in heatmap_base['points']:
                municipio = point['municipio']
                total_visitas = Visita.query.filter_by(municipio=municipio).count()
                point['weight'] = min(1, total_visitas / 10)  # Normalizar
        
        return jsonify({
            'success': True,
            'data': heatmap_base,
            'tipo': tipo_heatmap,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter dados do heatmap: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/clusters', methods=['GET'])
def get_clusters():
    """Retorna clusters de marcadores para o mapa"""
    try:
        if not maps_service:
            return jsonify({
                'error': 'Serviço de mapas não inicializado',
                'success': False
            }), 503
        
        # Obter dados do mapa
        map_data = maps_service.get_map_data()
        clusters = map_data.get('clusters', [])
        
        return jsonify({
            'success': True,
            'data': {
                'clusters': clusters,
                'total': len(clusters)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro ao obter clusters: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500

@google_maps_bp.route('/api/maps/export', methods=['POST'])
def export_map():
    """Exporta imagem ou dados do mapa atual"""
    try:
        data = request.get_json()
        formato = data.get('formato', 'png')
        incluir_dados = data.get('incluir_dados', False)
        
        # Por enquanto, retornar URL simulada
        # Em produção, gerar imagem real do mapa
        export_data = {
            'formato': formato,
            'url': f'/api/maps/download/map_export_{datetime.now().timestamp()}.{formato}',
            'timestamp': datetime.now().isoformat()
        }
        
        if incluir_dados:
            map_data = maps_service.get_map_data()
            export_data['dados'] = {
                'marcadores': len(map_data['marcadores']),
                'estatisticas': map_data['estatisticas']
            }
        
        return jsonify({
            'success': True,
            'data': export_data,
            'message': f'Mapa exportado como {formato}'
        })
        
    except Exception as e:
        logger.error(f"Erro ao exportar mapa: {e}")
        return jsonify({
            'error': f'Erro interno: {str(e)}',
            'success': False
        }), 500