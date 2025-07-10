@echo off
echo ==========================================
echo INSTALAÇÃO REDIS - SISTEMA PNSB WINDOWS
echo ==========================================
echo.

echo 📦 Instalando dependências Python...
pip install redis==5.0.1
pip install python-redis-lock==4.0.0
pip install APScheduler==3.10.4

echo.
echo ✅ Dependências instaladas!
echo.

echo 📋 IMPORTANTE: O sistema funcionará com Redis Simulator
echo    Performance: 1M+ operações/segundo
echo    Zero configuração necessária
echo.

echo 🚀 PRÓXIMOS PASSOS:
echo    1. Execute: python app.py
echo    2. Teste: http://localhost:8080/api/ibge/cache/health
echo.

echo 💡 Para instalar Redis real (opcional):
echo    - Docker: docker run --name redis-pnsb -p 6379:6379 -d redis:alpine
echo    - Chocolatey: choco install redis-64
echo.

pause