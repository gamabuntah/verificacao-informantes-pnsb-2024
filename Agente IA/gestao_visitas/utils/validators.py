from datetime import datetime, date, time
import re
from functools import wraps
from flask import request, jsonify
from ..config import MUNICIPIOS, TIPOS_PESQUISA, TIPOS_INFORMANTE, STATUS_VISITA

class ValidationError(Exception):
    """Exceção personalizada para erros de validação"""
    pass

class InputValidator:
    """Classe para validação de entradas"""
    
    @staticmethod
    def validate_required_fields(data, required_fields):
        """Valida se todos os campos obrigatórios estão presentes"""
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(f"Campos obrigatórios ausentes: {', '.join(missing_fields)}")
    
    @staticmethod
    def validate_municipio(municipio):
        """Valida se o município é válido"""
        if not municipio or municipio not in MUNICIPIOS:
            raise ValidationError(f"Município inválido. Deve ser um de: {', '.join(MUNICIPIOS)}")
        return municipio.strip()
    
    @staticmethod
    def validate_date(date_str):
        """Valida formato de data (permite qualquer data para registro histórico)"""
        try:
            data_visita = datetime.strptime(date_str, '%Y-%m-%d').date()
            # Removida restrição de data passada para permitir registro histórico
            return data_visita
        except ValueError:
            raise ValidationError("Formato de data inválido. Use YYYY-MM-DD")
    
    @staticmethod
    def validate_time(time_str):
        """Valida formato de hora"""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            raise ValidationError("Formato de hora inválido. Use HH:MM")
    
    @staticmethod
    def validate_tipo_pesquisa(tipo):
        """Valida tipo de pesquisa"""
        if tipo not in TIPOS_PESQUISA:
            raise ValidationError(f"Tipo de pesquisa inválido. Deve ser um de: {', '.join(TIPOS_PESQUISA.keys())}")
        return tipo
    
    @staticmethod
    def validate_tipo_informante(tipo):
        """Valida tipo de informante"""
        if tipo not in TIPOS_INFORMANTE:
            raise ValidationError(f"Tipo de informante inválido. Deve ser um de: {', '.join(TIPOS_INFORMANTE.keys())}")
        return tipo
    
    @staticmethod
    def validate_status(status):
        """Valida status da visita"""
        if status not in STATUS_VISITA:
            raise ValidationError(f"Status inválido. Deve ser um de: {', '.join(STATUS_VISITA.keys())}")
        return status
    
    @staticmethod
    def sanitize_string(text, max_length=255):
        """Sanitiza string removendo caracteres perigosos"""
        if not text:
            return ""
        
        # Remove caracteres de controle e limita comprimento
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', str(text))
        return sanitized[:max_length].strip()
    
    @staticmethod
    def validate_email(email):
        """Valida formato de email"""
        if not email:
            return ""
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            raise ValidationError("Formato de email inválido")
        return email.lower().strip()
    
    @staticmethod
    def validate_phone(phone):
        """Valida formato de telefone brasileiro"""
        if not phone:
            return ""
        
        # Remove caracteres não numéricos
        phone_clean = re.sub(r'[^\d]', '', phone)
        
        # Valida se tem 10 ou 11 dígitos
        if len(phone_clean) not in [10, 11]:
            raise ValidationError("Telefone deve ter 10 ou 11 dígitos")
        
        return phone_clean

def validate_json_input(required_fields=None, optional_fields=None):
    """Decorator para validar entrada JSON"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'error': 'JSON inválido ou ausente'}), 400
                
                # Validar campos obrigatórios
                if required_fields:
                    InputValidator.validate_required_fields(data, required_fields)
                
                # Sanitizar strings
                for key, value in data.items():
                    if isinstance(value, str):
                        data[key] = InputValidator.sanitize_string(value)
                
                # Adicionar dados validados ao request
                request.validated_data = data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                return jsonify({'error': str(e)}), 400
            except Exception as e:
                return jsonify({'error': 'Erro interno de validação'}), 500
        
        return decorated_function
    return decorator

class VisitaValidator:
    """Validador específico para dados de visita"""
    
    @staticmethod
    def validate_visita_data(data):
        """Valida dados completos de uma visita"""
        validated = {}
        
        # Campos obrigatórios
        validated['municipio'] = InputValidator.validate_municipio(data.get('municipio'))
        validated['data'] = InputValidator.validate_date(data.get('data'))
        validated['hora_inicio'] = InputValidator.validate_time(data.get('hora_inicio'))
        validated['informante'] = InputValidator.sanitize_string(data.get('informante'), 100)
        validated['tipo_pesquisa'] = InputValidator.validate_tipo_pesquisa(data.get('tipo_pesquisa'))
        
        # Campos opcionais
        if data.get('hora_fim'):
            validated['hora_fim'] = InputValidator.validate_time(data.get('hora_fim'))
        else:
            validated['hora_fim'] = validated['hora_inicio']
        
        validated['tipo_informante'] = InputValidator.validate_tipo_informante(
            data.get('tipo_informante', 'prefeitura')
        )
        validated['observacoes'] = InputValidator.sanitize_string(data.get('observacoes', ''), 500)
        
        # Validação de lógica de negócio
        if validated.get('hora_fim') and validated['hora_fim'] < validated['hora_inicio']:
            raise ValidationError("Hora de fim deve ser posterior à hora de início")
        
        if not validated['informante']:
            raise ValidationError("Nome do informante é obrigatório")
        
        return validated