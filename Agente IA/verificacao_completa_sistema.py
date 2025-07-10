#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n{'=' * 80}")
    print(f"{title.upper()}")
    print(f"{'=' * 80}")

def verificar_sistema_completo():
    """Verificação completa do sistema PNSB"""
    
    problemas = []
    avisos = []
    
    print_section("VERIFICAÇÃO COMPLETA DO SISTEMA PNSB")
    print(f"Data da verificação: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    # 1. VERIFICAR ESTRUTURA DE DIRETÓRIOS
    print_section("1. ESTRUTURA DE DIRETÓRIOS")
    
    diretorios_essenciais = [
        "gestao_visitas",
        "gestao_visitas/models",
        "gestao_visitas/services",
        "gestao_visitas/routes",
        "gestao_visitas/templates",
        "gestao_visitas/static",
        "gestao_visitas/utils",
        "gestao_visitas/backups",
        "gestao_visitas/backups_automaticos",
        "documentos_pnsb"
    ]
    
    for dir_path in diretorios_essenciais:
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/{dir_path}"
        if os.path.exists(full_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - FALTANDO!")
            problemas.append(f"Diretório essencial faltando: {dir_path}")
    
    # 2. VERIFICAR ARQUIVOS CRÍTICOS
    print_section("2. ARQUIVOS CRÍTICOS DO SISTEMA")
    
    arquivos_criticos = {
        "app.py": "Arquivo principal da aplicação",
        "requirements.txt": "Dependências do projeto",
        ".env": "Variáveis de ambiente",
        "gestao_visitas/__init__.py": "Inicializador do pacote",
        "gestao_visitas/config.py": "Configurações do sistema",
        "gestao_visitas/db.py": "Configuração do banco de dados"
    }
    
    for arquivo, desc in arquivos_criticos.items():
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/{arquivo}"
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {arquivo} ({size} bytes) - {desc}")
            if size == 0:
                avisos.append(f"Arquivo {arquivo} está vazio")
        else:
            print(f"❌ {arquivo} - FALTANDO! - {desc}")
            problemas.append(f"Arquivo crítico faltando: {arquivo}")
    
    # 3. VERIFICAR BANCO DE DADOS
    print_section("3. INTEGRIDADE DO BANCO DE DADOS")
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    if os.path.exists(db_path):
        print(f"✅ Banco de dados encontrado ({os.path.getsize(db_path)} bytes)")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar integridade
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            if integrity == "ok":
                print("✅ Integridade do banco: OK")
            else:
                print(f"❌ Problema de integridade: {integrity}")
                problemas.append(f"Banco de dados com problemas de integridade: {integrity}")
            
            # Verificar tabelas essenciais
            tabelas_essenciais = [
                'visitas', 'checklists', 'contatos', 
                'questionarios_obrigatorios', 'entidades_identificadas',
                'progresso_questionarios', 'entidades_prioritarias_uf'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tabelas_existentes = [t[0] for t in cursor.fetchall()]
            
            print("\nTabelas do banco:")
            for tabela in tabelas_essenciais:
                if tabela in tabelas_existentes:
                    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                    count = cursor.fetchone()[0]
                    print(f"  ✅ {tabela}: {count} registros")
                else:
                    print(f"  ❌ {tabela}: FALTANDO!")
                    problemas.append(f"Tabela essencial faltando: {tabela}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Erro ao verificar banco: {str(e)}")
            problemas.append(f"Erro ao acessar banco de dados: {str(e)}")
    else:
        print("❌ Banco de dados não encontrado!")
        problemas.append("Banco de dados principal não encontrado")
    
    # 4. VERIFICAR CONFIGURAÇÕES
    print_section("4. CONFIGURAÇÕES E VARIÁVEIS DE AMBIENTE")
    
    env_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/.env"
    if os.path.exists(env_path):
        print("✅ Arquivo .env encontrado")
        
        # Verificar variáveis essenciais
        with open(env_path, 'r') as f:
            env_content = f.read()
            
        vars_essenciais = [
            'SECRET_KEY',
            'GOOGLE_MAPS_API_KEY',
            'DATABASE_URL'
        ]
        
        for var in vars_essenciais:
            if var in env_content:
                print(f"  ✅ {var} configurada")
            else:
                print(f"  ❌ {var} não configurada")
                avisos.append(f"Variável de ambiente {var} não configurada")
    else:
        print("❌ Arquivo .env não encontrado")
        problemas.append("Arquivo de configuração .env não encontrado")
    
    # 5. VERIFICAR SERVIÇOS
    print_section("5. SERVIÇOS DO SISTEMA")
    
    servicos_essenciais = [
        "relatorios.py",
        "rotas.py",
        "maps.py",
        "checklist.py",
        "auto_scheduler.py",
        "questionarios.py"
    ]
    
    for servico in servicos_essenciais:
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/services/{servico}"
        if os.path.exists(full_path):
            print(f"✅ {servico}")
        else:
            print(f"❌ {servico} - FALTANDO!")
            avisos.append(f"Serviço {servico} não encontrado")
    
    # 6. VERIFICAR MODELOS
    print_section("6. MODELOS DE DADOS")
    
    modelos_essenciais = [
        "agendamento.py",
        "checklist.py",
        "contatos.py",
        "questionarios_obrigatorios.py"
    ]
    
    for modelo in modelos_essenciais:
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/models/{modelo}"
        if os.path.exists(full_path):
            print(f"✅ {modelo}")
        else:
            print(f"❌ {modelo} - FALTANDO!")
            problemas.append(f"Modelo essencial faltando: {modelo}")
    
    # 7. VERIFICAR LOGS
    print_section("7. SISTEMA DE LOGS")
    
    log_files = [
        "app.log",
        "flask.log",
        "server.log"
    ]
    
    for log_file in log_files:
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/{log_file}"
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"✅ {log_file} ({size} bytes)")
            if size > 10485760:  # 10MB
                avisos.append(f"Arquivo de log {log_file} muito grande ({size} bytes)")
        else:
            print(f"ℹ️  {log_file} - não existe (normal se sistema não foi executado)")
    
    # 8. VERIFICAR BACKUPS
    print_section("8. SISTEMA DE BACKUPS")
    
    backup_dirs = [
        "gestao_visitas/backups",
        "gestao_visitas/backups_automaticos"
    ]
    
    for backup_dir in backup_dirs:
        full_path = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/{backup_dir}"
        if os.path.exists(full_path):
            backups = os.listdir(full_path)
            print(f"✅ {backup_dir}: {len(backups)} backups encontrados")
            
            # Verificar backup mais recente
            if backups:
                backups_com_tempo = []
                for b in backups:
                    b_path = os.path.join(full_path, b)
                    if os.path.isfile(b_path) or os.path.isdir(b_path):
                        mtime = os.path.getmtime(b_path)
                        backups_com_tempo.append((b, mtime))
                
                if backups_com_tempo:
                    backups_com_tempo.sort(key=lambda x: x[1], reverse=True)
                    ultimo_backup = backups_com_tempo[0]
                    tempo_decorrido = (datetime.now().timestamp() - ultimo_backup[1]) / 3600
                    print(f"   Último backup: {ultimo_backup[0]} ({tempo_decorrido:.1f} horas atrás)")
                    
                    if tempo_decorrido > 24:
                        avisos.append(f"Último backup tem mais de 24 horas")
        else:
            print(f"❌ {backup_dir} - FALTANDO!")
            avisos.append(f"Diretório de backup {backup_dir} não encontrado")
    
    # RESUMO FINAL
    print_section("RESUMO DA VERIFICAÇÃO")
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   - Problemas críticos: {len(problemas)}")
    print(f"   - Avisos: {len(avisos)}")
    
    if problemas:
        print(f"\n❌ PROBLEMAS CRÍTICOS ({len(problemas)}):")
        for i, problema in enumerate(problemas, 1):
            print(f"   {i}. {problema}")
    
    if avisos:
        print(f"\n⚠️  AVISOS ({len(avisos)}):")
        for i, aviso in enumerate(avisos, 1):
            print(f"   {i}. {aviso}")
    
    if not problemas and not avisos:
        print("\n✅ SISTEMA EM PERFEITO ESTADO!")
    elif not problemas:
        print("\n✅ Sistema operacional, mas com alguns avisos para atenção.")
    else:
        print("\n❌ Sistema com problemas críticos que precisam ser resolvidos!")
    
    # RECOMENDAÇÕES
    print_section("RECOMENDAÇÕES DE AÇÃO")
    
    if problemas or avisos:
        recomendacoes = []
        
        # Analisar problemas e gerar recomendações
        for problema in problemas:
            if "banco de dados" in problema.lower():
                recomendacoes.append("Restaurar banco de dados a partir do último backup")
            if "faltando" in problema.lower():
                recomendacoes.append("Verificar se todos os arquivos foram copiados corretamente")
            if "integridade" in problema.lower():
                recomendacoes.append("Executar verificação e reparo do banco de dados")
        
        for aviso in avisos:
            if "backup" in aviso.lower():
                recomendacoes.append("Executar backup manual do sistema")
            if "log" in aviso.lower() and "grande" in aviso.lower():
                recomendacoes.append("Limpar arquivos de log antigos")
            if "variável" in aviso.lower():
                recomendacoes.append("Configurar variáveis de ambiente faltantes no arquivo .env")
        
        # Recomendações gerais baseadas nos dados encontrados
        if any("checklist" in p.lower() for p in problemas):
            recomendacoes.append("Inicializar sistema de checklists executando o script apropriado")
        
        if any("questionário" in p.lower() for p in problemas):
            recomendacoes.append("Configurar questionários obrigatórios para os municípios")
        
        if any("contato" in p.lower() for p in problemas):
            recomendacoes.append("Importar dados de contatos usando o script de importação")
        
        # Imprimir recomendações únicas
        recomendacoes_unicas = list(set(recomendacoes))
        for i, rec in enumerate(recomendacoes_unicas, 1):
            print(f"{i}. {rec}")
    else:
        print("Nenhuma ação necessária - sistema funcionando perfeitamente!")
    
    print("\n" + "=" * 80)
    print("Verificação concluída.")

if __name__ == "__main__":
    verificar_sistema_completo()