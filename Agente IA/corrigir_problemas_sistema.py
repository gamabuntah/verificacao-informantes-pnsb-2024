#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import sqlite3
from datetime import datetime
from pathlib import Path

# Adicionar o diretório ao PYTHONPATH
sys.path.append(str(Path(__file__).parent))

def corrigir_problemas():
    """Corrige os principais problemas identificados no sistema"""
    
    print("=" * 80)
    print("CORREÇÃO AUTOMÁTICA DOS PROBLEMAS DO SISTEMA PNSB")
    print("=" * 80)
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    problemas_corrigidos = []
    
    # 1. CORRIGIR FORMATOS DE DATA
    print("\n1. CORRIGINDO FORMATOS DE DATA")
    print("-" * 40)
    
    cursor.execute("SELECT id, data FROM visitas WHERE data LIKE '% %'")
    visitas_com_data_errada = cursor.fetchall()
    
    if visitas_com_data_errada:
        print(f"Encontradas {len(visitas_com_data_errada)} visitas com formato de data incorreto")
        
        for visita_id, data_errada in visitas_com_data_errada:
            # Extrair apenas a parte da data (YYYY-MM-DD)
            data_correta = data_errada.split(' ')[0]
            cursor.execute("UPDATE visitas SET data = ? WHERE id = ?", (data_correta, visita_id))
            print(f"   ✅ Visita ID {visita_id}: {data_errada} → {data_correta}")
        
        conn.commit()
        problemas_corrigidos.append(f"Corrigidas {len(visitas_com_data_errada)} datas com formato incorreto")
    else:
        print("   ✅ Todas as datas estão no formato correto")
    
    # 2. PADRONIZAR TIPOS DE PESQUISA
    print("\n\n2. PADRONIZANDO TIPOS DE PESQUISA")
    print("-" * 40)
    
    # Mapeamento de valores incorretos para corretos
    mapeamentos_tipo = {
        'ambos': 'MRS+MAP',
        'AMBOS': 'MRS+MAP',
        'Ambos': 'MRS+MAP'
    }
    
    for tipo_errado, tipo_correto in mapeamentos_tipo.items():
        cursor.execute("UPDATE visitas SET tipo_pesquisa = ? WHERE tipo_pesquisa = ?", 
                      (tipo_correto, tipo_errado))
        rows_affected = cursor.rowcount
        if rows_affected > 0:
            print(f"   ✅ Corrigido '{tipo_errado}' → '{tipo_correto}' ({rows_affected} registros)")
    
    conn.commit()
    
    # 3. CRIAR CHECKLISTS PARA VISITAS
    print("\n\n3. CRIANDO CHECKLISTS PARA VISITAS")
    print("-" * 40)
    
    # Verificar visitas sem checklist
    cursor.execute("""
        SELECT v.id FROM visitas v
        LEFT JOIN checklists c ON v.id = c.visita_id
        WHERE c.id IS NULL
    """)
    visitas_sem_checklist = cursor.fetchall()
    
    if visitas_sem_checklist:
        print(f"Criando checklists para {len(visitas_sem_checklist)} visitas...")
        
        for (visita_id,) in visitas_sem_checklist:
            cursor.execute("""
                INSERT INTO checklists (visita_id, observacoes_antes, observacoes_durante, observacoes_apos)
                VALUES (?, '', '', '')
            """, (visita_id,))
        
        conn.commit()
        print(f"   ✅ {len(visitas_sem_checklist)} checklists criados")
        problemas_corrigidos.append(f"Criados {len(visitas_sem_checklist)} checklists para visitas existentes")
    else:
        print("   ✅ Todas as visitas já possuem checklist")
    
    # 4. CONFIGURAR QUESTIONÁRIOS OBRIGATÓRIOS
    print("\n\n4. CONFIGURANDO QUESTIONÁRIOS OBRIGATÓRIOS")
    print("-" * 40)
    
    # Verificar se já existem configurações
    cursor.execute("SELECT COUNT(*) FROM questionarios_obrigatorios")
    total_config = cursor.fetchone()[0]
    
    if total_config == 0:
        # Obter resumo das entidades por município
        cursor.execute("""
            SELECT municipio, tipo_entidade,
                   MAX(mrs_obrigatorio) as mrs_obrig,
                   MAX(map_obrigatorio) as map_obrig
            FROM entidades_identificadas
            GROUP BY municipio, tipo_entidade
        """)
        config_necessarias = cursor.fetchall()
        
        if config_necessarias:
            print(f"Criando {len(config_necessarias)} configurações de questionários...")
            
            for municipio, tipo_entidade, mrs_obrig, map_obrig in config_necessarias:
                cursor.execute("""
                    INSERT INTO questionarios_obrigatorios 
                    (municipio, tipo_entidade, mrs_obrigatorio, map_obrigatorio, criado_em, atualizado_em, ativo)
                    VALUES (?, ?, ?, ?, ?, ?, 1)
                """, (municipio, tipo_entidade, bool(mrs_obrig), bool(map_obrig), 
                     datetime.now(), datetime.now()))
            
            conn.commit()
            print(f"   ✅ {len(config_necessarias)} configurações criadas")
            problemas_corrigidos.append(f"Criadas {len(config_necessarias)} configurações de questionários obrigatórios")
    else:
        print(f"   ✅ Já existem {total_config} configurações de questionários")
    
    # 5. ATUALIZAR STATUS DOS QUESTIONÁRIOS NAS ENTIDADES
    print("\n\n5. ATUALIZANDO STATUS DOS QUESTIONÁRIOS")
    print("-" * 40)
    
    # Atualizar status baseado em regras de negócio
    # Definir status inicial como 'pendente' para entidades sem status
    cursor.execute("""
        UPDATE entidades_identificadas
        SET status_mrs = 'pendente'
        WHERE mrs_obrigatorio = 1 AND status_mrs IS NULL
    """)
    mrs_atualizados = cursor.rowcount
    
    cursor.execute("""
        UPDATE entidades_identificadas
        SET status_map = 'pendente'
        WHERE map_obrigatorio = 1 AND status_map IS NULL
    """)
    map_atualizados = cursor.rowcount
    
    if mrs_atualizados > 0 or map_atualizados > 0:
        conn.commit()
        print(f"   ✅ Status atualizados: MRS ({mrs_atualizados}), MAP ({map_atualizados})")
        problemas_corrigidos.append(f"Atualizados status de {mrs_atualizados} MRS e {map_atualizados} MAP")
    else:
        print("   ✅ Todos os status já estão definidos")
    
    # 6. EXECUTAR SCRIPT DE IMPORTAÇÃO DE CONTATOS
    print("\n\n6. IMPORTANDO CONTATOS")
    print("-" * 40)
    
    script_contatos = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/scripts/importar_contatos.py"
    
    if os.path.exists(script_contatos):
        print("Executando script de importação de contatos...")
        try:
            import subprocess
            result = subprocess.run([sys.executable, script_contatos], capture_output=True, text=True)
            if result.returncode == 0:
                print("   ✅ Contatos importados com sucesso!")
                problemas_corrigidos.append("Contatos importados dos arquivos CSV")
            else:
                print(f"   ❌ Erro ao importar contatos: {result.stderr}")
        except Exception as e:
            print(f"   ❌ Erro ao executar script: {str(e)}")
    else:
        print("   ❌ Script de importação não encontrado")
    
    conn.close()
    
    # RESUMO
    print("\n\n" + "=" * 80)
    print("RESUMO DAS CORREÇÕES")
    print("=" * 80)
    
    if problemas_corrigidos:
        print(f"\n✅ {len(problemas_corrigidos)} problemas corrigidos:")
        for i, correcao in enumerate(problemas_corrigidos, 1):
            print(f"   {i}. {correcao}")
    else:
        print("\n✅ Nenhuma correção foi necessária - sistema já estava em ordem!")
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("   1. Reiniciar o servidor Flask para aplicar as mudanças")
    print("   2. Verificar se o mapa de progresso está funcionando corretamente")
    print("   3. Testar a criação de novas visitas e checklists")
    print("   4. Atualizar o status dos questionários conforme forem preenchidos")
    
    print("\n" + "=" * 80)
    print("Correção concluída!")

if __name__ == "__main__":
    corrigir_problemas()