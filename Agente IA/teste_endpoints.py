#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
from datetime import datetime, timedelta

def testar_endpoints():
    """Testa os principais endpoints da API"""
    
    base_url = "http://localhost:8080"
    
    print("=" * 80)
    print("TESTE DOS ENDPOINTS DA API")
    print("=" * 80)
    
    endpoints = [
        {"method": "GET", "url": "/api/visitas", "desc": "Listar todas as visitas"},
        {"method": "GET", "url": "/api/contatos", "desc": "Listar contatos"},
        {"method": "GET", "url": "/api/entidades", "desc": "Listar entidades"},
        {"method": "GET", "url": "/api/prestadores", "desc": "Listar prestadores"},
        {"method": "GET", "url": "/api/questionarios/obrigatorios", "desc": "Listar questionários obrigatórios"},
        {"method": "GET", "url": "/api/mapa/progresso", "desc": "Progresso do mapa"},
        {"method": "GET", "url": "/api/relatorios/dashboard", "desc": "Dashboard de relatórios"},
    ]
    
    resultados = []
    
    for endpoint in endpoints:
        print(f"\n📝 Testando: {endpoint['desc']}")
        print(f"   {endpoint['method']} {endpoint['url']}")
        
        try:
            if endpoint['method'] == 'GET':
                response = requests.get(f"{base_url}{endpoint['url']}", timeout=5)
            
            status = response.status_code
            
            if status == 200:
                print(f"   ✅ Status: {status} - OK")
                try:
                    data = response.json()
                    if isinstance(data, list):
                        print(f"   📊 Retornou {len(data)} registros")
                    elif isinstance(data, dict):
                        print(f"   📊 Retornou objeto com {len(data)} campos")
                except:
                    print(f"   📊 Retornou dados (não JSON)")
            else:
                print(f"   ❌ Status: {status} - ERRO")
                resultados.append(f"ERRO em {endpoint['url']}: Status {status}")
        
        except requests.exceptions.ConnectionError:
            print(f"   ❌ ERRO: Servidor não está rodando ou não acessível")
            resultados.append(f"ERRO em {endpoint['url']}: Conexão recusada")
        except requests.exceptions.Timeout:
            print(f"   ❌ ERRO: Timeout na requisição")
            resultados.append(f"ERRO em {endpoint['url']}: Timeout")
        except Exception as e:
            print(f"   ❌ ERRO: {str(e)}")
            resultados.append(f"ERRO em {endpoint['url']}: {str(e)}")
    
    # Teste de criação de visita
    print("\n\n📝 Testando criação de visita")
    try:
        nova_visita = {
            "municipio": "Itajaí",
            "data": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "hora_inicio": "09:00",
            "hora_fim": "11:00",
            "local": "Prefeitura Municipal",
            "tipo_pesquisa": "MRS",
            "tipo_informante": "prefeitura",
            "observacoes": "Teste de API"
        }
        
        response = requests.post(
            f"{base_url}/api/visitas",
            json=nova_visita,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 201:
            print("   ✅ Visita criada com sucesso!")
            visita_criada = response.json()
            print(f"   ID da visita: {visita_criada.get('id')}")
        else:
            print(f"   ❌ Erro ao criar visita: Status {response.status_code}")
            print(f"   Resposta: {response.text}")
            
    except Exception as e:
        print(f"   ❌ ERRO: {str(e)}")
    
    # Resumo
    print("\n\n" + "=" * 80)
    print("RESUMO DOS TESTES")
    print("=" * 80)
    
    if resultados:
        print("\n❌ Problemas encontrados:")
        for problema in resultados:
            print(f"   - {problema}")
    else:
        print("\n✅ Todos os endpoints testados responderam corretamente!")
    
    print("\n⚠️  NOTA: Certifique-se de que o servidor está rodando em http://localhost:8080")

if __name__ == "__main__":
    testar_endpoints()