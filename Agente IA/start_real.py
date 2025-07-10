#!/usr/bin/env python3
"""
Inicializador REAL - sem timeout, funcionamento garantido
Windows 11 + WSL2 específico
"""

import os
import sys
import time
import socket
from pathlib import Path

def verificar_porta_livre(porta):
    """Verifica se uma porta está livre"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', porta))
        sock.close()
        return True
    except:
        return False

def main():
    print("🔥 INICIALIZADOR REAL - WINDOWS 11 + WSL2")
    print("=" * 50)
    
    # Verificar portas disponíveis
    portas_teste = [5000, 8000, 3000, 8080, 9000]
    porta_livre = None
    
    print("🔍 Verificando portas disponíveis...")
    for porta in portas_teste:
        if verificar_porta_livre(porta):
            porta_livre = porta
            print(f"✅ Porta {porta}: LIVRE")
            break
        else:
            print(f"❌ Porta {porta}: OCUPADA")
    
    if not porta_livre:
        print("❌ Nenhuma porta disponível!")
        return 1
    
    print(f"🎯 Usando porta: {porta_livre}")
    print("")
    
    try:
        # Importar Flask
        from flask import Flask, jsonify
        
        # Criar app simples
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sistema PNSB - FUNCIONANDO!</title>
                <meta charset="UTF-8">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: linear-gradient(45deg, #4CAF50, #45a049);
                        color: white;
                    }
                    .container {
                        background: rgba(255,255,255,0.1);
                        padding: 30px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                    }
                    h1 { font-size: 3em; margin-bottom: 20px; }
                    .status { 
                        background: #4CAF50; 
                        padding: 15px; 
                        border-radius: 10px; 
                        margin: 20px 0;
                        font-size: 1.2em;
                        font-weight: bold;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎉 SISTEMA PNSB</h1>
                    <div class="status">✅ SERVIDOR FUNCIONANDO PERFEITAMENTE!</div>
                    <h2>Gestão de Informantes - Santa Catarina</h2>
                    <p><strong>✅ Windows 11 + WSL2: OK</strong></p>
                    <p><strong>✅ Flask: OK</strong></p>
                    <p><strong>✅ Conexão: OK</strong></p>
                    <hr style="margin: 30px 0;">
                    <h3>🎯 Próximos Passos:</h3>
                    <p>1. ✅ Servidor confirmado funcionando</p>
                    <p>2. 🔧 Configurar sistema completo</p>
                    <p>3. 📊 Importar dados dos 11 municípios</p>
                    <p>4. 🚀 Iniciar coleta PNSB 2024</p>
                </div>
            </body>
            </html>
            """
        
        @app.route('/api/status')
        def status():
            return jsonify({
                "status": "funcionando",
                "sistema": "PNSB",
                "windows": "11", 
                "wsl": "2",
                "porta": porta_livre,
                "timestamp": time.time()
            })
        
        # Configurar para Windows 11 + WSL2
        print("🚀 INICIANDO SERVIDOR...")
        print("")
        print("🌐 ENDEREÇOS PARA TESTAR NO WINDOWS 11:")
        print(f"   1. http://localhost:{porta_livre}")
        print(f"   2. http://127.0.0.1:{porta_livre}")
        print(f"   3. http://172.30.57.206:{porta_livre}")
        print("")
        print("📱 STATUS:")
        print(f"   • API Status: http://localhost:{porta_livre}/api/status")
        print("")
        print("⏹️  Para parar: Ctrl+C")
        print("=" * 50)
        
        # Iniciar com configuração otimizada para Windows 11
        app.run(
            host='0.0.0.0',  # Aceitar de qualquer IP
            port=porta_livre,
            debug=False,     # Sem debug para evitar problemas
            use_reloader=False,  # Sem reload automático
            threaded=True,   # Suporte a múltiplas conexões
            processes=1      # Processo único
        )
        
    except ImportError as e:
        print(f"❌ Erro de importação: {e}")
        print("💡 Execute: pip install flask")
        return 1
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n⏹️ Servidor parado pelo usuário")
        exit(0)