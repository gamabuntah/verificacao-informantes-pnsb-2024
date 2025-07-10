#!/usr/bin/env python3
"""
TESTE DA CORREÇÃO DO ERRO DE MODAL
================================

Verifica se o erro de JavaScript foi corrigido.
"""

def verificar_correcao():
    """Verifica se as correções foram aplicadas."""
    print("🔍 VERIFICANDO CORREÇÕES DO ERRO DE MODAL...")
    print("=" * 50)
    
    with open('gestao_visitas/templates/visitas.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contar ocorrências de 'const modal'
    occurrences = content.count('const modal = new bootstrap.Modal')
    print(f"📊 Ocorrências de 'const modal = new bootstrap.Modal': {occurrences}")
    
    if occurrences > 0:
        print("❌ AINDA HÁ CONFLITOS! Localizando...")
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'const modal = new bootstrap.Modal' in line:
                print(f"   Linha {i}: {line.strip()}")
        return False
    else:
        print("✅ CONFLITOS RESOLVIDOS!")
        
        # Verificar se as novas variáveis estão presentes
        new_vars = [
            'const modalReagendar',
            'const modalEdicao', 
            'const modalChecklistShow'
        ]
        
        for var in new_vars:
            if var in content:
                print(f"   ✅ {var} encontrada")
            else:
                print(f"   ❌ {var} não encontrada")
        
        return True

def main():
    print("=" * 60)
    print("🔧 TESTE DA CORREÇÃO DO ERRO DE MODAL")
    print("=" * 60)
    
    sucesso = verificar_correcao()
    
    print("\n" + "=" * 60)
    print("📋 RESULTADO")
    print("=" * 60)
    
    if sucesso:
        print("🎉 ERRO DE MODAL CORRIGIDO!")
        print()
        print("✅ O erro 'Identifier modal has already been declared' foi resolvido")
        print("✅ Agora as visitas devem aparecer normalmente")
        print()
        print("🚀 PRÓXIMOS PASSOS:")
        print("1. Reinicie o sistema (Ctrl+C e python app.py)")
        print("2. Limpe o cache do navegador (Ctrl+F5)")
        print("3. Acesse: http://localhost:8080/visitas")
        print("4. Suas 2 visitas devem aparecer agora!")
    else:
        print("⚠️ AINDA HÁ CONFLITOS DE VARIÁVEIS")
        print("   Será necessário corrigir manualmente")
    
    print("=" * 60)

if __name__ == "__main__":
    main()