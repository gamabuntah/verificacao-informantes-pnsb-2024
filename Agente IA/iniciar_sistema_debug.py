#!/usr/bin/env python3
"""
INICIALIZAÇÃO DO SISTEMA EM MODO DEBUG
====================================

Este script inicia o sistema e verifica se há erros.
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

def verificar_dependencias():
    """Verifica se todas as dependências estão instaladas."""
    print("🔍 VERIFICANDO DEPENDÊNCIAS...")
    
    dependencias = [
        'flask', 'sqlalchemy', 'flask_sqlalchemy', 'flask_migrate',
        'pandas', 'requests', 'werkzeug'
    ]
    
    faltando = []
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            faltando.append(dep)
    
    if faltando:
        print(f"\n❌ DEPENDÊNCIAS FALTANDO: {', '.join(faltando)}")
        return False
    
    print("✅ TODAS AS DEPENDÊNCIAS OK")
    return True

def testar_importacao_app():
    """Testa se o app pode ser importado."""
    print("\n🔍 TESTANDO IMPORTAÇÃO DO APP...")
    
    try:
        from app import app
        print("✅ App importado com sucesso")
        
        with app.app_context():
            from gestao_visitas.models.agendamento import Visita
            visitas = Visita.query.all()
            print(f"✅ {len(visitas)} visitas encontradas no banco")
            
            for visita in visitas:
                print(f"   - {visita.municipio} ({visita.data}) - {visita.status}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao importar app: {e}")
        import traceback
        traceback.print_exc()
        return False

def iniciar_sistema():
    """Inicia o sistema Flask."""
    print("\n🚀 INICIANDO SISTEMA FLASK...")
    print("=" * 50)
    
    try:
        # Importar e configurar o app
        from app import app
        
        print("✅ App carregado")
        print("🌐 Iniciando servidor em http://localhost:8080")
        print("📝 Logs do sistema:")
        print("-" * 30)
        
        # Iniciar o servidor
        app.run(host='127.0.0.1', port=8080, debug=True, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n🛑 Sistema interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro ao iniciar sistema: {e}")
        import traceback
        traceback.print_exc()

def testar_sistema_externo():
    """Testa o sistema externamente."""
    print("\n🧪 TESTANDO SISTEMA EXTERNAMENTE...")
    
    # Aguardar um pouco para o sistema iniciar
    time.sleep(3)
    
    try:
        # Testar endpoint básico
        response = requests.get('http://localhost:8080/', timeout=5)
        print(f"✅ Página principal: {response.status_code}")
        
        # Testar API de visitas
        response = requests.get('http://localhost:8080/api/visitas', timeout=5)
        print(f"✅ API visitas: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Visitas retornadas: {len(data)}")
            
            for visita in data:
                print(f"   - {visita.get('municipio')} ({visita.get('data')})")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao sistema")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar sistema: {e}")
        return False

def main():
    print("=" * 60)
    print("🔧 INICIALIZAÇÃO DO SISTEMA EM MODO DEBUG")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        return
    
    # 1. Verificar dependências
    if not verificar_dependencias():
        print("\n❌ INSTALE AS DEPENDÊNCIAS FALTANDO PRIMEIRO")
        return
    
    # 2. Testar importação
    if not testar_importacao_app():
        print("\n❌ PROBLEMAS NA IMPORTAÇÃO DO APP")
        return
    
    print("\n" + "=" * 60)
    print("🎯 SISTEMA PRONTO PARA INICIAR!")
    print("=" * 60)
    print()
    print("ℹ️  INSTRUÇÕES:")
    print("   • O sistema será iniciado em http://localhost:8080")
    print("   • Acesse http://localhost:8080/visitas para ver as visitas")
    print("   • Pressione Ctrl+C para parar o sistema")
    print("   • Observe os logs para identificar erros")
    print()
    
    input("Pressione ENTER para iniciar o sistema...")
    
    # 3. Iniciar sistema
    iniciar_sistema()

if __name__ == "__main__":
    main()