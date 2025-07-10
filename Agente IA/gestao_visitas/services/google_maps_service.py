"""
Sistema de Google Maps Funcional para o Projeto PNSB 2024
Gerencia marcadores, rotas, clustering e visualizações do mapa
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime, timedelta
import math

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.contatos import Contato
from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
from gestao_visitas.db import db
from gestao_visitas.config import MUNICIPIOS

# Configuração do logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Coordenadas reais dos municípios PNSB
COORDENADAS_MUNICIPIOS = {
    'Balneário Camboriú': {'lat': -26.9906, 'lng': -48.6347},
    'Balneário Piçarras': {'lat': -26.7632, 'lng': -48.6719},
    'Bombinhas': {'lat': -27.1392, 'lng': -48.5158},
    'Camboriú': {'lat': -27.0252, 'lng': -48.6541},
    'Itajaí': {'lat': -26.9078, 'lng': -48.6619},
    'Itapema': {'lat': -27.0903, 'lng': -48.6111},
    'Luiz Alves': {'lat': -26.7205, 'lng': -48.9303},
    'Navegantes': {'lat': -26.8989, 'lng': -48.6544},
    'Penha': {'lat': -26.7694, 'lng': -48.6453},
    'Porto Belo': {'lat': -27.1578, 'lng': -48.5528},
    'Ilhota': {'lat': -26.9014, 'lng': -48.8275}
}

class MarkerType(Enum):
    """Tipos de marcadores no mapa"""
    PREFEITURA = "prefeitura"
    EMPRESA_LIMPEZA = "empresa_limpeza"
    COOPERATIVA = "cooperativa"
    OUTROS = "outros"
    CLUSTER = "cluster"

class MarkerStatus(Enum):
    """Status dos marcadores baseado no progresso"""
    FINALIZADO = "finalizado"
    EM_FOLLOWUP = "em_followup"
    EXECUTADO = "executado"
    AGENDADO = "agendado"
    SEM_VISITA = "sem_visita"
    CRITICO = "critico"

@dataclass
class MapMarker:
    """Representa um marcador no mapa"""
    id: str
    tipo: MarkerType
    status: MarkerStatus
    latitude: float
    longitude: float
    municipio: str
    titulo: str
    descricao: str
    dados: Dict
    prioridade: str  # P1, P2, P3
    icone: str
    cor: str

@dataclass
class MapRoute:
    """Representa uma rota no mapa"""
    id: str
    origem: Dict[str, float]
    destino: Dict[str, float]
    waypoints: List[Dict[str, float]]
    distancia_km: float
    duracao_minutos: int
    visitas: List[str]
    otimizada: bool

class GoogleMapsService:
    """
    Sistema de Google Maps Funcional para PNSB 2024
    
    Gerencia todos os aspectos do mapa incluindo marcadores,
    rotas, clustering, heatmaps e visualizações interativas.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.municipios_coords = COORDENADAS_MUNICIPIOS
        logger.info("GoogleMapsService inicializado com sucesso")
    
    def get_map_data(self) -> Dict:
        """
        Retorna todos os dados necessários para o mapa
        
        Returns:
            Dict com marcadores, configurações e estatísticas
        """
        try:
            logger.info("Gerando dados para o mapa PNSB")
            
            # Obter todos os marcadores
            marcadores = self._generate_all_markers()
            
            # Calcular centro e zoom ideais
            centro, zoom = self._calculate_map_center_zoom(marcadores)
            
            # Gerar clusters se necessário
            clusters = self._generate_clusters(marcadores) if len(marcadores) > 20 else []
            
            # Obter rotas otimizadas
            rotas = self._get_optimized_routes()
            
            # Gerar dados para heatmap
            heatmap_data = self._generate_heatmap_data()
            
            # Estatísticas do mapa
            estatisticas = self._calculate_map_statistics(marcadores)
            
            result = {
                'marcadores': [self._marker_to_dict(m) for m in marcadores],
                'clusters': clusters,
                'rotas': rotas,
                'heatmap': heatmap_data,
                'configuracoes': {
                    'centro': centro,
                    'zoom': zoom,
                    'tipo_mapa': 'roadmap',
                    'estilos': self._get_map_styles()
                },
                'estatisticas': estatisticas,
                'filtros_disponiveis': {
                    'status': [s.value for s in MarkerStatus],
                    'tipo': [t.value for t in MarkerType],
                    'prioridade': ['P1', 'P2', 'P3'],
                    'municipio': list(MUNICIPIOS)
                }
            }
            
            logger.info(f"Dados do mapa gerados: {len(marcadores)} marcadores")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao gerar dados do mapa: {e}")
            raise
    
    def _generate_all_markers(self) -> List[MapMarker]:
        """Gera todos os marcadores para o mapa"""
        marcadores = []
        
        for municipio in MUNICIPIOS:
            coords = self.municipios_coords.get(municipio)
            if not coords:
                continue
            
            # Obter dados do município
            visitas = Visita.query.filter_by(municipio=municipio).all()
            progresso_obj = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            # Converter para dicionário se necessário
            if hasattr(progresso_obj, '__dict__'):
                progresso_dict = progresso_obj.__dict__
            else:
                progresso_dict = progresso_obj or {}
            
            # Agrupar visitas por tipo
            visitas_por_tipo = {}
            for visita in visitas:
                tipo = visita.tipo_informante or 'prefeitura'
                if tipo not in visitas_por_tipo:
                    visitas_por_tipo[tipo] = []
                visitas_por_tipo[tipo].append(visita)
            
            # Criar marcador principal do município
            status = self._determine_municipio_status(visitas, progresso_dict)
            cor = self._get_status_color(status)
            
            marcador_principal = MapMarker(
                id=f"municipio_{municipio.lower().replace(' ', '_')}",
                tipo=MarkerType.PREFEITURA,
                status=status,
                latitude=coords['lat'],
                longitude=coords['lng'],
                municipio=municipio,
                titulo=municipio,
                descricao=self._generate_marker_description(municipio, visitas, progresso_dict),
                dados={
                    'total_visitas': len(visitas),
                    'visitas_finalizadas': len([v for v in visitas if v.status == 'finalizada']),
                    'progresso_mrs': progresso_dict.get('percentual_mrs', 0),
                    'progresso_map': progresso_dict.get('percentual_map', 0),
                    'prioridades': progresso_dict.get('prioridades', {})
                },
                prioridade=self._determine_prioridade(progresso_dict),
                icone=self._get_marker_icon(status, MarkerType.PREFEITURA),
                cor=cor
            )
            marcadores.append(marcador_principal)
            
            # Criar marcadores secundários para entidades específicas
            for tipo, visitas_tipo in visitas_por_tipo.items():
                if tipo != 'prefeitura' and visitas_tipo:
                    # Offset pequeno para não sobrepor marcadores
                    offset_lat = 0.01 * (hash(tipo) % 5 - 2) / 100
                    offset_lng = 0.01 * (hash(tipo) % 5 - 2) / 100
                    
                    marker_tipo = self._tipo_to_marker_type(tipo)
                    status_tipo = self._determine_entity_status(visitas_tipo)
                    
                    marcador_entidade = MapMarker(
                        id=f"{municipio}_{tipo}".lower().replace(' ', '_'),
                        tipo=marker_tipo,
                        status=status_tipo,
                        latitude=coords['lat'] + offset_lat,
                        longitude=coords['lng'] + offset_lng,
                        municipio=municipio,
                        titulo=f"{tipo.title()} - {municipio}",
                        descricao=f"{len(visitas_tipo)} visitas registradas",
                        dados={
                            'tipo_entidade': tipo,
                            'total_visitas': len(visitas_tipo),
                            'visitas_finalizadas': len([v for v in visitas_tipo if v.status == 'finalizada'])
                        },
                        prioridade='P2' if tipo in ['empresa_limpeza', 'cooperativa'] else 'P3',
                        icone=self._get_marker_icon(status_tipo, marker_tipo),
                        cor=self._get_status_color(status_tipo)
                    )
                    marcadores.append(marcador_entidade)
        
        return marcadores
    
    def _determine_municipio_status(self, visitas: List[Visita], progresso: Dict) -> MarkerStatus:
        """Determina o status do município baseado nas visitas e progresso"""
        if not visitas:
            return MarkerStatus.SEM_VISITA
        
        # Verificar progresso dos questionários
        progresso_total = (progresso.get('percentual_mrs', 0) + progresso.get('percentual_map', 0)) / 2
        
        if progresso_total >= 100:
            return MarkerStatus.FINALIZADO
        elif progresso_total >= 50:
            return MarkerStatus.EM_FOLLOWUP
        
        # Verificar status das visitas
        visitas_finalizadas = len([v for v in visitas if v.status == 'finalizada'])
        visitas_em_andamento = len([v for v in visitas if v.status in ['em follow-up', 'verificação whatsapp']])
        
        if visitas_finalizadas > 0:
            return MarkerStatus.EXECUTADO
        elif visitas_em_andamento > 0:
            return MarkerStatus.EM_FOLLOWUP
        else:
            return MarkerStatus.AGENDADO
    
    def _determine_entity_status(self, visitas: List[Visita]) -> MarkerStatus:
        """Determina o status de uma entidade específica"""
        if not visitas:
            return MarkerStatus.SEM_VISITA
        
        # Pegar status da visita mais recente
        visita_recente = max(visitas, key=lambda v: v.data_atualizacao or v.data_criacao)
        
        status_map = {
            'finalizada': MarkerStatus.FINALIZADO,
            'em follow-up': MarkerStatus.EM_FOLLOWUP,
            'verificação whatsapp': MarkerStatus.EM_FOLLOWUP,
            'realizada': MarkerStatus.EXECUTADO,
            'agendada': MarkerStatus.AGENDADO,
            'em preparação': MarkerStatus.AGENDADO
        }
        
        return status_map.get(visita_recente.status, MarkerStatus.AGENDADO)
    
    def _get_status_color(self, status: MarkerStatus) -> str:
        """Retorna a cor hexadecimal para cada status"""
        colors = {
            MarkerStatus.FINALIZADO: '#28a745',     # Verde
            MarkerStatus.EM_FOLLOWUP: '#ffc107',    # Amarelo
            MarkerStatus.EXECUTADO: '#17a2b8',      # Azul
            MarkerStatus.AGENDADO: '#6c757d',       # Cinza
            MarkerStatus.SEM_VISITA: '#dc3545',     # Vermelho
            MarkerStatus.CRITICO: '#ff0000'         # Vermelho forte
        }
        return colors.get(status, '#6c757d')
    
    def _get_marker_icon(self, status: MarkerStatus, tipo: MarkerType) -> str:
        """Retorna o ícone apropriado para o marcador"""
        # Ícones base por tipo
        base_icons = {
            MarkerType.PREFEITURA: 'building',
            MarkerType.EMPRESA_LIMPEZA: 'truck',
            MarkerType.COOPERATIVA: 'people',
            MarkerType.OUTROS: 'place',
            MarkerType.CLUSTER: 'group_work'
        }
        
        # Modificadores por status
        if status == MarkerStatus.FINALIZADO:
            return f"{base_icons[tipo]}_check"
        elif status == MarkerStatus.CRITICO:
            return f"{base_icons[tipo]}_alert"
        else:
            return base_icons[tipo]
    
    def _generate_marker_description(self, municipio: str, visitas: List[Visita], progresso: Dict) -> str:
        """Gera descrição detalhada para o marcador"""
        total_visitas = len(visitas)
        finalizadas = len([v for v in visitas if v.status == 'finalizada'])
        
        desc = f"<strong>{municipio}</strong><br>"
        desc += f"Visitas: {finalizadas}/{total_visitas}<br>"
        desc += f"MRS: {progresso.get('percentual_mrs', 0):.1f}%<br>"
        desc += f"MAP: {progresso.get('percentual_map', 0):.1f}%<br>"
        
        # Adicionar informações de prioridade
        prioridades = progresso.get('prioridades', {})
        if prioridades.get('p1', {}).get('total_entidades', 0) > 0:
            desc += f"<span style='color: #dc3545'>P1: {prioridades['p1']['total_entidades']} entidades</span><br>"
        if prioridades.get('p2', {}).get('total_entidades', 0) > 0:
            desc += f"<span style='color: #ffc107'>P2: {prioridades['p2']['total_entidades']} entidades</span><br>"
        
        return desc
    
    def _determine_prioridade(self, progresso: Dict) -> str:
        """Determina a prioridade do município"""
        prioridades = progresso.get('prioridades', {})
        
        if prioridades.get('p1', {}).get('total_entidades', 0) > 0:
            return 'P1'
        elif prioridades.get('p2', {}).get('total_entidades', 0) > 0:
            return 'P2'
        else:
            return 'P3'
    
    def _tipo_to_marker_type(self, tipo: str) -> MarkerType:
        """Converte tipo de entidade para tipo de marcador"""
        tipo_map = {
            'empresa_limpeza': MarkerType.EMPRESA_LIMPEZA,
            'cooperativa': MarkerType.COOPERATIVA,
            'prefeitura': MarkerType.PREFEITURA
        }
        return tipo_map.get(tipo.lower(), MarkerType.OUTROS)
    
    def _calculate_map_center_zoom(self, marcadores: List[MapMarker]) -> Tuple[Dict[str, float], int]:
        """Calcula centro e zoom ideais para mostrar todos os marcadores"""
        if not marcadores:
            # Centro padrão em Santa Catarina
            return {'lat': -26.9, 'lng': -48.65}, 10
        
        # Calcular bounds
        lats = [m.latitude for m in marcadores]
        lngs = [m.longitude for m in marcadores]
        
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        
        # Centro
        center = {
            'lat': (min_lat + max_lat) / 2,
            'lng': (min_lng + max_lng) / 2
        }
        
        # Calcular zoom baseado na distância
        lat_diff = max_lat - min_lat
        lng_diff = max_lng - min_lng
        max_diff = max(lat_diff, lng_diff)
        
        if max_diff < 0.1:
            zoom = 12
        elif max_diff < 0.5:
            zoom = 11
        elif max_diff < 1:
            zoom = 10
        else:
            zoom = 9
        
        return center, zoom
    
    def _generate_clusters(self, marcadores: List[MapMarker]) -> List[Dict]:
        """Gera clusters para marcadores próximos"""
        # Implementação simplificada de clustering
        # Em produção, usar algoritmo mais sofisticado
        clusters = []
        cluster_radius = 0.05  # ~5km
        
        used_markers = set()
        
        for i, marker in enumerate(marcadores):
            if marker.id in used_markers:
                continue
            
            cluster_markers = [marker]
            used_markers.add(marker.id)
            
            # Encontrar marcadores próximos
            for j, other in enumerate(marcadores[i+1:], i+1):
                if other.id in used_markers:
                    continue
                
                distance = self._calculate_distance(
                    marker.latitude, marker.longitude,
                    other.latitude, other.longitude
                )
                
                if distance < cluster_radius:
                    cluster_markers.append(other)
                    used_markers.add(other.id)
            
            # Criar cluster se houver múltiplos marcadores
            if len(cluster_markers) > 1:
                cluster_lat = sum(m.latitude for m in cluster_markers) / len(cluster_markers)
                cluster_lng = sum(m.longitude for m in cluster_markers) / len(cluster_markers)
                
                clusters.append({
                    'id': f"cluster_{len(clusters)}",
                    'lat': cluster_lat,
                    'lng': cluster_lng,
                    'count': len(cluster_markers),
                    'markers': [m.id for m in cluster_markers]
                })
        
        return clusters
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância entre dois pontos em graus"""
        return math.sqrt((lat2 - lat1)**2 + (lon2 - lon1)**2)
    
    def _get_optimized_routes(self) -> List[Dict]:
        """Retorna rotas otimizadas para visitas"""
        # Por enquanto, retornar rotas vazias
        # Implementar integração com serviço de rotas
        return []
    
    def _generate_heatmap_data(self) -> Dict:
        """Gera dados para o heatmap de intensidade"""
        heatmap_points = []
        
        for municipio in MUNICIPIOS:
            coords = self.municipios_coords.get(municipio)
            if not coords:
                continue
            
            # Calcular intensidade baseada no progresso
            progresso_obj = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
            
            # Converter para dicionário se necessário
            if hasattr(progresso_obj, '__dict__'):
                progresso_dict = progresso_obj.__dict__
            else:
                progresso_dict = progresso_obj or {}
            
            progresso_total = (progresso_dict.get('percentual_mrs', 0) + progresso_dict.get('percentual_map', 0)) / 2
            
            # Inverter intensidade (menos progresso = mais intenso)
            intensidade = max(0.1, 1 - (progresso_total / 100))
            
            heatmap_points.append({
                'lat': coords['lat'],
                'lng': coords['lng'],
                'weight': intensidade,
                'municipio': municipio
            })
        
        return {
            'points': heatmap_points,
            'radius': 30,
            'opacity': 0.6,
            'gradient': {
                '0': 'green',
                '0.5': 'yellow',
                '1': 'red'
            }
        }
    
    def _calculate_map_statistics(self, marcadores: List[MapMarker]) -> Dict:
        """Calcula estatísticas do mapa"""
        total = len(marcadores)
        por_status = {}
        por_tipo = {}
        por_prioridade = {}
        
        for marker in marcadores:
            # Por status
            status = marker.status.value
            por_status[status] = por_status.get(status, 0) + 1
            
            # Por tipo
            tipo = marker.tipo.value
            por_tipo[tipo] = por_tipo.get(tipo, 0) + 1
            
            # Por prioridade
            prioridade = marker.prioridade
            por_prioridade[prioridade] = por_prioridade.get(prioridade, 0) + 1
        
        return {
            'total_marcadores': total,
            'por_status': por_status,
            'por_tipo': por_tipo,
            'por_prioridade': por_prioridade,
            'municipios_criticos': len([m for m in marcadores if m.status == MarkerStatus.CRITICO]),
            'municipios_finalizados': len([m for m in marcadores if m.status == MarkerStatus.FINALIZADO])
        }
    
    def _marker_to_dict(self, marker: MapMarker) -> Dict:
        """Converte marcador para dicionário serializável"""
        return {
            'id': marker.id,
            'tipo': marker.tipo.value,
            'status': marker.status.value,
            'position': {
                'lat': marker.latitude,
                'lng': marker.longitude
            },
            'municipio': marker.municipio,
            'titulo': marker.titulo,
            'descricao': marker.descricao,
            'dados': marker.dados,
            'prioridade': marker.prioridade,
            'icone': marker.icone,
            'cor': marker.cor
        }
    
    def _get_map_styles(self) -> List[Dict]:
        """Retorna estilos customizados para o mapa"""
        # Estilo profissional para o PNSB
        return [
            {
                "featureType": "water",
                "elementType": "geometry",
                "stylers": [{"color": "#e9e9e9"}, {"lightness": 17}]
            },
            {
                "featureType": "landscape",
                "elementType": "geometry",
                "stylers": [{"color": "#f5f5f5"}, {"lightness": 20}]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry.fill",
                "stylers": [{"color": "#ffffff"}, {"lightness": 17}]
            },
            {
                "featureType": "road.highway",
                "elementType": "geometry.stroke",
                "stylers": [{"color": "#ffffff"}, {"lightness": 29}, {"weight": 0.2}]
            },
            {
                "featureType": "poi",
                "elementType": "geometry",
                "stylers": [{"color": "#f5f5f5"}, {"lightness": 21}]
            },
            {
                "featureType": "administrative",
                "elementType": "geometry.stroke",
                "stylers": [{"color": "#fefefe"}, {"lightness": 17}, {"weight": 1.2}]
            }
        ]