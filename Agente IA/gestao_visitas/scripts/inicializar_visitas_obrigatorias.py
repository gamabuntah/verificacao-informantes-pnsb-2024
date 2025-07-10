#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para Inicializar Sistema de Visitas Obrigatórias
======================================================

Este script configura o sistema completo de controle de visitas obrigatórias:
1. Cria tabelas no banco de dados
2. Inicializa visitas obrigatórias para todas as entidades P1/P2
3. Vincula visitas existentes
4. Calcula status inicial

Execute este script após implementar o sistema de visitas obrigatórias.
"""

import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from gestao_visitas.db import db
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    """Cria app Flask para inicialização"""
    app = Flask(__name__)
    
    # Configuração do banco
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, '..', 'gestao_visitas.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'init_script_key'
    
    db.init_app(app)
    
    return app

def inicializar_sistema_completo():
    """Inicializa todo o sistema de visitas obrigatórias"""
    
    print("=" * 80)
    print("🚀 INICIALIZANDO SISTEMA DE VISITAS OBRIGATÓRIAS - PNSB 2024")
    print("=" * 80)
    
    app = create_app()
    
    with app.app_context():
        
        # ===== PASSO 1: CRIAR TABELAS =====
        print("\n📋 PASSO 1: Criando tabelas do sistema...")
        try:
            # Importar modelos para garantir que tabelas sejam criadas
            from gestao_visitas.models.visitas_obrigatorias import (
                VisitaObrigatoria, 
                StatusVisitasObrigatorias
            )
            from gestao_visitas.models.agendamento import Visita
            from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
            
            # Criar todas as tabelas
            db.create_all()
            print("   ✅ Tabelas criadas com sucesso")
            
        except Exception as e:
            print(f"   ❌ Erro ao criar tabelas: {str(e)}")
            return False
        
        # ===== PASSO 2: INICIALIZAR VISITAS OBRIGATÓRIAS =====
        print("\n🏢 PASSO 2: Inicializando visitas obrigatórias...")
        try:
            from gestao_visitas.models.visitas_obrigatorias import inicializar_visitas_obrigatorias
            
            resultado = inicializar_visitas_obrigatorias()
            
            print(f"   ✅ {resultado['visitas_criadas']} visitas obrigatórias criadas")
            print(f"   ✅ {resultado['municipios_processados']} municípios processados")
            
            if resultado['detalhes']:
                print("   📋 Primeiras visitas criadas:")
                for i, visita in enumerate(resultado['detalhes'][:3]):
                    print(f"      {i+1}. {visita['nome_entidade']} - {visita['municipio']} (P{visita['prioridade']})")
            
        except Exception as e:
            print(f"   ❌ Erro ao inicializar visitas obrigatórias: {str(e)}")
            logger.exception("Erro detalhado:")
            return False
        
        # ===== PASSO 3: SINCRONIZAR VISITAS EXISTENTES =====
        print("\n🔄 PASSO 3: Sincronizando com visitas existentes...")
        try:
            from gestao_visitas.models.visitas_obrigatorias import sincronizar_visita_obrigatoria_com_visita_real
            
            # Buscar todas as visitas existentes
            visitas_existentes = Visita.query.all()
            print(f"   📊 Encontradas {len(visitas_existentes)} visitas existentes")
            
            sincronizadas = 0
            for visita in visitas_existentes:
                try:
                    num_sincronizadas = sincronizar_visita_obrigatoria_com_visita_real(visita.id)
                    if num_sincronizadas > 0:
                        sincronizadas += num_sincronizadas
                except:
                    pass  # Ignorar erros de sincronização individual
            
            print(f"   ✅ {sincronizadas} visitas obrigatórias sincronizadas")
            
        except Exception as e:
            print(f"   ⚠️ Aviso: Erro na sincronização: {str(e)}")
            # Não é crítico, continuar
        
        # ===== PASSO 4: CALCULAR STATUS INICIAL =====
        print("\n📊 PASSO 4: Calculando status inicial dos municípios...")
        try:
            from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
            
            status_calculados = 0
            for municipio in MUNICIPIOS_PNSB:
                try:
                    status = StatusVisitasObrigatorias.recalcular_status_municipio(municipio)
                    if status:
                        status_calculados += 1
                        print(f"   ✅ {municipio}: {status.concluidas}/{status.total_obrigatorias} visitas concluídas ({status.percentual_conclusao:.0f}%)")
                except Exception as e:
                    print(f"   ⚠️ {municipio}: Erro ao calcular status - {str(e)}")
            
            print(f"   ✅ Status calculado para {status_calculados}/{len(MUNICIPIOS_PNSB)} municípios")
            
        except Exception as e:
            print(f"   ❌ Erro ao calcular status: {str(e)}")
            return False
        
        # ===== PASSO 5: VERIFICAÇÃO FINAL =====
        print("\n🔍 PASSO 5: Verificação final do sistema...")
        try:
            # Verificar dados criados
            total_visitas_obrigatorias = VisitaObrigatoria.query.filter_by(ativo=True).count()
            total_status_municipios = StatusVisitasObrigatorias.query.count()
            
            # Estatísticas por prioridade
            p1_count = VisitaObrigatoria.query.filter_by(prioridade=1, ativo=True).count()
            p2_count = VisitaObrigatoria.query.filter_by(prioridade=2, ativo=True).count()
            
            # Estatísticas por status
            nao_agendadas = VisitaObrigatoria.query.filter_by(status_visita='nao_agendada', ativo=True).count()
            agendadas = VisitaObrigatoria.query.filter_by(status_visita='agendada', ativo=True).count()
            concluidas = VisitaObrigatoria.query.filter_by(status_visita='concluida', ativo=True).count()
            
            print(f"   📊 Total de visitas obrigatórias: {total_visitas_obrigatorias}")
            print(f"   📊 Municípios com status: {total_status_municipios}")
            print(f"   📊 Prioridade P1 (Críticas): {p1_count}")
            print(f"   📊 Prioridade P2 (Importantes): {p2_count}")
            print(f"   📊 Não agendadas: {nao_agendadas}")
            print(f"   📊 Agendadas: {agendadas}")
            print(f"   📊 Concluídas: {concluidas}")
            
            if total_visitas_obrigatorias > 0:
                percentual_completo = (concluidas / total_visitas_obrigatorias * 100)
                print(f"   📊 Progresso geral: {percentual_completo:.1f}%")
                
                print("\n   ✅ Sistema verificado com sucesso!")
            else:
                print("   ⚠️ Nenhuma visita obrigatória encontrada")
                return False
            
        except Exception as e:
            print(f"   ❌ Erro na verificação: {str(e)}")
            return False
        
        # ===== SUCESSO =====
        print("\n" + "=" * 80)
        print("🎉 SISTEMA DE VISITAS OBRIGATÓRIAS INICIALIZADO COM SUCESSO!")
        print("=" * 80)
        print("\n📋 PRÓXIMOS PASSOS:")
        print("   1. Acesse /api/visitas-obrigatorias/status-visitas-obrigatorias para ver o status geral")
        print("   2. Use /api/visitas-obrigatorias/dashboard-integrado/<municipio> para dashboards por município")
        print("   3. Gerencie visitas obrigatórias através das APIs criadas")
        print("\n💡 DICA: Execute este script novamente sempre que adicionar novas entidades P1/P2")
        
        return True

def verificar_pre_requisitos():
    """Verifica se os pré-requisitos estão atendidos"""
    print("🔍 Verificando pré-requisitos...")
    
    try:
        # Verificar se consegue importar modelos necessários
        from gestao_visitas.models.agendamento import Visita
        from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
        from gestao_visitas.config import MUNICIPIOS
        
        print("   ✅ Modelos importados com sucesso")
        print(f"   ✅ {len(MUNICIPIOS)} municípios PNSB configurados")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Erro de importação: {str(e)}")
        return False
    except Exception as e:
        print(f"   ❌ Erro inesperado: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 SCRIPT DE INICIALIZAÇÃO - SISTEMA DE VISITAS OBRIGATÓRIAS")
    print(f"📅 Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verificar pré-requisitos
    if not verificar_pre_requisitos():
        print("\n❌ Pré-requisitos não atendidos. Verifique a instalação.")
        sys.exit(1)
    
    # Executar inicialização
    sucesso = inicializar_sistema_completo()
    
    if sucesso:
        print(f"\n✅ Inicialização concluída com sucesso em {datetime.now().strftime('%H:%M:%S')}")
        sys.exit(0)
    else:
        print(f"\n❌ Inicialização falhou em {datetime.now().strftime('%H:%M:%S')}")
        sys.exit(1)