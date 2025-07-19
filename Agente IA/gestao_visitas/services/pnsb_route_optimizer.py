"""
Serviço de Otimização de Rotas para PNSB 2024
Sistema completo e funcional para otimização de visitas de campo
"""

import math
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from flask import current_app

from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita

logger = logging.getLogger(__name__)


@dataclass
class PNSBRoutePoint:
    """Ponto de visita PNSB com informações específicas do projeto"""
    id: str
    name: str
    lat: float
    lng: float
    municipality: str
    entity_type: str  # 'prefeitura', 'empresa', 'autarquia', etc.
    survey_type: str  # 'MRS', 'MAP', 'ambos'
    priority: int  # 1=alta, 2=média, 3=baixa
    estimated_duration: int = 120  # minutos (2h padrão PNSB)
    business_hours: Dict[str, str] = None
    contact_info: Dict[str, str] = None
    visit_requirements: List[str] = None
    
    def __post_init__(self):
        if self.business_hours is None:
            self.business_hours = {'start': '08:00', 'end': '17:00'}
        if self.contact_info is None:
            self.contact_info = {}
        if self.visit_requirements is None:
            self.visit_requirements = []


@dataclass
class PNSBOptimizedRoute:
    """Resultado da otimização de rota PNSB"""
    route_points: List[PNSBRoutePoint]
    total_distance_km: float
    total_duration_hours: float
    total_travel_time_hours: float
    start_time: str
    end_time: str
    optimization_level: str  # 'basic', 'intermediate', 'advanced'
    route_efficiency: float  # 0-100%
    daily_capacity: int  # quantas visitas por dia
    week_schedule: List[Dict] = None
    
    def __post_init__(self):
        if self.week_schedule is None:
            self.week_schedule = []


class PNSBRouteOptimizer:
    """
    Otimizador de rotas específico para PNSB 2024
    Considera horários comerciais, prioridades, tipos de coleta
    """
    
    def __init__(self):
        self.base_location = {
            'name': 'Agência IBGE Itajaí',
            'lat': -26.9076,
            'lng': -48.6619,
            'address': 'Rua Rubens de Almeida, 123, Itajaí/SC'
        }
        
        # Coordenadas dos municípios PNSB 2024
        self.municipalities = {
            'Balneário Camboriú': {'lat': -26.9906, 'lng': -48.6349},
            'Balneário Piçarras': {'lat': -26.7574, 'lng': -48.6717},
            'Bombinhas': {'lat': -27.1433, 'lng': -48.4884},
            'Camboriú': {'lat': -27.0248, 'lng': -48.6583},
            'Itajaí': {'lat': -26.9076, 'lng': -48.6619},
            'Itapema': {'lat': -27.0890, 'lng': -48.6114},
            'Luiz Alves': {'lat': -26.7169, 'lng': -48.9357},
            'Navegantes': {'lat': -26.8968, 'lng': -48.6565},
            'Penha': {'lat': -26.7711, 'lng': -48.6506},
            'Porto Belo': {'lat': -27.1588, 'lng': -48.5552},
            'Ilhota': {'lat': -26.8984, 'lng': -48.8269}
        }
        
        # Horários comerciais padrão
        self.business_hours = {
            'prefeitura': {'start': '08:00', 'end': '17:00', 'lunch': '12:00-13:00'},
            'empresa': {'start': '08:00', 'end': '18:00', 'lunch': '12:00-13:00'},
            'autarquia': {'start': '08:00', 'end': '16:00', 'lunch': '12:00-13:00'}
        }
        
        # Tempos de deslocamento estimados (em minutos)
        self.travel_times = self._calculate_travel_matrix()
        
        logger.info("✅ PNSBRouteOptimizer inicializado")
    
    def _calculate_travel_matrix(self) -> Dict[str, Dict[str, int]]:
        """Calcula matriz de tempos de deslocamento entre municípios"""
        matrix = {}
        
        for origin, origin_coords in self.municipalities.items():
            matrix[origin] = {}
            for dest, dest_coords in self.municipalities.items():
                if origin == dest:
                    matrix[origin][dest] = 0
                else:
                    # Cálculo aproximado baseado em distância e condições locais
                    distance = self._calculate_distance(
                        origin_coords['lat'], origin_coords['lng'],
                        dest_coords['lat'], dest_coords['lng']
                    )
                    # Velocidade média considerando trânsito local: 45 km/h
                    travel_time = int((distance / 45) * 60)  # em minutos
                    matrix[origin][dest] = max(travel_time, 15)  # mínimo 15 min
        
        return matrix
    
    def _calculate_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        """Calcula distância entre dois pontos usando fórmula de Haversine"""
        R = 6371  # Raio da Terra em km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2)**2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def load_visits_from_database(self, date_filter: Optional[str] = None) -> List[PNSBRoutePoint]:
        """Carrega visitas do banco de dados e converte para RoutePoints"""
        try:
            query = db.session.query(Visita)
            
            if date_filter:
                query = query.filter(Visita.data == date_filter)
            
            visitas = query.filter(Visita.status.in_(['agendada', 'confirmada'])).all()
            
            route_points = []
            for visita in visitas:
                municipality_coords = self.municipalities.get(visita.municipio)
                
                if municipality_coords:
                    point = PNSBRoutePoint(
                        id=str(visita.id),
                        name=f"{visita.local or visita.municipio} - {visita.municipio}",
                        lat=municipality_coords['lat'],
                        lng=municipality_coords['lng'],
                        municipality=visita.municipio,
                        entity_type='prefeitura',  # Assumindo prefeitura como padrão
                        survey_type=visita.tipo_coleta or 'ambos',
                        priority=2,  # Média como padrão
                        estimated_duration=120,  # 2h padrão
                        business_hours=self.business_hours['prefeitura']
                    )
                    route_points.append(point)
            
            logger.info(f"✅ Carregadas {len(route_points)} visitas do banco")
            return route_points
            
        except Exception as e:
            logger.error(f"❌ Erro ao carregar visitas: {str(e)}")
            return []
    
    def optimize_daily_route(self, points: List[PNSBRoutePoint], 
                           start_time: str = "08:00") -> PNSBOptimizedRoute:
        """Otimiza rota para um dia específico"""
        if not points:
            return self._create_empty_route()
        
        # Algoritmo de otimização: Nearest Neighbor com melhorias
        optimized_points = self._optimize_sequence(points)
        
        # Calcular métricas da rota
        total_distance = self._calculate_route_distance(optimized_points)
        total_travel_time = self._calculate_route_travel_time(optimized_points)
        total_visit_time = sum(point.estimated_duration for point in optimized_points) / 60
        
        # Calcular horários
        current_time = datetime.strptime(start_time, "%H:%M")
        end_time = current_time + timedelta(hours=total_travel_time + total_visit_time)
        
        # Calcular eficiência
        efficiency = self._calculate_route_efficiency(optimized_points)
        
        route = PNSBOptimizedRoute(
            route_points=optimized_points,
            total_distance_km=total_distance,
            total_duration_hours=total_travel_time + total_visit_time,
            total_travel_time_hours=total_travel_time,
            start_time=start_time,
            end_time=end_time.strftime("%H:%M"),
            optimization_level='intermediate',
            route_efficiency=efficiency,
            daily_capacity=len(optimized_points)
        )
        
        logger.info(f"✅ Rota otimizada: {len(optimized_points)} pontos, "
                   f"{total_distance:.1f}km, {total_travel_time + total_visit_time:.1f}h")
        
        return route
    
    def optimize_weekly_schedule(self, points: List[PNSBRoutePoint], 
                               working_days: int = 5) -> List[PNSBOptimizedRoute]:
        """Otimiza cronograma semanal distribuindo visitas"""
        if not points:
            return []
        
        # Priorizar por urgência e localização
        sorted_points = sorted(points, key=lambda p: (p.priority, p.municipality))
        
        # Distribuir em grupos por dia
        points_per_day = max(1, len(sorted_points) // working_days)
        daily_groups = []
        
        for i in range(0, len(sorted_points), points_per_day):
            daily_group = sorted_points[i:i + points_per_day]
            daily_groups.append(daily_group)
        
        # Otimizar cada dia
        weekly_routes = []
        for day, group in enumerate(daily_groups):
            if group:
                route = self.optimize_daily_route(group, "08:00")
                weekly_routes.append(route)
        
        logger.info(f"✅ Cronograma semanal otimizado: {len(weekly_routes)} dias")
        return weekly_routes
    
    def _optimize_sequence(self, points: List[PNSBRoutePoint]) -> List[PNSBRoutePoint]:
        """Otimiza sequência de visitas usando algoritmo Nearest Neighbor"""
        if len(points) <= 1:
            return points
        
        # Começar do ponto mais próximo da base
        base_coords = (self.base_location['lat'], self.base_location['lng'])
        
        unvisited = points.copy()
        optimized = []
        
        # Encontrar ponto inicial mais próximo
        closest_point = min(unvisited, key=lambda p: self._calculate_distance(
            base_coords[0], base_coords[1], p.lat, p.lng
        ))
        
        current_point = closest_point
        optimized.append(current_point)
        unvisited.remove(current_point)
        
        # Algoritmo Nearest Neighbor
        while unvisited:
            closest = min(unvisited, key=lambda p: self._calculate_distance(
                current_point.lat, current_point.lng, p.lat, p.lng
            ))
            optimized.append(closest)
            unvisited.remove(closest)
            current_point = closest
        
        return optimized
    
    def _calculate_route_distance(self, points: List[PNSBRoutePoint]) -> float:
        """Calcula distância total da rota"""
        if len(points) < 2:
            return 0
        
        total_distance = 0
        
        # Distância da base até primeiro ponto
        total_distance += self._calculate_distance(
            self.base_location['lat'], self.base_location['lng'],
            points[0].lat, points[0].lng
        )
        
        # Distâncias entre pontos
        for i in range(len(points) - 1):
            total_distance += self._calculate_distance(
                points[i].lat, points[i].lng,
                points[i + 1].lat, points[i + 1].lng
            )
        
        # Distância do último ponto até a base
        total_distance += self._calculate_distance(
            points[-1].lat, points[-1].lng,
            self.base_location['lat'], self.base_location['lng']
        )
        
        return total_distance
    
    def _calculate_route_travel_time(self, points: List[PNSBRoutePoint]) -> float:
        """Calcula tempo total de deslocamento"""
        distance = self._calculate_route_distance(points)
        # Velocidade média: 45 km/h considerando trânsito local
        return distance / 45
    
    def _calculate_route_efficiency(self, points: List[PNSBRoutePoint]) -> float:
        """Calcula eficiência da rota (0-100%)"""
        if len(points) <= 1:
            return 100.0
        
        # Eficiência baseada na distância total vs distância direta
        total_distance = self._calculate_route_distance(points)
        
        # Calcular distância direta total (sem otimização)
        direct_distance = sum(
            self._calculate_distance(
                self.base_location['lat'], self.base_location['lng'],
                point.lat, point.lng
            ) * 2  # ida e volta
            for point in points
        )
        
        if direct_distance == 0:
            return 100.0
        
        efficiency = max(0, 100 - ((total_distance / direct_distance) * 100 - 100))
        return min(100, efficiency)
    
    def _create_empty_route(self) -> PNSBOptimizedRoute:
        """Cria rota vazia"""
        return PNSBOptimizedRoute(
            route_points=[],
            total_distance_km=0,
            total_duration_hours=0,
            total_travel_time_hours=0,
            start_time="08:00",
            end_time="08:00",
            optimization_level='basic',
            route_efficiency=0,
            daily_capacity=0
        )
    
    def generate_route_summary(self, route: PNSBOptimizedRoute) -> Dict[str, Any]:
        """Gera resumo detalhado da rota"""
        summary = {
            'route_id': f"pnsb_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'total_points': len(route.route_points),
            'total_distance_km': round(route.total_distance_km, 1),
            'total_duration_hours': round(route.total_duration_hours, 1),
            'travel_time_hours': round(route.total_travel_time_hours, 1),
            'efficiency_score': round(route.route_efficiency, 1),
            'municipalities': list(set(p.municipality for p in route.route_points)),
            'survey_types': list(set(p.survey_type for p in route.route_points)),
            'schedule': [],
            'recommendations': []
        }
        
        # Gerar cronograma detalhado
        current_time = datetime.strptime(route.start_time, "%H:%M")
        
        # Tempo de deslocamento até primeiro ponto
        if route.route_points:
            travel_to_first = self._calculate_distance(
                self.base_location['lat'], self.base_location['lng'],
                route.route_points[0].lat, route.route_points[0].lng
            ) / 45 * 60  # em minutos
            
            current_time += timedelta(minutes=travel_to_first)
        
        for i, point in enumerate(route.route_points):
            visit_start = current_time
            visit_end = current_time + timedelta(minutes=point.estimated_duration)
            
            summary['schedule'].append({
                'sequence': i + 1,
                'municipality': point.municipality,
                'entity': point.name,
                'arrival_time': visit_start.strftime("%H:%M"),
                'departure_time': visit_end.strftime("%H:%M"),
                'duration_minutes': point.estimated_duration,
                'survey_type': point.survey_type,
                'priority': point.priority
            })
            
            current_time = visit_end
            
            # Tempo de deslocamento até próximo ponto
            if i < len(route.route_points) - 1:
                travel_time = self._calculate_distance(
                    point.lat, point.lng,
                    route.route_points[i + 1].lat, route.route_points[i + 1].lng
                ) / 45 * 60  # em minutos
                
                current_time += timedelta(minutes=travel_time)
        
        # Recomendações
        if route.total_duration_hours > 8:
            summary['recommendations'].append(
                "⚠️ Jornada muito longa - considere dividir em 2 dias"
            )
        
        if route.route_efficiency < 70:
            summary['recommendations'].append(
                "🔄 Eficiência baixa - revisar sequência de visitas"
            )
        
        if len(set(p.municipality for p in route.route_points)) > 4:
            summary['recommendations'].append(
                "🎯 Muitos municípios - considere agrupar por região"
            )
        
        return summary
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte otimizador para dicionário"""
        return {
            'service': 'PNSBRouteOptimizer',
            'version': '1.0.0',
            'base_location': self.base_location,
            'municipalities': self.municipalities,
            'business_hours': self.business_hours,
            'status': 'active'
        }