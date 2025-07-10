#!/usr/bin/env python3
"""
Teste para verificar se a validação de data foi removida corretamente.
"""

import sys
from pathlib import Path

# Adicionar o projeto ao path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

from datetime import datetime, date, timedelta
from gestao_visitas.utils.validators import InputValidator, ValidationError

def test_date_validation():
    """Testa se agora é possível usar datas passadas."""
    
    print("🔍 Testando validação de datas...")
    
    # Data de hoje
    hoje = date.today()
    
    # Data de ontem (deveria funcionar agora)
    ontem = hoje - timedelta(days=1)
    
    # Data do ano passado (deveria funcionar)
    ano_passado = hoje - timedelta(days=365)
    
    # Data futura (sempre funcionou)
    futuro = hoje + timedelta(days=30)
    
    testes = [
        ("Data de hoje", hoje.strftime('%Y-%m-%d')),
        ("Data de ontem", ontem.strftime('%Y-%m-%d')),
        ("Data do ano passado", ano_passado.strftime('%Y-%m-%d')),
        ("Data futura", futuro.strftime('%Y-%m-%d')),
    ]
    
    resultados = []
    
    for nome, data_str in testes:
        try:
            resultado = InputValidator.validate_date(data_str)
            print(f"✅ {nome} ({data_str}): ACEITA")
            resultados.append(True)
        except ValidationError as e:
            print(f"❌ {nome} ({data_str}): REJEITADA - {e}")
            resultados.append(False)
        except Exception as e:
            print(f"💥 {nome} ({data_str}): ERRO - {e}")
            resultados.append(False)
    
    print(f"\n📊 Resultado: {sum(resultados)}/{len(resultados)} testes passaram")
    
    if all(resultados):
        print("🎉 SUCESSO! Todas as datas são aceitas agora.")
        print("   Você pode agendar visitas em qualquer data!")
        return True
    else:
        print("⚠️ Alguns testes falharam. Verificar implementação.")
        return False

def test_invalid_date_format():
    """Testa se formatos inválidos ainda são rejeitados."""
    
    print("\n🔍 Testando formatos inválidos (devem ser rejeitados)...")
    
    formatos_invalidos = [
        "2025-13-01",  # Mês inválido
        "2025-01-32",  # Dia inválido
        "01/01/2025",  # Formato errado
        "2025/01/01",  # Formato errado
        "invalid",     # Texto inválido
        "",            # Vazio
    ]
    
    rejeitados = 0
    
    for formato in formatos_invalidos:
        try:
            InputValidator.validate_date(formato)
            print(f"❌ {formato}: ACEITO (deveria ser rejeitado)")
        except ValidationError:
            print(f"✅ {formato}: REJEITADO (correto)")
            rejeitados += 1
        except Exception as e:
            print(f"✅ {formato}: REJEITADO - {e}")
            rejeitados += 1
    
    print(f"\n📊 {rejeitados}/{len(formatos_invalidos)} formatos inválidos rejeitados corretamente")
    
    return rejeitados == len(formatos_invalidos)

if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTE DE VALIDAÇÃO DE DATAS - PNSB")
    print("=" * 60)
    
    test1 = test_date_validation()
    test2 = test_invalid_date_format()
    
    print("\n" + "=" * 60)
    print("📋 RESUMO DOS TESTES")
    print("=" * 60)
    
    if test1 and test2:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("   ✅ Datas passadas são aceitas")
        print("   ✅ Formatos inválidos são rejeitados")
        print("   ✅ Sistema pronto para registro histórico")
        sys.exit(0)
    else:
        print("⚠️ ALGUNS TESTES FALHARAM")
        if not test1:
            print("   ❌ Problema com aceitação de datas passadas")
        if not test2:
            print("   ❌ Problema com rejeição de formatos inválidos")
        sys.exit(1)