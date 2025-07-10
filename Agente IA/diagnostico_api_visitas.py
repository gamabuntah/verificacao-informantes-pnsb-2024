#!/usr/bin/env python3
"""
DIAGNÓSTICO DA API DE VISITAS - SISTEMA PNSB
===========================================

Este script diagnostica problemas na API /api/visitas.
"""

import os
import sys
import sqlite3
from pathlib import Path

def verificar_banco_diretamente():
    """Verifica os dados diretamente no banco SQLite."""
    print("🔍 VERIFICANDO BANCO DE DADOS DIRETAMENTE...")
    print("=" * 50)
    
    db_path = 'gestao_visitas/gestao_visitas.db'
    
    if not os.path.exists(db_path):
        print("❌ Banco de dados não encontrado")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar estrutura da tabela visitas
    cursor.execute('PRAGMA table_info(visitas)')
    columns = cursor.fetchall()
    
    print("📋 ESTRUTURA DA TABELA VISITAS:")
    for col in columns:
        print(f"   {col[1]} ({col[2]}) - Null: {col[3]} - Default: {col[4]}")
    
    # Verificar dados na tabela
    cursor.execute('SELECT COUNT(*) FROM visitas')
    count = cursor.fetchone()[0]
    print(f"\n📊 TOTAL DE VISITAS: {count}")
    
    if count > 0:
        cursor.execute('SELECT * FROM visitas')
        visitas = cursor.fetchall()
        
        print("\n📋 DADOS DAS VISITAS:")
        col_names = [col[1] for col in columns]
        
        for i, visita in enumerate(visitas, 1):
            print(f"\n   VISITA {i}:")
            for j, value in enumerate(visita):
                print(f"     {col_names[j]}: {value}")
    
    conn.close()
    return count > 0

def testar_modelo_sqlalchemy():
    """Testa o modelo SQLAlchemy diretamente."""
    print("\n🔬 TESTANDO MODELO SQLALCHEMY...")
    print("=" * 50)
    
    try:
        # Importar o contexto do Flask
        sys.path.append('.')
        from app import app, db
        from gestao_visitas.models.agendamento import Visita
        
        with app.app_context():
            # Buscar visitas usando SQLAlchemy
            print("📊 Buscando visitas com SQLAlchemy...")
            visitas = Visita.query.all()
            print(f"   Encontradas: {len(visitas)} visitas")
            
            for i, visita in enumerate(visitas, 1):
                print(f"\n   VISITA {i}:")
                print(f"     ID: {visita.id}")
                print(f"     Município: {visita.municipio}")
                print(f"     Data: {visita.data}")
                print(f"     Status: {visita.status}")
                
                # Testar método to_dict()
                try:
                    visita_dict = visita.to_dict()
                    print(f"     to_dict() funcionou: ✅")
                    print(f"     Chaves: {list(visita_dict.keys())}")
                except Exception as e:
                    print(f"     to_dict() falhou: ❌ {e}")
                    import traceback
                    traceback.print_exc()
            
            return len(visitas) > 0
            
    except Exception as e:
        print(f"❌ Erro ao testar modelo: {e}")
        import traceback
        traceback.print_exc()
        return False

def testar_api_localmente():
    """Testa a API localmente sem fazer requisição HTTP."""
    print("\n🌐 TESTANDO LÓGICA DA API LOCALMENTE...")
    print("=" * 50)
    
    try:
        sys.path.append('.')
        from app import app, db
        from gestao_visitas.models.agendamento import Visita
        
        with app.app_context():
            # Simular a lógica da API
            print("📊 Simulando GET /api/visitas...")
            
            try:
                visitas = Visita.query.order_by(Visita.data.asc(), Visita.hora_inicio.asc()).all()
                print(f'   Qtd visitas encontradas: {len(visitas)}')
                
                visitas_dict = []
                for v in visitas:
                    try:
                        visita_dict = v.to_dict()
                        visitas_dict.append(visita_dict)
                        print(f'   ✅ Visita {v.id} convertida com sucesso')
                    except Exception as e:
                        print(f'   ❌ Erro ao converter visita {getattr(v, "id", None)}: {e}')
                        import traceback
                        traceback.print_exc()
                
                print(f"\n📋 RESULTADO FINAL:")
                print(f"   Total processadas: {len(visitas_dict)}")
                
                if visitas_dict:
                    print(f"   Primeira visita: {visitas_dict[0]}")
                
                return len(visitas_dict) > 0
                
            except Exception as e:
                print(f"❌ Erro na lógica da API: {e}")
                import traceback
                traceback.print_exc()
                return False
                
    except Exception as e:
        print(f"❌ Erro ao testar API: {e}")
        import traceback
        traceback.print_exc()
        return False

def verificar_checklist():
    """Verifica se há problema com checklists."""
    print("\n✅ VERIFICANDO CHECKLISTS...")
    print("=" * 50)
    
    try:
        sys.path.append('.')
        from app import app, db
        from gestao_visitas.models.checklist import Checklist
        
        with app.app_context():
            checklists = Checklist.query.all()
            print(f"📊 Checklists encontrados: {len(checklists)}")
            
            for checklist in checklists:
                print(f"   Checklist ID: {checklist.id}, Visita ID: {checklist.visita_id}")
                
                try:
                    checklist_dict = checklist.to_dict()
                    print(f"   ✅ Checklist to_dict() funcionou")
                except Exception as e:
                    print(f"   ❌ Erro no checklist to_dict(): {e}")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro ao verificar checklists: {e}")
        return False

def main():
    print("=" * 60)
    print("🔍 DIAGNÓSTICO DA API DE VISITAS - SISTEMA PNSB")
    print("=" * 60)
    
    # Verificar se estamos no diretório correto
    if not Path("app.py").exists():
        print("❌ ERRO: Execute este script no diretório do projeto")
        print("   cd 'Verificação Informantes PNSB/Agente IA'")
        return
    
    # 1. Verificar banco diretamente
    banco_ok = verificar_banco_diretamente()
    
    # 2. Verificar checklists
    checklist_ok = verificar_checklist()
    
    # 3. Testar modelo SQLAlchemy
    modelo_ok = testar_modelo_sqlalchemy()
    
    # 4. Testar lógica da API
    api_ok = testar_api_localmente()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO DO DIAGNÓSTICO")
    print("=" * 60)
    print(f"🗄️ Banco de dados: {'✅ OK' if banco_ok else '❌ PROBLEMA'}")
    print(f"✅ Checklists: {'✅ OK' if checklist_ok else '❌ PROBLEMA'}")
    print(f"🔬 Modelo SQLAlchemy: {'✅ OK' if modelo_ok else '❌ PROBLEMA'}")
    print(f"🌐 Lógica da API: {'✅ OK' if api_ok else '❌ PROBLEMA'}")
    
    if all([banco_ok, modelo_ok, api_ok]):
        print("\n🎉 TUDO FUNCIONANDO! O problema pode ser:")
        print("   • Sistema não está rodando")
        print("   • Problema de cache do navegador")
        print("   • Erro de JavaScript no frontend")
    else:
        print("\n⚠️ PROBLEMAS IDENTIFICADOS!")
        print("   Verifique os erros acima para identificar a causa")
    
    print("=" * 60)

if __name__ == "__main__":
    main()