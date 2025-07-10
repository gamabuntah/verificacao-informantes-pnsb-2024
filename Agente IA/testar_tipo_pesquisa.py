#!/usr/bin/env python3
"""
TESTE DO DROPDOWN TIPO DE PESQUISA
=================================

Verifica se a correção do dropdown foi aplicada corretamente.
"""

import re
from pathlib import Path

def verificar_correcao_dropdown():
    """Verifica se as correções foram aplicadas no dropdown."""
    print("🔍 VERIFICANDO CORREÇÃO DO DROPDOWN TIPO DE PESQUISA...")
    print("=" * 50)
    
    arquivo_visitas = Path('gestao_visitas/templates/visitas.html')
    
    if not arquivo_visitas.exists():
        print("❌ Arquivo visitas.html não encontrado")
        return False
    
    with open(arquivo_visitas, 'r', encoding='utf-8') as f:
        content = f.read()
    
    resultados = []
    
    # 1. Verificar se há apenas uma opção "ambos" no HTML
    opcoes_html = re.findall(r'<option[^>]*value="[^"]*"[^>]*>.*?</option>', content, re.IGNORECASE)
    opcoes_ambos = [op for op in opcoes_html if 'ambos' in op.lower()]
    
    print("📋 OPÇÕES DO DROPDOWN ENCONTRADAS:")
    for i, opcao in enumerate(opcoes_html, 1):
        if 'MRS' in opcao or 'MAP' in opcao or 'ambos' in opcao.lower():
            print(f"   {i}. {opcao}")
    
    print(f"\n📊 ANÁLISE:")
    print(f"   Total de opções com 'ambos': {len(opcoes_ambos)}")
    
    if len(opcoes_ambos) == 1:
        opcao_correta = 'MRS + MAP' in opcoes_ambos[0]
        print(f"   ✅ Apenas uma opção 'ambos' encontrada")
        print(f"   {'✅' if opcao_correta else '❌'} Contém 'MRS + MAP': {opcao_correta}")
        resultados.append(opcao_correta)
    else:
        print(f"   ❌ Múltiplas opções 'ambos' encontradas (deveria ser apenas 1)")
        resultados.append(False)
    
    # 2. Verificar se o JavaScript não adiciona opção duplicada
    js_adiciona_ambos = 'optAmbos.value = \'AMBOS\'' in content
    print(f"   {'❌' if js_adiciona_ambos else '✅'} JavaScript adiciona 'AMBOS' duplicado: {js_adiciona_ambos}")
    resultados.append(not js_adiciona_ambos)
    
    # 3. Verificar consistência nas validações
    validacoes_ambos = re.findall(r'[\'"]AMBOS[\'"]', content)
    print(f"   Referências a 'AMBOS' (maiúsculo): {len(validacoes_ambos)}")
    
    validacoes_ambos_minus = re.findall(r'[\'"]ambos[\'"]', content)
    print(f"   Referências a 'ambos' (minúsculo): {len(validacoes_ambos_minus)}")
    
    # Deve usar apenas minúsculo
    consistencia_ok = len(validacoes_ambos) == 0
    print(f"   {'✅' if consistencia_ok else '❌'} Consistência de nomenclatura: {consistencia_ok}")
    resultados.append(consistencia_ok)
    
    return all(resultados)

def verificar_backend():
    """Verifica se o backend aceita 'ambos' corretamente."""
    print("\n🔍 VERIFICANDO BACKEND...")
    print("=" * 30)
    
    arquivo_app = Path('app.py')
    
    if not arquivo_app.exists():
        print("❌ Arquivo app.py não encontrado")
        return False
    
    with open(arquivo_app, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar validação no backend
    validacao_backend = "['MRS', 'MAP', 'ambos']" in content
    print(f"   {'✅' if validacao_backend else '❌'} Backend aceita 'ambos': {validacao_backend}")
    
    return validacao_backend

def mostrar_resultado_esperado():
    """Mostra como deve ficar o dropdown."""
    print("\n🎯 RESULTADO ESPERADO NO DROPDOWN:")
    print("=" * 40)
    print("📋 Opções que devem aparecer:")
    print("   1. MRS - Manejo de Resíduos Sólidos")
    print("   2. MAP - Manejo de Águas Pluviais")
    print("   3. MRS + MAP")
    print()
    print("❌ Não deve aparecer:")
    print("   • Ambos (sem descrição)")
    print("   • Opções duplicadas")

def main():
    print("=" * 60)
    print("🔧 TESTE DO DROPDOWN TIPO DE PESQUISA")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        return
    
    # Verificar correções
    frontend_ok = verificar_correcao_dropdown()
    backend_ok = verificar_backend()
    
    # Mostrar resultado
    mostrar_resultado_esperado()
    
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    if frontend_ok and backend_ok:
        print("🎉 CORREÇÃO APLICADA COM SUCESSO!")
        print("   ✅ Frontend corrigido")
        print("   ✅ Backend compatível")
        print()
        print("🚀 PRÓXIMOS PASSOS:")
        print("   1. Reinicie o sistema (Ctrl+C e python app.py)")
        print("   2. Limpe o cache do navegador (Ctrl+F5)")
        print("   3. Acesse: http://localhost:8080/visitas")
        print("   4. Verifique o dropdown 'Tipo de Pesquisa'")
        print()
        print("✅ Agora deve aparecer apenas:")
        print("   • MRS - Manejo de Resíduos Sólidos")
        print("   • MAP - Manejo de Águas Pluviais")  
        print("   • MRS + MAP")
    else:
        print("⚠️ CORREÇÃO INCOMPLETA:")
        if not frontend_ok:
            print("   ❌ Frontend ainda tem problemas")
        if not backend_ok:
            print("   ❌ Backend não aceita 'ambos'")
    
    print("=" * 60)

if __name__ == "__main__":
    main()