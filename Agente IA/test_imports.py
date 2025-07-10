#!/usr/bin/env python3
"""
Script para testar imports e diagnosticar problemas de dependências.
Execute este script antes de rodar o app.py para identificar problemas.
"""

import sys
import os
from pathlib import Path

def test_basic_imports():
    """Testa imports básicos do Python."""
    print("🔍 Testando imports básicos do Python...")
    
    try:
        import os, sys, json, datetime
        print("✅ Imports básicos: OK")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports básicos: {e}")
        return False

def test_flask_imports():
    """Testa imports do Flask."""
    print("\n🔍 Testando imports do Flask...")
    
    try:
        import flask
        from flask import Flask, request, render_template
        from flask_sqlalchemy import SQLAlchemy
        from flask_login import LoginManager
        from flask_migrate import Migrate
        print("✅ Flask e extensões: OK")
        return True
    except Exception as e:
        print(f"❌ Erro nos imports do Flask: {e}")
        print("💡 Execute: pip install Flask Flask-SQLAlchemy Flask-Login Flask-Migrate")
        return False

def test_external_libraries():
    """Testa bibliotecas externas."""
    print("\n🔍 Testando bibliotecas externas...")
    
    libraries = [
        ("python-dotenv", "dotenv"),
        ("requests", "requests"),
        ("pandas", "pandas"),
        ("googlemaps", "googlemaps"),
        ("geopy", "geopy"),
        ("openpyxl", "openpyxl")
    ]
    
    all_ok = True
    for lib_name, import_name in libraries:
        try:
            __import__(import_name)
            print(f"✅ {lib_name}: OK")
        except ImportError:
            print(f"❌ {lib_name}: NÃO ENCONTRADO")
            print(f"   Execute: pip install {lib_name}")
            all_ok = False
        except Exception as e:
            print(f"⚠️  {lib_name}: ERRO - {e}")
            all_ok = False
    
    return all_ok

def test_project_imports():
    """Testa imports específicos do projeto."""
    print("\n🔍 Testando imports do projeto...")
    
    # Adicionar o diretório do projeto ao path
    project_dir = Path(__file__).parent
    sys.path.insert(0, str(project_dir))
    
    imports_to_test = [
        "gestao_visitas.config.security",
        "gestao_visitas.models.agendamento",
        "gestao_visitas.services.rastreamento_questionarios",
        "gestao_visitas.services.dashboard_avancado",
        "gestao_visitas.routes.api"
    ]
    
    all_ok = True
    for import_path in imports_to_test:
        try:
            __import__(import_path)
            print(f"✅ {import_path}: OK")
        except ImportError as e:
            print(f"❌ {import_path}: ERRO - {e}")
            all_ok = False
        except Exception as e:
            print(f"⚠️  {import_path}: ERRO - {e}")
            all_ok = False
    
    return all_ok

def test_environment_variables():
    """Testa variáveis de ambiente."""
    print("\n🔍 Testando variáveis de ambiente...")
    
    # Tentar carregar .env
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ python-dotenv carregado")
    except ImportError:
        print("❌ python-dotenv não encontrado")
        print("   Execute: pip install python-dotenv")
    except Exception as e:
        print(f"⚠️  Erro ao carregar .env: {e}")
    
    # Verificar variáveis importantes
    env_vars = ["SECRET_KEY", "GOOGLE_MAPS_API_KEY", "GOOGLE_GEMINI_API_KEY"]
    found_vars = 0
    
    for var in env_vars:
        value = os.getenv(var)
        if value and not value.startswith('your_'):
            print(f"✅ {var}: Configurada")
            found_vars += 1
        else:
            print(f"⚠️  {var}: Não configurada (usará valores padrão)")
    
    print(f"📊 {found_vars}/{len(env_vars)} variáveis configuradas")
    return True

def test_database_connection():
    """Testa conexão com banco de dados."""
    print("\n🔍 Testando banco de dados...")
    
    try:
        from sqlalchemy import create_engine
        
        # Testar SQLite local
        db_path = Path(__file__).parent / "gestao_visitas" / "gestao_visitas.db"
        db_url = f"sqlite:///{db_path}"
        
        engine = create_engine(db_url)
        connection = engine.connect()
        connection.close()
        
        print(f"✅ Banco SQLite: OK ({db_path})")
        return True
        
    except Exception as e:
        print(f"❌ Erro no banco de dados: {e}")
        print("💡 O banco será criado automaticamente na primeira execução")
        return True  # Não é erro crítico

def generate_diagnostic_report():
    """Gera relatório completo de diagnóstico."""
    print("=" * 60)
    print("🔧 DIAGNÓSTICO DE DEPENDÊNCIAS - SISTEMA PNSB")
    print("=" * 60)
    
    tests = [
        ("Imports Básicos", test_basic_imports),
        ("Flask e Extensões", test_flask_imports),
        ("Bibliotecas Externas", test_external_libraries),
        ("Imports do Projeto", test_project_imports),
        ("Variáveis de Ambiente", test_environment_variables),
        ("Banco de Dados", test_database_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro durante teste '{test_name}': {e}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO FINAL")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"   {status:<12} {test_name}")
    
    print(f"\n📈 Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 SISTEMA PRONTO PARA EXECUÇÃO!")
        print("   Execute: python app.py")
    elif passed >= total - 1:
        print("\n✅ SISTEMA QUASE PRONTO!")
        print("   Pode tentar executar: python app.py")
        print("   Alguns recursos opcionais podem não funcionar")
    else:
        print("\n⚠️  SISTEMA PRECISA DE CORREÇÕES!")
        print("   Instale as dependências faltantes antes de executar")
    
    print("=" * 60)
    return passed, total

if __name__ == "__main__":
    try:
        passed, total = generate_diagnostic_report()
        
        # Exit code baseado no resultado
        if passed == total:
            sys.exit(0)  # Tudo OK
        elif passed >= total - 1:
            sys.exit(1)  # Problemas menores
        else:
            sys.exit(2)  # Problemas críticos
            
    except Exception as e:
        print(f"\n❌ Erro crítico durante diagnóstico: {e}")
        sys.exit(3)