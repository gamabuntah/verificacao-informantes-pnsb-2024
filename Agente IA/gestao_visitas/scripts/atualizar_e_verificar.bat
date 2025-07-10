@echo off
echo === Iniciando processo de atualizacao e verificacao ===

REM Verificar se estamos no PowerShell ou CMD
if "%COMSPEC%"=="%SystemRoot%\System32\cmd.exe" (
    echo Executando no CMD...
    call .\venv\Scripts\activate.bat
) else (
    echo Executando no PowerShell...
    .\venv\Scripts\Activate.ps1
)

REM Importar contatos
echo.
echo === Importando contatos ===
python "Agente IA/gestao_visitas/scripts/importar_contatos.py"

REM Verificar integridade
echo.
echo === Verificando integridade ===
python "Agente IA/gestao_visitas/scripts/verificar_integridade_contatos.py"

echo.
echo === Processo concluido ===
pause 