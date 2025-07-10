#!/usr/bin/env python3
"""
Servidor para Windows - PNSB
Versão simplificada que funciona diretamente no Windows
"""

from flask import Flask, render_template_string
import os

app = Flask(__name__)

# HTML básico do sistema
HTML_SISTEMA = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema PNSB - Gestão de Visitas</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
        }
        .header h1 {
            color: #333;
            margin: 0;
            font-size: 2.5em;
        }
        .header p {
            color: #666;
            margin: 10px 0 0 0;
            font-size: 1.2em;
        }
        .status {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border: 1px solid #c3e6cb;
        }
        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin-top: 30px;
        }
        .card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 12px;
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        }
        .card h3 {
            color: #333;
            margin-top: 0;
        }
        .btn {
            background: #667eea;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 10px 5px;
            transition: background 0.3s ease;
        }
        .btn:hover {
            background: #5a6fd8;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Sistema PNSB 2024</h1>
            <p>Gestão de Visitas - Santa Catarina</p>
        </div>
        
        <div class="status">
            ✅ <strong>Servidor funcionando!</strong> Sistema PNSB operacional em modo de teste.
        </div>
        
        <div class="cards">
            <div class="card">
                <h3>📋 Gestão de Visitas</h3>
                <p>Agende e gerencie visitas aos 11 municípios de Santa Catarina para coleta de dados MRS e MAP.</p>
                <a href="#" class="btn">Acessar Visitas</a>
            </div>
            
            <div class="card">
                <h3>📞 Contatos</h3>
                <p>Gerencie informações de contato das prefeituras e responsáveis pelos questionários.</p>
                <a href="#" class="btn">Ver Contatos</a>
            </div>
            
            <div class="card">
                <h3>✅ Checklist</h3>
                <p>Acompanhe o progresso das etapas de preparação e execução das visitas.</p>
                <a href="#" class="btn">Abrir Checklist</a>
            </div>
            
            <div class="card">
                <h3>📊 Relatórios</h3>
                <p>Visualize dados consolidados e progresso geral da pesquisa PNSB 2024.</p>
                <a href="#" class="btn">Ver Relatórios</a>
            </div>
        </div>
        
        <div style="margin-top: 40px; text-align: center; color: #666;">
            <p><strong>Municípios:</strong> Balneário Camboriú, Balneário Piçarras, Bombinhas, Camboriú, Itajaí, Itapema, Luiz Alves, Navegantes, Penha, Porto Belo, Ilhota</p>
            <p><strong>Servidor ativo em:</strong> {{ server_info }}</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    server_info = f"localhost:5000 (Windows)"
    return render_template_string(HTML_SISTEMA, server_info=server_info)

@app.route('/health')
def health():
    return {'status': 'ok', 'server': 'PNSB Windows Server'}

if __name__ == '__main__':
    print("=" * 50)
    print("🚀 SERVIDOR PNSB PARA WINDOWS")
    print("=" * 50)
    print("✅ Iniciando servidor Flask...")
    print("🌐 Acesse: http://localhost:5000")
    print("🔧 Para parar: Ctrl+C")
    print("=" * 50)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False)
    except Exception as e:
        print(f"❌ Erro: {e}")
        print("🔧 Tentando porta alternativa 8080...")
        app.run(host='127.0.0.1', port=8080, debug=False)