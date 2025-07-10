import pytest
import os
import tempfile
from gestao_visitas.app_factory import create_app
from gestao_visitas.db import db
from gestao_visitas.models.agendamento import Visita
from gestao_visitas.models.checklist import Checklist
from gestao_visitas.models.contatos import Contato

@pytest.fixture
def app():
    """Cria aplicação Flask para testes"""
    
    # Configurar variáveis de ambiente para testes
    os.environ['SECRET_KEY'] = 'test_secret_key'
    os.environ['GOOGLE_MAPS_API_KEY'] = 'test_maps_key'
    os.environ['GOOGLE_GEMINI_API_KEY'] = 'test_gemini_key'
    
    # Criar aplicação para testes
    app = create_app('testing')
    
    with app.app_context():
        yield app

@pytest.fixture
def client(app):
    """Cliente de teste Flask"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Runner CLI de teste"""
    return app.test_cli_runner()

@pytest.fixture
def db_session(app):
    """Sessão de banco de dados para testes"""
    with app.app_context():
        db.create_all()
        yield db.session
        db.session.remove()
        db.drop_all()

@pytest.fixture
def sample_visita(db_session):
    """Cria visita de exemplo para testes"""
    from datetime import datetime, time, date
    
    visita = Visita(
        municipio="Itajaí",
        data=date(2024, 12, 25),
        hora_inicio=time(9, 0),
        hora_fim=time(10, 0),
        informante="João Silva",
        tipo_pesquisa="MRS",
        tipo_informante="prefeitura",
        status="agendada",
        observacoes="Teste de visita"
    )
    
    db_session.add(visita)
    db_session.commit()
    
    return visita

@pytest.fixture
def sample_checklist(db_session, sample_visita):
    """Cria checklist de exemplo para testes"""
    checklist = Checklist(visita_id=sample_visita.id)
    
    db_session.add(checklist)
    db_session.commit()
    
    return checklist

@pytest.fixture
def sample_contato(db_session):
    """Cria contato de exemplo para testes"""
    contato = Contato(
        municipio="Itajaí",
        tipo_pesquisa="MRS",
        tipo_entidade="prefeitura",
        local_mais_provavel="Secretaria de Meio Ambiente",
        responsavel_mais_provavel="Maria Santos",
        endereco_mais_provavel="Rua das Flores, 123",
        contato_mais_provavel="(47) 99999-9999",
        horario_mais_provavel="8h às 17h"
    )
    
    db_session.add(contato)
    db_session.commit()
    
    return contato

@pytest.fixture
def auth_headers():
    """Headers de autenticação para testes de API"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }