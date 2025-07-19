import pytest
from datetime import datetime, date, time
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.contatos import Contato

class TestVisitaModel:
    """Testes para o modelo Visita"""
    
    def test_criar_visita(self, db_session):
        """Testa criação de visita"""
        visita = Visita(
            municipio="Itajaí",
            data=date(2024, 12, 25),
            hora_inicio=time(9, 0),
            hora_fim=time(10, 0),
            local="João Silva",
            tipo_pesquisa="MRS",
            status="agendada"
        )
        
        db_session.add(visita)
        db_session.commit()
        
        assert visita.id is not None
        assert visita.municipio == "Itajaí"
        assert visita.status == "agendada"
        assert visita.data_criacao is not None
    
    def test_visita_to_dict(self, sample_visita):
        """Testa conversão para dicionário"""
        visita_dict = sample_visita.to_dict()
        
        assert isinstance(visita_dict, dict)
        assert visita_dict['municipio'] == "Itajaí"
        assert visita_dict['local'] == "João Silva"
        assert 'data' in visita_dict
    
    def test_atualizar_status_visita(self, sample_visita, db_session):
        """Testa atualização de status"""
        # Status válido
        sample_visita.atualizar_status('em preparação')
        assert sample_visita.status == 'em preparação'
        
        # Status inválido
        with pytest.raises(ValueError):
            sample_visita.atualizar_status('status_inexistente')
    
    def test_pode_ser_editada(self, sample_visita):
        """Testa se visita pode ser editada"""
        assert sample_visita.pode_ser_editada() == True
        
        sample_visita.status = 'finalizada'
        assert sample_visita.pode_ser_editada() == False
    
    def test_pode_ser_excluida(self, sample_visita):
        """Testa se visita pode ser excluída"""
        assert sample_visita.pode_ser_excluida() == True
        
        sample_visita.status = 'em execução'
        assert sample_visita.pode_ser_excluida() == False

class TestChecklistModel:
    """Testes para o modelo Checklist"""
    
    def test_criar_checklist(self, db_session, sample_visita):
        """Testa criação de checklist"""
        checklist = Checklist(visita_id=sample_visita.id)
        
        db_session.add(checklist)
        db_session.commit()
        
        assert checklist.id is not None
        assert checklist.visita_id == sample_visita.id
    
    def test_checklist_to_dict(self, sample_checklist):
        """Testa conversão para dicionário"""
        checklist_dict = sample_checklist.to_dict()
        
        assert isinstance(checklist_dict, dict)
        assert 'visita_id' in checklist_dict
        assert 'data_criacao' in checklist_dict
    
    def test_atualizar_status_item(self, sample_checklist, db_session):
        """Testa atualização de status de item"""
        sample_checklist.atualizar_status('materiais', 'cracha_ibge', True)
        
        db_session.commit()
        
        assert sample_checklist.cracha_ibge == True
    
    def test_progresso_geral(self, sample_checklist):
        """Testa cálculo de progresso geral"""
        progresso = sample_checklist.progresso_geral()
        
        assert isinstance(progresso, dict)
        assert 'total_itens' in progresso
        assert 'itens_concluidos' in progresso
        assert 'percentual' in progresso

class TestContatoModel:
    """Testes para o modelo Contato"""
    
    def test_criar_contato(self, db_session):
        """Testa criação de contato"""
        contato = Contato(
            municipio="Itajaí",
            tipo_pesquisa="MRS",
            tipo_entidade="prefeitura"
        )
        
        db_session.add(contato)
        db_session.commit()
        
        assert contato.id is not None
        assert contato.municipio == "Itajaí"
        assert contato.tipo_pesquisa == "MRS"
    
    def test_contato_to_dict(self, sample_contato):
        """Testa conversão para dicionário"""
        contato_dict = sample_contato.to_dict()
        
        assert isinstance(contato_dict, dict)
        assert contato_dict['municipio'] == "Itajaí"
        assert contato_dict['tipo_pesquisa'] == "MRS"
    
    def test_get_melhor_opcao(self, sample_contato):
        """Testa obtenção da melhor opção"""
        melhor_local = sample_contato.get_melhor_opcao('local')
        
        assert melhor_local == "Secretaria de Meio Ambiente"
    
    def test_atualizar_campo_ia(self, sample_contato, db_session):
        """Testa atualização de campo por IA"""
        sample_contato.atualizar_campo_ia('local', 'chatgpt', 'Novo Local ChatGPT')
        
        db_session.commit()
        
        assert sample_contato.local_chatgpt == 'Novo Local ChatGPT'