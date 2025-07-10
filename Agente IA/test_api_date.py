#!/usr/bin/env python3
"""
Teste para verificar se a API permite datas passadas após a correção.
"""

import requests
import json
from datetime import datetime, date, timedelta

def test_api_date_validation():
    """Testa se a API aceita datas passadas."""
    
    base_url = "http://localhost:8080"
    
    print("🔍 Testando API de visitas com datas passadas...")
    
    # Data de ontem
    ontem = date.today() - timedelta(days=1)
    
    # Dados de teste
    visita_data = {
        "municipio": "Itajaí",
        "data": ontem.strftime('%Y-%m-%d'),
        "hora_inicio": "14:00",
        "hora_fim": "15:00",
        "local": "Prefeitura de Itajaí",
        "tipo_pesquisa": "MRS",
        "tipo_informante": "prefeitura",
        "observacoes": "Teste de data passada"
    }
    
    try:
        # Testar criação de visita com data passada
        print(f"📝 Testando criação de visita para {ontem.strftime('%d/%m/%Y')}...")
        
        response = requests.post(
            f"{base_url}/api/visitas",
            json=visita_data,
            headers={'Content-Type': 'application/json'},
            timeout=10
        )
        
        if response.status_code == 201:
            print("✅ SUCESSO: Visita criada com data passada!")
            visita_criada = response.json()
            visita_id = visita_criada.get('id')
            
            if visita_id:
                # Testar atualização com data ainda mais passada
                data_mais_passada = ontem - timedelta(days=5)
                
                visita_data_update = visita_data.copy()
                visita_data_update['data'] = data_mais_passada.strftime('%Y-%m-%d')
                visita_data_update['observacoes'] = "Teste de atualização para data mais passada"
                
                print(f"📝 Testando atualização para {data_mais_passada.strftime('%d/%m/%Y')}...")
                
                response_update = requests.put(
                    f"{base_url}/api/visitas/{visita_id}",
                    json=visita_data_update,
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                if response_update.status_code == 200:
                    print("✅ SUCESSO: Visita atualizada com data passada!")
                    return True
                else:
                    print(f"❌ ERRO na atualização: {response_update.status_code}")
                    print(f"   Resposta: {response_update.text}")
                    return False
            else:
                print("⚠️ Visita criada mas sem ID retornado")
                return False
                
        else:
            print(f"❌ ERRO na criação: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar à API")
        print("   Certifique-se que o sistema está rodando com 'python app.py'")
        return False
    except Exception as e:
        print(f"❌ ERRO inesperado: {e}")
        return False

def show_test_instructions():
    """Mostra instruções para o teste."""
    print("=" * 60)
    print("🧪 TESTE DE VALIDAÇÃO DE DATAS VIA API")
    print("=" * 60)
    print("")
    print("📋 INSTRUÇÕES:")
    print("1. Certifique-se que o sistema está rodando:")
    print("   python app.py")
    print("")
    print("2. Deixe o sistema executando e abra outro terminal")
    print("")
    print("3. Execute este teste:")
    print("   python test_api_date.py")
    print("")
    print("4. O teste tentará:")
    print("   ✅ Criar visita com data passada")
    print("   ✅ Atualizar visita para data ainda mais passada")
    print("")

if __name__ == "__main__":
    show_test_instructions()
    
    resultado = test_api_date_validation()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    if resultado:
        print("🎉 TESTE PASSOU!")
        print("   ✅ API aceita datas passadas")
        print("   ✅ Tanto criação quanto atualização funcionam")
        print("   ✅ Sistema pronto para uso")
    else:
        print("❌ TESTE FALHOU!")
        print("   Pode haver validações adicionais não removidas")
        print("   Verifique se o sistema está rodando")
    
    print("=" * 60)