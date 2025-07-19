#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def validar_entidades():
    """Valida regras de negócio das entidades identificadas"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    if not os.path.exists(db_path):
        print('❌ Banco de dados não encontrado')
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print('=== VALIDAÇÃO DE REGRAS DE NEGÓCIO ===')
    
    # 1. Verificar se todas as prefeituras estão P1
    print('\n1. Verificar prefeituras P1:')
    cursor.execute("""
        SELECT municipio, prioridade, categoria_prioridade, mrs_obrigatorio, map_obrigatorio 
        FROM entidades_identificadas 
        WHERE tipo_entidade = 'prefeitura' 
        ORDER BY municipio
    """)
    prefeituras = cursor.fetchall()
    
    municipios_esperados = [
        'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 
        'Camboriú', 'Itajaí', 'Itapema', 'Luiz Alves', 
        'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
    ]
    
    municipios_encontrados = []
    problemas_prioridade = []
    problemas_questionarios = []
    
    for pref in prefeituras:
        municipio, prioridade, categoria, mrs, map_val = pref
        municipios_encontrados.append(municipio)
        
        if prioridade != 1 or categoria != 'p1':
            problemas_prioridade.append(f'  ❌ {municipio}: prioridade {prioridade}/{categoria} (deveria ser 1/p1)')
        
        if not mrs or not map_val:
            problemas_questionarios.append(f'  ❌ {municipio}: MRS={mrs} MAP={map_val} (ambos deveriam ser True)')
    
    municipios_faltantes = set(municipios_esperados) - set(municipios_encontrados)
    
    print(f'✅ Prefeituras encontradas: {len(prefeituras)}/11')
    if municipios_faltantes:
        print(f'❌ Prefeituras faltantes: {list(municipios_faltantes)}')
    
    if problemas_prioridade:
        print('❌ Problemas de prioridade:')
        for p in problemas_prioridade:
            print(p)
    
    if problemas_questionarios:
        print('❌ Problemas de questionários obrigatórios:')
        for p in problemas_questionarios:
            print(p)
    
    # 2. Verificar distribuição de prioridades
    print('\n2. Distribuição de prioridades:')
    cursor.execute("""
        SELECT prioridade, categoria_prioridade, COUNT(*) 
        FROM entidades_identificadas 
        GROUP BY prioridade, categoria_prioridade 
        ORDER BY prioridade
    """)
    prioridades = cursor.fetchall()
    
    for prio, cat, count in prioridades:
        print(f'  P{prio} ({cat}): {count} entidades')
    
    # 3. Verificar status de questionários
    print('\n3. Status dos questionários:')
    cursor.execute("""
        SELECT status_mrs, COUNT(*) 
        FROM entidades_identificadas 
        WHERE mrs_obrigatorio = 1 
        GROUP BY status_mrs
    """)
    mrs_status = cursor.fetchall()
    
    cursor.execute("""
        SELECT status_map, COUNT(*) 
        FROM entidades_identificadas 
        WHERE map_obrigatorio = 1 
        GROUP BY status_map
    """)
    map_status = cursor.fetchall()
    
    print('  MRS Status:')
    for status, count in mrs_status:
        print(f'    {status}: {count}')
    
    print('  MAP Status:')
    for status, count in map_status:
        print(f'    {status}: {count}')
    
    # 4. Verificar integridade referencial
    print('\n4. Integridade referencial:')
    cursor.execute("""
        SELECT COUNT(*) 
        FROM entidades_identificadas 
        WHERE visita_id IS NOT NULL
    """)
    entidades_com_visita = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM entidades_identificadas 
        WHERE visita_id IS NOT NULL 
        AND visita_id NOT IN (SELECT id FROM visitas)
    """)
    entidades_orfas = cursor.fetchone()[0]
    
    print(f'  Entidades com visita: {entidades_com_visita}')
    if entidades_orfas > 0:
        print(f'  ❌ Entidades órfãs (visita inexistente): {entidades_orfas}')
    else:
        print(f'  ✅ Integridade referencial OK')
    
    # 5. Validar status workflow
    print('\n5. Validar status workflow:')
    cursor.execute("""
        SELECT status_mrs, COUNT(*) 
        FROM entidades_identificadas 
        WHERE status_mrs NOT IN ('nao_iniciado', 'respondido', 'validado_concluido', 'nao_aplicavel')
        GROUP BY status_mrs
    """)
    mrs_invalid = cursor.fetchall()
    
    cursor.execute("""
        SELECT status_map, COUNT(*) 
        FROM entidades_identificadas 
        WHERE status_map NOT IN ('nao_iniciado', 'respondido', 'validado_concluido', 'nao_aplicavel')
        GROUP BY status_map
    """)
    map_invalid = cursor.fetchall()
    
    if mrs_invalid:
        print('  ❌ Status MRS inválidos:')
        for status, count in mrs_invalid:
            print(f'    {status}: {count}')
    
    if map_invalid:
        print('  ❌ Status MAP inválidos:')
        for status, count in map_invalid:
            print(f'    {status}: {count}')
    
    if not mrs_invalid and not map_invalid:
        print('  ✅ Status workflow OK')
    
    conn.close()
    return True

if __name__ == "__main__":
    validar_entidades()