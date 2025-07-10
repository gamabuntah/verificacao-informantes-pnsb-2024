@echo off
chcp 65001 > nul

echo =============================================
echo  SISTEMA PNSB 2024 - INICIALIZAÇÃO SEGURA
echo =============================================
echo.

:: Definir variáveis
set "PROJETO_DIR=C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB"
set "AGENTE_DIR=%PROJETO_DIR%\Agente IA"

:: Verificar se executando como administrador
net session >nul 2>&1
if errorlevel 1 (
    echo ⚠️ AVISO: Execute como Administrador para melhor compatibilidade
    echo.
    timeout /t 3 >nul
)

:: Navegar para o diretório
echo 📁 Navegando para o diretório do projeto...
cd /d "%PROJETO_DIR%"

if not exist ".venv" (
    echo ❌ Ambiente virtual não encontrado!
    echo Execute primeiro: instalar_dependencias_completas.bat
    pause
    exit /b 1
)

:: Ativar ambiente virtual
echo 🚀 Ativando ambiente virtual...
call .venv\Scripts\activate.bat

:: Navegar para o diretório da aplicação
echo 📂 Navegando para o diretório da aplicação...
cd /d "%AGENTE_DIR%"

echo.
echo 🌐 Configuração de rede segura...
echo    - Host: 127.0.0.1 (localhost)
echo    - Porta: 5000
echo    - Modo: Desenvolvimento
echo.

:: Configurar variáveis de ambiente para evitar conflitos
set FLASK_APP=app.py
set FLASK_ENV=development
set FLASK_DEBUG=1
set PYTHONPATH=%AGENTE_DIR%

:: Tentar liberar a porta 5000 se estiver em uso
echo 🔧 Verificando porta 5000...
netstat -an | find "127.0.0.1:5000" >nul
if not errorlevel 1 (
    echo ⚠️ Porta 5000 em uso. Tentando liberar...
    for /f "tokens=5" %%a in ('netstat -ano ^| find "127.0.0.1:5000"') do (
        taskkill /F /PID %%a >nul 2>&1
    )
    timeout /t 2 >nul
)

:: Configurações de segurança do Windows
echo 🔒 Aplicando configurações de segurança...
set PYTHONUNBUFFERED=1
set WERKZEUG_RUN_MAIN=true

echo.
echo ✅ Sistema será iniciado em: http://127.0.0.1:5000
echo.
echo 📋 INSTRUÇÕES:
echo    1. Aguarde a mensagem "Running on http://127.0.0.1:5000"
echo    2. Abra seu navegador
echo    3. Acesse: http://127.0.0.1:5000
echo    4. Para parar: Pressione CTRL+C
echo.
echo 🚀 Iniciando servidor Flask...
echo =============================================
echo.

:: Executar Flask com configurações específicas para Windows
python app.py

:: Se chegou aqui, o servidor foi encerrado
echo.
echo =============================================
echo 🛑 Servidor Flask encerrado.
echo =============================================
echo.

:: Verificar se foi erro ou encerramento normal
if errorlevel 1 (
    echo ❌ O servidor foi encerrado com erro.
    echo.
    echo 💡 SOLUÇÕES POSSÍVEIS:
    echo    1. Execute como Administrador
    echo    2. Verifique se a porta 5000 está livre
    echo    3. Desative temporariamente o antivírus
    echo    4. Verifique o Windows Firewall
    echo.
    echo 📞 Consulte SOLUCAO_PROBLEMAS.md para mais ajuda
) else (
    echo ✅ Servidor encerrado normalmente.
)

echo.
pause