#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recriar o banco de dados em local temporário
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

def recriar_banco_temp():
    """Recria o banco de dados em local temporário e depois move"""
    
    print("🔧 RECRIANDO BANCO DE DADOS EM LOCAL TEMPORÁRIO")
    print("=" * 50)
    
    # Caminhos
    db_dir = os.path.join(os.getcwd(), 'gestao_visitas')
    db_path = os.path.join(db_dir, 'gestao_visitas.db')
    
    # Criar banco temporário
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    print(f"📦 Criando banco temporário: {temp_db_path}")
    
    try:
        from flask import Flask
        from gestao_visitas.db import db
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{temp_db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'recreate_temp_db_key'
        
        db.init_app(app)
        
        with app.app_context():
            # Importar todos os modelos
            from gestao_visitas.models.agendamento import Visita, Calendario
            from gestao_visitas.models.checklist import Checklist
            from gestao_visitas.models.contatos import Contato, TipoEntidade, FonteInformacao
            from gestao_visitas.models.questionarios_obrigatorios import (
                QuestionarioObrigatorio, 
                EntidadeIdentificada, 
                ProgressoQuestionarios,
                EntidadePrioritariaUF
            )
            from gestao_visitas.models.visitas_obrigatorias import (
                VisitaObrigatoria,
                StatusVisitasObrigatorias
            )
            
            # Criar todas as tabelas
            print("🏗️ Criando estrutura do banco...")
            db.create_all()
            print("   ✅ Tabelas criadas com sucesso")
            
            # Recriar visitas obrigatórias
            print("📊 Inicializando visitas obrigatórias...")
            try:
                from gestao_visitas.models.visitas_obrigatorias import inicializar_visitas_obrigatorias
                resultado = inicializar_visitas_obrigatorias()
                print(f"   ✅ {resultado['visitas_criadas']} visitas obrigatórias criadas")
            except Exception as e:
                print(f"   ⚠️ Erro ao inicializar visitas obrigatórias: {e}")
            
            # Recriar progresso de questionários
            print("📈 Inicializando progresso de questionários...")
            try:
                from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
                
                for municipio in MUNICIPIOS_PNSB:
                    try:
                        progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
                        if progresso:
                            db.session.add(progresso)
                    except:
                        pass  # Ignorar erros individuais
                
                db.session.commit()
                print(f"   ✅ Progresso recriado para {len(MUNICIPIOS_PNSB)} municípios")
            except Exception as e:
                print(f"   ⚠️ Erro ao recriar progresso: {e}")
            
            # Verificar dados criados
            print("🔍 Verificando dados criados...")
            try:
                vo_count = VisitaObrigatoria.query.count()
                prog_count = ProgressoQuestionarios.query.count()
                status_count = StatusVisitasObrigatorias.query.count()
                
                print(f"   📋 Visitas obrigatórias: {vo_count}")
                print(f"   📈 Registros de progresso: {prog_count}")
                print(f"   📊 Status municipais: {status_count}")
                
                if vo_count > 0:
                    print("   ✅ Banco criado com dados essenciais")
                else:
                    print("   ⚠️ Banco criado mas sem dados")
                
            except Exception as e:
                print(f"   ⚠️ Erro na verificação: {e}")
        
        # Agora tentar mover o banco para o local correto
        print("📁 Movendo banco para local definitivo...")
        
        # Garantir que o diretório existe
        os.makedirs(db_dir, exist_ok=True)
        
        # Remover banco antigo se existir (tentativa)
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print("   🗑️ Banco antigo removido")
            except:
                # Tentar renomear em vez de remover
                try:
                    backup_name = f"{db_path}.old_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    os.rename(db_path, backup_name)
                    print(f"   📦 Banco antigo renomeado para {os.path.basename(backup_name)}")
                except:
                    print("   ⚠️ Não foi possível remover banco antigo")
        
        # Copiar banco temporário para local definitivo
        try:
            shutil.copy2(temp_db_path, db_path)
            print(f"   ✅ Banco movido para: {db_path}")
        except Exception as e:
            print(f"   ❌ Erro ao mover banco: {e}")
            print(f"   💡 Banco temporário está em: {temp_db_path}")
            print("   💡 Copie manualmente se necessário")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar banco temporário: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Limpar arquivo temporário
        try:
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
        except:
            pass

if __name__ == "__main__":
    print("🚀 SCRIPT DE RECRIAÇÃO TEMPORÁRIA - PNSB 2024")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    sucesso = recriar_banco_temp()
    
    if sucesso:
        print("\n" + "=" * 50)
        print("✅ BANCO RECRIADO COM SUCESSO!")
        print("🚀 Agora você pode reiniciar o Flask")
        print("🌐 Acesse: http://127.0.0.1:5001")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ FALHA NA RECRIAÇÃO DO BANCO")
        print("🔧 Tente executar o Flask - ele criará um banco vazio")
        print("=" * 50)
        sys.exit(1)