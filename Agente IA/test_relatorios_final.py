#!/usr/bin/env python3
"""
Teste final para verificar se as visitas aparecem corretamente nos relatórios.
"""

import requests
import json

def test_diferentes_periodos():
    """Testa diferentes períodos de relatório"""
    print("🔍 TESTE FINAL - VISITAS NOS RELATÓRIOS")
    print("=" * 60)
    
    periodos = [
        ('hoje', 'HOJE'),
        ('semana', 'ESTA SEMANA'),
        ('mes', 'ESTE MÊS'),
        ('custom?inicio=2025-06-01&fim=2025-07-31', 'JUN-JUL (PERÍODO COMPLETO)')
    ]
    
    for periodo, nome in periodos:
        print(f"\n📅 TESTANDO: {nome}")
        print("-" * 40)
        
        url = f"http://127.0.0.1:8080/api/relatorios/{periodo}"
        
        try:
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Erro HTTP {response.status_code}")
                continue
            
            data = response.json()
            resumo = data.get('resumo', {})
            detalhes = data.get('detalhes', [])
            
            total_visitas = resumo.get('total_visitas', 0)
            
            print(f"✅ Total de visitas: {total_visitas}")
            
            if total_visitas > 0:
                print(f"   📊 Por município: {resumo.get('por_municipio', {})}")
                print(f"   📊 Por status: {resumo.get('por_status', {})}")
                
                if detalhes:
                    print(f"   📋 Primeira visita:")
                    primeira = detalhes[0].get('dados_visita', {})
                    print(f"      - {primeira.get('municipio')} em {primeira.get('data')} - {primeira.get('status')}")
            else:
                print("   ⚠️  Nenhuma visita encontrada neste período")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
    
    print(f"\n" + "=" * 60)
    print("📋 CONCLUSÕES:")
    print("=" * 60)
    print("✅ Para ver TODAS as visitas: use 'Período Personalizado' com datas de junho/julho")
    print("✅ Para ver visitas de hoje: use 'Hoje' (pode não ter nenhuma)")
    print("✅ Para ver visitas deste mês: use 'Este Mês' (julho - poucas visitas)")
    print("✅ RECOMENDAÇÃO: Use a opção 'Últimos 30 dias' no dropdown")

if __name__ == "__main__":
    test_diferentes_periodos()