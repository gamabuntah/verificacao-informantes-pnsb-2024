"""
Serviço de Otimização de Rotas para PNSB 2024
Algoritmos avançados para otimização multi-stop e planejamento inteligente de jornadas
"""

import math
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app
import logging
import json
import itertools
from dataclasses import dataclass

from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF
from gestao_visitas.services.offline_maps_service import OfflineMapsService


@dataclass
class RoutePoint:
    """Representa um ponto na rota"""
    id: str
    name: str
    lat: float
    lng: float
    municipality: str
    priority: int
    estimated_duration: int = 60  # minutos
    time_window_start: Optional[str] = None
    time_window_end: Optional[str] = None
    visit_type: str = "standard"  # standard, priority, follow_up
    requirements: List[str] = None
    
    def __post_init__(self):
        if self.requirements is None:
            self.requirements = []


@dataclass
class OptimizedRoute:
    """Resultado de uma rota otimizada"""
    points: List[RoutePoint]
    total_distance_km: float
    total_duration_minutes: int
    total_driving_time_minutes: int
    optimization_score: float
    route_type: str
    created_at: datetime
    metadata: Dict[str, Any]


class RouteOptimizer:
    """Serviço avançado de otimização de rotas para pesquisa PNSB"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.offline_maps = OfflineMapsService()
        
        # PONTO DE PARTIDA FIXO: Agência IBGE Itajaí
        self.starting_point = {
            'name': 'Agência IBGE Itajaí',
            'address': 'Rua Camboriú, 26, Centro, Itajaí - SC',
            'lat': -26.9077,
            'lng': -48.6618,
            'municipality': 'Itajaí',
            'type': 'base_operacional'
        }
        
        # Configurações de otimização
        self.max_points_per_route = 8  # Máximo de pontos por dia
        self.max_daily_hours = 8  # Horas máximas de trabalho por dia
        self.lunch_break_duration = 60  # Pausa para almoço em minutos
        self.travel_buffer_factor = 1.2  # Buffer para imprevistos (20%)
        
        # Pesos para função objetivo
        self.weights = {
            'distance': 0.4,        # Minimizar distância total
            'time': 0.3,           # Minimizar tempo total
            'priority': 0.2,       # Priorizar entidades P1
            'efficiency': 0.1      # Maximizar eficiência geral
        }
        
        # Google Maps integration
        self.google_maps_client = None
        self._init_google_maps()
    
    def _init_google_maps(self):
        """Inicializar cliente do Google Maps se chave disponível"""
        try:
            api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
            if not api_key:
                self.logger.warning("⚠️ Google Maps API key não encontrada no config")
                return
                
            # Verificar se a chave não está vazia ou é placeholder
            if len(api_key) < 20:
                self.logger.warning("⚠️ Google Maps API key parece inválida (muito curta)")
                return
                
            import googlemaps
            
            # Testar inicialização do client
            self.google_maps_client = googlemaps.Client(key=api_key)
            
            # Fazer teste básico de conectividade
            try:
                # Teste simples de geocoding para verificar se a chave é válida
                test_result = self.google_maps_client.geocode("Itajaí, SC, Brazil")
                if test_result:
                    self.logger.info("🗺️ Google Maps API inicializada e testada com sucesso")
                else:
                    self.logger.warning("⚠️ Google Maps API inicializada mas teste retornou resultado vazio")
            except Exception as test_error:
                self.logger.error(f"❌ Google Maps API key inválida ou sem quota: {test_error}")
                self.google_maps_client = None
                
        except ImportError:
            self.logger.warning("⚠️ googlemaps package não instalado")
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Google Maps: {e}")
            self.google_maps_client = None
    
    def is_google_maps_available(self) -> bool:
        """Verificar se Google Maps está disponível"""
        return self.google_maps_client is not None
    
    def optimize_route_with_google_maps(self, points: List[RoutePoint], 
                                      target_date: str = None,
                                      start_time: str = "08:00",
                                      end_time: str = "18:00",
                                      include_business_hours: bool = True) -> Dict[str, Any]:
        """Otimizar rota usando Google Maps API - Nível 2/3"""
        try:
            if not self.is_google_maps_available():
                return {
                    'sucesso': False,
                    'erro': 'Google Maps API não disponível',
                    'fallback_to_level1': True
                }
            
            nivel = 3 if include_business_hours else 2
            self.logger.info(f"🗺️ Iniciando otimização Nível {nivel} com {len(points)} pontos")
            
            # NÍVEL 3: Buscar horários reais das entidades
            if include_business_hours:
                self.logger.info("🕰️ Buscando horários de atendimento reais...")
                try:
                    points = self._enrich_points_with_business_hours(points, target_date)
                except Exception as e:
                    self.logger.warning(f"⚠️ Falha ao obter horários reais: {e}. Continuando sem horários.")
            
            # Preparar coordenadas para Google Maps
            coords = self._prepare_coordinates_for_google_maps(points)
            
            # CORREÇÃO: Incluir IBGE na matriz para calcular ida e volta
            # Criar ponto IBGE
            ibge_point = RoutePoint(
                id='IBGE',
                name=self.starting_point['name'],
                lat=self.starting_point['lat'],
                lng=self.starting_point['lng'],
                municipality=self.starting_point['municipality'],
                priority=0,
                estimated_duration=0
            )
            
            # Criar lista com IBGE + visitas
            points_with_base = [ibge_point] + points
            coords_with_base = coords.copy()
            coords_with_base[self.starting_point['municipality']] = (self.starting_point['lat'], self.starting_point['lng'])
            
            # Obter matriz de distâncias/tempo do Google Maps (agora 4x4)
            distance_matrix = self._get_google_distance_matrix(points_with_base, coords_with_base, target_date)
            
            if not distance_matrix:
                return {
                    'sucesso': False,
                    'erro': 'Falha ao obter dados do Google Maps',
                    'fallback_to_level1': True
                }
            
            # Resolver TSP com dados reais e horários
            optimized_order = self._solve_tsp_with_google_data(points, distance_matrix, include_business_hours)
            
            # Construir rota otimizada
            optimized_points = [points[i] for i in optimized_order]
            
            # Calcular horários com dados do Google Maps e horários reais
            route_with_schedule = self._calculate_schedule_with_google_data_v1(
                optimized_points, distance_matrix, start_time, end_time, include_business_hours
            )
            
            # Obter direções detalhadas
            self.logger.info(f"🔍 COMPARAÇÃO DE PONTOS:")
            self.logger.info(f"   optimized_points: {[p.municipality for p in optimized_points]}")
            self.logger.info(f"   route_with_schedule: {[item.get('municipio', item.get('municipality', 'UNKNOWN')) for item in route_with_schedule]}")
            detailed_directions = self._get_detailed_directions(optimized_points, coords)
            
            # Calcular estatísticas
            self.logger.debug(f"🔍 ANTES DAS STATS: schedule tem {len(route_with_schedule)} itens")
            for i, item in enumerate(route_with_schedule):
                if 'point' in item:
                    self.logger.debug(f"   Item {i}: ✅ TEM 'point' - {item['point'].name}")
                else:
                    self.logger.debug(f"   Item {i}: ❌ SEM 'point'")
            
            self.logger.info(f"🔍 CALCULANDO ESTATÍSTICAS com {len(route_with_schedule)} visitas")
            self.logger.info(f"🔍 MATRIX DISTANCES type: {type(distance_matrix.get('distances', 'N/A'))}")
            self.logger.info(f"🔍 MATRIX DURATIONS type: {type(distance_matrix.get('durations', 'N/A'))}")
            stats = self._calculate_google_route_statistics(route_with_schedule, distance_matrix)
            
            # Converter RoutePoint para dict para serialização JSON
            from dataclasses import asdict
            optimized_points_dict = [asdict(point) for point in optimized_points]
            
            result = {
                'sucesso': True,
                'rota_otimizada': optimized_points_dict,
                'rota_com_horarios': route_with_schedule,
                'estatisticas': stats,
                'direcoes_detalhadas': detailed_directions,
                'nivel': nivel,
                'fonte_dados': f'Google Maps API + Places API' if nivel == 3 else 'Google Maps API',
                'horarios_reais_incluidos': include_business_hours,
                'timestamp': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Otimização Nível {nivel} concluída com sucesso")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização Nível {nivel if 'nivel' in locals() else 2}: {str(e)}")
            return {
                'sucesso': False,
                'erro': str(e),
                'fallback_to_level1': True
            }
    
    def _prepare_coordinates_for_google_maps(self, points: List[RoutePoint]) -> Dict[str, Tuple[float, float]]:
        """Preparar coordenadas para uso com Google Maps, incluindo ponto de partida IBGE"""
        coords = {}
        
        # Adicionar ponto de partida IBGE
        coords['IBGE_START'] = (self.starting_point['lat'], self.starting_point['lng'])
        
        # Adicionar pontos das visitas
        for point in points:
            coords[point.id] = (point.lat, point.lng)
            
        return coords
    
    def _get_google_distance_matrix(self, points: List[RoutePoint], 
                                  coords: Dict[str, Tuple[float, float]], 
                                  target_date: str = None) -> Optional[Dict]:
        """Obter matriz de distâncias/tempo real do Google Maps"""
        try:
            if not self.google_maps_client:
                self.logger.error("❌ Google Maps client não inicializado")
                return None
            
            # Preparar origens (incluindo IBGE) e destinos (pontos das visitas)
            origins = [coords['IBGE_START']] + [coords.get(point.id, (point.lat, point.lng)) for point in points]
            destinations = [coords.get(point.id, (point.lat, point.lng)) for point in points] + [coords['IBGE_START']]
            
            self.logger.info(f"🗺️ Consultando matriz de distâncias: {len(origins)} origens, {len(destinations)} destinos")
            
            # Definir horário de partida
            departure_time = self._calculate_departure_time(target_date)
            self.logger.info(f"🕐 Horário de partida calculado: {departure_time}")
            
            # Verificar se há muitos pontos (limite da API: 25x25)
            if len(origins) > 25 or len(destinations) > 25:
                self.logger.warning(f"⚠️ Muitos pontos para Distance Matrix API: {len(origins)}x{len(destinations)}")
                return None
            
            # Fazer chamada para Distance Matrix API
            matrix_result = self.google_maps_client.distance_matrix(
                origins=origins,
                destinations=destinations,
                mode="driving",
                departure_time=departure_time,
                traffic_model="best_guess",
                units="metric"
            )
            
            self.logger.info(f"📊 Resposta da API: status={matrix_result.get('status', 'UNKNOWN')}")
            
            if matrix_result['status'] != 'OK':
                error_msg = matrix_result.get('error_message', 'Erro desconhecido')
                self.logger.error(f"❌ Google Maps API erro: {matrix_result['status']} - {error_msg}")
                return None
            
            # Processar resultado
            processed_matrix = self._process_google_matrix_result(matrix_result, points)
            self.logger.info("✅ Matriz de distâncias processada com sucesso")
            
            return processed_matrix
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter matriz do Google Maps: {str(e)}")
            import traceback
            self.logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _calculate_departure_time(self, target_date: str = None) -> datetime:
        """Calcular horário de partida para consulta de trânsito"""
        if target_date:
            try:
                # Tentar diferentes formatos de data
                if 'T' in target_date:
                    # Formato ISO completo
                    date_obj = datetime.fromisoformat(target_date)
                else:
                    # Formato YYYY-MM-DD
                    date_obj = datetime.strptime(target_date, '%Y-%m-%d')
                
                # Definir horário para 8:00 AM
                departure_time = date_obj.replace(hour=8, minute=0, second=0, microsecond=0)
                
                # Garantir que não é no passado
                now = datetime.now()
                if departure_time <= now:
                    # Se a data/hora é no passado, usar agora + 5 minutos
                    departure_time = now + timedelta(minutes=5)
                    self.logger.warning(f"⚠️ Data de partida ajustada para o futuro: {departure_time}")
                
                return departure_time
                
            except (ValueError, TypeError) as e:
                self.logger.warning(f"⚠️ Erro ao processar data '{target_date}': {e}")
        
        # Fallback para agora + 10 minutos (garantir futuro)
        now = datetime.now()
        departure_time = now + timedelta(minutes=10)
        self.logger.info(f"🕐 Usando horário de partida padrão: {departure_time}")
        return departure_time
    
    def _process_google_matrix_result(self, matrix_result: Dict, points: List[RoutePoint]) -> Dict:
        """Processar resultado da Distance Matrix API"""
        processed = {
            'distances': {},
            'durations': {},
            'duration_in_traffic': {},
            'points': {i: point.id for i, point in enumerate(points)},
            'ibge_distances': {},
            'ibge_durations': {}
        }
        
        rows = matrix_result['rows']
        
        # Lista de IDs incluindo IBGE no início
        all_ids = ['IBGE_START'] + [point.id for point in points]
        
        for i, row in enumerate(rows):
            origin_id = all_ids[i]
            
            if origin_id not in processed['distances']:
                processed['distances'][origin_id] = {}
                processed['durations'][origin_id] = {}
                processed['duration_in_traffic'][origin_id] = {}
            
            for j, element in enumerate(row['elements']):
                # Destinos são todos os pontos das visitas + retorno para IBGE
                dest_ids = [point.id for point in points] + ['IBGE_START']
                dest_id = dest_ids[j] if j < len(dest_ids) else f'dest_{j}'
                
                if element['status'] == 'OK':
                    processed['distances'][origin_id][dest_id] = element['distance']['value']  # metros
                    processed['durations'][origin_id][dest_id] = element['duration']['value']  # segundos
                    
                    # Tempo com trânsito (se disponível)
                    if 'duration_in_traffic' in element:
                        processed['duration_in_traffic'][origin_id][dest_id] = element['duration_in_traffic']['value']
                    else:
                        processed['duration_in_traffic'][origin_id][dest_id] = element['duration']['value']
                        
                    # Armazenar dados específicos do IBGE para fácil acesso
                    if origin_id == 'IBGE_START':
                        processed['ibge_distances'][dest_id] = element['distance']['value']
                        processed['ibge_durations'][dest_id] = element['duration']['value']
                else:
                    # Usar dados padrão se API falhar
                    processed['distances'][origin_id][dest_id] = 999999  # Distância alta
                    processed['durations'][origin_id][dest_id] = 999999  # Tempo alto
                    processed['duration_in_traffic'][origin_id][dest_id] = 999999
        
        return processed
    
    def _solve_tsp_with_google_data(self, points: List[RoutePoint], 
                                  distance_matrix: Dict,
                                  consider_business_hours: bool = False) -> List[int]:
        """Resolver TSP usando dados reais do Google Maps e horários"""
        n = len(points)
        
        if n <= 1:
            return list(range(n))
        
        # Usar algoritmo de otimização baseado em tempo com trânsito e horários
        if n <= 8:
            return self._brute_force_tsp_google(points, distance_matrix, consider_business_hours)
        else:
            return self._genetic_algorithm_tsp_google(points, distance_matrix, consider_business_hours)
    
    def _brute_force_tsp_google(self, points: List[RoutePoint], 
                               distance_matrix: Dict,
                               consider_business_hours: bool = False) -> List[int]:
        """TSP por força bruta usando dados do Google Maps e horários"""
        from itertools import permutations
        
        n = len(points)
        best_route = None
        best_score = float('inf')
        
        # Ordenar por prioridade primeiro
        priority_order = sorted(range(n), key=lambda i: points[i].priority)
        
        # Tentar algumas permutações baseadas em prioridade
        for perm in permutations(priority_order):
            score = self._calculate_route_score_google(
                perm, points, distance_matrix, consider_business_hours
            )
            
            if score < best_score:
                best_score = score
                best_route = list(perm)
        
        return best_route or list(range(n))
    
    def _genetic_algorithm_tsp_google(self, points: List[RoutePoint], 
                                    distance_matrix: Dict,
                                    consider_business_hours: bool = False) -> List[int]:
        """Algoritmo genético para TSP com dados do Google Maps e horários"""
        n = len(points)
        population_size = min(50, n * 2)
        generations = 100
        
        # Gerar população inicial
        population = []
        for _ in range(population_size):
            route = list(range(n))
            np.random.shuffle(route)
            population.append(route)
        
        # Evoluir população
        for generation in range(generations):
            # Avaliar fitness
            fitness_scores = []
            for route in population:
                score = self._calculate_route_score_google(
                    route, points, distance_matrix, consider_business_hours
                )
                fitness_scores.append(1 / (1 + score))  # Inverter para maximizar
            
            # Seleção dos melhores
            sorted_indices = sorted(range(len(fitness_scores)), 
                                  key=lambda i: fitness_scores[i], reverse=True)
            
            # Manter melhores 50%
            elite_size = population_size // 2
            new_population = [population[i] for i in sorted_indices[:elite_size]]
            
            # Gerar descendentes
            while len(new_population) < population_size:
                parent1 = population[sorted_indices[np.random.randint(0, elite_size)]]
                parent2 = population[sorted_indices[np.random.randint(0, elite_size)]]
                child = self._crossover(parent1, parent2)
                child = self._mutate(child)
                new_population.append(child)
            
            population = new_population
        
        # Retornar melhor rota
        best_route = population[0]
        best_score = self._calculate_route_score_google(
            best_route, points, distance_matrix, consider_business_hours
        )
        
        for route in population[1:]:
            score = self._calculate_route_score_google(
                route, points, distance_matrix, consider_business_hours
            )
            if score < best_score:
                best_score = score
                best_route = route
        
        return best_route
    
    def _calculate_route_score_google(self, route: List[int], 
                                    points: List[RoutePoint], 
                                    distance_matrix: Dict,
                                    consider_business_hours: bool = False) -> float:
        """Calcular score da rota usando dados do Google Maps e horários"""
        total_time = 0
        total_distance = 0
        priority_penalty = 0
        business_hours_penalty = 0
        
        current_time_minutes = 8 * 60  # Começar às 8:00
        
        for i in range(len(route)):
            current_idx = route[i]
            current_point = points[current_idx]
            
            # Penálti por prioridade (P1 deve vir antes)
            priority_penalty += current_point.priority * i * 10
            
            # Penálti por horários de funcionamento (Nível 3)
            if consider_business_hours and hasattr(current_point, 'business_hours'):
                business_penalty = self._calculate_business_hours_penalty(
                    current_point, current_time_minutes
                )
                business_hours_penalty += business_penalty
            
            # Tempo de visita
            current_time_minutes += current_point.estimated_duration
            
            if i < len(route) - 1:
                next_idx = route[i + 1]
                current_id = points[current_idx].id
                next_id = points[next_idx].id
                
                # Usar tempo com trânsito se disponível
                if (current_id in distance_matrix.get('duration_in_traffic', {}) and 
                    next_id in distance_matrix['duration_in_traffic'][current_id]):
                    travel_time = distance_matrix['duration_in_traffic'][current_id][next_id] / 60  # minutos
                    distance = distance_matrix['distances'][current_id][next_id] / 1000  # km
                elif (current_id in distance_matrix.get('durations', {}) and 
                      next_id in distance_matrix['durations'][current_id]):
                    travel_time = distance_matrix['durations'][current_id][next_id] / 60  # minutos
                    distance = distance_matrix['distances'][current_id][next_id] / 1000  # km
                else:
                    travel_time = 999  # Penálti alto
                    distance = 999
                
                total_time += travel_time
                total_distance += distance
                current_time_minutes += travel_time + 15  # buffer
        
        # Combinar métricas com pesos
        score = (
            self.weights['time'] * total_time +
            self.weights['distance'] * total_distance +
            self.weights['priority'] * priority_penalty +
            (0.1 * business_hours_penalty if consider_business_hours else 0)
        )
        
        return score
    
    def _calculate_business_hours_penalty(self, point: RoutePoint, 
                                        visit_time_minutes: int) -> float:
        """Calcular penálti por visita fora do horário de funcionamento"""
        if not hasattr(point, 'business_hours') or not point.business_hours:
            return 0
        
        try:
            business_hours = point.business_hours
            
            # Se tem horários específicos do Google
            if 'today_open' in business_hours and 'today_close' in business_hours:
                if not business_hours.get('is_open_target_day', True):
                    return 1000  # Penálti alto por estar fechado
                
                open_minutes = self._time_to_minutes(business_hours['today_open'])
                close_minutes = self._time_to_minutes(business_hours['today_close'])
                
                # Penálti por visita antes da abertura
                if visit_time_minutes < open_minutes:
                    return (open_minutes - visit_time_minutes) * 2
                
                # Penálti por visita próxima ao fechamento
                if visit_time_minutes > close_minutes - point.estimated_duration:
                    return (visit_time_minutes - (close_minutes - point.estimated_duration)) * 3
            
            # Se tem horários padrão
            elif 'monday_friday' in business_hours:
                open_time = business_hours['monday_friday']['open']
                close_time = business_hours['monday_friday']['close']
                
                open_minutes = self._time_to_minutes(open_time)
                close_minutes = self._time_to_minutes(close_time)
                
                if visit_time_minutes < open_minutes:
                    return (open_minutes - visit_time_minutes) * 2
                
                if visit_time_minutes > close_minutes - point.estimated_duration:
                    return (visit_time_minutes - (close_minutes - point.estimated_duration)) * 3
            
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular penálti de horários: {str(e)}")
            return 0
    
    def _crossover(self, parent1: List[int], parent2: List[int]) -> List[int]:
        """Crossover para algoritmo genético"""
        size = len(parent1)
        start, end = sorted(np.random.choice(range(size), 2, replace=False))
        
        child = [-1] * size
        child[start:end] = parent1[start:end]
        
        pointer = 0
        for item in parent2:
            if item not in child:
                while child[pointer] != -1:
                    pointer += 1
                child[pointer] = item
        
        return child
    
    def _mutate(self, route: List[int]) -> List[int]:
        """Mutação para algoritmo genético"""
        if np.random.random() < 0.1:  # 10% chance de mutação
            i, j = np.random.choice(range(len(route)), 2, replace=False)
            route[i], route[j] = route[j], route[i]
        return route
    
    def _calculate_schedule_with_google_data_v1(self, points: List[RoutePoint], 
                                           distance_matrix: Dict,
                                           start_time: str, end_time: str,
                                           consider_business_hours: bool = False) -> List[Dict]:
        """Calcular cronograma usando dados do Google Maps e horários reais"""
        schedule = []
        current_time_minutes = self._time_to_minutes(start_time)
        
        for i, point in enumerate(points):
            # Verificar se o ponto está aberto no horário planejado
            if consider_business_hours and hasattr(point, 'business_hours'):
                adjusted_time = self._adjust_time_for_business_hours(current_time_minutes, point)
                if adjusted_time != current_time_minutes:
                    current_time_minutes = adjusted_time
            
            # Calcular tempo de chegada
            arrival_time = self._minutes_to_time(current_time_minutes)
            
            # Tempo da visita
            visit_duration = point.estimated_duration
            departure_time = self._minutes_to_time(current_time_minutes + visit_duration)
            
            # Obter informações de tráfego
            traffic_info = self._get_traffic_info_for_time(current_time_minutes)
            
            # Informações de horário de funcionamento
            business_info = self._get_business_hours_info(point) if consider_business_hours else None
            
            schedule_item = {
                'id': point.id,
                'name': point.name,
                'municipio': point.municipality,
                'prioridade': f"P{point.priority}",
                'hora': arrival_time,
                'horaSugerida': arrival_time,
                'tempo_visita': visit_duration,
                'duracao_minutos': visit_duration,  # Para compatibilidade com statistics
                'horario_saida': departure_time,
                'trafegoInfo': traffic_info,
                'businessHoursInfo': business_info,
                'tempoDeslocamento': 0,
                'point': point  # Adicionar o objeto RoutePoint para cálculos de distância
            }
            
            # Calcular tempo de deslocamento para próximo ponto
            if i < len(points) - 1:
                next_point = points[i + 1]
                travel_time = self._get_travel_time_google(point, next_point, distance_matrix)
                schedule_item['tempoDeslocamento'] = travel_time
                schedule_item['tempo_viagem_proxima'] = travel_time  # Para compatibilidade com statistics
                
                # Avançar tempo
                current_time_minutes += visit_duration + travel_time + 15  # buffer
                
                # Considerar pausa para almoço
                if 12 * 60 <= current_time_minutes < 13 * 60:
                    current_time_minutes = 13 * 60  # Pular para 13:00
            
            schedule.append(schedule_item)
        
        return schedule
    
    def _get_travel_time_google(self, origin: RoutePoint, destination: RoutePoint, 
                               distance_matrix: Dict) -> int:
        """Obter tempo de viagem usando dados do Google Maps"""
        try:
            traffic_time = distance_matrix['duration_in_traffic'][origin.id][destination.id]
            return max(1, traffic_time // 60)  # Converter para minutos
        except KeyError:
            return 30  # Fallback padrão
    
    def _get_traffic_info_for_time(self, time_minutes: int) -> str:
        """Obter informações de tráfego para horário específico"""
        hour = time_minutes // 60
        
        if 7 <= hour <= 9:
            return "Trânsito Pesado (Rush Matinal)"
        elif 11 <= hour <= 13:
            return "Trânsito Moderado (Almoço)"
        elif 17 <= hour <= 19:
            return "Trânsito Pesado (Rush Vespertino)"
        elif 10 <= hour <= 16:
            return "Trânsito Leve"
        else:
            return "Trânsito Livre"
    
    def _calculate_google_route_statistics(self, schedule: List[Dict], 
                                         distance_matrix: Dict) -> Dict:
        """Calcular estatísticas da rota usando dados do Google Maps"""
        total_distance = 0
        total_travel_time = 0
        total_visit_time = 0
        
        # VERSÃO CORRIGIDA: Usar apenas estrutura de dicionário (consistente com _process_google_matrix_result)
        if distance_matrix and 'distances' in distance_matrix:
            try:
                matrix_distances = distance_matrix['distances']
                matrix_durations = distance_matrix.get('durations', {})
                
                self.logger.info(f"🔍 CALCULANDO ESTATÍSTICAS: {len(schedule)} visitas")
                self.logger.info(f"🔍 Matrix distances type: {type(matrix_distances)}")
                
                # Verificar se é dicionário (estrutura correta) ou lista (fallback)
                if isinstance(matrix_distances, dict):
                    # 1. VIAGEM INICIAL: IBGE → Primeira visita
                    if 'IBGE_START' in matrix_distances and len(schedule) > 0:
                        first_visit_id = schedule[0].get('id', f"visita_{schedule[0].get('nome', 'sem_nome')}")
                        if first_visit_id in matrix_distances['IBGE_START']:
                            ida_distance = matrix_distances['IBGE_START'][first_visit_id]
                            total_distance += ida_distance / 1000
                            self.logger.info(f"✅ IDA: IBGE → {first_visit_id}: {ida_distance/1000:.2f}km")
                            
                            # Tempo de ida
                            if isinstance(matrix_durations, dict) and 'IBGE_START' in matrix_durations:
                                ida_time = matrix_durations['IBGE_START'].get(first_visit_id, 0)
                                total_travel_time += ida_time / 60
                                self.logger.info(f"✅ TEMPO IDA: {ida_time/60:.1f}min")
                    
                    # 2. VIAGENS ENTRE VISITAS
                    for i in range(len(schedule) - 1):
                        current_id = schedule[i].get('id', f"visita_{schedule[i].get('nome', 'sem_nome')}")
                        next_id = schedule[i + 1].get('id', f"visita_{schedule[i + 1].get('nome', 'sem_nome')}")
                        
                        if current_id in matrix_distances and next_id in matrix_distances[current_id]:
                            distance_meters = matrix_distances[current_id][next_id]
                            total_distance += distance_meters / 1000
                            self.logger.info(f"✅ ENTRE VISITAS: {current_id} → {next_id}: {distance_meters/1000:.2f}km")
                            
                            # Tempo entre visitas
                            if isinstance(matrix_durations, dict) and current_id in matrix_durations:
                                travel_seconds = matrix_durations[current_id].get(next_id, 0)
                                total_travel_time += travel_seconds / 60
                                self.logger.info(f"✅ TEMPO ENTRE VISITAS: {travel_seconds/60:.1f}min")
                    
                    # 3. VIAGEM DE RETORNO: Última visita → IBGE
                    if len(schedule) > 0:
                        last_visit_id = schedule[-1].get('id', f"visita_{schedule[-1].get('nome', 'sem_nome')}")
                        if last_visit_id in matrix_distances and 'IBGE_START' in matrix_distances[last_visit_id]:
                            volta_distance = matrix_distances[last_visit_id]['IBGE_START']
                            total_distance += volta_distance / 1000
                            self.logger.info(f"✅ VOLTA: {last_visit_id} → IBGE: {volta_distance/1000:.2f}km")
                            
                            # Tempo de volta
                            if isinstance(matrix_durations, dict) and last_visit_id in matrix_durations:
                                volta_time = matrix_durations[last_visit_id].get('IBGE_START', 0)
                                total_travel_time += volta_time / 60
                                self.logger.info(f"✅ TEMPO VOLTA: {volta_time/60:.1f}min")
                    
                    self.logger.info(f"✅ DISTÂNCIA TOTAL GOOGLE MAPS: {total_distance:.2f}km")
                    self.logger.info(f"✅ TEMPO VIAGEM TOTAL GOOGLE MAPS: {total_travel_time:.1f}min")
                    
                elif isinstance(matrix_distances, list) and len(matrix_distances) > 0:
                    # FALLBACK: Matrix como lista (estrutura antiga)
                    self.logger.warning(f"⚠️ Matrix distances é lista, usando fallback: {len(matrix_distances)}x{len(matrix_distances[0]) if matrix_distances else 0}")
                    
                    # 1. VIAGEM INICIAL: IBGE → Primeira visita
                    if len(matrix_distances) > 0 and len(matrix_distances[0]) > 1:
                        ida_distance = matrix_distances[0][1]  # IBGE → Primeiro ponto
                        if isinstance(ida_distance, (int, float)) and ida_distance > 0:
                            total_distance += ida_distance / 1000
                            self.logger.info(f"✅ IDA (lista): IBGE → Primeira: {ida_distance/1000:.2f}km")
                    
                    # 2. VIAGENS ENTRE VISITAS
                    for i in range(1, len(schedule)):
                        if i < len(matrix_distances) and i+1 < len(matrix_distances[i]):
                            distance_meters = matrix_distances[i][i+1]
                            if isinstance(distance_meters, (int, float)) and distance_meters > 0:
                                total_distance += distance_meters / 1000
                                self.logger.info(f"✅ ENTRE VISITAS (lista): {i}→{i+1}: {distance_meters/1000:.2f}km")
                    
                    # 3. VIAGEM DE RETORNO: Última visita → IBGE
                    if len(schedule) > 0 and len(schedule) < len(matrix_distances):
                        volta_distance = matrix_distances[len(schedule)][0]
                        if isinstance(volta_distance, (int, float)) and volta_distance > 0:
                            total_distance += volta_distance / 1000
                            self.logger.info(f"✅ VOLTA (lista): Última → IBGE: {volta_distance/1000:.2f}km")
                    
                    # Calcular tempos (se disponível)
                    if isinstance(matrix_durations, list) and len(matrix_durations) > 0:
                        # Tempo de ida
                        if len(matrix_durations) > 0 and len(matrix_durations[0]) > 1:
                            ida_time = matrix_durations[0][1]
                            if isinstance(ida_time, (int, float)) and ida_time > 0:
                                total_travel_time += ida_time / 60
                        
                        # Tempos entre visitas
                        for i in range(1, len(schedule)):
                            if i < len(matrix_durations) and i+1 < len(matrix_durations[i]):
                                travel_seconds = matrix_durations[i][i+1]
                                if isinstance(travel_seconds, (int, float)) and travel_seconds > 0:
                                    total_travel_time += travel_seconds / 60
                        
                        # Tempo de volta
                        if len(schedule) > 0 and len(schedule) < len(matrix_durations):
                            volta_time = matrix_durations[len(schedule)][0]
                            if isinstance(volta_time, (int, float)) and volta_time > 0:
                                total_travel_time += volta_time / 60
                    
                    self.logger.info(f"✅ DISTÂNCIA TOTAL (fallback lista): {total_distance:.2f}km")
                    self.logger.info(f"✅ TEMPO VIAGEM TOTAL (fallback lista): {total_travel_time:.1f}min")
                    
                else:
                    self.logger.warning(f"⚠️ Matrix distances formato desconhecido: {type(matrix_distances)}")
                    
            except Exception as e:
                self.logger.error(f"❌ Erro ao calcular estatísticas do Google Maps: {e}")
                self.logger.error(f"❌ Fallback para cálculo estimado")
        
        # Adicionar tempo das visitas
        for item in schedule:
            visit_duration = item.get('duracao_minutos', item.get('tempo_visita', 90))
            total_visit_time += visit_duration
        
        # Se não conseguiu obter dados do Google Maps, usar estimativas
        if total_distance == 0 or total_travel_time == 0:
            self.logger.warning("⚠️ Dados do Google Maps não disponíveis, usando estimativas")
            
            # Fallback para estimativas baseadas em tempo de viagem
            for item in schedule:
                travel_time = item.get('tempo_viagem_proxima', item.get('tempoDeslocamento', 0))
                total_travel_time += travel_time
                
                # Estimativa de distância baseada no tempo (30 km/h médio)
                if travel_time > 0:
                    estimated_distance = travel_time * 0.5
                    total_distance += estimated_distance
        
        total_journey_time = total_travel_time + total_visit_time
        efficiency = round((total_visit_time / total_journey_time) * 100) if total_journey_time > 0 else 0
        
        return {
            'numeroVisitas': len(schedule),
            'distanciaTotal': round(total_distance, 2),
            'tempoTotalViagem': int(round(total_travel_time)),
            'tempoTotalVisitas': int(round(total_visit_time)),
            'tempoTotalJornada': int(round(total_journey_time)),
            'eficiencia': efficiency
        }
    
    def _get_detailed_directions(self, points: List[RoutePoint]) -> List[Dict]:
        """Obter direções detalhadas entre pontos"""
        directions = []
        
        for i in range(len(points) - 1):
            origin = points[i]
            destination = points[i + 1]
            
            try:
                result = self.google_maps_client.directions(
                    origin=(origin.lat, origin.lng),
                    destination=(destination.lat, destination.lng),
                    mode="driving",
                    departure_time=datetime.now()
                )
                
                if result:
                    route = result[0]
                    leg = route['legs'][0]
                    
                    direction_info = {
                        'de': origin.name,
                        'para': destination.name,
                        'distancia': leg['distance']['text'],
                        'duracao': leg['duration']['text'],
                        'passos': [step['html_instructions'] for step in leg['steps'][:3]]  # Top 3 steps
                    }
                    
                    directions.append(direction_info)
                
            except Exception as e:
                self.logger.error(f"Erro ao obter direções: {e}")
                directions.append({
                    'de': origin.name,
                    'para': destination.name,
                    'erro': 'Direções não disponíveis'
                })
        
        return directions
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Converter string de tempo para minutos"""
        try:
            hour, minute = map(int, time_str.split(':'))
            return hour * 60 + minute
        except (ValueError, AttributeError):
            return 8 * 60  # Padrão: 8:00
    
    def _minutes_to_time(self, minutes: int) -> str:
        """Converter minutos para string de tempo"""
        hour = minutes // 60
        minute = minutes % 60
        return f"{hour:02d}:{minute:02d}"
    
    def _enrich_points_with_business_hours(self, points: List[RoutePoint], 
                                               target_date: str = None) -> List[RoutePoint]:
        """Enriquecer pontos com horários reais usando Google Places API"""
        enriched_points = []
        
        for point in points:
            try:
                # Buscar informações do local
                place_info = self._search_place_by_name_and_location(point)
                
                if place_info and 'place_id' in place_info:
                    # Obter detalhes incluindo horários
                    place_details = self._get_place_details(place_info['place_id'])
                    
                    if place_details and 'opening_hours' in place_details:
                        # Adicionar horários ao ponto
                        point.business_hours = self._parse_opening_hours(
                            place_details['opening_hours'], target_date
                        )
                        point.place_id = place_info['place_id']
                        point.google_rating = place_details.get('rating')
                        point.google_address = place_details.get('formatted_address')
                        
                        self.logger.info(f"✅ Horários obtidos para {point.name}")
                    else:
                        # Usar horários padrão
                        point.business_hours = self._get_default_business_hours(point)
                        self.logger.warning(f"⚠️ Usando horários padrão para {point.name}")
                else:
                    # Usar horários padrão
                    point.business_hours = self._get_default_business_hours(point)
                    self.logger.warning(f"⚠️ Local não encontrado no Google: {point.name}")
                    
            except Exception as e:
                self.logger.error(f"❌ Erro ao buscar horários de {point.name}: {str(e)}")
                point.business_hours = self._get_default_business_hours(point)
            
            enriched_points.append(point)
        
        return enriched_points
    
    def _search_place_by_name_and_location(self, point: RoutePoint) -> Optional[Dict]:
        """Buscar local no Google Places por nome e localização"""
        try:
            # Construir query de busca
            query_terms = []
            
            # Adicionar termos baseados no tipo de entidade
            if 'prefeitura' in point.name.lower():
                query_terms.extend(['prefeitura', 'municipal', point.municipality])
            elif 'empresa' in point.visit_type.lower():
                query_terms.extend(['empresa', point.municipality])
            elif 'cooperativa' in point.visit_type.lower():
                query_terms.extend(['cooperativa', 'catadores', point.municipality])
            else:
                query_terms.extend([point.municipality])
            
            # Se temos nome específico, usar
            if hasattr(point, 'entity_name') and point.entity_name:
                query_terms.insert(0, point.entity_name)
            
            query = ' '.join(query_terms)
            
            # Buscar usando Places API Text Search
            places_result = self.google_maps_client.places(
                query=query,
                location=(point.lat, point.lng),
                radius=5000,  # 5km de raio
                language='pt-BR',
                region='br'
            )
            
            if places_result['status'] == 'OK' and places_result['results']:
                # Pegar o primeiro resultado mais relevante
                best_match = places_result['results'][0]
                
                # Verificar distância para garantir que é o local correto
                place_location = best_match['geometry']['location']
                distance = self._calculate_distance(
                    point.lat, point.lng,
                    place_location['lat'], place_location['lng']
                )
                
                # Se está dentro de 2km, consideramos uma boa correspondência
                if distance <= 2.0:
                    return {
                        'place_id': best_match['place_id'],
                        'name': best_match['name'],
                        'distance_km': distance,
                        'rating': best_match.get('rating'),
                        'types': best_match.get('types', [])
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erro na busca do local: {str(e)}")
            return None
    
    def _get_place_details(self, place_id: str) -> Optional[Dict]:
        """Obter detalhes completos do local incluindo horários"""
        try:
            details_result = self.google_maps_client.place(
                place_id=place_id,
                fields=[
                    'name', 'formatted_address', 'opening_hours',
                    'rating', 'types', 'website', 'formatted_phone_number'
                ],
                language='pt-BR'
            )
            
            if details_result['status'] == 'OK':
                return details_result['result']
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter detalhes do local: {str(e)}")
            return None
    
    def _parse_opening_hours(self, opening_hours: Dict, target_date: str = None) -> Dict:
        """Processar horários de funcionamento do Google Places"""
        try:
            parsed_hours = {
                'is_open_now': opening_hours.get('open_now', False),
                'periods': [],
                'weekday_text': opening_hours.get('weekday_text', []),
                'special_notes': []
            }
            
            # Processar períodos de funcionamento
            if 'periods' in opening_hours:
                for period in opening_hours['periods']:
                    if 'open' in period:
                        open_time = period['open']
                        close_time = period.get('close', {'day': open_time['day'], 'time': '2359'})
                        
                        parsed_hours['periods'].append({
                            'day': open_time['day'],  # 0=domingo, 1=segunda, etc.
                            'open': self._format_google_time(open_time['time']),
                            'close': self._format_google_time(close_time['time'])
                        })
            
            # Adicionar notas especiais
            if target_date:
                day_of_week = self._get_day_of_week_from_date(target_date)
                today_hours = self._get_hours_for_day(parsed_hours['periods'], day_of_week)
                
                if today_hours:
                    parsed_hours['today_open'] = today_hours['open']
                    parsed_hours['today_close'] = today_hours['close']
                    parsed_hours['is_open_target_day'] = True
                else:
                    parsed_hours['is_open_target_day'] = False
                    parsed_hours['special_notes'].append('Fechado no dia da visita')
            
            return parsed_hours
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar horários: {str(e)}")
            return self._get_default_business_hours_dict()
    
    def _format_google_time(self, time_str: str) -> str:
        """Converter formato de tempo do Google (ex: '0900') para 'HH:MM'"""
        if len(time_str) == 4:
            return f"{time_str[:2]}:{time_str[2:]}"
        return time_str
    
    def _get_day_of_week_from_date(self, date_str: str) -> int:
        """Obter dia da semana (0=domingo) a partir de string de data"""
        try:
            date_obj = datetime.fromisoformat(date_str.split('T')[0])
            # Converter para formato do Google (0=domingo)
            return (date_obj.weekday() + 1) % 7
        except:
            return datetime.now().weekday() + 1 % 7
    
    def _get_hours_for_day(self, periods: List[Dict], day: int) -> Optional[Dict]:
        """Obter horários para um dia específico"""
        for period in periods:
            if period['day'] == day:
                return period
        return None
    
    def _get_default_business_hours(self, point: RoutePoint) -> Dict:
        """Horários padrão baseados no tipo de entidade"""
        if 'prefeitura' in point.name.lower() or point.visit_type == 'prefeitura':
            return {
                'type': 'government',
                'monday_friday': {'open': '08:00', 'close': '17:00'},
                'saturday': {'open': '08:00', 'close': '12:00'},
                'sunday': 'closed',
                'lunch_break': {'start': '12:00', 'end': '13:00'},
                'notes': 'Horário padrão de prefeitura'
            }
        elif 'empresa' in point.visit_type.lower():
            return {
                'type': 'business',
                'monday_friday': {'open': '08:00', 'close': '18:00'},
                'saturday': {'open': '08:00', 'close': '12:00'},
                'sunday': 'closed',
                'lunch_break': {'start': '12:00', 'end': '13:00'},
                'notes': 'Horário comercial padrão'
            }
        else:
            return {
                'type': 'flexible',
                'monday_friday': {'open': '08:00', 'close': '17:00'},
                'saturday': {'open': '08:00', 'close': '12:00'},
                'sunday': 'closed',
                'notes': 'Horário estimado - confirmar com entidade'
            }
    
    def _get_default_business_hours_dict(self) -> Dict:
        """Horários padrão genéricos"""
        return {
            'is_open_now': True,
            'periods': [
                {'day': 1, 'open': '08:00', 'close': '17:00'},  # Segunda
                {'day': 2, 'open': '08:00', 'close': '17:00'},  # Terça
                {'day': 3, 'open': '08:00', 'close': '17:00'},  # Quarta
                {'day': 4, 'open': '08:00', 'close': '17:00'},  # Quinta
                {'day': 5, 'open': '08:00', 'close': '17:00'},  # Sexta
            ],
            'weekday_text': ['Seg-Sex: 08:00-17:00'],
            'is_open_target_day': True,
            'today_open': '08:00',
            'today_close': '17:00'
        }
    
    def _adjust_time_for_business_hours(self, current_time_minutes: int, 
                                      point: RoutePoint) -> int:
        """Ajustar horário de visita baseado no funcionamento real"""
        if not hasattr(point, 'business_hours') or not point.business_hours:
            return current_time_minutes
        
        try:
            business_hours = point.business_hours
            
            # Se tem horários do Google Places
            if 'today_open' in business_hours and 'today_close' in business_hours:
                open_minutes = self._time_to_minutes(business_hours['today_open'])
                close_minutes = self._time_to_minutes(business_hours['today_close'])
                
                # Se estamos antes da abertura, ajustar para horário de abertura
                if current_time_minutes < open_minutes:
                    self.logger.info(f"🕰️ Ajustando visita para abertura: {business_hours['today_open']}")
                    return open_minutes
                
                # Se estamos muito próximos do fechamento, antecipar
                if current_time_minutes > close_minutes - point.estimated_duration:
                    # Tentar agendar para antes do fechamento
                    preferred_time = close_minutes - point.estimated_duration - 30  # 30min buffer
                    if preferred_time >= open_minutes:
                        self.logger.info(f"🕰️ Antecipando visita devido ao horário de fechamento")
                        return preferred_time
            
            # Se tem horários padrão (formato antigo)
            elif 'monday_friday' in business_hours:
                open_time = business_hours['monday_friday']['open']
                close_time = business_hours['monday_friday']['close']
                
                open_minutes = self._time_to_minutes(open_time)
                close_minutes = self._time_to_minutes(close_time)
                
                if current_time_minutes < open_minutes:
                    return open_minutes
                
                if current_time_minutes > close_minutes - point.estimated_duration:
                    preferred_time = close_minutes - point.estimated_duration - 30
                    if preferred_time >= open_minutes:
                        return preferred_time
            
            return current_time_minutes
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao ajustar horários: {str(e)}")
            return current_time_minutes
    
    def _get_business_hours_info(self, point: RoutePoint) -> Optional[str]:
        """Obter informações de horário para exibição"""
        if not hasattr(point, 'business_hours') or not point.business_hours:
            return None
        
        try:
            business_hours = point.business_hours
            
            if 'today_open' in business_hours and 'today_close' in business_hours:
                status = "Aberto" if business_hours.get('is_open_target_day', True) else "Fechado"
                hours = f"{business_hours['today_open']}-{business_hours['today_close']}"
                
                # Determinar fonte dos dados com mais precisão
                if 'weekday_text' in business_hours or 'periods' in business_hours:
                    source = "Google Places"
                elif business_hours.get('source') == 'Fallback Genérico (VERIFICAR HORÁRIOS REAIS!)':
                    source = "⚠️ VERIFICAR"
                    if 'warning' in business_hours:
                        return f"{status}: {hours} ({source} - {business_hours['warning']})"
                elif 'Fallback' in business_hours.get('source', ''):
                    source = "Estimado"
                else:
                    source = "Padrão"
                
                return f"{status}: {hours} ({source})"
            
            elif 'monday_friday' in business_hours:
                hours = business_hours['monday_friday']
                return f"Comercial: {hours['open']}-{hours['close']} (Padrão)"
            
            return "Horários não disponíveis"
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao formatar informações de horário: {str(e)}")
            return "Erro ao obter horários"
    
    def _calculate_distance(self, lat1: float, lng1: float, 
                          lat2: float, lng2: float) -> float:
        """Calcular distância entre dois pontos em km"""
        import math
        
        R = 6371  # Raio da Terra em km
        dLat = math.radians(lat2 - lat1)
        dLng = math.radians(lng2 - lng1)
        
        a = (math.sin(dLat/2) * math.sin(dLat/2) + 
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
             math.sin(dLng/2) * math.sin(dLng/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def optimize_daily_route(self, points: List[RoutePoint], 
                           start_location: Tuple[float, float] = None,
                           optimization_type: str = "balanced") -> OptimizedRoute:
        """
        Otimiza uma rota para um dia específico
        
        Args:
            points: Lista de pontos a serem visitados
            start_location: Localização de início (lat, lng)
            optimization_type: Tipo de otimização (distance, time, priority, balanced)
            
        Returns:
            Rota otimizada
        """
        try:
            self.logger.info(f"🗺️ Otimizando rota diária com {len(points)} pontos")
            
            if len(points) == 0:
                return self._create_empty_route()
            
            if len(points) == 1:
                return self._create_single_point_route(points[0])
            
            # Ajustar pesos baseado no tipo de otimização
            self._adjust_weights(optimization_type)
            
            # Calcular matriz de distâncias
            distance_matrix = self._calculate_distance_matrix(points, start_location)
            
            # Executar algoritmo de otimização
            if len(points) <= 8:
                # Para rotas pequenas, usar força bruta otimizada
                optimized_order = self._optimize_small_route(points, distance_matrix)
            else:
                # Para rotas maiores, usar algoritmo genético
                optimized_order = self._optimize_large_route(points, distance_matrix)
            
            # Construir rota otimizada
            optimized_points = [points[i] for i in optimized_order]
            
            # Calcular métricas da rota
            total_distance, total_time, driving_time = self._calculate_route_metrics(
                optimized_points, distance_matrix, optimized_order
            )
            
            # Calcular score de otimização
            optimization_score = self._calculate_optimization_score(
                optimized_points, total_distance, total_time, driving_time
            )
            
            result = OptimizedRoute(
                points=optimized_points,
                total_distance_km=round(total_distance / 1000, 2),
                total_duration_minutes=total_time,
                total_driving_time_minutes=driving_time,
                optimization_score=optimization_score,
                route_type=optimization_type,
                created_at=datetime.now(),
                metadata={
                    'algorithm': 'tsp_optimization' if len(points) <= 8 else 'genetic_algorithm',
                    'points_count': len(points),
                    'optimization_weights': self.weights.copy(),
                    'constraints_applied': self._get_applied_constraints(points)
                }
            )
            
            self.logger.info(f"✅ Rota otimizada: {len(optimized_points)} pontos, "
                           f"{result.total_distance_km}km, {result.total_duration_minutes}min")
            
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização de rota: {str(e)}")
            return self._create_fallback_route(points)
    
    def optimize_weekly_plan(self, points: List[RoutePoint], 
                           start_date: datetime,
                           working_days: int = 5) -> List[OptimizedRoute]:
        """
        Otimiza um plano semanal dividindo pontos em múltiplos dias
        
        Args:
            points: Lista de pontos para a semana
            start_date: Data de início da semana
            working_days: Número de dias úteis
            
        Returns:
            Lista de rotas otimizadas por dia
        """
        try:
            self.logger.info(f"📅 Otimizando plano semanal: {len(points)} pontos em {working_days} dias")
            
            if not points:
                return []
            
            # Agrupar pontos por prioridade e proximidade
            daily_groups = self._distribute_points_across_days(points, working_days)
            
            weekly_routes = []
            current_date = start_date
            
            for day_idx, day_points in enumerate(daily_groups):
                if not day_points:
                    continue
                
                # Otimizar rota do dia
                daily_route = self.optimize_daily_route(
                    day_points, 
                    optimization_type="balanced"
                )
                
                # Adicionar metadados do dia
                daily_route.metadata.update({
                    'day_of_week': day_idx + 1,
                    'planned_date': current_date.isoformat(),
                    'is_part_of_weekly_plan': True
                })
                
                weekly_routes.append(daily_route)
                current_date += timedelta(days=1)
            
            # Aplicar otimizações entre dias
            weekly_routes = self._optimize_inter_day_transitions(weekly_routes)
            
            self.logger.info(f"✅ Plano semanal otimizado: {len(weekly_routes)} dias")
            
            return weekly_routes
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização semanal: {str(e)}")
            return []
    
    def suggest_optimal_start_time(self, route: OptimizedRoute, 
                                 target_end_time: str = "17:00") -> Dict[str, str]:
        """
        Sugere horário ideal de início baseado na rota otimizada
        
        Args:
            route: Rota otimizada
            target_end_time: Horário desejado de término
            
        Returns:
            Dicionário com horários sugeridos
        """
        try:
            # Converter horário alvo para minutos
            target_hour, target_min = map(int, target_end_time.split(':'))
            target_minutes = target_hour * 60 + target_min
            
            # Calcular tempo total necessário (incluindo buffer)
            total_time_needed = route.total_duration_minutes * self.travel_buffer_factor
            total_time_needed += self.lunch_break_duration  # Adicionar pausa
            
            # Calcular horário de início ideal
            start_minutes = target_minutes - total_time_needed
            
            # Ajustar para horário comercial (não antes das 8h)
            min_start_minutes = 8 * 60  # 8:00
            if start_minutes < min_start_minutes:
                start_minutes = min_start_minutes
            
            # Converter de volta para formato de horas
            start_hour = int(start_minutes // 60)
            start_min = int(start_minutes % 60)
            
            # Calcular horários de cada ponto
            point_schedule = self._calculate_point_schedule(route, start_hour, start_min)
            
            return {
                'recommended_start': f"{start_hour:02d}:{start_min:02d}",
                'estimated_end': target_end_time,
                'total_duration_hours': round(total_time_needed / 60, 1),
                'includes_lunch_break': True,
                'point_schedule': point_schedule,
                'optimization_notes': self._generate_schedule_notes(route)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular horários: {str(e)}")
            return {
                'recommended_start': "08:00",
                'estimated_end': "17:00",
                'error': str(e)
            }
    
    def get_alternative_routes(self, points: List[RoutePoint], 
                             count: int = 3) -> List[OptimizedRoute]:
        """
        Gera múltiplas alternativas de rota com diferentes critérios
        
        Args:
            points: Pontos a serem visitados
            count: Número de alternativas
            
        Returns:
            Lista de rotas alternativas
        """
        try:
            optimization_types = ["distance", "time", "priority", "balanced"]
            alternatives = []
            
            for opt_type in optimization_types[:count]:
                route = self.optimize_daily_route(points, optimization_type=opt_type)
                route.route_type = f"alternative_{opt_type}"
                alternatives.append(route)
            
            # Ordenar por score de otimização
            alternatives.sort(key=lambda r: r.optimization_score, reverse=True)
            
            return alternatives[:count]
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar alternativas: {str(e)}")
            return []
    
    def analyze_route_efficiency(self, route: OptimizedRoute) -> Dict[str, Any]:
        """
        Analisa a eficiência de uma rota otimizada
        
        Args:
            route: Rota a ser analisada
            
        Returns:
            Análise detalhada da eficiência
        """
        try:
            # Métricas básicas
            avg_distance_between_points = route.total_distance_km / max(len(route.points) - 1, 1)
            efficiency_score = route.optimization_score
            
            # Análise temporal
            work_time_ratio = (route.total_duration_minutes - route.total_driving_time_minutes) / route.total_duration_minutes
            
            # Análise geográfica
            geographic_spread = self._calculate_geographic_spread(route.points)
            
            # Sugestões de melhoria
            suggestions = self._generate_efficiency_suggestions(route)
            
            return {
                'efficiency_metrics': {
                    'overall_score': round(efficiency_score, 2),
                    'avg_distance_km': round(avg_distance_between_points, 2),
                    'work_time_ratio': round(work_time_ratio, 2),
                    'geographic_spread_km': round(geographic_spread, 2),
                    'points_per_hour': round(len(route.points) / (route.total_duration_minutes / 60), 1)
                },
                'time_analysis': {
                    'total_duration_hours': round(route.total_duration_minutes / 60, 1),
                    'driving_time_hours': round(route.total_driving_time_minutes / 60, 1),
                    'work_time_hours': round((route.total_duration_minutes - route.total_driving_time_minutes) / 60, 1),
                    'estimated_breaks_minutes': 60  # Lunch break
                },
                'geographic_analysis': {
                    'municipalities_covered': len(set(p.municipality for p in route.points)),
                    'priority_points': len([p for p in route.points if p.priority == 1]),
                    'route_compactness': self._calculate_route_compactness(route.points)
                },
                'suggestions': suggestions,
                'optimization_potential': self._assess_optimization_potential(route)
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de eficiência: {str(e)}")
            return {'error': str(e)}
    
    def load_entities_as_route_points(self, municipality: str = None) -> List[RoutePoint]:
        """
        Carrega entidades do banco como pontos de rota
        
        Args:
            municipality: Filtrar por município específico
            
        Returns:
            Lista de pontos de rota
        """
        try:
            points = []
            
            # Carregar entidades identificadas
            query_identificadas = EntidadeIdentificada.query.filter_by(geocodificacao_status='sucesso')
            if municipality:
                query_identificadas = query_identificadas.filter_by(municipio=municipality)
            
            for entity in query_identificadas.all():
                if entity.latitude and entity.longitude:
                    requirements = []
                    if entity.mrs_obrigatorio:
                        requirements.append('MRS')
                    if entity.map_obrigatorio:
                        requirements.append('MAP')
                    
                    point = RoutePoint(
                        id=f"identificada_{entity.id}",
                        name=entity.nome_entidade,
                        lat=entity.latitude,
                        lng=entity.longitude,
                        municipality=entity.municipio,
                        priority=entity.prioridade or 2,
                        estimated_duration=90 if len(requirements) > 1 else 60,
                        visit_type="standard",
                        requirements=requirements
                    )
                    points.append(point)
            
            # Carregar entidades prioritárias
            query_prioritarias = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='sucesso')
            if municipality:
                query_prioritarias = query_prioritarias.filter_by(municipio=municipality)
            
            for entity in query_prioritarias.all():
                if entity.latitude and entity.longitude:
                    requirements = []
                    if entity.mrs_obrigatorio:
                        requirements.append('MRS')
                    if entity.map_obrigatorio:
                        requirements.append('MAP')
                    
                    point = RoutePoint(
                        id=f"prioritaria_{entity.id}",
                        name=entity.nome_entidade,
                        lat=entity.latitude,
                        lng=entity.longitude,
                        municipality=entity.municipio,
                        priority=1,  # Sempre P1
                        estimated_duration=120,  # Mais tempo para P1
                        visit_type="priority",
                        requirements=requirements
                    )
                    points.append(point)
            
            self.logger.info(f"📍 Carregadas {len(points)} entidades como pontos de rota")
            return points
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar entidades: {str(e)}")
            return []
    
    def optimize_with_google_maps(self, points: List[RoutePoint], 
                                 target_date: str = None) -> OptimizedRoute:
        """
        Otimização Nível 2: Com Google Maps API
        
        Args:
            points: Lista de pontos a serem visitados
            target_date: Data alvo para considerar trânsito (formato YYYY-MM-DD)
            
        Returns:
            Rota otimizada com dados reais do Google Maps
        """
        try:
            self.logger.info(f"🗺️ Iniciando otimização Nível 2 com Google Maps API")
            
            if not self.is_google_maps_available():
                self.logger.warning("⚠️ Google Maps não disponível, usando otimização local")
                return self.optimize_local(points)
            
            if len(points) == 0:
                return self._create_empty_route()
            
            if len(points) == 1:
                return self._create_single_point_route(points[0])
            
            # Preparar coordenadas dos municípios para Google Maps
            municipalities_coords = self._get_municipalities_coordinates()
            
            # Calcular matriz de distâncias/tempo real com Google Maps
            distance_matrix = self._get_google_distance_matrix(points, municipalities_coords, target_date)
            
            if not distance_matrix:
                self.logger.warning("⚠️ Falha na matriz do Google Maps, usando otimização local")
                return self.optimize_local(points)
            
            # Aplicar algoritmo TSP com dados reais
            optimized_order = self._solve_tsp_with_google_data(points, distance_matrix)
            
            # Calcular estatísticas finais
            total_distance_km, total_time_minutes = self._calculate_route_stats_google(
                optimized_order, distance_matrix
            )
            
            # Obter direções detalhadas para rota final
            detailed_directions = self._get_detailed_directions(optimized_order, municipalities_coords)
            
            result = OptimizedRoute(
                points=optimized_order,
                total_distance_km=total_distance_km,
                total_duration_minutes=total_time_minutes,
                total_driving_time_minutes=total_time_minutes - (len(points) * 90),  # Subtrair tempo de visitas
                optimization_score=self._calculate_optimization_score_google(
                    total_distance_km, total_time_minutes, len(points)
                ),
                route_type="google_maps_level_2",
                created_at=datetime.now(),
                metadata={
                    'algorithm': 'google_maps_tsp',
                    'api_calls': len(points) * (len(points) - 1),
                    'traffic_considered': bool(target_date),
                    'detailed_directions': detailed_directions,
                    'level': 2
                }
            )
            
            self.logger.info(f"✅ Otimização Nível 2 concluída: {total_distance_km:.1f}km, {total_time_minutes}min")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização Google Maps: {e}")
            # Fallback para otimização local
            return self.optimize_local(points)
    
    def optimize_local(self, points: List[RoutePoint]) -> OptimizedRoute:
        """
        Otimização Nível 1: Local (sem APIs externas)
        
        Args:
            points: Lista de pontos a serem visitados
            
        Returns:
            Rota otimizada usando algoritmos locais
        """
        try:
            self.logger.info(f"🧠 Iniciando otimização Nível 1 (local)")
            
            if len(points) == 0:
                return self._create_empty_route()
            
            if len(points) == 1:
                return self._create_single_point_route(points[0])
            
            # Usar algoritmo local existente (já implementado no frontend)
            municipalities_coords = self._get_municipalities_coordinates()
            
            # Implementar TSP básico
            optimized_order = self._solve_tsp_local(points, municipalities_coords)
            
            # Calcular estatísticas
            total_distance_km, total_time_minutes = self._calculate_route_stats_local(
                optimized_order, municipalities_coords
            )
            
            result = OptimizedRoute(
                points=optimized_order,
                total_distance_km=total_distance_km,
                total_duration_minutes=total_time_minutes,
                total_driving_time_minutes=total_time_minutes - (len(points) * 90),
                optimization_score=self._calculate_optimization_score_local(
                    total_distance_km, total_time_minutes, len(points)
                ),
                route_type="local_level_1",
                created_at=datetime.now(),
                metadata={
                    'algorithm': 'local_tsp',
                    'coordinates_used': True,
                    'level': 1
                }
            )
            
            self.logger.info(f"✅ Otimização Nível 1 concluída: {total_distance_km:.1f}km, {total_time_minutes}min")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro na otimização local: {e}")
            raise
    
    # Métodos auxiliares do Google Maps (Nível 2)
    
    def _get_municipalities_coordinates(self) -> Dict[str, Tuple[float, float]]:
        """Retorna coordenadas dos municípios de SC"""
        return {
            'Balneário Camboriú': (-26.9906, -48.6348),
            'Balneário Piçarras': (-26.7677, -48.6686),
            'Bombinhas': (-27.1394, -48.4839),
            'Camboriú': (-27.0254, -48.6515),
            'Itajaí': (-26.9077, -48.6644),
            'Itapema': (-27.0896, -48.6127),
            'Luiz Alves': (-26.7184, -48.9377),
            'Navegantes': (-26.8987, -48.6516),
            'Penha': (-26.7733, -48.6515),
            'Porto Belo': (-27.1587, -48.5543),
            'Ilhota': (-26.8996, -48.8279)
        }
    
    
    
    def _enrich_points_with_business_hours(self, points: List[RoutePoint], target_date: str = None) -> List[RoutePoint]:
        """Enriquecer pontos com horários de funcionamento reais (Google Places API)"""
        if not self.google_maps_client:
            self.logger.warning("🕰️ Google Maps client não disponível para buscar horários")
            return points
        
        enriched_points = []
        
        for point in points:
            try:
                # Buscar place_id primeiro via text search
                query = f"{point.name}, {point.municipality}, SC, Brazil"
                self.logger.info(f"🔍 Buscando horários para: {query}")
                
                # Text search para encontrar o place
                search_results = self.google_maps_client.places(
                    query=query,
                    location=(point.lat, point.lng),
                    radius=1000,
                    type='establishment'
                )
                
                if search_results['status'] == 'OK' and search_results['results']:
                    place = search_results['results'][0]
                    place_id = place['place_id']
                    
                    # Buscar detalhes do place incluindo horários
                    place_details = self.google_maps_client.place(
                        place_id=place_id,
                        fields=['opening_hours', 'name', 'formatted_address']
                    )
                    
                    if place_details['status'] == 'OK':
                        result = place_details['result']
                        
                        # Processar horários de funcionamento
                        if 'opening_hours' in result:
                            opening_hours = result['opening_hours']
                            business_hours = self._parse_opening_hours(opening_hours, target_date)
                            
                            # Adicionar horários ao ponto
                            point.business_hours = business_hours
                            
                            self.logger.info(f"✅ Horários encontrados para {point.name}: {business_hours}")
                        else:
                            self.logger.warning(f"⚠️ Horários não disponíveis para {point.name}")
                            point.business_hours = self._get_default_business_hours(point)
                    else:
                        self.logger.warning(f"⚠️ Falha ao obter detalhes para {point.name}")
                        point.business_hours = self._get_default_business_hours(point)
                else:
                    self.logger.warning(f"⚠️ Local não encontrado: {query}")
                    point.business_hours = self._get_default_business_hours(point)
                    
            except Exception as e:
                self.logger.error(f"❌ Erro ao buscar horários para {point.name}: {e}")
                point.business_hours = self._get_default_business_hours(point)
            
            enriched_points.append(point)
        
        return enriched_points
    
    def _parse_opening_hours(self, opening_hours: Dict, target_date: str = None) -> Dict:
        """Processar horários de funcionamento do Google Places"""
        try:
            # Determinar dia da semana
            if target_date:
                from datetime import datetime
                date_obj = datetime.strptime(target_date, '%Y-%m-%d')
                weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            else:
                from datetime import datetime
                weekday = datetime.now().weekday()
            
            # Mapear para formato Google (0=Sunday, 6=Saturday)
            google_weekday = (weekday + 1) % 7
            
            business_hours = {
                'is_open_now': opening_hours.get('open_now', True),
                'weekday_text': opening_hours.get('weekday_text', []),
                'periods': opening_hours.get('periods', [])
            }
            
            # Encontrar horário para o dia específico
            if business_hours['periods']:
                for period in business_hours['periods']:
                    if period.get('open', {}).get('day') == google_weekday:
                        open_time = period.get('open', {}).get('time', '0800')
                        close_time = period.get('close', {}).get('time', '1700')
                        
                        # Converter para formato HH:MM
                        business_hours['today_open'] = f"{open_time[:2]}:{open_time[2:]}"
                        business_hours['today_close'] = f"{close_time[:2]}:{close_time[2:]}"
                        business_hours['is_open_target_day'] = True
                        break
                else:
                    # Dia não encontrado, provavelmente fechado
                    business_hours['is_open_target_day'] = False
            
            return business_hours
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao processar horários: {e}")
            return self._get_default_business_hours_dict()
    
    def _get_default_business_hours(self, point: RoutePoint) -> Dict:
        """Obter horários padrão GENÉRICOS quando Google Places API falha"""
        # IMPORTANTE: Estes são apenas fallbacks genéricos
        # O sistema sempre deve tentar buscar horários reais via Google Places API primeiro
        
        entity_type = getattr(point, 'visit_type', 'standard')
        
        if 'prefeitura' in point.name.lower() or entity_type == 'prefeitura':
            # FALLBACK GENÉRICO - cada prefeitura tem horários únicos!
            return {
                'today_open': '08:00',  # Horário conservador mais cedo
                'today_close': '17:00', # Horário conservador mais tarde
                'is_open_target_day': True,
                'monday_friday': {'open': '08:00', 'close': '17:00'},
                'source': 'Fallback Genérico (VERIFICAR HORÁRIOS REAIS!)',
                'warning': 'Horários reais podem variar - confirmar com entidade'
            }
        elif 'secretaria' in point.name.lower() or entity_type == 'secretaria':
            # Secretarias municipais geralmente seguem padrão comercial
            return {
                'today_open': '08:00',
                'today_close': '17:00',
                'is_open_target_day': True,
                'monday_friday': {'open': '08:00', 'close': '17:00'},
                'source': 'Fallback Genérico',
                'warning': 'Confirmar horários específicos da secretaria'
            }
        else:
            # Entidades comerciais/outras - padrão comercial
            return {
                'today_open': '08:00',
                'today_close': '18:00',
                'is_open_target_day': True,
                'monday_friday': {'open': '08:00', 'close': '18:00'},
                'source': 'Fallback Genérico',
                'warning': 'Horários podem variar'
            }
    
    def _get_default_business_hours_dict(self) -> Dict:
        """Horários padrão quando não consegue determinar"""
        return {
            'today_open': '08:00',
            'today_close': '17:00',
            'is_open_target_day': True,
            'source': 'Padrão Genérico'
        }
    
    def _calculate_schedule_with_google_data(self, points: List[RoutePoint], 
                                           distance_matrix: Dict, 
                                           start_time: str, 
                                           end_time: str, 
                                           include_business_hours: bool = False) -> List[Dict]:
        """Calcular cronograma usando dados do Google Maps"""
        schedule = []
        current_time_minutes = self._time_str_to_minutes(start_time)
        
        for i, point in enumerate(points):
            # Calcular horário de início
            start_hour = current_time_minutes // 60
            start_min = current_time_minutes % 60
            
            # Calcular horário de fim
            end_time_minutes = current_time_minutes + point.estimated_duration
            end_hour = end_time_minutes // 60
            end_min = end_time_minutes % 60
            
            schedule_item = {
                'point': point,
                'horario_inicio': f"{start_hour:02d}:{start_min:02d}",
                'horario_fim': f"{end_hour:02d}:{end_min:02d}",
                'duracao_minutos': point.estimated_duration,
                'municipio': point.municipality,
                'nome': point.name,
                'prioridade': f"p{point.priority}"
            }
            
            # Adicionar tempo de viagem e distância para próximo ponto
            if i < len(points) - 1:
                next_point = points[i + 1]
                travel_time = 30  # Default
                distance_km = 0  # Default
                
                try:
                    if point.id in distance_matrix['durations'] and next_point.id in distance_matrix['durations'][point.id]:
                        travel_time = distance_matrix['durations'][point.id][next_point.id] // 60
                        
                        # Obter distância real também
                        if point.id in distance_matrix['distances'] and next_point.id in distance_matrix['distances'][point.id]:
                            distance_km = distance_matrix['distances'][point.id][next_point.id] / 1000
                            self.logger.debug(f"✅ Dados reais Google Maps: {distance_km:.2f}km, {travel_time}min entre {point.name} → {next_point.name}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Erro ao obter dados Google Maps: {e}")
                
                schedule_item['tempo_viagem_proxima'] = travel_time
                schedule_item['distancia_proxima_km'] = round(distance_km, 2)
                current_time_minutes = end_time_minutes + travel_time
            
            schedule.append(schedule_item)
        
        return schedule
    
    def _time_str_to_minutes(self, time_str: str) -> int:
        """Converter string de hora para minutos"""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return 8 * 60  # Default 8:00
    
    def _solve_tsp_local(self, points: List[RoutePoint], 
                        coords: Dict[str, Tuple[float, float]]) -> List[RoutePoint]:
        """Resolver TSP usando algoritmo local (Haversine)"""
        try:
            # Implementar algoritmo similar ao do frontend
            # Separar por prioridade
            p1_points = [p for p in points if p.priority == 1]
            p2_points = [p for p in points if p.priority == 2]
            p3_points = [p for p in points if p.priority >= 3]
            
            def haversine_distance(lat1, lng1, lat2, lng2):
                """Calcular distância usando fórmula de Haversine"""
                R = 6371  # Raio da Terra em km
                dlat = math.radians(lat2 - lat1)
                dlng = math.radians(lng2 - lng1)
                a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                     math.sin(dlng/2) * math.sin(dlng/2))
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            
            def optimize_group(group):
                if len(group) <= 1:
                    return group
                
                route = [group[0]]
                remaining = group[1:]
                
                while remaining:
                    current = route[-1]
                    current_coords = coords.get(current.municipality, (current.lat, current.lng))
                    
                    nearest = min(remaining, key=lambda p: haversine_distance(
                        current_coords[0], current_coords[1],
                        coords.get(p.municipality, (p.lat, p.lng))[0],
                        coords.get(p.municipality, (p.lat, p.lng))[1]
                    ))
                    
                    route.append(nearest)
                    remaining.remove(nearest)
                
                return route
            
            # Otimizar cada grupo
            optimized = []
            for group in [p1_points, p2_points, p3_points]:
                optimized.extend(optimize_group(group))
            
            return optimized
            
        except Exception as e:
            self.logger.error(f"❌ Erro no TSP local: {e}")
            return points
    
    def _calculate_route_stats_google(self, points: List[RoutePoint], 
                                    distance_matrix: Dict) -> Tuple[float, int]:
        """Calcular estatísticas usando dados do Google Maps"""
        try:
            total_distance_m = 0
            total_time_s = 0
            
            distances = distance_matrix['distances']
            durations = distance_matrix['durations_in_traffic']
            
            # Mapear pontos para índices
            point_indices = {id(point): i for i, point in enumerate(points)}
            
            for i in range(len(points) - 1):
                current_idx = point_indices[id(points[i])]
                next_idx = point_indices[id(points[i + 1])]
                
                total_distance_m += distances[current_idx][next_idx]
                total_time_s += durations[current_idx][next_idx]
            
            # Adicionar tempo das visitas
            total_time_s += len(points) * 90 * 60  # 90 min por visita
            
            return total_distance_m / 1000.0, total_time_s // 60  # km, minutos
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular estatísticas Google: {e}")
            return 0.0, 0
    
    def _calculate_route_stats_local(self, points: List[RoutePoint], 
                                   coords: Dict[str, Tuple[float, float]]) -> Tuple[float, int]:
        """Calcular estatísticas usando algoritmo local"""
        try:
            def haversine_distance(lat1, lng1, lat2, lng2):
                R = 6371
                dlat = math.radians(lat2 - lat1)
                dlng = math.radians(lng2 - lng1)
                a = (math.sin(dlat/2) * math.sin(dlat/2) + 
                     math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * 
                     math.sin(dlng/2) * math.sin(dlng/2))
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                return R * c
            
            total_distance_km = 0
            total_time_minutes = 0
            
            for i in range(len(points) - 1):
                current_coords = coords.get(points[i].municipality, (points[i].lat, points[i].lng))
                next_coords = coords.get(points[i + 1].municipality, (points[i + 1].lat, points[i + 1].lng))
                
                distance = haversine_distance(
                    current_coords[0], current_coords[1],
                    next_coords[0], next_coords[1]
                )
                
                total_distance_km += distance
                
                # Estimar tempo (30 km/h + fator de trânsito)
                travel_time = (distance / 30.0) * 60 * 1.4  # minutos
                total_time_minutes += max(15, travel_time)
            
            # Adicionar tempo das visitas
            total_time_minutes += len(points) * 90  # 90 min por visita
            
            return total_distance_km, int(total_time_minutes)
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao calcular estatísticas locais: {e}")
            return 0.0, 0
    
    def _get_detailed_directions(self, points: List[RoutePoint], 
                               coords: Dict[str, Tuple[float, float]]) -> List[Dict]:
        """Obter direções detalhadas do Google Maps incluindo viagem inicial e retorno"""
        try:
            if not self.google_maps_client or len(points) < 1:
                return []
            
            directions = []
            base_coords = (self.starting_point['lat'], self.starting_point['lng'])
            
            # 1. VIAGEM INICIAL: Base → Primeiro ponto
            if len(points) > 0:
                first_point_coords = coords.get(points[0].municipality, (points[0].lat, points[0].lng))
                
                result = self.google_maps_client.directions(
                    origin=base_coords,
                    destination=first_point_coords,
                    mode="driving",
                    language="pt-BR"
                )
                
                if result:
                    route = result[0]
                    leg = route['legs'][0]
                    
                    directions.append({
                        'from': self.starting_point['name'],
                        'to': points[0].municipality,
                        'distance': leg['distance']['text'],
                        'duration': leg['duration']['text'],
                        'steps': [step['html_instructions'] for step in leg['steps'][:3]],
                        'trip_type': 'initial'
                    })
            
            # 2. VIAGENS ENTRE PONTOS: Ponto A → Ponto B
            for i in range(len(points) - 1):
                origin_coords = coords.get(points[i].municipality, (points[i].lat, points[i].lng))
                dest_coords = coords.get(points[i + 1].municipality, (points[i + 1].lat, points[i + 1].lng))
                
                result = self.google_maps_client.directions(
                    origin=origin_coords,
                    destination=dest_coords,
                    mode="driving",
                    language="pt-BR"
                )
                
                if result:
                    route = result[0]
                    leg = route['legs'][0]
                    
                    directions.append({
                        'from': points[i].municipality,
                        'to': points[i + 1].municipality,
                        'distance': leg['distance']['text'],
                        'duration': leg['duration']['text'],
                        'steps': [step['html_instructions'] for step in leg['steps'][:3]],
                        'trip_type': 'between_points'
                    })
            
            # 3. VIAGEM DE RETORNO: Último ponto → Base
            if len(points) > 0:
                last_point_coords = coords.get(points[-1].municipality, (points[-1].lat, points[-1].lng))
                
                result = self.google_maps_client.directions(
                    origin=last_point_coords,
                    destination=base_coords,
                    mode="driving",
                    language="pt-BR"
                )
                
                if result:
                    route = result[0]
                    leg = route['legs'][0]
                    
                    directions.append({
                        'from': points[-1].municipality,
                        'to': self.starting_point['name'],
                        'distance': leg['distance']['text'],
                        'duration': leg['duration']['text'],
                        'steps': [step['html_instructions'] for step in leg['steps'][:3]],
                        'trip_type': 'return'
                    })
            
            return directions
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter direções: {e}")
            return []
    
    def _calculate_optimization_score_google(self, distance_km: float, 
                                           time_minutes: int, num_points: int) -> float:
        """Calcular score de otimização para dados do Google Maps"""
        try:
            # Score baseado em eficiência
            efficiency = num_points / (time_minutes / 60.0)  # visitas por hora
            distance_efficiency = num_points / distance_km if distance_km > 0 else 0  # visitas por km
            
            # Normalizar para 0-100
            score = min(100, (efficiency * 10) + (distance_efficiency * 20))
            return round(score, 1)
            
        except:
            return 50.0  # Score neutro
    
    def _calculate_optimization_score_local(self, distance_km: float, 
                                          time_minutes: int, num_points: int) -> float:
        """Calcular score de otimização para dados locais"""
        try:
            # Score mais conservador para dados estimados
            efficiency = num_points / (time_minutes / 60.0)
            score = min(90, efficiency * 8)  # Máximo 90 para algoritmo local
            return round(score, 1)
            
        except:
            return 40.0  # Score neutro mais baixo
    
    def _create_empty_route(self) -> OptimizedRoute:
        """Criar rota vazia"""
        return OptimizedRoute(
            points=[],
            total_distance_km=0.0,
            total_duration_minutes=0,
            total_driving_time_minutes=0,
            optimization_score=0.0,
            route_type="empty",
            created_at=datetime.now(),
            metadata={'level': 0}
        )
    
    def _create_single_point_route(self, point: RoutePoint) -> OptimizedRoute:
        """Criar rota com um único ponto"""
        return OptimizedRoute(
            points=[point],
            total_distance_km=0.0,
            total_duration_minutes=point.estimated_duration,
            total_driving_time_minutes=0,
            optimization_score=100.0,
            route_type="single_point",
            created_at=datetime.now(),
            metadata={'level': 1}
        )
    
    # Métodos privados auxiliares
    
    def _adjust_weights(self, optimization_type: str):
        """Ajusta pesos baseado no tipo de otimização"""
        if optimization_type == "distance":
            self.weights = {'distance': 0.7, 'time': 0.2, 'priority': 0.05, 'efficiency': 0.05}
        elif optimization_type == "time":
            self.weights = {'distance': 0.2, 'time': 0.7, 'priority': 0.05, 'efficiency': 0.05}
        elif optimization_type == "priority":
            self.weights = {'distance': 0.2, 'time': 0.2, 'priority': 0.5, 'efficiency': 0.1}
        else:  # balanced
            self.weights = {'distance': 0.4, 'time': 0.3, 'priority': 0.2, 'efficiency': 0.1}
    
    def _calculate_distance_matrix(self, points: List[RoutePoint], 
                                 start_location: Tuple[float, float] = None) -> np.ndarray:
        """Calcula matriz de distâncias entre pontos"""
        n = len(points)
        matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    # Tentar buscar do cache offline primeiro
                    cached_route = self.offline_maps.get_cached_route(
                        (points[i].lat, points[i].lng),
                        (points[j].lat, points[j].lng)
                    )
                    
                    if cached_route:
                        matrix[i][j] = cached_route.get('distance_meters', 0)
                    else:
                        # Calcular distância euclidiana como fallback
                        distance = self._calculate_haversine_distance(
                            points[i].lat, points[i].lng,
                            points[j].lat, points[j].lng
                        )
                        matrix[i][j] = distance * 1000  # Converter para metros
        
        return matrix
    
    def _calculate_haversine_distance(self, lat1: float, lng1: float, 
                                    lat2: float, lng2: float) -> float:
        """Calcula distância haversine entre dois pontos em km"""
        R = 6371  # Raio da Terra em km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _optimize_small_route(self, points: List[RoutePoint], 
                            distance_matrix: np.ndarray) -> List[int]:
        """Otimização para rotas pequenas usando TSP"""
        n = len(points)
        if n <= 1:
            return list(range(n))
        
        best_order = None
        best_score = float('inf')
        
        # Testar todas as permutações possíveis (força bruta para n <= 8)
        for permutation in itertools.permutations(range(1, n)):
            order = [0] + list(permutation)  # Começar sempre do primeiro ponto
            score = self._calculate_route_score(order, points, distance_matrix)
            
            if score < best_score:
                best_score = score
                best_order = order
        
        return best_order or list(range(n))
    
    def _optimize_large_route(self, points: List[RoutePoint], 
                            distance_matrix: np.ndarray) -> List[int]:
        """Otimização para rotas grandes usando algoritmo genético simplificado"""
        n = len(points)
        
        # Para rotas muito grandes, usar nearest neighbor heuristic
        visited = [False] * n
        order = [0]  # Começar do primeiro ponto
        visited[0] = True
        
        current = 0
        while len(order) < n:
            min_distance = float('inf')
            next_point = -1
            
            for i in range(n):
                if not visited[i]:
                    # Considerar distância e prioridade
                    distance = distance_matrix[current][i]
                    priority_bonus = (3 - points[i].priority) * 1000  # Menor valor = maior prioridade
                    score = distance + priority_bonus
                    
                    if score < min_distance:
                        min_distance = score
                        next_point = i
            
            if next_point != -1:
                order.append(next_point)
                visited[next_point] = True
                current = next_point
        
        return order
    
    def _calculate_route_score(self, order: List[int], points: List[RoutePoint], 
                             distance_matrix: np.ndarray) -> float:
        """Calcula score de uma rota baseado na função objetivo"""
        total_distance = 0
        total_time = 0
        priority_penalty = 0
        
        # Calcular distância e tempo total
        for i in range(len(order) - 1):
            current_idx = order[i]
            next_idx = order[i + 1]
            
            distance = distance_matrix[current_idx][next_idx]
            total_distance += distance
            
            # Estimar tempo de viagem (assumindo velocidade média)
            travel_time = distance / 1000 * 2  # ~30 km/h média em área urbana
            work_time = points[next_idx].estimated_duration
            total_time += travel_time + work_time
        
        # Penalizar por não priorizar P1
        for i, point_idx in enumerate(order):
            if points[point_idx].priority == 1 and i > len(order) // 2:
                priority_penalty += 1000  # Penalidade por deixar P1 para o final
        
        # Calcular score final com pesos
        score = (self.weights['distance'] * total_distance +
                self.weights['time'] * total_time * 60 +  # Converter para segundos
                self.weights['priority'] * priority_penalty)
        
        return score
    
    def _calculate_route_metrics(self, points: List[RoutePoint], 
                               distance_matrix: np.ndarray, 
                               order: List[int]) -> Tuple[float, int, int]:
        """Calcula métricas detalhadas da rota"""
        total_distance = 0
        total_driving_time = 0
        total_work_time = 0
        
        for i in range(len(order) - 1):
            current_idx = order[i]
            next_idx = order[i + 1]
            
            # Distância
            distance = distance_matrix[current_idx][next_idx]
            total_distance += distance
            
            # Tempo de viagem
            travel_time = max(distance / 1000 * 2, 5)  # Mínimo 5 min entre pontos
            total_driving_time += travel_time
        
        # Tempo de trabalho
        for point in points:
            total_work_time += point.estimated_duration
        
        total_time = total_driving_time + total_work_time
        
        return total_distance, int(total_time), int(total_driving_time)
    
    def _calculate_optimization_score(self, points: List[RoutePoint], 
                                    total_distance: float, total_time: int, 
                                    driving_time: int) -> float:
        """Calcula score de otimização (0-100)"""
        try:
            # Métricas ideais para comparação
            ideal_distance_per_point = 2000  # 2km entre pontos
            ideal_work_time_ratio = 0.7  # 70% do tempo trabalhando
            
            # Score de distância (melhor = menor distância)
            avg_distance = total_distance / max(len(points) - 1, 1)
            distance_score = max(0, 100 - (avg_distance / ideal_distance_per_point) * 50)
            
            # Score de eficiência temporal
            work_time = total_time - driving_time
            work_ratio = work_time / total_time if total_time > 0 else 0
            time_score = work_ratio / ideal_work_time_ratio * 100
            time_score = min(100, time_score)
            
            # Score de prioridade (P1 no início = melhor)
            priority_score = 100
            for i, point in enumerate(points):
                if point.priority == 1 and i > len(points) // 2:
                    priority_score -= 20
            
            # Score final ponderado
            final_score = (distance_score * 0.4 + time_score * 0.4 + priority_score * 0.2)
            
            return max(0, min(100, final_score))
            
        except Exception:
            return 50.0  # Score neutro em caso de erro
    
    def _distribute_points_across_days(self, points: List[RoutePoint], 
                                     working_days: int) -> List[List[RoutePoint]]:
        """Distribui pontos de forma inteligente entre os dias"""
        if not points:
            return []
        
        # Separar por prioridade
        p1_points = [p for p in points if p.priority == 1]
        other_points = [p for p in points if p.priority != 1]
        
        # Distribuir P1 primeiro (uma por dia se possível)
        daily_groups = [[] for _ in range(working_days)]
        
        for i, p1_point in enumerate(p1_points):
            day_idx = i % working_days
            daily_groups[day_idx].append(p1_point)
        
        # Distribuir outros pontos por proximidade geográfica
        remaining_points = other_points.copy()
        
        for day_idx in range(working_days):
            target_points_per_day = (len(points) // working_days) + (1 if day_idx < len(points) % working_days else 0)
            current_day_points = len(daily_groups[day_idx])
            
            while current_day_points < target_points_per_day and remaining_points:
                if daily_groups[day_idx]:
                    # Encontrar ponto mais próximo aos já alocados no dia
                    last_point = daily_groups[day_idx][-1]
                    closest_point = min(remaining_points, 
                                      key=lambda p: self._calculate_haversine_distance(
                                          last_point.lat, last_point.lng, p.lat, p.lng))
                else:
                    # Se não há pontos no dia, pegar qualquer um
                    closest_point = remaining_points[0]
                
                daily_groups[day_idx].append(closest_point)
                remaining_points.remove(closest_point)
                current_day_points += 1
        
        # Adicionar pontos restantes
        for point in remaining_points:
            # Adicionar ao dia com menos pontos
            min_day = min(range(working_days), key=lambda i: len(daily_groups[i]))
            daily_groups[min_day].append(point)
        
        return daily_groups
    
    def _optimize_inter_day_transitions(self, weekly_routes: List[OptimizedRoute]) -> List[OptimizedRoute]:
        """Otimiza transições entre dias consecutivos"""
        if len(weekly_routes) <= 1:
            return weekly_routes
        
        optimized_routes = []
        
        for i, route in enumerate(weekly_routes):
            optimized_route = route
            
            # Para dias após o primeiro, considerar posição final do dia anterior
            if i > 0:
                prev_route = optimized_routes[i - 1]
                if prev_route.points:
                    last_point_prev_day = prev_route.points[-1]
                    
                    # Reorganizar início do dia atual para começar próximo ao fim do anterior
                    current_points = route.points.copy()
                    if current_points:
                        # Encontrar melhor ponto de início
                        best_start_idx = 0
                        min_distance = float('inf')
                        
                        for j, point in enumerate(current_points):
                            distance = self._calculate_haversine_distance(
                                last_point_prev_day.lat, last_point_prev_day.lng,
                                point.lat, point.lng
                            )
                            if distance < min_distance:
                                min_distance = distance
                                best_start_idx = j
                        
                        # Reordenar se necessário
                        if best_start_idx != 0:
                            reordered_points = (current_points[best_start_idx:] + 
                                              current_points[:best_start_idx])
                            
                            # Recriar rota com nova ordem
                            optimized_route = self.optimize_daily_route(reordered_points)
                            optimized_route.metadata.update(route.metadata)
            
            optimized_routes.append(optimized_route)
        
        return optimized_routes
    
    def _calculate_point_schedule(self, route: OptimizedRoute, 
                                start_hour: int, start_min: int) -> List[Dict[str, str]]:
        """Calcula horário estimado para cada ponto da rota"""
        schedule = []
        current_time = start_hour * 60 + start_min  # Em minutos
        
        for i, point in enumerate(route.points):
            # Horário de chegada
            arrival_hour = int(current_time // 60)
            arrival_min = int(current_time % 60)
            
            # Horário de saída (após trabalho)
            departure_time = current_time + point.estimated_duration
            departure_hour = int(departure_time // 60)
            departure_min = int(departure_time % 60)
            
            schedule.append({
                'point_name': point.name,
                'arrival_time': f"{arrival_hour:02d}:{arrival_min:02d}",
                'departure_time': f"{departure_hour:02d}:{departure_min:02d}",
                'duration_minutes': point.estimated_duration
            })
            
            current_time = departure_time
            
            # Adicionar tempo de viagem para o próximo ponto
            if i < len(route.points) - 1:
                # Estimar tempo de viagem (usar dados reais se disponível)
                travel_time = 15  # Default 15 min
                current_time += travel_time
        
        return schedule
    
    def _generate_schedule_notes(self, route: OptimizedRoute) -> List[str]:
        """Gera notas e sugestões para o horário"""
        notes = []
        
        if route.total_duration_minutes > 480:  # Mais de 8 horas
            notes.append("⚠️ Rota extensa - considere dividir em dois dias")
        
        p1_count = len([p for p in route.points if p.priority == 1])
        if p1_count > 0:
            notes.append(f"🎯 {p1_count} entidade(s) prioritária(s) incluída(s)")
        
        if route.total_driving_time_minutes > route.total_duration_minutes * 0.4:
            notes.append("🚗 Muito tempo de deslocamento - verificar otimização")
        
        return notes
    
    def _create_empty_route(self) -> OptimizedRoute:
        """Cria rota vazia para casos especiais"""
        return OptimizedRoute(
            points=[],
            total_distance_km=0,
            total_duration_minutes=0,
            total_driving_time_minutes=0,
            optimization_score=0,
            route_type="empty",
            created_at=datetime.now(),
            metadata={'reason': 'no_points_provided'}
        )
    
    def _create_single_point_route(self, point: RoutePoint) -> OptimizedRoute:
        """Cria rota com um único ponto"""
        return OptimizedRoute(
            points=[point],
            total_distance_km=0,
            total_duration_minutes=point.estimated_duration,
            total_driving_time_minutes=0,
            optimization_score=100,
            route_type="single_point",
            created_at=datetime.now(),
            metadata={'reason': 'single_point_only'}
        )
    
    def _create_fallback_route(self, points: List[RoutePoint]) -> OptimizedRoute:
        """Cria rota de fallback em caso de erro"""
        total_duration = sum(p.estimated_duration for p in points)
        
        return OptimizedRoute(
            points=points,
            total_distance_km=len(points) * 5,  # Estimativa
            total_duration_minutes=total_duration + len(points) * 15,  # 15 min entre pontos
            total_driving_time_minutes=len(points) * 15,
            optimization_score=50,
            route_type="fallback",
            created_at=datetime.now(),
            metadata={'reason': 'optimization_error', 'original_order': True}
        )
    
    def _get_applied_constraints(self, points: List[RoutePoint]) -> List[str]:
        """Lista restrições aplicadas na otimização"""
        constraints = []
        
        if any(p.time_window_start for p in points):
            constraints.append("time_windows")
        
        if any(p.priority == 1 for p in points):
            constraints.append("priority_ordering")
        
        if len(points) > self.max_points_per_route:
            constraints.append("max_points_limit")
        
        return constraints
    
    def _calculate_geographic_spread(self, points: List[RoutePoint]) -> float:
        """Calcula dispersão geográfica dos pontos"""
        if len(points) < 2:
            return 0
        
        lats = [p.lat for p in points]
        lngs = [p.lng for p in points]
        
        max_lat, min_lat = max(lats), min(lats)
        max_lng, min_lng = max(lngs), min(lngs)
        
        # Calcular distância entre extremos
        spread = self._calculate_haversine_distance(min_lat, min_lng, max_lat, max_lng)
        
        return spread
    
    def _calculate_route_compactness(self, points: List[RoutePoint]) -> float:
        """Calcula compacidade da rota (0-1, onde 1 = mais compacta)"""
        if len(points) < 3:
            return 1.0
        
        # Calcular centro geográfico
        center_lat = sum(p.lat for p in points) / len(points)
        center_lng = sum(p.lng for p in points) / len(points)
        
        # Calcular distâncias do centro
        distances = [self._calculate_haversine_distance(center_lat, center_lng, p.lat, p.lng) 
                    for p in points]
        
        avg_distance = sum(distances) / len(distances)
        max_distance = max(distances)
        
        # Compacidade = 1 - (variação das distâncias)
        if max_distance == 0:
            return 1.0
        
        compactness = 1 - (max_distance - avg_distance) / max_distance
        
        return max(0, min(1, compactness))
    
    def _generate_efficiency_suggestions(self, route: OptimizedRoute) -> List[str]:
        """Gera sugestões para melhorar eficiência"""
        suggestions = []
        
        # Análise de tempo
        work_time_ratio = (route.total_duration_minutes - route.total_driving_time_minutes) / route.total_duration_minutes
        if work_time_ratio < 0.6:
            suggestions.append("Considere agrupar mais visitas próximas para reduzir tempo de deslocamento")
        
        # Análise de distância
        avg_distance = route.total_distance_km / max(len(route.points) - 1, 1)
        if avg_distance > 5:
            suggestions.append("Distância média entre pontos é alta - verificar possibilidade de reagrupamento")
        
        # Análise de prioridade
        p1_points = [i for i, p in enumerate(route.points) if p.priority == 1]
        if p1_points and max(p1_points) > len(route.points) // 2:
            suggestions.append("Priorizar entidades P1 no início do dia")
        
        # Análise temporal
        if route.total_duration_minutes > 480:
            suggestions.append("Rota muito longa - considere dividir em múltiplos dias")
        
        return suggestions
    
    def _assess_optimization_potential(self, route: OptimizedRoute) -> Dict[str, Any]:
        """Avalia potencial de otimização adicional"""
        potential = {
            'can_improve': False,
            'improvement_areas': [],
            'estimated_savings': {}
        }
        
        # Verificar se há melhorias possíveis
        if route.optimization_score < 80:
            potential['can_improve'] = True
            potential['improvement_areas'].append('route_order')
        
        # Estimar economias possíveis
        if route.total_driving_time_minutes > route.total_duration_minutes * 0.4:
            potential['estimated_savings']['time_minutes'] = int(route.total_driving_time_minutes * 0.2)
            potential['estimated_savings']['distance_km'] = round(route.total_distance_km * 0.15, 1)
        
        return potential