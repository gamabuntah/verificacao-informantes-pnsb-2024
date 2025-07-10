#!/usr/bin/env python3
"""
Script para limpar dados existentes do banco
"""

from sqlalchemy import create_engine, text

def limpar_dados():
    """Limpa todos os dados das tabelas"""
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    engine = create_engine(f'sqlite:///{db_path}')
    
    print("🧹 LIMPEZA DOS DADOS")
    print("=" * 20)
    
    with engine.connect() as conn:
        try:
            # Verificar dados atuais
            result = conn.execute(text("SELECT COUNT(*) FROM visitas"))
            count_visitas = result.fetchone()[0]
            
            result = conn.execute(text("SELECT COUNT(*) FROM checklists"))
            count_checklists = result.fetchone()[0]
            
            print(f"Dados atuais: Visitas={count_visitas}, Checklists={count_checklists}")
            
            if count_visitas > 0 or count_checklists > 0:
                trans = conn.begin()
                try:
                    # Limpar dados
                    conn.execute(text("DELETE FROM checklists"))
                    conn.execute(text("DELETE FROM visitas"))
                    
                    # Tentar resetar auto-increment (pode não existir sqlite_sequence)
                    try:
                        conn.execute(text("DELETE FROM sqlite_sequence WHERE name IN ('visitas', 'checklists')"))
                    except:
                        pass  # sqlite_sequence pode não existir se não houve inserções
                    
                    trans.commit()
                    print("✅ Dados limpos com sucesso")
                    
                except Exception as e:
                    print(f"❌ Erro na limpeza: {e}")
                    trans.rollback()
            else:
                print("✅ Banco já está limpo")
                
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    limpar_dados()
    print("\n🎉 Limpeza concluída!")
    print("💡 Banco pronto para novos dados")