#!/usr/bin/env python3
"""
Validação estrutural dos serviços avançados implementados no sistema PNSB.

Este script valida a estrutura e implementação dos 16 serviços avançados
sem depender do contexto da aplicação Flask.
"""

import os
import sys
import ast
import inspect
from pathlib import Path
from typing import Dict, List, Set

def validate_service_file_structure():
    """Valida se todos os arquivos de serviços existem e têm estrutura adequada."""
    print("🔍 Validando estrutura dos arquivos de serviços...")
    
    services_dir = Path(__file__).parent / "gestao_visitas" / "services"
    
    expected_services = [
        "rastreamento_questionarios.py",
        "dashboard_produtividade.py", 
        "sistema_backup_contingencia.py",
        "prestadores.py",
        "notificacoes_alertas.py",
        "analise_resistencia.py",
        "assistente_abordagem.py",
        "comunicacao_eficiente.py",
        "logistica_maps.py",
        "perfil_informante.py",
        "dashboard_avancado.py",
        "agendamento_avancado.py",
        "checklist_inteligente.py",
        "contatos_inteligente.py",
        "relatorios_avancados.py",
        "whatsapp_business.py"
    ]
    
    results = {}
    
    for service_file in expected_services:
        service_path = services_dir / service_file
        service_name = service_file.replace('.py', '')
        
        if service_path.exists():
            try:
                with open(service_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Parse AST para análise estrutural
                tree = ast.parse(content)
                
                # Analisar classes e métodos
                classes = []
                functions = []
                imports = []
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                        classes.append({
                            'name': node.name,
                            'methods': methods,
                            'method_count': len(methods)
                        })
                    elif isinstance(node, ast.FunctionDef) and not any(node.lineno > cls.lineno for cls in ast.walk(tree) if isinstance(cls, ast.ClassDef)):
                        functions.append(node.name)
                    elif isinstance(node, ast.Import):
                        imports.extend([alias.name for alias in node.names])
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        imports.extend([f"{module}.{alias.name}" for alias in node.names])
                
                results[service_name] = {
                    'exists': True,
                    'size_kb': round(len(content) / 1024, 2),
                    'lines': len(content.split('\n')),
                    'classes': classes,
                    'functions': functions,
                    'imports': imports[:10],  # Primeiros 10 imports
                    'has_main_class': len(classes) > 0,
                    'comprehensive': len(content) > 5000  # Considera abrangente se > 5KB
                }
                
                print(f"✅ {service_name}: {results[service_name]['size_kb']}KB, {len(classes)} classe(s)")
                
            except Exception as e:
                results[service_name] = {
                    'exists': True,
                    'error': str(e),
                    'valid': False
                }
                print(f"❌ {service_name}: Erro ao analisar - {e}")
        else:
            results[service_name] = {
                'exists': False
            }
            print(f"❌ {service_name}: Arquivo não encontrado")
    
    return results

def validate_class_names_and_methods():
    """Valida se as classes têm nomes adequados e métodos principais."""
    print("\n🔧 Validando classes e métodos principais...")
    
    services_dir = Path(__file__).parent / "gestao_visitas" / "services"
    
    expected_classes_and_methods = {
        "rastreamento_questionarios.py": {
            "expected_classes": ["RastreamentoQuestionarios"],
            "key_methods": ["obter_dashboard_completo", "otimizar_cronograma"]
        },
        "dashboard_produtividade.py": {
            "expected_classes": ["DashboardProdutividade"],
            "key_methods": ["obter_dashboard_pesquisador", "calcular_gamificacao"]
        },
        "sistema_backup_contingencia.py": {
            "expected_classes": ["SistemaBackupContingencia"],
            "key_methods": ["criar_backup_completo", "listar_backups"]
        },
        "prestadores.py": {
            "expected_classes": ["GestaoAvancadaPrestadores", "Prestador"],
            "key_methods": ["validar_prestador", "gerar_dashboard"]
        },
        "notificacoes_alertas.py": {
            "expected_classes": ["SistemaNotificacoes"],
            "key_methods": ["enviar_notificacao", "verificar_alertas"]
        },
        "analise_resistencia.py": {
            "expected_classes": ["AnaliseResistencia"],
            "key_methods": ["analisar_resistencia", "sugerir_estrategia"]
        },
        "dashboard_avancado.py": {
            "expected_classes": ["DashboardAvancado"],
            "key_methods": ["obter_dashboard_principal", "_gerar_dashboard_completo"]
        },
        "agendamento_avancado.py": {
            "expected_classes": ["AgendamentoAvancado"],
            "key_methods": ["sugerir_horarios", "detectar_conflitos"]
        },
        "checklist_inteligente.py": {
            "expected_classes": ["ChecklistInteligente"],
            "key_methods": ["gerar_checklist_personalizado", "validar_completude"]
        },
        "contatos_inteligente.py": {
            "expected_classes": ["ContatosInteligente"],
            "key_methods": ["enriquecer_contato_automatico", "validar_qualidade"]
        },
        "relatorios_avancados.py": {
            "expected_classes": ["RelatoriosAvancados"],
            "key_methods": ["gerar_relatorio_executivo", "gerar_dashboard_metricas"]
        }
    }
    
    validation_results = {}
    
    for service_file, expectations in expected_classes_and_methods.items():
        service_path = services_dir / service_file
        service_name = service_file.replace('.py', '')
        
        if not service_path.exists():
            validation_results[service_name] = {"exists": False}
            continue
            
        try:
            with open(service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            found_classes = []
            all_methods = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    found_classes.append(node.name)
                    methods = [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                    all_methods.extend(methods)
            
            # Verificar classes esperadas
            expected_classes = expectations["expected_classes"]
            classes_found = [cls for cls in expected_classes if cls in found_classes]
            
            # Verificar métodos-chave
            key_methods = expectations["key_methods"]
            methods_found = []
            for method in key_methods:
                # Busca por nome parcial (flexível)
                partial_matches = [m for m in all_methods if method.replace("_", "").lower() in m.replace("_", "").lower()]
                if partial_matches:
                    methods_found.extend(partial_matches)
            
            validation_results[service_name] = {
                "exists": True,
                "expected_classes": expected_classes,
                "found_classes": found_classes,
                "classes_match": len(classes_found) > 0,
                "expected_methods": key_methods,
                "found_methods": list(set(methods_found)),
                "methods_coverage": len(methods_found) / len(key_methods) if key_methods else 0,
                "all_methods_count": len(all_methods),
                "comprehensive": len(all_methods) >= 10
            }
            
            coverage = validation_results[service_name]["methods_coverage"]
            print(f"✅ {service_name}: {len(classes_found)}/{len(expected_classes)} classes, {coverage:.1%} métodos")
            
        except Exception as e:
            validation_results[service_name] = {
                "exists": True,
                "error": str(e)
            }
            print(f"❌ {service_name}: Erro - {e}")
    
    return validation_results

def validate_import_dependencies():
    """Valida dependências e imports dos serviços."""
    print("\n📦 Validando dependências e imports...")
    
    services_dir = Path(__file__).parent / "gestao_visitas" / "services"
    common_dependencies = []
    flask_dependencies = []
    external_dependencies = []
    
    for service_file in services_dir.glob("*.py"):
        if service_file.name.startswith("__"):
            continue
            
        try:
            with open(service_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith('flask'):
                            flask_dependencies.append(alias.name)
                        elif alias.name in ['datetime', 'typing', 'json', 'os', 'sys']:
                            common_dependencies.append(alias.name)
                        else:
                            external_dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if module.startswith('flask'):
                        flask_dependencies.append(module)
                    elif module.startswith('..'):
                        common_dependencies.append(module)
                    else:
                        external_dependencies.append(module)
        
        except Exception as e:
            print(f"❌ Erro ao analisar {service_file.name}: {e}")
    
    # Contar frequências
    common_freq = {}
    for dep in common_dependencies:
        common_freq[dep] = common_freq.get(dep, 0) + 1
    
    flask_freq = {}
    for dep in flask_dependencies:
        flask_freq[dep] = flask_freq.get(dep, 0) + 1
    
    print(f"✅ Dependências comuns mais usadas: {list(common_freq.keys())[:5]}")
    print(f"✅ Dependências Flask encontradas: {len(set(flask_dependencies))}")
    print(f"✅ Dependências externas: {len(set(external_dependencies))}")
    
    return {
        "common_dependencies": common_freq,
        "flask_dependencies": flask_freq,
        "external_dependencies": list(set(external_dependencies))
    }

def validate_whatsapp_routes():
    """Valida especificamente as rotas do WhatsApp."""
    print("\n📱 Validando rotas WhatsApp...")
    
    whatsapp_file = Path(__file__).parent / "gestao_visitas" / "routes" / "whatsapp_api.py"
    
    if not whatsapp_file.exists():
        print("❌ Arquivo whatsapp_api.py não encontrado")
        return {"exists": False}
    
    try:
        with open(whatsapp_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Buscar rotas Flask
        routes_found = []
        webhook_handlers = []
        
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('@') and 'route(' in line:
                routes_found.append(line)
            elif 'def ' in line and ('webhook' in line.lower() or 'send' in line.lower()):
                webhook_handlers.append(line)
        
        expected_routes = ['webhook', 'send_message', 'send_template', 'send_bulk']
        routes_coverage = 0
        
        for expected in expected_routes:
            if any(expected in route for route in routes_found):
                routes_coverage += 1
        
        result = {
            "exists": True,
            "routes_found": len(routes_found),
            "handlers_found": len(webhook_handlers),
            "expected_routes": expected_routes,
            "routes_coverage": routes_coverage / len(expected_routes),
            "has_webhook": any('webhook' in route for route in routes_found),
            "comprehensive": len(content) > 2000
        }
        
        print(f"✅ WhatsApp API: {routes_coverage}/{len(expected_routes)} rotas, {len(webhook_handlers)} handlers")
        return result
        
    except Exception as e:
        print(f"❌ Erro ao validar WhatsApp: {e}")
        return {"exists": True, "error": str(e)}

def generate_comprehensive_report():
    """Gera relatório abrangente da validação."""
    print("\n" + "="*60)
    print("📊 RELATÓRIO ABRANGENTE DE VALIDAÇÃO DOS SERVIÇOS")
    print("="*60)
    
    # Executar todas as validações
    structure_results = validate_service_file_structure()
    class_results = validate_class_names_and_methods()
    dependencies_results = validate_import_dependencies()
    whatsapp_results = validate_whatsapp_routes()
    
    # Calcular estatísticas gerais
    total_services = len(structure_results)
    services_exist = sum(1 for result in structure_results.values() if result.get('exists', False))
    services_comprehensive = sum(1 for result in structure_results.values() if result.get('comprehensive', False))
    
    classes_with_methods = sum(1 for result in class_results.values() if result.get('methods_coverage', 0) > 0.5)
    
    print(f"\n📈 ESTATÍSTICAS GERAIS:")
    print(f"   • Total de serviços: {total_services}")
    print(f"   • Serviços existentes: {services_exist}/{total_services} ({services_exist/total_services*100:.1f}%)")
    print(f"   • Serviços abrangentes: {services_comprehensive}/{total_services} ({services_comprehensive/total_services*100:.1f}%)")
    print(f"   • Classes bem implementadas: {classes_with_methods}/{len(class_results)} ({classes_with_methods/max(len(class_results),1)*100:.1f}%)")
    
    print(f"\n🏗️ ANÁLISE DE ESTRUTURA:")
    total_lines = sum(result.get('lines', 0) for result in structure_results.values())
    total_size = sum(result.get('size_kb', 0) for result in structure_results.values())
    print(f"   • Total de linhas de código: {total_lines:,}")
    print(f"   • Tamanho total: {total_size:.1f} KB")
    print(f"   • Média de linhas por serviço: {total_lines/max(services_exist,1):.0f}")
    
    print(f"\n🔧 IMPLEMENTAÇÃO:")
    total_classes = sum(len(result.get('classes', [])) for result in structure_results.values())
    print(f"   • Total de classes implementadas: {total_classes}")
    print(f"   • Média de classes por serviço: {total_classes/max(services_exist,1):.1f}")
    
    if whatsapp_results.get('exists'):
        print(f"\n📱 WHATSAPP API:")
        print(f"   • Rotas implementadas: {whatsapp_results.get('routes_coverage', 0)*100:.0f}%")
        print(f"   • Webhook configurado: {'✅' if whatsapp_results.get('has_webhook') else '❌'}")
    
    # Score geral de qualidade
    quality_score = (
        (services_exist / total_services) * 0.3 +
        (services_comprehensive / total_services) * 0.3 +
        (classes_with_methods / max(len(class_results), 1)) * 0.3 +
        (whatsapp_results.get('routes_coverage', 0)) * 0.1
    ) * 100
    
    print(f"\n🏆 SCORE DE QUALIDADE GERAL: {quality_score:.1f}/100")
    
    if quality_score >= 90:
        print("🎉 EXCELENTE! Sistema muito bem implementado.")
    elif quality_score >= 75:
        print("✅ MUITO BOM! Sistema bem implementado.")
    elif quality_score >= 60:
        print("👍 BOM! Sistema adequadamente implementado.")
    elif quality_score >= 40:
        print("⚠️ REGULAR! Necessita algumas melhorias.")
    else:
        print("❌ NECESSITA MELHORIAS! Revisar implementações.")
    
    print("\n🎯 SERVIÇOS MAIS ROBUSTOS:")
    robust_services = []
    for name, result in structure_results.items():
        if result.get('comprehensive') and result.get('lines', 0) > 200:
            robust_services.append((name, result.get('lines', 0)))
    
    robust_services.sort(key=lambda x: x[1], reverse=True)
    for name, lines in robust_services[:5]:
        print(f"   • {name}: {lines} linhas")
    
    print("\n" + "="*60)
    print("✅ VALIDAÇÃO ESTRUTURAL CONCLUÍDA")
    print("="*60)
    
    return {
        'quality_score': quality_score,
        'services_exist': services_exist,
        'total_services': total_services,
        'comprehensive_services': services_comprehensive
    }

if __name__ == "__main__":
    try:
        report = generate_comprehensive_report()
        
        # Exit code baseado na qualidade
        if report['quality_score'] >= 75:
            sys.exit(0)  # Sucesso
        elif report['quality_score'] >= 50:
            sys.exit(1)  # Parcial
        else:
            sys.exit(2)  # Necessita melhorias
            
    except Exception as e:
        print(f"❌ Erro durante validação: {e}")
        sys.exit(3)  # Erro crítico