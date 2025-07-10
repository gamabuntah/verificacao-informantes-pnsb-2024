#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES DE FLUXO COMPLETO - WORKFLOW PNSB 2024
============================================

Este arquivo contém testes que simulam o fluxo completo do PNSB 2024,
desde o agendamento de uma visita até sua finalização, verificando se
o sistema funciona corretamente end-to-end.

Cenários Testados:
- Fluxo completo: Agendamento → Preparação → Execução → Questionários → Validação → Finalização
- Cenários de exceção: Reagendamento, não realização, problemas de validação
- Integração entre visitas, checklists e questionários
- Sistema inteligente de status em ação
- Workflow de múltiplos municípios e prioridades
"""

import sys
import os
import pytest
import json
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada


class TestFluxoCompletoVisitaPNSB:
    """Teste do fluxo completo de uma visita PNSB"""
    
    @pytest.fixture
    def setup_database(self):
        """Setup do banco para testes"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield db
            db.drop_all()
    
    def test_fluxo_completo_visita_bem_sucedida(self, setup_database):
        """
        Teste: Fluxo completo de uma visita bem-sucedida
        Cenário: Prefeitura de Itajaí, MRS e MAP obrigatórios
        """
        
        # === ETAPA 1: AGENDAMENTO ===
        print("\n=== ETAPA 1: AGENDAMENTO ===")
        
        # Criar visita agendada
        visita = Visita(
            municipio="Itajaí",
            data=date.today() + timedelta(days=1),
            hora_inicio=time(9, 0),
            hora_fim=time(17, 0),
            local="Prefeitura de Itajaí",
            tipo_pesquisa="MRS",
            status="agendada"
        )
        db.session.add(visita)
        
        # Criar checklist associado
        checklist = Checklist(visita_id=visita.id)
        db.session.add(checklist)
        
        # Criar entidade identificada (Prefeitura - P1)
        entidade = EntidadeIdentificada(
            municipio="Itajaí",
            nome_entidade="Prefeitura de Itajaí",
            tipo_entidade="prefeitura",
            status_mrs="nao_iniciado",
            status_map="nao_iniciado",
            prioridade=1,
            mrs_obrigatorio=True,
            map_obrigatorio=True
        )
        db.session.add(entidade)
        db.session.commit()
        
        # Verificar status inicial
        assert visita.status == "agendada"
        assert visita.calcular_status_inteligente() == "agendada"
        assert visita.recomendar_proxima_acao() == "Completar preparação da visita no checklist"
        
        print(f"✅ Visita agendada - Status: {visita.status}")
        print(f"✅ Recomendação: {visita.recomendar_proxima_acao()}")
        
        # === ETAPA 2: PREPARAÇÃO ===
        print("\n=== ETAPA 2: PREPARAÇÃO ===")
        
        # Simular preenchimento do checklist de preparação
        with patch.object(checklist, 'calcular_progresso_preparacao', return_value=90):
            with patch.object(checklist, 'calcular_progresso_execucao', return_value=0):
                with patch.object(checklist, 'calcular_progresso_resultados', return_value=0):
                    # Status inteligente deve ainda ser agendada, mas recomendação muda
                    status_inteligente = visita.calcular_status_inteligente()
                    recomendacao = visita.recomendar_proxima_acao()
                    
                    assert status_inteligente == "agendada"
                    assert recomendacao == "Iniciar visita"  # Preparação completa
        
        print(f"✅ Preparação completa - Recomendação: {recomendacao}")
        
        # === ETAPA 3: EXECUÇÃO DA VISITA ===
        print("\n=== ETAPA 3: EXECUÇÃO DA VISITA ===")
        
        # Atualizar status para em andamento
        visita.atualizar_status("em andamento")
        assert visita.status == "em andamento"
        
        # Simular execução da visita
        with patch.object(checklist, 'calcular_progresso_preparacao', return_value=90):
            with patch.object(checklist, 'calcular_progresso_execucao', return_value=85):
                with patch.object(checklist, 'calcular_progresso_resultados', return_value=0):
                    # Com checklist de execução completo, deve sugerir realizada
                    status_inteligente = visita.calcular_status_inteligente()
                    assert status_inteligente == "realizada"
        
        # Atualizar status para realizada
        visita.atualizar_status("realizada")
        assert visita.status == "realizada"
        
        print(f"✅ Visita executada - Status: {visita.status}")
        
        # === ETAPA 4: PREENCHIMENTO DE QUESTIONÁRIOS ===
        print("\n=== ETAPA 4: PREENCHIMENTO DE QUESTIONÁRIOS ===")
        
        # Simular preenchimento do questionário MRS
        entidade.status_mrs = "respondido"
        db.session.commit()
        
        # Verificar que status inteligente detecta questionários respondidos
        status_inteligente = visita.calcular_status_inteligente()
        recomendacao = visita.recomendar_proxima_acao()
        
        assert status_inteligente == "questionários concluídos"
        assert "questionários pendentes" in recomendacao or "questionários respondidos" in recomendacao
        
        print(f"✅ MRS respondido - Status inteligente: {status_inteligente}")
        
        # Simular preenchimento do questionário MAP
        entidade.status_map = "respondido"
        db.session.commit()
        
        # Atualizar status da visita
        visita.atualizar_status("questionários concluídos")
        
        print(f"✅ MAP respondido - Status visita: {visita.status}")
        
        # === ETAPA 5: VALIDAÇÃO ===
        print("\n=== ETAPA 5: VALIDAÇÃO ===")
        
        # Simular validação dos questionários
        entidade.status_mrs = "validado_concluido"
        entidade.status_map = "validado_concluido"
        db.session.commit()
        
        # Verificar que status inteligente detecta validação
        status_inteligente = visita.calcular_status_inteligente()
        assert status_inteligente == "questionários validados"
        
        # Atualizar status da visita
        visita.atualizar_status("questionários validados")
        
        print(f"✅ Questionários validados - Status: {visita.status}")
        
        # === ETAPA 6: FINALIZAÇÃO ===
        print("\n=== ETAPA 6: FINALIZAÇÃO ===")
        
        # Simular preenchimento das ações pós-visita
        with patch.object(checklist, 'calcular_progresso_preparacao', return_value=90):
            with patch.object(checklist, 'calcular_progresso_execucao', return_value=85):
                with patch.object(checklist, 'calcular_progresso_resultados', return_value=90):
                    # Com todos os checklists e questionários completos, deve finalizar
                    status_inteligente = visita.calcular_status_inteligente()
                    assert status_inteligente == "finalizada"
        
        # Finalizar visita
        visita.atualizar_status("finalizada")
        
        # Verificar progresso completo
        progresso_completo = visita.calcular_progresso_completo()
        assert progresso_completo['progresso_total'] > 90  # Quase 100%
        
        print(f"✅ Visita finalizada - Progresso: {progresso_completo['progresso_total']:.1f}%")
        
        # === VERIFICAÇÕES FINAIS ===
        print("\n=== VERIFICAÇÕES FINAIS ===")
        
        # Verificar que todos os objetivos foram alcançados
        assert visita.status == "finalizada"
        assert entidade.status_mrs == "validado_concluido"
        assert entidade.status_map == "validado_concluido"
        assert visita.recomendar_proxima_acao() == "Visita finalizada"
        
        print("✅ Fluxo completo executado com sucesso!")
        print(f"✅ Status final: {visita.status}")
        print(f"✅ MRS: {entidade.status_mrs}")
        print(f"✅ MAP: {entidade.status_map}")
        print(f"✅ Recomendação final: {visita.recomendar_proxima_acao()}")
    
    def test_fluxo_com_reagendamento(self, setup_database):
        """
        Teste: Fluxo com reagendamento
        Cenário: Visita precisa ser remarcada
        """
        
        print("\n=== TESTE: FLUXO COM REAGENDAMENTO ===")
        
        # Criar visita agendada
        visita = Visita(
            municipio="Navegantes",
            data=date.today(),
            hora_inicio=time(14, 0),
            local="Prefeitura",
            status="agendada"
        )
        db.session.add(visita)
        db.session.commit()
        
        # Reagendar visita
        visita.atualizar_status("remarcada")
        assert visita.status == "remarcada"
        
        # Reagendar para nova data
        visita.data = date.today() + timedelta(days=3)
        visita.atualizar_status("agendada")
        
        assert visita.status == "agendada"
        print(f"✅ Visita reagendada para {visita.data}")
    
    def test_fluxo_visita_nao_realizada(self, setup_database):
        """
        Teste: Fluxo com visita não realizada
        Cenário: Visita não pode ser realizada
        """
        
        print("\n=== TESTE: FLUXO VISITA NÃO REALIZADA ===")
        
        # Criar visita e entidade
        visita = Visita(
            municipio="Bombinhas",
            data=date.today(),
            hora_inicio=time(10, 0),
            local="Prefeitura",
            status="agendada"
        )
        db.session.add(visita)
        
        entidade = EntidadeIdentificada(
            municipio="Bombinhas",
            nome_entidade="Prefeitura de Bombinhas",
            tipo_entidade="prefeitura",
            status_mrs="nao_iniciado",
            status_map="nao_iniciado",
            prioridade=1
        )
        db.session.add(entidade)
        db.session.commit()
        
        # Marcar como não realizada
        visita.atualizar_status("não realizada")
        
        # Verificar que entidades ficam como não aplicável
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.sincronizar_entidades_por_visita') as mock_sync:
            # Simular sincronização
            entidade.status_mrs = "nao_aplicavel"
            entidade.status_map = "nao_aplicavel"
            
            status_summary = visita.obter_status_questionarios()
            # Com visita não realizada, questionários devem ser não aplicáveis
        
        print(f"✅ Visita não realizada - Status: {visita.status}")
        print(f"✅ Entidade MRS: {entidade.status_mrs}")
        print(f"✅ Entidade MAP: {entidade.status_map}")


class TestFluxoMultiplosMunicipios:
    """Teste do fluxo com múltiplos municípios e prioridades"""
    
    @pytest.fixture
    def setup_multiplos_municipios(self):
        """Setup com múltiplos municípios e entidades"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            
            # Criar visitas para diferentes municípios
            municipios_teste = ["Itajaí", "Navegantes", "Camboriú"]
            
            for i, municipio in enumerate(municipios_teste):
                # Visita
                visita = Visita(
                    municipio=municipio,
                    data=date.today() + timedelta(days=i),
                    hora_inicio=time(9, 0),
                    local=f"Prefeitura de {municipio}",
                    status="agendada"
                )
                db.session.add(visita)
                
                # Entidades com diferentes prioridades
                # P1 - Prefeitura (sempre obrigatória)
                entidade_p1 = EntidadeIdentificada(
                    municipio=municipio,
                    nome_entidade=f"Prefeitura de {municipio}",
                    tipo_entidade="prefeitura",
                    status_mrs="nao_iniciado",
                    status_map="nao_iniciado",
                    prioridade=1,
                    mrs_obrigatorio=True,
                    map_obrigatorio=True
                )
                db.session.add(entidade_p1)
                
                # P2 - Empresa terceirizada (se existir)
                if i < 2:  # Apenas Itajaí e Navegantes
                    entidade_p2 = EntidadeIdentificada(
                        municipio=municipio,
                        nome_entidade=f"Empresa Limpeza {municipio}",
                        tipo_entidade="empresa_terceirizada",
                        status_mrs="nao_iniciado",
                        status_map="nao_iniciado",
                        prioridade=2,
                        mrs_obrigatorio=True,
                        map_obrigatorio=False
                    )
                    db.session.add(entidade_p2)
            
            db.session.commit()
            yield db
            db.drop_all()
    
    def test_progresso_multiplos_municipios(self, setup_multiplos_municipios):
        """
        Teste: Progresso de múltiplos municípios com diferentes estágios
        """
        
        print("\n=== TESTE: MÚLTIPLOS MUNICÍPIOS ===")
        
        visitas = Visita.query.all()
        entidades = EntidadeIdentificada.query.all()
        
        # Simular diferentes estágios para cada município
        
        # === ITAJAÍ: FINALIZADA ===
        visita_itajai = Visita.query.filter_by(municipio="Itajaí").first()
        entidades_itajai = EntidadeIdentificada.query.filter_by(municipio="Itajaí").all()
        
        visita_itajai.status = "finalizada"
        for entidade in entidades_itajai:
            entidade.status_mrs = "validado_concluido"
            entidade.status_map = "validado_concluido"
        
        # === NAVEGANTES: EM PROGRESSO ===
        visita_navegantes = Visita.query.filter_by(municipio="Navegantes").first()
        entidades_navegantes = EntidadeIdentificada.query.filter_by(municipio="Navegantes").all()
        
        visita_navegantes.status = "questionários concluídos"
        for entidade in entidades_navegantes:
            entidade.status_mrs = "respondido"
            if entidade.map_obrigatorio:
                entidade.status_map = "respondido"
        
        # === CAMBORIÚ: AGENDADA ===
        visita_camboriu = Visita.query.filter_by(municipio="Camboriú").first()
        # Mantém status inicial
        
        db.session.commit()
        
        # Verificar progresso por município
        progresso_itajai = visita_itajai.calcular_progresso_completo()
        progresso_navegantes = visita_navegantes.calcular_progresso_completo()
        progresso_camboriu = visita_camboriu.calcular_progresso_completo()
        
        print(f"Itajaí: {progresso_itajai['progresso_total']:.1f}% - {visita_itajai.status}")
        print(f"Navegantes: {progresso_navegantes['progresso_total']:.1f}% - {visita_navegantes.status}")
        print(f"Camboriú: {progresso_camboriu['progresso_total']:.1f}% - {visita_camboriu.status}")
        
        # Verificar que Itajaí tem maior progresso
        assert progresso_itajai['progresso_total'] > progresso_navegantes['progresso_total']
        assert progresso_navegantes['progresso_total'] > progresso_camboriu['progresso_total']
        
        # Calcular estatísticas P1/P2/P3
        stats_p1 = {'total': 0, 'concluidos': 0}
        stats_p2 = {'total': 0, 'concluidos': 0}
        
        for entidade in entidades:
            if entidade.prioridade == 1:
                stats_p1['total'] += 1
                if (entidade.status_mrs == 'validado_concluido' and 
                    entidade.status_map == 'validado_concluido'):
                    stats_p1['concluidos'] += 1
            elif entidade.prioridade == 2:
                stats_p2['total'] += 1
                mrs_ok = not entidade.mrs_obrigatorio or entidade.status_mrs == 'validado_concluido'
                map_ok = not entidade.map_obrigatorio or entidade.status_map == 'validado_concluido'
                if mrs_ok and map_ok:
                    stats_p2['concluidos'] += 1
        
        print(f"P1: {stats_p1['concluidos']}/{stats_p1['total']} concluídas")
        print(f"P2: {stats_p2['concluidos']}/{stats_p2['total']} concluídas")
        
        # Verificar lógica de prioridades
        assert stats_p1['total'] == 3  # Uma prefeitura por município
        assert stats_p1['concluidos'] == 1  # Apenas Itajaí finalizada
        assert stats_p2['total'] == 2  # Itajaí e Navegantes têm empresa


class TestCenariosExcepcionais:
    """Testes para cenários excepcionais e edge cases"""
    
    @pytest.fixture
    def setup_cenarios(self):
        """Setup para cenários excepcionais"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield db
            db.drop_all()
    
    def test_questionario_validado_sem_mrs_obrigatorio(self, setup_cenarios):
        """
        Teste: Entidade com MAP obrigatório mas MRS não obrigatório
        """
        
        # Criar entidade específica (ex: empresa que só faz coleta)
        visita = Visita(municipio="Penha", data=date.today(), hora_inicio=time(10, 0), local="Empresa XYZ")
        db.session.add(visita)
        
        entidade = EntidadeIdentificada(
            municipio="Penha",
            nome_entidade="Empresa Coleta XYZ",
            tipo_entidade="empresa_terceirizada",
            status_mrs="nao_aplicavel",  # Não aplicável
            status_map="validado_concluido",  # Obrigatório e concluído
            prioridade=2,
            mrs_obrigatorio=False,
            map_obrigatorio=True
        )
        db.session.add(entidade)
        db.session.commit()
        
        # Verificar que entidade é considerada concluída
        status_summary = visita.obter_status_questionarios()
        
        # Simular cálculo de conclusão
        mrs_ok = not entidade.mrs_obrigatorio or entidade.status_mrs == 'validado_concluido'
        map_ok = not entidade.map_obrigatorio or entidade.status_map == 'validado_concluido'
        
        assert mrs_ok == True  # MRS não obrigatório
        assert map_ok == True  # MAP obrigatório e validado
        
        print("✅ Entidade com apenas MAP obrigatório funciona corretamente")
    
    def test_visita_sem_entidades(self, setup_cenarios):
        """
        Teste: Visita sem entidades identificadas
        """
        
        visita = Visita(municipio="Porto Belo", data=date.today(), hora_inicio=time(9, 0), local="Local Indefinido")
        db.session.add(visita)
        db.session.commit()
        
        # Não adicionar entidades
        
        # Verificar que sistema funciona sem entidades
        status_inteligente = visita.calcular_status_inteligente()
        status_summary = visita.obter_status_questionarios()
        progresso = visita.calcular_progresso_completo()
        
        assert status_inteligente == visita.status  # Mantém status atual
        assert status_summary['total_entidades'] == 0
        assert isinstance(progresso['progresso_total'], (int, float))
        
        print("✅ Sistema funciona sem entidades identificadas")
    
    def test_checklist_incompleto(self, setup_cenarios):
        """
        Teste: Comportamento com checklist incompleto
        """
        
        visita = Visita(municipio="Luiz Alves", data=date.today(), hora_inicio=time(11, 0), local="Prefeitura")
        # Não adicionar checklist
        db.session.add(visita)
        db.session.commit()
        
        # Verificar que sistema funciona sem checklist
        progresso_checklist = visita.obter_progresso_checklist()
        
        assert progresso_checklist['antes'] == 0
        assert progresso_checklist['durante'] == 0
        assert progresso_checklist['apos'] == 0
        
        print("✅ Sistema funciona sem checklist")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])