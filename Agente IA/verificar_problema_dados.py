#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def verificar_problema_dados():
    """Verifica problemas específicos com dados zerados"""
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("VERIFICAÇÃO DE PROBLEMAS COM DADOS ZERADOS")
    print("=" * 80)
    
    # 1. VERIFICAR CHECKLISTS
    print("\n1. ANÁLISE DOS CHECKLISTS")
    print("-" * 40)
    
    # Verificar se existem checklists
    cursor.execute("SELECT COUNT(*) as total FROM checklists")
    total_checklists = cursor.fetchone()['total']
    print(f"Total de checklists: {total_checklists}")
    
    if total_checklists == 0:
        # Verificar se há visitas sem checklist
        cursor.execute("""
            SELECT v.id, v.municipio, v.data, v.status
            FROM visitas v
            LEFT JOIN checklists c ON v.id = c.visita_id
            WHERE c.id IS NULL
        """)
        visitas_sem_checklist = cursor.fetchall()
        
        if visitas_sem_checklist:
            print(f"\n⚠️  {len(visitas_sem_checklist)} visitas sem checklist:")
            for v in visitas_sem_checklist[:5]:  # Mostrar apenas as 5 primeiras
                print(f"   - ID {v['id']}: {v['municipio']} ({v['data']}) - Status: {v['status']}")
            
            print("\n💡 SOLUÇÃO: Executar script para criar checklists para visitas existentes")
    
    # 2. VERIFICAR CONTATOS
    print("\n\n2. ANÁLISE DOS CONTATOS")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total FROM contatos")
    total_contatos = cursor.fetchone()['total']
    print(f"Total de contatos: {total_contatos}")
    
    if total_contatos == 0:
        # Verificar se existem arquivos CSV de contatos
        csv_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/pesquisa_contatos_prefeituras"
        if os.path.exists(csv_path):
            csv_files = [f for f in os.listdir(csv_path) if f.endswith('.csv')]
            print(f"\n📁 Arquivos CSV encontrados em pesquisa_contatos_prefeituras: {len(csv_files)}")
            for csv_file in csv_files:
                print(f"   - {csv_file}")
            
            print("\n💡 SOLUÇÃO: Executar script de importação de contatos dos arquivos CSV")
        else:
            print("\n❌ Diretório de CSVs de contatos não encontrado")
    
    # 3. VERIFICAR QUESTIONÁRIOS OBRIGATÓRIOS
    print("\n\n3. ANÁLISE DOS QUESTIONÁRIOS OBRIGATÓRIOS")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total FROM questionarios_obrigatorios")
    total_quest_obrig = cursor.fetchone()['total']
    print(f"Total de configurações de questionários obrigatórios: {total_quest_obrig}")
    
    if total_quest_obrig == 0:
        # Verificar entidades identificadas
        cursor.execute("""
            SELECT municipio, COUNT(*) as total,
                   SUM(mrs_obrigatorio) as mrs_obrig,
                   SUM(map_obrigatorio) as map_obrig
            FROM entidades_identificadas
            GROUP BY municipio
        """)
        entidades_por_municipio = cursor.fetchall()
        
        if entidades_por_municipio:
            print("\n📊 Entidades identificadas por município:")
            for e in entidades_por_municipio:
                print(f"   - {e['municipio']}: {e['total']} entidades (MRS: {e['mrs_obrig']}, MAP: {e['map_obrig']})")
            
            print("\n💡 SOLUÇÃO: Configurar questionários obrigatórios baseado nas entidades identificadas")
    
    # 4. VERIFICAR PROGRESSO DOS QUESTIONÁRIOS
    print("\n\n4. ANÁLISE DO PROGRESSO DOS QUESTIONÁRIOS")
    print("-" * 40)
    
    cursor.execute("""
        SELECT municipio, 
               total_mrs_obrigatorios, mrs_concluidos,
               total_map_obrigatorios, map_concluidos,
               percentual_geral
        FROM progresso_questionarios
        WHERE percentual_geral > 0
    """)
    progressos_com_dados = cursor.fetchall()
    
    if not progressos_com_dados:
        print("⚠️  Todos os municípios estão com progresso 0%")
        
        # Verificar se há questionários preenchidos nas entidades
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM entidades_identificadas
            WHERE status_mrs IS NOT NULL OR status_map IS NOT NULL
        """)
        entidades_com_status = cursor.fetchone()['total']
        
        print(f"\nEntidades com status de questionário: {entidades_com_status}")
        
        if entidades_com_status == 0:
            print("\n💡 SOLUÇÃO: Atualizar status dos questionários conforme forem sendo preenchidos")
    
    # 5. VERIFICAR INCONSISTÊNCIAS
    print("\n\n5. VERIFICAÇÃO DE INCONSISTÊNCIAS")
    print("-" * 40)
    
    # Verificar visitas com tipos de pesquisa inconsistentes
    cursor.execute("""
        SELECT DISTINCT tipo_pesquisa, COUNT(*) as total
        FROM visitas
        GROUP BY tipo_pesquisa
    """)
    tipos_pesquisa = cursor.fetchall()
    
    print("Tipos de pesquisa encontrados:")
    inconsistencias = []
    for tp in tipos_pesquisa:
        print(f"   - '{tp['tipo_pesquisa']}': {tp['total']} visitas")
        if tp['tipo_pesquisa'] not in ['MRS', 'MAP', 'MRS+MAP']:
            inconsistencias.append(f"Tipo de pesquisa não padronizado: '{tp['tipo_pesquisa']}'")
    
    # Verificar datas inválidas
    cursor.execute("SELECT id, data FROM visitas")
    visitas_datas = cursor.fetchall()
    
    datas_invalidas = []
    for v in visitas_datas:
        if ' ' in str(v['data']):  # Data com hora incluída
            datas_invalidas.append(f"Visita ID {v['id']}: formato de data inválido '{v['data']}'")
    
    if datas_invalidas:
        print(f"\n⚠️  {len(datas_invalidas)} visitas com formato de data inválido")
        inconsistencias.extend(datas_invalidas[:3])  # Adicionar apenas as 3 primeiras
    
    # CRIAR SCRIPTS DE CORREÇÃO
    print("\n\n" + "=" * 80)
    print("SCRIPTS DE CORREÇÃO RECOMENDADOS")
    print("=" * 80)
    
    scripts_necessarios = []
    
    if total_checklists == 0:
        scripts_necessarios.append({
            'nome': 'criar_checklists.py',
            'descricao': 'Criar checklists para todas as visitas existentes',
            'prioridade': 'ALTA'
        })
    
    if total_contatos == 0:
        scripts_necessarios.append({
            'nome': 'importar_contatos.py',
            'descricao': 'Importar contatos dos arquivos CSV',
            'prioridade': 'ALTA'
        })
    
    if total_quest_obrig == 0:
        scripts_necessarios.append({
            'nome': 'configurar_questionarios.py',
            'descricao': 'Configurar questionários obrigatórios por município',
            'prioridade': 'MÉDIA'
        })
    
    if inconsistencias:
        scripts_necessarios.append({
            'nome': 'corrigir_inconsistencias.py',
            'descricao': 'Corrigir tipos de pesquisa e formatos de data',
            'prioridade': 'ALTA'
        })
    
    if scripts_necessarios:
        print("\nScripts necessários:")
        for script in scripts_necessarios:
            print(f"\n📝 {script['nome']} (Prioridade: {script['prioridade']})")
            print(f"   {script['descricao']}")
    else:
        print("\n✅ Nenhum script de correção necessário!")
    
    conn.close()

if __name__ == "__main__":
    verificar_problema_dados()