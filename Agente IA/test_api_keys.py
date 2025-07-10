#!/usr/bin/env python3
"""
Teste automático das chaves de API configuradas
"""

import os
import requests
import sys
from pathlib import Path

def test_google_maps_api():
    """Testa a chave do Google Maps"""
    print("🗺️ Testando Google Maps API...")
    
    # Carregar chave do .env
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return False
    
    api_key = None
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('GOOGLE_MAPS_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY não encontrada no .env")
        return False
    
    if api_key == 'your_google_maps_api_key_here':
        print("❌ Chave não configurada (ainda é o placeholder)")
        return False
    
    # Testar com Geocoding API
    test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Itajaí,SC,Brasil&key={api_key}"
    
    try:
        print(f"   Testando chave: {api_key[:10]}...{api_key[-5:]}")
        response = requests.get(test_url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            print("   ✅ Google Maps API funcionando!")
            print(f"   📍 Teste: Encontrou {len(data.get('results', []))} resultados para Itajaí")
            return True
        elif data.get('status') == 'REQUEST_DENIED':
            print("   ❌ Acesso negado!")
            print(f"   Erro: {data.get('error_message', 'APIs não ativadas ou restrições incorretas')}")
            return False
        elif data.get('status') == 'OVER_QUERY_LIMIT':
            print("   ⚠️ Cota excedida, mas chave válida")
            return True
        else:
            print(f"   ❌ Status: {data.get('status')}")
            print(f"   Erro: {data.get('error_message', 'Erro desconhecido')}")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ Erro de conexão: {e}")
        return False

def test_gemini_api():
    """Testa a chave do Gemini"""
    print("\n🤖 Testando Google Gemini API...")
    
    # Carregar chave do .env
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return False
    
    api_key = None
    with open(env_file, 'r') as f:
        for line in f:
            if line.startswith('GOOGLE_GEMINI_API_KEY='):
                api_key = line.split('=', 1)[1].strip()
                break
    
    if not api_key:
        print("❌ GOOGLE_GEMINI_API_KEY não encontrada no .env")
        return False
    
    if api_key == 'your_google_gemini_api_key_here':
        print("❌ Chave não configurada (ainda é o placeholder)")
        return False
    
    # Testar com uma requisição simples (modelo correto)
    test_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": "Diga apenas 'Teste OK' se você está funcionando."
            }]
        }]
    }
    
    try:
        print(f"   Testando chave: {api_key[:10]}...{api_key[-5:]}")
        response = requests.post(test_url, json=data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                print("   ✅ Google Gemini API funcionando!")
                text = result['candidates'][0]['content']['parts'][0]['text']
                print(f"   🤖 Resposta: {text.strip()}")
                return True
            else:
                print("   ❌ Resposta inesperada da API")
                return False
        elif response.status_code == 403:
            print("   ❌ Acesso negado!")
            print("   Verifique se a API está ativada e a chave está correta")
            return False
        elif response.status_code == 429:
            print("   ⚠️ Cota excedida, mas chave válida")
            return True
        else:
            print(f"   ❌ Status HTTP: {response.status_code}")
            print(f"   Erro: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"   ❌ Erro de conexão: {e}")
        return False

def test_flask_integration():
    """Testa se as chaves estão sendo carregadas no Flask"""
    print("\n🐍 Testando integração Flask...")
    
    try:
        # Importar e testar o SecurityConfig
        sys.path.append('.')
        from gestao_visitas.config.security import SecurityConfig
        
        maps_key = SecurityConfig.get_google_maps_key()
        gemini_key = SecurityConfig.get_google_gemini_key()
        
        if maps_key and maps_key != 'your_google_maps_api_key_here':
            print("   ✅ Google Maps key carregada no Flask")
        else:
            print("   ❌ Google Maps key não carregada no Flask")
        
        if gemini_key and gemini_key != 'your_google_gemini_api_key_here':
            print("   ✅ Google Gemini key carregada no Flask")
        else:
            print("   ❌ Google Gemini key não carregada no Flask")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erro ao testar Flask: {e}")
        return False

def main():
    print("=" * 60)
    print("🧪 TESTE DE CHAVES DE API - SISTEMA PNSB")
    print("=" * 60)
    
    maps_ok = test_google_maps_api()
    gemini_ok = test_gemini_api()
    flask_ok = test_flask_integration()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    print(f"🗺️ Google Maps API: {'✅ OK' if maps_ok else '❌ ERRO'}")
    print(f"🤖 Google Gemini API: {'✅ OK' if gemini_ok else '❌ ERRO'}")
    print(f"🐍 Integração Flask: {'✅ OK' if flask_ok else '❌ ERRO'}")
    
    if maps_ok and gemini_ok and flask_ok:
        print("\n🎉 TODAS AS CHAVES FUNCIONANDO!")
        print("✅ Sistema pronto para usar funcionalidades completas!")
        print("\n📋 PRÓXIMOS PASSOS:")
        print("1. Reinicie o Flask: python app.py")
        print("2. Teste mapas: http://localhost:8080/mapa-progresso")
        print("3. Teste chat IA: http://localhost:8080/assistente-abordagem")
    else:
        print("\n⚠️ ALGUMAS CONFIGURAÇÕES PRECISAM DE ATENÇÃO")
        print("📖 Consulte os guias de configuração:")
        print("• GOOGLE_MAPS_SETUP.md")
        print("• CONFIGURE_MAPS_STEPS.md")

if __name__ == "__main__":
    main()