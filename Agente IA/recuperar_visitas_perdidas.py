#!/usr/bin/env python3
"""
RECUPERAÇÃO DE VISITAS PERDIDAS - SISTEMA PNSB
==============================================

Este script recupera visitas que podem ter sido perdidas durante mudanças no banco.
"""

import sqlite3
import json
import os
from datetime import datetime
from pathlib import Path

def verificar_situacao_atual():
    """Verifica a situação atual do banco de dados."""
    print("🔍 VERIFICANDO SITUAÇÃO ATUAL...")
    print("=" * 50)
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados principal não encontrado")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    table_names = [t[0] for t in tables]
    
    print("📋 Tabelas encontradas:")
    for table in table_names:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"   {table}: {count} registros")
    
    conn.close()
    return True

def recuperar_de_backup():
    """Recupera visitas dos backups disponíveis."""
    print("\n🔄 RECUPERANDO DADOS DE BACKUP...")
    print("=" * 50)
    
    visitas_recuperadas = []
    
    # 1. Verificar backup JSON
    json_backup = 'gestao_visitas/backups/data_export_20250630_233728.json'
    if os.path.exists(json_backup):
        print("📄 Verificando backup JSON...")
        with open(json_backup, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        
        # Verificar visitas no backup
        if 'data' in backup_data and 'visitas_backup' in backup_data['data']:
            backup_visitas = backup_data['data']['visitas_backup']['rows']
            print(f"   Encontradas {len(backup_visitas)} visitas no backup JSON")
            
            for visita in backup_visitas:
                print(f"   📅 {visita['data']} - {visita['municipio']} - {visita['status']}")
                visitas_recuperadas.extend(backup_visitas)
    
    # 2. Verificar backup DB
    db_backup = 'gestao_visitas/backups/backup_20250630_233728.db'
    if os.path.exists(db_backup):
        print("🗄️ Verificando backup do banco...")
        conn = sqlite3.connect(db_backup)
        cursor = conn.cursor()
        
        # Verificar tabela visitas_backup
        try:
            cursor.execute('SELECT * FROM visitas_backup')
            backup_visitas_db = cursor.fetchall()
            
            # Obter nomes das colunas
            cursor.execute('PRAGMA table_info(visitas_backup)')
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"   Encontradas {len(backup_visitas_db)} visitas no backup DB")
            
            for visita_row in backup_visitas_db:
                visita_dict = dict(zip(columns, visita_row))
                print(f"   📅 {visita_dict['data']} - {visita_dict['municipio']} - {visita_dict['status']}")
                
        except Exception as e:
            print(f"   ⚠️ Erro ao acessar backup DB: {e}")
        
        conn.close()
    
    # 3. Verificar tabela visitas_backup no banco atual
    print("🔍 Verificando tabela visitas_backup no banco atual...")
    conn = sqlite3.connect('gestao_visitas/gestao_visitas.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM visitas_backup')
        backup_atual = cursor.fetchall()
        
        if backup_atual:
            cursor.execute('PRAGMA table_info(visitas_backup)')
            columns = [col[1] for col in cursor.fetchall()]
            
            print(f"   Encontradas {len(backup_atual)} visitas na tabela backup atual")
            
            for visita_row in backup_atual:
                visita_dict = dict(zip(columns, visita_row))
                print(f"   📅 {visita_dict['data']} - {visita_dict['municipio']} - {visita_dict['status']}")
        else:
            print("   Nenhuma visita na tabela backup atual")
            
    except Exception as e:
        print(f"   ⚠️ Erro ao acessar tabela backup: {e}")
    
    conn.close()
    
    return visitas_recuperadas

def restaurar_visitas():
    """Restaura visitas da tabela backup para a tabela principal."""
    print("\n⚡ RESTAURANDO VISITAS...")
    print("=" * 50)
    
    conn = sqlite3.connect('gestao_visitas/gestao_visitas.db')
    cursor = conn.cursor()
    
    try:
        # Verificar se há visitas no backup
        cursor.execute('SELECT COUNT(*) FROM visitas_backup')
        backup_count = cursor.fetchone()[0]
        
        if backup_count == 0:
            print("❌ Nenhuma visita encontrada na tabela backup")
            return False
        
        print(f"📦 Encontradas {backup_count} visitas na tabela backup")
        
        # Obter estrutura das tabelas
        cursor.execute('PRAGMA table_info(visitas_backup)')
        backup_columns = [col[1] for col in cursor.fetchall()]
        
        cursor.execute('PRAGMA table_info(visitas)')
        main_columns = [col[1] for col in cursor.fetchall()]
        
        print("📋 Estrutura das tabelas:")
        print(f"   Backup: {backup_columns}")
        print(f"   Principal: {main_columns}")
        
        # Mapear colunas compatíveis
        common_columns = [col for col in backup_columns if col in main_columns]
        if 'informante' in backup_columns and 'local' in main_columns:
            # Mapear 'informante' para 'local'
            common_columns = [col if col != 'informante' else 'local' for col in common_columns if col != 'informante']
            common_columns.append('local')
        
        print(f"   Colunas compatíveis: {common_columns}")
        
        # Buscar visitas do backup
        cursor.execute('SELECT * FROM visitas_backup')
        backup_visitas = cursor.fetchall()
        backup_col_dict = {col: idx for idx, col in enumerate(backup_columns)}
        
        # Inserir visitas na tabela principal
        visitas_inseridas = 0
        
        for visita_row in backup_visitas:
            try:
                # Verificar se a visita já existe
                municipio = visita_row[backup_col_dict['municipio']]
                data = visita_row[backup_col_dict['data']]
                
                cursor.execute('SELECT COUNT(*) FROM visitas WHERE municipio = ? AND data = ?', 
                             (municipio, data))
                existe = cursor.fetchone()[0] > 0
                
                if not existe:
                    # Preparar dados para inserção
                    valores = []
                    colunas_insert = []
                    
                    for col in main_columns:
                        if col == 'id':
                            continue  # Auto increment
                        elif col == 'local' and 'informante' in backup_col_dict:
                            # Mapear informante para local
                            valores.append(visita_row[backup_col_dict['informante']])
                            colunas_insert.append(col)
                        elif col in backup_col_dict:
                            valores.append(visita_row[backup_col_dict[col]])
                            colunas_insert.append(col)
                        else:
                            # Valor padrão para colunas não encontradas
                            if col == 'data_criacao':
                                valores.append(datetime.now().isoformat())
                            elif col == 'data_atualizacao':
                                valores.append(datetime.now().isoformat())
                            else:
                                valores.append(None)
                            colunas_insert.append(col)
                    
                    # Inserir visita
                    placeholders = ', '.join(['?' for _ in valores])
                    cols_str = ', '.join(colunas_insert)
                    
                    query = f'INSERT INTO visitas ({cols_str}) VALUES ({placeholders})'
                    cursor.execute(query, valores)
                    
                    visitas_inseridas += 1
                    print(f"   ✅ Restaurada: {municipio} - {data}")
                else:
                    print(f"   ⏭️ Já existe: {municipio} - {data}")
                    
            except Exception as e:
                print(f"   ❌ Erro ao restaurar visita: {e}")
        
        # Commit das mudanças
        conn.commit()
        print(f"\n🎉 SUCESSO: {visitas_inseridas} visitas restauradas!")
        
        return visitas_inseridas > 0
        
    except Exception as e:
        print(f"❌ Erro durante restauração: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def verificar_resultado():
    """Verifica o resultado final após restauração."""
    print("\n📊 VERIFICANDO RESULTADO FINAL...")
    print("=" * 50)
    
    conn = sqlite3.connect('gestao_visitas/gestao_visitas.db')
    cursor = conn.cursor()
    
    # Contar visitas atuais
    cursor.execute('SELECT COUNT(*) FROM visitas')
    total_visitas = cursor.fetchone()[0]
    
    print(f"📈 TOTAL DE VISITAS ATUAL: {total_visitas}")
    
    if total_visitas > 0:
        cursor.execute('SELECT municipio, data, status FROM visitas ORDER BY data DESC')
        visitas = cursor.fetchall()
        
        print("📋 TODAS AS VISITAS:")
        for i, (municipio, data, status) in enumerate(visitas, 1):
            print(f"   {i}. {municipio} - {data} - {status}")
    
    conn.close()

def main():
    print("=" * 60)
    print("🔄 RECUPERAÇÃO DE VISITAS PERDIDAS - SISTEMA PNSB")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        return
    
    # 1. Verificar situação atual
    if not verificar_situacao_atual():
        return
    
    # 2. Recuperar de backups
    recuperar_de_backup()
    
    # 3. Tentar restaurar visitas
    sucesso = restaurar_visitas()
    
    # 4. Verificar resultado final
    verificar_resultado()
    
    print("\n" + "=" * 60)
    if sucesso:
        print("🎉 RECUPERAÇÃO CONCLUÍDA COM SUCESSO!")
        print("   Acesse http://localhost:8080/visitas para verificar")
    else:
        print("⚠️ RECUPERAÇÃO PARCIAL OU SEM DADOS PARA RECUPERAR")
        print("   Pode ser que as visitas já estejam na tabela principal")
    print("=" * 60)

if __name__ == "__main__":
    main()