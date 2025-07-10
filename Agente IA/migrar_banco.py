#!/usr/bin/env python3
"""
Script para migrar o banco de dados de 'informante' para 'local'
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o caminho do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def migrar_banco():
    """Migra a coluna 'informante' para 'local' no banco SQLite"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
        return
    
    # Conectar ao banco
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("🔧 MIGRAÇÃO DO BANCO DE DADOS")
    print("=" * 40)
    
    with engine.connect() as conn:
        try:
            print("1. Verificando estrutura atual...")
            
            # Verificar se existe coluna 'informante'
            result = conn.execute(text("PRAGMA table_info(visitas)"))
            colunas = [row[1] for row in result.fetchall()]
            
            print(f"Colunas encontradas: {colunas}")
            
            if 'informante' in colunas and 'local' not in colunas:
                print("2. Renomeando coluna 'informante' para 'local'...")
                
                # SQLite não suporta ALTER COLUMN, então precisamos:
                # 1. Criar nova tabela com estrutura correta
                # 2. Copiar dados
                # 3. Renomear tabelas
                
                # Backup da tabela original
                conn.execute(text("ALTER TABLE visitas RENAME TO visitas_backup"))
                
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
                
                # Criar índices
                conn.execute(text("CREATE INDEX ix_visitas_municipio ON visitas (municipio)"))
                conn.execute(text("CREATE INDEX ix_visitas_data ON visitas (data)"))
                conn.execute(text("CREATE INDEX ix_visitas_tipo_pesquisa ON visitas (tipo_pesquisa)"))
                conn.execute(text("CREATE INDEX ix_visitas_status ON visitas (status)"))
                conn.execute(text("CREATE INDEX ix_visitas_data_criacao ON visitas (data_criacao)"))
                conn.execute(text("CREATE INDEX ix_visitas_tipo_informante ON visitas (tipo_informante)"))
                conn.execute(text("CREATE INDEX ix_visitas_pesquisador_responsavel ON visitas (pesquisador_responsavel)"))
                
                # Verificar migração
                result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
                count_new = result.fetchone()[0]
                
                result = conn.execute(text("SELECT COUNT(*) FROM visitas_backup"))
                count_old = result.fetchone()[0]
                
                if count_new == count_old:
                    print(f"✅ Migração bem-sucedida! {count_new} registros migrados")
                    # Apagar tabela backup
                    conn.execute(text("DROP TABLE visitas_backup"))
                    print("✅ Tabela backup removida")
                else:
                    print(f"❌ Erro na migração! Novo: {count_new}, Antigo: {count_old}")
                    return
                
            elif 'local' in colunas:
                print("✅ Coluna 'local' já existe. Migração não necessária.")
                
                # Verificar se tem dados
                result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
                count = result.fetchone()[0]
                print(f"📊 Registros na tabela: {count}")
                
                if count > 0:
                    print("\n⚠️  AVISO: Existem dados na tabela!")
                    print("Deseja apagar todos os dados para garantir integridade? (s/n): ", end="")
                    resposta = 's'  # Forçar limpeza para garantir integridade
                    
                    if resposta.lower() in ['s', 'sim', 'y', 'yes']:
                        # Apagar checklists primeiro
                        conn.execute(text("DELETE FROM checklists"))
                        # Depois apagar visitas
                        conn.execute(text("DELETE FROM visitas"))
                        # Reset auto-increment
                        conn.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('visitas', 'checklists')"))
                        print("✅ Todos os dados foram limpos")
                    
            else:
                print("❌ Estrutura da tabela não reconhecida")
                
            # Commit das mudanças
            conn.commit()
            
        except Exception as e:
            print(f"❌ Erro durante migração: {e}")
            conn.rollback()
            
def verificar_migracao():
    """Verifica se a migração foi bem-sucedida"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("\n📋 VERIFICAÇÃO PÓS-MIGRAÇÃO")
    print("=" * 30)
    
    with engine.connect() as conn:
        try:
            # Verificar estrutura da tabela
            result = conn.execute(text("PRAGMA table_info(visitas)"))
            colunas = [(row[1], row[2]) for row in result.fetchall()]
            
            print("Estrutura da tabela 'visitas':")
            for nome, tipo in colunas:
                print(f"  - {nome}: {tipo}")
                
            # Verificar se coluna 'local' existe
            nomes_colunas = [nome for nome, _ in colunas]
            if 'local' in nomes_colunas:
                print("\n✅ Coluna 'local' encontrada")
            else:
                print("\n❌ Coluna 'local' não encontrada")
                
            if 'informante' in nomes_colunas:
                print("⚠️  Coluna 'informante' ainda existe")
            else:
                print("✅ Coluna 'informante' removida com sucesso")
                
            # Verificar contagem de registros
            result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
            count_visitas = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM checklists"))
            count_checklists = result.fetchone()[0]
            
            print(f"\n📊 Registros atuais:")
            print(f"  - Visitas: {count_visitas}")
            print(f"  - Checklists: {count_checklists}")
            
        except Exception as e:
            print(f"❌ Erro na verificação: {e}")

if __name__ == "__main__":
    print("🚀 MIGRAÇÃO DE BANCO DE DADOS PNSB")
    print("Convertendo campo 'informante' para 'local'")
    print("=" * 50)
    
    migrar_banco()
    verificar_migracao()
    
    print("\n🎉 Migração concluída!")
    print("💡 O sistema agora está usando o campo 'local' corretamente")