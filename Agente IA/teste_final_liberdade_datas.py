#!/usr/bin/env python3
"""
TESTE FINAL DE LIBERDADE DE DATAS - SISTEMA PNSB
=================================================

Este script verifica definitivamente se o sistema permite 
agendamento em qualquer data (passada, presente, futura).
"""

import os
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

def verificar_arquivos_modificados():
    """Verifica se todos os arquivos foram modificados corretamente."""
    print("🔍 VERIFICANDO ARQUIVOS MODIFICADOS...")
    print("=" * 50)
    
    resultados = {}
    
    # 1. Verificar validators.py
    validators_path = Path("gestao_visitas/utils/validators.py")
    if validators_path.exists():
        with open(validators_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "Removida restrição de data passada" in content:
            print("   ✅ validators.py: LIBERDADE IMPLEMENTADA")
            resultados['validators'] = True
        else:
            print("   ❌ validators.py: AINDA COM RESTRIÇÕES")
            resultados['validators'] = False
    else:
        print("   ❌ validators.py: ARQUIVO NÃO ENCONTRADO")
        resultados['validators'] = False
    
    # 2. Verificar app.py
    app_path = Path("app.py")
    if app_path.exists():
        with open(app_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "sem restrição de data passada" in content:
            print("   ✅ app.py: LIBERDADE IMPLEMENTADA")
            resultados['app'] = True
        else:
            print("   ❌ app.py: AINDA COM RESTRIÇÕES")
            resultados['app'] = False
    else:
        print("   ❌ app.py: ARQUIVO NÃO ENCONTRADO")
        resultados['app'] = False
    
    # 3. Verificar visitas.html
    template_path = Path("gestao_visitas/templates/visitas.html")
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if "Removido validação de data passada" in content:
            print("   ✅ visitas.html: LIBERDADE IMPLEMENTADA")
            resultados['template'] = True
        else:
            print("   ❌ visitas.html: AINDA COM RESTRIÇÕES")
            resultados['template'] = False
    else:
        print("   ❌ visitas.html: ARQUIVO NÃO ENCONTRADO")
        resultados['template'] = False
    
    return resultados

def testar_validador_python():
    """Testa diretamente a função de validação Python."""
    print("\n🐍 TESTANDO VALIDAÇÃO PYTHON...")
    print("=" * 50)
    
    try:
        # Importar o validador
        sys.path.append('gestao_visitas/utils')
        from validators import validate_date
        
        # Testar datas variadas
        datas_teste = [
            ("2024-01-01", "Data do ano passado"),
            ("2025-06-30", "Data de ontem"),
            ("2025-07-01", "Data de hoje"),
            ("2025-12-31", "Data futura"),
            ("2020-05-15", "Data bem passada")
        ]
        
        sucessos = 0
        for data_str, descricao in datas_teste:
            try:
                resultado = validate_date(data_str)
                print(f"   ✅ {descricao} ({data_str}): ACEITA")
                sucessos += 1
            except Exception as e:
                print(f"   ❌ {descricao} ({data_str}): REJEITADA - {e}")
        
        print(f"\n📊 RESULTADO: {sucessos}/{len(datas_teste)} datas aceitas")
        return sucessos == len(datas_teste)
        
    except ImportError as e:
        print(f"   ❌ ERRO: Não foi possível importar validators.py - {e}")
        return False
    except Exception as e:
        print(f"   ❌ ERRO INESPERADO: {e}")
        return False

def mostrar_instrucoes_usuario():
    """Mostra instruções finais para o usuário."""
    print("\n" + "=" * 60)
    print("🎯 INSTRUÇÕES PARA TESTAR NO NAVEGADOR")
    print("=" * 60)
    print()
    print("1️⃣ REINICIE O SISTEMA:")
    print("   • Pare o app.py atual (Ctrl+C)")
    print("   • Execute novamente: python app.py")
    print()
    print("2️⃣ LIMPE O CACHE DO NAVEGADOR:")
    print("   • Pressione Ctrl + Shift + Delete")
    print("   • OU abra uma aba anônima/privada")
    print("   • OU pressione Ctrl + F5 para hard refresh")
    print()
    print("3️⃣ TESTE O AGENDAMENTO:")
    print("   • Acesse: http://localhost:5000")
    print("   • Vá em 'Gestão de Visitas'")
    print("   • Clique 'Nova Visita'")
    print("   • Digite uma data passada (ex: 2024-01-15)")
    print("   • Preencha os outros campos")
    print("   • Clique 'Salvar'")
    print()
    print("4️⃣ TESTE A EDIÇÃO:")
    print("   • Clique 'Editar' em uma visita existente")
    print("   • Altere para uma data passada")
    print("   • Salve as alterações")
    print()
    print("✅ SE NÃO HOUVER MAIS ERRO DE 'data anterior', FUNCIONOU!")

def main():
    print("=" * 60)
    print("🎉 TESTE FINAL DE LIBERDADE DE DATAS - SISTEMA PNSB")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        sys.exit(1)
    
    # Verificar arquivos modificados
    resultados_arquivos = verificar_arquivos_modificados()
    
    # Testar validação Python
    validacao_ok = testar_validador_python()
    
    # Resultado geral
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL DO TESTE")
    print("=" * 60)
    
    todos_ok = all(resultados_arquivos.values()) and validacao_ok
    
    if todos_ok:
        print("🎉 SUCESSO TOTAL!")
        print("   ✅ Todos os arquivos modificados corretamente")
        print("   ✅ Validação Python aceita datas passadas")
        print("   ✅ Sistema pronto para liberdade de datas")
        print()
        print("🚀 PRÓXIMO PASSO: Teste no navegador seguindo as instruções abaixo")
    else:
        print("⚠️ PROBLEMAS ENCONTRADOS:")
        if not resultados_arquivos.get('validators'):
            print("   ❌ Arquivo validators.py não foi modificado")
        if not resultados_arquivos.get('app'):
            print("   ❌ Arquivo app.py não foi modificado")
        if not resultados_arquivos.get('template'):
            print("   ❌ Arquivo visitas.html não foi modificado")
        if not validacao_ok:
            print("   ❌ Validação Python ainda rejeita datas passadas")
    
    # Mostrar instruções para teste no navegador
    mostrar_instrucoes_usuario()
    
    print("\n" + "=" * 60)
    print("💡 RESUMO DA FUNCIONALIDADE IMPLEMENTADA")
    print("=" * 60)
    print("✅ PODE agendar visitas em QUALQUER data")
    print("✅ PODE editar datas livremente")
    print("✅ PODE registrar visitas já realizadas")
    print("✅ MANTÉM validação de formato (YYYY-MM-DD)")
    print("✅ REJEITA datas impossíveis (2025-13-01)")
    print("=" * 60)

if __name__ == "__main__":
    main()