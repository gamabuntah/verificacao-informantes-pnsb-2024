@echo off
chcp 65001 > nul

echo =============================================
echo  INSTALADOR COMPLETO - SISTEMA PNSB 2024
echo =============================================
echo.

:: Definir o caminho do projeto
set "PROJETO_DIR=C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB"

:: Verificar se o diretório existe
if not exist "%PROJETO_DIR%" (
    echo ❌ Erro: Diretório do projeto não encontrado: %PROJETO_DIR%
    pause
    exit /b 1
)

echo 📁 Navegando para o diretório do projeto...
cd /d "%PROJETO_DIR%"

:: Verificar se o ambiente virtual existe
if not exist "%PROJETO_DIR%\.venv" (
    echo 🔧 Criando ambiente virtual...
    python -m venv .venv
    if errorlevel 1 (
        echo ❌ Erro ao criar ambiente virtual!
        pause
        exit /b 1
    )
)

:: Ativar ambiente virtual
echo 🚀 Ativando ambiente virtual...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ Erro ao ativar o ambiente virtual!
    pause
    exit /b 1
)

:: Atualizar o pip
echo 📦 Atualizando pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

:: Instalar dependências básicas primeiro
echo 📦 Instalando dependências básicas...
pip install flask==3.0.2
pip install flask-sqlalchemy==3.1.1
pip install flask-migrate==4.0.5
pip install python-dotenv==1.0.1
pip install pandas==2.3.0
pip install requests==2.31.0

:: Instalar dependências para Excel/CSV
echo 📊 Instalando suporte para Excel/CSV...
pip install openpyxl==3.1.2
pip install xlrd==2.0.1
pip install xlwt==1.3.0
pip install xlsxwriter==3.2.0

:: Instalar dependências de data/tempo
echo 📅 Instalando bibliotecas de data/tempo...
pip install python-dateutil==2.8.2
pip install pytz==2024.1
pip install tzdata==2025.2

:: Instalar dependências opcionais (com fallback)
echo 📋 Instalando dependências opcionais...
pip install pdfplumber==0.9.0
if errorlevel 1 (
    echo ⚠️ Aviso: pdfplumber não pôde ser instalado. Funcionalidades de PDF serão limitadas.
)

pip install flask-compress==1.14
if errorlevel 1 (
    echo ⚠️ Aviso: flask-compress não pôde ser instalado. Compressão será desabilitada.
)

pip install geopy==2.4.1
if errorlevel 1 (
    echo ⚠️ Aviso: geopy não pôde ser instalado. Cálculos de distância usarão aproximação.
)

pip install redis==5.0.1
if errorlevel 1 (
    echo ⚠️ Aviso: redis não pôde ser instalado. Sistema usará simulador de cache.
)

:: Instalar dependências de segurança
echo 🔒 Instalando dependências de segurança...
pip install werkzeug==3.0.1

:: Instalar dependências de teste (opcional)
echo 🧪 Instalando dependências de teste...
pip install pytest==7.4.3
pip install pytest-flask==1.3.0
pip install pytest-cov==4.1.0

:: Verificar instalação
echo.
echo 🔍 Verificando instalação...
python -c "import flask, flask_sqlalchemy, pandas, requests; print('✅ Dependências principais OK')"
if errorlevel 1 (
    echo ❌ Erro na verificação das dependências principais!
    pause
    exit /b 1
)

:: Verificar dependências opcionais
echo 🔍 Verificando dependências opcionais...
python -c "
try:
    import pdfplumber
    print('✅ pdfplumber: OK')
except ImportError:
    print('⚠️ pdfplumber: NÃO INSTALADO')

try:
    import flask_compress
    print('✅ flask-compress: OK')
except ImportError:
    print('⚠️ flask-compress: NÃO INSTALADO')

try:
    import geopy
    print('✅ geopy: OK')
except ImportError:
    print('⚠️ geopy: NÃO INSTALADO')

try:
    import redis
    print('✅ redis: OK')
except ImportError:
    print('⚠️ redis: NÃO INSTALADO')
"

echo.
echo =============================================
echo ✅ INSTALAÇÃO CONCLUÍDA COM SUCESSO!
echo =============================================
echo.
echo 📋 PRÓXIMOS PASSOS:
echo   1. Execute: executar_projeto.bat
echo   2. Acesse: http://127.0.0.1:5000
echo   3. Consulte: CLAUDE.md para documentação
echo.
echo 💡 NOTA: Dependências opcionais podem não estar instaladas,
echo    mas o sistema funcionará com funcionalidades reduzidas.
echo.
pause