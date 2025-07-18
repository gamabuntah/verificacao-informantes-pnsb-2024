#!/usr/bin/env python3
"""Simple query for duplicate analysis"""

import sqlite3
import os

# Path to database
db_path = "gestao_visitas/gestao_visitas.db"

if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

# Connect to database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Query all prefecture entities
query = """
SELECT 
    municipio,
    nome_entidade,
    fonte_identificacao,
    status_mrs,
    status_map,
    visita_id,
    id,
    origem_prefeitura,
    prioridade
FROM entidades_identificadas 
WHERE nome_entidade LIKE '%refeitura%'
ORDER BY municipio, nome_entidade
"""

cursor.execute(query)
results = cursor.fetchall()

# Group by municipality
municipalities = {}
for row in results:
    muni = row[0]
    if muni not in municipalities:
        municipalities[muni] = []
    municipalities[muni].append({
        'nome': row[1],
        'fonte': row[2] or 'sem_fonte',
        'mrs_status': row[3] or 'sem_status',
        'map_status': row[4] or 'sem_status',
        'visita_id': row[5] or 'sem_visita',
        'id': row[6],
        'origem_prefeitura': row[7],
        'prioridade': row[8]
    })

print('=' * 60)
print('ANÁLISE DE DUPLICATAS DE PREFEITURAS')
print('=' * 60)

total_entities = len(results)
duplicated_municipalities = 0

for muni, entities in municipalities.items():
    status_icon = "⚠️" if len(entities) > 1 else "✅"
    print(f'\n{status_icon} {muni}: {len(entities)} entidade(s)')
    
    if len(entities) > 1:
        duplicated_municipalities += 1
        
        for i, entity in enumerate(entities, 1):
            # Special analysis for Bombinhas (user specified)
            special_notes = []
            if 'vigilância' in entity['nome'].lower():
                special_notes.append("VIGILÂNCIA SANITÁRIA")
            if 'captação' in entity['nome'].lower():
                special_notes.append("CAPTAÇÃO")
            if entity['mrs_status'] not in ['sem_status', 'nao_iniciado']:
                special_notes.append(f"MRS:{entity['mrs_status']}")
            if entity['map_status'] not in ['sem_status', 'nao_iniciado']:
                special_notes.append(f"MAP:{entity['map_status']}")
            if entity['visita_id'] != 'sem_visita':
                special_notes.append(f"VISITA:{entity['visita_id']}")
            
            recommendation = "🔹 CANDIDATO REMOÇÃO"
            if special_notes:
                recommendation = "🔸 MANTER"
            if muni == 'Bombinhas' and ('vigilância' in entity['nome'].lower() or 'captação' in entity['nome'].lower()):
                recommendation = "🔺 MANTER (USUÁRIO ESPECIFICOU)"
            
            print(f"   {i}. ID:{entity['id']} - {entity['nome']}")
            print(f"      Status: MRS={entity['mrs_status']}, MAP={entity['map_status']}")
            print(f"      Fonte: {entity['fonte']} | Visita: {entity['visita_id']}")
            print(f"      Especiais: {', '.join(special_notes) if special_notes else 'nenhuma'}")
            print(f"      {recommendation}")
    else:
        entity = entities[0]
        print(f"   ✅ ID:{entity['id']} - {entity['nome']} (único)")

print('\n' + '=' * 60)
print('RESUMO')
print('=' * 60)
print(f"Total de entidades: {total_entities}")
print(f"Municípios com duplicatas: {duplicated_municipalities}")
print(f"Entidades esperadas: 11 (uma por município)")
print(f"Entidades excedentes: {total_entities - 11}")

conn.close()