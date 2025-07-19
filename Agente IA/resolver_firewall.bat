@echo off
echo 🛡️ RESOLVENDO PROBLEMA DE FIREWALL - PNSB 2024
echo ================================================

echo 1. Verificando se Python está sendo bloqueado...
netsh advfirewall firewall show rule name="Python" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Criando regra de firewall para Python...
    netsh advfirewall firewall add rule name="Python Flask PNSB" dir=in action=allow program="%~dp0\.venv\Scripts\python.exe" enable=yes
    netsh advfirewall firewall add rule name="Python Flask PNSB" dir=in action=allow program="python.exe" enable=yes
    netsh advfirewall firewall add rule name="Python Flask PNSB Port" dir=in action=allow protocol=TCP localport=5000
    echo ✅ Regras de firewall criadas
) else (
    echo ✅ Python já tem permissão no firewall
)

echo.
echo 2. Testando conexão local...
curl -s -m 5 http://127.0.0.1:5000/api/visitas >nul 2>&1
if %errorlevel% eq 0 (
    echo ✅ Conexão funcionando!
) else (
    echo ❌ Ainda há problemas de conexão
    echo.
    echo 💡 Tente:
    echo    1. Desabilitar antivírus temporariamente
    echo    2. Verificar se há proxy configurado
    echo    3. Reiniciar o navegador
)

echo.
echo 3. Informações de rede:
netstat -an | findstr ":5000"

pause
