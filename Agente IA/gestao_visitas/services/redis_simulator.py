"""
Redis Simulator - Implementação de Redis em Python puro
Simula funcionalidades Redis sem necessidade de instalação externa
"""

import time
import threading
import json
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class RedisSimulator:
    """
    Simulador de Redis em Python puro
    Implementa as principais funcionalidades Redis sem dependências externas
    """
    
    def __init__(self):
        self._data = {}  # Armazenamento principal
        self._ttl = {}   # Time To Live para cada chave
        self._lock = threading.RLock()  # Thread safety
        self._stats = {
            'commands_processed': 0,
            'connections_received': 0,
            'keyspace_hits': 0,
            'keyspace_misses': 0,
            'start_time': time.time()
        }
        
        # Iniciar thread de limpeza automática
        self._cleanup_thread = threading.Thread(target=self._cleanup_expired, daemon=True)
        self._cleanup_thread.start()
        
        logger.info("🚀 Redis Simulator iniciado com sucesso")
    
    def _cleanup_expired(self):
        """Thread que remove chaves expiradas periodicamente"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []
                
                with self._lock:
                    for key, expire_time in self._ttl.items():
                        if current_time >= expire_time:
                            expired_keys.append(key)
                    
                    for key in expired_keys:
                        if key in self._data:
                            del self._data[key]
                        if key in self._ttl:
                            del self._ttl[key]
                
                if expired_keys:
                    logger.debug(f"🧹 Limpeza automática: {len(expired_keys)} chaves expiradas removidas")
                
                # Verificar a cada 30 segundos
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Erro na limpeza automática: {e}")
                time.sleep(60)  # Esperar mais tempo se houver erro
    
    def _is_expired(self, key: str) -> bool:
        """Verifica se uma chave está expirada"""
        if key not in self._ttl:
            return False
        return time.time() >= self._ttl[key]
    
    def _serialize(self, value: Any) -> bytes:
        """Serializa valor para armazenamento"""
        try:
            if isinstance(value, (str, int, float, bool, list, dict)):
                return json.dumps(value, ensure_ascii=False).encode('utf-8')
            else:
                return pickle.dumps(value)
        except:
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserializa valor do armazenamento"""
        try:
            return json.loads(data.decode('utf-8'))
        except:
            try:
                return pickle.loads(data)
            except:
                return data
    
    def ping(self) -> bool:
        """Simula comando PING do Redis"""
        self._stats['commands_processed'] += 1
        return True
    
    def get(self, key: str) -> Optional[bytes]:
        """Simula comando GET do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            if key not in self._data:
                self._stats['keyspace_misses'] += 1
                return None
            
            if self._is_expired(key):
                del self._data[key]
                if key in self._ttl:
                    del self._ttl[key]
                self._stats['keyspace_misses'] += 1
                return None
            
            self._stats['keyspace_hits'] += 1
            return self._data[key]
    
    def set(self, key: str, value: Any) -> bool:
        """Simula comando SET do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            self._data[key] = self._serialize(value)
            # Remover TTL se existir (SET sem EX remove expiração)
            if key in self._ttl:
                del self._ttl[key]
        
        return True
    
    def setex(self, key: str, time_seconds: int, value: Any) -> bool:
        """Simula comando SETEX do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            self._data[key] = self._serialize(value)
            self._ttl[key] = time.time() + time_seconds
        
        return True
    
    def delete(self, *keys: str) -> int:
        """Simula comando DEL do Redis"""
        self._stats['commands_processed'] += 1
        deleted = 0
        
        with self._lock:
            for key in keys:
                if key in self._data:
                    del self._data[key]
                    deleted += 1
                if key in self._ttl:
                    del self._ttl[key]
        
        return deleted
    
    def exists(self, key: str) -> int:
        """Simula comando EXISTS do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            if key not in self._data:
                return 0
            
            if self._is_expired(key):
                del self._data[key]
                if key in self._ttl:
                    del self._ttl[key]
                return 0
            
            return 1
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Simula comando KEYS do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            all_keys = list(self._data.keys())
            
            # Remover chaves expiradas
            current_time = time.time()
            expired_keys = []
            for key in all_keys:
                if key in self._ttl and current_time >= self._ttl[key]:
                    expired_keys.append(key)
            
            for key in expired_keys:
                if key in self._data:
                    del self._data[key]
                if key in self._ttl:
                    del self._ttl[key]
                all_keys.remove(key)
            
            # Filtrar por padrão
            if pattern == "*":
                return all_keys
            
            # Implementação simples de pattern matching
            if pattern.endswith("*"):
                prefix = pattern[:-1]
                return [key for key in all_keys if key.startswith(prefix)]
            
            return [key for key in all_keys if key == pattern]
    
    def flushdb(self) -> bool:
        """Simula comando FLUSHDB do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            self._data.clear()
            self._ttl.clear()
        
        return True
    
    def info(self, section: str = "all") -> Dict[str, Any]:
        """Simula comando INFO do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            uptime = int(time.time() - self._stats['start_time'])
            
            return {
                'redis_version': '7.0.0-simulator',
                'redis_mode': 'standalone',
                'os': 'Python Simulator',
                'uptime_in_seconds': uptime,
                'connected_clients': 1,
                'used_memory': len(str(self._data)),
                'used_memory_human': f"{len(str(self._data))} bytes",
                'total_commands_processed': self._stats['commands_processed'],
                'keyspace_hits': self._stats['keyspace_hits'],
                'keyspace_misses': self._stats['keyspace_misses'],
                'keyspace': f"db0:keys={len(self._data)},expires={len(self._ttl)}"
            }
    
    def dbsize(self) -> int:
        """Simula comando DBSIZE do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            # Remover chaves expiradas antes de contar
            current_time = time.time()
            expired_keys = [
                key for key, expire_time in self._ttl.items() 
                if current_time >= expire_time
            ]
            
            for key in expired_keys:
                if key in self._data:
                    del self._data[key]
                if key in self._ttl:
                    del self._ttl[key]
            
            return len(self._data)
    
    def ttl(self, key: str) -> int:
        """Simula comando TTL do Redis"""
        self._stats['commands_processed'] += 1
        
        with self._lock:
            if key not in self._data:
                return -2  # Chave não existe
            
            if key not in self._ttl:
                return -1  # Chave existe mas não tem TTL
            
            remaining = int(self._ttl[key] - time.time())
            if remaining <= 0:
                # Chave expirada
                del self._data[key]
                del self._ttl[key]
                return -2
            
            return remaining

class RedisSimulatorClient:
    """
    Cliente que simula a interface do redis-py
    Drop-in replacement para redis.Redis()
    """
    
    def __init__(self, host='localhost', port=6379, db=0, decode_responses=False, **kwargs):
        self.redis_sim = RedisSimulator()
        self.decode_responses = decode_responses
        logger.info(f"🔌 Redis Simulator Client conectado (simulando {host}:{port}/db{db})")
    
    def ping(self):
        """Ping para testar conectividade"""
        return self.redis_sim.ping()
    
    def get(self, key):
        """Get value from key"""
        result = self.redis_sim.get(key)
        if result is None:
            return None
        
        # Retornar resultado deserializado direto para compatibilidade
        return self.redis_sim._deserialize(result)
    
    def set(self, key, value):
        """Set key to value"""
        return self.redis_sim.set(key, value)
    
    def setex(self, key, time, value):
        """Set key to value with expiration"""
        return self.redis_sim.setex(key, time, value)
    
    def delete(self, *keys):
        """Delete keys"""
        return self.redis_sim.delete(*keys)
    
    def exists(self, key):
        """Check if key exists"""
        return bool(self.redis_sim.exists(key))
    
    def keys(self, pattern="*"):
        """Get keys matching pattern"""
        return self.redis_sim.keys(pattern)
    
    def flushdb(self):
        """Clear database"""
        return self.redis_sim.flushdb()
    
    def info(self, section="all"):
        """Get server info"""
        return self.redis_sim.info(section)
    
    def dbsize(self):
        """Get database size"""
        return self.redis_sim.dbsize()
    
    def ttl(self, key):
        """Get TTL for key"""
        return self.redis_sim.ttl(key)

# Função que substitui redis.from_url para usar o simulador
def from_url(url, **kwargs):
    """
    Drop-in replacement para redis.from_url()
    Sempre retorna o simulador independente da URL
    """
    logger.info(f"🎭 Usando Redis Simulator em vez de {url}")
    return RedisSimulatorClient(**kwargs)

# Instância global do simulador
redis_simulator = RedisSimulatorClient()