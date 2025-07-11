"""
Serviço para buscar horários de funcionamento via Google Places API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class GooglePlacesService:
    """Serviço para buscar informações de estabelecimentos via Google Places API"""
    
    def __init__(self):
        self.base_url = "https://maps.googleapis.com/maps/api/place"
        self.cache = {}  # Cache em memória para horários
        self.cache_duration = 24 * 60 * 60  # 24 horas
        
    def get_api_key(self) -> str:
        """Obter chave da API do Google"""
        return current_app.config.get('GOOGLE_MAPS_API_KEY', '')
    
    def search_place(self, name: str, location: str, place_type: str = "local_government_office") -> Optional[Dict]:
        """
        Buscar um estabelecimento por nome e localização
        
        Args:
            name: Nome do estabelecimento (ex: "Prefeitura de Itajaí")
            location: Localização (ex: "Itajaí, SC, Brasil")
            place_type: Tipo do estabelecimento
            
        Returns:
            Informações do estabelecimento ou None se não encontrado
        """
        api_key = self.get_api_key()
        if not api_key:
            logger.warning("Google Places API key não configurada")
            return None
            
        # Construir query de busca
        query = f"{name} {location}"
        
        # Parâmetros da busca
        params = {
            'query': query,
            'key': api_key,
            'fields': 'place_id,name,formatted_address,opening_hours,geometry,business_status,types',
            'type': place_type
        }
        
        try:
            # Fazer busca textual
            response = requests.get(
                f"{self.base_url}/textsearch/json",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('results'):
                    # Retornar o primeiro resultado
                    return data['results'][0]
                else:
                    logger.info(f"Nenhum resultado encontrado para: {query}")
                    return None
            else:
                logger.error(f"Erro na busca do Google Places: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao buscar estabelecimento: {str(e)}")
            return None
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Obter detalhes completos de um estabelecimento
        
        Args:
            place_id: ID do estabelecimento no Google Places
            
        Returns:
            Detalhes completos do estabelecimento
        """
        api_key = self.get_api_key()
        if not api_key:
            return None
            
        params = {
            'place_id': place_id,
            'key': api_key,
            'fields': 'place_id,name,formatted_address,opening_hours,geometry,business_status,types,formatted_phone_number,website'
        }
        
        try:
            response = requests.get(
                f"{self.base_url}/details/json",
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('result')
            else:
                logger.error(f"Erro nos detalhes do Google Places: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao obter detalhes: {str(e)}")
            return None
    
    def get_opening_hours(self, name: str, location: str, municipio: str = None, tipo_estabelecimento: str = None) -> Optional[Dict]:
        """
        Obter horários de funcionamento de um estabelecimento
        
        Args:
            name: Nome do estabelecimento
            location: Localização
            municipio: Nome do município (para cache)
            tipo_estabelecimento: Tipo do estabelecimento (para cache)
            
        Returns:
            Horários de funcionamento formatados
        """
        # Verificar cache persistente primeiro
        if municipio and tipo_estabelecimento:
            try:
                from gestao_visitas.models.horarios_funcionamento import HorariosFuncionamento
                
                cached_data = HorariosFuncionamento.get_cached_horarios(municipio, tipo_estabelecimento)
                if cached_data:
                    logger.info(f"Cache hit para {municipio} - {tipo_estabelecimento}")
                    return cached_data['horarios']
            except ImportError:
                logger.warning("Modelo HorariosFuncionamento não disponível")
            except Exception as e:
                logger.error(f"Erro ao verificar cache: {str(e)}")
        
        # Verificar cache em memória
        cache_key = f"{name}_{location}"
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            if datetime.now() - cached_data['timestamp'] < timedelta(seconds=self.cache_duration):
                return cached_data['data']
        
        # Buscar estabelecimento
        place_info = self.search_place(name, location)
        if not place_info:
            return None
            
        # Obter horários
        opening_hours = place_info.get('opening_hours', {})
        if not opening_hours:
            # Tentar obter detalhes completos
            place_id = place_info.get('place_id')
            if place_id:
                details = self.get_place_details(place_id)
                if details:
                    opening_hours = details.get('opening_hours', {})
                    # Mesclar dados completos
                    place_info.update(details)
        
        # Processar horários
        formatted_hours = self._format_opening_hours(opening_hours)
        
        # Salvar no cache em memória
        self.cache[cache_key] = {
            'data': formatted_hours,
            'timestamp': datetime.now()
        }
        
        # Salvar no cache persistente
        if municipio and tipo_estabelecimento and place_info:
            try:
                from gestao_visitas.models.horarios_funcionamento import HorariosFuncionamento
                
                HorariosFuncionamento.update_horarios(
                    municipio=municipio,
                    tipo_estabelecimento=tipo_estabelecimento,
                    dados_google=place_info
                )
                logger.info(f"Cache atualizado para {municipio} - {tipo_estabelecimento}")
            except Exception as e:
                logger.error(f"Erro ao salvar cache: {str(e)}")
        
        return formatted_hours
    
    def _format_opening_hours(self, opening_hours: Dict) -> Optional[Dict]:
        """
        Formatar horários de funcionamento
        
        Args:
            opening_hours: Horários brutos da API
            
        Returns:
            Horários formatados
        """
        if not opening_hours:
            return None
            
        formatted = {
            'is_open_now': opening_hours.get('open_now', False),
            'periods': [],
            'weekday_text': opening_hours.get('weekday_text', []),
            'special_days': []
        }
        
        # Processar períodos
        periods = opening_hours.get('periods', [])
        for period in periods:
            formatted_period = {}
            
            # Dia da semana (0=domingo, 6=sábado)
            if 'open' in period:
                formatted_period['day'] = period['open'].get('day', 0)
                formatted_period['open_time'] = period['open'].get('time', '0000')
                
            if 'close' in period:
                formatted_period['close_time'] = period['close'].get('time', '2359')
            else:
                # Aberto 24h
                formatted_period['close_time'] = '2359'
                
            formatted['periods'].append(formatted_period)
        
        return formatted
    
    def get_current_status(self, name: str, location: str) -> Dict:
        """
        Verificar se um estabelecimento está aberto agora
        
        Args:
            name: Nome do estabelecimento
            location: Localização
            
        Returns:
            Status atual do estabelecimento
        """
        hours = self.get_opening_hours(name, location)
        
        if not hours:
            return {
                'is_open': None,
                'message': 'Horários não encontrados',
                'next_open': None,
                'next_close': None
            }
        
        now = datetime.now()
        current_day = now.weekday()  # 0=segunda, 6=domingo
        current_time = now.strftime('%H%M')
        
        # Google usa 0=domingo, Python usa 0=segunda
        google_day = (current_day + 1) % 7
        
        # Verificar se está aberto agora
        is_open = False
        for period in hours.get('periods', []):
            if period.get('day') == google_day:
                open_time = period.get('open_time', '0000')
                close_time = period.get('close_time', '2359')
                
                if open_time <= current_time <= close_time:
                    is_open = True
                    break
        
        return {
            'is_open': is_open,
            'message': 'Aberto' if is_open else 'Fechado',
            'hours': hours,
            'last_updated': datetime.now().isoformat()
        }
    
    def get_best_visit_times(self, name: str, location: str) -> List[Dict]:
        """
        Obter os melhores horários para visita
        
        Args:
            name: Nome do estabelecimento
            location: Localização
            
        Returns:
            Lista de horários recomendados
        """
        hours = self.get_opening_hours(name, location)
        if not hours:
            return []
            
        recommendations = []
        
        # Analisar horários por dia da semana
        for period in hours.get('periods', []):
            day = period.get('day', 0)
            open_time = period.get('open_time', '0000')
            close_time = period.get('close_time', '2359')
            
            # Converter para formato legível
            open_hour = f"{open_time[:2]}:{open_time[2:]}"
            close_hour = f"{close_time[:2]}:{close_time[2:]}"
            
            # Calcular horários recomendados (evitar horário de almoço)
            morning_end = "11:30"
            afternoon_start = "14:00"
            
            # Manhã
            if open_time <= "1130":
                recommendations.append({
                    'day': day,
                    'period': 'morning',
                    'start': open_hour,
                    'end': morning_end,
                    'recommendation': 'Melhor horário - maior disponibilidade'
                })
            
            # Tarde
            if close_time >= "1400":
                recommendations.append({
                    'day': day,
                    'period': 'afternoon',
                    'start': afternoon_start,
                    'end': close_hour,
                    'recommendation': 'Horário alternativo'
                })
        
        return recommendations

# Instância global do serviço
places_service = GooglePlacesService()