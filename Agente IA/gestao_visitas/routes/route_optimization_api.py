"""
APIs para Otimização de Rotas - PNSB 2024
Sistema avançado de otimização e planejamento de rotas
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import json
from typing import List, Dict, Any

from gestao_visitas.services.route_optimizer import RouteOptimizer, RoutePoint
from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita

route_optimization_bp = Blueprint('route_optimization', __name__)


@route_optimization_bp.route('/optimize/daily-route', methods=['POST'])
def optimize_daily_route():
    """
    Otimiza rota para um dia específico
    """
    try:
        data = request.get_json() or {}
        
        # Parâmetros de entrada
        municipality = data.get('municipality')
        optimization_type = data.get('optimization_type', 'balanced')  # distance, time, priority, balanced
        start_location = data.get('start_location')  # [lat, lng]
        custom_points = data.get('points', [])  # Pontos customizados
        
        optimizer = RouteOptimizer()
        
        # Carregar pontos
        if custom_points:
            # Usar pontos customizados
            route_points = []
            for point_data in custom_points:
                point = RoutePoint(
                    id=point_data.get('id', f"custom_{len(route_points)}"),
                    name=point_data['name'],
                    lat=float(point_data['lat']),
                    lng=float(point_data['lng']),
                    municipality=point_data.get('municipality', 'Unknown'),
                    priority=int(point_data.get('priority', 2)),
                    estimated_duration=int(point_data.get('estimated_duration', 60)),
                    visit_type=point_data.get('visit_type', 'standard'),
                    requirements=point_data.get('requirements', [])
                )
                route_points.append(point)
        else:
            # Carregar do banco de dados
            route_points = optimizer.load_entities_as_route_points(municipality)
        
        if not route_points:
            return jsonify({
                'success': False,
                'error': 'Nenhum ponto válido encontrado para otimização'
            }), 400
        
        # Otimizar rota
        start_coords = tuple(start_location) if start_location else None
        optimized_route = optimizer.optimize_daily_route(
            route_points, 
            start_location=start_coords,
            optimization_type=optimization_type
        )
        
        # Sugerir horários
        schedule_info = optimizer.suggest_optimal_start_time(optimized_route)
        
        # Analisar eficiência
        efficiency_analysis = optimizer.analyze_route_efficiency(optimized_route)
        
        return jsonify({
            'success': True,
            'data': {
                'optimized_route': {
                    'points': [_point_to_dict(p) for p in optimized_route.points],
                    'total_distance_km': optimized_route.total_distance_km,
                    'total_duration_minutes': optimized_route.total_duration_minutes,
                    'total_driving_time_minutes': optimized_route.total_driving_time_minutes,
                    'optimization_score': optimized_route.optimization_score,
                    'route_type': optimized_route.route_type,
                    'created_at': optimized_route.created_at.isoformat(),
                    'metadata': optimized_route.metadata
                },
                'schedule_suggestion': schedule_info,
                'efficiency_analysis': efficiency_analysis,
                'optimization_summary': {
                    'points_optimized': len(optimized_route.points),
                    'algorithm_used': optimized_route.metadata.get('algorithm', 'unknown'),
                    'optimization_type': optimization_type,
                    'estimated_fuel_cost': _estimate_fuel_cost(optimized_route.total_distance_km),
                    'environmental_impact': _calculate_co2_emissions(optimized_route.total_distance_km)
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na otimização de rota diária: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na otimização: {str(e)}'
        }), 500


@route_optimization_bp.route('/optimize/weekly-plan', methods=['POST'])
def optimize_weekly_plan():
    """
    Otimiza plano semanal dividindo pontos em múltiplos dias
    """
    try:
        data = request.get_json() or {}
        
        # Parâmetros de entrada
        municipality = data.get('municipality')
        start_date = data.get('start_date')  # ISO format
        working_days = data.get('working_days', 5)
        custom_points = data.get('points', [])
        
        if not start_date:
            return jsonify({
                'success': False,
                'error': 'Data de início é obrigatória'
            }), 400
        
        start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        optimizer = RouteOptimizer()
        
        # Carregar pontos
        if custom_points:
            route_points = []
            for point_data in custom_points:
                point = RoutePoint(
                    id=point_data.get('id', f"custom_{len(route_points)}"),
                    name=point_data['name'],
                    lat=float(point_data['lat']),
                    lng=float(point_data['lng']),
                    municipality=point_data.get('municipality', 'Unknown'),
                    priority=int(point_data.get('priority', 2)),
                    estimated_duration=int(point_data.get('estimated_duration', 60)),
                    visit_type=point_data.get('visit_type', 'standard')
                )
                route_points.append(point)
        else:
            route_points = optimizer.load_entities_as_route_points(municipality)
        
        if not route_points:
            return jsonify({
                'success': False,
                'error': 'Nenhum ponto encontrado para planejamento semanal'
            }), 400
        
        # Otimizar plano semanal
        weekly_routes = optimizer.optimize_weekly_plan(
            route_points, 
            start_date_obj, 
            working_days
        )
        
        # Calcular estatísticas semanais
        weekly_stats = _calculate_weekly_statistics(weekly_routes)
        
        return jsonify({
            'success': True,
            'data': {
                'weekly_plan': {
                    'start_date': start_date,
                    'working_days': working_days,
                    'total_days_planned': len(weekly_routes),
                    'daily_routes': [
                        {
                            'day': i + 1,
                            'planned_date': route.metadata.get('planned_date'),
                            'points': [_point_to_dict(p) for p in route.points],
                            'total_distance_km': route.total_distance_km,
                            'total_duration_minutes': route.total_duration_minutes,
                            'optimization_score': route.optimization_score,
                            'schedule_suggestion': optimizer.suggest_optimal_start_time(route)
                        }
                        for i, route in enumerate(weekly_routes)
                    ]
                },
                'weekly_statistics': weekly_stats,
                'recommendations': _generate_weekly_recommendations(weekly_routes, route_points)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na otimização semanal: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na otimização semanal: {str(e)}'
        }), 500


@route_optimization_bp.route('/optimize/alternatives', methods=['POST'])
def get_route_alternatives():
    """
    Gera múltiplas alternativas de rota com diferentes critérios
    """
    try:
        data = request.get_json() or {}
        
        municipality = data.get('municipality')
        alternatives_count = min(data.get('count', 3), 5)  # Máximo 5 alternativas
        custom_points = data.get('points', [])
        
        optimizer = RouteOptimizer()
        
        # Carregar pontos
        if custom_points:
            route_points = []
            for point_data in custom_points:
                point = RoutePoint(
                    id=point_data.get('id', f"custom_{len(route_points)}"),
                    name=point_data['name'],
                    lat=float(point_data['lat']),
                    lng=float(point_data['lng']),
                    municipality=point_data.get('municipality', 'Unknown'),
                    priority=int(point_data.get('priority', 2)),
                    estimated_duration=int(point_data.get('estimated_duration', 60))
                )
                route_points.append(point)
        else:
            route_points = optimizer.load_entities_as_route_points(municipality)
        
        if not route_points:
            return jsonify({
                'success': False,
                'error': 'Nenhum ponto encontrado para gerar alternativas'
            }), 400
        
        # Gerar alternativas
        alternatives = optimizer.get_alternative_routes(route_points, alternatives_count)
        
        return jsonify({
            'success': True,
            'data': {
                'alternatives': [
                    {
                        'option': i + 1,
                        'optimization_type': route.route_type.replace('alternative_', ''),
                        'points': [_point_to_dict(p) for p in route.points],
                        'total_distance_km': route.total_distance_km,
                        'total_duration_minutes': route.total_duration_minutes,
                        'optimization_score': route.optimization_score,
                        'pros_cons': _analyze_route_pros_cons(route),
                        'best_for': _determine_route_best_use(route)
                    }
                    for i, route in enumerate(alternatives)
                ],
                'comparison_summary': _create_alternatives_comparison(alternatives)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao gerar alternativas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao gerar alternativas: {str(e)}'
        }), 500


@route_optimization_bp.route('/analyze/efficiency', methods=['POST'])
def analyze_route_efficiency():
    """
    Analisa eficiência de uma rota específica
    """
    try:
        data = request.get_json() or {}
        
        # Reconstituir rota dos dados
        points_data = data.get('points', [])
        if not points_data:
            return jsonify({
                'success': False,
                'error': 'Dados da rota são obrigatórios'
            }), 400
        
        optimizer = RouteOptimizer()
        
        # Converter dados para RoutePoints
        route_points = []
        for point_data in points_data:
            point = RoutePoint(
                id=point_data.get('id', f"point_{len(route_points)}"),
                name=point_data['name'],
                lat=float(point_data['lat']),
                lng=float(point_data['lng']),
                municipality=point_data.get('municipality', 'Unknown'),
                priority=int(point_data.get('priority', 2)),
                estimated_duration=int(point_data.get('estimated_duration', 60))
            )
            route_points.append(point)
        
        # Otimizar para obter métricas
        optimized_route = optimizer.optimize_daily_route(route_points)
        
        # Análise detalhada
        efficiency_analysis = optimizer.analyze_route_efficiency(optimized_route)
        
        # Comparação com alternativas
        alternatives = optimizer.get_alternative_routes(route_points, 2)
        best_alternative = alternatives[0] if alternatives else None
        
        comparison = None
        if best_alternative:
            comparison = {
                'current_score': optimized_route.optimization_score,
                'best_alternative_score': best_alternative.optimization_score,
                'potential_improvement': best_alternative.optimization_score - optimized_route.optimization_score,
                'distance_savings_km': optimized_route.total_distance_km - best_alternative.total_distance_km,
                'time_savings_minutes': optimized_route.total_duration_minutes - best_alternative.total_duration_minutes
            }
        
        return jsonify({
            'success': True,
            'data': {
                'efficiency_analysis': efficiency_analysis,
                'current_route_summary': {
                    'total_points': len(optimized_route.points),
                    'total_distance_km': optimized_route.total_distance_km,
                    'total_duration_hours': round(optimized_route.total_duration_minutes / 60, 1),
                    'optimization_score': optimized_route.optimization_score
                },
                'improvement_comparison': comparison,
                'actionable_recommendations': _generate_actionable_recommendations(efficiency_analysis)
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na análise de eficiência: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na análise: {str(e)}'
        }), 500


@route_optimization_bp.route('/municipalities/points', methods=['GET'])
def get_municipality_points():
    """
    Retorna pontos disponíveis por município para otimização
    """
    try:
        municipality = request.args.get('municipality')
        include_coordinates = request.args.get('include_coordinates', 'true').lower() == 'true'
        
        optimizer = RouteOptimizer()
        points = optimizer.load_entities_as_route_points(municipality)
        
        # Estatísticas por município
        municipalities_stats = {}
        for point in points:
            mun = point.municipality
            if mun not in municipalities_stats:
                municipalities_stats[mun] = {
                    'total_points': 0,
                    'priority_points': 0,
                    'mrs_required': 0,
                    'map_required': 0
                }
            
            municipalities_stats[mun]['total_points'] += 1
            if point.priority == 1:
                municipalities_stats[mun]['priority_points'] += 1
            if 'MRS' in point.requirements:
                municipalities_stats[mun]['mrs_required'] += 1
            if 'MAP' in point.requirements:
                municipalities_stats[mun]['map_required'] += 1
        
        return jsonify({
            'success': True,
            'data': {
                'municipalities_statistics': municipalities_stats,
                'total_points': len(points),
                'points': [_point_to_dict(p, include_coordinates) for p in points] if municipality else [],
                'optimization_ready': len(points) > 0,
                'recommendations': {
                    'ideal_daily_limit': 6,
                    'max_recommended_distance': 50,
                    'estimated_days_needed': max(1, len(points) // 6) if points else 0
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro ao carregar pontos: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao carregar dados: {str(e)}'
        }), 500


@route_optimization_bp.route('/integrate/visits', methods=['POST'])
def integrate_with_visits():
    """
    Integra otimização de rotas com visitas agendadas
    """
    try:
        data = request.get_json() or {}
        
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        municipality = data.get('municipality')
        
        if not start_date:
            return jsonify({
                'success': False,
                'error': 'Data de início é obrigatória'
            }), 400
        
        start_date_obj = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_date_obj = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else start_date_obj + timedelta(days=7)
        
        # Buscar visitas existentes no período
        query = Visita.query.filter(
            Visita.data_visita >= start_date_obj.date(),
            Visita.data_visita <= end_date_obj.date()
        )
        
        if municipality:
            query = query.filter(Visita.municipio == municipality)
        
        existing_visits = query.all()
        
        # Converter visitas para pontos de rota
        optimizer = RouteOptimizer()
        visit_points = []
        
        for visit in existing_visits:
            if hasattr(visit, 'latitude') and visit.latitude and visit.longitude:
                point = RoutePoint(
                    id=f"visit_{visit.id}",
                    name=f"{visit.local or 'Local não especificado'}",
                    lat=visit.latitude,
                    lng=visit.longitude,
                    municipality=visit.municipio,
                    priority=1 if visit.status == 'agendada' else 2,
                    estimated_duration=120,  # 2 horas para visitas
                    visit_type="scheduled_visit"
                )
                visit_points.append(point)
        
        # Adicionar entidades não visitadas
        all_entity_points = optimizer.load_entities_as_route_points(municipality)
        
        # Filtrar entidades já visitadas
        visited_entity_ids = set()
        for visit in existing_visits:
            if hasattr(visit, 'entidade_id') and visit.entidade_id:
                visited_entity_ids.add(f"identificada_{visit.entidade_id}")
                visited_entity_ids.add(f"prioritaria_{visit.entidade_id}")
        
        unvisited_points = [p for p in all_entity_points if p.id not in visited_entity_ids]
        
        # Otimizar considerando visitas existentes e pendentes
        all_points = visit_points + unvisited_points
        
        if all_points:
            optimized_plan = optimizer.optimize_weekly_plan(all_points, start_date_obj)
        else:
            optimized_plan = []
        
        return jsonify({
            'success': True,
            'data': {
                'integration_summary': {
                    'period': f"{start_date} a {end_date or start_date}",
                    'existing_visits': len(existing_visits),
                    'pending_entities': len(unvisited_points),
                    'total_points_to_optimize': len(all_points)
                },
                'existing_visits': [
                    {
                        'id': visit.id,
                        'local': visit.local,
                        'municipio': visit.municipio,
                        'data_visita': visit.data_visita.isoformat() if visit.data_visita else None,
                        'status': visit.status
                    }
                    for visit in existing_visits
                ],
                'optimized_plan': [
                    {
                        'day': i + 1,
                        'planned_date': route.metadata.get('planned_date'),
                        'points': [_point_to_dict(p) for p in route.points],
                        'includes_scheduled_visits': any(p.visit_type == 'scheduled_visit' for p in route.points),
                        'total_duration_hours': round(route.total_duration_minutes / 60, 1)
                    }
                    for i, route in enumerate(optimized_plan)
                ],
                'recommendations': [
                    f"Reagendar {len([v for v in existing_visits if v.status == 'agendada'])} visitas confirmadas",
                    f"Otimizar {len(unvisited_points)} entidades pendentes",
                    "Considerar janelas de horário das visitas existentes"
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro na integração com visitas: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro na integração: {str(e)}'
        }), 500


# Funções auxiliares

def _point_to_dict(point: RoutePoint, include_coordinates: bool = True) -> Dict[str, Any]:
    """Converte RoutePoint para dicionário"""
    result = {
        'id': point.id,
        'name': point.name,
        'municipality': point.municipality,
        'priority': point.priority,
        'estimated_duration_minutes': point.estimated_duration,
        'visit_type': point.visit_type,
        'requirements': point.requirements
    }
    
    if include_coordinates:
        result.update({
            'lat': point.lat,
            'lng': point.lng
        })
    
    if point.time_window_start:
        result['time_window_start'] = point.time_window_start
    if point.time_window_end:
        result['time_window_end'] = point.time_window_end
    
    return result


def _estimate_fuel_cost(distance_km: float) -> Dict[str, float]:
    """Estima custo de combustível"""
    # Valores médios para Santa Catarina (2024)
    fuel_consumption_per_100km = 12  # litros
    fuel_price_per_liter = 5.50  # reais
    
    fuel_needed = (distance_km / 100) * fuel_consumption_per_100km
    total_cost = fuel_needed * fuel_price_per_liter
    
    return {
        'distance_km': distance_km,
        'fuel_liters': round(fuel_needed, 2),
        'estimated_cost_brl': round(total_cost, 2)
    }


def _calculate_co2_emissions(distance_km: float) -> Dict[str, float]:
    """Calcula emissões de CO2"""
    # Fator de emissão médio para veículos leves
    co2_per_km = 0.12  # kg CO2 por km
    
    total_co2 = distance_km * co2_per_km
    
    return {
        'distance_km': distance_km,
        'co2_emissions_kg': round(total_co2, 2),
        'trees_equivalent': round(total_co2 / 22, 1)  # 1 árvore absorve ~22kg CO2/ano
    }


def _calculate_weekly_statistics(weekly_routes: List) -> Dict[str, Any]:
    """Calcula estatísticas do plano semanal"""
    if not weekly_routes:
        return {}
    
    total_points = sum(len(route.points) for route in weekly_routes)
    total_distance = sum(route.total_distance_km for route in weekly_routes)
    total_time = sum(route.total_duration_minutes for route in weekly_routes)
    avg_score = sum(route.optimization_score for route in weekly_routes) / len(weekly_routes)
    
    return {
        'total_days': len(weekly_routes),
        'total_points': total_points,
        'total_distance_km': round(total_distance, 2),
        'total_duration_hours': round(total_time / 60, 1),
        'average_optimization_score': round(avg_score, 1),
        'average_points_per_day': round(total_points / len(weekly_routes), 1),
        'average_distance_per_day': round(total_distance / len(weekly_routes), 2),
        'estimated_total_cost': _estimate_fuel_cost(total_distance),
        'environmental_impact': _calculate_co2_emissions(total_distance)
    }


def _generate_weekly_recommendations(weekly_routes: List, all_points: List) -> List[str]:
    """Gera recomendações para o plano semanal"""
    recommendations = []
    
    if not weekly_routes:
        return ["Nenhuma rota otimizada disponível"]
    
    # Análise de carga de trabalho
    daily_points = [len(route.points) for route in weekly_routes]
    max_points = max(daily_points) if daily_points else 0
    min_points = min(daily_points) if daily_points else 0
    
    if max_points - min_points > 3:
        recommendations.append("Considere redistribuir pontos para equilibrar carga diária")
    
    # Análise de distância
    daily_distances = [route.total_distance_km for route in weekly_routes]
    avg_distance = sum(daily_distances) / len(daily_distances) if daily_distances else 0
    
    if avg_distance > 40:
        recommendations.append("Distância diária média alta - verificar agrupamento por proximidade")
    
    # Análise de prioridade
    total_p1 = len([p for route in weekly_routes for p in route.points if p.priority == 1])
    if total_p1 > 0:
        recommendations.append(f"Priorizar {total_p1} entidades P1 nos primeiros dias")
    
    # Análise temporal
    long_days = [route for route in weekly_routes if route.total_duration_minutes > 480]
    if long_days:
        recommendations.append(f"{len(long_days)} dia(s) com mais de 8h - considere redistribuir")
    
    return recommendations


def _analyze_route_pros_cons(route) -> Dict[str, List[str]]:
    """Analisa prós e contras de uma rota"""
    pros = []
    cons = []
    
    # Análise de distância
    if route.total_distance_km < 30:
        pros.append("Baixo consumo de combustível")
    elif route.total_distance_km > 60:
        cons.append("Alto consumo de combustível")
    
    # Análise de tempo
    work_time_ratio = (route.total_duration_minutes - route.total_driving_time_minutes) / route.total_duration_minutes
    if work_time_ratio > 0.7:
        pros.append("Alto tempo produtivo (pouco deslocamento)")
    elif work_time_ratio < 0.5:
        cons.append("Muito tempo em deslocamento")
    
    # Análise de pontos
    if len(route.points) >= 6:
        pros.append("Alta produtividade (muitos pontos)")
    elif len(route.points) <= 3:
        cons.append("Baixa produtividade (poucos pontos)")
    
    # Análise de otimização
    if route.optimization_score >= 80:
        pros.append("Rota bem otimizada")
    elif route.optimization_score < 60:
        cons.append("Rota pode ser melhorada")
    
    return {'pros': pros, 'cons': cons}


def _determine_route_best_use(route) -> str:
    """Determina o melhor uso para uma rota"""
    if route.total_distance_km < 20:
        return "Ideal para dias com pouco combustível disponível"
    elif route.total_driving_time_minutes < route.total_duration_minutes * 0.3:
        return "Ideal para maximizar tempo de trabalho"
    elif len([p for p in route.points if p.priority == 1]) > len(route.points) * 0.5:
        return "Ideal para focar em entidades prioritárias"
    elif route.total_duration_minutes < 360:
        return "Ideal para meio período ou treinamento"
    else:
        return "Ideal para dia completo de trabalho"


def _create_alternatives_comparison(alternatives: List) -> Dict[str, Any]:
    """Cria comparação entre alternativas"""
    if not alternatives:
        return {}
    
    distances = [route.total_distance_km for route in alternatives]
    times = [route.total_duration_minutes for route in alternatives]
    scores = [route.optimization_score for route in alternatives]
    
    return {
        'best_for_distance': alternatives[distances.index(min(distances))].route_type.replace('alternative_', ''),
        'best_for_time': alternatives[times.index(min(times))].route_type.replace('alternative_', ''),
        'best_overall_score': alternatives[scores.index(max(scores))].route_type.replace('alternative_', ''),
        'distance_range': f"{min(distances):.1f} - {max(distances):.1f} km",
        'time_range': f"{min(times)//60:.1f} - {max(times)//60:.1f} horas",
        'score_range': f"{min(scores):.1f} - {max(scores):.1f}"
    }


def _generate_actionable_recommendations(efficiency_analysis: Dict) -> List[str]:
    """Gera recomendações acionáveis baseadas na análise"""
    recommendations = []
    
    metrics = efficiency_analysis.get('efficiency_metrics', {})
    suggestions = efficiency_analysis.get('suggestions', [])
    
    # Transformar sugestões em ações específicas
    for suggestion in suggestions:
        if "agrupar" in suggestion.lower():
            recommendations.append("AÇÃO: Reagendar visitas próximas para o mesmo dia")
        elif "priorizar" in suggestion.lower():
            recommendations.append("AÇÃO: Mover entidades P1 para início da rota")
        elif "dividir" in suggestion.lower():
            recommendations.append("AÇÃO: Criar rota adicional para reduzir carga diária")
    
    # Recomendações baseadas em métricas
    if metrics.get('work_time_ratio', 0) < 0.6:
        recommendations.append("AÇÃO: Revisar agrupamento geográfico para reduzir deslocamentos")
    
    if metrics.get('points_per_hour', 0) < 0.8:
        recommendations.append("AÇÃO: Otimizar tempo de visita ou adicionar mais pontos")
    
    return recommendations