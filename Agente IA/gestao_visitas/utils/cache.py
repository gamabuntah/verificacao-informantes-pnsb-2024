import json
import pickle
import hashlib
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Optional, Callable
import os

class SimpleCache:
    """Cache simples em memória com TTL"""
    
    def __init__(self, default_ttl=300):  # 5 minutos padrão
        self._cache = {}
        self._ttl = {}
        self.default_ttl = default_ttl
    
    def _is_expired(self, key):
        """Verifica se uma chave expirou"""
        if key not in self._ttl:
            return True
        return time.time() > self._ttl[key]
    
    def get(self, key):
        """Obtém valor do cache"""
        if key in self._cache and not self._is_expired(key):
            return self._cache[key]
        return None
    
    def set(self, key, value, ttl=None):
        """Define valor no cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        self._cache[key] = value
        self._ttl[key] = time.time() + ttl
    
    def delete(self, key):
        """Remove valor do cache"""
        self._cache.pop(key, None)
        self._ttl.pop(key, None)
    
    def clear(self):
        """Limpa todo o cache"""
        self._cache.clear()
        self._ttl.clear()
    
    def cleanup(self):
        """Remove itens expirados"""
        expired_keys = [
            key for key in self._cache.keys() 
            if self._is_expired(key)
        ]
        for key in expired_keys:
            self.delete(key)
    
    def size(self):
        """Retorna número de itens no cache"""
        self.cleanup()
        return len(self._cache)

class FileCache:
    """Cache baseado em arquivos"""
    
    def __init__(self, cache_dir="cache", default_ttl=3600):
        self.cache_dir = cache_dir
        self.default_ttl = default_ttl
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_file_path(self, key):
        """Gera caminho do arquivo para a chave"""
        # Cria hash da chave para nome de arquivo seguro
        key_hash = hashlib.md5(str(key).encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{key_hash}.cache")
    
    def _is_expired(self, file_path):
        """Verifica se arquivo expirou"""
        if not os.path.exists(file_path):
            return True
        
        # Lê timestamp do início do arquivo
        try:
            with open(file_path, 'rb') as f:
                timestamp = pickle.load(f)
                return time.time() > timestamp
        except:
            return True
    
    def get(self, key):
        """Obtém valor do cache"""
        file_path = self._get_file_path(key)
        
        if self._is_expired(file_path):
            return None
        
        try:
            with open(file_path, 'rb') as f:
                pickle.load(f)  # Skip timestamp
                return pickle.load(f)
        except:
            return None
    
    def set(self, key, value, ttl=None):
        """Define valor no cache"""
        if ttl is None:
            ttl = self.default_ttl
        
        file_path = self._get_file_path(key)
        expire_time = time.time() + ttl
        
        try:
            with open(file_path, 'wb') as f:
                pickle.dump(expire_time, f)
                pickle.dump(value, f)
        except Exception as e:
            print(f"Erro ao salvar cache: {e}")
    
    def delete(self, key):
        """Remove valor do cache"""
        file_path = self._get_file_path(key)
        try:
            os.remove(file_path)
        except OSError:
            pass
    
    def clear(self):
        """Limpa todo o cache"""
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                try:
                    os.remove(os.path.join(self.cache_dir, filename))
                except OSError:
                    pass
    
    def cleanup(self):
        """Remove arquivos expirados"""
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.cache'):
                file_path = os.path.join(self.cache_dir, filename)
                if self._is_expired(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass

class CacheManager:
    """Gerenciador de cache com múltiplos backends"""
    
    def __init__(self, use_file_cache=False, cache_dir="cache"):
        if use_file_cache:
            self.cache = FileCache(cache_dir)
        else:
            self.cache = SimpleCache()
        
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0
        }
    
    def get(self, key):
        """Obtém valor do cache com estatísticas"""
        value = self.cache.get(key)
        if value is not None:
            self.stats['hits'] += 1
        else:
            self.stats['misses'] += 1
        return value
    
    def set(self, key, value, ttl=None):
        """Define valor no cache com estatísticas"""
        self.cache.set(key, value, ttl)
        self.stats['sets'] += 1
    
    def delete(self, key):
        """Remove valor do cache"""
        self.cache.delete(key)
    
    def clear(self):
        """Limpa cache e estatísticas"""
        self.cache.clear()
        self.stats = {'hits': 0, 'misses': 0, 'sets': 0}
    
    def get_stats(self):
        """Retorna estatísticas do cache"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests
        }

# Instância global do cache
cache_manager = CacheManager()

def cached(ttl=300, key_prefix=""):
    """Decorator para cache de funções"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Gerar chave do cache
            key_data = {
                'func_name': func.__name__,
                'args': args,
                'kwargs': kwargs,
                'prefix': key_prefix
            }
            cache_key = hashlib.md5(
                json.dumps(key_data, sort_keys=True, default=str).encode()
            ).hexdigest()
            
            # Tentar obter do cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Executar função e cachear resultado
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        # Adicionar método para limpar cache da função
        wrapper.clear_cache = lambda: cache_manager.clear()
        wrapper.cache_key = lambda *args, **kwargs: hashlib.md5(
            json.dumps({
                'func_name': func.__name__,
                'args': args,
                'kwargs': kwargs,
                'prefix': key_prefix
            }, sort_keys=True, default=str).encode()
        ).hexdigest()
        
        return wrapper
    return decorator

def cache_model_query(model_class, ttl=600):
    """Decorator específico para cache de queries de modelo"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"model_{model_class.__name__}_{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = func(*args, **kwargs)
            
            # Converter resultado para formato cacheável
            if hasattr(result, 'to_dict'):
                cache_data = result.to_dict()
            elif isinstance(result, list) and result and hasattr(result[0], 'to_dict'):
                cache_data = [item.to_dict() for item in result]
            else:
                cache_data = result
            
            cache_manager.set(cache_key, cache_data, ttl)
            return result
        
        return wrapper
    return decorator

class CacheUtils:
    """Utilitários para cache"""
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalida cache por padrão (simplificado)"""
        # Para implementação completa, seria necessário iterar sobre as chaves
        # Por simplicidade, limparemos todo o cache quando houver padrão
        if pattern:
            cache_manager.clear()
    
    @staticmethod
    def warm_up_cache():
        """Aquece o cache com dados frequentemente acessados"""
        from ..models.agendamento import Visita
        from ..models.contatos import Contato
        from ..config import MUNICIPIOS, TIPOS_PESQUISA, STATUS_VISITA
        
        # Cache configurações estáticas
        cache_manager.set('config_municipios', MUNICIPIOS, ttl=86400)  # 24h
        cache_manager.set('config_tipos_pesquisa', TIPOS_PESQUISA, ttl=86400)
        cache_manager.set('config_status_visita', STATUS_VISITA, ttl=86400)
        
        # Cache estatísticas básicas
        try:
            total_visitas = Visita.query.count()
            total_contatos = Contato.query.count()
            
            cache_manager.set('stats_total_visitas', total_visitas, ttl=3600)  # 1h
            cache_manager.set('stats_total_contatos', total_contatos, ttl=3600)
        except:
            pass  # Ignora erros se BD não estiver disponível
    
    @staticmethod
    def get_cache_info():
        """Retorna informações do cache"""
        stats = cache_manager.get_stats()
        
        if hasattr(cache_manager.cache, 'size'):
            stats['size'] = cache_manager.cache.size()
        
        return stats