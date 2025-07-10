@echo off
chcp 65001 > nul

echo =============================================
echo  CONFIGURADOR DE PERMISSÕES - WINDOWS
echo =============================================
echo.

:: Verificar se executando como administrador
net session >nul 2>&1
if errorlevel 1 (
    echo ❌ ERRO: Este script precisa ser executado como Administrador!
    echo.
    echo 💡 COMO EXECUTAR COMO ADMINISTRADOR:
    echo    1. Clique com botão direito neste arquivo
    echo    2. Selecione "Executar como administrador"
    echo.
    pause
    exit /b 1
)

echo ✅ Executando como Administrador
echo.

:: Definir variáveis
set "PROJETO_DIR=C:\Users\ggmob\Cursor AI\Verificação Informantes PNSB"
set "PYTHON_EXE=%PROJETO_DIR%\.venv\Scripts\python.exe"

echo 🔧 Configurando permissões para o Sistema PNSB 2024...
echo.

:: 1. Liberar portas 5000 e 5001
echo 🌐 Liberando portas 5000 e 5001...
netsh advfirewall firewall add rule name="PNSB Flask 5000" dir=in action=allow protocol=TCP localport=5000
netsh advfirewall firewall add rule name="PNSB Flask 5001" dir=in action=allow protocol=TCP localport=5001
echo    ✅ Regras de firewall adicionadas

:: 2. Verificar e matar processos na porta 5000
echo 🔍 Verificando processos na porta 5000...
for /f "tokens=5" %%a in ('netstat -ano ^| find "127.0.0.1:5000" 2^>nul') do (
    echo    🛑 Encerrando processo %%a na porta 5000
    taskkill /F /PID %%a >nul 2>&1
)

:: 3. Verificar e matar processos na porta 5001  
echo 🔍 Verificando processos na porta 5001...
for /f "tokens=5" %%a in ('netstat -ano ^| find "127.0.0.1:5001" 2^>nul') do (
    echo    🛑 Encerrando processo %%a na porta 5001
    taskkill /F /PID %%a >nul 2>&1
)

:: 4. Configurar permissões do Python
if exist "%PYTHON_EXE%" (
    echo 🐍 Configurando permissões do Python...
    icacls "%PYTHON_EXE%" /grant:r "Usuários:(RX)" /T >nul 2>&1
    echo    ✅ Permissões do Python configuradas
) else (
    echo ⚠️ Python não encontrado em: %PYTHON_EXE%
)

:: 5. Configurar permissões do diretório
echo 📁 Configurando permissões do diretório do projeto...
icacls "%PROJETO_DIR%" /grant:r "Usuários:(F)" /T >nul 2>&1
echo    ✅ Permissões do diretório configuradas

:: 6. Resetar configurações de rede problemáticas
echo 🔄 Resetando configurações de rede...
netsh winsock reset >nul 2>&1
netsh int ip reset >nul 2>&1
echo    ✅ Configurações de rede resetadas

:: 7. Configurar Windows Defender (se estiver ativo)
echo 🛡️ Configurando exclusões do Windows Defender...
powershell -Command "Add-MpPreference -ExclusionPath '%PROJETO_DIR%' -Force" 2>nul
if errorlevel 1 (
    echo    ⚠️ Não foi possível configurar exclusões do Windows Defender
    echo    💡 Configure manualmente se necessário
) else (
    echo    ✅ Exclusões do Windows Defender configuradas
)

echo.
echo =============================================
echo ✅ CONFIGURAÇÃO CONCLUÍDA!
echo =============================================
echo.
echo 📋 O QUE FOI CONFIGURADO:
echo    ✅ Regras de firewall para portas 5000 e 5001
echo    ✅ Processos conflitantes encerrados
echo    ✅ Permissões do Python configuradas
echo    ✅ Permissões do diretório ajustadas
echo    ✅ Configurações de rede resetadas
echo    ✅ Exclusões do antivírus (se possível)
echo.
echo 🚀 PRÓXIMOS PASSOS:
echo    1. Execute: executar_projeto_corrigido.bat
echo    2. Se ainda der erro, reinicie o computador
echo    3. Execute novamente como administrador
echo.
echo 💡 NOTA: Algumas alterações podem precisar de reinicialização
echo    para ter efeito completo.
echo.
pause