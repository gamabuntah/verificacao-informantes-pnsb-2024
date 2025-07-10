@echo off
echo ==============================================
echo  INSTALACAO DE DEPENDENCIAS - SISTEMA PNSB
echo ==============================================
echo.

echo [1/4] Verificando Python...
python --version
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado. Instale Python 3.8+ primeiro.
    pause
    exit /b 1
)

echo.
echo [2/4] Atualizando pip...
python -m pip install --upgrade pip

echo.
echo [3/4] Instalando dependencias do requirements.txt...
python -m pip install -r requirements.txt

echo.
echo [4/4] Instalando dependencias especificas...
python -m pip install python-dotenv
python -m pip install pandas
python -m pip install openpyxl
python -m pip install geopy

echo.
echo ==============================================
echo  INSTALACAO CONCLUIDA COM SUCESSO!
echo ==============================================
echo.
echo Proximo passo: Execute 'python app.py' para iniciar o sistema
echo.
pause