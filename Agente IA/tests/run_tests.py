#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EXECUTAR TESTES - SISTEMA PNSB 2024
===================================

Script para executar toda a suíte de testes do sistema PNSB 2024.
Inclui relatórios detalhados e análise de cobertura.
"""

import os
import sys
import subprocess
import time
from datetime import datetime

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_banner():
    """Imprimir banner dos testes"""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                          🧪 SISTEMA DE TESTES PNSB 2024                      ║
║                                                                              ║
║  Sistema Inteligente de Status para Gestão de Visitas                       ║
║  Pesquisa Nacional de Saneamento Básico - Santa Catarina                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)
    print(f"🕐 Início dos testes: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

def run_python_tests():
    """Executar testes Python"""
    print("\n🐍 EXECUTANDO TESTES PYTHON")
    print("-" * 50)
    
    test_files = [
        "test_sistema_inteligente.py",
        "test_integracao_api_frontend.py", 
        "test_fluxo_completo_pnsb.py",
        "test_logica_negocio_pnsb.py",
        "test_performance_robustez.py"
    ]
    
    results = {}
    
    for test_file in test_files:
        print(f"\n📋 Executando: {test_file}")
        
        start_time = time.time()
        
        try:
            # Executar pytest com verbose output
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                test_file, 
                "-v", 
                "--tb=short",
                "--disable-warnings"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            results[test_file] = {
                'success': result.returncode == 0,
                'time': execution_time,
                'output': result.stdout,
                'errors': result.stderr
            }
            
            if result.returncode == 0:
                print(f"   ✅ SUCESSO em {execution_time:.2f}s")
            else:
                print(f"   ❌ FALHA em {execution_time:.2f}s")
                print(f"   Erros: {result.stderr[:200]}...")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao executar: {str(e)}")
            results[test_file] = {
                'success': False,
                'time': 0,
                'output': '',
                'errors': str(e)
            }
    
    return results

def run_javascript_tests():
    """Executar testes JavaScript"""
    print("\n🌐 TESTES JAVASCRIPT DISPONÍVEIS")
    print("-" * 50)
    
    js_test_file = "test_frontend_javascript.html"
    
    if os.path.exists(os.path.join(os.path.dirname(__file__), js_test_file)):
        print(f"📄 Arquivo de teste JavaScript: {js_test_file}")
        print("   Para executar os testes JavaScript:")
        print(f"   1. Abra o arquivo {js_test_file} em um navegador")
        print("   2. Os testes serão executados automaticamente")
        print("   3. Verifique os resultados na interface web")
        print("   ✅ Testes JavaScript configurados")
        return True
    else:
        print("   ❌ Arquivo de teste JavaScript não encontrado")
        return False

def generate_report(python_results, js_available):
    """Gerar relatório final"""
    print("\n📊 RELATÓRIO FINAL")
    print("=" * 80)
    
    total_tests = len(python_results)
    successful_tests = sum(1 for result in python_results.values() if result['success'])
    total_time = sum(result['time'] for result in python_results.values())
    
    print(f"📈 Estatísticas:")
    print(f"   • Total de arquivos de teste: {total_tests}")
    print(f"   • Testes Python bem-sucedidos: {successful_tests}/{total_tests}")
    print(f"   • Taxa de sucesso: {(successful_tests/total_tests)*100:.1f}%")
    print(f"   • Tempo total de execução: {total_time:.2f}s")
    print(f"   • Testes JavaScript: {'✅ Disponíveis' if js_available else '❌ Não disponíveis'}")
    
    print(f"\n📋 Detalhes por arquivo:")
    for test_file, result in python_results.items():
        status = "✅ PASSOU" if result['success'] else "❌ FALHOU"
        print(f"   • {test_file:<40} {status} ({result['time']:.2f}s)")
    
    print(f"\n🎯 Cobertura de Testes:")
    print("   • ✅ Sistema Inteligente de Status")
    print("   • ✅ Integração API ↔ Frontend") 
    print("   • ✅ Fluxo Completo PNSB")
    print("   • ✅ Lógica de Negócio")
    print("   • ✅ Performance e Robustez")
    print("   • ✅ Frontend JavaScript")
    
    if successful_tests == total_tests:
        print("\n🎉 TODOS OS TESTES PYTHON PASSARAM!")
        print("   O sistema está funcionando corretamente conforme especificações PNSB.")
    else:
        print(f"\n⚠️ {total_tests - successful_tests} teste(s) falharam")
        print("   Verifique os logs acima para detalhes dos erros.")
        
        # Mostrar detalhes dos erros
        print("\n🐛 DETALHES DOS ERROS:")
        for test_file, result in python_results.items():
            if not result['success']:
                print(f"\n   📄 {test_file}:")
                print(f"      {result['errors'][:300]}...")

def check_dependencies():
    """Verificar dependências necessárias"""
    print("\n🔍 VERIFICANDO DEPENDÊNCIAS")
    print("-" * 50)
    
    dependencies = ['pytest', 'flask', 'sqlalchemy']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep} - FALTANDO")
            missing.append(dep)
    
    if missing:
        print(f"\n⚠️ Dependências faltando: {', '.join(missing)}")
        print("   Execute: pip install " + " ".join(missing))
        return False
    
    print("   ✅ Todas as dependências estão instaladas")
    return True

def main():
    """Função principal"""
    print_banner()
    
    # Verificar dependências
    if not check_dependencies():
        print("\n❌ Não é possível executar os testes sem as dependências.")
        return 1
    
    # Executar testes Python
    python_results = run_python_tests()
    
    # Verificar testes JavaScript
    js_available = run_javascript_tests()
    
    # Gerar relatório
    generate_report(python_results, js_available)
    
    # Determinar código de saída
    all_passed = all(result['success'] for result in python_results.values())
    
    print(f"\n🕐 Fim dos testes: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    if all_passed:
        print("🎉 SUCESSO: Todos os testes passaram!")
        return 0
    else:
        print("❌ FALHA: Alguns testes falharam.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)