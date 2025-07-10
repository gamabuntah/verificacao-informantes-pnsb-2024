#!/usr/bin/env python3
"""
Aplicação PNSB - Sistema de Gestão de Visitas
Versão refatorada com melhorias de segurança, arquitetura e performance
"""

import os
from dotenv import load_dotenv
from gestao_visitas.app_factory import create_app
from gestao_visitas.config.security import SecurityConfig
from gestao_visitas.utils.cache import CacheUtils

# Carregar variáveis de ambiente
load_dotenv()

def main():
    """Função principal da aplicação"""
    
    print("🚀 Iniciando Sistema PNSB - Gestão de Visitas")
    print("=" * 50)
    
    # Determinar ambiente
    env = os.getenv('FLASK_ENV', 'development')
    print(f"📍 Ambiente: {env}")
    
    # Validar configuração
    print("🔐 Validando configuração de segurança...")
    if not SecurityConfig.validate_environment():
        print("⚠️  Algumas funcionalidades podem estar limitadas")
    
    # Criar aplicação
    print("🏗️  Criando aplicação...")
    app = create_app(env)
    
    # Aquecer cache
    print("🔥 Aquecendo cache...")
    with app.app_context():
        CacheUtils.warm_up_cache()
    
    # Configurações de execução
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = env == 'development'
    
    print("=" * 50)
    print(f"🌐 Servidor rodando em: http://{host}:{port}")
    print(f"🔧 Debug: {'Ativado' if debug else 'Desativado'}")
    print("=" * 50)
    print("📝 Para parar o servidor: Ctrl+C")
    print("=" * 50)
    
    # Iniciar servidor
    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 Servidor encerrado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar servidor: {e}")
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())