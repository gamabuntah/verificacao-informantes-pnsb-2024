import pytest
import json
from datetime import date, datetime

class TestVisitasAPI:
    """Testes para API de visitas"""
    
    def test_get_visitas_empty(self, client, db_session):
        """Testa busca de visitas em base vazia"""
        response = client.get('/api/visitas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data'] == []
    
    def test_get_visitas_with_data(self, client, sample_visita):
        """Testa busca de visitas com dados"""
        response = client.get('/api/visitas')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']) == 1
        assert data['data'][0]['municipio'] == 'Itajaí'
    
    def test_criar_visita_sucesso(self, client, db_session, auth_headers):
        """Testa criação de visita com sucesso"""
        visita_data = {
            'municipio': 'Itajaí',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'hora_fim': '10:00',
            'informante': 'João Silva',
            'tipo_pesquisa': 'MRS',
            'tipo_informante': 'prefeitura',
            'observacoes': 'Teste'
        }
        
        response = client.post('/api/visitas', 
                             data=json.dumps(visita_data),
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['municipio'] == 'Itajaí'
    
    def test_criar_visita_dados_invalidos(self, client, auth_headers):
        """Testa criação de visita com dados inválidos"""
        visita_data = {
            'municipio': 'Município Inexistente',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'informante': 'João Silva',
            'tipo_pesquisa': 'TIPO_INVALIDO'
        }
        
        response = client.post('/api/visitas',
                             data=json.dumps(visita_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_criar_visita_campos_obrigatorios(self, client, auth_headers):
        """Testa criação de visita sem campos obrigatórios"""
        visita_data = {
            'municipio': 'Itajaí'
            # Faltam campos obrigatórios
        }
        
        response = client.post('/api/visitas',
                             data=json.dumps(visita_data),
                             headers=auth_headers)
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] == False
        assert 'obrigatórios' in data['error']
    
    def test_get_visita_inexistente(self, client):
        """Testa busca de visita inexistente"""
        response = client.get('/api/visitas/999')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
    
    def test_atualizar_visita_sucesso(self, client, sample_visita, auth_headers):
        """Testa atualização de visita com sucesso"""
        visita_data = {
            'municipio': 'Navegantes',
            'data': '2024-12-26',
            'hora_inicio': '10:00',
            'hora_fim': '11:00',
            'informante': 'Maria Silva',
            'tipo_pesquisa': 'MAP',
            'observacoes': 'Atualizado'
        }
        
        response = client.put(f'/api/visitas/{sample_visita.id}',
                            data=json.dumps(visita_data),
                            headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['municipio'] == 'Navegantes'
    
    def test_atualizar_status_visita(self, client, sample_visita, auth_headers):
        """Testa atualização de status de visita"""
        status_data = {'status': 'em preparação'}
        
        response = client.post(f'/api/visitas/{sample_visita.id}/status',
                             data=json.dumps(status_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['status'] == 'em preparação'
    
    def test_excluir_visita_sucesso(self, client, sample_visita):
        """Testa exclusão de visita com sucesso"""
        response = client.delete(f'/api/visitas/{sample_visita.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

class TestChecklistAPI:
    """Testes para API de checklist"""
    
    def test_get_checklist_inexistente(self, client, sample_visita):
        """Testa busca de checklist que será criado automaticamente"""
        response = client.get(f'/api/checklist/{sample_visita.id}')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data']['visita_id'] == sample_visita.id
    
    def test_salvar_checklist(self, client, sample_visita, auth_headers):
        """Testa salvamento de checklist"""
        checklist_data = {
            'etapa': 'Antes da Visita',
            'dados': {
                'cracha_ibge': True,
                'recibo_entrega': False,
                'observacoes_0': 'Observação de teste'
            }
        }
        
        response = client.post(f'/api/checklist/{sample_visita.id}',
                             data=json.dumps(checklist_data),
                             headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True

class TestContatosAPI:
    """Testes para API de contatos"""
    
    def test_listar_contatos_empty(self, client, db_session):
        """Testa listagem de contatos em base vazia"""
        response = client.get('/api/contatos')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert data['data'] == []
    
    def test_listar_contatos_with_data(self, client, sample_contato):
        """Testa listagem de contatos com dados"""
        response = client.get('/api/contatos')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert len(data['data']) == 1
        assert data['data'][0]['municipio'] == 'Itajaí'

class TestRelatoriosAPI:
    """Testes para API de relatórios"""
    
    def test_relatorio_hoje(self, client, sample_visita):
        """Testa geração de relatório do dia"""
        response = client.get('/api/relatorios/hoje')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] == True
        assert 'data' in data

class TestErrorHandling:
    """Testes para tratamento de erros"""
    
    def test_404_endpoint_inexistente(self, client):
        """Testa endpoint inexistente"""
        response = client.get('/api/endpoint_inexistente')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['type'] == 'not_found'
    
    def test_405_metodo_nao_permitido(self, client):
        """Testa método não permitido"""
        response = client.patch('/api/visitas')  # PATCH não é permitido
        
        assert response.status_code == 405
        data = json.loads(response.data)
        assert data['success'] == False
        assert data['type'] == 'method_not_allowed'
    
    def test_400_json_invalido(self, client, auth_headers):
        """Testa JSON inválido"""
        headers = auth_headers.copy()
        
        response = client.post('/api/visitas',
                             data="invalid json",
                             headers=headers)
        
        assert response.status_code == 400