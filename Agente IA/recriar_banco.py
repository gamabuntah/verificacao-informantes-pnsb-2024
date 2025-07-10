#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para recriar o banco de dados quando há corrupção
"""

import os
import sys
import shutil
from datetime import datetime

def recriar_banco():
    """Recria o banco de dados do zero"""
    
    print("🔧 RECRIANDO BANCO DE DADOS PNSB 2024")
    print("=" * 50)
    
    # Caminho do banco
    db_path = os.path.join(os.getcwd(), 'gestao_visitas', 'gestao_visitas.db')
    db_backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 1. Fazer backup do banco corrompido
    try:
        if os.path.exists(db_path):
            print(f"📦 Fazendo backup do banco corrompido...")
            shutil.move(db_path, db_backup_path)
            print(f"   ✅ Backup salvo em: {os.path.basename(db_backup_path)}")
    except Exception as e:
        print(f"   ⚠️ Não foi possível fazer backup: {e}")
    
    # 2. Criar novo banco
    print("🏗️ Criando novo banco de dados...")
    
    try:
        from flask import Flask
        from gestao_visitas.db import db
        
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SECRET_KEY'] = 'recreate_db_key'
        
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
            db.create_all()
            print("   ✅ Tabelas criadas com sucesso")
            
            # 3. Repovoar dados essenciais
            print("📊 Repovoando dados essenciais...")
            
            # Recriar visitas obrigatórias
            try:
                from gestao_visitas.models.visitas_obrigatorias import inicializar_visitas_obrigatorias
                resultado = inicializar_visitas_obrigatorias()
                print(f"   ✅ {resultado['visitas_criadas']} visitas obrigatórias criadas")
            except Exception as e:
                print(f"   ⚠️ Erro ao inicializar visitas obrigatórias: {e}")
            
            # Recriar progresso de questionários
            try:
                from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
                from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
                
                for municipio in MUNICIPIOS_PNSB:
                    progresso = ProgressoQuestionarios.calcular_progresso_municipio(municipio)
                    if progresso:
                        db.session.add(progresso)
                
                db.session.commit()
                print(f"   ✅ Progresso de questionários recriado para {len(MUNICIPIOS_PNSB)} municípios")
            except Exception as e:
                print(f"   ⚠️ Erro ao recriar progresso: {e}")
            
            print("🎉 Banco de dados recriado com sucesso!")
            print(f"📁 Localização: {db_path}")
            
            # Verificar dados
            print("\n📊 Verificando dados...")
            try:
                from gestao_visitas.models.visitas_obrigatorias import VisitaObrigatoria
                from gestao_visitas.models.questionarios_obrigatorios import ProgressoQuestionarios
                
                vo_count = VisitaObrigatoria.query.count()
                prog_count = ProgressoQuestionarios.query.count()
                
                print(f"   📋 Visitas obrigatórias: {vo_count}")
                print(f"   📈 Registros de progresso: {prog_count}")
                
            except Exception as e:
                print(f"   ⚠️ Erro na verificação: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao recriar banco: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 SCRIPT DE RECRIAÇÃO DE BANCO - PNSB 2024")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    sucesso = recriar_banco()
    
    if sucesso:
        print("\n" + "=" * 50)
        print("✅ BANCO RECRIADO COM SUCESSO!")
        print("🚀 Agora você pode reiniciar o Flask")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ FALHA NA RECRIAÇÃO DO BANCO")
        print("🔧 Verifique os logs acima")
        print("=" * 50)
        sys.exit(1)