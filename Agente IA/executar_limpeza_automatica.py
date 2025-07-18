#!/usr/bin/env python3
"""
Execução automática da limpeza de duplicatas (versão não-interativa)
"""

import sqlite3
from datetime import datetime

def executar_limpeza():
    """Executa a limpeza automaticamente baseada na análise prévia"""
    
    print("🚀 EXECUTANDO LIMPEZA AUTOMÁTICA DE DUPLICATAS")
    print("=" * 60)
    
    # IDs para remoção (baseado na análise prévia)
    ids_para_remover = [18, 15, 14, 17, 19]  # IDs das entidades problemáticas
    
    # Criar backup
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_path = "gestao_visitas/gestao_visitas.db"
    backup_path = f"gestao_visitas/gestao_visitas_backup_pre_limpeza_{timestamp}.db"
    
    with open(db_path, 'rb') as original:
        with open(backup_path, 'wb') as backup:
            backup.write(original.read())
    
    print(f"✅ Backup criado: {backup_path}")
    
    # Conectar e executar
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        conn.execute("BEGIN TRANSACTION")
        
        # Buscar detalhes das entidades antes da remoção
        placeholders = ','.join(['?' for _ in ids_para_remover])
        cursor.execute(f"""
            SELECT id, municipio, nome_entidade 
            FROM entidades_identificadas 
            WHERE id IN ({placeholders})
        """, ids_para_remover)
        
        entities_to_remove = cursor.fetchall()
        
        print("🗑️ REMOVENDO ENTIDADES:")
        for entity in entities_to_remove:
            entity_id, municipio, nome = entity
            cursor.execute("DELETE FROM entidades_identificadas WHERE id = ?", (entity_id,))
            print(f"   ✅ Removido ID:{entity_id} - {nome} ({municipio})")
        
        conn.commit()
        
        # Verificar resultado final
        cursor.execute("SELECT COUNT(*) FROM entidades_identificadas WHERE nome_entidade LIKE '%refeitura%'")
        final_count = cursor.fetchone()[0]
        
        print(f"\n🎉 LIMPEZA CONCLUÍDA COM SUCESSO!")
        print(f"   🗑️ Entidades removidas: {len(entities_to_remove)}")
        print(f"   🏛️ Total de prefeituras restantes: {final_count}")
        
        # Verificar por município
        cursor.execute("""
            SELECT municipio, COUNT(*) as count, GROUP_CONCAT(nome_entidade, ' | ') as nomes
            FROM entidades_identificadas 
            WHERE nome_entidade LIKE '%refeitura%'
            GROUP BY municipio
            ORDER BY municipio
        """)
        
        municipios_result = cursor.fetchall()
        
        print(f"\n📊 SITUAÇÃO POR MUNICÍPIO:")
        for muni_data in municipios_result:
            municipio, count, nomes = muni_data
            status_icon = "⚠️" if count > 1 else "✅"
            print(f"   {status_icon} {municipio}: {count} entidade(s)")
            if count > 1:
                print(f"      {nomes}")
        
        print(f"\n✅ CORREÇÃO DO CÓDIGO TAMBÉM APLICADA!")
        print(f"   A função garantir_prefeitura_completa() foi corrigida")
        print(f"   para prevenir duplicatas futuras.")
        
    except Exception as e:
        conn.rollback()
        print(f"❌ ERRO durante a limpeza: {e}")
        print(f"💾 Backup disponível em: {backup_path}")
    
    finally:
        conn.close()

if __name__ == '__main__':
    executar_limpeza()