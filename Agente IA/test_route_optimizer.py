#!/usr/bin/env python3
"""
TESTE ROBUSTO DO OTIMIZADOR DE ROTAS
Verifica se a correção da lógica duplicada está funcionando corretamente
"""

import requests
import json
import time
import sys
from datetime import datetime, timedelta

# Configuração do servidor
BASE_URL = "http://127.0.0.1:8080"
API_URL = f"{BASE_URL}/api/otimizar-rotas"

def log_test(message):
    """Log com timestamp"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_route_optimization(visitas_ids, nivel=3, execucoes=3):
    """
    Testa otimização de rotas múltiplas vezes com os mesmos dados
    Para verificar consistência dos resultados
    """
    log_test(f"🧪 TESTE: {len(visitas_ids)} visitas, Nível {nivel}, {execucoes} execuções")
    
    # Preparar dados de teste
    data = {
        "visitas": visitas_ids,
        "data_visita": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "nivel": nivel,
        "incluir_horarios_comerciais": True if nivel == 3 else False
    }
    
    results = []
    
    for i in range(execucoes):
        log_test(f"  Execução {i+1}/{execucoes}")
        
        try:
            # Fazer requisição
            response = requests.post(API_URL, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('sucesso'):
                    stats = result.get('estatisticas', {})
                    
                    # Extrair dados importantes
                    execution_result = {
                        'execucao': i + 1,
                        'numero_visitas': stats.get('numeroVisitas', 0),
                        'distancia_total': stats.get('distanciaTotal', 0),
                        'tempo_viagem': stats.get('tempoTotalViagem', 0),
                        'tempo_visitas': stats.get('tempoTotalVisitas', 0),
                        'tempo_jornada': stats.get('tempoTotalJornada', 0),
                        'eficiencia': stats.get('eficiencia', 0),
                        'nivel': result.get('nivel', 0),
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    results.append(execution_result)
                    
                    log_test(f"    ✅ Sucesso: {stats.get('distanciaTotal', 0):.2f}km, "
                           f"{stats.get('tempoTotalViagem', 0)}min viagem, "
                           f"Nível {result.get('nivel', 0)}")
                else:
                    log_test(f"    ❌ Erro: {result.get('erro', 'Desconhecido')}")
                    
            else:
                log_test(f"    ❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            log_test(f"    ❌ Exceção: {str(e)}")
            
        # Pequena pausa entre execuções
        time.sleep(1)
    
    return results

def analyze_consistency(results):
    """Analisa consistência dos resultados"""
    log_test("🔍 ANÁLISE DE CONSISTÊNCIA:")
    
    if not results:
        log_test("  ❌ Nenhum resultado para analisar")
        return False
    
    # Verificar se todas as execuções têm os mesmos valores
    first_result = results[0]
    all_consistent = True
    
    for key in ['numero_visitas', 'distancia_total', 'tempo_viagem', 'eficiencia']:
        values = [r.get(key, 0) for r in results]
        unique_values = set(values)
        
        if len(unique_values) == 1:
            log_test(f"  ✅ {key}: {values[0]} (consistente)")
        else:
            log_test(f"  ❌ {key}: {values} (INCONSISTENTE)")
            all_consistent = False
    
    return all_consistent

def main():
    log_test("🚀 INICIANDO TESTE ROBUSTO DO OTIMIZADOR DE ROTAS")
    log_test("=" * 60)
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(BASE_URL, timeout=5)
        log_test(f"✅ Servidor ativo: {response.status_code}")
    except:
        log_test("❌ Servidor não está rodando em http://127.0.0.1:8080")
        sys.exit(1)
    
    # Cenários de teste
    test_scenarios = [
        {"name": "2 visitas próximas", "visitas": [2, 3], "nivel": 3},
        {"name": "3 visitas mistas", "visitas": [2, 4, 5], "nivel": 3},
        {"name": "4 visitas diversas", "visitas": [2, 3, 4, 5], "nivel": 3},
        {"name": "Mesmo cenário Nível 2", "visitas": [2, 3], "nivel": 2},
        {"name": "Mesmo cenário Nível 1", "visitas": [2, 3], "nivel": 1},
    ]
    
    all_tests_passed = True
    
    for scenario in test_scenarios:
        log_test(f"\n🎯 CENÁRIO: {scenario['name']}")
        log_test("-" * 40)
        
        # Executar testes
        results = test_route_optimization(
            scenario['visitas'], 
            scenario['nivel'], 
            execucoes=3
        )
        
        # Analisar consistência
        if analyze_consistency(results):
            log_test("  ✅ CENÁRIO PASSOU - Resultados consistentes")
        else:
            log_test("  ❌ CENÁRIO FALHOU - Resultados inconsistentes")
            all_tests_passed = False
    
    # Resultado final
    log_test("\n" + "=" * 60)
    if all_tests_passed:
        log_test("🎉 TODOS OS TESTES PASSARAM!")
        log_test("✅ Otimizador de rotas está funcionando corretamente")
    else:
        log_test("💥 ALGUNS TESTES FALHARAM!")
        log_test("❌ Ainda há problemas de consistência")
    
    log_test("=" * 60)

if __name__ == "__main__":
    main()