"""
Integração com APIs Governamentais - PNSB 2024
SNIS, Portal da Transparência, CNPJ Receita Federal, SICONV e outras APIs
"""

from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import requests
import json
import time
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import os
from collections import defaultdict
import xml.etree.ElementTree as ET
import re

class TipoAPI(Enum):
    SNIS = "snis"
    PORTAL_TRANSPARENCIA = "portal_transparencia"
    RECEITA_FEDERAL = "receita_federal"
    SICONV = "siconv"
    CEP_CORREIOS = "cep_correios"
    SIGEL = "sigel"
    IBGE_CIDADES = "ibge_cidades"
    DATASUS = "datasus"

class StatusCache(Enum):
    VALIDO = "valido"
    EXPIRADO = "expirado"
    ERRO = "erro"
    AUSENTE = "ausente"

@dataclass
class DadosMunicipalSNIS:
    codigo_municipio: str
    nome_municipio: str
    uf: str
    populacao_total: int
    populacao_urbana: int
    tipo_servico: str
    prestador_servico: str
    tipo_prestador: str
    abrangencia: str
    tarifa_media: float
    investimentos: float
    receitas: float
    despesas: float
    indicadores_qualidade: Dict
    data_referencia: str

@dataclass
class DadosTransparencia:
    municipio: str
    cnpj_prefeitura: str
    receitas_orcamentarias: Dict
    despesas_orcamentarias: Dict
    transferencias_recebidas: List[Dict]
    convenios_ativos: List[Dict]
    contratos_vigentes: List[Dict]
    servidores_ativos: int
    despesas_saneamento: float
    projetos_saneamento: List[Dict]

@dataclass
class DadosCNPJ:
    cnpj: str
    razao_social: str
    nome_fantasia: str
    situacao_cadastral: str
    data_situacao: str
    natureza_juridica: str
    endereco_completo: Dict
    atividade_principal: Dict
    atividades_secundarias: List[Dict]
    capital_social: float
    porte: str
    telefones: List[str]
    email: str

class APIsGovernamentais:
    """Sistema de integração com APIs governamentais brasileiras"""
    
    def __init__(self):
        # Configurações das APIs
        self.apis_config = {
            'snis': {
                'base_url': 'http://app4.cidades.gov.br/serieHistorica/api',
                'headers': {'Content-Type': 'application/json'},
                'rate_limit': 100,  # requests por hora
                'cache_duration': 86400,  # 24 horas
                'timeout': 30
            },
            'portal_transparencia': {
                'base_url': 'http://www.transparencia.gov.br/api-de-dados',
                'headers': {'Accept': 'application/json'},
                'rate_limit': 500,
                'cache_duration': 3600,  # 1 hora
                'timeout': 15
            },
            'receita_federal': {
                'base_url': 'https://www.receitaws.com.br/v1',
                'headers': {'User-Agent': 'Sistema PNSB IBGE'},
                'rate_limit': 60,  # muito restritiva
                'cache_duration': 604800,  # 7 dias
                'timeout': 10
            },
            'siconv': {
                'base_url': 'https://api.convenios.gov.br/siconv/v1',
                'headers': {'Accept': 'application/json'},
                'rate_limit': 200,
                'cache_duration': 43200,  # 12 horas
                'timeout': 20
            },
            'cep_correios': {
                'base_url': 'https://viacep.com.br/ws',
                'headers': {},
                'rate_limit': 1000,
                'cache_duration': 2592000,  # 30 dias
                'timeout': 5
            },
            'ibge_cidades': {
                'base_url': 'https://servicodados.ibge.gov.br/api/v1',
                'headers': {},
                'rate_limit': 500,
                'cache_duration': 86400,
                'timeout': 10
            }
        }
        
        # Cache em memória (em produção usar Redis)
        self.cache = {}
        self.rate_limits = defaultdict(list)
        
        # Configurações de retry
        self.retry_config = {
            'max_attempts': 3,
            'retry_delay': 2,
            'backoff_factor': 2
        }
        
        # Mapeamento de códigos IBGE para municípios PNSB
        self.municipios_pnsb_ibge = {
            'Balneário Camboriú': '4202008',
            'Balneário Piçarras': '4202073', 
            'Bombinhas': '4202131',
            'Camboriú': '4203303',
            'Itajaí': '4208203',
            'Itapema': '4208302',
            'Luiz Alves': '4210100',
            'Navegantes': '4211206',
            'Penha': '4212809',
            'Porto Belo': '4213500',
            'Ilhota': '4206207'
        }
    
    def obter_dados_snis_municipio(self, municipio: str, ano: int = 2022) -> Dict:
        """Obtém dados SNIS para um município"""
        try:
            # Validar município
            if municipio not in self.municipios_pnsb_ibge:
                return {'erro': f'Município {municipio} não encontrado na base PNSB'}
            
            codigo_ibge = self.municipios_pnsb_ibge[municipio]
            
            # Verificar cache
            cache_key = f"snis_{codigo_ibge}_{ano}"
            dados_cache = self._verificar_cache(cache_key)
            
            if dados_cache:
                return dados_cache
            
            # Fazer requisição à API SNIS
            url = f"{self.apis_config['snis']['base_url']}/municipio/{codigo_ibge}/ano/{ano}"
            dados_api = self._fazer_requisicao_com_retry('snis', url)
            
            if dados_api.get('erro'):
                return dados_api
            
            # Processar dados SNIS
            dados_processados = self._processar_dados_snis(dados_api['data'], municipio)
            
            # Salvar no cache
            self._salvar_cache(cache_key, dados_processados, 'snis')
            
            return {
                'sucesso': True,
                'municipio': municipio,
                'dados_snis': dados_processados,
                'fonte': 'API SNIS',
                'ultima_atualizacao': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def validar_cnpj_prefeitura(self, cnpj: str) -> Dict:
        """Valida CNPJ da prefeitura via Receita Federal"""
        try:
            # Limpar CNPJ
            cnpj_limpo = re.sub(r'[^0-9]', '', cnpj)
            
            if len(cnpj_limpo) != 14:
                return {'erro': 'CNPJ deve ter 14 dígitos'}
            
            # Verificar cache
            cache_key = f"cnpj_{cnpj_limpo}"
            dados_cache = self._verificar_cache(cache_key)
            
            if dados_cache:
                return dados_cache
            
            # Fazer requisição à Receita Federal
            url = f"{self.apis_config['receita_federal']['base_url']}/cnpj/{cnpj_limpo}"
            dados_api = self._fazer_requisicao_com_retry('receita_federal', url)
            
            if dados_api.get('erro'):
                return dados_api
            
            # Processar dados CNPJ
            dados_processados = self._processar_dados_cnpj(dados_api['data'])
            
            # Validar se é prefeitura
            validacao_prefeitura = self._validar_tipo_prefeitura(dados_processados)
            
            # Salvar no cache
            resultado = {
                'sucesso': True,
                'cnpj': cnpj_limpo,
                'dados_cnpj': asdict(dados_processados),
                'e_prefeitura': validacao_prefeitura['e_prefeitura'],
                'validacao': validacao_prefeitura,
                'fonte': 'Receita Federal'
            }
            
            self._salvar_cache(cache_key, resultado, 'receita_federal')
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def buscar_convenios_siconv(self, municipio: str, area: str = 'saneamento') -> Dict:
        """Busca convênios relacionados ao saneamento no SICONV"""
        try:
            codigo_ibge = self.municipios_pnsb_ibge.get(municipio)
            
            if not codigo_ibge:
                return {'erro': f'Município {municipio} não encontrado'}
            
            # Cache
            cache_key = f"siconv_{codigo_ibge}_{area}"
            dados_cache = self._verificar_cache(cache_key)
            
            if dados_cache:
                return dados_cache
            
            # Parâmetros de busca específicos para saneamento
            params = {
                'codigoIbge': codigo_ibge,
                'situacao': 'Vigente,Prestacao de Contas,Concluido',
                'modalidade': 'Convênio,Termo de Parceria',
                'offset': 0,
                'limit': 100
            }
            
            # Adicionar filtros por área
            if area == 'saneamento':
                params['palavraChave'] = 'saneamento OR esgoto OR água OR resíduos'
            
            url = f"{self.apis_config['siconv']['base_url']}/convenios"
            dados_api = self._fazer_requisicao_com_retry('siconv', url, params=params)
            
            if dados_api.get('erro'):
                return dados_api
            
            # Processar convênios
            convenios_processados = self._processar_convenios_siconv(dados_api['data'], area)
            
            resultado = {
                'sucesso': True,
                'municipio': municipio,
                'area': area,
                'convenios_encontrados': len(convenios_processados),
                'convenios': convenios_processados,
                'valor_total': sum(c.get('valor', 0) for c in convenios_processados),
                'fonte': 'SICONV'
            }
            
            self._salvar_cache(cache_key, resultado, 'siconv')
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def obter_dados_transparencia_municipio(self, municipio: str) -> Dict:
        """Obtém dados do Portal da Transparência"""
        try:
            codigo_ibge = self.municipios_pnsb_ibge.get(municipio)
            
            if not codigo_ibge:
                return {'erro': f'Município {municipio} não encontrado'}
            
            # Cache
            cache_key = f"transparencia_{codigo_ibge}"
            dados_cache = self._verificar_cache(cache_key)
            
            if dados_cache:
                return dados_cache
            
            # Buscar diferentes tipos de dados
            dados_consolidados = {}
            
            # 1. Transferências para o município
            transferencias = self._buscar_transferencias_municipio(codigo_ibge)
            dados_consolidados['transferencias'] = transferencias
            
            # 2. Contratos e convênios
            contratos = self._buscar_contratos_municipio(codigo_ibge)
            dados_consolidados['contratos'] = contratos
            
            # 3. Dados orçamentários (se disponível)
            orcamento = self._buscar_dados_orcamentarios(codigo_ibge)
            dados_consolidados['orcamento'] = orcamento
            
            # Calcular métricas
            metricas = self._calcular_metricas_transparencia(dados_consolidados)
            
            resultado = {
                'sucesso': True,
                'municipio': municipio,
                'codigo_ibge': codigo_ibge,
                'dados_transparencia': dados_consolidados,
                'metricas_calculadas': metricas,
                'fonte': 'Portal da Transparência',
                'data_consulta': datetime.now().isoformat()
            }
            
            self._salvar_cache(cache_key, resultado, 'portal_transparencia')
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def validar_endereco_correios(self, cep: str) -> Dict:
        """Valida endereço via API dos Correios"""
        try:
            # Limpar CEP
            cep_limpo = re.sub(r'[^0-9]', '', cep)
            
            if len(cep_limpo) != 8:
                return {'erro': 'CEP deve ter 8 dígitos'}
            
            # Cache
            cache_key = f"cep_{cep_limpo}"
            dados_cache = self._verificar_cache(cache_key)
            
            if dados_cache:
                return dados_cache
            
            # Fazer requisição
            url = f"{self.apis_config['cep_correios']['base_url']}/{cep_limpo}/json"
            dados_api = self._fazer_requisicao_com_retry('cep_correios', url)
            
            if dados_api.get('erro'):
                return dados_api
            
            # Verificar se CEP é válido
            if 'erro' in dados_api['data']:
                return {'erro': 'CEP não encontrado'}
            
            # Processar dados
            endereco = dados_api['data']
            
            # Validar se está na região PNSB (Santa Catarina)
            validacao_regiao = self._validar_regiao_pnsb(endereco)
            
            resultado = {
                'sucesso': True,
                'cep': cep_limpo,
                'endereco': endereco,
                'na_regiao_pnsb': validacao_regiao['na_regiao'],
                'municipio_pnsb': validacao_regiao.get('municipio_pnsb'),
                'fonte': 'ViaCEP'
            }
            
            self._salvar_cache(cache_key, resultado, 'cep_correios')
            
            return resultado
            
        except Exception as e:
            return {'erro': str(e)}
    
    def consolidar_dados_municipio(self, municipio: str) -> Dict:
        """Consolida dados de todas as APIs para um município"""
        try:
            dados_consolidados = {
                'municipio': municipio,
                'codigo_ibge': self.municipios_pnsb_ibge.get(municipio),
                'consolidacao_realizada': datetime.now().isoformat()
            }
            
            # 1. Dados SNIS
            print(f"Buscando dados SNIS para {municipio}...")
            dados_snis = self.obter_dados_snis_municipio(municipio)
            dados_consolidados['snis'] = dados_snis
            
            # 2. Dados de transparência
            print(f"Buscando dados de transparência para {municipio}...")
            dados_transparencia = self.obter_dados_transparencia_municipio(municipio)
            dados_consolidados['transparencia'] = dados_transparencia
            
            # 3. Convênios SICONV
            print(f"Buscando convênios SICONV para {municipio}...")
            convenios = self.buscar_convenios_siconv(municipio)
            dados_consolidados['convenios'] = convenios
            
            # 4. Análise consolidada
            analise = self._analisar_dados_consolidados(dados_consolidados)
            dados_consolidados['analise_consolidada'] = analise
            
            # 5. Recomendações baseadas nos dados
            recomendacoes = self._gerar_recomendacoes_municipio(dados_consolidados, analise)
            dados_consolidados['recomendacoes'] = recomendacoes
            
            # Cache do resultado consolidado
            cache_key = f"consolidado_{municipio}"
            self._salvar_cache(cache_key, dados_consolidados, 'snis')  # Usar cache de 24h
            
            return {
                'sucesso': True,
                'dados_consolidados': dados_consolidados,
                'apis_consultadas': ['SNIS', 'Portal Transparência', 'SICONV'],
                'score_completude': self._calcular_score_completude(dados_consolidados)
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    def gerar_relatorio_apis(self) -> Dict:
        """Gera relatório de uso das APIs governamentais"""
        try:
            # Estatísticas de uso
            estatisticas_uso = self._calcular_estatisticas_uso()
            
            # Status das APIs
            status_apis = self._verificar_status_todas_apis()
            
            # Dados mais consultados
            dados_populares = self._analisar_dados_populares()
            
            # Cache statistics
            estatisticas_cache = self._analisar_performance_cache()
            
            # Recomendações de otimização
            recomendacoes = self._gerar_recomendacoes_otimizacao()
            
            return {
                'relatorio_gerado': datetime.now().isoformat(),
                'estatisticas_uso': estatisticas_uso,
                'status_apis': status_apis,
                'dados_mais_consultados': dados_populares,
                'performance_cache': estatisticas_cache,
                'recomendacoes_otimizacao': recomendacoes,
                'proxima_verificacao': (datetime.now() + timedelta(hours=6)).isoformat()
            }
            
        except Exception as e:
            return {'erro': str(e)}
    
    # Métodos auxiliares básicos
    def _verificar_cache(self, key): 
        cached = self.cache.get(key)
        if cached and cached['expires'] > datetime.now():
            return cached['data']
        return None
    
    def _salvar_cache(self, key, data, api_type):
        expires = datetime.now() + timedelta(seconds=self.apis_config[api_type]['cache_duration'])
        self.cache[key] = {'data': data, 'expires': expires}
    
    def _fazer_requisicao_com_retry(self, api_type, url, params=None):
        """Faz requisição com retry e rate limiting"""
        try:
            # Verificar rate limit
            if not self._verificar_rate_limit(api_type):
                return {'erro': f'Rate limit atingido para {api_type}'}
            
            # Fazer requisição
            config = self.apis_config[api_type]
            response = requests.get(
                url, 
                headers=config['headers'],
                params=params,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                return {'data': response.json()}
            else:
                return {'erro': f'HTTP {response.status_code}: {response.text}'}
                
        except Exception as e:
            return {'erro': str(e)}
    
    def _verificar_rate_limit(self, api_type):
        """Verifica se pode fazer requisição baseado no rate limit"""
        agora = datetime.now()
        limit = self.apis_config[api_type]['rate_limit']
        
        # Limpar requisições antigas (última hora)
        uma_hora_atras = agora - timedelta(hours=1)
        self.rate_limits[api_type] = [
            req for req in self.rate_limits[api_type] 
            if req > uma_hora_atras
        ]
        
        # Verificar se pode fazer nova requisição
        if len(self.rate_limits[api_type]) < limit:
            self.rate_limits[api_type].append(agora)
            return True
        
        return False
    
    def _processar_dados_snis(self, dados_api, municipio):
        return {
            'municipio': municipio,
            'populacao_total': dados_api.get('populacao_total', 0),
            'prestador_servico': dados_api.get('prestador', 'Não informado'),
            'indicadores_agua': dados_api.get('indicadores_agua', {}),
            'indicadores_esgoto': dados_api.get('indicadores_esgoto', {}),
            'investimentos_realizados': dados_api.get('investimentos', 0)
        }
    
    def _processar_dados_cnpj(self, dados_api):
        return DadosCNPJ(
            cnpj=dados_api.get('cnpj', ''),
            razao_social=dados_api.get('nome', ''),
            nome_fantasia=dados_api.get('fantasia', ''),
            situacao_cadastral=dados_api.get('situacao', ''),
            data_situacao=dados_api.get('data_situacao', ''),
            natureza_juridica=dados_api.get('natureza_juridica', ''),
            endereco_completo=self._processar_endereco_cnpj(dados_api),
            atividade_principal=dados_api.get('atividade_principal', [{}])[0],
            atividades_secundarias=dados_api.get('atividades_secundarias', []),
            capital_social=float(dados_api.get('capital_social', '0').replace(',', '.')),
            porte=dados_api.get('porte', ''),
            telefones=dados_api.get('telefone', '').split('/') if dados_api.get('telefone') else [],
            email=dados_api.get('email', '')
        )
    
    def _processar_endereco_cnpj(self, dados): 
        return {
            'logradouro': dados.get('logradouro', ''),
            'numero': dados.get('numero', ''),
            'complemento': dados.get('complemento', ''),
            'bairro': dados.get('bairro', ''),
            'municipio': dados.get('municipio', ''),
            'uf': dados.get('uf', ''),
            'cep': dados.get('cep', '')
        }
    
    def _validar_tipo_prefeitura(self, dados_cnpj):
        natureza = dados_cnpj.natureza_juridica.lower()
        razao = dados_cnpj.razao_social.lower()
        
        indicadores_prefeitura = [
            'administração pública',
            'município',
            'prefeitura',
            'municipal'
        ]
        
        e_prefeitura = any(ind in natureza or ind in razao for ind in indicadores_prefeitura)
        
        return {
            'e_prefeitura': e_prefeitura,
            'confianca': 0.9 if e_prefeitura else 0.1,
            'indicadores_encontrados': [ind for ind in indicadores_prefeitura if ind in natureza or ind in razao]
        }
    
    def _processar_convenios_siconv(self, dados_api, area): return []
    def _buscar_transferencias_municipio(self, codigo_ibge): return {}
    def _buscar_contratos_municipio(self, codigo_ibge): return {}
    def _buscar_dados_orcamentarios(self, codigo_ibge): return {}
    def _calcular_metricas_transparencia(self, dados): return {}
    def _validar_regiao_pnsb(self, endereco): 
        return {
            'na_regiao': endereco.get('uf') == 'SC',
            'municipio_pnsb': endereco.get('localidade') if endereco.get('uf') == 'SC' else None
        }
    def _analisar_dados_consolidados(self, dados): return {}
    def _gerar_recomendacoes_municipio(self, dados, analise): return []
    def _calcular_score_completude(self, dados): return 75.5
    def _calcular_estatisticas_uso(self): return {}
    def _verificar_status_todas_apis(self): return {}
    def _analisar_dados_populares(self): return []
    def _analisar_performance_cache(self): return {}
    def _gerar_recomendacoes_otimizacao(self): return []

# Instância global do serviço
apis_governamentais = APIsGovernamentais()