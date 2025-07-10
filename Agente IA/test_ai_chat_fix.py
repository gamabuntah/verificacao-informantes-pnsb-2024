#!/usr/bin/env python3
"""
Teste específico para verificar se o chat de IA está funcionando corretamente
"""

import requests
import json
import time

def test_ai_chat_endpoint():
    """Testa o endpoint de chat da IA"""
    print("🤖 TESTANDO ENDPOINT DE CHAT DA IA")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    # Verificar se servidor está rodando
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code != 200:
            print("❌ Servidor Flask não está respondendo")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Servidor Flask não está rodando")
        print("💡 Execute: python app.py")
        return False
    
    print("✅ Servidor Flask rodando")
    
    # Testes específicos do chat
    test_messages = [
        {
            "message": "Qual é a melhor estratégia para abordar municípios com alta resistência?",
            "context": "PNSB 2024 - Santa Catarina"
        },
        {
            "message": "Como otimizar a logística de visitas aos municípios?",
            "context": "Pesquisa Nacional de Saneamento Básico"
        },
        {
            "message": "Quais são os indicadores de sucesso na coleta de dados?",
            "context": "IBGE - PNSB - Resíduos Sólidos"
        }
    ]
    
    all_tests_passed = True
    
    for i, test_data in enumerate(test_messages, 1):
        print(f"\n🧪 TESTE {i}: {test_data['message'][:50]}...")
        
        try:
            response = requests.post(
                f"{base_url}/api/chat",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('success'):
                    ai_response = result.get('data', {}).get('response', '')
                    is_fallback = result.get('data', {}).get('fallback_used', False)
                    source = result.get('data', {}).get('source', 'unknown')
                    
                    print(f"✅ Status: Sucesso")
                    print(f"📝 Resposta: {ai_response[:100]}...")
                    print(f"🔧 Fonte: {source}")
                    print(f"⚠️ Fallback usado: {'Sim' if is_fallback else 'Não'}")
                    
                    if is_fallback:
                        print("💡 API Gemini não disponível, usando respostas padrão")
                    else:
                        print("🤖 API Gemini funcionando!")
                        
                else:
                    print(f"❌ Erro na API: {result.get('message', 'Erro desconhecido')}")
                    all_tests_passed = False
                    
            else:
                print(f"❌ Erro HTTP: {response.status_code}")
                print(f"Resposta: {response.text}")
                all_tests_passed = False
                
        except Exception as e:
            print(f"❌ Erro no teste: {e}")
            all_tests_passed = False
        
        time.sleep(1)  # Pausa entre testes
    
    return all_tests_passed

def test_frontend_integration():
    """Testa se a página do mapa está carregando corretamente"""
    print("\n🖥️ TESTANDO INTEGRAÇÃO FRONTEND")
    print("=" * 50)
    
    base_url = "http://localhost:8080"
    
    try:
        response = requests.get(f"{base_url}/mapa-progresso", timeout=10)
        
        if response.status_code == 200:
            content = response.text
            
            # Verificar se as funções JS estão presentes
            checks = [
                ('queryAIAssistant', 'Função de chat da IA'),
                ('buildPNSBContext', 'Função de contexto PNSB'),
                ('displayAIResponse', 'Função de exibição de resposta'),
                ('ai-query-input', 'Campo de input da IA'),
                ('/api/chat', 'Endpoint da API de chat')
            ]
            
            print("🔍 Verificando elementos da página:")
            
            for check, description in checks:
                if check in content:
                    print(f"  ✅ {description}")
                else:
                    print(f"  ❌ {description} - NÃO ENCONTRADO")
                    return False
            
            print("✅ Página do mapa carregando corretamente")
            return True
            
        else:
            print(f"❌ Erro ao carregar página: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar frontend: {e}")
        return False

def main():
    print("🔧 TESTE DE CORREÇÃO DO CHAT DE IA - MAPA PROGRESSO")
    print("=" * 60)
    print()
    
    # Teste 1: Endpoint da API
    api_test = test_ai_chat_endpoint()
    
    # Teste 2: Frontend
    frontend_test = test_frontend_integration()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    print(f"🌐 API Chat Endpoint: {'✅ OK' if api_test else '❌ ERRO'}")
    print(f"🖥️ Frontend Integration: {'✅ OK' if frontend_test else '❌ ERRO'}")
    
    if api_test and frontend_test:
        print("\n🎉 CORREÇÃO APLICADA COM SUCESSO!")
        print("✅ O chat de IA no Mapa de Progresso deve estar funcionando!")
        print("\n📋 COMO TESTAR:")
        print("1. Acesse: http://localhost:8080/mapa-progresso")
        print("2. Localize o painel 'Agente de Estratégia IA'")
        print("3. Digite uma pergunta sobre PNSB")
        print("4. Clique no botão de enviar")
        print("5. Aguarde a resposta da IA")
        
        print("\n💡 EXEMPLOS DE PERGUNTAS:")
        print("• 'Qual melhor horário para contatar prefeituras?'")
        print("• 'Como abordar municípios resistentes?'")
        print("• 'Estratégia para otimizar as visitas?'")
        
    else:
        print("\n⚠️ ALGUNS PROBLEMAS DETECTADOS")
        if not api_test:
            print("🔧 Verifique se a API Gemini está configurada")
        if not frontend_test:
            print("🔧 Verifique se as modificações no template foram aplicadas")

if __name__ == "__main__":
    main()