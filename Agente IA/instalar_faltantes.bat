@echo off
echo ==============================================
echo  INSTALACAO RAPIDA - DEPENDENCIAS FALTANTES
echo ==============================================
echo.

echo Instalando dependencias que podem estar faltando...
echo.

echo [1/4] Instalando python-dotenv...
python -m pip install python-dotenv

echo [2/4] Instalando geopy...
python -m pip install geopy

echo [3/4] Instalando pandas e openpyxl...
python -m pip install pandas openpyxl

echo [4/4] Verificando instalacao...
python -c "import dotenv, geopy, pandas, openpyxl; print('✅ Todas as dependencias instaladas!')"

echo.
echo ==============================================
echo  INSTALACAO CONCLUIDA!
echo  Agora execute: python app.py
echo ==============================================
echo.
pause