import pytest
from datetime import datetime, date
from gestao_visitas.utils.validators import (
    InputValidator, 
    ValidationError, 
    VisitaValidator
)

class TestInputValidator:
    """Testes para InputValidator"""
    
    def test_validate_required_fields_sucesso(self):
        """Testa validação de campos obrigatórios com sucesso"""
        data = {'nome': 'João', 'email': 'joao@email.com'}
        required_fields = ['nome', 'email']
        
        # Não deve levantar exceção
        InputValidator.validate_required_fields(data, required_fields)
    
    def test_validate_required_fields_falha(self):
        """Testa validação de campos obrigatórios com falha"""
        data = {'nome': 'João'}
        required_fields = ['nome', 'email']
        
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_required_fields(data, required_fields)
        
        assert 'email' in str(exc_info.value)
    
    def test_validate_municipio_valido(self):
        """Testa validação de município válido"""
        municipio = InputValidator.validate_municipio('Itajaí')
        assert municipio == 'Itajaí'
    
    def test_validate_municipio_invalido(self):
        """Testa validação de município inválido"""
        with pytest.raises(ValidationError):
            InputValidator.validate_municipio('Município Inexistente')
    
    def test_validate_date_valida(self):
        """Testa validação de data válida"""
        # Data futura
        data_str = '2024-12-25'
        data_obj = InputValidator.validate_date(data_str)
        assert isinstance(data_obj, date)
    
    def test_validate_date_passado(self):
        """Testa validação de data no passado"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_date('2020-01-01')
        
        assert 'passado' in str(exc_info.value).lower()
    
    def test_validate_date_formato_invalido(self):
        """Testa validação de data com formato inválido"""
        with pytest.raises(ValidationError) as exc_info:
            InputValidator.validate_date('25/12/2024')
        
        assert 'formato' in str(exc_info.value).lower()
    
    def test_validate_time_valido(self):
        """Testa validação de hora válida"""
        from datetime import time
        hora = InputValidator.validate_time('14:30')
        assert isinstance(hora, time)
        assert hora.hour == 14
        assert hora.minute == 30
    
    def test_validate_time_invalido(self):
        """Testa validação de hora inválida"""
        with pytest.raises(ValidationError):
            InputValidator.validate_time('25:30')  # Hora inválida
    
    def test_validate_tipo_pesquisa_valido(self):
        """Testa validação de tipo de pesquisa válido"""
        tipo = InputValidator.validate_tipo_pesquisa('MRS')
        assert tipo == 'MRS'
    
    def test_validate_tipo_pesquisa_invalido(self):
        """Testa validação de tipo de pesquisa inválido"""
        with pytest.raises(ValidationError):
            InputValidator.validate_tipo_pesquisa('TIPO_INVALIDO')
    
    def test_sanitize_string_normal(self):
        """Testa sanitização de string normal"""
        text = "Texto normal com acentos: ção"
        sanitized = InputValidator.sanitize_string(text)
        assert sanitized == text
    
    def test_sanitize_string_caracteres_controle(self):
        """Testa sanitização removendo caracteres de controle"""
        text = "Texto\x00com\x1fcaracteres\x7fde controle"
        sanitized = InputValidator.sanitize_string(text)
        assert 'comcaracteresde controle' in sanitized
        assert '\x00' not in sanitized
    
    def test_sanitize_string_comprimento_maximo(self):
        """Testa sanitização com limite de comprimento"""
        text = "a" * 300
        sanitized = InputValidator.sanitize_string(text, max_length=100)
        assert len(sanitized) == 100
    
    def test_validate_email_valido(self):
        """Testa validação de email válido"""
        email = InputValidator.validate_email('teste@email.com')
        assert email == 'teste@email.com'
    
    def test_validate_email_invalido(self):
        """Testa validação de email inválido"""
        with pytest.raises(ValidationError):
            InputValidator.validate_email('email_invalido')
    
    def test_validate_phone_valido(self):
        """Testa validação de telefone válido"""
        phone = InputValidator.validate_phone('(47) 99999-9999')
        assert phone == '47999999999'  # Apenas números
    
    def test_validate_phone_invalido(self):
        """Testa validação de telefone inválido"""
        with pytest.raises(ValidationError):
            InputValidator.validate_phone('123')  # Muito curto

class TestVisitaValidator:
    """Testes para VisitaValidator"""
    
    def test_validate_visita_data_completa(self):
        """Testa validação de dados completos de visita"""
        data = {
            'municipio': 'Itajaí',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'hora_fim': '10:00',
            'informante': 'João Silva',
            'tipo_pesquisa': 'MRS',
            'tipo_informante': 'prefeitura',
            'observacoes': 'Teste'
        }
        
        validated = VisitaValidator.validate_visita_data(data)
        
        assert validated['municipio'] == 'Itajaí'
        assert validated['informante'] == 'João Silva'
        assert validated['tipo_pesquisa'] == 'MRS'
    
    def test_validate_visita_data_minima(self):
        """Testa validação com dados mínimos obrigatórios"""
        data = {
            'municipio': 'Itajaí',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'informante': 'João Silva',
            'tipo_pesquisa': 'MRS'
        }
        
        validated = VisitaValidator.validate_visita_data(data)
        
        assert validated['hora_fim'] == validated['hora_inicio']  # Default
        assert validated['tipo_informante'] == 'prefeitura'  # Default
    
    def test_validate_visita_hora_fim_antes_inicio(self):
        """Testa validação com hora fim antes do início"""
        data = {
            'municipio': 'Itajaí',
            'data': '2024-12-25',
            'hora_inicio': '10:00',
            'hora_fim': '09:00',  # Antes do início
            'informante': 'João Silva',
            'tipo_pesquisa': 'MRS'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            VisitaValidator.validate_visita_data(data)
        
        assert 'posterior' in str(exc_info.value).lower()
    
    def test_validate_visita_informante_vazio(self):
        """Testa validação com informante vazio"""
        data = {
            'municipio': 'Itajaí',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'informante': '',  # Vazio
            'tipo_pesquisa': 'MRS'
        }
        
        with pytest.raises(ValidationError) as exc_info:
            VisitaValidator.validate_visita_data(data)
        
        assert 'informante' in str(exc_info.value).lower()
    
    def test_validate_visita_municipio_invalido(self):
        """Testa validação com município inválido"""
        data = {
            'municipio': 'Município Inexistente',
            'data': '2024-12-25',
            'hora_inicio': '09:00',
            'informante': 'João Silva',
            'tipo_pesquisa': 'MRS'
        }
        
        with pytest.raises(ValidationError):
            VisitaValidator.validate_visita_data(data)