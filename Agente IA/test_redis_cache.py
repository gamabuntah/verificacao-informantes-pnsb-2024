#!/usr/bin/env python3
"""
Script de teste para validar funcionamento do cache Redis
Execute: python test_redis_cache.py
"""

import sys
import time
import requests
from gestao_visitas.services.redis_cache import redis_cache

def test_redis_connection():
    """Testa conexão básica com Redis"""
    print("🔍 Testando conexão Redis...")
    
    health = redis_cache.health_check()
    print(f"Status: {health['status']}")
    print(f"Redis conectado: {health['redis_connected']}")
    
    if health['issues']:
        print("Problemas encontrados:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    return health['status'] == 'healthy'

def test_cache_operations():
    """Testa operações básicas de cache"""
    print("\n📋 Testando operações de cache...")
    
    # Teste de escrita
    test_key = 'test_cache_key'
    test_value = {'municipio': 'Itajaí', 'populacao': 183373}
    
    print("✍️ Salvando no cache...")
    success = redis_cache.set(test_key, test_value, 30)
    print(f"  Resultado: {'✅ Sucesso' if success else '❌ Falha'}")
    
    # Teste de leitura
    print("📖 Lendo do cache...")
    cached_value = redis_cache.get(test_key)
    
    if cached_value == test_value:
        print("  ✅ Valor recuperado corretamente")
    else:
        print(f"  ❌ Valor incorreto. Esperado: {test_value}, Obtido: {cached_value}")
    
    # Teste de existência
    exists = redis_cache.exists(test_key)
    print(f"  Chave existe: {'✅ Sim' if exists else '❌ Não'}")
    
    # Teste de remoção
    print("🗑️ Removendo do cache...")
    deleted = redis_cache.delete(test_key)
    print(f"  Resultado: {'✅ Removido' if deleted else '❌ Falha'}")
    
    # Verificar se foi removido
    exists_after = redis_cache.exists(test_key)
    print(f"  Chave existe após remoção: {'❌ Ainda existe' if exists_after else '✅ Removida'}")

def test_cache_metrics():
    """Testa métricas de performance"""
    print("\n📊 Testando métricas...")
    
    metrics = redis_cache.get_metrics()
    
    print(f"Hits: {metrics['hits']}")
    print(f"Misses: {metrics['misses']}")
    print(f"Hit Rate: {metrics['hit_rate_percent']}%")
    print(f"Redis conectado: {metrics['redis_connected']}")
    print(f"Cache local (fallback): {metrics['cache_size_local']} itens")

def test_api_endpoints():
    """Testa endpoints da API"""
    print("\n🌐 Testando endpoints da API...")
    
    base_url = "http://localhost:8080/api/ibge"
    
    endpoints = [
        ('/cache/health', 'Health Check'),
        ('/cache/status', 'Cache Status'),
        ('/cache/metrics', 'Cache Metrics')
    ]
    
    for endpoint, description in endpoints:
        try:
            print(f"🔍 Testando {description}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ {description} OK")
            else:
                print(f"  ⚠️ {description} retornou status {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"  ❌ Servidor não está rodando em localhost:8080")
            break
        except Exception as e:
            print(f"  ❌ Erro: {e}")

def performance_test():
    """Teste básico de performance"""
    print("\n⚡ Teste de Performance...")
    
    num_operations = 100
    test_data = {'teste': 'dados_performance', 'timestamp': time.time()}
    
    # Teste de escrita
    start_time = time.time()
    for i in range(num_operations):
        redis_cache.set(f"perf_test_{i}", test_data, 60)
    write_time = time.time() - start_time
    
    # Teste de leitura
    start_time = time.time()
    for i in range(num_operations):
        redis_cache.get(f"perf_test_{i}")
    read_time = time.time() - start_time
    
    # Limpeza
    for i in range(num_operations):
        redis_cache.delete(f"perf_test_{i}")
    
    print(f"Escritas: {num_operations} ops em {write_time:.2f}s = {num_operations/write_time:.0f} ops/s")
    print(f"Leituras: {num_operations} ops em {read_time:.2f}s = {num_operations/read_time:.0f} ops/s")

def main():
    """Executa todos os testes"""
    print("🚀 TESTE DO SISTEMA REDIS CACHE - PNSB")
    print("=" * 50)
    
    # Teste 1: Conexão
    redis_ok = test_redis_connection()
    
    # Teste 2: Operações básicas
    test_cache_operations()
    
    # Teste 3: Métricas
    test_cache_metrics()
    
    # Teste 4: Performance (só se Redis estiver funcionando)
    if redis_ok:
        performance_test()
    
    # Teste 5: APIs (se servidor estiver rodando)
    test_api_endpoints()
    
    print("\n" + "=" * 50)
    if redis_ok:
        print("🎉 TODOS OS TESTES CONCLUÍDOS!")
        print("✅ Sistema Redis funcionando corretamente")
    else:
        print("⚠️ TESTES CONCLUÍDOS COM AVISOS")
        print("💡 Sistema funcionará com cache local como fallback")
    
    print("\nPróximos passos:")
    print("1. Se Redis não estiver funcionando, execute: install_redis.bat")
    print("2. Inicie o servidor: python app.py")
    print("3. Teste a API: http://localhost:8080/api/ibge/cache/health")

if __name__ == "__main__":
    main()