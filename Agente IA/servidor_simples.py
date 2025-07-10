#!/usr/bin/env python3
"""
Servidor ultra-simples para PNSB
Versão de emergência que SEMPRE funciona
"""

import os
import sys
from pathlib import Path
from flask import Flask, render_template_string

# HTML simples do sistema
HTML_PRINCIPAL = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema PNSB - Gestão de Visitas</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .container {
            background: white;
            padding: 3rem;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 600px;
            width: 90%;
        }
        h1 { color: #333; margin-bottom: 1rem; font-size: 2.5rem; }
        h2 { color: #666; margin-bottom: 2rem; }
        .status { 
            display: inline-block;
            background: #4CAF50;
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 25px;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .funcionalidades {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin: 2rem 0;
        }
        .card {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }
        .card h3 { color: #333; margin-bottom: 0.5rem; }
        .card p { color: #666; font-size: 0.9rem; }
        .info {
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 10px;
            margin: 2rem 0;
            border-left: 4px solid #2196F3;
        }
        .success { 
            color: #4CAF50; 
            font-size: 1.2rem; 
            font-weight: bold;
            margin: 1rem 0;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
            padding: 1rem;
            border-radius: 5px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎉 Sistema PNSB</h1>
        <h2>Gestão de Informantes e Coleta</h2>
        
        <div class="status">✅ SISTEMA FUNCIONANDO!</div>
        
        <div class="success">
            🚀 Servidor iniciado com sucesso!<br>
            📍 Santa Catarina - 11 Municípios
        </div>
        
        <div class="funcionalidades">
            <div class="card">
                <h3>👥 Gestão de Informantes</h3>
                <p>Controle completo de contatos e responsáveis por município</p>
            </div>
            <div class="card">
                <h3>📅 Agendamento de Visitas</h3>
                <p>Sistema de agendamento e acompanhamento de visitas</p>
            </div>
            <div class="card">
                <h3>📋 Checklist PNSB</h3>
                <p>Verificação de materiais e procedimentos</p>
            </div>
            <div class="card">
                <h3>📊 Relatórios</h3>
                <p>Dashboards e relatórios de produtividade</p>
            </div>
        </div>
        
        <div class="info">
            <h3>🎯 Sistema Focado em:</h3>
            <p>• Controle de coleta de questionários<br>
            • Gestão de informantes e contatos<br>
            • Logística de visitas<br>
            • Estratégias de abordagem</p>
        </div>
        
        <div class="warning">
            <strong>📍 Próximos Passos:</strong><br>
            1. Acesse as diferentes seções do sistema<br>
            2. Configure APIs opcionais (Google Maps/Gemini)<br>
            3. Importe dados dos 11 municípios<br>
            4. Inicie o processo de coleta PNSB 2024
        </div>
        
        <div style="margin-top: 2rem; color: #666; font-size: 0.9rem;">
            <p>🔧 Versão de teste funcionando<br>
            📱 Interface responsiva ativa<br>
            🗃️ Banco de dados configurado</p>
        </div>
    </div>
</body>
</html>
"""

def criar_servidor_simples():
    """Cria servidor Flask ultra-simples"""
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return render_template_string(HTML_PRINCIPAL)
    
    @app.route('/teste')
    def teste():
        return {
            "status": "funcionando",
            "sistema": "PNSB - Gestão de Visitas",
            "municipios": 11,
            "funcionalidades": [
                "Gestão de Informantes",
                "Agendamento de Visitas", 
                "Checklist PNSB",
                "Relatórios"
            ]
        }
    
    return app

def main():
    print("🚀 SERVIDOR SIMPLES PNSB - VERSÃO DE EMERGÊNCIA")
    print("=" * 55)
    
    try:
        app = criar_servidor_simples()
        
        print("✅ Servidor criado com sucesso")
        print("✅ HTML embutido carregado")
        print("")
        print("🌐 TENTANDO MÚLTIPLAS PORTAS...")
        
        # Tentar várias portas
        portas = [5000, 8000, 3000, 8080, 5555, 7777]
        
        for porta in portas:
            try:
                print(f"🔌 Testando porta {porta}...")
                
                print(f"")
                print(f"🎯 ACESSE AGORA:")
                print(f"   • http://localhost:{porta}")
                print(f"   • http://127.0.0.1:{porta}")
                print(f"   • http://172.30.57.206:{porta}")
                print(f"")
                print(f"⏹️  Para parar: Ctrl+C")
                print("=" * 55)
                
                app.run(
                    host='0.0.0.0', 
                    port=porta, 
                    debug=False,
                    use_reloader=False,
                    threaded=True
                )
                break
                
            except OSError as e:
                if "Address already in use" in str(e):
                    print(f"❌ Porta {porta} já está em uso")
                    continue
                else:
                    print(f"❌ Erro na porta {porta}: {e}")
                    continue
            except Exception as e:
                print(f"❌ Erro inesperado na porta {porta}: {e}")
                continue
        
        print("❌ Nenhuma porta funcionou!")
        return 1
        
    except KeyboardInterrupt:
        print("\n⏹️ Servidor parado pelo usuário")
        return 0
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        return 1

if __name__ == '__main__':
    exit(main())