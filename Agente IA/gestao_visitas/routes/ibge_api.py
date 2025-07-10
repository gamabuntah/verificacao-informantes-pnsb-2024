"""
Endpoints Flask para integração com dados do IBGE
Fornece APIs REST para o frontend consumir
"""

from flask import Blueprint, jsonify, request
import asyncio
from ..services.ibge_service import ibge_service

# Criar blueprint para APIs IBGE
ibge_bp = Blueprint('ibge_api', __name__, url_prefix='/api/ibge')

def run_async(coro):
    """Helper para executar código async em contexto Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

@ibge_bp.route('/municipios', methods=['GET'])
def get_municipios():
    """
    GET /api/ibge/municipios
    Retorna lista de municípios PNSB com dados básicos
    """
    try:
        municipios = run_async(ibge_service.get_municipios_santa_catarina())
        
        return jsonify({
            'success': True,
            'data': municipios,
            'total': len(municipios),
            'message': 'Municípios obtidos com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar municípios'
        }), 500

@ibge_bp.route('/demograficos', methods=['GET'])
def get_dados_demograficos():
    """
    GET /api/ibge/demograficos
    Retorna dados demográficos dos municípios PNSB
    """
    try:
        # Primeiro buscar municípios
        municipios = run_async(ibge_service.get_municipios_santa_catarina())
        
        # Depois buscar dados demográficos
        dados_demograficos = run_async(ibge_service.get_dados_demograficos(municipios))
        
        # Enriquecer dados com informações dos municípios
        resultado = []
        for municipio in municipios:
            nome = municipio['nome']
            if nome in dados_demograficos:
                dados = dados_demograficos[nome]
                resultado.append({
                    'id': municipio['id'],
                    'nome': nome,
                    'populacao': dados['populacao'],
                    'densidade': calcular_densidade(nome, dados['populacao']),
                    'ano_referencia': dados['ano_referencia'],
                    'fonte': 'IBGE - Censo/Estimativa'
                })
        
        return jsonify({
            'success': True,
            'data': resultado,
            'total': len(resultado),
            'message': 'Dados demográficos obtidos com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar dados demográficos'
        }), 500

@ibge_bp.route('/economicos', methods=['GET'])
def get_dados_economicos():
    """
    GET /api/ibge/economicos
    Retorna dados econômicos dos municípios PNSB
    """
    try:
        # Primeiro buscar municípios
        municipios = run_async(ibge_service.get_municipios_santa_catarina())
        
        # Depois buscar dados econômicos
        dados_economicos = run_async(ibge_service.get_dados_economicos(municipios))
        
        # Buscar também dados demográficos para calcular PIB per capita
        dados_demograficos = run_async(ibge_service.get_dados_demograficos(municipios))
        
        # Enriquecer dados
        resultado = []
        for municipio in municipios:
            nome = municipio['nome']
            if nome in dados_economicos:
                dados_econ = dados_economicos[nome]
                dados_demo = dados_demograficos.get(nome, {})
                
                pib_per_capita = None
                if dados_demo.get('populacao'):
                    pib_per_capita = dados_econ['pib'] / dados_demo['populacao']
                
                resultado.append({
                    'id': municipio['id'],
                    'nome': nome,
                    'pib': dados_econ['pib'],
                    'pib_per_capita': pib_per_capita,
                    'ano_referencia': dados_econ['ano_referencia'],
                    'fonte': 'IBGE - Produto Interno Bruto dos Municípios'
                })
        
        return jsonify({
            'success': True,
            'data': resultado,
            'total': len(resultado),
            'message': 'Dados econômicos obtidos com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar dados econômicos'
        }), 500

@ibge_bp.route('/consolidado', methods=['GET'])
def get_dados_consolidados():
    """
    GET /api/ibge/consolidado
    Retorna todos os dados consolidados dos municípios PNSB
    """
    try:
        # Buscar todos os dados
        municipios = run_async(ibge_service.get_municipios_santa_catarina())
        dados_demograficos = run_async(ibge_service.get_dados_demograficos(municipios))
        dados_economicos = run_async(ibge_service.get_dados_economicos(municipios))
        
        # Consolidar dados
        resultado = []
        for municipio in municipios:
            nome = municipio['nome']
            
            # Dados demográficos
            demo = dados_demograficos.get(nome, {})
            populacao = demo.get('populacao', 0)
            
            # Dados econômicos
            econ = dados_economicos.get(nome, {})
            pib = econ.get('pib', 0)
            pib_per_capita = pib / populacao if populacao > 0 else 0
            
            resultado.append({
                'id': municipio['id'],
                'nome': nome,
                'dados_basicos': {
                    'id_ibge': municipio['id'],
                    'microrregiao': municipio.get('microrregiao', {}).get('nome', 'N/A'),
                    'mesorregiao': municipio.get('microrregiao', {}).get('mesorregiao', {}).get('nome', 'N/A')
                },
                'demograficos': {
                    'populacao': populacao,
                    'densidade': calcular_densidade(nome, populacao),
                    'ano_referencia': demo.get('ano_referencia', 'N/A')
                },
                'economicos': {
                    'pib': pib,
                    'pib_per_capita': pib_per_capita,
                    'ano_referencia': econ.get('ano_referencia', 'N/A')
                },
                'indicadores': {
                    'icm_score': calcular_icm(nome, populacao, pib_per_capita),
                    'classificacao_porte': classificar_porte_municipio(populacao),
                    'nivel_desenvolvimento': classificar_desenvolvimento(pib_per_capita)
                }
            })
        
        return jsonify({
            'success': True,
            'data': resultado,
            'total': len(resultado),
            'metadata': {
                'fonte_demografica': 'IBGE - Censo/Estimativas',
                'fonte_economica': 'IBGE - PIB dos Municípios',
                'ultima_atualizacao': 'Cache local',
                'municipios_pnsb': len(resultado)
            },
            'message': 'Dados consolidados obtidos com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao buscar dados consolidados'
        }), 500

@ibge_bp.route('/cache/status', methods=['GET'])
def get_cache_status():
    """
    GET /api/ibge/cache/status
    Retorna status do cache Redis e métricas de performance
    """
    try:
        # Obter métricas do Redis
        cache_metrics = ibge_service.cache.get_metrics()
        
        # Verificar chaves específicas IBGE
        cache_keys = ['municipios_sc', 'demograficos_pnsb', 'economicos_pnsb']
        cache_info = {}
        
        for key in cache_keys:
            exists = ibge_service.cache.exists(f"ibge:{key}")
            cache_info[key] = {
                'existe': exists,
                'cache_key': f"ibge:{key}"
            }
        
        return jsonify({
            'success': True,
            'cache_redis': cache_metrics,
            'cache_keys_ibge': cache_info,
            'ttl_segundos': ibge_service.cache_ttl,
            'message': 'Status do cache obtido com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao obter status do cache'
        }), 500

@ibge_bp.route('/cache/clear', methods=['POST'])
def clear_cache():
    """
    POST /api/ibge/cache/clear
    Limpa o cache Redis IBGE forçando nova busca
    """
    try:
        # Limpar apenas chaves IBGE
        keys_removed = ibge_service.cache.clear_pattern("ibge:*")
        
        return jsonify({
            'success': True,
            'message': f'Cache IBGE limpo com sucesso. {keys_removed} entradas removidas.',
            'keys_removed': keys_removed,
            'pattern': 'ibge:*'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao limpar cache'
        }), 500

@ibge_bp.route('/cache/health', methods=['GET'])
def get_cache_health():
    """
    GET /api/ibge/cache/health
    Verifica saúde do sistema de cache Redis
    """
    try:
        health_status = ibge_service.cache.health_check()
        
        # Determinar código de status HTTP baseado na saúde
        if health_status['status'] == 'healthy':
            status_code = 200
        elif health_status['status'] == 'degraded':
            status_code = 206  # Partial Content
        else:
            status_code = 503  # Service Unavailable
        
        return jsonify({
            'success': True,
            'health': health_status,
            'message': f"Cache está {health_status['status']}"
        }), status_code
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao verificar saúde do cache'
        }), 500

@ibge_bp.route('/cache/metrics', methods=['GET'])
def get_cache_metrics():
    """
    GET /api/ibge/cache/metrics
    Retorna métricas detalhadas de performance do cache
    """
    try:
        metrics = ibge_service.cache.get_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'message': 'Métricas obtidas com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro ao obter métricas'
        }), 500

@ibge_bp.route('/cache/preload', methods=['POST'])
def preload_cache():
    """
    POST /api/ibge/cache/preload
    Pre-carrega dados comuns no cache (cache warming)
    """
    try:
        # Definir funções de carregamento
        data_loaders = {
            'municipios_sc': lambda: run_async(ibge_service.get_municipios_santa_catarina()),
        }
        
        # Só carregar dados demográficos e econômicos se temos municípios
        municipios = data_loaders['municipios_sc']()
        if municipios:
            data_loaders['demograficos_pnsb'] = lambda: run_async(ibge_service.get_dados_demograficos(municipios))
            data_loaders['economicos_pnsb'] = lambda: run_async(ibge_service.get_dados_economicos(municipios))
        
        # Pre-carregar dados
        results = ibge_service.cache.preload_common_data(data_loaders)
        
        successful_loads = sum(1 for success in results.values() if success)
        total_loads = len(results)
        
        return jsonify({
            'success': True,
            'preload_results': results,
            'summary': f'{successful_loads}/{total_loads} caches carregados com sucesso',
            'message': 'Pre-carregamento concluído'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Erro no pre-carregamento do cache'
        }), 500

# Funções auxiliares
def calcular_densidade(municipio: str, populacao: int) -> float:
    """Calcula densidade demográfica com base na área conhecida"""
    areas_km2 = {
        'Itajaí': 289.96,
        'Balneário Camboriú': 23.36,
        'Bombinhas': 23.32,
        'Itapema': 120.69,
        'Navegantes': 105.29,
        'Penha': 90.25,
        'Camboriú': 184.29,
        'Porto Belo': 66.98,
        'Balneário Piçarras': 44.00,
        'Luiz Alves': 96.90,
        'Ilhota': 92.61
    }
    
    area = areas_km2.get(municipio, 100)  # Default 100 km²
    return populacao / area if area > 0 else 0

def calcular_icm(municipio: str, populacao: int, pib_per_capita: float) -> int:
    """Calcula Índice de Complexidade Municipal"""
    # Fatores baseados em população e desenvolvimento econômico
    fator_populacao = min(populacao / 200000, 1.0) * 30  # Max 30 pontos
    fator_economico = min(pib_per_capita / 50000, 1.0) * 30  # Max 30 pontos
    fator_logistico = 40  # Base logística (40 pontos)
    
    # Ajustes por município específico
    ajustes = {
        'Balneário Camboriú': -10,  # Mais complexo turisticamente
        'Itajaí': -5,  # Porto importante
        'Bombinhas': +10,  # Menor e mais simples
        'Luiz Alves': +15,  # Rural e pequeno
        'Ilhota': +15
    }
    
    icm = fator_populacao + fator_economico + fator_logistico
    icm += ajustes.get(municipio, 0)
    
    return max(0, min(100, int(icm)))

def classificar_porte_municipio(populacao: int) -> str:
    """Classifica porte do município"""
    if populacao < 20000:
        return 'Pequeno Porte I'
    elif populacao < 50000:
        return 'Pequeno Porte II'
    elif populacao < 100000:
        return 'Médio Porte'
    else:
        return 'Grande Porte'

def classificar_desenvolvimento(pib_per_capita: float) -> str:
    """Classifica nível de desenvolvimento"""
    if pib_per_capita < 20000:
        return 'Desenvolvimento Baixo'
    elif pib_per_capita < 35000:
        return 'Desenvolvimento Médio'
    else:
        return 'Alto Desenvolvimento'