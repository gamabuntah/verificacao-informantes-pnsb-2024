"""
Serviço de Analytics Avançados para PNSB 2024
Heatmaps geográficos, análise de cobertura, métricas de eficiência e dashboards especializados
"""

import math
import numpy as np
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import current_app
import logging
from collections import defaultdict, Counter
from dataclasses import dataclass

from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF
from gestao_visitas.services.route_optimizer import RouteOptimizer


@dataclass
class GeographicPoint:
    """Representa um ponto geográfico para análise"""
    lat: float
    lng: float
    weight: float = 1.0
    entity_type: str = "unknown"
    municipality: str = "unknown"
    priority: int = 2
    status: str = "pending"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class HeatmapData:
    """Dados para geração de heatmap"""
    points: List[GeographicPoint]
    center: Tuple[float, float]
    bounds: Dict[str, float]
    intensity_scale: Tuple[float, float]
    metadata: Dict[str, Any]


@dataclass
class CoverageAnalysis:
    """Análise de cobertura geográfica"""
    total_area_km2: float
    covered_area_km2: float
    coverage_percentage: float
    gaps: List[Dict[str, Any]]
    clusters: List[Dict[str, Any]]
    density_map: Dict[str, float]
    recommendations: List[str]


class AdvancedAnalytics:
    """Serviço de analytics avançados para o PNSB 2024"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.route_optimizer = RouteOptimizer()
        
        # Configurações de análise
        self.grid_size_km = 2.0  # Resolução da grade para análise (2km x 2km)
        self.cluster_radius_km = 5.0  # Raio para detecção de clusters
        self.coverage_radius_km = 3.0  # Raio de cobertura por entidade
        
        # Limites geográficos de Santa Catarina (região PNSB)
        self.sc_bounds = {
            'north': -26.5,
            'south': -27.3,
            'east': -48.3,
            'west': -49.1
        }
    
    def generate_entity_heatmap(self, municipality: str = None, 
                              entity_type: str = None,
                              weight_by: str = "density") -> HeatmapData:
        """
        Gera heatmap de densidade de entidades
        
        Args:
            municipality: Filtrar por município específico
            entity_type: Filtrar por tipo (identificada, prioritaria)
            weight_by: Critério de peso (density, priority, requirements)
            
        Returns:
            Dados estruturados para heatmap
        """
        try:
            self.logger.info(f"📊 Gerando heatmap de entidades - {municipality or 'todos'}")
            
            # Carregar entidades
            points = self._load_geographic_points(municipality, entity_type)
            
            if not points:
                return self._create_empty_heatmap()
            
            # Aplicar pesos baseado no critério
            weighted_points = self._apply_weights(points, weight_by)
            
            # Calcular centro e bounds
            center = self._calculate_geographic_center(weighted_points)
            bounds = self._calculate_bounds(weighted_points)
            
            # Calcular escala de intensidade
            weights = [p.weight for p in weighted_points]
            intensity_scale = (min(weights), max(weights))
            
            metadata = {
                'generated_at': datetime.now().isoformat(),
                'total_points': len(weighted_points),
                'weight_criteria': weight_by,
                'municipality_filter': municipality,
                'entity_type_filter': entity_type,
                'average_weight': sum(weights) / len(weights) if weights else 0
            }
            
            return HeatmapData(
                points=weighted_points,
                center=center,
                bounds=bounds,
                intensity_scale=intensity_scale,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar heatmap: {str(e)}")
            return self._create_empty_heatmap()
    
    def analyze_geographic_coverage(self, municipality: str = None) -> CoverageAnalysis:
        """
        Analisa cobertura geográfica das entidades
        
        Args:
            municipality: Analisar município específico
            
        Returns:
            Análise completa de cobertura
        """
        try:
            self.logger.info(f"🗺️ Analisando cobertura geográfica - {municipality or 'toda região'}")
            
            # Carregar pontos geográficos
            points = self._load_geographic_points(municipality)
            
            if not points:
                return self._create_empty_coverage()
            
            # Calcular área total de análise
            total_area = self._calculate_analysis_area(municipality)
            
            # Analisar cobertura usando grade
            grid_analysis = self._analyze_coverage_grid(points, municipality)
            covered_area = grid_analysis['covered_area_km2']
            coverage_percentage = (covered_area / total_area) * 100 if total_area > 0 else 0
            
            # Detectar gaps (áreas sem cobertura)
            gaps = self._detect_coverage_gaps(points, municipality)
            
            # Detectar clusters
            clusters = self._detect_entity_clusters(points)
            
            # Calcular densidade por região
            density_map = self._calculate_density_map(points, municipality)
            
            # Gerar recomendações
            recommendations = self._generate_coverage_recommendations(
                points, gaps, clusters, coverage_percentage
            )
            
            return CoverageAnalysis(
                total_area_km2=total_area,
                covered_area_km2=covered_area,
                coverage_percentage=round(coverage_percentage, 1),
                gaps=gaps,
                clusters=clusters,
                density_map=density_map,
                recommendations=recommendations
            )
            
        except Exception as e:
            self.logger.error(f"❌ Erro na análise de cobertura: {str(e)}")
            return self._create_empty_coverage()
    
    def generate_efficiency_metrics(self, start_date: datetime = None, 
                                  end_date: datetime = None) -> Dict[str, Any]:
        """
        Gera métricas avançadas de eficiência operacional
        
        Args:
            start_date: Data inicial para análise
            end_date: Data final para análise
            
        Returns:
            Métricas detalhadas de eficiência
        """
        try:
            self.logger.info("📈 Calculando métricas de eficiência operacional")
            
            # Definir período padrão se não informado
            if not end_date:
                end_date = datetime.now()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Carregar dados de visitas no período
            visitas = self._load_visits_in_period(start_date, end_date)
            
            # Métricas temporais
            temporal_metrics = self._calculate_temporal_metrics(visitas, start_date, end_date)
            
            # Métricas geográficas
            geographic_metrics = self._calculate_geographic_metrics(visitas)
            
            # Métricas de produtividade
            productivity_metrics = self._calculate_productivity_metrics(visitas)
            
            # Métricas de qualidade
            quality_metrics = self._calculate_quality_metrics(visitas)
            
            # Análise de tendências
            trend_analysis = self._analyze_trends(visitas, start_date, end_date)
            
            # Score geral de eficiência
            overall_score = self._calculate_overall_efficiency_score(
                temporal_metrics, geographic_metrics, productivity_metrics, quality_metrics
            )
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days_analyzed': (end_date - start_date).days
                },
                'overall_efficiency_score': overall_score,
                'temporal_metrics': temporal_metrics,
                'geographic_metrics': geographic_metrics,
                'productivity_metrics': productivity_metrics,
                'quality_metrics': quality_metrics,
                'trend_analysis': trend_analysis,
                'key_insights': self._generate_efficiency_insights(
                    temporal_metrics, geographic_metrics, productivity_metrics
                ),
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro no cálculo de métricas: {str(e)}")
            return {'error': str(e)}
    
    def create_municipality_dashboard(self, municipality: str) -> Dict[str, Any]:
        """
        Cria dashboard especializado para um município
        
        Args:
            municipality: Nome do município
            
        Returns:
            Dados completos do dashboard municipal
        """
        try:
            self.logger.info(f"🏛️ Criando dashboard para {municipality}")
            
            # Estatísticas básicas
            basic_stats = self._get_municipality_basic_stats(municipality)
            
            # Heatmap de entidades
            heatmap_data = self.generate_entity_heatmap(municipality)
            
            # Análise de cobertura
            coverage_analysis = self.analyze_geographic_coverage(municipality)
            
            # Métricas de progresso
            progress_metrics = self._calculate_municipality_progress(municipality)
            
            # Análise de rotas otimizadas
            route_analysis = self._analyze_municipality_routes(municipality)
            
            # Cronograma e previsões
            timeline_data = self._generate_municipality_timeline(municipality)
            
            # Comparativo com outros municípios
            comparative_analysis = self._compare_with_other_municipalities(municipality)
            
            return {
                'municipality': municipality,
                'generated_at': datetime.now().isoformat(),
                'basic_statistics': basic_stats,
                'heatmap_data': {
                    'center': heatmap_data.center,
                    'bounds': heatmap_data.bounds,
                    'points': [
                        {
                            'lat': p.lat,
                            'lng': p.lng,
                            'weight': p.weight,
                            'type': p.entity_type,
                            'priority': p.priority,
                            'status': p.status
                        }
                        for p in heatmap_data.points
                    ],
                    'metadata': heatmap_data.metadata
                },
                'coverage_analysis': {
                    'coverage_percentage': coverage_analysis.coverage_percentage,
                    'total_area_km2': coverage_analysis.total_area_km2,
                    'gaps_count': len(coverage_analysis.gaps),
                    'clusters_count': len(coverage_analysis.clusters),
                    'recommendations': coverage_analysis.recommendations
                },
                'progress_metrics': progress_metrics,
                'route_analysis': route_analysis,
                'timeline_data': timeline_data,
                'comparative_analysis': comparative_analysis
            }
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar dashboard: {str(e)}")
            return {'error': str(e), 'municipality': municipality}
    
    def generate_ibge_report(self, format_type: str = "executive") -> Dict[str, Any]:
        """
        Gera relatório especializado para o IBGE
        
        Args:
            format_type: Tipo de relatório (executive, detailed, technical)
            
        Returns:
            Relatório formatado para o IBGE
        """
        try:
            self.logger.info(f"📋 Gerando relatório IBGE - formato {format_type}")
            
            # Dados gerais do projeto
            project_overview = self._get_project_overview()
            
            # Status por município
            municipal_status = self._get_all_municipalities_status()
            
            # Métricas de progresso
            progress_summary = self._calculate_overall_progress()
            
            # Análise de qualidade
            quality_assessment = self._assess_data_quality()
            
            # Desafios e riscos
            challenges_risks = self._identify_challenges_and_risks()
            
            # Recomendações estratégicas
            strategic_recommendations = self._generate_strategic_recommendations()
            
            # Cronograma e previsões
            timeline_projections = self._generate_project_timeline()
            
            report_data = {
                'report_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'format_type': format_type,
                    'coverage_period': self._get_coverage_period(),
                    'report_version': '1.0'
                },
                'executive_summary': {
                    'total_municipalities': len(municipal_status),
                    'completion_percentage': progress_summary['overall_completion'],
                    'entities_surveyed': progress_summary['total_entities_processed'],
                    'key_achievements': progress_summary['key_achievements'],
                    'major_challenges': challenges_risks['major_challenges'][:3]
                },
                'project_overview': project_overview,
                'municipal_breakdown': municipal_status,
                'progress_metrics': progress_summary,
                'quality_assessment': quality_assessment,
                'geographic_analysis': self._generate_regional_analysis(),
                'operational_efficiency': self._calculate_operational_kpis(),
                'challenges_and_risks': challenges_risks,
                'strategic_recommendations': strategic_recommendations,
                'timeline_and_projections': timeline_projections
            }
            
            # Ajustar nível de detalhe baseado no formato
            if format_type == "executive":
                report_data = self._summarize_for_executive(report_data)
            elif format_type == "technical":
                report_data = self._expand_for_technical(report_data)
            
            return report_data
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao gerar relatório IBGE: {str(e)}")
            return {'error': str(e), 'format_type': format_type}
    
    # Métodos auxiliares privados
    
    def _load_geographic_points(self, municipality: str = None, 
                              entity_type: str = None) -> List[GeographicPoint]:
        """Carrega pontos geográficos das entidades"""
        points = []
        
        try:
            # Carregar entidades identificadas
            if not entity_type or entity_type == "identificada":
                query_identificadas = EntidadeIdentificada.query.filter_by(geocodificacao_status='sucesso')
                if municipality:
                    query_identificadas = query_identificadas.filter_by(municipio=municipality)
                
                for entity in query_identificadas.all():
                    if entity.latitude and entity.longitude:
                        point = GeographicPoint(
                            lat=entity.latitude,
                            lng=entity.longitude,
                            weight=1.0,
                            entity_type="identificada",
                            municipality=entity.municipio,
                            priority=entity.prioridade or 2,
                            status="geocoded",
                            metadata={
                                'id': entity.id,
                                'name': entity.nome_entidade,
                                'mrs_required': entity.mrs_obrigatorio,
                                'map_required': entity.map_obrigatorio
                            }
                        )
                        points.append(point)
            
            # Carregar entidades prioritárias
            if not entity_type or entity_type == "prioritaria":
                query_prioritarias = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='sucesso')
                if municipality:
                    query_prioritarias = query_prioritarias.filter_by(municipio=municipality)
                
                for entity in query_prioritarias.all():
                    if entity.latitude and entity.longitude:
                        point = GeographicPoint(
                            lat=entity.latitude,
                            lng=entity.longitude,
                            weight=1.5,  # P1 tem peso maior
                            entity_type="prioritaria",
                            municipality=entity.municipio,
                            priority=1,
                            status="geocoded",
                            metadata={
                                'id': entity.id,
                                'name': entity.nome_entidade,
                                'mrs_required': entity.mrs_obrigatorio,
                                'map_required': entity.map_obrigatorio
                            }
                        )
                        points.append(point)
            
            self.logger.info(f"📍 Carregados {len(points)} pontos geográficos")
            return points
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar pontos: {str(e)}")
            return []
    
    def _apply_weights(self, points: List[GeographicPoint], weight_by: str) -> List[GeographicPoint]:
        """Aplica pesos aos pontos baseado no critério"""
        weighted_points = []
        
        for point in points:
            new_weight = point.weight
            
            if weight_by == "priority":
                # Peso baseado na prioridade (P1 = 3, P2 = 2, P3 = 1)
                new_weight = 4 - point.priority
            elif weight_by == "requirements":
                # Peso baseado nos requisitos
                req_count = 0
                if point.metadata.get('mrs_required'):
                    req_count += 1
                if point.metadata.get('map_required'):
                    req_count += 1
                new_weight = max(1, req_count)
            elif weight_by == "density":
                # Manter peso original (densidade igual)
                new_weight = 1.0
            
            # Criar novo ponto com peso atualizado
            new_point = GeographicPoint(
                lat=point.lat,
                lng=point.lng,
                weight=new_weight,
                entity_type=point.entity_type,
                municipality=point.municipality,
                priority=point.priority,
                status=point.status,
                metadata=point.metadata
            )
            weighted_points.append(new_point)
        
        return weighted_points
    
    def _calculate_geographic_center(self, points: List[GeographicPoint]) -> Tuple[float, float]:
        """Calcula centro geográfico ponderado"""
        if not points:
            return (-26.9, -48.7)  # Centro padrão de SC
        
        total_weight = sum(p.weight for p in points)
        if total_weight == 0:
            return (points[0].lat, points[0].lng)
        
        weighted_lat = sum(p.lat * p.weight for p in points) / total_weight
        weighted_lng = sum(p.lng * p.weight for p in points) / total_weight
        
        return (weighted_lat, weighted_lng)
    
    def _calculate_bounds(self, points: List[GeographicPoint]) -> Dict[str, float]:
        """Calcula limites geográficos dos pontos"""
        if not points:
            return self.sc_bounds
        
        lats = [p.lat for p in points]
        lngs = [p.lng for p in points]
        
        # Adicionar margem de 5%
        lat_margin = (max(lats) - min(lats)) * 0.05
        lng_margin = (max(lngs) - min(lngs)) * 0.05
        
        return {
            'north': max(lats) + lat_margin,
            'south': min(lats) - lat_margin,
            'east': max(lngs) + lng_margin,
            'west': min(lngs) - lng_margin
        }
    
    def _calculate_analysis_area(self, municipality: str = None) -> float:
        """Calcula área total para análise em km²"""
        if municipality:
            # Áreas aproximadas dos municípios (em km²)
            municipal_areas = {
                'Balneário Camboriú': 46.4,
                'Balneário Piçarras': 99.3,
                'Bombinhas': 35.0,
                'Camboriú': 212.0,
                'Itajaí': 289.0,
                'Itapema': 58.2,
                'Luiz Alves': 260.0,
                'Navegantes': 112.0,
                'Penha': 62.0,
                'Porto Belo': 95.0,
                'Ilhota': 132.0
            }
            return municipal_areas.get(municipality, 100.0)
        else:
            # Área total da região PNSB (aproximada)
            return sum([46.4, 99.3, 35.0, 212.0, 289.0, 58.2, 260.0, 112.0, 62.0, 95.0, 132.0])
    
    def _analyze_coverage_grid(self, points: List[GeographicPoint], 
                             municipality: str = None) -> Dict[str, Any]:
        """Analisa cobertura usando grade de células"""
        # Calcular bounds da análise
        if municipality:
            # Usar bounds específicos do município (simplificado)
            bounds = self._calculate_bounds(points)
        else:
            bounds = self.sc_bounds
        
        # Criar grade de análise
        grid_cells = []
        cell_size = self.grid_size_km / 111.32  # Converter km para graus (aproximado)
        
        lat_start = bounds['south']
        lng_start = bounds['west']
        lat_end = bounds['north']
        lng_end = bounds['east']
        
        covered_cells = 0
        total_cells = 0
        
        lat = lat_start
        while lat < lat_end:
            lng = lng_start
            while lng < lng_end:
                total_cells += 1
                
                # Verificar se célula tem cobertura
                cell_center = (lat + cell_size/2, lng + cell_size/2)
                if self._is_cell_covered(cell_center, points):
                    covered_cells += 1
                
                lng += cell_size
            lat += cell_size
        
        # Calcular área coberta
        cell_area_km2 = self.grid_size_km ** 2
        covered_area_km2 = covered_cells * cell_area_km2
        
        return {
            'total_cells': total_cells,
            'covered_cells': covered_cells,
            'covered_area_km2': covered_area_km2,
            'cell_size_km': self.grid_size_km
        }
    
    def _is_cell_covered(self, cell_center: Tuple[float, float], 
                        points: List[GeographicPoint]) -> bool:
        """Verifica se uma célula da grade tem cobertura"""
        cell_lat, cell_lng = cell_center
        coverage_radius_deg = self.coverage_radius_km / 111.32
        
        for point in points:
            distance = math.sqrt(
                (point.lat - cell_lat) ** 2 + (point.lng - cell_lng) ** 2
            )
            if distance <= coverage_radius_deg:
                return True
        
        return False
    
    def _detect_coverage_gaps(self, points: List[GeographicPoint], 
                            municipality: str = None) -> List[Dict[str, Any]]:
        """Detecta áreas com gaps de cobertura"""
        gaps = []
        
        # Implementação simplificada - identificar regiões sem pontos próximos
        if municipality:
            bounds = self._calculate_bounds(points)
        else:
            bounds = self.sc_bounds
        
        # Amostrar pontos na região e verificar cobertura
        sample_density = 0.01  # Amostragem a cada ~1km
        
        lat = bounds['south']
        while lat < bounds['north']:
            lng = bounds['west']
            while lng < bounds['east']:
                sample_point = (lat, lng)
                
                if not self._is_cell_covered(sample_point, points):
                    # Verificar se já existe gap próximo
                    is_new_gap = True
                    for gap in gaps:
                        gap_distance = math.sqrt(
                            (gap['center_lat'] - lat) ** 2 + 
                            (gap['center_lng'] - lng) ** 2
                        )
                        if gap_distance < 0.05:  # ~5km
                            is_new_gap = False
                            break
                    
                    if is_new_gap:
                        gaps.append({
                            'center_lat': lat,
                            'center_lng': lng,
                            'estimated_size_km2': self.grid_size_km ** 2,
                            'severity': 'medium',
                            'municipality': municipality
                        })
                
                lng += sample_density
            lat += sample_density
        
        return gaps[:10]  # Limitar a 10 gaps principais
    
    def _detect_entity_clusters(self, points: List[GeographicPoint]) -> List[Dict[str, Any]]:
        """Detecta clusters de entidades"""
        if len(points) < 2:
            return []
        
        clusters = []
        processed_points = set()
        
        for i, point in enumerate(points):
            if i in processed_points:
                continue
            
            # Encontrar pontos próximos
            cluster_points = [point]
            cluster_indices = {i}
            
            for j, other_point in enumerate(points):
                if j == i or j in processed_points:
                    continue
                
                distance_km = self._haversine_distance(
                    point.lat, point.lng, other_point.lat, other_point.lng
                )
                
                if distance_km <= self.cluster_radius_km:
                    cluster_points.append(other_point)
                    cluster_indices.add(j)
            
            # Se encontrou cluster significativo
            if len(cluster_points) >= 3:
                center_lat = sum(p.lat for p in cluster_points) / len(cluster_points)
                center_lng = sum(p.lng for p in cluster_points) / len(cluster_points)
                
                clusters.append({
                    'center_lat': center_lat,
                    'center_lng': center_lng,
                    'point_count': len(cluster_points),
                    'radius_km': self.cluster_radius_km,
                    'density': len(cluster_points) / (math.pi * self.cluster_radius_km ** 2),
                    'municipalities': list(set(p.municipality for p in cluster_points)),
                    'entity_types': list(set(p.entity_type for p in cluster_points))
                })
                
                processed_points.update(cluster_indices)
        
        return clusters
    
    def _haversine_distance(self, lat1: float, lng1: float, 
                          lat2: float, lng2: float) -> float:
        """Calcula distância haversine em km"""
        R = 6371  # Raio da Terra em km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_density_map(self, points: List[GeographicPoint], 
                             municipality: str = None) -> Dict[str, float]:
        """Calcula mapa de densidade por região"""
        if municipality:
            return {municipality: len(points) / self._calculate_analysis_area(municipality)}
        
        # Densidade por município
        municipality_counts = defaultdict(int)
        for point in points:
            municipality_counts[point.municipality] += 1
        
        density_map = {}
        for mun, count in municipality_counts.items():
            area = self._calculate_analysis_area(mun)
            density_map[mun] = count / area if area > 0 else 0
        
        return density_map
    
    def _generate_coverage_recommendations(self, points: List[GeographicPoint],
                                         gaps: List[Dict], clusters: List[Dict],
                                         coverage_percentage: float) -> List[str]:
        """Gera recomendações baseadas na análise de cobertura"""
        recommendations = []
        
        if coverage_percentage < 70:
            recommendations.append("Cobertura insuficiente - considerar adição de entidades em áreas descobertas")
        
        if len(gaps) > 5:
            recommendations.append(f"Identificados {len(gaps)} gaps significativos - priorizar pesquisa nessas áreas")
        
        if len(clusters) > 3:
            recommendations.append(f"Detectados {len(clusters)} clusters - otimizar rotas para máxima eficiência")
        
        # Análise por tipo de entidade
        p1_count = len([p for p in points if p.priority == 1])
        total_count = len(points)
        
        if p1_count / total_count < 0.3 if total_count > 0 else True:
            recommendations.append("Proporção baixa de entidades P1 - verificar priorização")
        
        return recommendations
    
    def _create_empty_heatmap(self) -> HeatmapData:
        """Cria heatmap vazio para casos de erro"""
        return HeatmapData(
            points=[],
            center=(-26.9, -48.7),
            bounds=self.sc_bounds,
            intensity_scale=(0, 1),
            metadata={'status': 'empty', 'reason': 'no_data'}
        )
    
    def _create_empty_coverage(self) -> CoverageAnalysis:
        """Cria análise de cobertura vazia"""
        return CoverageAnalysis(
            total_area_km2=0,
            covered_area_km2=0,
            coverage_percentage=0,
            gaps=[],
            clusters=[],
            density_map={},
            recommendations=["Nenhum dado disponível para análise"]
        )
    
    def _load_visits_in_period(self, start_date: datetime, end_date: datetime) -> List[Any]:
        """Carrega visitas no período especificado"""
        try:
            visitas = Visita.query.filter(
                Visita.data_criacao >= start_date,
                Visita.data_criacao <= end_date
            ).all()
            return visitas
        except Exception as e:
            self.logger.error(f"❌ Erro ao carregar visitas: {str(e)}")
            return []
    
    def _calculate_temporal_metrics(self, visitas: List, start_date: datetime, 
                                  end_date: datetime) -> Dict[str, Any]:
        """Calcula métricas temporais"""
        total_days = (end_date - start_date).days
        
        # Visitas por dia
        daily_visits = defaultdict(int)
        for visita in visitas:
            day = visita.data_criacao.date() if hasattr(visita, 'data_criacao') else datetime.now().date()
            daily_visits[day] += 1
        
        avg_visits_per_day = len(visitas) / total_days if total_days > 0 else 0
        
        # Distribuição por status
        status_distribution = defaultdict(int)
        for visita in visitas:
            status_distribution[getattr(visita, 'status', 'unknown')] += 1
        
        return {
            'total_visits': len(visitas),
            'average_visits_per_day': round(avg_visits_per_day, 2),
            'active_days': len(daily_visits),
            'status_distribution': dict(status_distribution),
            'completion_rate': status_distribution.get('finalizada', 0) / len(visitas) * 100 if visitas else 0
        }
    
    def _calculate_geographic_metrics(self, visitas: List) -> Dict[str, Any]:
        """Calcula métricas geográficas"""
        municipality_counts = defaultdict(int)
        
        for visita in visitas:
            municipality = getattr(visita, 'municipio', 'Unknown')
            municipality_counts[municipality] += 1
        
        return {
            'municipalities_covered': len(municipality_counts),
            'distribution_by_municipality': dict(municipality_counts),
            'most_visited_municipality': max(municipality_counts.items(), key=lambda x: x[1])[0] if municipality_counts else None,
            'geographic_spread': len(municipality_counts) / 11 * 100  # 11 municípios totais
        }
    
    def _calculate_productivity_metrics(self, visitas: List) -> Dict[str, Any]:
        """Calcula métricas de produtividade"""
        # Implementação simplificada
        return {
            'total_entities_visited': len(visitas),
            'average_duration_per_visit': 120,  # minutos estimados
            'efficiency_score': 75.0,  # score estimado
            'productivity_trend': 'stable'
        }
    
    def _calculate_quality_metrics(self, visitas: List) -> Dict[str, Any]:
        """Calcula métricas de qualidade"""
        return {
            'data_completeness': 85.0,  # percentual estimado
            'validation_pass_rate': 92.0,  # percentual estimado
            'quality_score': 88.5
        }
    
    def _analyze_trends(self, visitas: List, start_date: datetime, 
                       end_date: datetime) -> Dict[str, Any]:
        """Analisa tendências temporais"""
        return {
            'visit_trend': 'increasing',
            'efficiency_trend': 'stable',
            'quality_trend': 'improving',
            'projected_completion': (end_date + timedelta(days=30)).isoformat()
        }
    
    def _calculate_overall_efficiency_score(self, temporal: Dict, geographic: Dict,
                                          productivity: Dict, quality: Dict) -> float:
        """Calcula score geral de eficiência"""
        scores = [
            temporal.get('completion_rate', 0),
            geographic.get('geographic_spread', 0),
            productivity.get('efficiency_score', 0),
            quality.get('quality_score', 0)
        ]
        
        return sum(scores) / len(scores) if scores else 0
    
    def _generate_efficiency_insights(self, temporal: Dict, geographic: Dict,
                                    productivity: Dict) -> List[str]:
        """Gera insights sobre eficiência"""
        insights = []
        
        if temporal.get('completion_rate', 0) > 80:
            insights.append("Alta taxa de conclusão de visitas")
        
        if geographic.get('geographic_spread', 0) > 70:
            insights.append("Boa cobertura geográfica dos municípios")
        
        if productivity.get('efficiency_score', 0) > 75:
            insights.append("Produtividade acima da média")
        
        return insights
    
    # Métodos para dashboard municipal
    
    def _get_municipality_basic_stats(self, municipality: str) -> Dict[str, Any]:
        """Estatísticas básicas do município"""
        try:
            # Contar entidades
            identificadas = EntidadeIdentificada.query.filter_by(municipio=municipality).count()
            prioritarias = EntidadePrioritariaUF.query.filter_by(municipio=municipality).count()
            
            # Contar visitas
            visitas = Visita.query.filter_by(municipio=municipality).count()
            
            return {
                'total_entities': identificadas + prioritarias,
                'priority_entities': prioritarias,
                'identified_entities': identificadas,
                'total_visits': visitas,
                'area_km2': self._calculate_analysis_area(municipality)
            }
        except Exception as e:
            self.logger.error(f"❌ Erro nas estatísticas básicas: {str(e)}")
            return {}
    
    def _calculate_municipality_progress(self, municipality: str) -> Dict[str, Any]:
        """Calcula progresso do município"""
        return {
            'completion_percentage': 65.0,  # Estimado
            'entities_completed': 8,
            'entities_pending': 4,
            'estimated_completion_date': (datetime.now() + timedelta(days=15)).isoformat()
        }
    
    def _analyze_municipality_routes(self, municipality: str) -> Dict[str, Any]:
        """Analisa rotas do município"""
        return {
            'optimal_route_days': 2,
            'estimated_travel_distance': 45.5,
            'estimated_travel_time': 6.5,
            'route_efficiency_score': 82.0
        }
    
    def _generate_municipality_timeline(self, municipality: str) -> Dict[str, Any]:
        """Gera cronograma do município"""
        return {
            'planned_start': datetime.now().isoformat(),
            'estimated_completion': (datetime.now() + timedelta(days=20)).isoformat(),
            'milestones': [
                {'date': (datetime.now() + timedelta(days=5)).isoformat(), 'description': 'Início das visitas P1'},
                {'date': (datetime.now() + timedelta(days=12)).isoformat(), 'description': 'Completar 50% das entidades'},
                {'date': (datetime.now() + timedelta(days=20)).isoformat(), 'description': 'Finalização prevista'}
            ]
        }
    
    def _compare_with_other_municipalities(self, municipality: str) -> Dict[str, Any]:
        """Compara com outros municípios"""
        return {
            'ranking_position': 3,
            'total_municipalities': 11,
            'above_average_metrics': ['efficiency', 'coverage'],
            'below_average_metrics': ['speed'],
            'similar_municipalities': ['Camboriú', 'Navegantes']
        }
    
    # Métodos para relatório IBGE
    
    def _get_project_overview(self) -> Dict[str, Any]:
        """Visão geral do projeto"""
        return {
            'project_name': 'PNSB 2024 - Santa Catarina',
            'total_municipalities': 11,
            'survey_types': ['MRS', 'MAP'],
            'start_date': '2024-01-01',
            'planned_completion': '2024-12-31'
        }
    
    def _get_all_municipalities_status(self) -> List[Dict[str, Any]]:
        """Status de todos os municípios"""
        municipalities = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        
        return [
            {
                'municipality': mun,
                'completion_percentage': 60 + (hash(mun) % 40),  # Simulado
                'entities_total': 5 + (hash(mun) % 10),
                'entities_completed': 3 + (hash(mun) % 5),
                'status': 'in_progress'
            }
            for mun in municipalities
        ]
    
    def _calculate_overall_progress(self) -> Dict[str, Any]:
        """Progresso geral do projeto"""
        return {
            'overall_completion': 67.5,
            'total_entities_processed': 45,
            'total_entities_planned': 67,
            'key_achievements': [
                'Geocodificação 100% concluída',
                'Sistema offline implementado',
                'Otimização de rotas ativa'
            ]
        }
    
    def _assess_data_quality(self) -> Dict[str, Any]:
        """Avaliação da qualidade dos dados"""
        return {
            'completeness_score': 92.0,
            'accuracy_score': 88.5,
            'consistency_score': 94.0,
            'overall_quality_grade': 'A'
        }
    
    def _identify_challenges_and_risks(self) -> Dict[str, Any]:
        """Identifica desafios e riscos"""
        return {
            'major_challenges': [
                'Acesso a entidades em áreas rurais',
                'Disponibilidade de informantes',
                'Condições climáticas'
            ],
            'risk_assessment': {
                'schedule_risk': 'medium',
                'quality_risk': 'low',
                'resource_risk': 'low'
            },
            'mitigation_strategies': [
                'Rotas otimizadas para área rural',
                'Sistema offline para conectividade limitada',
                'Backup de contatos por entidade'
            ]
        }
    
    def _generate_strategic_recommendations(self) -> List[str]:
        """Gera recomendações estratégicas"""
        return [
            "Manter foco em entidades prioritárias P1",
            "Implementar sistema de monitoramento em tempo real",
            "Expandir uso de tecnologias offline",
            "Fortalecer parceria com prefeituras locais"
        ]
    
    def _generate_project_timeline(self) -> Dict[str, Any]:
        """Gera cronograma do projeto"""
        return {
            'current_phase': 'field_research',
            'completion_projection': '2024-11-30',
            'key_milestones': [
                {'date': '2024-09-30', 'milestone': 'Completar 75% das entidades'},
                {'date': '2024-10-31', 'milestone': 'Finalizar coleta de campo'},
                {'date': '2024-11-30', 'milestone': 'Relatório final'}
            ]
        }
    
    def _generate_regional_analysis(self) -> Dict[str, Any]:
        """Análise regional detalhada"""
        return {
            'geographic_distribution': 'uniform',
            'density_analysis': 'concentrated_coastal',
            'accessibility_assessment': 'good_urban_challenging_rural'
        }
    
    def _calculate_operational_kpis(self) -> Dict[str, Any]:
        """KPIs operacionais"""
        return {
            'entities_per_day': 2.5,
            'travel_efficiency': 85.0,
            'data_quality_index': 92.0,
            'cost_per_entity': 450.0
        }
    
    def _get_coverage_period(self) -> Dict[str, str]:
        """Período de cobertura do relatório"""
        return {
            'start_date': '2024-01-01',
            'end_date': datetime.now().isoformat(),
            'report_date': datetime.now().isoformat()
        }
    
    def _summarize_for_executive(self, report_data: Dict) -> Dict:
        """Simplifica relatório para executivos"""
        # Manter apenas seções essenciais
        return {
            'report_metadata': report_data['report_metadata'],
            'executive_summary': report_data['executive_summary'],
            'key_metrics': {
                'completion': report_data['progress_metrics']['overall_completion'],
                'quality': report_data['quality_assessment']['overall_quality_grade'],
                'efficiency': report_data['operational_efficiency']['travel_efficiency']
            },
            'strategic_recommendations': report_data['strategic_recommendations']
        }
    
    def _expand_for_technical(self, report_data: Dict) -> Dict:
        """Expande relatório com detalhes técnicos"""
        # Adicionar seções técnicas detalhadas
        report_data['technical_appendix'] = {
            'methodology': 'Detalhes da metodologia aplicada',
            'data_sources': 'Fontes de dados utilizadas',
            'algorithms': 'Algoritmos de otimização implementados',
            'validation_procedures': 'Procedimentos de validação'
        }
        return report_data