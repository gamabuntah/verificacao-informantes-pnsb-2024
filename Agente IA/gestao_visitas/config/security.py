import os
import secrets

# Try to load dotenv if available, but don't fail if not installed
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Arquivo .env carregado com sucesso")
except ImportError:
    print("⚠️  python-dotenv não encontrado. Usando variáveis de ambiente do sistema.")
except Exception as e:
    print(f"⚠️  Erro ao carregar .env: {e}")
    print("   Continuando com variáveis de ambiente do sistema...")

class SecurityConfig:
    """Configurações de segurança centralizadas"""
    
    @staticmethod
    def get_secret_key():
        """Gera ou obtém chave secreta segura"""
        secret_key = os.getenv('SECRET_KEY')
        if not secret_key or secret_key == 'your_secure_secret_key_here':
            # Gera chave temporária se não estiver configurada
            secret_key = secrets.token_hex(32)
            print("⚠️  ATENÇÃO: Usando chave temporária. Configure SECRET_KEY no .env!")
        return secret_key
    
    @staticmethod
    def get_google_maps_key():
        """Obtém chave da API do Google Maps"""
        api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not api_key or api_key == 'your_google_maps_api_key_here':
            print("⚠️  ATENÇÃO: Google Maps API Key não configurada!")
            return None
        return api_key
    
    @staticmethod
    def get_google_gemini_key():
        """Obtém chave da API do Google Gemini"""
        api_key = os.getenv('GOOGLE_GEMINI_API_KEY')
        if not api_key or api_key == 'your_google_gemini_api_key_here':
            print("⚠️  ATENÇÃO: Google Gemini API Key não configurada!")
            return None
        return api_key
    
    @staticmethod
    def validate_environment():
        """Valida se todas as variáveis de ambiente estão configuradas"""
        required_vars = [
            'SECRET_KEY',
            'GOOGLE_MAPS_API_KEY',
            'GOOGLE_GEMINI_API_KEY'
        ]
        
        missing_vars = []
        for var in required_vars:
            value = os.getenv(var)
            if not value or value.startswith('your_'):
                missing_vars.append(var)
        
        if missing_vars:
            print("❌ Variáveis de ambiente não configuradas:")
            for var in missing_vars:
                print(f"   - {var}")
            print("\n💡 Configure essas variáveis no arquivo .env")
            return False
        
        print("✅ Todas as variáveis de ambiente estão configuradas!")
        return True