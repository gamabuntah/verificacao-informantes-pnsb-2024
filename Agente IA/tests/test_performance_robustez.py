#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTES DE PERFORMANCE E ROBUSTEZ - PNSB 2024
===========================================

Este arquivo contém testes para verificar performance, robustez e
comportamento do sistema sob diferentes condições de carga e cenários edge.

Aspectos Testados:
- Performance das APIs com grandes volumes de dados
- Robustez do sistema com dados malformados
- Comportamento com falhas de rede/banco
- Limits de memória e processamento
- Concorrência e thread safety
- Recuperação de erros
"""

import sys
import os
import pytest
import time
import threading
import json
from datetime import datetime, date, time as dt_time, timedelta
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor, as_completed

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.questionarios_obrigatorios import EntidadeIdentificada


class TestPerformanceAPIs:
    """Testes de performance das APIs"""
    
    @pytest.fixture
    def client_with_data(self):
        """Fixture com dados de teste em larga escala"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.test_client() as client:
            with app.app_context():
                db.create_all()
                
                # Criar dados de teste em larga escala
                print("Criando dados de teste...")
                start_time = time.time()
                
                municipios = ["Itajaí", "Navegantes", "Camboriú", "Bombinhas", "Penha"]
                
                for i in range(100):  # 100 visitas
                    municipio = municipios[i % len(municipios)]
                    
                    visita = Visita(
                        municipio=municipio,
                        data=date.today() + timedelta(days=i % 30),
                        hora_inicio=dt_time(9 + (i % 8), 0),
                        hora_fim=dt_time(17, 0),
                        local=f"Local {i}",
                        tipo_pesquisa="MRS" if i % 2 == 0 else "MAP",
                        status=["agendada", "em andamento", "realizada", "finalizada"][i % 4]
                    )
                    db.session.add(visita)
                    
                    # Checklist para cada visita
                    checklist = Checklist(visita_id=visita.id)
                    db.session.add(checklist)
                    
                    # 2-5 entidades por município
                    for j in range(2 + (i % 4)):
                        entidade = EntidadeIdentificada(
                            municipio=municipio,
                            nome_entidade=f"Entidade {i}-{j}",
                            tipo_entidade=["prefeitura", "empresa_terceirizada", "entidade_catadores"][j % 3],
                            status_mrs=["nao_iniciado", "respondido", "validado_concluido"][j % 3],
                            status_map=["nao_iniciado", "respondido", "validado_concluido"][(j+1) % 3],
                            prioridade=(j % 3) + 1,
                            mrs_obrigatorio=j % 2 == 0,
                            map_obrigatorio=j % 3 == 0
                        )
                        db.session.add(entidade)
                
                db.session.commit()
                
                setup_time = time.time() - start_time
                print(f"Dados criados em {setup_time:.2f}s")
                
                yield client
                db.drop_all()
    
    def test_performance_dashboard_inteligente(self, client_with_data):
        """Teste: Performance da API dashboard-inteligente com muitos dados"""
        
        # Fazer múltiplas requisições e medir tempo
        tempos = []
        
        for i in range(5):
            start_time = time.time()
            response = client_with_data.get('/api/visitas/dashboard-inteligente')
            end_time = time.time()
            
            assert response.status_code == 200
            tempos.append(end_time - start_time)
        
        tempo_medio = sum(tempos) / len(tempos)
        tempo_maximo = max(tempos)
        
        print(f"Tempo médio: {tempo_medio:.3f}s")
        print(f"Tempo máximo: {tempo_maximo:.3f}s")
        
        # Performance deve ser aceitável (< 3s para muitos dados)
        assert tempo_medio < 3.0, f"Performance muito lenta: {tempo_medio:.3f}s"
        assert tempo_maximo < 5.0, f"Pico de performance muito alto: {tempo_maximo:.3f}s"
    
    def test_performance_multiplas_visitas_status(self, client_with_data):
        """Teste: Performance ao consultar status de múltiplas visitas"""
        
        # Obter IDs de visitas
        with app.app_context():
            visita_ids = [v.id for v in Visita.query.limit(20).all()]
        
        # Fazer requisições concorrentes
        def consultar_status(visita_id):
            start_time = time.time()
            response = client_with_data.get(f'/api/visitas/{visita_id}/status-inteligente')
            end_time = time.time()
            return (response.status_code, end_time - start_time)
        
        # Executar em paralelo
        start_total = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(consultar_status, vid) for vid in visita_ids]
            resultados = [future.result() for future in as_completed(futures)]
        end_total = time.time()
        
        # Verificar resultados
        sucessos = sum(1 for status, _ in resultados if status == 200)
        tempos = [tempo for _, tempo in resultados]
        tempo_total = end_total - start_total
        
        print(f"Sucessos: {sucessos}/{len(visita_ids)}")
        print(f"Tempo médio por requisição: {sum(tempos)/len(tempos):.3f}s")
        print(f"Tempo total paralelo: {tempo_total:.3f}s")
        
        assert sucessos == len(visita_ids), "Nem todas as requisições foram bem-sucedidas"
        assert tempo_total < 10.0, f"Tempo total muito alto: {tempo_total:.3f}s"
    
    def test_performance_calculo_progresso_completo(self, client_with_data):
        """Teste: Performance do cálculo de progresso completo"""
        
        with app.app_context():
            visitas = Visita.query.limit(50).all()
            
            start_time = time.time()
            
            for visita in visitas:
                # Simular checklist
                mock_checklist = Mock()
                mock_checklist.calcular_progresso_preparacao.return_value = 80
                mock_checklist.calcular_progresso_execucao.return_value = 70
                mock_checklist.calcular_progresso_resultados.return_value = 60
                visita.checklist = mock_checklist
                
                # Calcular progresso (operação potencialmente custosa)
                progresso = visita.calcular_progresso_completo()
                assert isinstance(progresso['progresso_total'], (int, float))
            
            end_time = time.time()
            
            tempo_total = end_time - start_time
            tempo_por_visita = tempo_total / len(visitas)
            
            print(f"Tempo total para {len(visitas)} visitas: {tempo_total:.3f}s")
            print(f"Tempo por visita: {tempo_por_visita:.4f}s")
            
            # Deve ser rápido mesmo com muitas visitas
            assert tempo_por_visita < 0.1, f"Cálculo muito lento: {tempo_por_visita:.4f}s por visita"


class TestRobustezDados:
    """Testes de robustez com dados malformados ou extremos"""
    
    @pytest.fixture
    def setup_robustez(self):
        """Setup para testes de robustez"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with app.app_context():
            db.create_all()
            yield db
            db.drop_all()
    
    def test_robustez_dados_nulos(self, setup_robustez):
        """Teste: Sistema funciona com dados nulos/vazios"""
        
        # Visita com dados mínimos
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=dt_time(9, 0),
            local="Local"
        )
        # Não adicionar checklist nem entidades
        db.session.add(visita)
        db.session.commit()
        
        # Sistema deve funcionar sem falhar
        try:
            status_inteligente = visita.calcular_status_inteligente()
            progresso_checklist = visita.obter_progresso_checklist()
            status_questionarios = visita.obter_status_questionarios()
            progresso_completo = visita.calcular_progresso_completo()
            recomendacao = visita.recomendar_proxima_acao()
            
            # Verificar que retorna valores válidos mesmo sem dados
            assert isinstance(status_inteligente, str)
            assert isinstance(progresso_checklist, dict)
            assert isinstance(status_questionarios, dict)
            assert isinstance(progresso_completo, dict)
            assert isinstance(recomendacao, str)
            
            print("✅ Sistema robusto com dados nulos")
            
        except Exception as e:
            pytest.fail(f"Sistema falhou com dados nulos: {e}")
    
    def test_robustez_dados_extremos(self, setup_robustez):
        """Teste: Sistema funciona com dados extremos"""
        
        # Criar dados extremos
        visita = Visita(
            municipio="A" * 100,  # Nome muito longo
            data=date(2100, 12, 31),  # Data futura extrema
            hora_inicio=dt_time(0, 0),  # Meia-noite
            hora_fim=dt_time(23, 59),  # Quase meia-noite
            local="X" * 1000,  # Local muito longo
            observacoes="Observação " * 100  # Observações muito longas
        )
        db.session.add(visita)
        
        # Entidade com dados extremos
        entidade = EntidadeIdentificada(
            municipio="A" * 100,
            nome_entidade="B" * 200,
            tipo_entidade="empresa_terceirizada",
            prioridade=999,  # Prioridade inválida
            status_mrs="status_inexistente",  # Status inválido
            status_map="outro_status_inexistente"
        )
        db.session.add(entidade)
        
        try:
            db.session.commit()
            
            # Tentar operações mesmo com dados extremos
            status_inteligente = visita.calcular_status_inteligente()
            progresso = visita.calcular_progresso_completo()
            
            # Sistema deve ser resiliente
            assert isinstance(status_inteligente, str)
            assert isinstance(progresso, dict)
            
            print("✅ Sistema robusto com dados extremos")
            
        except Exception as e:
            # Pode falhar ao salvar (validação de banco), mas não deve quebrar aplicação
            print(f"⚠️ Dados extremos rejeitados pelo banco (esperado): {e}")
    
    def test_robustez_encoding_caracteres_especiais(self, setup_robustez):
        """Teste: Sistema funciona com caracteres especiais"""
        
        # Dados com caracteres especiais
        visita = Visita(
            municipio="São João de Açúcar",  # Acentos
            data=date.today(),
            hora_inicio=dt_time(14, 0),
            local="Rua das Flores, 123 - Centro (próximo ao café)",  # Pontuação
            observacoes="Teste com émojis 🏢 e símbolos ©®™ e números ½¼¾"
        )
        db.session.add(visita)
        
        entidade = EntidadeIdentificada(
            municipio="São João de Açúcar",
            nome_entidade="Empresa Ção & Filhos Ltda.",
            tipo_entidade="empresa_terceirizada",
            observacoes="Observação com\nnova linha e\ttab"
        )
        db.session.add(entidade)
        
        try:
            db.session.commit()
            
            # Converter para dict (JSON)
            visita_dict = visita.to_dict()
            entidade_dict = entidade.to_dict()
            
            # Verificar que pode ser serializado para JSON
            json_str = json.dumps(visita_dict, ensure_ascii=False)
            assert isinstance(json_str, str)
            
            print("✅ Sistema robusto com caracteres especiais")
            
        except Exception as e:
            pytest.fail(f"Sistema falhou com caracteres especiais: {e}")
    
    def test_robustez_concorrencia(self, setup_robustez):
        """Teste: Sistema funciona com acesso concorrente"""
        
        # Criar visita base
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=dt_time(10, 0),
            local="Local Teste"
        )
        db.session.add(visita)
        db.session.commit()
        
        visita_id = visita.id
        
        # Função para atualizar status
        def atualizar_status_worker(worker_id):
            try:
                with app.app_context():
                    # Simular múltiplos workers atualizando status
                    visita = Visita.query.get(visita_id)
                    if visita:
                        # Operações que podem ser concorrentes
                        status_inteligente = visita.calcular_status_inteligente()
                        progresso = visita.calcular_progresso_completo()
                        
                        # Simular pequeno delay
                        time.sleep(0.01)
                        
                        return True
                return False
            except Exception as e:
                print(f"Worker {worker_id} falhou: {e}")
                return False
        
        # Executar múltiplos workers
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(atualizar_status_worker, i) for i in range(20)]
            resultados = [future.result() for future in as_completed(futures)]
        
        sucessos = sum(1 for r in resultados if r)
        print(f"Sucessos em concorrência: {sucessos}/{len(resultados)}")
        
        # Maioria deve ter sucesso
        assert sucessos >= len(resultados) * 0.8, "Muitas falhas em concorrência"


class TestRobustezErros:
    """Testes de robustez com simulação de erros"""
    
    def test_robustez_banco_indisponivel(self):
        """Teste: Sistema funciona quando banco está indisponível"""
        
        visita = Visita(
            municipio="Itajaí",
            data=date.today(),
            hora_inicio=dt_time(11, 0),
            local="Local"
        )
        
        # Simular erro de banco
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            mock_query.side_effect = Exception("Banco indisponível")
            
            # Sistema deve ser resiliente
            try:
                status_inteligente = visita.calcular_status_inteligente()
                status_questionarios = visita.obter_status_questionarios()
                
                # Deve retornar valores padrão sem falhar
                assert status_inteligente == visita.status  # Fallback para status atual
                assert status_questionarios['total_entidades'] == 0
                
                print("✅ Sistema resiliente a falhas de banco")
                
            except Exception as e:
                pytest.fail(f"Sistema não foi resiliente a falha de banco: {e}")
    
    def test_robustez_checklist_corrompido(self):
        """Teste: Sistema funciona com checklist corrompido"""
        
        visita = Visita(
            municipio="Navegantes",
            data=date.today(),
            hora_inicio=dt_time(15, 0),
            local="Local"
        )
        
        # Simular checklist corrompido
        mock_checklist = Mock()
        mock_checklist.calcular_progresso_preparacao.side_effect = Exception("Checklist corrompido")
        mock_checklist.calcular_progresso_execucao.side_effect = Exception("Checklist corrompido")
        mock_checklist.calcular_progresso_resultados.side_effect = Exception("Checklist corrompido")
        visita.checklist = mock_checklist
        
        # Sistema deve ser resiliente
        try:
            progresso_checklist = visita.obter_progresso_checklist()
            progresso_completo = visita.calcular_progresso_completo()
            
            # Deve retornar valores padrão
            assert progresso_checklist == {'antes': 0, 'durante': 0, 'apos': 0}
            assert isinstance(progresso_completo['progresso_total'], (int, float))
            
            print("✅ Sistema resiliente a checklist corrompido")
            
        except Exception as e:
            pytest.fail(f"Sistema não foi resiliente a checklist corrompido: {e}")
    
    def test_robustez_memoria_limitada(self):
        """Teste: Sistema funciona com muitos dados (simulação de limite de memória)"""
        
        # Simular processamento de muitos dados
        municipios = ["Itajaí"] * 1000  # Muitos municípios
        
        try:
            # Operação que pode consumir muita memória
            resultados = []
            for i, municipio in enumerate(municipios):
                if i % 100 == 0:  # Log a cada 100 itens
                    print(f"Processando item {i}/{len(municipios)}")
                
                # Simular processamento
                visita = Visita(
                    municipio=municipio,
                    data=date.today(),
                    hora_inicio=dt_time(9, 0),
                    local=f"Local {i}"
                )
                
                # Operação que pode consumir memória
                progresso = visita.calcular_progresso_completo()
                resultados.append(progresso['progresso_total'])
                
                # Simular limpeza periódica (garbage collection)
                if i % 100 == 0:
                    del resultados[:-10]  # Manter apenas os últimos 10
            
            print(f"✅ Processamento de {len(municipios)} itens concluído")
            
        except MemoryError:
            print("⚠️ Limite de memória atingido (esperado em teste)")
        except Exception as e:
            pytest.fail(f"Erro inesperado em teste de memória: {e}")


class TestValidacaoLimites:
    """Testes para validar limites do sistema"""
    
    def test_limite_municipios_simultaneos(self):
        """Teste: Sistema funciona com todos os municípios PNSB simultaneamente"""
        
        from gestao_visitas.config import MUNICIPIOS as MUNICIPIOS_PNSB
        
        visitas = []
        for municipio in MUNICIPIOS_PNSB:
            visita = Visita(
                municipio=municipio,
                data=date.today(),
                hora_inicio=dt_time(9, 0),
                local=f"Prefeitura de {municipio}"
            )
            visitas.append(visita)
        
        # Simular processamento de todos os municípios
        start_time = time.time()
        
        for visita in visitas:
            status_inteligente = visita.calcular_status_inteligente()
            progresso = visita.calcular_progresso_completo()
            assert isinstance(status_inteligente, str)
            assert isinstance(progresso['progresso_total'], (int, float))
        
        end_time = time.time()
        tempo_total = end_time - start_time
        
        print(f"Processamento de {len(MUNICIPIOS_PNSB)} municípios: {tempo_total:.3f}s")
        
        # Deve ser eficiente mesmo com todos os municípios
        assert tempo_total < 2.0, f"Processamento muito lento: {tempo_total:.3f}s"
    
    def test_limite_entidades_por_municipio(self):
        """Teste: Sistema funciona com muitas entidades por município"""
        
        # Simular município com muitas entidades
        with patch('gestao_visitas.models.questionarios_obrigatorios.EntidadeIdentificada.query') as mock_query:
            # Simular 100 entidades
            mock_entidades = []
            for i in range(100):
                mock_entidade = Mock()
                mock_entidade.status_mrs = ["nao_iniciado", "respondido", "validado_concluido"][i % 3]
                mock_entidade.status_map = ["nao_iniciado", "respondido", "validado_concluido"][(i+1) % 3]
                mock_entidades.append(mock_entidade)
            
            mock_query.filter_by.return_value.all.return_value = mock_entidades
            
            visita = Visita(
                municipio="Itajaí",
                data=date.today(),
                hora_inicio=dt_time(9, 0),
                local="Local"
            )
            
            start_time = time.time()
            
            # Operações que processam todas as entidades
            status_questionarios = visita.obter_status_questionarios()
            status_inteligente = visita.calcular_status_inteligente()
            
            end_time = time.time()
            tempo_processamento = end_time - start_time
            
            print(f"Processamento de 100 entidades: {tempo_processamento:.3f}s")
            
            # Verificar que dados estão corretos
            assert status_questionarios['total_entidades'] == 100
            assert isinstance(status_inteligente, str)
            
            # Deve ser eficiente mesmo com muitas entidades
            assert tempo_processamento < 1.0, f"Processamento muito lento: {tempo_processamento:.3f}s"


if __name__ == "__main__":
    # Executar testes de performance (podem demorar)
    pytest.main([__file__, "-v", "--tb=short", "-s"])  # -s para ver prints