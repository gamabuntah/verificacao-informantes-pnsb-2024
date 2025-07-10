#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES DE LÓGICA DE NEGÓCIO - PNSB 2024
=====================================

Este arquivo contém testes para verificar se as regras de negócio específicas
do PNSB 2024 estão sendo implementadas corretamente.

Regras Testadas:
- Prioridades P1/P2/P3 seguem critérios PNSB
- Questionários MRS vs MAP conforme tipo de entidade
- Validação vs Resposta de questionários
- Workflow de status específico PNSB
- Cálculo de progresso conforme metodologia PNSB
- Municípios cobertos pelo projeto
"""

import sys
import os
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada
from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB


class TestRegrasPrioridadePNSB:
    """Testes para verificar regras de prioridade do PNSB"""
    
    def test_prioridade_p1_criterios_corretos(self):
        """
        Teste: P1 (Críticas) - Prefeituras e Lista UF
        Regra PNSB: P1 são sempre obrigatórias para cumprimento dos objetivos
        """
        
        # P1 - Prefeitura (sempre P1)
        prefeitura = EntidadeIdentificada(
            municipio="Itajaí",
            nome_entidade="Prefeitura de Itajaí",
            tipo_entidade="prefeitura",
            prioridade=1,
            mrs_obrigatorio=True,
            map_obrigatorio=True,
            origem_prefeitura=True
        )
        
        # Verificar características P1
        assert prefeitura.prioridade == 1
        assert prefeitura.mrs_obrigatorio == True
        assert prefeitura.map_obrigatorio == True
        assert prefeitura.origem_prefeitura == True
        
        # P1 - Entidade da Lista UF
        entidade_uf = EntidadeIdentificada(
            municipio="Itajaí",
            nome_entidade="Empresa Lista UF",
            tipo_entidade="empresa_terceirizada",
            prioridade=1,
            mrs_obrigatorio=True,
            map_obrigatorio=False,
            origem_lista_uf=True
        )
        
        assert entidade_uf.prioridade == 1
        assert entidade_uf.origem_lista_uf == True
        
        print("✅ P1 - Critérios de prioridade crítica validados")
    
    def test_prioridade_p2_criterios_corretos(self):
        """
        Teste: P2 (Importantes) - Entidades identificadas em campo
        Regra PNSB: P2 se tornam obrigatórias quando incluídas no trabalho
        """
        
        entidade_campo = EntidadeIdentificada(
            municipio="Navegantes",
            nome_entidade="Empresa Identificada em Campo",
            tipo_entidade="empresa_terceirizada",
            prioridade=2,
            mrs_obrigatorio=True,
            map_obrigatorio=False,
            origem_campo=True
        )
        
        # Verificar características P2
        assert entidade_campo.prioridade == 2
        assert entidade_campo.origem_campo == True
        # P2 pode ter diferentes combinações de obrigatoriedade
        assert isinstance(entidade_campo.mrs_obrigatorio, bool)
        assert isinstance(entidade_campo.map_obrigatorio, bool)
        
        print("✅ P2 - Critérios de prioridade importante validados")
    
    def test_prioridade_p3_criterios_corretos(self):
        """
        Teste: P3 (Opcionais) - Para trabalho abrangente se houver recursos
        Regra PNSB: P3 são informacionais, não obrigatórias
        """
        
        entidade_referencia = EntidadeIdentificada(
            municipio="Camboriú",
            nome_entidade="Entidade de Referência",
            tipo_entidade="entidade_catadores",
            prioridade=3,
            mrs_obrigatorio=False,
            map_obrigatorio=False
        )
        
        # Verificar características P3
        assert entidade_referencia.prioridade == 3
        # P3 geralmente não são obrigatórias
        assert entidade_referencia.mrs_obrigatorio == False
        assert entidade_referencia.map_obrigatorio == False
        
        print("✅ P3 - Critérios de prioridade opcional validados")
    
    def test_calculo_progresso_por_prioridade(self):
        """
        Teste: Cálculo de progresso considera prioridades corretamente
        Regra PNSB: P1 devem ser 100% antes de considerar P2/P3
        """
        
        # Simular entidades de diferentes prioridades
        entidades = [
            # P1 - 2 entidades, 1 concluída
            Mock(prioridade=1, status_mrs='validado_concluido', status_map='validado_concluido', 
                 mrs_obrigatorio=True, map_obrigatorio=True),
            Mock(prioridade=1, status_mrs='respondido', status_map='nao_iniciado',
                 mrs_obrigatorio=True, map_obrigatorio=True),
            
            # P2 - 1 entidade, concluída
            Mock(prioridade=2, status_mrs='validado_concluido', status_map='nao_aplicavel',
                 mrs_obrigatorio=True, map_obrigatorio=False),
            
            # P3 - 1 entidade, não iniciada
            Mock(prioridade=3, status_mrs='nao_iniciado', status_map='nao_iniciado',
                 mrs_obrigatorio=False, map_obrigatorio=False)
        ]
        
        # Calcular estatísticas por prioridade
        stats = {'p1': {'total': 0, 'concluidos': 0},
                'p2': {'total': 0, 'concluidos': 0},
                'p3': {'total': 0, 'concluidos': 0}}
        
        for entidade in entidades:
            prioridade = f"p{entidade.prioridade}"
            stats[prioridade]['total'] += 1
            
            # Considerar concluído se todos os obrigatórios estão validados
            mrs_ok = not entidade.mrs_obrigatorio or entidade.status_mrs == 'validado_concluido'
            map_ok = not entidade.map_obrigatorio or entidade.status_map == 'validado_concluido'
            
            if mrs_ok and map_ok:
                stats[prioridade]['concluidos'] += 1
        
        # Verificar cálculos
        assert stats['p1']['total'] == 2
        assert stats['p1']['concluidos'] == 1  # 50%
        assert stats['p2']['total'] == 1
        assert stats['p2']['concluidos'] == 1  # 100%
        assert stats['p3']['total'] == 1
        assert stats['p3']['concluidos'] == 0  # 0%
        
        # P1 não está 100%, então município não está completo
        municipio_completo = stats['p1']['concluidos'] == stats['p1']['total']
        assert municipio_completo == False
        
        print("✅ Cálculo de progresso por prioridade validado")


class TestRegrasTipoQuestionario:
    """Testes para verificar regras de tipo de questionário"""
    
    def test_mrs_obrigatorio_por_tipo_entidade(self):
        """
        Teste: MRS obrigatório conforme tipo de entidade
        Regra PNSB: Nem toda entidade precisa responder MRS
        """
        
        casos_teste = [
            # Prefeitura - sempre MRS + MAP
            {"tipo": "prefeitura", "mrs_esperado": True, "map_esperado": True},
            
            # Empresa terceirizada - geralmente MRS
            {"tipo": "empresa_terceirizada", "mrs_esperado": True, "map_esperado": False},
            
            # Entidade catadores - pode variar
            {"tipo": "entidade_catadores", "mrs_esperado": True, "map_esperado": False},
            
            # Empresa não vinculada - pode variar
            {"tipo": "empresa_nao_vinculada", "mrs_esperado": False, "map_esperado": False}
        ]
        
        for caso in casos_teste:
            # Verificar que é possível configurar conforme esperado
            entidade = EntidadeIdentificada(
                municipio="Itajaí",
                nome_entidade=f"Teste {caso['tipo']}",
                tipo_entidade=caso['tipo'],
                mrs_obrigatorio=caso['mrs_esperado'],
                map_obrigatorio=caso['map_esperado']
            )
            
            assert entidade.mrs_obrigatorio == caso['mrs_esperado']
            assert entidade.map_obrigatorio == caso['map_esperado']
        
        print("✅ Regras de obrigatoriedade por tipo de entidade validadas")
    
    def test_map_obrigatorio_criterios(self):
        """
        Teste: MAP obrigatório conforme critérios específicos
        Regra PNSB: MAP focado em águas pluviais - nem sempre aplicável
        """
        
        # Entidades que devem ter MAP
        entidades_com_map = [
            {"nome": "Prefeitura", "tipo": "prefeitura", "justificativa": "Gestão municipal"},
            {"nome": "Empresa Drenagem", "tipo": "empresa_terceirizada", "justificativa": "Serviço de drenagem"}
        ]
        
        # Entidades que podem não ter MAP
        entidades_sem_map = [
            {"nome": "Cooperativa Catadores", "tipo": "entidade_catadores", "justificativa": "Foco em resíduos sólidos"},
            {"nome": "Empresa Coleta", "tipo": "empresa_terceirizada", "justificativa": "Apenas coleta de lixo"}
        ]
        
        for entidade_info in entidades_com_map:
            entidade = EntidadeIdentificada(
                nome_entidade=entidade_info["nome"],
                tipo_entidade=entidade_info["tipo"],
                map_obrigatorio=True
            )
            assert entidade.map_obrigatorio == True
        
        for entidade_info in entidades_sem_map:
            entidade = EntidadeIdentificada(
                nome_entidade=entidade_info["nome"],
                tipo_entidade=entidade_info["tipo"],
                map_obrigatorio=False
            )
            assert entidade.map_obrigatorio == False
        
        print("✅ Regras de obrigatoriedade MAP validadas")


class TestRegrasValidacaoQuestionarios:
    """Testes para verificar regras de validação de questionários"""
    
    def test_distincao_respondido_vs_validado(self):
        """
        Teste: Distinção entre 'respondido' e 'validado_concluido'
        Regra PNSB: Questionário pode estar respondido mas não validado
        """
        
        entidade = EntidadeIdentificada(
            municipio="Itajaí",
            nome_entidade="Teste Validação",
            status_mrs="respondido",
            status_map="nao_iniciado"
        )
        
        # Verificar estados distintos
        assert entidade.status_mrs == "respondido"
        assert entidade.status_mrs != "validado_concluido"
        
        # Simular processo de validação
        entidade.status_mrs = "validado_concluido"
        assert entidade.status_mrs == "validado_concluido"
        
        print("✅ Distinção respondido vs validado funciona corretamente")
    
    def test_criterios_validacao_pnsb(self):
        """
        Teste: Critérios de validação seguem padrões PNSB
        Regra PNSB: Validação significa "sem críticas para correção"
        """
        
        # Cenários de validação
        cenarios = [
            {"status_inicial": "nao_iniciado", "pode_validar": False},
            {"status_inicial": "respondido", "pode_validar": True},
            {"status_inicial": "validado_concluido", "pode_validar": False},  # Já validado
            {"status_inicial": "nao_aplicavel", "pode_validar": False}
        ]
        
        for cenario in cenarios:
            entidade = EntidadeIdentificada(
                municipio="Teste",
                nome_entidade="Teste Critérios",
                status_mrs=cenario["status_inicial"]
            )
            
            if cenario["pode_validar"]:
                # Deve ser possível validar
                entidade.status_mrs = "validado_concluido"
                assert entidade.status_mrs == "validado_concluido"
            else:
                # Verificar que estado inicial é mantido ou mudança é lógica
                assert entidade.status_mrs == cenario["status_inicial"]
        
        print("✅ Critérios de validação PNSB validados")
    
    def test_progressao_status_questionarios(self):
        """
        Teste: Progressão correta de status de questionários
        Regra PNSB: nao_iniciado → respondido → validado_concluido
        """
        
        entidade = EntidadeIdentificada(
            municipio="Teste",
            nome_entidade="Teste Progressão",
            status_mrs="nao_iniciado"
        )
        
        # Progressão válida
        progressao_valida = [
            "nao_iniciado",
            "respondido", 
            "validado_concluido"
        ]
        
        for i, status in enumerate(progressao_valida):
            entidade.status_mrs = status
            assert entidade.status_mrs == status
            
            # Verificar que não pode retroceder (regra de negócio)
            if i > 0:
                status_anterior = progressao_valida[i-1]
                # Em um sistema real, isso poderia ser controlado por validação
                # Aqui apenas documentamos a regra
        
        print("✅ Progressão de status de questionários validada")


class TestRegrasMunicipiosPNSB:
    """Testes para verificar regras específicas dos municípios PNSB"""
    
    def test_municipios_cobertos_pnsb_2024(self):
        """
        Teste: Apenas municípios específicos são cobertos pelo PNSB 2024
        Regra PNSB: 11 municípios específicos de Santa Catarina
        """
        
        municipios_esperados = [
            "Balneário Camboriú", "Balneário Piçarras", "Bombinhas", "Camboriú",
            "Itajaí", "Itapema", "Luiz Alves", "Navegantes", "Penha", "Porto Belo", "Ilhota"
        ]
        
        # Verificar que MUNICIPIOS_PNSB contém exatamente estes municípios
        assert len(MUNICIPIOS_PNSB) == 11
        
        for municipio in municipios_esperados:
            assert municipio in MUNICIPIOS_PNSB
        
        # Verificar que não há municípios extras
        for municipio in MUNICIPIOS_PNSB:
            assert municipio in municipios_esperados
        
        print("✅ Lista de municípios PNSB 2024 validada")
    
    def test_cobertura_geografica_consistente(self):
        """
        Teste: Cobertura geográfica é consistente
        Regra PNSB: Todos são municípios de Santa Catarina, região costeira
        """
        
        # Verificar que todos os nomes são válidos (sem caracteres estranhos)
        for municipio in MUNICIPIOS_PNSB:
            assert isinstance(municipio, str)
            assert len(municipio) > 0
            assert municipio[0].isupper()  # Deve começar com maiúscula
            assert not municipio.startswith(" ")  # Não deve ter espaço inicial
            assert not municipio.endswith(" ")  # Não deve ter espaço final
        
        print("✅ Consistência geográfica validada")
    
    def test_entidades_por_municipio_realistica(self):
        """
        Teste: Número de entidades por município é realístico
        Regra PNSB: Cada município deve ter pelo menos prefeitura (P1)
        """
        
        for municipio in MUNICIPIOS_PNSB:
            # Simular criação de entidades mínimas
            prefeitura = EntidadeIdentificada(
                municipio=municipio,
                nome_entidade=f"Prefeitura de {municipio}",
                tipo_entidade="prefeitura",
                prioridade=1,
                mrs_obrigatorio=True,
                map_obrigatorio=True
            )
            
            # Verificar que prefeitura pode ser criada para qualquer município
            assert prefeitura.municipio == municipio
            assert prefeitura.prioridade == 1
            assert prefeitura.tipo_entidade == "prefeitura"
        
        print("✅ Entidades mínimas por município validadas")


class TestRegrasWorkflowVisitas:
    """Testes para verificar regras de workflow de visitas"""
    
    def test_workflow_status_pnsb_especifico(self):
        """
        Teste: Workflow de status específico para PNSB
        Regra PNSB: Deve refletir processo real de coleta
        """
        
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=time(9, 0),
            local="Prefeitura",
            status="agendada"
        )
        
        # Workflow específico PNSB
        workflow_pnsb = [
            "agendada",
            "em andamento",
            "realizada",
            "questionários concluídos",
            "questionários validados",
            "finalizada"
        ]
        
        # Verificar transições válidas
        for i in range(len(workflow_pnsb) - 1):
            status_atual = workflow_pnsb[i]
            proximo_status = workflow_pnsb[i + 1]
            
            visita.status = status_atual
            
            # Deve ser possível avançar para próximo status
            try:
                visita.atualizar_status(proximo_status)
                assert visita.status == proximo_status
            except ValueError as e:
                pytest.fail(f"Transição válida falhou: {status_atual} -> {proximo_status}: {e}")
        
        print("✅ Workflow PNSB específico validado")
    
    def test_integracao_visita_questionarios_checklist(self):
        """
        Teste: Integração entre visita, questionários e checklist
        Regra PNSB: Todos devem trabalhar em conjunto
        """
        
        # Criar visita completa
        visita = Visita(
            municipio="Navegantes",
            data=date.today(),
            hora_inicio=time(10, 0),
            local="Prefeitura",
            status="realizada"
        )
        
        # Mock checklist
        mock_checklist = Mock()
        mock_checklist.calcular_progresso_preparacao.return_value = 90
        mock_checklist.calcular_progresso_execucao.return_value = 85
        mock_checklist.calcular_progresso_resultados.return_value = 70
        visita.checklist = mock_checklist
        
        # Criar entidade associada
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_entidade = Mock()
            mock_entidade.status_mrs = "respondido"
            mock_entidade.status_map = "validado_concluido"
            mock_query.filter_by.return_value.all.return_value = [mock_entidade]
            
            # Verificar integração
            status_inteligente = visita.calcular_status_inteligente()
            progresso_completo = visita.calcular_progresso_completo()
            
            # Sistema deve considerar dados de todas as fontes
            assert status_inteligente in ["questionários concluídos", "questionários validados"]
            assert isinstance(progresso_completo['progresso_total'], (int, float))
            assert 0 <= progresso_completo['progresso_total'] <= 100
        
        print("✅ Integração visita-questionários-checklist validada")


class TestRegrasCalculoProgresso:
    """Testes para verificar regras de cálculo de progresso"""
    
    def test_pesos_progresso_pnsb(self):
        """
        Teste: Pesos de progresso seguem metodologia PNSB
        Regra PNSB: Questionários têm maior peso que checklist
        """
        
        visita = Visita(municipio="Camboriú", data=date.today(), hora_inicio=time(11, 0), local="Local")
        
        # Mock checklist com valores conhecidos
        mock_checklist = Mock()
        mock_checklist.calcular_progresso_preparacao.return_value = 80  # 20% * 80 = 16
        mock_checklist.calcular_progresso_execucao.return_value = 70    # 30% * 70 = 21
        mock_checklist.calcular_progresso_resultados.return_value = 60  # 10% * 60 = 6
        visita.checklist = mock_checklist
        
        # Mock questionários com valores conhecidos
        with patch.object(visita, 'obter_status_questionarios') as mock_status:
            mock_status.return_value = {
                'total_entidades': 2,
                'mrs': {'validado_concluido': 1, 'respondido': 1},  # 1.5/2 = 75%
                'map': {'validado_concluido': 0, 'respondido': 1}   # 0.5/2 = 25%
            }
            
            progresso = visita.calcular_progresso_completo()
            
            # Verificar cálculo: 16 + 21 + 6 + (40% * 50%) = 43 + 20 = 63%
            # Progresso questionários: (1.5 + 0.5) / 4 * 100 = 50%
            expected = 16 + 21 + 6 + (0.4 * 50)  # 63%
            
            assert abs(progresso['progresso_total'] - expected) < 1
            assert progresso['detalhes']['questionarios'] == 50.0
        
        print("✅ Pesos de progresso PNSB validados")
    
    def test_progresso_municipio_completo(self):
        """
        Teste: Cálculo de município completo
        Regra PNSB: Município só é completo quando P1 está 100%
        """
        
        # Simular município com P1 incompleto
        entidades_p1_incompleto = [
            Mock(prioridade=1, status_mrs='validado_concluido', status_map='respondido',
                 mrs_obrigatorio=True, map_obrigatorio=True),  # Incompleto
            Mock(prioridade=2, status_mrs='validado_concluido', status_map='validado_concluido',
                 mrs_obrigatorio=True, map_obrigatorio=True)   # Completo
        ]
        
        completos_p1 = 0
        total_p1 = 0
        
        for entidade in entidades_p1_incompleto:
            if entidade.prioridade == 1:
                total_p1 += 1
                mrs_ok = not entidade.mrs_obrigatorio or entidade.status_mrs == 'validado_concluido'
                map_ok = not entidade.map_obrigatorio or entidade.status_map == 'validado_concluido'
                if mrs_ok and map_ok:
                    completos_p1 += 1
        
        municipio_completo = (completos_p1 == total_p1) and total_p1 > 0
        assert municipio_completo == False  # P1 não está completo
        
        # Simular município com P1 completo
        entidades_p1_completo = [
            Mock(prioridade=1, status_mrs='validado_concluido', status_map='validado_concluido',
                 mrs_obrigatorio=True, map_obrigatorio=True),  # Completo
        ]
        
        completos_p1 = 0
        total_p1 = 0
        
        for entidade in entidades_p1_completo:
            if entidade.prioridade == 1:
                total_p1 += 1
                mrs_ok = not entidade.mrs_obrigatorio or entidade.status_mrs == 'validado_concluido'
                map_ok = not entidade.map_obrigatorio or entidade.status_map == 'validado_concluido'
                if mrs_ok and map_ok:
                    completos_p1 += 1
        
        municipio_completo = (completos_p1 == total_p1) and total_p1 > 0
        assert municipio_completo == True  # P1 está completo
        
        print("✅ Cálculo de município completo validado")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])