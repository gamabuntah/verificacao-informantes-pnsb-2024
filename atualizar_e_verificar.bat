@echo off
REM Script para atualizar banco, importar contatos e verificar integridade

REM Detectar terminal e ativar ambiente virtual
if "%COMSPEC%"=="%SystemRoot%\System32\cmd.exe" (
    echo Ativando ambiente virtual no CMD...
    call .\venv\Scripts\activate.bat
) else (
    echo Ativando ambiente virtual no PowerShell...
    .\venv\Scripts\Activate.ps1
)

echo.
echo === Importando contatos ===
python "Agente IA/gestao_visitas/scripts/importar_contatos.py"

echo.
echo === Verificando integridade ===
python "Agente IA/gestao_visitas/scripts/verificar_integridade_contatos.py"

echo.
echo === Processo concluido ===
pause 