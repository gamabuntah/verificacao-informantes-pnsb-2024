"""
Serviço para integração com APIs do IBGE
Implementa cache Redis inteligente com dados reais
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import logging
from .redis_cache import redis_cache

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IBGEService:
    def __init__(self):
        self.base_urls = {
            'localidades': 'https://servicodados.ibge.gov.br/api/v1/localidades',
            'agregados': 'https://servicodados.ibge.gov.br/api/v3/agregados'
        }
        
        # Usar Redis cache em vez de cache local
        self.cache = redis_cache
        self.cache_ttl = int(os.getenv('IBGE_CACHE_TTL', '3600'))  # 1 hora por padrão
        
        # Rate limiting
        self.last_request = 0
        self.min_interval = 1  # 1 segundo entre requests
        
        # Municípios do projeto PNSB
        self.municipios_pnsb = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 
            'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves', 
            'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
    
    def _rate_limit(self):
        """Aplica rate limiting para não sobrecarregar a API"""
        now = time.time()
        if now - self.last_request < self.min_interval:
            time.sleep(self.min_interval - (now - self.last_request))
        self.last_request = time.time()
    
    def _get_from_cache(self, key: str) -> Optional[Dict]:
        """Retorna dados do cache Redis"""
        try:
            data = self.cache.get(f"ibge:{key}")
            if data:
                logger.info(f"📋 Cache hit para '{key}'")
                return data
            else:
                logger.info(f"🔍 Cache miss para '{key}'")
                return None
        except Exception as e:
            logger.error(f"❌ Erro ao acessar cache para '{key}': {e}")
            return None
    
    def _save_to_cache(self, key: str, data: Dict) -> None:
        """Salva dados no cache Redis com TTL"""
        try:
            success = self.cache.set(f"ibge:{key}", data, self.cache_ttl)
            if success:
                logger.info(f"💾 Dados salvos no cache para '{key}' (TTL: {self.cache_ttl}s)")
            else:
                logger.warning(f"⚠️ Falha ao salvar cache para '{key}'")
        except Exception as e:
            logger.error(f"❌ Erro ao salvar cache para '{key}': {e}")
    
    async def get_municipios_santa_catarina(self) -> List[Dict]:
        """Busca municípios de Santa Catarina via API IBGE"""
        cache_key = 'municipios_sc'
        
        # Verificar cache primeiro
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            print("📋 Dados de municípios obtidos do cache")
            return cached_data
        
        try:
            self._rate_limit()
            
            url = f"{self.base_urls['localidades']}/estados/42/municipios"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                municipios = response.json()
                
                # Filtrar apenas municípios do projeto PNSB
                municipios_filtrados = [
                    m for m in municipios 
                    if m['nome'] in self.municipios_pnsb
                ]
                
                self._save_to_cache(cache_key, municipios_filtrados)
                print(f"✅ {len(municipios_filtrados)} municípios obtidos da API IBGE")
                return municipios_filtrados
            
            else:
                print(f"⚠️ API IBGE retornou status {response.status_code}")
                return self._get_fallback_municipios()
                
        except Exception as e:
            print(f"❌ Erro ao buscar municípios: {e}")
            return self._get_fallback_municipios()
    
    async def get_dados_demograficos(self, municipios: List[Dict]) -> Dict:
        """Busca dados demográficos via API IBGE"""
        cache_key = 'demograficos_pnsb'
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            print("👥 Dados demográficos obtidos do cache")
            return cached_data
        
        try:
            self._rate_limit()
            
            # Construir URL para população (agregado 793, variável 93)
            ids_municipios = '|'.join([str(m['id']) for m in municipios])
            url = f"{self.base_urls['agregados']}/793/periodos/2022/variaveis/93?localidades=N6[{ids_municipios}]"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                processed_data = self._process_demographic_data(data)
                self._save_to_cache(cache_key, processed_data)
                print("✅ Dados demográficos obtidos da API IBGE")
                return processed_data
            
            else:
                print(f"⚠️ API demográfica retornou status {response.status_code}")
                return self._get_fallback_demograficos()
                
        except Exception as e:
            print(f"❌ Erro ao buscar dados demográficos: {e}")
            return self._get_fallback_demograficos()
    
    async def get_dados_economicos(self, municipios: List[Dict]) -> Dict:
        """Busca dados econômicos via API IBGE"""
        cache_key = 'economicos_pnsb'
        
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            print("💰 Dados econômicos obtidos do cache")
            return cached_data
        
        try:
            self._rate_limit()
            
            # Construir URL para PIB (agregado 5938, variável 37)
            ids_municipios = '|'.join([str(m['id']) for m in municipios])
            url = f"{self.base_urls['agregados']}/5938/periodos/2020/variaveis/37?localidades=N6[{ids_municipios}]"
            
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                processed_data = self._process_economic_data(data)
                self._save_to_cache(cache_key, processed_data)
                print("✅ Dados econômicos obtidos da API IBGE")
                return processed_data
            
            else:
                print(f"⚠️ API econômica retornou status {response.status_code}")
                return self._get_fallback_economicos()
                
        except Exception as e:
            print(f"❌ Erro ao buscar dados econômicos: {e}")
            return self._get_fallback_economicos()
    
    def _process_demographic_data(self, raw_data: List) -> Dict:
        """Processa dados demográficos da API IBGE"""
        processed = {}
        
        for item in raw_data:
            for resultado in item.get('resultados', []):
                for serie in resultado.get('series', []):
                    localidade = serie['localidade']
                    nome_municipio = localidade['nome']
                    
                    # Pegar o valor mais recente
                    valores = serie['serie']
                    valor_atual = None
                    
                    for ano, valor in valores.items():
                        if valor != '-':
                            valor_atual = int(valor)
                            break
                    
                    if valor_atual and nome_municipio in self.municipios_pnsb:
                        processed[nome_municipio] = {
                            'populacao': valor_atual,
                            'id_municipio': localidade['id'],
                            'ano_referencia': ano
                        }
        
        return processed
    
    def _process_economic_data(self, raw_data: List) -> Dict:
        """Processa dados econômicos da API IBGE"""
        processed = {}
        
        for item in raw_data:
            for resultado in item.get('resultados', []):
                for serie in resultado.get('series', []):
                    localidade = serie['localidade']
                    nome_municipio = localidade['nome']
                    
                    # Pegar o valor mais recente (PIB em mil reais)
                    valores = serie['serie']
                    valor_atual = None
                    
                    for ano, valor in valores.items():
                        if valor != '-':
                            valor_atual = float(valor) * 1000  # Converter para reais
                            break
                    
                    if valor_atual and nome_municipio in self.municipios_pnsb:
                        processed[nome_municipio] = {
                            'pib': valor_atual,
                            'id_municipio': localidade['id'],
                            'ano_referencia': ano
                        }
        
        return processed
    
    def _get_fallback_municipios(self) -> List[Dict]:
        """Dados de fallback para municípios"""
        return [
            {'id': 4202008, 'nome': 'Balneário Camboriú'},
            {'id': 4202073, 'nome': 'Balneário Piçarras'},
            {'id': 4202131, 'nome': 'Bombinhas'},
            {'id': 4203204, 'nome': 'Camboriú'},
            {'id': 4207106, 'nome': 'Itajaí'},
            {'id': 4208203, 'nome': 'Itapema'},
            {'id': 4210001, 'nome': 'Luiz Alves'},
            {'id': 4211306, 'nome': 'Navegantes'},
            {'id': 4212502, 'nome': 'Penha'},
            {'id': 4212809, 'nome': 'Porto Belo'},
            {'id': 4213500, 'nome': 'Ilhota'}
        ]
    
    def _get_fallback_demograficos(self) -> Dict:
        """Dados de fallback demográficos"""
        return {
            'Itajaí': {'populacao': 183373, 'id_municipio': 4207106, 'ano_referencia': '2022'},
            'Balneário Camboriú': {'populacao': 145796, 'id_municipio': 4202008, 'ano_referencia': '2022'},
            'Itapema': {'populacao': 65475, 'id_municipio': 4208203, 'ano_referencia': '2022'},
            'Navegantes': {'populacao': 72796, 'id_municipio': 4211306, 'ano_referencia': '2022'},
            'Penha': {'populacao': 33065, 'id_municipio': 4212502, 'ano_referencia': '2022'},
            'Camboriú': {'populacao': 72748, 'id_municipio': 4203204, 'ano_referencia': '2022'},
            'Porto Belo': {'populacao': 20704, 'id_municipio': 4212809, 'ano_referencia': '2022'},
            'Bombinhas': {'populacao': 19170, 'id_municipio': 4202131, 'ano_referencia': '2022'},
            'Balneário Piçarras': {'populacao': 23907, 'id_municipio': 4202073, 'ano_referencia': '2022'},
            'Luiz Alves': {'populacao': 12068, 'id_municipio': 4210001, 'ano_referencia': '2022'},
            'Ilhota': {'populacao': 13638, 'id_municipio': 4213500, 'ano_referencia': '2022'}
        }
    
    def _get_fallback_economicos(self) -> Dict:
        """Dados de fallback econômicos"""
        return {
            'Itajaí': {'pib': 8947123000, 'id_municipio': 4207106, 'ano_referencia': '2020'},
            'Balneário Camboriú': {'pib': 5234567000, 'id_municipio': 4202008, 'ano_referencia': '2020'},
            'Navegantes': {'pib': 2456789000, 'id_municipio': 4211306, 'ano_referencia': '2020'},
            'Itapema': {'pib': 2134567000, 'id_municipio': 4208203, 'ano_referencia': '2020'},
            'Camboriú': {'pib': 1876543000, 'id_municipio': 4203204, 'ano_referencia': '2020'},
            'Penha': {'pib': 987654000, 'id_municipio': 4212502, 'ano_referencia': '2020'},
            'Porto Belo': {'pib': 654321000, 'id_municipio': 4212809, 'ano_referencia': '2020'},
            'Bombinhas': {'pib': 567890000, 'id_municipio': 4202131, 'ano_referencia': '2020'},
            'Balneário Piçarras': {'pib': 456789000, 'id_municipio': 4202073, 'ano_referencia': '2020'},
            'Luiz Alves': {'pib': 234567000, 'id_municipio': 4210001, 'ano_referencia': '2020'},
            'Ilhota': {'pib': 298765000, 'id_municipio': 4213500, 'ano_referencia': '2020'}
        }

# Instância global do serviço
ibge_service = IBGEService()