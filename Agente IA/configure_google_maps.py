#!/usr/bin/env python3
"""
Script para configurar Google Maps API no projeto PNSB
Execute: python configure_google_maps.py
"""

import os
import re
import requests
import sys
from pathlib import Path

def print_header():
    print("=" * 60)
    print("🗺️  CONFIGURAÇÃO GOOGLE MAPS API - SISTEMA PNSB")
    print("=" * 60)
    print()

def validate_api_key_format(api_key):
    """Valida o formato básico da chave de API"""
    if not api_key:
        return False
    
    # Chaves do Google Maps geralmente começam com "AIza" e têm 39 caracteres
    if not api_key.startswith('AIza'):
        return False
    
    if len(api_key) != 39:
        return False
    
    # Deve conter apenas caracteres alfanuméricos, hífens e underscores
    if not re.match(r'^[A-Za-z0-9\-_]+$', api_key):
        return False
    
    return True

def test_api_key(api_key):
    """Testa a chave de API fazendo uma requisição real"""
    print("🔍 Testando chave de API...")
    
    # Teste com Geocoding API (mais simples)
    test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Itajaí,SC,Brasil&key={api_key}"
    
    try:
        response = requests.get(test_url, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            print("✅ Chave de API válida e funcionando!")
            return True
        elif data.get('status') == 'REQUEST_DENIED':
            print("❌ Chave de API inválida ou APIs não ativadas")
            print(f"Erro: {data.get('error_message', 'Erro desconhecido')}")
            return False
        elif data.get('status') == 'OVER_QUERY_LIMIT':
            print("⚠️ Cota da API excedida, mas chave parece válida")
            return True
        else:
            print(f"❌ Erro na API: {data.get('status')}")
            print(f"Mensagem: {data.get('error_message', 'Erro desconhecido')}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False

def update_env_file(api_key):
    """Atualiza o arquivo .env com a nova chave"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ Arquivo .env não encontrado!")
        return False
    
    # Ler conteúdo atual
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir a linha da chave do Google Maps
    new_content = re.sub(
        r'GOOGLE_MAPS_API_KEY=.*',
        f'GOOGLE_MAPS_API_KEY={api_key}',
        content
    )
    
    # Salvar arquivo atualizado
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Arquivo .env atualizado com sucesso!")
    return True

def show_setup_instructions():
    """Mostra instruções detalhadas de configuração"""
    print("📋 INSTRUÇÕES PARA OBTER SUA CHAVE DE API:")
    print()
    print("1. 🌐 Acesse: https://console.cloud.google.com/")
    print("2. 📁 Crie um novo projeto ou selecione existente")
    print("3. 🔧 Ative as seguintes APIs:")
    print("   • Maps JavaScript API")
    print("   • Geocoding API")
    print("   • Directions API")
    print("   • Distance Matrix API")
    print("4. 🔑 Crie uma chave de API em 'Credenciais'")
    print("5. 🔒 Configure restrições de segurança:")
    print("   • Referenciadores HTTP: http://localhost:8080/*")
    print("   • Restringir às APIs ativadas")
    print("6. 💳 Configure faturamento (obrigatório, mas tem cota gratuita)")
    print()
    print("📖 Guia completo: Veja o arquivo GOOGLE_MAPS_SETUP.md")
    print()

def check_current_config():
    """Verifica a configuração atual"""
    try:
        from gestao_visitas.config.security import SecurityConfig
        current_key = SecurityConfig.get_google_maps_key()
        
        if current_key and current_key != 'your_google_maps_api_key_here':
            print(f"🔍 Chave atual encontrada: {current_key[:10]}...{current_key[-5:]}")
            return current_key
        else:
            print("⚠️ Nenhuma chave configurada")
            return None
    except Exception as e:
        print(f"❌ Erro ao verificar configuração: {e}")
        return None

def main():
    print_header()
    
    # Verificar configuração atual
    current_key = check_current_config()
    
    # Se já tem chave, perguntar se quer testar ou trocar
    if current_key:
        print("\nOpções:")
        print("1. Testar chave atual")
        print("2. Configurar nova chave")
        print("3. Ver instruções de configuração")
        print("4. Sair")
        
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == '1':
            if test_api_key(current_key):
                print("\n🎉 Sua configuração está funcionando perfeitamente!")
                return
            else:
                print("\n❌ Problemas com a chave atual. Configure uma nova.")
        elif choice == '3':
            show_setup_instructions()
            return
        elif choice == '4':
            return
        # Se escolheu 2 ou teve problemas, continua para configurar nova chave
    
    # Mostrar instruções
    show_setup_instructions()
    
    # Solicitar nova chave
    while True:
        print("🔑 Cole sua chave de API do Google Maps:")
        api_key = input("Chave: ").strip()
        
        if not api_key:
            print("❌ Chave não pode estar vazia!")
            continue
        
        # Validar formato
        if not validate_api_key_format(api_key):
            print("❌ Formato de chave inválido!")
            print("   • Deve começar com 'AIza'")
            print("   • Deve ter 39 caracteres")
            print("   • Apenas letras, números, hífens e underscores")
            continue
        
        # Testar chave
        if test_api_key(api_key):
            # Atualizar arquivo .env
            if update_env_file(api_key):
                print("\n🎉 CONFIGURAÇÃO CONCLUÍDA COM SUCESSO!")
                print()
                print("📋 PRÓXIMOS PASSOS:")
                print("1. Reinicie o Flask: Ctrl+C e execute 'python app.py'")
                print("2. Teste o mapa em: http://localhost:8080/mapa-progresso")
                print("3. Verifique rotas em: http://localhost:8080/visitas")
                print()
                print("📊 MONITORAMENTO:")
                print("• Acompanhe uso: https://console.cloud.google.com/apis/dashboard")
                print("• Configure alertas de cota para evitar custos inesperados")
                break
            else:
                print("❌ Erro ao salvar configuração")
        else:
            retry = input("\n❌ Chave inválida. Tentar novamente? (s/n): ").lower()
            if retry != 's':
                break

if __name__ == "__main__":
    main()