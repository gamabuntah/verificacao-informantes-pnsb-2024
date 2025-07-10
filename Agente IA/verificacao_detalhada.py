#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
import json
from datetime import datetime
from collections import defaultdict

def verificacao_detalhada():
    """Verificação detalhada do sistema PNSB"""
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    problemas = []
    
    print("=" * 80)
    print("VERIFICAÇÃO DETALHADA DO SISTEMA PNSB")
    print("=" * 80)
    
    # 1. VERIFICAR VISITAS
    print("\n1. ANÁLISE DAS VISITAS")
    print("-" * 40)
    
    cursor.execute("SELECT * FROM visitas ORDER BY data, hora_inicio")
    visitas = cursor.fetchall()
    
    print(f"Total de visitas: {len(visitas)}")
    
    # Contar por município
    municipios_visitas = defaultdict(int)
    status_count = defaultdict(int)
    tipos_pesquisa = defaultdict(int)
    
    for visita in visitas:
        municipios_visitas[visita['municipio']] += 1
        status_count[visita['status']] += 1
        tipos_pesquisa[visita['tipo_pesquisa']] += 1
    
    print("\n📍 Visitas por município:")
    for mun, count in sorted(municipios_visitas.items()):
        print(f"   - {mun}: {count} visitas")
    
    print("\n📊 Status das visitas:")
    for status, count in sorted(status_count.items()):
        print(f"   - {status}: {count}")
    
    print("\n📝 Tipos de pesquisa:")
    for tipo, count in sorted(tipos_pesquisa.items()):
        print(f"   - {tipo}: {count}")
    
    # Verificar municípios faltantes
    municipios_esperados = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 
        'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves', 
        'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    municipios_sem_visita = set(municipios_esperados) - set(municipios_visitas.keys())
    if municipios_sem_visita:
        problemas.append(f"Municípios sem visitas agendadas: {', '.join(municipios_sem_visita)}")
    
    # Verificar datas
    print("\n📅 Análise de datas:")
    datas_passadas = 0
    for visita in visitas:
        try:
            data_visita = datetime.strptime(visita['data'], '%Y-%m-%d').date()
            if data_visita < datetime.now().date():
                datas_passadas += 1
        except:
            problemas.append(f"Data inválida na visita ID {visita['id']}: {visita['data']}")
    
    if datas_passadas > 0:
        print(f"   ⚠️  {datas_passadas} visitas com datas passadas")
    
    # 2. VERIFICAR ENTIDADES IDENTIFICADAS
    print("\n\n2. ANÁLISE DAS ENTIDADES IDENTIFICADAS")
    print("-" * 40)
    
    cursor.execute("SELECT * FROM entidades_identificadas")
    entidades = cursor.fetchall()
    
    print(f"Total de entidades: {len(entidades)}")
    
    # Análise por município
    entidades_por_municipio = defaultdict(int)
    prioridades = defaultdict(int)
    tipos_entidade = defaultdict(int)
    
    for ent in entidades:
        entidades_por_municipio[ent['municipio']] += 1
        prioridades[ent['categoria_prioridade']] += 1
        tipos_entidade[ent['tipo_entidade']] += 1
    
    print("\n📍 Entidades por município:")
    for mun, count in sorted(entidades_por_municipio.items()):
        print(f"   - {mun}: {count} entidades")
    
    print("\n🎯 Distribuição de prioridades:")
    for prio, count in sorted(prioridades.items()):
        print(f"   - {prio}: {count}")
    
    print("\n🏢 Tipos de entidade:")
    for tipo, count in sorted(tipos_entidade.items()):
        print(f"   - {tipo}: {count}")
    
    # 3. VERIFICAR CHECKLISTS
    print("\n\n3. ANÁLISE DOS CHECKLISTS")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total FROM checklists")
    total_checklists = cursor.fetchone()['total']
    print(f"Total de checklists: {total_checklists}")
    
    if total_checklists == 0:
        problemas.append("Nenhum checklist criado - sistema de checklist pode estar inativo")
    
    # 4. VERIFICAR QUESTIONÁRIOS OBRIGATÓRIOS
    print("\n\n4. ANÁLISE DOS QUESTIONÁRIOS OBRIGATÓRIOS")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total FROM questionarios_obrigatorios")
    total_quest = cursor.fetchone()['total']
    print(f"Total de configurações de questionários: {total_quest}")
    
    if total_quest == 0:
        problemas.append("Nenhuma configuração de questionário obrigatório - sistema pode não estar configurado")
    
    # 5. VERIFICAR PROGRESSO DOS QUESTIONÁRIOS
    print("\n\n5. ANÁLISE DO PROGRESSO DOS QUESTIONÁRIOS")
    print("-" * 40)
    
    cursor.execute("SELECT * FROM progresso_questionarios")
    progressos = cursor.fetchall()
    
    for prog in progressos:
        print(f"\n📊 {prog['municipio']}:")
        print(f"   - MRS: {prog['mrs_concluidos'] or 0}/{prog['total_mrs_obrigatorios'] or 0} ({prog['percentual_mrs'] or 0:.1f}%)")
        print(f"   - MAP: {prog['map_concluidos'] or 0}/{prog['total_map_obrigatorios'] or 0} ({prog['percentual_map'] or 0:.1f}%)")
        print(f"   - Geral: {prog['percentual_geral'] or 0:.1f}%")
    
    # 6. VERIFICAR CONTATOS
    print("\n\n6. ANÁLISE DOS CONTATOS")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total FROM contatos")
    total_contatos = cursor.fetchone()['total']
    print(f"Total de contatos: {total_contatos}")
    
    if total_contatos == 0:
        problemas.append("Nenhum contato cadastrado - pode ser necessário importar dados de contatos")
    
    # 7. VERIFICAR ENTIDADES PRIORITÁRIAS UF
    print("\n\n7. ANÁLISE DAS ENTIDADES PRIORITÁRIAS (LISTA UF)")
    print("-" * 40)
    
    cursor.execute("SELECT COUNT(*) as total, COUNT(DISTINCT municipio) as municipios FROM entidades_prioritarias_uf")
    uf_stats = cursor.fetchone()
    print(f"Total de entidades da lista UF: {uf_stats['total']}")
    print(f"Municípios cobertos: {uf_stats['municipios']}")
    
    # 8. VERIFICAR ARQUIVOS IMPORTANTES
    print("\n\n8. VERIFICAÇÃO DE ARQUIVOS DO SISTEMA")
    print("-" * 40)
    
    arquivos_criticos = [
        "app.py",
        "requirements.txt",
        "gestao_visitas/config.py",
        "gestao_visitas/__init__.py"
    ]
    
    for arquivo in arquivos_criticos:
        caminho_completo = f"/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/{arquivo}"
        if os.path.exists(caminho_completo):
            print(f"   ✅ {arquivo}")
        else:
            print(f"   ❌ {arquivo} - ARQUIVO FALTANDO!")
            problemas.append(f"Arquivo crítico faltando: {arquivo}")
    
    # RESUMO DOS PROBLEMAS
    print("\n\n" + "=" * 80)
    print("RESUMO DOS PROBLEMAS ENCONTRADOS")
    print("=" * 80)
    
    if problemas:
        for i, problema in enumerate(problemas, 1):
            print(f"{i}. ❌ {problema}")
    else:
        print("✅ Nenhum problema crítico encontrado!")
    
    # RECOMENDAÇÕES
    print("\n\nRECOMENDAÇÕES:")
    print("-" * 40)
    
    if total_checklists == 0:
        print("1. Inicializar sistema de checklists para as visitas existentes")
    
    if total_quest == 0:
        print("2. Configurar questionários obrigatórios para cada município")
    
    if total_contatos == 0:
        print("3. Importar dados de contatos das prefeituras")
    
    if municipios_sem_visita:
        print(f"4. Agendar visitas para os municípios faltantes: {', '.join(municipios_sem_visita)}")
    
    if datas_passadas > 0:
        print("5. Atualizar datas das visitas passadas ou mudar seus status")
    
    conn.close()

if __name__ == "__main__":
    verificacao_detalhada()