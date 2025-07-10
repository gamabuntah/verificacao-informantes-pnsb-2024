#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES UNITÁRIOS - SISTEMA INTELIGENTE DE STATUS PNSB 2024
===========================================================

Este arquivo contém testes para verificar se o sistema inteligente de status
está funcionando corretamente conforme os objetivos do PNSB.

Objetivos Testados:
- Sistema identifica corretamente status baseado em questionários e checklists
- Distinção entre questionários 'respondido' e 'validado_concluido'
- Integração correta entre visitas, questionários e checklists
- Recomendações de próximas ações são precisas
- Workflow segue processo PNSB real
"""

import sys
import os
import pytest
import json
from datetime import datetime, date, time
from unittest.mock import Mock, patch, MagicMock

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada


class TestSistemaInteligenteStatus:
    """Testes para o sistema inteligente de status"""
    
    def setup_method(self):
        """Setup antes de cada teste"""
        self.visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=time(9, 0),
            hora_fim=time(17, 0),
            local="Prefeitura",
            tipo_pesquisa="MRS",
            status="agendada"
        )
        
        # Mock checklist
        self.mock_checklist = Mock()
        self.mock_checklist.calcular_progresso_preparacao.return_value = 80
        self.mock_checklist.calcular_progresso_execucao.return_value = 70
        self.mock_checklist.calcular_progresso_resultados.return_value = 60
        self.visita.checklist = self.mock_checklist
        
    def test_status_inteligente_agendada_para_realizada(self):
        """Teste: Visita agendada com checklist preparação completo deve ir para 'realizada'"""
        
        # Arrange
        self.visita.status = "em andamento"
        self.mock_checklist.calcular_progresso_preparacao.return_value = 85  # >80%
        
        # Mock questionários vazios
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = []
            
            # Act
            status_inteligente = self.visita.calcular_status_inteligente()
            
            # Assert
            assert status_inteligente == "realizada", f"Esperado 'realizada', obtido '{status_inteligente}'"
    
    def test_status_inteligente_com_questionarios_respondidos(self):
        """Teste: Visita com questionários respondidos deve ir para 'questionários concluídos'"""
        
        # Arrange
        self.visita.status = "realizada"
        self.mock_checklist.calcular_progresso_execucao.return_value = 85  # >80%
        
        # Mock entidades com questionários respondidos
        mock_entidade = Mock()
        mock_entidade.status_mrs = "respondido"
        mock_entidade.status_map = "nao_iniciado"
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Act
            status_inteligente = self.visita.calcular_status_inteligente()
            
            # Assert
            assert status_inteligente == "questionários concluídos", f"Esperado 'questionários concluídos', obtido '{status_inteligente}'"
    
    def test_status_inteligente_com_questionarios_validados(self):
        """Teste: Visita com questionários validados deve ir para 'questionários validados'"""
        
        # Arrange
        self.visita.status = "questionários concluídos"
        
        # Mock entidades com questionários validados
        mock_entidade = Mock()
        mock_entidade.status_mrs = "validado_concluido"
        mock_entidade.status_map = "validado_concluido"
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Act
            status_inteligente = self.visita.calcular_status_inteligente()
            
            # Assert
            assert status_inteligente == "questionários validados", f"Esperado 'questionários validados', obtido '{status_inteligente}'"
    
    def test_status_inteligente_finalizada(self):
        """Teste: Visita com questionários validados + checklist pós-visita deve ir para 'finalizada'"""
        
        # Arrange
        self.visita.status = "questionários validados"
        self.mock_checklist.calcular_progresso_resultados.return_value = 85  # >80%
        
        # Mock entidades com questionários validados
        mock_entidade = Mock()
        mock_entidade.status_mrs = "validado_concluido"
        mock_entidade.status_map = "validado_concluido"
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Act
            status_inteligente = self.visita.calcular_status_inteligente()
            
            # Assert
            assert status_inteligente == "finalizada", f"Esperado 'finalizada', obtido '{status_inteligente}'"
    
    def test_progresso_checklist_calculation(self):
        """Teste: Cálculo de progresso do checklist funciona corretamente"""
        
        # Act
        progresso = self.visita.obter_progresso_checklist()
        
        # Assert
        assert progresso['antes'] == 80
        assert progresso['durante'] == 70
        assert progresso['apos'] == 60
    
    def test_status_questionarios_summary(self):
        """Teste: Resumo de status dos questionários é calculado corretamente"""
        
        # Arrange
        mock_entidades = [
            Mock(status_mrs="respondido", status_map="nao_iniciado"),
            Mock(status_mrs="validado_concluido", status_map="respondido"),
            Mock(status_mrs="nao_iniciado", status_map="validado_concluido")
        ]
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = mock_entidades
            
            # Act
            status_summary = self.visita.obter_status_questionarios()
            
            # Assert
            assert status_summary['total_entidades'] == 3
            assert status_summary['mrs']['respondido'] == 1
            assert status_summary['mrs']['validado_concluido'] == 1
            assert status_summary['mrs']['nao_iniciado'] == 1
            assert status_summary['map']['respondido'] == 1
            assert status_summary['map']['validado_concluido'] == 1
            assert status_summary['map']['nao_iniciado'] == 1
    
    def test_recomendacao_proxima_acao_agendada(self):
        """Teste: Recomendação para visita agendada"""
        
        # Arrange
        self.visita.status = "agendada"
        self.mock_checklist.calcular_progresso_preparacao.return_value = 40  # <50%
        
        # Act
        recomendacao = self.visita.recomendar_proxima_acao()
        
        # Assert
        assert recomendacao == "Completar preparação da visita no checklist"
    
    def test_recomendacao_proxima_acao_realizada(self):
        """Teste: Recomendação para visita realizada com questionários pendentes"""
        
        # Arrange
        self.visita.status = "realizada"
        
        # Mock questionários não iniciados
        with patch.object(self.visita, 'obter_status_questionarios') as mock_status:
            mock_status.return_value = {
                'mrs': {'nao_iniciado': 2, 'respondido': 0, 'validado_concluido': 0},
                'map': {'nao_iniciado': 1, 'respondido': 0, 'validado_concluido': 0}
            }
            
            # Act
            recomendacao = self.visita.recomendar_proxima_acao()
            
            # Assert
            assert recomendacao == "Responder questionários pendentes"
    
    def test_progresso_completo_calculation(self):
        """Teste: Cálculo de progresso completo considera todos os fatores"""
        
        # Arrange
        mock_entidades = [Mock(status_mrs="validado_concluido", status_map="respondido")]
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = mock_entidades
            
            # Act
            progresso_completo = self.visita.calcular_progresso_completo()
            
            # Assert
            assert 'progresso_total' in progresso_completo
            assert 'detalhes' in progresso_completo
            assert 'status_inteligente' in progresso_completo
            
            detalhes = progresso_completo['detalhes']
            assert detalhes['preparacao'] == 80
            assert detalhes['execucao'] == 70
            assert detalhes['finalizacao'] == 60
            
            # Progresso questionários: 1.5/2 = 75% (1 validado + 0.5 respondido de 2 total)
            assert detalhes['questionarios'] == 75.0
            
            # Progresso total: 80*0.2 + 70*0.3 + 75*0.4 + 60*0.1 = 67%
            expected_total = 80*0.2 + 70*0.3 + 75*0.4 + 60*0.1
            assert abs(progresso_completo['progresso_total'] - expected_total) < 0.1
    
    def test_to_dict_inclui_dados_inteligentes(self):
        """Teste: Conversão para dict inclui dados inteligentes"""
        
        # Arrange
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = []
            
            # Act
            visita_dict = self.visita.to_dict()
            
            # Assert
            assert 'status_inteligente' in visita_dict
            assert 'progresso_checklist' in visita_dict
            assert 'status_questionarios' in visita_dict
            assert 'proxima_acao' in visita_dict
            assert 'progresso_completo' in visita_dict


class TestValidacaoWorkflowPNSB:
    """Testes para validar se o workflow segue processo PNSB real"""
    
    def test_workflow_status_transitions(self):
        """Teste: Transições de status seguem workflow PNSB"""
        
        # Arrange
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=time(9, 0),
            local="Prefeitura",
            status="agendada"
        )
        
        # Test valid transitions
        valid_transitions = [
            ("agendada", ["em andamento", "realizada", "remarcada", "não realizada"]),
            ("em andamento", ["realizada", "agendada", "remarcada", "não realizada"]),
            ("realizada", ["questionários concluídos", "agendada", "em andamento"]),
            ("questionários concluídos", ["questionários validados", "realizada"]),
            ("questionários validados", ["finalizada", "questionários concluídos"]),
            ("finalizada", ["questionários validados", "questionários concluídos", "realizada"])
        ]
        
        for current_status, allowed_next in valid_transitions:
            visita.status = current_status
            for next_status in allowed_next:
                # Act & Assert - should not raise exception
                try:
                    visita.atualizar_status(next_status)
                    assert visita.status == next_status
                    visita.status = current_status  # Reset for next test
                except ValueError:
                    pytest.fail(f"Transição válida falhou: {current_status} -> {next_status}")
    
    def test_workflow_invalid_transitions(self):
        """Teste: Transições inválidas são rejeitadas"""
        
        # Arrange
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=time(9, 0),
            local="Prefeitura",
            status="agendada"
        )
        
        # Test invalid transitions
        invalid_transitions = [
            ("agendada", "questionários concluídos"),  # Não pode pular etapas
            ("agendada", "finalizada"),                # Não pode pular para fim
            ("em andamento", "questionários validados"), # Não pode pular validação
            ("questionários concluídos", "finalizada")   # Deve validar antes
        ]
        
        for current_status, invalid_next in invalid_transitions:
            visita.status = current_status
            
            # Act & Assert - should raise ValueError
            with pytest.raises(ValueError, match="Transição de status não permitida"):
                visita.atualizar_status(invalid_next)


class TestIntegracaoQuestionariosChecklist:
    """Testes para verificar integração entre questionários e checklist"""
    
    def test_status_considerando_ambos_mrs_map(self):
        """Teste: Status considera tanto MRS quanto MAP quando ambos são obrigatórios"""
        
        # Arrange
        visita = Visita(municipio="Itajaí", data=date.today(), hora_inicio=time(9, 0), 
                       local="Prefeitura", status="realizada")
        
        # Mock entidade com MRS validado e MAP respondido
        mock_entidade = Mock()
        mock_entidade.status_mrs = "validado_concluido"
        mock_entidade.status_map = "respondido"  # Ainda não validado
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Act
            status_inteligente = visita.calcular_status_inteligente()
            
            # Assert - Deve ser 'questionários validados' pois tem pelo menos um validado
            assert status_inteligente == "questionários validados"
    
    def test_checklist_influencia_status_finalizacao(self):
        """Teste: Checklist pós-visita influencia status de finalização"""
        
        # Arrange
        visita = Visita(municipio="Itajaí", data=date.today(), hora_inicio=time(9, 0),
                       local="Prefeitura", status="questionários validados")
        
        mock_checklist = Mock()
        mock_checklist.calcular_progresso_preparacao.return_value = 100
        mock_checklist.calcular_progresso_execucao.return_value = 100
        mock_checklist.calcular_progresso_resultados.return_value = 90  # >80%
        visita.checklist = mock_checklist
        
        # Mock questionários validados
        mock_entidade = Mock()
        mock_entidade.status_mrs = "validado_concluido"
        mock_entidade.status_map = "validado_concluido"
        
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Act
            status_inteligente = visita.calcular_status_inteligente()
            
            # Assert
            assert status_inteligente == "finalizada"


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])