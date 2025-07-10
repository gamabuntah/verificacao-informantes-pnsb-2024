#!/usr/bin/env python3
"""
Script simples para iniciar o servidor PNSB
Versão sem complicações - apenas funciona
"""

import os
import sys
from pathlib import Path

# Adicionar diretório atual ao Python path
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

def main():
    print("🚀 SISTEMA PNSB - INICIALIZAÇÃO SIMPLES")
    print("=" * 50)
    
    try:
        # Configurar variáveis de ambiente básicas
        os.environ['FLASK_DEBUG'] = '1'
        
        # Importar e criar app
        from gestao_visitas.app_factory import create_app
        from gestao_visitas.db import db
        
        print("✅ Criando aplicação...")
        app = create_app('development')
        
        print("✅ Verificando banco de dados...")
        with app.app_context():
            try:
                db.create_all()
                print("✅ Banco de dados pronto")
            except Exception as e:
                print(f"⚠️ Erro no banco: {e}")
        
        print("✅ Configuração completa!")
        print("")
        print("🌐 SERVIDOR INICIANDO...")
        print("   • URL: http://127.0.0.1:5000")
        print("   • URL: http://localhost:5000")
        print("   • Para parar: Ctrl+C")
        print("")
        print("=" * 50)
        
        # Iniciar servidor
        app.run(
            host='127.0.0.1',
            port=5000,
            debug=True,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n⏹️ Servidor parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == '__main__':
    exit(main())