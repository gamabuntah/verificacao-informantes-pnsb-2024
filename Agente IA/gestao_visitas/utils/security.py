"""
Sistema de Segurança e Criptografia para PNSB 2024
Implementa funções de hash, criptografia e validação segura
"""

import hashlib
import secrets
import hmac
import base64
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, Dict, Any
import re

class SecurityManager:
    """Gerenciador de segurança para o sistema PNSB"""
    
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        self.hash_algorithm = 'sha256'
        self.token_expiry_hours = 24
    
    def generate_secure_token(self, length: int = 32) -> str:
        """Gera token seguro para autenticação"""
        return secrets.token_urlsafe(length)
    
    def hash_password(self, password: str) -> str:
        """Hash seguro de senha usando Werkzeug"""
        return generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
    
    def verify_password(self, password: str, hash: str) -> bool:
        """Verifica senha contra hash"""
        return check_password_hash(hash, password)
    
    def generate_api_key(self, user_id: str, expires_hours: int = None) -> str:
        """Gera API key com expiração"""
        expires = expires_hours or self.token_expiry_hours
        expiry = datetime.now() + timedelta(hours=expires)
        
        payload = f"{user_id}:{expiry.isoformat()}"
        signature = self.create_signature(payload)
        
        api_key = base64.b64encode(f"{payload}:{signature}".encode()).decode()
        return api_key
    
    def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Valida API key e retorna dados do usuário"""
        try:
            decoded = base64.b64decode(api_key.encode()).decode()
            parts = decoded.rsplit(':', 1)
            
            if len(parts) != 2:
                return None
            
            payload, signature = parts
            
            # Verificar assinatura
            if not self.verify_signature(payload, signature):
                return None
            
            # Extrair dados
            user_id, expiry_str = payload.split(':', 1)
            expiry = datetime.fromisoformat(expiry_str)
            
            # Verificar expiração
            if datetime.now() > expiry:
                return None
            
            return {
                'user_id': user_id,
                'expiry': expiry,
                'valid': True
            }
            
        except Exception:
            return None
    
    def create_signature(self, data: str) -> str:
        """Cria assinatura HMAC para dados"""
        return hmac.new(
            self.secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verifica assinatura HMAC"""
        expected = self.create_signature(data)
        return hmac.compare_digest(expected, signature)
    
    def hash_sensitive_data(self, data: str, salt: str = None) -> Dict[str, str]:
        """Hash para dados sensíveis com salt"""
        salt = salt or secrets.token_hex(16)
        
        salted_data = f"{salt}{data}{self.secret_key}"
        hash_value = hashlib.sha256(salted_data.encode()).hexdigest()
        
        return {
            'hash': hash_value,
            'salt': salt
        }
    
    def verify_sensitive_data(self, data: str, hash_value: str, salt: str) -> bool:
        """Verifica dados sensíveis contra hash"""
        expected = self.hash_sensitive_data(data, salt)
        return hmac.compare_digest(expected['hash'], hash_value)

class InputValidator:
    """Validador de entrada para prevenir ataques"""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """Sanitiza string de entrada"""
        if not input_str:
            return ""
        
        # Limitar tamanho
        sanitized = str(input_str)[:max_length]
        
        # Remover caracteres perigosos básicos
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Valida formato de email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email)) if email else False
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """Valida formato de telefone brasileiro"""
        if not phone:
            return False
        
        # Remove caracteres não numéricos
        clean_phone = re.sub(r'[^\d]', '', phone)
        
        # Telefone brasileiro: 10 ou 11 dígitos
        return len(clean_phone) in [10, 11] and clean_phone.isdigit()
    
    @staticmethod
    def validate_municipio_sc(municipio: str) -> bool:
        """Valida se é um município válido de SC para PNSB"""
        municipios_validos = [
            'Balneário Camboriú', 'Balneário Piçarras', 'Bombinhas', 'Camboriú',
            'Itajaí', 'Itapema', 'Luiz Alves', 'Navegantes', 'Penha', 'Porto Belo', 'Ilhota'
        ]
        return municipio in municipios_validos if municipio else False
    
    @staticmethod
    def validate_priority(priority: Any) -> bool:
        """Valida prioridade PNSB (1, 2, 3)"""
        try:
            p = int(priority)
            return p in [1, 2, 3]
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_status_pnsb(status: str) -> bool:
        """Valida status do workflow PNSB"""
        status_validos = [
            'nao_iniciado', 'contactado', 'respondido', 
            'aguardando_validacao', 'validado_concluido',
            'revisao_necessaria', 'cancelado'
        ]
        return status in status_validos if status else False

class RateLimitEnhanced:
    """Rate limiter avançado com diferentes níveis"""
    
    def __init__(self):
        self.limits = {
            'api_general': {'requests': 100, 'window': 3600},  # 100/hora
            'api_critical': {'requests': 20, 'window': 3600},  # 20/hora para operações críticas
            'login_attempts': {'requests': 5, 'window': 900},  # 5 tentativas/15min
            'file_upload': {'requests': 10, 'window': 3600}    # 10 uploads/hora
        }
        self.counters = {}
    
    def is_allowed(self, client_ip: str, endpoint_type: str = 'api_general') -> bool:
        """Verifica se requisição é permitida"""
        if endpoint_type not in self.limits:
            return True
        
        limit_config = self.limits[endpoint_type]
        key = f"{client_ip}:{endpoint_type}"
        
        now = datetime.now()
        window_start = now - timedelta(seconds=limit_config['window'])
        
        # Limpar registros antigos
        if key in self.counters:
            self.counters[key] = [
                timestamp for timestamp in self.counters[key] 
                if timestamp > window_start
            ]
        else:
            self.counters[key] = []
        
        # Verificar limite
        if len(self.counters[key]) >= limit_config['requests']:
            return False
        
        # Adicionar nova requisição
        self.counters[key].append(now)
        return True
    
    def get_remaining_requests(self, client_ip: str, endpoint_type: str = 'api_general') -> int:
        """Retorna número de requisições restantes"""
        if endpoint_type not in self.limits:
            return 999
        
        limit_config = self.limits[endpoint_type]
        key = f"{client_ip}:{endpoint_type}"
        
        if key not in self.counters:
            return limit_config['requests']
        
        return max(0, limit_config['requests'] - len(self.counters[key]))

# Instâncias globais
security_manager = SecurityManager()
input_validator = InputValidator()
rate_limiter_enhanced = RateLimitEnhanced()

# Funções de conveniência
def hash_password(password: str) -> str:
    """Função conveniente para hash de senha"""
    return security_manager.hash_password(password)

def verify_password(password: str, hash: str) -> bool:
    """Função conveniente para verificação de senha"""
    return security_manager.verify_password(password, hash)

def generate_secure_token(length: int = 32) -> str:
    """Função conveniente para gerar token"""
    return security_manager.generate_secure_token(length)

def validate_input_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Valida e sanitiza dados de entrada"""
    validated = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            validated[key] = input_validator.sanitize_string(value)
        elif key == 'email' and value:
            if input_validator.validate_email(value):
                validated[key] = value
            else:
                raise ValueError(f"Email inválido: {value}")
        elif key == 'telefone' and value:
            if input_validator.validate_phone(value):
                validated[key] = value
            else:
                raise ValueError(f"Telefone inválido: {value}")
        elif key == 'municipio' and value:
            if input_validator.validate_municipio_sc(value):
                validated[key] = value
            else:
                raise ValueError(f"Município SC inválido: {value}")
        elif key == 'prioridade' and value is not None:
            if input_validator.validate_priority(value):
                validated[key] = int(value)
            else:
                raise ValueError(f"Prioridade inválida: {value}")
        else:
            validated[key] = value
    
    return validated

if __name__ == "__main__":
    # Teste do sistema de segurança
    print("🔒 TESTE DO SISTEMA DE SEGURANÇA PNSB")
    print("=" * 50)
    
    # Teste de hash de senha
    password = "senha_teste_pnsb_2024"
    hashed = hash_password(password)
    verified = verify_password(password, hashed)
    print(f"✅ Hash de senha: {verified}")
    
    # Teste de token
    token = generate_secure_token()
    print(f"✅ Token gerado: {token[:16]}...")
    
    # Teste de validação
    test_data = {
        'email': 'teste@ibge.gov.br',
        'telefone': '(11) 99999-9999',
        'municipio': 'Itajaí',
        'prioridade': 1
    }
    
    try:
        validated = validate_input_data(test_data)
        print(f"✅ Validação: {len(validated)} campos validados")
    except ValueError as e:
        print(f"❌ Erro de validação: {e}")
    
    print("🎉 Sistema de segurança configurado!")