#!/usr/bin/env python3
"""
Script para limpar todas as visitas do banco de dados e preparar para futuras migrações
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Adicionar o caminho do projeto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar modelos
try:
    from gestao_visitas.models.agendamento import Visita
    from gestao_visitas.models.checklist import Checklist
    from gestao_visitas.db import db
    from app import app
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    sys.exit(1)

def verificar_e_limpar_banco():
    """Verifica o conteúdo atual do banco e limpa todas as visitas"""
    
    with app.app_context():
        print("=== VERIFICAÇÃO DO BANCO DE DADOS ===")
        
        # Verificar visitas existentes
        try:
            visitas = Visita.query.all()
            print(f"Visitas encontradas: {len(visitas)}")
            
            if visitas:
                print("\nVisitas existentes:")
                for i, visita in enumerate(visitas, 1):
                    print(f"{i}. ID: {visita.id}")
                    print(f"   Município: {getattr(visita, 'municipio', 'N/A')}")
                    print(f"   Data: {getattr(visita, 'data', 'N/A')}")
                    # Verificar se tem campo 'informante' ou 'local'
                    if hasattr(visita, 'informante'):
                        print(f"   Informante (campo antigo): {getattr(visita, 'informante', 'N/A')}")
                    if hasattr(visita, 'local'):
                        print(f"   Local (campo novo): {getattr(visita, 'local', 'N/A')}")
                    print(f"   Status: {getattr(visita, 'status', 'N/A')}")
                    print()
        except Exception as e:
            print(f"Erro ao verificar visitas: {e}")
            
        # Verificar checklists existentes
        try:
            checklists = Checklist.query.all()
            print(f"Checklists encontrados: {len(checklists)}")
        except Exception as e:
            print(f"Erro ao verificar checklists: {e}")
            
        print("\n=== LIMPEZA DO BANCO ===")
        
        # Confirmar limpeza
        resposta = input("Deseja apagar TODAS as visitas e checklists? (sim/não): ").lower().strip()
        
        if resposta in ['sim', 's', 'yes', 'y']:
            try:
                # Apagar todos os checklists primeiro (devido à foreign key)
                num_checklists = Checklist.query.count()
                if num_checklists > 0:
                    Checklist.query.delete()
                    print(f"✓ {num_checklists} checklists apagados")
                
                # Apagar todas as visitas
                num_visitas = Visita.query.count()
                if num_visitas > 0:
                    Visita.query.delete()
                    print(f"✓ {num_visitas} visitas apagadas")
                
                # Commit das mudanças
                db.session.commit()
                
                print("\n✅ Banco de dados limpo com sucesso!")
                print("✅ Pronto para futuras alterações de schema sem perda de dados")
                
                # Verificar se limpeza foi efetiva
                visitas_restantes = Visita.query.count()
                checklists_restantes = Checklist.query.count()
                
                print(f"\nVerificação final:")
                print(f"- Visitas restantes: {visitas_restantes}")
                print(f"- Checklists restantes: {checklists_restantes}")
                
            except Exception as e:
                print(f"❌ Erro durante a limpeza: {e}")
                db.session.rollback()
                
        else:
            print("❌ Limpeza cancelada pelo usuário")
            
def resetar_autoincrement():
    """Resetar contadores de auto-incremento das tabelas"""
    
    with app.app_context():
        try:
            # Para SQLite, resetar a sequência
            db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='visitas'"))
            db.session.execute(text("DELETE FROM sqlite_sequence WHERE name='checklists'"))
            db.session.commit()
            print("✓ Contadores de auto-incremento resetados")
        except Exception as e:
            print(f"Aviso: Não foi possível resetar auto-incremento: {e}")

def verificar_schema_atual():
    """Verificar o schema atual das tabelas"""
    
    print("\n=== VERIFICAÇÃO DO SCHEMA ===")
    
    with app.app_context():
        try:
            # Verificar schema da tabela visitas
            engine = db.engine
            inspector = db.inspect(engine)
            
            if 'visitas' in inspector.get_table_names():
                colunas = inspector.get_columns('visitas')
                print("Colunas da tabela 'visitas':")
                for col in colunas:
                    print(f"  - {col['name']}: {col['type']}")
            
            if 'checklists' in inspector.get_table_names():
                colunas = inspector.get_columns('checklists')
                print("\nColunas da tabela 'checklists':")
                for col in colunas:
                    print(f"  - {col['name']}: {col['type']}")
                    
        except Exception as e:
            print(f"Erro ao verificar schema: {e}")

if __name__ == "__main__":
    print("🔧 FERRAMENTA DE LIMPEZA DO BANCO DE DADOS PNSB")
    print("=" * 50)
    
    # Verificar schema atual
    verificar_schema_atual()
    
    # Verificar e limpar dados
    verificar_e_limpar_banco()
    
    # Resetar contadores
    resetar_autoincrement()
    
    print("\n🎉 Processo concluído!")
    print("💡 Agora o sistema está preparado para mudanças de schema futuras")