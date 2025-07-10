#!/bin/bash

# Sistema PNSB - Script de Inicialização
# Este script configura e inicia o sistema completo

echo "🚀 INICIANDO SISTEMA PNSB COMPLETO"
echo "=================================="

# Definir PATH para pip3
export PATH="$HOME/.local/bin:$PATH"

# Definir variáveis de ambiente
export FLASK_DEBUG=1
export FLASK_ENV=development

# Navegar para diretório do projeto
cd "/mnt/c/users/ggmob/Cursor AI/Verificação Informantes PNSB/Agente IA"

echo "🔧 Verificando dependências..."

# Verificar se as dependências estão instaladas
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Instalando dependências..."
    pip3 install -r requirements.txt
    pip3 install pandas geopy
fi

echo "🗄️ Verificando banco de dados..."

# Verificar se o banco existe, se não, criar
if [ ! -f "gestao_visitas/gestao_visitas.db" ]; then
    echo "🔧 Criando banco de dados..."
    python3 -c "
from gestao_visitas.app_factory import create_app
from gestao_visitas.db import db
app = create_app('development')
with app.app_context():
    db.create_all()
    print('✅ Banco criado!')
"
fi

echo "🌐 Iniciando servidor web..."
echo ""
echo "📋 INFORMAÇÕES IMPORTANTES:"
echo "   🌍 URL: http://127.0.0.1:5000"
echo "   🔑 Debugger PIN: (será mostrado abaixo)"
echo "   ⏹️ Para parar: Ctrl+C"
echo ""
echo "🎯 PÁGINAS PARA TESTAR:"
echo "   📊 Dashboard: http://127.0.0.1:5000/"
echo "   📅 Visitas: http://127.0.0.1:5000/visitas"
echo "   📋 Checklist: http://127.0.0.1:5000/checklist"
echo "   📇 Contatos: http://127.0.0.1:5000/contatos"
echo "   📈 Relatórios: http://127.0.0.1:5000/relatorios"
echo ""
echo "🔧 APIs PNSB PARA TESTAR:"
echo "   🎛️ Status: http://127.0.0.1:5000/api/pnsb/status/funcionalidades-pnsb"
echo "   🗺️ Mapa: http://127.0.0.1:5000/api/pnsb/questionarios/mapa-progresso"
echo "   👥 Produtividade: http://127.0.0.1:5000/api/pnsb/produtividade/comparativo-equipe"
echo ""
echo "=================================="

# Iniciar o sistema
python3 app_new.py