#!/usr/bin/env python3
"""
Teste completo de integração das APIs no projeto PNSB
"""

import os
import sys
import requests
import time
from pathlib import Path

def load_env_vars():
    """Carrega variáveis do arquivo .env"""
    env_vars = {}
    env_file = Path('.env')
    
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
    
    return env_vars

def test_google_maps_integration():
    """Testa integração do Google Maps no projeto"""
    print("🗺️ TESTANDO INTEGRAÇÃO GOOGLE MAPS...")
    
    try:
        # Importar e testar o MapaService
        sys.path.append('.')
        from gestao_visitas.services.maps import MapaService
        from gestao_visitas.config.security import SecurityConfig
        
        # Verificar se a chave está carregada
        api_key = SecurityConfig.get_google_maps_key()
        if not api_key or api_key == 'your_google_maps_api_key_here':
            print("   ❌ Chave do Google Maps não configurada")
            return False
        
        print(f"   🔑 Chave carregada: {api_key[:10]}...{api_key[-5:]}")
        
        # Criar instância do serviço
        mapa_service = MapaService(api_key)
        print("   ✅ MapaService criado")
        
        # Testar cálculo de rota
        print("   🚗 Testando cálculo de rota...")
        rota = mapa_service.calcular_rota("Itajaí, SC", "Balneário Camboriú, SC")
        
        if 'erro' in rota:
            print(f"   ❌ Erro na rota: {rota['erro']}")
            return False
        else:
            print(f"   ✅ Rota calculada: {rota.get('distancia', 'N/A')} - {rota.get('duracao', 'N/A')}")
        
        # Testar estimativa de tempo
        print("   ⏱️ Testando estimativa de tempo...")
        tempo = mapa_service.estimar_tempo("Itajaí, SC", "Navegantes, SC")
        
        if 'erro' in tempo:
            print(f"   ❌ Erro na estimativa: {tempo['erro']}")
            return False
        else:
            print(f"   ✅ Tempo estimado: {tempo.get('duracao', 'N/A')}")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_gemini_integration():
    """Testa integração do Gemini no projeto"""
    print("\n🤖 TESTANDO INTEGRAÇÃO GEMINI...")
    
    try:
        # Importar e testar o SecurityConfig
        sys.path.append('.')
        from gestao_visitas.config.security import SecurityConfig
        
        # Verificar se a chave está carregada
        api_key = SecurityConfig.get_google_gemini_key()
        if not api_key or api_key == 'your_google_gemini_api_key_here':
            print("   ❌ Chave do Gemini não configurada")
            return False
        
        print(f"   🔑 Chave carregada: {api_key[:10]}...{api_key[-5:]}")
        
        # Testar API de chat diretamente
        print("   💬 Testando API de chat...")
        
        payload = {
            "contents": [
                {"role": "user", "parts": [{"text": "Responda apenas 'OK' se você está funcionando."}]}
            ]
        }
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={api_key}"
        
        response = requests.post(url, json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result:
                resposta = result['candidates'][0]['content']['parts'][0]['text']
                print(f"   ✅ Gemini respondeu: {resposta.strip()}")
                return True
            else:
                print("   ❌ Resposta da API sem candidatos")
                return False
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_api_endpoints():
    """Testa endpoints da API do Flask"""
    print("\n🌐 TESTANDO ENDPOINTS DA API...")
    
    base_url = "http://localhost:8080"
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code != 200:
            print("   ❌ Servidor Flask não está respondendo")
            return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Servidor Flask não está rodando")
        print("   💡 Execute: python app.py")
        return False
    
    print("   ✅ Servidor Flask rodando")
    
    # Testar endpoint de rota
    print("   🚗 Testando endpoint /api/rota...")
    try:
        rota_data = {
            "origem": "Itajaí, SC",
            "destino": "Balneário Camboriú, SC"
        }
        
        response = requests.post(f"{base_url}/api/rota", json=rota_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("   ✅ Endpoint de rota funcionando")
            else:
                print(f"   ❌ Erro no endpoint: {result.get('message', 'Erro desconhecido')}")
                return False
        elif response.status_code == 503:
            print("   ⚠️ Serviço de mapas não disponível (chave não configurada)")
            return False
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    # Testar endpoint de chat
    print("   💬 Testando endpoint /api/chat...")
    try:
        chat_data = {
            "message": "Diga apenas 'Teste OK'"
        }
        
        response = requests.post(f"{base_url}/api/chat", json=chat_data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                resposta = result.get('data', {}).get('response', '')
                print(f"   ✅ Endpoint de chat funcionando: {resposta.strip()}")
            else:
                print(f"   ❌ Erro no endpoint: {result.get('message', 'Erro desconhecido')}")
                return False
        elif response.status_code == 503:
            print("   ⚠️ Serviço de chat não disponível (chave não configurada)")
            return False
        else:
            print(f"   ❌ Erro HTTP: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    return True

def test_frontend_integration():
    """Testa se o frontend pode usar as APIs"""
    print("\n🖥️ TESTANDO INTEGRAÇÃO FRONTEND...")
    
    # Verificar se as páginas que usam APIs estão carregando
    base_url = "http://localhost:8080"
    
    pages_to_test = [
        ("/mapa-progresso", "Mapa de Progresso"),
        ("/assistente-abordagem", "Assistente de Abordagem"),
        ("/visitas", "Gestão de Visitas")
    ]
    
    try:
        for path, name in pages_to_test:
            response = requests.get(f"{base_url}{path}", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ {name} carregando")
            else:
                print(f"   ❌ {name} erro {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Erro ao testar frontend: {e}")
        return False
    
    return True

def main():
    print("=" * 60)
    print("🧪 TESTE COMPLETO DE INTEGRAÇÃO DAS APIs - PNSB")
    print("=" * 60)
    
    # Carregar variáveis de ambiente
    env_vars = load_env_vars()
    
    # Executar testes
    maps_ok = test_google_maps_integration()
    gemini_ok = test_gemini_integration()
    endpoints_ok = test_api_endpoints()
    frontend_ok = test_frontend_integration()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL DA INTEGRAÇÃO")
    print("=" * 60)
    
    print(f"🗺️ Google Maps Service: {'✅ OK' if maps_ok else '❌ ERRO'}")
    print(f"🤖 Gemini AI Service: {'✅ OK' if gemini_ok else '❌ ERRO'}")
    print(f"🌐 API Endpoints: {'✅ OK' if endpoints_ok else '❌ ERRO'}")
    print(f"🖥️ Frontend Pages: {'✅ OK' if frontend_ok else '❌ ERRO'}")
    
    if all([maps_ok, gemini_ok, endpoints_ok, frontend_ok]):
        print("\n🎉 INTEGRAÇÃO COMPLETA FUNCIONANDO!")
        print("✅ Todas as APIs estão integradas e funcionais!")
        print("\n📋 FUNCIONALIDADES DISPONÍVEIS:")
        print("• 🗺️ Cálculo de rotas otimizadas")
        print("• ⏱️ Estimativas de tempo de viagem")
        print("• 🤖 Chat inteligente com IA")
        print("• 📍 Visualização de mapas interativos")
        print("• 🚗 Planejamento logístico avançado")
        
        print("\n🚀 PRÓXIMOS PASSOS:")
        print("1. Teste as funcionalidades no navegador")
        print("2. Configure alertas de cota no Google Cloud")
        print("3. Monitore uso das APIs")
        
    else:
        print("\n⚠️ ALGUMAS INTEGRAÇÕES PRECISAM DE ATENÇÃO")
        
        if not maps_ok:
            print("🔧 Google Maps: Verifique chave e restrições")
        if not gemini_ok:
            print("🔧 Gemini: Ative Generative Language API")
        if not endpoints_ok:
            print("🔧 Endpoints: Verifique se Flask está rodando")
        if not frontend_ok:
            print("🔧 Frontend: Verifique rotas e templates")

if __name__ == "__main__":
    main()