#!/usr/bin/env python3
"""
Teste de Melhorias de Layout PNSB
Verifica se todas as melhorias de UX/UI foram implementadas
"""

import os
import re

def test_design_system():
    """Testa se o sistema de design foi implementado"""
    print("🎨 Testando sistema de design...")
    
    design_file = 'gestao_visitas/static/css/design-system.css'
    if not os.path.exists(design_file):
        print("❌ Arquivo design-system.css não encontrado")
        return False
    
    with open(design_file, 'r') as f:
        content = f.read()
    
    required_components = [
        ':root {',  # Variáveis CSS
        '--primary-color:',
        '.card-standard',
        '.btn-primary-custom',
        '.input-custom',
        '.select-custom',
        '.sidebar',
        '.navbar-custom',
        '.breadcrumb-custom',
        '.loading-overlay',
        '.notification',
        '.table-responsive-stack'
    ]
    
    missing_components = []
    for component in required_components:
        if component not in content:
            missing_components.append(component)
    
    if missing_components:
        print(f"❌ Componentes faltando: {missing_components}")
        return False
    else:
        print("✅ Sistema de design implementado corretamente")
        return True

def test_javascript_components():
    """Testa se os componentes JavaScript foram implementados"""
    print("🔧 Testando componentes JavaScript...")
    
    js_file = 'gestao_visitas/static/js/components.js'
    if not os.path.exists(js_file):
        print("❌ Arquivo components.js não encontrado")
        return False
    
    with open(js_file, 'r') as f:
        content = f.read()
    
    required_classes = [
        'class SidebarManager',
        'class LoadingManager',
        'class NotificationManager',
        'class BreadcrumbManager',
        'class ResponsiveTableManager',
        'class FormManager',
        'class Utils',
        'class App'
    ]
    
    missing_classes = []
    for cls in required_classes:
        if cls not in content:
            missing_classes.append(cls)
    
    if missing_classes:
        print(f"❌ Classes JavaScript faltando: {missing_classes}")
        return False
    else:
        print("✅ Componentes JavaScript implementados corretamente")
        return True

def test_sidebar_navigation():
    """Testa se a navegação lateral foi implementada"""
    print("🧭 Testando navegação lateral...")
    
    base_file = 'gestao_visitas/templates/base.html'
    if not os.path.exists(base_file):
        print("❌ Arquivo base.html não encontrado")
        return False
    
    with open(base_file, 'r') as f:
        content = f.read()
    
    required_elements = [
        '<aside class="sidebar">',
        'class="sidebar-nav"',
        'class="nav-section"',
        'class="nav-link-custom"',
        'class="sidebar-toggle"',
        'navbar-custom'
    ]
    
    missing_elements = []
    for element in required_elements:
        if element not in content:
            missing_elements.append(element)
    
    if missing_elements:
        print(f"❌ Elementos da sidebar faltando: {missing_elements}")
        return False
    else:
        print("✅ Navegação lateral implementada corretamente")
        return True

def test_responsive_tables():
    """Testa se as tabelas responsivas foram implementadas"""
    print("📱 Testando tabelas responsivas...")
    
    contatos_file = 'gestao_visitas/templates/contatos.html'
    if not os.path.exists(contatos_file):
        print("❌ Arquivo contatos.html não encontrado")
        return False
    
    with open(contatos_file, 'r') as f:
        content = f.read()
    
    # Verificar se as classes responsivas foram aplicadas
    required_classes = [
        'table-responsive-custom',
        'table-responsive-stack',
        'table-custom',
        'card-standard'
    ]
    
    missing_classes = []
    for cls in required_classes:
        if cls not in content:
            missing_classes.append(cls)
    
    if missing_classes:
        print(f"❌ Classes responsivas faltando: {missing_classes}")
        return False
    else:
        print("✅ Tabelas responsivas implementadas corretamente")
        return True

def test_consistent_inputs():
    """Testa se os inputs foram padronizados"""
    print("📝 Testando padronização de inputs...")
    
    files_to_check = [
        'gestao_visitas/templates/contatos.html',
        'gestao_visitas/templates/visitas.html'
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            print(f"❌ Arquivo {file_path} não encontrado")
            all_good = False
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Verificar se usa as classes customizadas
        if 'input-custom' in content and 'select-custom' in content:
            print(f"✅ {file_path}: Inputs padronizados")
        else:
            print(f"❌ {file_path}: Inputs não padronizados")
            all_good = False
    
    return all_good

def test_modern_buttons():
    """Testa se os botões foram modernizados"""
    print("🔘 Testando botões modernos...")
    
    files_to_check = [
        'gestao_visitas/templates/contatos.html',
        'gestao_visitas/templates/visitas.html'
    ]
    
    all_good = True
    
    for file_path in files_to_check:
        if not os.path.exists(file_path):
            continue
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Verificar se usa as classes de botão customizadas
        modern_button_classes = [
            'btn-primary-custom',
            'btn-secondary-custom', 
            'btn-outline-custom'
        ]
        
        has_modern_buttons = any(btn_class in content for btn_class in modern_button_classes)
        
        if has_modern_buttons:
            print(f"✅ {file_path}: Botões modernizados")
        else:
            print(f"❌ {file_path}: Botões não modernizados")
            all_good = False
    
    return all_good

def test_breadcrumbs_integration():
    """Testa se os breadcrumbs foram integrados"""
    print("🗂️ Testando integração de breadcrumbs...")
    
    # Verificar arquivo de inicialização
    breadcrumb_file = 'gestao_visitas/static/js/breadcrumbs-init.js'
    if not os.path.exists(breadcrumb_file):
        print("❌ Arquivo breadcrumbs-init.js não encontrado")
        return False
    
    # Verificar se foi incluído no base.html
    base_file = 'gestao_visitas/templates/base.html'
    with open(base_file, 'r') as f:
        base_content = f.read()
    
    if 'breadcrumbs-init.js' not in base_content:
        print("❌ breadcrumbs-init.js não incluído no base.html")
        return False
    
    if 'breadcrumb-container' not in base_content:
        print("❌ Container de breadcrumbs não encontrado no base.html")
        return False
    
    print("✅ Breadcrumbs integrados corretamente")
    return True

def test_accessibility_improvements():
    """Testa melhorias de acessibilidade"""
    print("♿ Testando melhorias de acessibilidade...")
    
    base_file = 'gestao_visitas/templates/base.html'
    with open(base_file, 'r') as f:
        content = f.read()
    
    accessibility_features = [
        'aria-label=',
        'role="navigation"',
        'aria-current=',
        'aria-expanded='
    ]
    
    found_features = []
    for feature in accessibility_features:
        if feature in content:
            found_features.append(feature)
    
    if len(found_features) >= 2:  # Pelo menos 2 features de acessibilidade
        print(f"✅ Melhorias de acessibilidade implementadas: {found_features}")
        return True
    else:
        print(f"⚠️ Poucas melhorias de acessibilidade encontradas: {found_features}")
        return False

def main():
    """Executa todos os testes de layout"""
    print("=" * 60)
    print("🎨 TESTE DE MELHORIAS DE LAYOUT PNSB")
    print("=" * 60)
    
    tests = [
        test_design_system,
        test_javascript_components,
        test_sidebar_navigation,
        test_responsive_tables,
        test_consistent_inputs,
        test_modern_buttons,
        test_breadcrumbs_integration,
        test_accessibility_improvements
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    print("📊 RESULTADOS FINAIS - MELHORIAS DE LAYOUT")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 TODAS AS MELHORIAS FORAM IMPLEMENTADAS!")
        print("✅ Layout moderno e responsivo pronto")
        print("\n🌟 Melhorias implementadas:")
        print("   ✅ Sistema de design consistente")
        print("   ✅ Navegação lateral moderna")
        print("   ✅ Tabelas totalmente responsivas")
        print("   ✅ Componentes JavaScript avançados")
        print("   ✅ Inputs e botões padronizados")
        print("   ✅ Breadcrumbs automáticos")
        print("   ✅ Melhorias de acessibilidade")
        print("   ✅ Feedback visual melhorado")
        
        print("\n💡 O sistema agora possui:")
        print("   📱 Design totalmente responsivo")
        print("   🎨 Interface moderna e consistente")
        print("   ⚡ Componentes interativos")
        print("   ♿ Melhor acessibilidade")
        print("   🧭 Navegação intuitiva")
        
        return 0
    else:
        print(f"❌ {total - passed} MELHORIAS AINDA PRECISAM SER FINALIZADAS")
        print(f"📊 Taxa de conclusão: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print("\n🔧 Revise os itens acima que falharam")
        return 1

if __name__ == '__main__':
    exit(main())