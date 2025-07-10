#!/usr/bin/env python3
"""
Script para limpar cache e reiniciar o sistema com as mudanças aplicadas.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

def clear_python_cache():
    """Remove cache Python."""
    print("🧹 Limpando cache Python...")
    
    cache_dirs = [
        "__pycache__",
        "gestao_visitas/__pycache__",
        "gestao_visitas/models/__pycache__",
        "gestao_visitas/routes/__pycache__",
        "gestao_visitas/services/__pycache__",
        "gestao_visitas/utils/__pycache__",
        "gestao_visitas/config/__pycache__"
    ]
    
    for cache_dir in cache_dirs:
        cache_path = Path(cache_dir)
        if cache_path.exists():
            try:
                # Remover todos os arquivos .pyc
                for pyc_file in cache_path.glob("*.pyc"):
                    pyc_file.unlink()
                print(f"   ✅ Cache removido: {cache_dir}")
            except Exception as e:
                print(f"   ⚠️ Erro ao remover {cache_dir}: {e}")
        else:
            print(f"   ℹ️ Cache não encontrado: {cache_dir}")

def show_browser_cache_instructions():
    """Mostra instruções para limpar cache do navegador."""
    print("\n🌐 INSTRUÇÕES PARA LIMPAR CACHE DO NAVEGADOR:")
    print("=" * 50)
    print("")
    print("📋 Para garantir que as mudanças sejam aplicadas:")
    print("")
    print("🔸 CHROME/EDGE:")
    print("   • Ctrl + Shift + Delete")
    print("   • Ou F12 → Network → Disable cache")
    print("   • Ou Ctrl + F5 (hard refresh)")
    print("")
    print("🔸 FIREFOX:")
    print("   • Ctrl + Shift + Delete")
    print("   • Ou Ctrl + F5 (hard refresh)")
    print("")
    print("🔸 ALTERNATIVA RÁPIDA:")
    print("   • Abra uma aba anônima/privada")
    print("   • Acesse http://localhost:8080")
    print("")

def verify_changes():
    """Verifica se as mudanças foram aplicadas nos arquivos."""
    print("🔍 Verificando mudanças aplicadas...")
    
    # Verificar validators.py
    validators_path = Path("gestao_visitas/utils/validators.py")
    if validators_path.exists():
        with open(validators_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "data passada para permitir registro histórico" in content:
            print("   ✅ validators.py: Mudança aplicada")
        else:
            print("   ❌ validators.py: Mudança NÃO aplicada")
    
    # Verificar app.py
    app_path = Path("app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "sem restrição de data passada" in content:
            print("   ✅ app.py: Mudança aplicada")
        else:
            print("   ❌ app.py: Mudança NÃO aplicada")
    
    # Verificar visitas.html
    template_path = Path("gestao_visitas/templates/visitas.html")
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "Removido validação de data passada" in content:
            print("   ✅ visitas.html: Mudança aplicada")
        else:
            print("   ❌ visitas.html: Mudança NÃO aplicada")

def main():
    print("=" * 60)
    print("🔄 LIMPEZA DE CACHE E VERIFICAÇÃO - SISTEMA PNSB")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        sys.exit(1)
    
    # Limpar cache Python
    clear_python_cache()
    
    # Verificar mudanças
    verify_changes()
    
    # Instruções de navegador
    show_browser_cache_instructions()
    
    print("=" * 60)
    print("🚀 PRÓXIMOS PASSOS:")
    print("=" * 60)
    print("")
    print("1. ✅ Cache Python limpo")
    print("2. 🌐 Limpe o cache do navegador (instruções acima)")
    print("3. 🔄 Reinicie o sistema:")
    print("   • Pare o app.py (Ctrl+C)")
    print("   • Execute: python app.py")
    print("4. 🧪 Teste o agendamento com data passada")
    print("")
    print("💡 Se ainda houver erro, execute:")
    print("   python test_api_date.py")
    print("")
    
if __name__ == "__main__":
    main()