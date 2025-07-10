"""
Serviço de Mapas Offline para PNSB 2024
Cache de tiles de mapas, rotas pré-calculadas e sincronização para áreas rurais
"""

import os
import json
import requests
import time
import hashlib
import sqlite3
import googlemaps
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import current_app
import logging

from gestao_visitas.db import db
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada, EntidadePrioritariaUF


class OfflineMapsService:
    """Serviço para cache de mapas e funcionamento offline"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_dir = self._get_cache_directory()
        self.tiles_db_path = os.path.join(self.base_dir, 'map_tiles.db')
        self.routes_db_path = os.path.join(self.base_dir, 'routes_cache.db')
        self.gmaps = None
        self._initialize_databases()
        self._initialize_gmaps()
    
    def _get_cache_directory(self) -> str:
        """Cria e retorna diretório para cache de mapas"""
        base_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 
            '..', 'offline_maps_cache'
        )
        os.makedirs(base_dir, exist_ok=True)
        return base_dir
    
    def _initialize_gmaps(self):
        """Inicializa cliente Google Maps se API key disponível"""
        try:
            api_key = current_app.config.get('GOOGLE_MAPS_API_KEY')
            if api_key and api_key.strip() != '':
                self.gmaps = googlemaps.Client(key=api_key.strip())
                self.logger.info("🗺️ Google Maps API inicializada para cache offline")
            else:
                self.logger.warning("⚠️ Google Maps API key não configurada - modo offline limitado")
                self.gmaps = None
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar Google Maps API: {str(e)}")
            self.gmaps = None
    
    def _initialize_databases(self):
        """Inicializa bancos SQLite para cache"""
        try:
            # Database para tiles de mapas
            with sqlite3.connect(self.tiles_db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS map_tiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        zoom_level INTEGER NOT NULL,
                        tile_x INTEGER NOT NULL,
                        tile_y INTEGER NOT NULL,
                        tile_data BLOB NOT NULL,
                        tile_hash TEXT NOT NULL,
                        cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        tile_source TEXT DEFAULT 'osm',
                        UNIQUE(zoom_level, tile_x, tile_y, tile_source)
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_tiles_coords 
                    ON map_tiles(zoom_level, tile_x, tile_y, tile_source)
                ''')
            
            # Database para rotas pré-calculadas
            with sqlite3.connect(self.routes_db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS cached_routes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        origin_lat REAL NOT NULL,
                        origin_lng REAL NOT NULL,
                        dest_lat REAL NOT NULL,
                        dest_lng REAL NOT NULL,
                        route_hash TEXT NOT NULL UNIQUE,
                        route_data TEXT NOT NULL,
                        distance_meters INTEGER,
                        duration_seconds INTEGER,
                        cached_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        expires_at DATETIME,
                        route_source TEXT DEFAULT 'google_maps'
                    )
                ''')
                
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_routes_coords 
                    ON cached_routes(origin_lat, origin_lng, dest_lat, dest_lng)
                ''')
                
                # Tabela para entidades offline
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS offline_entities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        entity_id INTEGER NOT NULL,
                        entity_type TEXT NOT NULL,
                        entity_data TEXT NOT NULL,
                        sync_status TEXT DEFAULT 'synced',
                        last_modified DATETIME DEFAULT CURRENT_TIMESTAMP,
                        needs_upload BOOLEAN DEFAULT 0
                    )
                ''')
            
            self.logger.info("🗺️ Databases de cache offline inicializados")
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inicializar databases offline: {str(e)}")
    
    def _calculate_route_hash(self, origin_lat: float, origin_lng: float, 
                            dest_lat: float, dest_lng: float) -> str:
        """Calcula hash único para uma rota"""
        route_key = f"{origin_lat:.6f},{origin_lng:.6f}-{dest_lat:.6f},{dest_lng:.6f}"
        return hashlib.md5(route_key.encode()).hexdigest()
    
    def cache_route(self, origin_coords: Tuple[float, float], 
                   dest_coords: Tuple[float, float], route_data: Dict) -> bool:
        """
        Armazena uma rota no cache offline
        
        Args:
            origin_coords: (latitude, longitude) origem
            dest_coords: (latitude, longitude) destino  
            route_data: Dados da rota do Google Maps
            
        Returns:
            True se armazenado com sucesso
        """
        try:
            origin_lat, origin_lng = origin_coords
            dest_lat, dest_lng = dest_coords
            
            route_hash = self._calculate_route_hash(origin_lat, origin_lng, dest_lat, dest_lng)
            expires_at = datetime.now() + timedelta(days=30)  # Cache por 30 dias
            
            with sqlite3.connect(self.routes_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO cached_routes 
                    (origin_lat, origin_lng, dest_lat, dest_lng, route_hash, 
                     route_data, distance_meters, duration_seconds, expires_at, route_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    origin_lat, origin_lng, dest_lat, dest_lng, route_hash,
                    json.dumps(route_data),
                    route_data.get('distance_meters', 0),
                    route_data.get('duration_seconds', 0),
                    expires_at,
                    'google_maps'
                ))
            
            self.logger.info(f"✅ Rota armazenada no cache: {route_hash}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao cachear rota: {str(e)}")
            return False
    
    def get_cached_route(self, origin_coords: Tuple[float, float], 
                        dest_coords: Tuple[float, float]) -> Optional[Dict]:
        """
        Recupera rota do cache offline
        
        Args:
            origin_coords: (latitude, longitude) origem
            dest_coords: (latitude, longitude) destino
            
        Returns:
            Dados da rota ou None se não encontrada
        """
        try:
            origin_lat, origin_lng = origin_coords
            dest_lat, dest_lng = dest_coords
            
            route_hash = self._calculate_route_hash(origin_lat, origin_lng, dest_lat, dest_lng)
            
            with sqlite3.connect(self.routes_db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute('''
                    SELECT route_data, distance_meters, duration_seconds, cached_at
                    FROM cached_routes 
                    WHERE route_hash = ? AND expires_at > datetime('now')
                ''', (route_hash,))
                
                row = cursor.fetchone()
                if row:
                    route_data = json.loads(row['route_data'])
                    route_data.update({
                        'distance_meters': row['distance_meters'],
                        'duration_seconds': row['duration_seconds'],
                        'cached_at': row['cached_at'],
                        'source': 'offline_cache'
                    })
                    
                    self.logger.info(f"📱 Rota recuperada do cache offline: {route_hash}")
                    return route_data
                    
        except Exception as e:
            self.logger.error(f"❌ Erro ao recuperar rota do cache: {str(e)}")
        
        return None
    
    def precalculate_entity_routes(self, municipio: str = None) -> Dict:
        """
        Pré-calcula rotas entre todas as entidades de um município
        
        Args:
            municipio: Município específico ou None para todos
            
        Returns:
            Estatísticas do processamento
        """
        try:
            
            # Buscar entidades geocodificadas
            query_identificadas = EntidadeIdentificada.query.filter_by(geocodificacao_status='sucesso')
            query_prioritarias = EntidadePrioritariaUF.query.filter_by(geocodificacao_status='sucesso')
            
            if municipio:
                query_identificadas = query_identificadas.filter_by(municipio=municipio)
                query_prioritarias = query_prioritarias.filter_by(municipio=municipio)
            
            entidades_identificadas = query_identificadas.all()
            entidades_prioritarias = query_prioritarias.all()
            
            # Combinar todas as entidades
            todas_entidades = []
            
            for ent in entidades_identificadas:
                if ent.latitude and ent.longitude:
                    todas_entidades.append({
                        'id': f'identificada_{ent.id}',
                        'nome': ent.nome_entidade,
                        'municipio': ent.municipio,
                        'lat': ent.latitude,
                        'lng': ent.longitude,
                        'tipo': 'identificada'
                    })
            
            for ent in entidades_prioritarias:
                if ent.latitude and ent.longitude:
                    todas_entidades.append({
                        'id': f'prioritaria_{ent.id}',
                        'nome': ent.nome_entidade,
                        'municipio': ent.municipio,
                        'lat': ent.latitude,
                        'lng': ent.longitude,
                        'tipo': 'prioritaria'
                    })
            
            self.logger.info(f"🗺️ Pré-calculando rotas para {len(todas_entidades)} entidades")
            
            rotas_calculadas = 0
            rotas_erro = 0
            
            # Calcular rotas entre todas as combinações
            for i, origem in enumerate(todas_entidades):
                for j, destino in enumerate(todas_entidades):
                    if i >= j:  # Evitar duplicatas e self-routes
                        continue
                    
                    try:
                        # Verificar se já existe no cache
                        cached = self.get_cached_route(
                            (origem['lat'], origem['lng']),
                            (destino['lat'], destino['lng'])
                        )
                        
                        if not cached:
                            # Calcular nova rota com Google Maps
                            if self.gmaps:
                                directions = self.gmaps.directions(
                                    origin=(origem['lat'], origem['lng']),
                                    destination=(destino['lat'], destino['lng']),
                                    mode='driving'
                                )
                                
                                if directions:
                                    route = directions[0]
                                    leg = route['legs'][0]
                                    
                                    route_data = {
                                        'distance_text': leg['distance']['text'],
                                        'distance_meters': leg['distance']['value'],
                                        'duration_text': leg['duration']['text'],
                                        'duration_seconds': leg['duration']['value'],
                                        'origin': origem,
                                        'destination': destino,
                                        'polyline': route['overview_polyline']['points'],
                                        'steps': leg['steps']
                                    }
                                    
                                    # Armazenar no cache
                                    self.cache_route(
                                        (origem['lat'], origem['lng']),
                                        (destino['lat'], destino['lng']),
                                        route_data
                                    )
                                    
                                    rotas_calculadas += 1
                                    
                                    # Rate limiting
                                    time.sleep(0.1)
                                else:
                                    rotas_erro += 1
                            else:
                                self.logger.warning("⚠️ Google Maps não disponível para pré-cálculo")
                                break
                        else:
                            rotas_calculadas += 1
                            
                    except Exception as e:
                        self.logger.error(f"❌ Erro ao calcular rota {origem['nome']} -> {destino['nome']}: {str(e)}")
                        rotas_erro += 1
            
            estatisticas = {
                'entidades_processadas': len(todas_entidades),
                'rotas_calculadas': rotas_calculadas,
                'rotas_erro': rotas_erro,
                'municipio': municipio or 'todos',
                'processado_em': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Pré-cálculo concluído: {estatisticas}")
            return estatisticas
            
        except Exception as e:
            self.logger.error(f"❌ Erro no pré-cálculo de rotas: {str(e)}")
            return {'erro': str(e)}
    
    def cache_map_tiles_for_region(self, center_lat: float, center_lng: float, 
                                 radius_km: float = 5, zoom_levels: List[int] = None) -> Dict:
        """
        Faz cache dos tiles de mapa para uma região específica
        
        Args:
            center_lat: Latitude central
            center_lng: Longitude central
            radius_km: Raio em km para cache
            zoom_levels: Níveis de zoom (padrão: [10, 12, 14, 16])
            
        Returns:
            Estatísticas do cache
        """
        if zoom_levels is None:
            zoom_levels = [10, 12, 14, 16]  # Do overview ao detalhe
        
        try:
            tiles_cached = 0
            tiles_error = 0
            
            for zoom in zoom_levels:
                # Calcular bounds dos tiles para a região
                tile_bounds = self._calculate_tile_bounds(center_lat, center_lng, radius_km, zoom)
                
                for tile_x in range(tile_bounds['min_x'], tile_bounds['max_x'] + 1):
                    for tile_y in range(tile_bounds['min_y'], tile_bounds['max_y'] + 1):
                        try:
                            # Verificar se tile já existe no cache
                            if not self._tile_exists_in_cache(zoom, tile_x, tile_y):
                                # Baixar tile do OpenStreetMap
                                tile_data = self._download_osm_tile(zoom, tile_x, tile_y)
                                
                                if tile_data:
                                    self._save_tile_to_cache(zoom, tile_x, tile_y, tile_data)
                                    tiles_cached += 1
                                else:
                                    tiles_error += 1
                                
                                # Rate limiting
                                time.sleep(0.05)
                            else:
                                tiles_cached += 1
                                
                        except Exception as e:
                            self.logger.error(f"❌ Erro ao cachear tile {zoom}/{tile_x}/{tile_y}: {str(e)}")
                            tiles_error += 1
            
            estatisticas = {
                'center': {'lat': center_lat, 'lng': center_lng},
                'radius_km': radius_km,
                'zoom_levels': zoom_levels,
                'tiles_cached': tiles_cached,
                'tiles_error': tiles_error,
                'cached_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"✅ Cache de tiles concluído: {tiles_cached} tiles")
            return estatisticas
            
        except Exception as e:
            self.logger.error(f"❌ Erro no cache de tiles: {str(e)}")
            return {'erro': str(e)}
    
    def _calculate_tile_bounds(self, lat: float, lng: float, radius_km: float, zoom: int) -> Dict:
        """Calcula bounds dos tiles para uma região circular"""
        import math
        
        # Converter raio para graus (aproximação)
        radius_deg = radius_km / 111.32  # 1 grau ≈ 111.32 km
        
        # Bounds da região
        north = lat + radius_deg
        south = lat - radius_deg
        east = lng + radius_deg
        west = lng - radius_deg
        
        # Converter para tiles
        def deg2tile(lat_deg, lng_deg, zoom):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            tile_x = int((lng_deg + 180.0) / 360.0 * n)
            tile_y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return tile_x, tile_y
        
        min_x, max_y = deg2tile(south, west, zoom)
        max_x, min_y = deg2tile(north, east, zoom)
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y
        }
    
    def _tile_exists_in_cache(self, zoom: int, tile_x: int, tile_y: int) -> bool:
        """Verifica se tile já existe no cache"""
        try:
            with sqlite3.connect(self.tiles_db_path) as conn:
                cursor = conn.execute('''
                    SELECT 1 FROM map_tiles 
                    WHERE zoom_level = ? AND tile_x = ? AND tile_y = ? 
                    AND expires_at > datetime('now')
                ''', (zoom, tile_x, tile_y))
                return cursor.fetchone() is not None
        except:
            return False
    
    def _download_osm_tile(self, zoom: int, tile_x: int, tile_y: int) -> Optional[bytes]:
        """Baixa tile do OpenStreetMap"""
        try:
            url = f"https://tile.openstreetmap.org/{zoom}/{tile_x}/{tile_y}.png"
            headers = {
                'User-Agent': 'PNSB2024-OfflineCache/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao baixar tile OSM: {str(e)}")
            return None
    
    def _save_tile_to_cache(self, zoom: int, tile_x: int, tile_y: int, tile_data: bytes):
        """Salva tile no cache"""
        try:
            tile_hash = hashlib.md5(tile_data).hexdigest()
            expires_at = datetime.now() + timedelta(days=7)  # Tiles expiram em 7 dias
            
            with sqlite3.connect(self.tiles_db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO map_tiles 
                    (zoom_level, tile_x, tile_y, tile_data, tile_hash, expires_at, tile_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (zoom, tile_x, tile_y, tile_data, tile_hash, expires_at, 'osm'))
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao salvar tile: {str(e)}")
    
    def get_cache_statistics(self) -> Dict:
        """Retorna estatísticas do cache offline"""
        try:
            stats = {}
            
            # Estatísticas de tiles
            with sqlite3.connect(self.tiles_db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM map_tiles')
                stats['total_tiles'] = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(*) FROM map_tiles WHERE expires_at > datetime("now")')
                stats['valid_tiles'] = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT SUM(LENGTH(tile_data)) FROM map_tiles')
                size_bytes = cursor.fetchone()[0] or 0
                stats['tiles_size_mb'] = round(size_bytes / (1024 * 1024), 2)
            
            # Estatísticas de rotas
            with sqlite3.connect(self.routes_db_path) as conn:
                cursor = conn.execute('SELECT COUNT(*) FROM cached_routes')
                stats['total_routes'] = cursor.fetchone()[0]
                
                cursor = conn.execute('SELECT COUNT(*) FROM cached_routes WHERE expires_at > datetime("now")')
                stats['valid_routes'] = cursor.fetchone()[0]
            
            # Tamanho total dos arquivos
            tiles_size = os.path.getsize(self.tiles_db_path) if os.path.exists(self.tiles_db_path) else 0
            routes_size = os.path.getsize(self.routes_db_path) if os.path.exists(self.routes_db_path) else 0
            stats['total_cache_size_mb'] = round((tiles_size + routes_size) / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao obter estatísticas: {str(e)}")
            return {'erro': str(e)}
    
    def cleanup_expired_cache(self) -> Dict:
        """Remove itens expirados do cache"""
        try:
            deleted_tiles = 0
            deleted_routes = 0
            
            # Limpar tiles expirados
            with sqlite3.connect(self.tiles_db_path) as conn:
                cursor = conn.execute('DELETE FROM map_tiles WHERE expires_at <= datetime("now")')
                deleted_tiles = cursor.rowcount
                conn.execute('VACUUM')  # Otimizar database
            
            # Limpar rotas expiradas
            with sqlite3.connect(self.routes_db_path) as conn:
                cursor = conn.execute('DELETE FROM cached_routes WHERE expires_at <= datetime("now")')
                deleted_routes = cursor.rowcount
                conn.execute('VACUUM')  # Otimizar database
            
            result = {
                'deleted_tiles': deleted_tiles,
                'deleted_routes': deleted_routes,
                'cleaned_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"🧹 Cache limpo: {deleted_tiles} tiles, {deleted_routes} rotas removidas")
            return result
            
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza do cache: {str(e)}")
            return {'erro': str(e)}


# Funções de conveniência
def cache_santa_catarina_maps():
    """Cache de mapas para toda região de Santa Catarina do PNSB"""
    service = OfflineMapsService()
    
    # Coordenadas centrais de SC (região PNSB)
    sc_center = (-26.9, -48.7)  # Aproximadamente Itajaí
    
    return service.cache_map_tiles_for_region(
        sc_center[0], sc_center[1], 
        radius_km=50,  # 50km cobrindo toda região PNSB
        zoom_levels=[10, 12, 14, 16, 18]
    )


def precalculate_all_routes():
    """Pré-calcula todas as rotas entre entidades"""
    service = OfflineMapsService()
    return service.precalculate_entity_routes()