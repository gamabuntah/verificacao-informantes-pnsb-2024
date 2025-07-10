"""
Redis Cache Service - Sistema de cache distribuído para o projeto PNSB
Substitui o cache em memória por cache Redis para melhor performance e persistência
"""

import json
import pickle
import time
import os
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import logging

# Imports opcionais com fallback
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

try:
    from redis_lock import Lock
    REDIS_LOCK_AVAILABLE = True
except ImportError:
    REDIS_LOCK_AVAILABLE = False
    Lock = None

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RedisCache:
    """
    Serviço de cache Redis com funcionalidades avançadas:
    - TTL automático
    - Serialização inteligente
    - Locks distribuídos
    - Métricas de performance
    - Fallback para cache local
    """
    
    def __init__(self, redis_url: str = None, default_ttl: int = 3600):
        """
        Inicializa o cache Redis
        
        Args:
            redis_url: URL de conexão Redis (padrão: env REDIS_URL)
            default_ttl: TTL padrão em segundos (padrão: 1 hora)
        """
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self.redis_client = None
        self.fallback_cache = {}  # Cache local como fallback
        self.metrics = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0,
            'fallback_uses': 0
        }
        
        # Tentar conectar ao Redis
        self._connect()
    
    def _connect(self) -> bool:
        """
        Estabelece conexão com Redis com retry automático
        Se Redis não estiver disponível, usa simulador automático
        
        Returns:
            bool: True se conectou com sucesso, False caso contrário
        """
        try:
            # Tentar Redis real primeiro (se disponível)
            if not REDIS_AVAILABLE:
                raise ImportError("Redis não instalado")
                
            self.redis_client = redis.from_url(
                self.redis_url,
                decode_responses=False,  # Manter bytes para pickle
                socket_connect_timeout=2,
                socket_timeout=2,
                retry_on_timeout=False
            )
            
            # Testar conexão
            self.redis_client.ping()
            logger.info("✅ Conectado ao Redis real com sucesso")
            return True
            
        except Exception as e:
            logger.info(f"🎭 Redis não disponível ({str(e)[:50]}...), usando simulador automático")
            
            # Usar simulador Redis automático
            try:
                from .redis_simulator import from_url
                self.redis_client = from_url(
                    self.redis_url,
                    decode_responses=False
                )
                
                # Testar conexão do simulador
                self.redis_client.ping()
                logger.info("🚀 Redis Simulator ativado com sucesso - performance total!")
                return True
                
            except Exception as sim_error:
                logger.warning(f"⚠️ Erro no simulador Redis: {sim_error}")
                logger.info("📋 Usando cache local como fallback final")
                self.redis_client = None
                return False
    
    def _serialize_value(self, value: Any) -> bytes:
        """
        Serializa valor para armazenamento no Redis
        Usa pickle para objetos complexos, JSON para tipos simples
        
        Args:
            value: Valor a ser serializado
            
        Returns:
            bytes: Valor serializado
        """
        try:
            # Tentar JSON primeiro (mais rápido e legível)
            if isinstance(value, (str, int, float, bool, list, dict)):
                return json.dumps(value, ensure_ascii=False).encode('utf-8')
            else:
                # Usar pickle para objetos complexos
                return pickle.dumps(value)
        except Exception as e:
            logger.warning(f"Erro na serialização, usando pickle: {e}")
            return pickle.dumps(value)
    
    def _deserialize_value(self, data: bytes) -> Any:
        """
        Deserializa valor do Redis
        
        Args:
            data: Dados serializados
            
        Returns:
            Any: Valor deserializado
        """
        try:
            # Tentar JSON primeiro
            return json.loads(data.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Tentar pickle
                return pickle.loads(data)
            except Exception as e:
                logger.error(f"Erro na deserialização: {e}")
                return None
    
    def get(self, key: str) -> Optional[Any]:
        """
        Recupera valor do cache
        
        Args:
            key: Chave do cache
            
        Returns:
            Any: Valor armazenado ou None se não encontrado
        """
        try:
            if self.redis_client:
                # Tentar Redis primeiro
                data = self.redis_client.get(f"pnsb:{key}")
                if data is not None:
                    self.metrics['hits'] += 1
                    # Se data já é um objeto deserializado (simulador), retornar direto
                    if isinstance(data, (dict, list, str, int, float, bool)) and not isinstance(data, bytes):
                        return data
                    return self._deserialize_value(data)
                else:
                    self.metrics['misses'] += 1
                    return None
            else:
                # Usar fallback local
                self.metrics['fallback_uses'] += 1
                cached_item = self.fallback_cache.get(key)
                if cached_item:
                    # Verificar TTL
                    if time.time() - cached_item['timestamp'] < cached_item['ttl']:
                        self.metrics['hits'] += 1
                        return cached_item['value']
                    else:
                        # Expirado
                        del self.fallback_cache[key]
                        self.metrics['misses'] += 1
                        return None
                else:
                    self.metrics['misses'] += 1
                    return None
                    
        except Exception as e:
            logger.error(f"Erro ao recuperar cache para '{key}': {e}")
            self.metrics['errors'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Armazena valor no cache
        
        Args:
            key: Chave do cache
            value: Valor a ser armazenado
            ttl: Time to Live em segundos (opcional)
            
        Returns:
            bool: True se armazenado com sucesso
        """
        ttl = ttl or self.default_ttl
        
        try:
            if self.redis_client:
                # Armazenar no Redis
                serialized_value = self._serialize_value(value)
                result = self.redis_client.setex(
                    f"pnsb:{key}", 
                    ttl, 
                    serialized_value
                )
                if result:
                    self.metrics['sets'] += 1
                    return True
                    
            # Fallback para cache local
            self.metrics['fallback_uses'] += 1
            self.fallback_cache[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
            self.metrics['sets'] += 1
            return True
            
        except Exception as e:
            logger.error(f"Erro ao armazenar cache para '{key}': {e}")
            self.metrics['errors'] += 1
            return False
    
    def delete(self, key: str) -> bool:
        """
        Remove valor do cache
        
        Args:
            key: Chave a ser removida
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            if self.redis_client:
                result = self.redis_client.delete(f"pnsb:{key}")
                return bool(result)
            else:
                # Fallback local
                if key in self.fallback_cache:
                    del self.fallback_cache[key]
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Erro ao deletar cache para '{key}': {e}")
            self.metrics['errors'] += 1
            return False
    
    def exists(self, key: str) -> bool:
        """
        Verifica se chave existe no cache
        
        Args:
            key: Chave a ser verificada
            
        Returns:
            bool: True se existe
        """
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(f"pnsb:{key}"))
            else:
                # Fallback local com verificação de TTL
                cached_item = self.fallback_cache.get(key)
                if cached_item:
                    if time.time() - cached_item['timestamp'] < cached_item['ttl']:
                        return True
                    else:
                        del self.fallback_cache[key]
                        return False
                return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar existência de '{key}': {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Remove todas as chaves que correspondem ao padrão
        
        Args:
            pattern: Padrão de busca (ex: "ibge:*")
            
        Returns:
            int: Número de chaves removidas
        """
        try:
            if self.redis_client:
                keys = self.redis_client.keys(f"pnsb:{pattern}")
                if keys:
                    return self.redis_client.delete(*keys)
                return 0
            else:
                # Fallback local
                keys_to_delete = [
                    k for k in self.fallback_cache.keys() 
                    if pattern.replace('*', '') in k
                ]
                for key in keys_to_delete:
                    del self.fallback_cache[key]
                return len(keys_to_delete)
                
        except Exception as e:
            logger.error(f"Erro ao limpar padrão '{pattern}': {e}")
            return 0
    
    def get_with_lock(self, key: str, lock_timeout: int = 10) -> tuple[Optional[Any], Lock]:
        """
        Recupera valor com lock distribuído (útil para evitar cache stampede)
        
        Args:
            key: Chave do cache
            lock_timeout: Timeout do lock em segundos
            
        Returns:
            tuple: (valor, lock_object)
        """
        if not self.redis_client or not REDIS_LOCK_AVAILABLE:
            # Sem Redis ou redis-lock, não há lock distribuído
            return self.get(key), None
        
        try:
            lock = Lock(self.redis_client, f"lock:pnsb:{key}", timeout=lock_timeout)
            value = self.get(key)
            return value, lock
        except Exception as e:
            logger.error(f"Erro ao obter lock para '{key}': {e}")
            return self.get(key), None
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas de performance do cache
        
        Returns:
            Dict: Métricas detalhadas
        """
        total_requests = self.metrics['hits'] + self.metrics['misses']
        hit_rate = (self.metrics['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'hits': self.metrics['hits'],
            'misses': self.metrics['misses'],
            'sets': self.metrics['sets'],
            'errors': self.metrics['errors'],
            'fallback_uses': self.metrics['fallback_uses'],
            'hit_rate_percent': round(hit_rate, 2),
            'total_requests': total_requests,
            'redis_connected': self.redis_client is not None,
            'cache_size_local': len(self.fallback_cache),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict[str, Any]:
        """
        Verifica saúde do sistema de cache
        
        Returns:
            Dict: Status de saúde
        """
        health = {
            'status': 'healthy',
            'redis_connected': False,
            'fallback_available': True,
            'last_check': datetime.now().isoformat(),
            'issues': []
        }
        
        # Testar Redis
        try:
            if self.redis_client:
                self.redis_client.ping()
                health['redis_connected'] = True
            else:
                health['issues'].append('Redis não conectado, usando fallback local')
        except Exception as e:
            health['issues'].append(f'Erro no Redis: {str(e)}')
            # Tentar reconectar
            self._connect()
        
        # Verificar fallback
        try:
            test_key = 'health_check_test'
            self.set(test_key, 'test_value', 5)
            value = self.get(test_key)
            if value != 'test_value':
                health['issues'].append('Cache não está funcionando corretamente')
                health['status'] = 'degraded'
            self.delete(test_key)
        except Exception as e:
            health['issues'].append(f'Erro no teste de cache: {str(e)}')
            health['status'] = 'unhealthy'
        
        return health
    
    def preload_common_data(self, data_loaders: Dict[str, callable]) -> Dict[str, bool]:
        """
        Pre-carrega dados comuns no cache (cache warming)
        
        Args:
            data_loaders: Dict com chave->função para carregar dados
            
        Returns:
            Dict: Status do carregamento para cada chave
        """
        results = {}
        
        for key, loader_func in data_loaders.items():
            try:
                if not self.exists(key):
                    logger.info(f"🔄 Pre-carregando cache para '{key}'...")
                    data = loader_func()
                    if data is not None:
                        self.set(key, data)
                        results[key] = True
                        logger.info(f"✅ Cache carregado para '{key}'")
                    else:
                        results[key] = False
                        logger.warning(f"⚠️ Falha ao carregar dados para '{key}'")
                else:
                    results[key] = True
                    logger.info(f"📋 Cache já existe para '{key}'")
                    
            except Exception as e:
                logger.error(f"❌ Erro ao pre-carregar '{key}': {e}")
                results[key] = False
        
        return results

# Instância global do cache Redis
redis_cache = RedisCache()

# Função helper para migração gradual
def get_cache_instance():
    """
    Retorna instância do cache Redis
    Facilita migração gradual do código existente
    """
    return redis_cache