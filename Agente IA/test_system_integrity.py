#!/usr/bin/env python3
"""
Teste de Integridade do Sistema PNSB
Verifica se todos os componentes estão corretamente implementados
"""

import os
import sys
from pathlib import Path

def test_file_structure():
    """Testa se a estrutura de arquivos está correta"""
    print("🔍 Testando estrutura de arquivos...")
    
    required_files = [
        'gestao_visitas/models/contatos.py',
        'gestao_visitas/models/agendamento.py',
        'gestao_visitas/services/perfil_informante.py',
        'gestao_visitas/services/logistica_maps.py',
        'gestao_visitas/services/comunicacao_eficiente.py',
        'gestao_visitas/services/analise_resistencia.py',
        'gestao_visitas/services/dashboard_produtividade.py',
        'gestao_visitas/services/otimizador_cronograma.py',
        'gestao_visitas/routes/funcionalidades_pnsb_api.py',
        'gestao_visitas/config/security.py',
        'gestao_visitas/utils/validators.py',
        'gestao_visitas/utils/error_handlers.py',
        'migrations/versions/001_add_pnsb_fields.py',
        'requirements.txt',
        '.env'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Arquivos faltando: {missing_files}")
        return False
    else:
        print("✅ Todos os arquivos necessários estão presentes")
        return True

def test_python_syntax():
    """Testa sintaxe Python de arquivos críticos"""
    print("🔍 Testando sintaxe Python...")
    
    python_files = [
        'gestao_visitas/models/contatos.py',
        'gestao_visitas/models/agendamento.py',
        'gestao_visitas/services/perfil_informante.py',
        'gestao_visitas/services/logistica_maps.py',
        'gestao_visitas/routes/funcionalidades_pnsb_api.py',
        'gestao_visitas/config/security.py',
        'gestao_visitas/utils/validators.py',
        'gestao_visitas/utils/error_handlers.py'
    ]
    
    syntax_errors = []
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}: {e}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: {e}")
    
    if syntax_errors:
        print(f"❌ Erros de sintaxe encontrados:")
        for error in syntax_errors:
            print(f"   {error}")
        return False
    else:
        print("✅ Sintaxe Python válida em todos os arquivos")
        return True

def test_model_fields():
    """Testa se os modelos têm os campos necessários"""
    print("🔍 Testando campos dos modelos...")
    
    # Testar modelo Contato
    try:
        with open('gestao_visitas/models/contatos.py', 'r') as f:
            contato_content = f.read()
        
        required_contato_fields = [
            'nome = Column',
            'telefone = Column', 
            'email = Column',
            'cargo = Column',
            'orgao = Column',
            'endereco = Column',
            'historico_abordagens = Column',
            'historico_comunicacao = Column'
        ]
        
        missing_contato_fields = []
        for field in required_contato_fields:
            if field not in contato_content:
                missing_contato_fields.append(field)
        
        if missing_contato_fields:
            print(f"❌ Campos faltando no modelo Contato: {missing_contato_fields}")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar modelo Contato: {e}")
        return False
    
    # Testar modelo Visita
    try:
        with open('gestao_visitas/models/agendamento.py', 'r') as f:
            visita_content = f.read()
        
        if 'pesquisador_responsavel = Column' not in visita_content:
            print("❌ Campo pesquisador_responsavel faltando no modelo Visita")
            return False
    except Exception as e:
        print(f"❌ Erro ao verificar modelo Visita: {e}")
        return False
    
    print("✅ Todos os campos necessários estão presentes nos modelos")
    return True

def test_api_endpoints():
    """Testa se os endpoints da API estão definidos"""
    print("🔍 Testando definição de endpoints da API...")
    
    try:
        with open('gestao_visitas/routes/funcionalidades_pnsb_api.py', 'r') as f:
            api_content = f.read()
        
        expected_endpoints = [
            '@funcionalidades_pnsb_bp.route(\'/perfil-informante/',
            '@funcionalidades_pnsb_bp.route(\'/logistica/',
            '@funcionalidades_pnsb_bp.route(\'/questionarios/',
            '@funcionalidades_pnsb_bp.route(\'/abordagem/',
            '@funcionalidades_pnsb_bp.route(\'/contingencia/',
            '@funcionalidades_pnsb_bp.route(\'/comunicacao/',
            '@funcionalidades_pnsb_bp.route(\'/resistencia/',
            '@funcionalidades_pnsb_bp.route(\'/produtividade/',
            '@funcionalidades_pnsb_bp.route(\'/cronograma/'
        ]
        
        missing_endpoints = []
        for endpoint in expected_endpoints:
            if endpoint not in api_content:
                missing_endpoints.append(endpoint)
        
        if missing_endpoints:
            print(f"❌ Endpoints faltando: {missing_endpoints}")
            return False
        else:
            print("✅ Todos os endpoints principais estão definidos")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar endpoints: {e}")
        return False

def test_service_classes():
    """Testa se as classes de serviço estão definidas"""
    print("🔍 Testando classes de serviço...")
    
    services = {
        'gestao_visitas/services/perfil_informante.py': 'class PerfilInformante',
        'gestao_visitas/services/logistica_maps.py': 'class LogisticaMaps',
        'gestao_visitas/services/comunicacao_eficiente.py': 'class ComunicacaoEficiente',
        'gestao_visitas/services/analise_resistencia.py': 'class AnaliseResistencia',
        'gestao_visitas/services/dashboard_produtividade.py': 'class DashboardProdutividade',
        'gestao_visitas/services/otimizador_cronograma.py': 'class OtimizadorCronograma'
    }
    
    missing_classes = []
    for file_path, class_def in services.items():
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            if class_def not in content:
                missing_classes.append(f"{class_def} em {file_path}")
        except Exception as e:
            missing_classes.append(f"Erro ao ler {file_path}: {e}")
    
    if missing_classes:
        print(f"❌ Classes de serviço faltando: {missing_classes}")
        return False
    else:
        print("✅ Todas as classes de serviço estão definidas")
        return True

def test_migrations():
    """Testa se as migrações estão presentes"""
    print("🔍 Testando migrações do banco de dados...")
    
    migration_file = 'migrations/versions/001_add_pnsb_fields.py'
    
    if not os.path.exists(migration_file):
        print(f"❌ Migração PNSB não encontrada: {migration_file}")
        return False
    
    try:
        with open(migration_file, 'r') as f:
            migration_content = f.read()
        
        required_migrations = [
            'nome',
            'telefone', 
            'email',
            'pesquisador_responsavel'
        ]
        
        missing_migrations = []
        for field in required_migrations:
            if field not in migration_content:
                missing_migrations.append(field)
        
        if missing_migrations:
            print(f"❌ Campos faltando na migração: {missing_migrations}")
            return False
        else:
            print("✅ Migração PNSB está completa")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar migração: {e}")
        return False

def test_configuration():
    """Testa se as configurações estão presentes"""
    print("🔍 Testando configurações...")
    
    # Verificar arquivo .env
    if not os.path.exists('.env'):
        print("❌ Arquivo .env não encontrado")
        return False
    
    # Verificar requirements.txt
    if not os.path.exists('requirements.txt'):
        print("❌ Arquivo requirements.txt não encontrado")
        return False
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements = f.read()
        
        required_packages = ['Flask', 'SQLAlchemy', 'googlemaps', 'alembic']
        missing_packages = []
        
        for package in required_packages:
            if package not in requirements:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"❌ Pacotes faltando no requirements.txt: {missing_packages}")
            return False
        else:
            print("✅ Configurações estão corretas")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar configurações: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DE INTEGRIDADE DO SISTEMA PNSB")
    print("=" * 60)
    
    tests = [
        test_file_structure,
        test_python_syntax,
        test_model_fields,
        test_api_endpoints,
        test_service_classes,
        test_migrations,
        test_configuration
    ]
    
    results = []
    for test in tests:
        result = test()
        results.append(result)
        print()
    
    print("=" * 60)
    print("📊 RESULTADOS FINAIS")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema está íntegro e pronto para uso")
        print("\n💡 Próximos passos:")
        print("   1. Instalar dependências: pip install -r requirements.txt")
        print("   2. Configurar chaves da API no arquivo .env")
        print("   3. Executar migrações: flask db upgrade")
        print("   4. Iniciar o sistema: python app_new.py")
        return 0
    else:
        print(f"❌ {total - passed} TESTES FALHARAM!")
        print(f"📊 Taxa de sucesso: {passed}/{total} ({(passed/total)*100:.1f}%)")
        print("\n🔧 Corrija os problemas acima antes de continuar")
        return 1

if __name__ == '__main__':
    exit(main())