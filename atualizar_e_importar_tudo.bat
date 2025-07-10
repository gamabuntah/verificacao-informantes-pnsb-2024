@echo off
chcp 65001 > nul

REM Detectar terminal e ativar ambiente virtual corretamente
set VENV_ACTIVATED=0
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    set VENV_ACTIVATED=1
) else if exist .venv\Scripts\Activate.ps1 (
    powershell -Command ". .venv\Scripts\Activate.ps1"
    set VENV_ACTIVATED=1
)

if %VENV_ACTIVATED%==0 (
    echo ERRO: Ambiente virtual nao encontrado ou nao foi possivel ativar!
    pause
    exit /b 1
)

cd "Agente IA"

REM Rodar migrações
if not exist "migrations" (
    flask db init
)
flask db migrate -m "Ajuste final modelo contatos"
flask db upgrade

REM Importar contatos
echo Importando contatos...
python -m gestao_visitas.scripts.importar_contatos

echo.
echo Processo concluido! Verifique a interface web.
pause 