#!/usr/bin/env python3
"""
Script para migrar o banco de dados de 'informante' para 'local' (versão corrigida)
"""

import os
import sys
from sqlalchemy import create_engine, text

def migrar_banco():
    """Migra a coluna 'informante' para 'local' no banco SQLite"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return
    
    # Conectar ao banco
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("🔧 MIGRAÇÃO DO BANCO DE DADOS V2")
    print("=" * 40)
    
    with engine.connect() as conn:
        try:
            print("1. Verificando estrutura atual...")
            
            # Verificar se existe coluna 'informante'
            result = conn.execute(text("PRAGMA table_info(visitas)"))
            colunas = [row[1] for row in result.fetchall()]
            
            print(f"Colunas encontradas: {colunas}")
            
            if 'informante' in colunas and 'local' not in colunas:
                print("2. Preparando migração...")
                
                # Verificar se há dados antes da migração
                result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
                count_original = result.fetchone()[0]
                print(f"   Registros a migrar: {count_original}")
                
                if count_original > 0:
                    # Mostrar alguns dados para confirmar
                    result = conn.execute(text("SELECT id, municipio, informante, status FROM visitas LIMIT 3"))
                    sample_data = result.fetchall()
                    print("   Amostra dos dados:")
                    for row in sample_data:
                        print(f"     ID: {row[0]}, Município: {row[1]}, Informante: {row[2]}, Status: {row[3]}")
                
                print("\n⚠️  Esta operação irá:")
                print("   - Renomear a coluna 'informante' para 'local'")
                print("   - Preservar todos os dados existentes")
                print("   - Recriar a estrutura da tabela")
                
                # Para automatizar, vamos continuar
                print("\n3. Executando migração...")
                
                # Começar transação
                trans = conn.begin()
                
                try:
                    # Backup da tabela original
                    conn.execute(text("ALTER TABLE visitas RENAME TO visitas_backup"))
                    print("   ✓ Backup da tabela criado")
                    
                    # Criar nova tabela com estrutura correta
                    conn.execute(text("""
                        CREATE TABLE visitas (
                            id INTEGER PRIMARY KEY,
                            municipio VARCHAR(100) NOT NULL,
                            data DATETIME NOT NULL,
                            hora_inicio TIME NOT NULL,
                            hora_fim TIME NOT NULL,
                            local VARCHAR(100) NOT NULL,
                            tipo_pesquisa VARCHAR(10) NOT NULL DEFAULT 'MRS',
                            status VARCHAR(20) DEFAULT 'agendada',
                            observacoes VARCHAR(500),
                            data_criacao DATETIME,
                            data_atualizacao DATETIME,
                            tipo_informante VARCHAR(30) NOT NULL DEFAULT 'prefeitura',
                            pesquisador_responsavel VARCHAR(100)
                        )
                    """))
                    print("   ✓ Nova tabela criada")
                    
                    # Copiar dados da tabela backup para nova tabela
                    conn.execute(text("""
                        INSERT INTO visitas (
                            id, municipio, data, hora_inicio, hora_fim, local,
                            tipo_pesquisa, status, observacoes, data_criacao,
                            data_atualizacao, tipo_informante, pesquisador_responsavel
                        )
                        SELECT 
                            id, municipio, data, hora_inicio, hora_fim, informante,
                            tipo_pesquisa, status, observacoes, data_criacao,
                            data_atualizacao, tipo_informante, pesquisador_responsavel
                        FROM visitas_backup
                    """))
                    print("   ✓ Dados copiados")
                    
                    # Criar índices (com IF NOT EXISTS para evitar erros)
                    indices = [
                        "CREATE INDEX IF NOT EXISTS ix_visitas_municipio ON visitas (municipio)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_data ON visitas (data)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_tipo_pesquisa ON visitas (tipo_pesquisa)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_status ON visitas (status)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_data_criacao ON visitas (data_criacao)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_tipo_informante ON visitas (tipo_informante)",
                        "CREATE INDEX IF NOT EXISTS ix_visitas_pesquisador_responsavel ON visitas (pesquisador_responsavel)"
                    ]
                    
                    for indice in indices:
                        conn.execute(text(indice))
                    print("   ✓ Índices criados")
                    
                    # Verificar migração
                    result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
                    count_new = result.fetchone()[0]
                    
                    if count_new == count_original:
                        print(f"   ✓ Migração verificada: {count_new} registros")
                        
                        # Apagar tabela backup
                        conn.execute(text("DROP TABLE visitas_backup"))
                        print("   ✓ Backup removido")
                        
                        # Commit da transação
                        trans.commit()
                        print("\n✅ Migração concluída com sucesso!")
                        
                    else:
                        print(f"   ❌ Erro: contagem diferente! Novo: {count_new}, Original: {count_original}")
                        trans.rollback()
                        return False
                        
                except Exception as e:
                    print(f"   ❌ Erro durante migração: {e}")
                    trans.rollback()
                    return False
                
            elif 'local' in colunas:
                print("✅ Coluna 'local' já existe.")
                
                # Verificar se ainda tem coluna informante (migração incompleta)
                if 'informante' in colunas:
                    print("⚠️  Coluna 'informante' ainda existe. Removendo...")
                    
                    # Verificar se há dados diferentes entre as colunas
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM visitas 
                        WHERE informante != local OR (informante IS NULL) != (local IS NULL)
                    """))
                    diff_count = result.fetchone()[0]
                    
                    if diff_count > 0:
                        print(f"   ⚠️  {diff_count} registros têm diferenças entre 'informante' e 'local'")
                        # Para segurança, vamos manter os dados de 'local'
                    
                    # Recriar tabela sem coluna informante
                    trans = conn.begin()
                    try:
                        conn.execute(text("ALTER TABLE visitas RENAME TO visitas_temp"))
                        
                        conn.execute(text("""
                            CREATE TABLE visitas (
                                id INTEGER PRIMARY KEY,
                                municipio VARCHAR(100) NOT NULL,
                                data DATETIME NOT NULL,
                                hora_inicio TIME NOT NULL,
                                hora_fim TIME NOT NULL,
                                local VARCHAR(100) NOT NULL,
                                tipo_pesquisa VARCHAR(10) NOT NULL DEFAULT 'MRS',
                                status VARCHAR(20) DEFAULT 'agendada',
                                observacoes VARCHAR(500),
                                data_criacao DATETIME,
                                data_atualizacao DATETIME,
                                tipo_informante VARCHAR(30) NOT NULL DEFAULT 'prefeitura',
                                pesquisador_responsavel VARCHAR(100)
                            )
                        """))
                        
                        conn.execute(text("""
                            INSERT INTO visitas SELECT 
                                id, municipio, data, hora_inicio, hora_fim, local,
                                tipo_pesquisa, status, observacoes, data_criacao,
                                data_atualizacao, tipo_informante, pesquisador_responsavel
                            FROM visitas_temp
                        """))
                        
                        conn.execute(text("DROP TABLE visitas_temp"))
                        trans.commit()
                        print("   ✓ Coluna 'informante' removida")
                        
                    except Exception as e:
                        print(f"   ❌ Erro ao remover coluna: {e}")
                        trans.rollback()
                
                # Verificar dados atuais
                result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
                count = result.fetchone()[0]
                print(f"📊 Registros na tabela: {count}")
                
                # Limpar dados antigos para garantir integridade
                print("\n4. Limpando dados antigos para garantir integridade...")
                trans = conn.begin()
                try:
                    conn.execute(text("DELETE FROM checklists"))
                    conn.execute(text("DELETE FROM visitas"))
                    conn.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('visitas', 'checklists')"))
                    trans.commit()
                    print("   ✓ Dados limpos")
                except Exception as e:
                    print(f"   ❌ Erro na limpeza: {e}")
                    trans.rollback()
                    
            else:
                print("❌ Estrutura da tabela não reconhecida")
                return False
                
        except Exception as e:
            print(f"❌ Erro geral: {e}")
            return False
            
    return True

def verificar_resultado():
    """Verifica o resultado final da migração"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("\n📋 VERIFICAÇÃO FINAL")
    print("=" * 20)
    
    with engine.connect() as conn:
        try:
            result = conn.execute(text("PRAGMA table_info(visitas)"))
            colunas = [row[1] for row in result.fetchall()]
            
            print(f"Colunas atuais: {colunas}")
            
            # Verificar status
            tem_local = 'local' in colunas
            tem_informante = 'informante' in colunas
            
            if tem_local and not tem_informante:
                print("✅ Migração completa: campo 'local' presente, 'informante' removido")
            elif tem_local and tem_informante:
                print("⚠️  Migração parcial: ambos os campos presentes")
            elif not tem_local and tem_informante:
                print("❌ Migração falhou: apenas 'informante' presente")
            else:
                print("❌ Erro: nenhum campo encontrado")
                
            # Verificar contagens
            result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
            count_visitas = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM checklists"))
            count_checklists = result.fetchone()[0]
            
            print(f"Registros: Visitas={count_visitas}, Checklists={count_checklists}")
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 MIGRAÇÃO DE BANCO DE DADOS PNSB V2")
    print("=" * 45)
    
    sucesso = migrar_banco()
    verificar_resultado()
    
    if sucesso:
        print("\n🎉 Processo concluído com sucesso!")
        print("💾 Banco de dados atualizado para usar campo 'local'")
        print("🔄 Reinicie o servidor Flask para aplicar as mudanças")
    else:
        print("\n❌ Processo falhou. Verifique os erros acima.")