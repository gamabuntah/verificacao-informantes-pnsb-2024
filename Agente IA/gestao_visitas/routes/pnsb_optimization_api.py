"""
API Unificada de Otimização de Rotas para PNSB 2024
Endpoints claros e funcionais para otimização de visitas
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
import logging
from typing import List, Dict, Any

from gestao_visitas.services.pnsb_route_optimizer import (
    PNSBRouteOptimizer, 
    PNSBRoutePoint, 
    PNSBOptimizedRoute
)
from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita

logger = logging.getLogger(__name__)

# Blueprint para APIs de otimização
pnsb_optimization_bp = Blueprint('pnsb_optimization', __name__)


@pnsb_optimization_bp.route('/status', methods=['GET'])
def optimization_status():
    """Status do serviço de otimização"""
    try:
        optimizer = PNSBRouteOptimizer()
        return jsonify({
            'status': 'active',
            'service': 'PNSB Route Optimization',
            'version': '1.0.0',
            'capabilities': {
                'daily_optimization': True,
                'weekly_planning': True,
                'database_integration': True,
                'custom_points': True
            },
            'municipalities': len(optimizer.municipalities),
            'base_location': optimizer.base_location
        })
    except Exception as e:
        logger.error(f"❌ Erro ao verificar status: {str(e)}")
        return jsonify({'error': 'Serviço indisponível'}), 500


@pnsb_optimization_bp.route('/optimize/daily', methods=['POST'])
def optimize_daily_route():
    """
    Otimiza rota para um dia específico
    
    Body:
    {
        "date": "2025-07-15",  # opcional
        "start_time": "08:00",  # opcional
        "custom_points": [],  # opcional
        "municipality_filter": "Itajaí"  # opcional
    }
    """
    try:
        data = request.get_json() or {}
        
        optimizer = PNSBRouteOptimizer()
        
        # Parâmetros
        date_filter = data.get('date')
        start_time = data.get('start_time', '08:00')
        custom_points = data.get('custom_points', [])
        municipality_filter = data.get('municipality_filter')
        
        # Carregar pontos
        if custom_points:
            # Usar pontos customizados
            route_points = []
            for point_data in custom_points:
                point = PNSBRoutePoint(
                    id=point_data.get('id', f"custom_{len(route_points)}"),
                    name=point_data['name'],
                    lat=float(point_data['lat']),
                    lng=float(point_data['lng']),
                    municipality=point_data.get('municipality', ''),
                    entity_type=point_data.get('entity_type', 'prefeitura'),
                    survey_type=point_data.get('survey_type', 'ambos'),
                    priority=int(point_data.get('priority', 2)),
                    estimated_duration=int(point_data.get('estimated_duration', 120))
                )
                route_points.append(point)
        else:
            # Carregar do banco de dados
            route_points = optimizer.load_visits_from_database(date_filter)
            
            # Filtrar por município se especificado
            if municipality_filter:
                route_points = [p for p in route_points if p.municipality == municipality_filter]
        
        if not route_points:
            return jsonify({
                'success': False,
                'error': 'Nenhuma visita encontrada para otimizar',
                'points_found': 0
            }), 400
        
        # Otimizar
        optimized_route = optimizer.optimize_daily_route(route_points, start_time)
        
        # Gerar resumo
        summary = optimizer.generate_route_summary(optimized_route)
        
        return jsonify({
            'success': True,
            'route': {
                'points': [_point_to_dict(p) for p in optimized_route.route_points],
                'total_distance_km': optimized_route.total_distance_km,
                'total_duration_hours': optimized_route.total_duration_hours,
                'travel_time_hours': optimized_route.total_travel_time_hours,
                'start_time': optimized_route.start_time,
                'end_time': optimized_route.end_time,
                'efficiency': optimized_route.route_efficiency,
                'optimization_level': optimized_route.optimization_level
            },
            'summary': summary,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro na otimização diária: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'optimization_error'
        }), 500


@pnsb_optimization_bp.route('/optimize/weekly', methods=['POST'])
def optimize_weekly_schedule():
    """
    Otimiza cronograma semanal
    
    Body:
    {
        "start_date": "2025-07-14",
        "working_days": 5,
        "municipality_filter": "Itajaí"  # opcional
    }
    """
    try:
        data = request.get_json() or {}
        
        optimizer = PNSBRouteOptimizer()
        
        # Parâmetros
        start_date = data.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        working_days = int(data.get('working_days', 5))
        municipality_filter = data.get('municipality_filter')
        
        # Carregar visitas agendadas
        route_points = optimizer.load_visits_from_database()
        
        # Filtrar por município se especificado
        if municipality_filter:
            route_points = [p for p in route_points if p.municipality == municipality_filter]
        
        if not route_points:
            return jsonify({
                'success': False,
                'error': 'Nenhuma visita encontrada para cronograma semanal',
                'points_found': 0
            }), 400
        
        # Otimizar cronograma semanal
        weekly_routes = optimizer.optimize_weekly_schedule(route_points, working_days)
        
        # Formatar resposta
        weekly_schedule = []
        for i, route in enumerate(weekly_routes):
            day_date = datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=i)
            
            weekly_schedule.append({
                'day': i + 1,
                'date': day_date.strftime('%Y-%m-%d'),
                'weekday': day_date.strftime('%A'),
                'points': [_point_to_dict(p) for p in route.route_points],
                'total_distance_km': route.total_distance_km,
                'total_duration_hours': route.total_duration_hours,
                'efficiency': route.route_efficiency,
                'summary': optimizer.generate_route_summary(route)
            })
        
        return jsonify({
            'success': True,
            'weekly_schedule': weekly_schedule,
            'total_days': len(weekly_routes),
            'total_points': sum(len(route.route_points) for route in weekly_routes),
            'avg_efficiency': sum(route.route_efficiency for route in weekly_routes) / len(weekly_routes) if weekly_routes else 0,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no cronograma semanal: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'type': 'weekly_optimization_error'
        }), 500


@pnsb_optimization_bp.route('/visits/pending', methods=['GET'])
def get_pending_visits():
    """Lista visitas pendentes para otimização"""
    try:
        optimizer = PNSBRouteOptimizer()
        
        # Carregar visitas pendentes
        route_points = optimizer.load_visits_from_database()
        
        # Agrupar por município
        by_municipality = {}
        for point in route_points:
            if point.municipality not in by_municipality:
                by_municipality[point.municipality] = []
            by_municipality[point.municipality].append(_point_to_dict(point))
        
        return jsonify({
            'success': True,
            'total_visits': len(route_points),
            'municipalities': len(by_municipality),
            'by_municipality': by_municipality,
            'available_municipalities': list(optimizer.municipalities.keys())
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar visitas pendentes: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pnsb_optimization_bp.route('/municipalities', methods=['GET'])
def get_municipalities():
    """Lista municípios disponíveis para otimização"""
    try:
        optimizer = PNSBRouteOptimizer()
        
        municipalities = []
        for name, coords in optimizer.municipalities.items():
            # Contar visitas agendadas por município
            visit_count = db.session.query(Visita).filter(
                Visita.municipio == name,
                Visita.status.in_(['agendada', 'confirmada'])
            ).count()
            
            municipalities.append({
                'name': name,
                'lat': coords['lat'],
                'lng': coords['lng'],
                'scheduled_visits': visit_count,
                'distance_from_base': optimizer._calculate_distance(
                    optimizer.base_location['lat'], 
                    optimizer.base_location['lng'],
                    coords['lat'], 
                    coords['lng']
                )
            })
        
        # Ordenar por distância da base
        municipalities.sort(key=lambda x: x['distance_from_base'])
        
        return jsonify({
            'success': True,
            'total_municipalities': len(municipalities),
            'municipalities': municipalities,
            'base_location': optimizer.base_location
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao listar municípios: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pnsb_optimization_bp.route('/export/csv', methods=['POST'])
def export_route_csv():
    """Exporta rota otimizada como CSV"""
    try:
        data = request.get_json() or {}
        
        # Recriar rota baseada nos dados fornecidos
        route_data = data.get('route', {})
        points = route_data.get('points', [])
        
        if not points:
            return jsonify({
                'success': False,
                'error': 'Nenhum ponto fornecido para exportação'
            }), 400
        
        # Gerar CSV
        csv_content = "Sequencia,Municipio,Local,Chegada,Saida,Duracao,Tipo_Coleta,Prioridade\n"
        
        for i, point in enumerate(points):
            csv_content += f"{i+1},{point.get('municipality', '')},{point.get('name', '')},"
            csv_content += f"{point.get('arrival_time', '')},{point.get('departure_time', '')},"
            csv_content += f"{point.get('estimated_duration', 120)},{point.get('survey_type', 'ambos')},"
            csv_content += f"{point.get('priority', 2)}\n"
        
        return jsonify({
            'success': True,
            'csv_content': csv_content,
            'filename': f"rota_pnsb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        })
        
    except Exception as e:
        logger.error(f"❌ Erro ao exportar CSV: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def _point_to_dict(point: PNSBRoutePoint) -> Dict[str, Any]:
    """Converte RoutePoint para dicionário"""
    return {
        'id': point.id,
        'name': point.name,
        'lat': point.lat,
        'lng': point.lng,
        'municipality': point.municipality,
        'entity_type': point.entity_type,
        'survey_type': point.survey_type,
        'priority': point.priority,
        'estimated_duration': point.estimated_duration,
        'business_hours': point.business_hours,
        'contact_info': point.contact_info,
        'requirements': point.visit_requirements
    }


# Handlers de erro
@pnsb_optimization_bp.errorhandler(400)
def bad_request(error):
    return jsonify({
        'success': False,
        'error': 'Requisição inválida',
        'type': 'bad_request'
    }), 400


@pnsb_optimization_bp.errorhandler(500)
def internal_error(error):
    logger.error(f"❌ Erro interno: {str(error)}")
    return jsonify({
        'success': False,
        'error': 'Erro interno do servidor',
        'type': 'internal_error'
    }), 500