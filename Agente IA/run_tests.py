#!/usr/bin/env python3
"""
Script para executar testes do projeto PNSB
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Executa comando e mostra resultado"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:", result.stderr)
    
    if result.returncode != 0:
        print(f"❌ Falha: {description}")
        return False
    else:
        print(f"✅ Sucesso: {description}")
        return True

def main():
    """Função principal"""
    print("🧪 Sistema de Testes - PNSB")
    print("="*50)
    
    # Verificar se estamos no diretório correto
    if not Path("gestao_visitas").exists():
        print("❌ Execute este script do diretório raiz do projeto")
        return 1
    
    # Configurar variáveis de ambiente para testes
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SECRET_KEY'] = 'test_secret_key'
    os.environ['GOOGLE_MAPS_API_KEY'] = 'test_maps_key'
    os.environ['GOOGLE_GEMINI_API_KEY'] = 'test_gemini_key'
    
    success = True
    
    # 1. Verificar se pytest está instalado
    if not run_command("python -m pytest --version", "Verificando pytest"):
        print("💡 Instale as dependências: pip install -r requirements.txt")
        return 1
    
    # 2. Executar testes unitários
    if not run_command("python -m pytest tests/test_models.py -v", "Testes de Modelos"):
        success = False
    
    # 3. Executar testes de validadores
    if not run_command("python -m pytest tests/test_validators.py -v", "Testes de Validadores"):
        success = False
    
    # 4. Executar testes de API
    if not run_command("python -m pytest tests/test_api.py -v", "Testes de API"):
        success = False
    
    # 5. Executar todos os testes com cobertura
    if not run_command("python -m pytest tests/ --cov=gestao_visitas --cov-report=term-missing", "Todos os Testes com Cobertura"):
        success = False
    
    # 6. Gerar relatório HTML de cobertura
    run_command("python -m pytest tests/ --cov=gestao_visitas --cov-report=html", "Relatório HTML de Cobertura")
    
    print("\n" + "="*50)
    if success:
        print("🎉 Todos os testes passaram!")
        print("📊 Relatório de cobertura gerado em: htmlcov/index.html")
    else:
        print("❌ Alguns testes falharam")
    print("="*50)
    
    return 0 if success else 1

if __name__ == '__main__':
    exit(main())