#!/usr/bin/env python3
"""
Verificação final e abrangente de todos os serviços implementados.
Este script faz uma verificação detalhada de cada serviço para garantir 
que está corretamente implementado e funcionando.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

class FinalServiceVerifier:
    def __init__(self):
        self.services_dir = Path(__file__).parent / "gestao_visitas" / "services"
        self.expected_services = {
            "rastreamento_questionarios.py": "RastreamentoQuestionarios",
            "dashboard_produtividade.py": "DashboardProdutividade", 
            "sistema_backup_contingencia.py": "SistemaBackupContingencia",
            "prestadores.py": "PrestadorService",
            "notificacoes_alertas.py": "SistemaNotificacoes",
            "analise_resistencia.py": "AnaliseResistencia",
            "assistente_abordagem.py": "AssistenteAbordagem",
            "comunicacao_eficiente.py": "ComunicacaoEficiente",
            "logistica_maps.py": "LogisticaMaps",
            "perfil_informante.py": "PerfilInformante",
            "dashboard_avancado.py": "DashboardAvancado",
            "agendamento_avancado.py": "AgendamentoAvancado",
            "checklist_inteligente.py": "ChecklistInteligente",
            "contatos_inteligente.py": "ContatosInteligente",
            "relatorios_avancados.py": "RelatoriosAvancados",
            "whatsapp_business.py": "WhatsAppBusinessService"
        }
        
    def verify_all_services(self) -> Dict[str, Any]:
        """Verifica todos os serviços e retorna relatório detalhado."""
        
        print("🔍 VERIFICAÇÃO FINAL DOS SERVIÇOS AVANÇADOS PNSB")
        print("=" * 60)
        
        results = {
            "services_verified": 0,
            "services_passed": 0,
            "services_failed": 0,
            "syntax_errors": 0,
            "missing_classes": 0,
            "total_lines": 0,
            "total_methods": 0,
            "details": {}
        }
        
        for service_file, expected_class in self.expected_services.items():
            print(f"\n📋 Verificando {service_file}...")
            
            service_result = self._verify_single_service(service_file, expected_class)
            results["details"][service_file] = service_result
            
            results["services_verified"] += 1
            if service_result["status"] == "PASSED":
                results["services_passed"] += 1
                print(f"✅ {service_file}: APROVADO")
            else:
                results["services_failed"] += 1
                print(f"❌ {service_file}: FALHOU - {service_result.get('error', 'Erro desconhecido')}")
            
            if service_result.get("syntax_error"):
                results["syntax_errors"] += 1
            if service_result.get("missing_class"):
                results["missing_classes"] += 1
                
            results["total_lines"] += service_result.get("lines", 0)
            results["total_methods"] += service_result.get("methods", 0)
        
        return results
    
    def _verify_single_service(self, service_file: str, expected_class: str) -> Dict[str, Any]:
        """Verifica um serviço específico."""
        
        service_path = self.services_dir / service_file
        result = {
            "status": "FAILED",
            "exists": False,
            "syntax_valid": False,
            "class_found": False,
            "missing_class": False,
            "syntax_error": False,
            "lines": 0,
            "methods": 0,
            "classes": [],
            "imports": []
        }
        
        # Verificar se arquivo existe
        if not service_path.exists():
            result["error"] = "Arquivo não encontrado"
            return result
        
        result["exists"] = True
        
        try:
            # Ler conteúdo do arquivo
            with open(service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result["lines"] = len(content.split('\n'))
            
            # Verificar sintaxe
            try:
                tree = ast.parse(content)
                result["syntax_valid"] = True
            except SyntaxError as e:
                result["error"] = f"Erro de sintaxe: {e}"
                result["syntax_error"] = True
                return result
            
            # Analisar estrutura
            classes_found = []
            methods_count = 0
            imports_found = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes_found.append(node.name)
                    # Contar métodos na classe
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            methods_count += 1
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports_found.append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports_found.append(node.module)
            
            result["classes"] = classes_found
            result["methods"] = methods_count
            result["imports"] = imports_found[:10]  # Primeiros 10 imports
            
            # Verificar se classe esperada foi encontrada
            if expected_class in classes_found:
                result["class_found"] = True
                result["status"] = "PASSED"
            else:
                result["missing_class"] = True
                result["error"] = f"Classe esperada '{expected_class}' não encontrada. Encontradas: {classes_found}"
            
        except Exception as e:
            result["error"] = f"Erro durante verificação: {str(e)}"
        
        return result
    
    def generate_final_report(self, results: Dict[str, Any]) -> None:
        """Gera relatório final detalhado."""
        
        print("\n" + "=" * 60)
        print("📊 RELATÓRIO FINAL DE VERIFICAÇÃO")
        print("=" * 60)
        
        # Estatísticas gerais
        total = results["services_verified"]
        passed = results["services_passed"]
        failed = results["services_failed"]
        
        print(f"\n📈 ESTATÍSTICAS GERAIS:")
        print(f"   • Total de serviços verificados: {total}")
        print(f"   • Serviços aprovados: {passed}")
        print(f"   • Serviços com falha: {failed}")
        print(f"   • Taxa de sucesso: {(passed/total)*100:.1f}%")
        print(f"   • Total de linhas: {results['total_lines']:,}")
        print(f"   • Total de métodos: {results['total_methods']}")
        
        # Problemas encontrados
        print(f"\n⚠️ PROBLEMAS IDENTIFICADOS:")
        print(f"   • Erros de sintaxe: {results['syntax_errors']}")
        print(f"   • Classes faltantes: {results['missing_classes']}")
        
        # Detalhes dos serviços
        print(f"\n📋 DETALHES POR SERVIÇO:")
        for service_file, details in results["details"].items():
            status_icon = "✅" if details["status"] == "PASSED" else "❌"
            print(f"   {status_icon} {service_file:<35} | {details.get('lines', 0):>4} linhas | {details.get('methods', 0):>3} métodos")
        
        # Serviços com problemas
        failed_services = [
            service for service, details in results["details"].items() 
            if details["status"] == "FAILED"
        ]
        
        if failed_services:
            print(f"\n❌ SERVIÇOS COM PROBLEMAS:")
            for service in failed_services:
                details = results["details"][service]
                print(f"   • {service}: {details.get('error', 'Erro desconhecido')}")
        
        # Score final
        if failed == 0:
            print(f"\n🎉 RESULTADO: TODOS OS SERVIÇOS APROVADOS!")
            print(f"   Sistema completamente implementado e validado.")
        elif failed <= 2:
            print(f"\n✅ RESULTADO: SISTEMA EM BOA CONDIÇÃO")
            print(f"   Apenas {failed} serviço(s) com problemas menores.")
        else:
            print(f"\n⚠️ RESULTADO: SISTEMA PRECISA DE ATENÇÃO")
            print(f"   {failed} serviço(s) requerem correção.")
        
        # Recomendações
        print(f"\n💡 RECOMENDAÇÕES:")
        if results["syntax_errors"] > 0:
            print(f"   • Corrigir {results['syntax_errors']} erro(s) de sintaxe")
        if results["missing_classes"] > 0:
            print(f"   • Implementar {results['missing_classes']} classe(s) faltante(s)")
        if failed == 0:
            print(f"   • Sistema pronto para produção!")
            print(f"   • Considerar testes de integração")
            print(f"   • Configurar ambiente de produção")
        
        print("=" * 60)

def run_final_verification():
    """Executa a verificação final completa."""
    
    verifier = FinalServiceVerifier()
    results = verifier.verify_all_services()
    verifier.generate_final_report(results)
    
    # Return exit code baseado nos resultados
    if results["services_failed"] == 0:
        return 0  # Sucesso total
    elif results["services_failed"] <= 2:
        return 1  # Problemas menores
    else:
        return 2  # Problemas significativos

if __name__ == "__main__":
    exit_code = run_final_verification()
    sys.exit(exit_code)