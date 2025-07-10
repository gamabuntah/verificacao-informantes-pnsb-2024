#!/usr/bin/env python3
"""
Script para testar a funcionalidade do autocomplete com "ambos"
"""

import requests
import json

def testar_dados_csv():
    """Testa se os dados CSV estão sendo carregados corretamente"""
    
    print("🔍 TESTE DO AUTOCOMPLETE - AMBOS")
    print("=" * 40)
    
    try:
        # Testar endpoint de dados CSV
        response = requests.get('http://127.0.0.1:8080/api/contatos_csv')
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dados CSV carregados: {len(data)} registros")
            
            # Verificar municípios disponíveis
            municipios = set()
            tipos_pesquisa = set()
            campos = set()
            
            for item in data:
                municipios.add(item.get('municipio', ''))
                tipos_pesquisa.add(item.get('tipo_pesquisa', ''))
                campos.add(item.get('campo', ''))
            
            print(f"📍 Municípios: {sorted(municipios)}")
            print(f"🔬 Tipos de pesquisa: {sorted(tipos_pesquisa)}")
            print(f"📝 Campos disponíveis: {sorted(campos)}")
            
            # Verificar dados de "local"
            dados_local = [item for item in data if 'local' in item.get('campo', '').lower()]
            print(f"🏢 Registros de 'local': {len(dados_local)}")
            
            if dados_local:
                print("\n📊 Amostra de dados de 'local':")
                for i, item in enumerate(dados_local[:3]):
                    print(f"  {i+1}. Município: {item.get('municipio')}")
                    print(f"     Tipo: {item.get('tipo_pesquisa')}")
                    print(f"     ChatGPT: {item.get('chatgpt', '')[:50]}...")
                    print(f"     Gemini: {item.get('gemini', '')[:50]}...")
                    print(f"     Mais Provável: {item.get('mais_provavel', '')[:50]}...")
                    print()
            
            # Testar distribuição por tipo de pesquisa
            mrs_count = len([item for item in dados_local if item.get('tipo_pesquisa') == 'MRS'])
            map_count = len([item for item in dados_local if item.get('tipo_pesquisa') == 'MAP'])
            
            print(f"📈 Distribuição de locais:")
            print(f"   MRS: {mrs_count} registros")
            print(f"   MAP: {map_count} registros")
            print(f"   Total que seria mostrado com 'ambos': {mrs_count + map_count}")
            
        else:
            print(f"❌ Erro ao carregar dados: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na conexão: {e}")

def testar_funcionalidade_interface():
    """Mostra instruções para testar a interface"""
    
    print("\n🖥️ TESTE NA INTERFACE")
    print("=" * 25)
    print("Para testar a nova funcionalidade:")
    print("1. Acesse: http://127.0.0.1:8080")
    print("2. Vá em 'Visitas' → 'Agendar Nova Visita'")
    print("3. Selecione um município (ex: Balneário Camboriú)")
    print("4. Selecione 'Ambos - MRS + MAP' no tipo de pesquisa")
    print("5. Clique no campo 'Local'")
    print("6. Verifique se aparecem sugestões de AMBOS os tipos com indicadores coloridos:")
    print("   🔴 MRS (vermelho)")
    print("   🔵 MAP (azul)")
    print("7. Compare com a seleção individual de MRS ou MAP")
    
    print("\n💡 O que deve funcionar:")
    print("✅ Mais sugestões quando 'ambos' selecionado (até 12 ao invés de 8)")
    print("✅ Indicadores visuais MRS/MAP nas sugestões")
    print("✅ Organização: primeiro MRS, depois MAP")
    print("✅ Prioritização: Mais Provável → ChatGPT → Gemini → Grok")

if __name__ == "__main__":
    testar_dados_csv()
    testar_funcionalidade_interface()
    
    print("\n🎉 Teste concluído!")
    print("💬 Se tudo estiver funcionando, a funcionalidade 'ambos' está pronta!")