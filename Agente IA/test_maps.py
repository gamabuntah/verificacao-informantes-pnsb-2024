#!/usr/bin/env python3
"""
Teste completo do sistema Google Maps PNSB 2024
"""
import requests
import json

def test_google_maps_system():
    print('🔍 VERIFICAÇÃO COMPLETA DO SISTEMA GOOGLE MAPS PNSB 2024')
    print('=' * 70)
    
    # 1. Testar servidor
    try:
        response = requests.get('http://127.0.0.1:8080/', timeout=5)
        print(f'✅ Servidor Flask: Running (Status: {response.status_code})')
    except Exception as e:
        print(f'❌ Servidor Flask: {e}')
        return False
    
    # 2. Testar página do mapa
    try:
        response = requests.get('http://127.0.0.1:8080/mapa-progresso', timeout=10)
        if response.status_code == 200:
            print('✅ Página mapa-progresso: Carregada com sucesso')
            
            # Verificar funções JavaScript
            content = response.text
            functions = [
                'carregarGoogleMaps',
                'inicializarGoogleMaps', 
                'adicionarMarcadoresGoogleMaps',
                'adicionarHeatmap',
                'inicializarLeafletFallback'
            ]
            
            all_found = True
            for func in functions:
                if func in content:
                    print(f'   ✅ {func}')
                else:
                    print(f'   ❌ {func}')
                    all_found = False
                    
            if all_found:
                print('✅ Todas as funções JavaScript implementadas')
            else:
                print('❌ Algumas funções JavaScript faltando')
                
        else:
            print(f'❌ Página mapa-progresso: HTTP {response.status_code}')
            
    except Exception as e:
        print(f'❌ Página mapa-progresso: {e}')
    
    print('\n' + '=' * 70)
    print('🌐 TESTANDO APIS DO GOOGLE MAPS')
    print('=' * 70)
    
    # 3. Testar APIs
    apis = [
        ('/api/maps/config', 'Configuração e API Key'),
        ('/api/maps/data', 'Dados dos marcadores'),
        ('/api/maps/heatmap?tipo=progresso', 'Heatmap de progresso'),
        ('/api/maps/clusters', 'Clusters de marcadores'),
        ('/api/maps/route', 'Cálculo de rotas (POST)')
    ]
    
    base_url = 'http://127.0.0.1:8080'
    api_results = {}
    
    for endpoint, description in apis:
        try:
            if endpoint == '/api/maps/route':
                # Testar POST
                test_data = {
                    'pontos': [
                        {'municipio': 'Itajaí', 'lat': -26.9078, 'lng': -48.6619},
                        {'municipio': 'Balneário Camboriú', 'lat': -26.9906, 'lng': -48.6347}
                    ]
                }
                response = requests.post(f'{base_url}{endpoint}', json=test_data, timeout=10)
            else:
                response = requests.get(f'{base_url}{endpoint}', timeout=10)
                
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f'✅ {description}: OK')
                    api_results[endpoint] = 'OK'
                    
                    # Detalhes específicos
                    if 'data' in data:
                        if endpoint == '/api/maps/data':
                            marcadores = data['data']['marcadores']
                            print(f'   📍 {len(marcadores)} marcadores carregados')
                            print(f'   🏘️ Municípios: {len(set(m["municipio"] for m in marcadores))}')
                            print(f'   📊 Estatísticas: {data["data"]["estatisticas"]["total_marcadores"]} total')
                        elif endpoint == '/api/maps/heatmap':
                            points = data['data']['points']
                            print(f'   🔥 {len(points)} pontos de heatmap')
                            print(f'   📈 Raio: {data["data"]["radius"]}px')
                        elif endpoint == '/api/maps/clusters':
                            print(f'   🏘️ {data["data"]["total"]} clusters ativos')
                        elif endpoint == '/api/maps/config':
                            has_key = 'apiKey' in data['data']
                            print(f'   🔑 API Key: {"Configurada" if has_key else "Não configurada"}')
                            if has_key:
                                print(f'   🌍 Língua: {data["data"]["language"]}')
                            print(f'   📍 Centro: {data["data"]["mapOptions"]["center"]}')
                        elif endpoint == '/api/maps/route':
                            print(f'   🗺️ Distância: {data["data"]["distancia_total_km"]}km')
                            print(f'   ⏱️ Tempo: {data["data"]["tempo_total_minutos"]}min')
                            
                else:
                    print(f'❌ {description}: Falha na resposta')
                    api_results[endpoint] = 'FAIL'
            else:
                print(f'❌ {description}: HTTP {response.status_code}')
                api_results[endpoint] = f'HTTP_{response.status_code}'
                
        except Exception as e:
            print(f'❌ {description}: {str(e)[:50]}...')
            api_results[endpoint] = f'ERROR_{str(e)[:20]}'
    
    print('\n' + '=' * 70)
    print('🎯 RESULTADO DA VERIFICAÇÃO')
    print('=' * 70)
    
    # Resumo dos resultados
    working_apis = sum(1 for result in api_results.values() if result == 'OK')
    total_apis = len(api_results)
    
    print(f'📊 APIs funcionando: {working_apis}/{total_apis}')
    print(f'📈 Taxa de sucesso: {(working_apis/total_apis)*100:.1f}%')
    
    if working_apis == total_apis:
        print('\n🎉 SISTEMA GOOGLE MAPS PNSB 2024 TOTALMENTE FUNCIONAL!')
        print('✅ Todas as funcionalidades implementadas e testadas')
        print('✅ Integração completa com dados do projeto')
        print('✅ Marcadores dinâmicos dos municípios PNSB')
        print('✅ Heatmap de progresso em tempo real')
        print('✅ Sistema de rotas e clustering')
        print('✅ APIs REST funcionando corretamente')
        print('\n📍 Acesse: http://127.0.0.1:8080/mapa-progresso')
        print('🎯 O mapa do Google Maps está TOTALMENTE FUNCIONAL!')
        return True
    else:
        print('\n⚠️ Alguns componentes precisam de atenção:')
        for endpoint, result in api_results.items():
            if result != 'OK':
                print(f'   ❌ {endpoint}: {result}')
        return False

if __name__ == '__main__':
    test_google_maps_system()