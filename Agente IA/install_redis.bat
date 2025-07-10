@echo off
echo ========================================
echo  INSTALACAO REDIS PARA SISTEMA PNSB
echo ========================================
echo.

echo [1/4] Instalando dependencias Python...
pip install redis==5.0.1 python-redis-lock==4.0.0 APScheduler==3.10.4

echo.
echo [2/4] Baixando Redis para Windows...
echo Visite: https://github.com/microsoftarchive/redis/releases
echo Baixe: Redis-x64-3.0.504.msi
echo.
echo Ou use Docker:
echo docker run --name redis-pnsb -p 6379:6379 -d redis:alpine
echo.

echo [3/4] Configurando variaveis de ambiente...
echo Adicione estas variaveis ao seu sistema:
echo.
echo REDIS_URL=redis://localhost:6379/0
echo IBGE_CACHE_TTL=3600
echo ENABLE_REAL_APIS=true
echo.

echo [4/4] Testando instalacao...
echo Executando teste de conectividade...
python -c "
try:
    import redis
    r = redis.from_url('redis://localhost:6379/0')
    r.ping()
    print('✅ Redis conectado com sucesso!')
except Exception as e:
    print('⚠️ Redis nao conectado:', e)
    print('💡 Sistema funcionara com cache local como fallback')
"

echo.
echo ========================================
echo  INSTALACAO CONCLUIDA
echo ========================================
echo.
echo Proximos passos:
echo 1. Inicie o servidor Redis (se ainda nao estiver rodando)
echo 2. Execute: python app.py
echo 3. Teste: http://localhost:8080/api/ibge/cache/health
echo.
pause