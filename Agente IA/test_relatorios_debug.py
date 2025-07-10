#!/usr/bin/env python3
"""
Script de debug específico para relatórios - verifica se as visitas estão aparecendo.
"""

import requests
import json

def test_relatorios_api():
    """Testa a API de relatórios detalhadamente"""
    print("🔍 TESTE DETALHADO DA API DE RELATÓRIOS")
    print("=" * 50)
    
    url = "http://127.0.0.1:8080/api/relatorios/mes"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API retornou status {response.status_code}")
            return
        
        data = response.json()
        
        print("📊 ESTRUTURA DOS DADOS:")
        print(f"- Tipo de data: {type(data)}")
        print(f"- Keys principais: {list(data.keys()) if isinstance(data, dict) else 'Não é dict'}")
        
        # Verificar resumo
        resumo = data.get('resumo', {})
        print(f"\n📈 RESUMO:")
        print(f"- Total visitas: {resumo.get('total_visitas', 'N/A')}")
        print(f"- Por status: {resumo.get('por_status', {})}")
        print(f"- Por município: {resumo.get('por_municipio', {})}")
        
        # Verificar detalhes
        detalhes = data.get('detalhes', [])
        print(f"\n📋 DETALHES:")
        print(f"- Quantidade de detalhes: {len(detalhes)}")
        
        if detalhes:
            for i, detalhe in enumerate(detalhes[:3]):  # Mostrar apenas os 3 primeiros
                print(f"\n  📄 Detalhe {i+1}:")
                if 'dados_visita' in detalhe:
                    dados = detalhe['dados_visita']
                    print(f"    - Município: {dados.get('municipio', 'N/A')}")
                    print(f"    - Data: {dados.get('data', 'N/A')}")
                    print(f"    - Hora início: {dados.get('hora_inicio', 'N/A')}")
                    print(f"    - Status: {dados.get('status', 'N/A')}")
                    print(f"    - Informante: {dados.get('informante', 'N/A')}")
                else:
                    print(f"    ❌ Sem 'dados_visita'")
                    print(f"    Keys disponíveis: {list(detalhe.keys()) if isinstance(detalhe, dict) else 'Não é dict'}")
        else:
            print("  ⚠️  Nenhum detalhe encontrado")
        
        # Verificar se tem fallback
        if data.get('fallback'):
            print(f"\n⚠️  ATENÇÃO: API está usando fallback")
            print(f"   Erro: {data.get('erro', 'Desconhecido')}")
        
        print(f"\n✅ Teste da API concluído")
        
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")

def test_direct_visitas():
    """Testa diretamente a API de visitas"""
    print("\n🔍 TESTE DIRETO DA API DE VISITAS")
    print("=" * 50)
    
    url = "http://127.0.0.1:8080/api/visitas"
    
    try:
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ API de visitas retornou status {response.status_code}")
            return
        
        data = response.json()
        
        print(f"📊 DADOS DIRETOS DAS VISITAS:")
        print(f"- Tipo: {type(data)}")
        print(f"- Quantidade: {len(data) if isinstance(data, list) else 'Não é lista'}")
        
        if isinstance(data, list) and data:
            for i, visita in enumerate(data[:3]):  # Mostrar apenas as 3 primeiras
                print(f"\n  📄 Visita {i+1}:")
                print(f"    - ID: {visita.get('id', 'N/A')}")
                print(f"    - Município: {visita.get('municipio', 'N/A')}")
                print(f"    - Data: {visita.get('data', 'N/A')}")
                print(f"    - Status: {visita.get('status', 'N/A')}")
                print(f"    - Tipo informante: {visita.get('tipo_informante', 'N/A')}")
        else:
            print("  ⚠️  Nenhuma visita encontrada ou formato inválido")
            
    except Exception as e:
        print(f"❌ Erro ao testar API de visitas: {e}")

if __name__ == "__main__":
    test_relatorios_api()
    test_direct_visitas()