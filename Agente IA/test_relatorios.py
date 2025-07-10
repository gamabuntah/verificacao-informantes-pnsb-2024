#!/usr/bin/env python3
"""
Script de teste para verificar se a funcionalidade de relatórios está funcionando corretamente.
"""

import requests
import json
import time
import sys

def test_api_endpoint(url, description):
    """Testa um endpoint da API"""
    print(f"🔍 Testando: {description}")
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se é um fallback (indica erro)
            if data.get('fallback'):
                print(f"⚠️  API funcionando mas com fallback - Erro: {data.get('erro', 'Desconhecido')}")
                return False
            else:
                print(f"✅ {description} - OK")
                return True
        else:
            print(f"❌ {description} - Erro HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {description} - Erro de conexão: {str(e)}")
        return False

def test_relatorios_page():
    """Testa se a página de relatórios carrega"""
    print(f"🔍 Testando: Página de relatórios")
    try:
        response = requests.get("http://127.0.0.1:8080/relatorios", timeout=10)
        
        if response.status_code == 200:
            if "Relatórios de Visitas" in response.text:
                print(f"✅ Página de relatórios - OK")
                return True
            else:
                print(f"⚠️  Página carregou mas conteúdo incorreto")
                return False
        else:
            print(f"❌ Página de relatórios - Erro HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Página de relatórios - Erro de conexão: {str(e)}")
        return False

def main():
    print("🧪 TESTE DE FUNCIONALIDADE - RELATÓRIOS PNSB")
    print("=" * 50)
    
    base_url = "http://127.0.0.1:8080"
    
    tests = [
        (f"{base_url}/relatorios", "Página de relatórios", test_relatorios_page),
        (f"{base_url}/api/relatorios/hoje", "API Relatório Hoje", test_api_endpoint),
        (f"{base_url}/api/relatorios/semana", "API Relatório Semana", test_api_endpoint),
        (f"{base_url}/api/relatorios/mes", "API Relatório Mês", test_api_endpoint),
    ]
    
    results = []
    
    for test_data in tests:
        if len(test_data) == 3:
            url, description, test_func = test_data
            if test_func == test_relatorios_page:
                result = test_func()
            else:
                result = test_func(url, description)
        else:
            url, description = test_data
            result = test_api_endpoint(url, description)
        
        results.append((description, result))
        time.sleep(0.5)  # Pequena pausa entre testes
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DOS TESTES:")
    print("=" * 50)
    
    success_count = 0
    for description, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} - {description}")
        if result:
            success_count += 1
    
    print(f"\n📈 RESUMO: {success_count}/{len(results)} testes passaram")
    
    if success_count == len(results):
        print("\n🎉 TODOS OS TESTES PASSARAM! A funcionalidade de relatórios está funcionando corretamente.")
        return 0
    else:
        print(f"\n⚠️  {len(results) - success_count} teste(s) falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())