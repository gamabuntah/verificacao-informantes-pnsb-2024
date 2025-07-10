#!/usr/bin/env python3
"""
Script de verificação completa da saúde do sistema PNSB.
"""

import requests
import json
import time
import sys
import os

def test_endpoint(url, description, expected_status=200):
    """Testa um endpoint"""
    print(f"🔍 Testando: {description}")
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == expected_status:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - Erro HTTP {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {description} - Erro de conexão: {str(e)}")
        return False

def test_api_with_json(url, description):
    """Testa endpoint que retorna JSON"""
    print(f"🔍 Testando: {description}")
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Verificar se é um dict com fallback
            if isinstance(data, dict) and data.get('fallback'):
                print(f"⚠️  {description} - Funcionando com fallback")
                return False
            # Se é uma lista ou dict válido, considerar sucesso
            elif isinstance(data, (list, dict)):
                print(f"✅ {description} - OK")
                return True
            else:
                print(f"❌ {description} - Resposta JSON inválida")
                return False
        else:
            print(f"❌ {description} - Erro HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ {description} - Erro: {str(e)}")
        return False

def main():
    print("🏥 VERIFICAÇÃO COMPLETA DE SAÚDE DO SISTEMA PNSB")
    print("=" * 60)
    
    base_url = "http://127.0.0.1:8080"
    
    # Testes de páginas principais
    page_tests = [
        (f"{base_url}/", "Página Dashboard"),
        (f"{base_url}/visitas", "Página Visitas"),
        (f"{base_url}/relatorios", "Página Relatórios"),
        (f"{base_url}/contatos", "Página Contatos"),
        (f"{base_url}/configuracoes", "Página Configurações"),
        (f"{base_url}/whatsapp", "Página WhatsApp"),
        (f"{base_url}/produtividade", "Página Produtividade"),
        (f"{base_url}/mapa-progresso", "Página Mapa Progresso"),
        (f"{base_url}/assistente-abordagem", "Página Assistente Abordagem"),
        (f"{base_url}/analise-resistencia", "Página Análise Resistência"),
        (f"{base_url}/sistema-alertas", "Página Sistema Alertas"),
    ]
    
    # Testes de APIs
    api_tests = [
        (f"{base_url}/api/visitas", "API Visitas"),
        (f"{base_url}/api/relatorios/hoje", "API Relatório Hoje"),
        (f"{base_url}/api/relatorios/semana", "API Relatório Semana"),
        (f"{base_url}/api/relatorios/mes", "API Relatório Mês"),
        (f"{base_url}/api/contatos", "API Contatos"),
        (f"{base_url}/api/contatos_csv", "API Contatos CSV"),
    ]
    
    # Testes específicos PNSB
    pnsb_tests = [
        (f"{base_url}/api/pnsb/status/funcionalidades-pnsb", "Status Funcionalidades PNSB"),
    ]
    
    # Assets e arquivos estáticos
    static_tests = [
        (f"{base_url}/sw.js", "Service Worker"),
        (f"{base_url}/static/manifest.json", "PWA Manifest"),
        (f"{base_url}/static/js/pwa.js", "PWA JavaScript"),
    ]
    
    results = []
    
    print("\n📄 TESTANDO PÁGINAS PRINCIPAIS:")
    print("-" * 40)
    for url, description in page_tests:
        result = test_endpoint(url, description)
        results.append((description, result))
        time.sleep(0.2)
    
    print("\n🔗 TESTANDO APIs:")
    print("-" * 40)
    for url, description in api_tests:
        result = test_api_with_json(url, description)
        results.append((description, result))
        time.sleep(0.2)
    
    print("\n⚙️  TESTANDO FUNCIONALIDADES PNSB:")
    print("-" * 40)
    for url, description in pnsb_tests:
        result = test_endpoint(url, description)
        results.append((description, result))
        time.sleep(0.2)
    
    print("\n📁 TESTANDO ARQUIVOS ESTÁTICOS:")
    print("-" * 40)
    for url, description in static_tests:
        result = test_endpoint(url, description)
        results.append((description, result))
        time.sleep(0.2)
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO DA VERIFICAÇÃO DE SAÚDE:")
    print("=" * 60)
    
    success_count = 0
    warning_count = 0
    
    for description, result in results:
        if result:
            status = "✅ OK"
            success_count += 1
        else:
            status = "❌ FALHA"
            if "fallback" in description.lower():
                warning_count += 1
    
        print(f"{status:12} - {description}")
    
    total_tests = len(results)
    success_rate = (success_count / total_tests) * 100
    
    print(f"\n📈 ESTATÍSTICAS:")
    print(f"   Total de testes: {total_tests}")
    print(f"   Sucessos: {success_count}")
    print(f"   Falhas: {total_tests - success_count}")
    print(f"   Taxa de sucesso: {success_rate:.1f}%")
    
    # Avaliar saúde geral
    if success_rate >= 90:
        print(f"\n🎉 SISTEMA SAUDÁVEL! ({success_rate:.1f}% de sucesso)")
        return 0
    elif success_rate >= 70:
        print(f"\n⚠️  SISTEMA COM PROBLEMAS MENORES ({success_rate:.1f}% de sucesso)")
        return 1
    else:
        print(f"\n🚨 SISTEMA COM PROBLEMAS CRÍTICOS ({success_rate:.1f}% de sucesso)")
        return 2

if __name__ == "__main__":
    sys.exit(main())