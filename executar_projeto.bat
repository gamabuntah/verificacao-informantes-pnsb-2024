@echo off
chcp 65001 > nul

echo Iniciando o projeto...
echo.

:: Definir o caminho do projeto
set "PROJETO_DIR=C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB"

:: Verificar se o diretório existe
if not exist "%PROJETO_DIR%" (
    echo Erro: Diretorio do projeto nao encontrado: %PROJETO_DIR%
    pause
    exit /b 1
)

:: Verificar se o ambiente virtual existe
if not exist "%PROJETO_DIR%\.venv" (
    echo Erro: Ambiente virtual nao encontrado!
    echo Por favor, crie o ambiente virtual primeiro com o comando:
    echo python -m venv .venv
    pause
    exit /b 1
)

:: Ativar ambiente virtual
echo Ativando ambiente virtual...
cd /d "%PROJETO_DIR%"
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Erro ao ativar o ambiente virtual!
    echo Verifique se o ambiente virtual existe em: %PROJETO_DIR%\.venv\Scripts\activate.bat
    pause
    exit /b 1
)

:: Verificar se o diretório Agente IA existe
if not exist "%PROJETO_DIR%\Agente IA" (
    echo Erro: Diretorio 'Agente IA' nao encontrado!
    pause
    exit /b 1
)

:: Navegar para o diretório do projeto
echo Navegando para o diretorio do projeto...
cd /d "%PROJETO_DIR%\Agente IA"

:: Verificar se o app.py existe
if not exist "app.py" (
    echo Erro: Arquivo app.py nao encontrado!
    echo Diretorio atual: %CD%
    pause
    exit /b 1
)

:: Iniciar o servidor Flask
echo.
echo Iniciando o servidor Flask...
echo O site estara disponivel em: http://127.0.0.1:5000
echo.
echo Pressione CTRL+C para encerrar o servidor
echo.
python app.py

:: Desativar ambiente virtual ao sair
call .venv\Scripts\deactivate.bat

echo.
echo Servidor encerrado.
pause 