#!/usr/bin/env python3
"""
DEBUG FRONTEND - VISITAS NÃO APARECEM
===================================

Este script cria uma versão de teste simplificada para identificar o problema.
"""

import os
from pathlib import Path

def criar_pagina_debug():
    """Cria uma página de debug simplificada."""
    
    debug_html = '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DEBUG - Visitas PNSB</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .debug-box { border: 2px solid #007bff; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .error { border-color: #dc3545; background-color: #f8d7da; }
        .success { border-color: #28a745; background-color: #d4edda; }
        .warning { border-color: #ffc107; background-color: #fff3cd; }
        .info { border-color: #17a2b8; background-color: #d1ecf1; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        #resultados { margin-top: 20px; }
        .visita-item { background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 3px; }
    </style>
</head>
<body>
    <h1>🔍 DEBUG - Visitas PNSB</h1>
    
    <div class="debug-box info">
        <h3>Teste de Conectividade</h3>
        <button onclick="testarConexao()">Testar Conexão</button>
        <button onclick="testarAPI()">Testar API</button>
        <button onclick="testarVisitas()">Carregar Visitas</button>
        <button onclick="limparResultados()">Limpar</button>
    </div>
    
    <div id="resultados"></div>
    
    <div class="debug-box">
        <h3>Visitas Carregadas:</h3>
        <div id="lista-visitas-debug">Nenhuma visita carregada ainda...</div>
    </div>

    <script>
        console.log('🔍 DEBUG PAGE CARREGADA');
        
        function log(message, type = 'info') {
            const div = document.createElement('div');
            div.className = `debug-box ${type}`;
            div.innerHTML = `<strong>${new Date().toLocaleTimeString()}</strong>: ${message}`;
            document.getElementById('resultados').appendChild(div);
            console.log(message);
        }
        
        function limparResultados() {
            document.getElementById('resultados').innerHTML = '';
            document.getElementById('lista-visitas-debug').innerHTML = 'Nenhuma visita carregada ainda...';
        }
        
        async function testarConexao() {
            log('🔍 Testando conexão com o servidor...', 'info');
            
            try {
                const response = await fetch('/', { 
                    method: 'GET',
                    cache: 'no-cache'
                });
                
                if (response.ok) {
                    log('✅ Conexão com servidor OK (status: ' + response.status + ')', 'success');
                } else {
                    log('❌ Erro na conexão (status: ' + response.status + ')', 'error');
                }
            } catch (error) {
                log('❌ Erro de conexão: ' + error.message, 'error');
            }
        }
        
        async function testarAPI() {
            log('🔍 Testando API /api/visitas...', 'info');
            
            try {
                const response = await fetch('/api/visitas', {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json'
                    },
                    cache: 'no-cache'
                });
                
                log('📊 Status da resposta: ' + response.status, response.ok ? 'success' : 'error');
                log('📊 Headers da resposta: ' + JSON.stringify([...response.headers.entries()]), 'info');
                
                const text = await response.text();
                log('📊 Resposta bruta: ' + text.substring(0, 500) + (text.length > 500 ? '...' : ''), 'info');
                
                if (response.ok) {
                    try {
                        const data = JSON.parse(text);
                        log('✅ API retornou JSON válido com ' + data.length + ' itens', 'success');
                        return data;
                    } catch (parseError) {
                        log('❌ Erro ao fazer parse do JSON: ' + parseError.message, 'error');
                        return null;
                    }
                } else {
                    log('❌ API retornou erro: ' + text, 'error');
                    return null;
                }
            } catch (error) {
                log('❌ Erro na API: ' + error.message, 'error');
                return null;
            }
        }
        
        async function testarVisitas() {
            log('🔍 Carregando visitas...', 'info');
            
            const visitas = await testarAPI();
            
            if (visitas && Array.isArray(visitas)) {
                if (visitas.length === 0) {
                    log('⚠️ API retornou array vazio - nenhuma visita encontrada', 'warning');
                    document.getElementById('lista-visitas-debug').innerHTML = '<em>Nenhuma visita retornada pela API</em>';
                } else {
                    log('✅ Visitas carregadas com sucesso!', 'success');
                    
                    const container = document.getElementById('lista-visitas-debug');
                    container.innerHTML = '';
                    
                    visitas.forEach((visita, index) => {
                        const div = document.createElement('div');
                        div.className = 'visita-item';
                        div.innerHTML = `
                            <strong>Visita ${index + 1}:</strong><br>
                            • ID: ${visita.id}<br>
                            • Município: ${visita.municipio}<br>
                            • Data: ${visita.data}<br>
                            • Status: ${visita.status}<br>
                            • Local: ${visita.local}<br>
                            • Tipo: ${visita.tipo_pesquisa}
                        `;
                        container.appendChild(div);
                        
                        log(`📅 Visita ${index + 1}: ${visita.municipio} (${visita.data}) - ${visita.status}`, 'success');
                    });
                }
            } else {
                log('❌ Dados inválidos retornados pela API', 'error');
                document.getElementById('lista-visitas-debug').innerHTML = '<em style="color: red;">Erro ao carregar visitas</em>';
            }
        }
        
        // Testar automaticamente quando a página carregar
        document.addEventListener('DOMContentLoaded', function() {
            log('🚀 Página de debug carregada - executando testes automáticos...', 'info');
            
            setTimeout(async () => {
                await testarConexao();
                await testarVisitas();
            }, 1000);
        });
    </script>
</body>
</html>'''
    
    # Salvar arquivo de debug
    debug_path = 'gestao_visitas/templates/debug_visitas.html'
    with open(debug_path, 'w', encoding='utf-8') as f:
        f.write(debug_html)
    
    print(f"✅ Página de debug criada: {debug_path}")
    return debug_path

def adicionar_rota_debug():
    """Adiciona rota de debug no app.py."""
    
    # Ler o arquivo app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se a rota já existe
    if '@app.route(\'/debug\')' in content:
        print("✅ Rota de debug já existe")
        return
    
    # Adicionar rota antes do "if __name__ == '__main__':"
    debug_route = '''
@app.route('/debug')
def debug_visitas():
    return render_template('debug_visitas.html')
'''
    
    # Inserir antes da linha final
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if line.strip().startswith("if __name__ == '__main__':"):
            lines.insert(i, debug_route)
            break
    
    # Salvar arquivo modificado
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print("✅ Rota de debug adicionada ao app.py")

def main():
    print("=" * 60)
    print("🔍 CRIANDO PÁGINA DE DEBUG PARA VISITAS")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        return
    
    # 1. Criar página de debug
    debug_path = criar_pagina_debug()
    
    # 2. Adicionar rota de debug
    adicionar_rota_debug()
    
    print("\n" + "=" * 60)
    print("🎯 PÁGINA DE DEBUG CRIADA!")
    print("=" * 60)
    print()
    print("📋 INSTRUÇÕES:")
    print("1. Certifique-se que o sistema está rodando:")
    print("   python app.py")
    print()
    print("2. Acesse a página de debug:")
    print("   http://localhost:8080/debug")
    print()
    print("3. A página irá testar automaticamente:")
    print("   • Conexão com o servidor")
    print("   • API /api/visitas")
    print("   • Carregamento das visitas")
    print()
    print("4. Observe os logs para identificar onde está falhando")
    print()
    print("✅ Esta página de debug irá nos mostrar exatamente")
    print("   onde está o problema na exibição das visitas!")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()