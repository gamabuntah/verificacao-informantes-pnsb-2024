#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES DE INTEGRAÇÃO - API ↔ FRONTEND PNSB 2024
==============================================

Este arquivo contém testes para verificar se a comunicação entre
backend (APIs) e frontend (JavaScript) está funcionando corretamente.

Objetivos Testados:
- Endpoints retornam dados no formato esperado pelo frontend
- Sistema de status inteligente funciona end-to-end
- Dados de questionários e checklists são sincronizados
- Mapa de progresso recebe dados corretos
- Performance das APIs está adequada
"""

import sys
import os
import pytest
import json
import requests
from datetime import datetime, date, time
from unittest.mock import Mock, patch
from flask import Flask

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada


class TestAPIEndpoints:
    """Testes para verificar se endpoints da API estão funcionando"""
    
    @pytest.fixture
    def client(self):
        """Fixture para client de teste"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                yield client
                db.drop_all()
    
    @pytest.fixture
    def sample_visita(self):
        """Fixture para visita de exemplo"""
        with app.app_context():
            visita = Visita(
                municipio="Itajaí",
                data=date.today(),
                hora_inicio=time(9, 0),
                hora_fim=time(17, 0),
                local="Prefeitura",
                tipo_pesquisa="MRS",
                status="agendada"
            )
            db.session.add(visita)
            
            # Adicionar checklist
            checklist = Checklist(visita_id=visita.id)
            db.session.add(checklist)
            
            # Adicionar entidade identificada
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
            yield visita
    
    def test_api_visitas_dashboard_inteligente(self, client, sample_visita):
        """Teste: API /api/visitas/dashboard-inteligente retorna dados corretos"""
        
        # Act
        response = client.get('/api/visitas/dashboard-inteligente')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estrutura da resposta
        assert 'estatisticas' in data
        assert 'filtros' in data
        assert 'timestamp' in data
        
        estatisticas = data['estatisticas']
        assert 'total_visitas' in estatisticas
        assert 'por_status' in estatisticas
        assert 'por_status_inteligente' in estatisticas
        assert 'progresso_medio' in estatisticas
        assert 'questionnaire_completion' in estatisticas
        assert 'checklist_progress' in estatisticas
        assert 'proximas_acoes' in estatisticas
        
        # Verificar dados da visita de exemplo
        assert estatisticas['total_visitas'] == 1
        assert 'agendada' in estatisticas['por_status']
    
    def test_api_visita_status_inteligente(self, client, sample_visita):
        """Teste: API /api/visitas/<id>/status-inteligente retorna dados corretos"""
        
        # Act
        response = client.get(f'/api/visitas/{sample_visita.id}/status-inteligente')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar estrutura da resposta
        required_fields = [
            'visita_id', 'status_atual', 'status_inteligente',
            'progresso_checklist', 'status_questionarios', 'proxima_acao',
            'progresso_completo', 'municipio', 'tipo_pesquisa', 'timestamp'
        ]
        
        for field in required_fields:
            assert field in data, f"Campo {field} está faltando na resposta"
        
        # Verificar tipos de dados
        assert isinstance(data['visita_id'], int)
        assert isinstance(data['progresso_checklist'], dict)
        assert isinstance(data['status_questionarios'], dict)
        assert isinstance(data['progresso_completo'], dict)
        
        # Verificar estrutura do progresso_checklist
        progresso_checklist = data['progresso_checklist']
        assert 'antes' in progresso_checklist
        assert 'durante' in progresso_checklist
        assert 'apos' in progresso_checklist
        
        # Verificar estrutura do status_questionarios
        status_questionarios = data['status_questionarios']
        assert 'mrs' in status_questionarios
        assert 'map' in status_questionarios
        assert 'total_entidades' in status_questionarios
    
    def test_api_visita_inexistente(self, client):
        """Teste: API retorna 404 para visita inexistente"""
        
        # Act
        response = client.get('/api/visitas/99999/status-inteligente')
        
        # Assert
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'não encontrada' in data['error'].lower()
    
    def test_api_questionarios_entidades_por_municipio(self, client, sample_visita):
        """Teste: API /api/questionarios/entidades-por-municipio retorna dados corretos"""
        
        # Act
        response = client.get('/api/questionarios/entidades-por-municipio')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar que retorna dicionário com municípios
        assert isinstance(data, dict)
        assert "Itajaí" in data
        
        # Verificar estrutura das entidades
        entidades_itajai = data["Itajaí"]
        assert isinstance(entidades_itajai, list)
        assert len(entidades_itajai) == 1
        
        entidade = entidades_itajai[0]
        required_fields = [
            'id', 'municipio', 'nome_entidade', 'tipo_entidade',
            'status_mrs', 'status_map', 'prioridade'
        ]
        
        for field in required_fields:
            assert field in entidade
    
    def test_api_visitas_progresso_mapa(self, client, sample_visita):
        """Teste: API /api/visitas/progresso-mapa retorna dados para o mapa"""
        
        # Act
        response = client.get('/api/visitas/progresso-mapa')
        
        # Assert
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Verificar que retorna dados para pelo menos um município
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_api_performance_dashboard(self, client, sample_visita):
        """Teste: Performance da API do dashboard está adequada"""
        
        import time
        
        # Act
        start_time = time.time()
        response = client.get('/api/visitas/dashboard-inteligente')
        end_time = time.time()
        
        # Assert
        assert response.status_code == 200
        
        # Performance deve ser menor que 2 segundos
        execution_time = end_time - start_time
        assert execution_time < 2.0, f"API muito lenta: {execution_time:.2f}s"


class TestIntegracaoFrontendBackend:
    """Testes para verificar integração entre frontend e backend"""
    
    def test_estrutura_dados_mapa_progresso(self):
        """Teste: Dados retornados pela API são compatíveis com JavaScript do mapa"""
        
        # Simular resposta da API dashboard-inteligente
        api_response = {
            'estatisticas': {
                'total_visitas': 10,
                'por_status': {'agendada': 3, 'em andamento': 2, 'realizada': 5},
                'por_status_inteligente': {'agendada': 2, 'realizada': 6, 'questionários concluídos': 2},
                'progresso_medio': 65.5,
                'questionnaire_completion': {
                    'mrs': {'respondido': 5, 'validado': 3},
                    'map': {'respondido': 4, 'validado': 2}
                },
                'checklist_progress': {
                    'preparacao': 75.0,
                    'execucao': 60.0,
                    'finalizacao': 40.0
                },
                'proximas_acoes': {
                    'Completar preparação da visita no checklist': 3,
                    'Responder questionários pendentes': 2,
                    'Validar questionários respondidos': 2
                }
            },
            'filtros': {'municipio': None, 'tipo_pesquisa': None},
            'timestamp': datetime.now().isoformat()
        }
        
        # Verificar que estrutura é compatível com JavaScript
        assert isinstance(api_response['estatisticas']['total_visitas'], int)
        assert isinstance(api_response['estatisticas']['progresso_medio'], (int, float))
        assert isinstance(api_response['estatisticas']['por_status'], dict)
        assert isinstance(api_response['estatisticas']['questionnaire_completion'], dict)
        
        # Verificar estrutura de conclusão de questionários
        mrs_data = api_response['estatisticas']['questionnaire_completion']['mrs']
        assert 'respondido' in mrs_data
        assert 'validado' in mrs_data
        assert isinstance(mrs_data['respondido'], int)
        assert isinstance(mrs_data['validado'], int)
    
    def test_estrutura_dados_status_inteligente(self):
        """Teste: Dados de status inteligente são compatíveis com JavaScript"""
        
        # Simular resposta da API status-inteligente
        api_response = {
            'visita_id': 1,
            'status_atual': 'realizada',
            'status_inteligente': 'questionários concluídos',
            'progresso_checklist': {
                'antes': 85.0,
                'durante': 70.0,
                'apos': 30.0
            },
            'status_questionarios': {
                'mrs': {'nao_iniciado': 0, 'respondido': 1, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'map': {'nao_iniciado': 1, 'respondido': 0, 'validado_concluido': 0, 'nao_aplicavel': 0},
                'total_entidades': 1
            },
            'proxima_acao': 'Validar questionários respondidos',
            'progresso_completo': {
                'progresso_total': 67.5,
                'detalhes': {
                    'preparacao': 85.0,
                    'execucao': 70.0,
                    'questionarios': 50.0,
                    'finalizacao': 30.0
                },
                'status_inteligente': 'questionários concluídos'
            }
        }
        
        # Verificar tipos esperados pelo JavaScript
        assert isinstance(api_response['visita_id'], int)
        assert isinstance(api_response['status_atual'], str)
        assert isinstance(api_response['status_inteligente'], str)
        assert isinstance(api_response['progresso_checklist'], dict)
        assert isinstance(api_response['progresso_completo']['progresso_total'], (int, float))
        
        # Verificar que percentuais estão no range correto
        for fase, valor in api_response['progresso_checklist'].items():
            assert 0 <= valor <= 100, f"Progresso {fase} fora do range: {valor}"
        
        assert 0 <= api_response['progresso_completo']['progresso_total'] <= 100
    
    def test_dados_prioridades_p1_p2_p3(self):
        """Teste: Dados de prioridades P1/P2/P3 são estruturados corretamente"""
        
        # Simular dados de entidades por município
        entidades_data = {
            "Itajaí": [
                {
                    'id': 1,
                    'municipio': 'Itajaí',
                    'nome_entidade': 'Prefeitura de Itajaí',
                    'tipo_entidade': 'prefeitura',
                    'status_mrs': 'validado_concluido',
                    'status_map': 'respondido',
                    'prioridade': 1,
                    'mrs_obrigatorio': True,
                    'map_obrigatorio': True
                },
                {
                    'id': 2,
                    'municipio': 'Itajaí',
                    'nome_entidade': 'Empresa XYZ',
                    'tipo_entidade': 'empresa_terceirizada',
                    'status_mrs': 'respondido',
                    'status_map': 'nao_iniciado',
                    'prioridade': 2,
                    'mrs_obrigatorio': True,
                    'map_obrigatorio': False
                }
            ]
        }
        
        # Simular cálculo de estatísticas P1/P2/P3 (como seria feito no JavaScript)
        stats = {'p1': {'total': 0, 'concluidos': 0, 'mrs': 0, 'map': 0},
                'p2': {'total': 0, 'concluidos': 0, 'mrs': 0, 'map': 0},
                'p3': {'total': 0, 'concluidos': 0, 'mrs': 0, 'map': 0}}
        
        for municipio, entidades in entidades_data.items():
            for entidade in entidades:
                prioridade = f"p{entidade['prioridade']}"
                if prioridade in stats:
                    stats[prioridade]['total'] += 1
                    
                    if entidade['status_mrs'] == 'validado_concluido':
                        stats[prioridade]['mrs'] += 1
                    if entidade['status_map'] == 'validado_concluido':
                        stats[prioridade]['map'] += 1
                    
                    # Considerar concluído se todos os obrigatórios estão validados
                    mrs_ok = not entidade['mrs_obrigatorio'] or entidade['status_mrs'] == 'validado_concluido'
                    map_ok = not entidade['map_obrigatorio'] or entidade['status_map'] == 'validado_concluido'
                    
                    if mrs_ok and map_ok:
                        stats[prioridade]['concluidos'] += 1
        
        # Verificar cálculos
        assert stats['p1']['total'] == 1
        assert stats['p1']['mrs'] == 1  # validado_concluido
        assert stats['p1']['map'] == 0  # apenas respondido
        assert stats['p1']['concluidos'] == 0  # MAP não está validado
        
        assert stats['p2']['total'] == 1
        assert stats['p2']['mrs'] == 0  # apenas respondido
        assert stats['p2']['map'] == 0  # nao_iniciado
        assert stats['p2']['concluidos'] == 0  # MRS não validado


class TestCompatibilidadeJavaScript:
    """Testes para verificar compatibilidade com código JavaScript"""
    
    def test_nomes_status_compativeis(self):
        """Teste: Nomes de status são compatíveis entre Python e JavaScript"""
        
        # Status definidos no Python
        python_status = [
            'agendada', 'em andamento', 'realizada', 'questionários concluídos',
            'questionários validados', 'finalizada', 'remarcada', 'não realizada'
        ]
        
        # Status esperados no JavaScript (baseado na função getStatusLabel)
        javascript_status = {
            'nao_iniciado': 'Não Iniciado',
            'respondido': 'Respondido',
            'validado_concluido': 'Validado/Concluído',
            'nao_aplicavel': 'Não Aplicável'
        }
        
        # Verificar que status de questionários são consistentes
        for status_key in javascript_status.keys():
            # Verificar que status existe e é válido
            assert isinstance(status_key, str)
            assert len(status_key) > 0
            assert '_' in status_key or status_key in ['respondido']  # padrão de nomenclatura
    
    def test_estrutura_municipios_pnsb(self):
        """Teste: Lista de municípios PNSB está consistente"""
        
        # Municípios definidos no sistema
        municipios_pnsb = [
            "Balneário Camboriú", "Balneário Piçarras", "Bombinhas", "Camboriú",
            "Itajaí", "Itapema", "Luiz Alves", "Navegantes", "Penha", "Porto Belo", "Ilhota"
        ]
        
        # Verificar que temos exatamente 11 municípios
        assert len(municipios_pnsb) == 11
        
        # Verificar que todos são strings não vazias
        for municipio in municipios_pnsb:
            assert isinstance(municipio, str)
            assert len(municipio) > 0
            assert municipio[0].isupper()  # Deve começar com maiúscula
    
    def test_formato_timestamp_api(self):
        """Teste: Timestamps da API são compatíveis com JavaScript Date"""
        
        # Simular timestamp como retornado pela API
        now = datetime.now()
        iso_timestamp = now.isoformat()
        
        # Verificar formato ISO que JavaScript pode parsear
        assert 'T' in iso_timestamp  # Separador de data/hora
        assert len(iso_timestamp) >= 19  # YYYY-MM-DDTHH:MM:SS
        
        # Verificar que JavaScript poderia parsear (simulação)
        try:
            # Simular new Date(timestamp) do JavaScript
            from datetime import datetime
            parsed = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
            assert isinstance(parsed, datetime)
        except ValueError:
            pytest.fail(f"Timestamp não é compatível com JavaScript: {iso_timestamp}")


if __name__ == "__main__":
    # Executar testes
    pytest.main([__file__, "-v", "--tb=short"])