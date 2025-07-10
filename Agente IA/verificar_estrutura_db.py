#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def verificar_estrutura_db():
    """Verifica a estrutura do banco de dados"""
    
    db_path = "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA/gestao_visitas/gestao_visitas.db"
    
    if not os.path.exists(db_path):
        print(f"Banco de dados não encontrado: {db_path}")
        return
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar todas as tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tabelas = cursor.fetchall()
    
    print(f"Tabelas encontradas no banco:")
    print("-" * 40)
    for tabela in tabelas:
        print(f"• {tabela[0]}")
    
    # Para cada tabela, mostrar estrutura
    for tabela in tabelas:
        nome_tabela = tabela[0]
        print(f"\n📋 Estrutura da tabela: {nome_tabela}")
        print("-" * 40)
        
        # Obter informações das colunas
        cursor.execute(f"PRAGMA table_info({nome_tabela})")
        colunas = cursor.fetchall()
        
        for col in colunas:
            print(f"   {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'}")
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {nome_tabela}")
        count = cursor.fetchone()[0]
        print(f"   → {count} registros")
        
        # Se for uma tabela que pode ter status, mostrar distribuição
        if nome_tabela in ['visita', 'agendamento']:
            try:
                cursor.execute(f"SELECT status, COUNT(*) FROM {nome_tabela} GROUP BY status")
                status_dist = cursor.fetchall()
                if status_dist:
                    print(f"   📊 Distribuição por status:")
                    for status, count in status_dist:
                        print(f"      - {status}: {count}")
            except:
                pass
    
    conn.close()

if __name__ == "__main__":
    verificar_estrutura_db()