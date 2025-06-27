"""Caching utilities for performance optimization."""

import hashlib
import json
import pickle
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union, Callable
from datetime import datetime, timedelta
import aiofiles
import asyncio
from functools import wraps

from .error_handling import ErrorHandler, safe_execute


class CacheManager:
    """Manager for file-based caching with TTL support."""
    
    def __init__(
        self, 
        cache_dir: Union[str, Path] = ".getsitedna_cache",
        default_ttl: int = 3600,  # 1 hour default
        max_size: int = 100 * 1024 * 1024,  # 100MB default
        cleanup_interval: int = 600  # 10 minutes
    ):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            default_ttl: Default time-to-live in seconds
            max_size: Maximum cache size in bytes
            cleanup_interval: How often to run cleanup in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.error_handler = ErrorHandler("CacheManager")
        self._last_cleanup = time.time()
        self._cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "errors": 0
        }
    
    def _get_cache_key(self, key: str) -> str:
        """Generate a safe cache key from input."""
        return hashlib.md5(key.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get cache file path for a key."""
        return self.cache_dir / f"{cache_key}.cache"
    
    def _get_metadata_path(self, cache_key: str) -> Path:
        """Get metadata file path for a key."""
        return self.cache_dir / f"{cache_key}.meta"
    
    def _is_expired(self, metadata: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if metadata.get("ttl") == -1:  # Never expires
            return False
        
        created_at = metadata.get("created_at", 0)
        ttl = metadata.get("ttl", self.default_ttl)
        return time.time() - created_at > ttl
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache."""
        cache_key = self._get_cache_key(key)
        cache_path = self._get_cache_path(cache_key)
        metadata_path = self._get_metadata_path(cache_key)
        
        try:
            # Check if files exist
            if not cache_path.exists() or not metadata_path.exists():
                self._cache_stats["misses"] += 1
                return default
            
            # Load metadata
            async with aiofiles.open(metadata_path, 'r') as f:
                metadata = json.loads(await f.read())
            
            # Check if expired
            if self._is_expired(metadata):
                await self._remove_cache_entry(cache_key)
                self._cache_stats["misses"] += 1
                return default
            
            # Load cached data
            async with aiofiles.open(cache_path, 'rb') as f:
                data = pickle.loads(await f.read())
            
            self._cache_stats["hits"] += 1
            return data
            
        except Exception as e:
            self.error_handler.handle_error(e)
            self._cache_stats["errors"] += 1
            return default
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        cache_key = self._get_cache_key(key)
        cache_path = self._get_cache_path(cache_key)
        metadata_path = self._get_metadata_path(cache_key)
        
        try:
            # Create metadata
            metadata = {
                "key": key,
                "created_at": time.time(),
                "ttl": ttl,
                "size": 0
            }
            
            # Serialize data
            serialized_data = pickle.dumps(value)
            metadata["size"] = len(serialized_data)
            
            # Check cache size limits
            await self._ensure_cache_space(metadata["size"])
            
            # Write cache file
            async with aiofiles.open(cache_path, 'wb') as f:
                await f.write(serialized_data)
            
            # Write metadata
            async with aiofiles.open(metadata_path, 'w') as f:
                await f.write(json.dumps(metadata))
            
            return True
            
        except Exception as e:
            self.error_handler.handle_error(e)
            self._cache_stats["errors"] += 1
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        cache_key = self._get_cache_key(key)
        return await self._remove_cache_entry(cache_key)
    
    async def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
            for meta_file in self.cache_dir.glob("*.meta"):
                meta_file.unlink()
            return True
        except Exception as e:
            self.error_handler.handle_error(e)
            return False
    
    async def _remove_cache_entry(self, cache_key: str) -> bool:
        """Remove a specific cache entry."""
        try:
            cache_path = self._get_cache_path(cache_key)
            metadata_path = self._get_metadata_path(cache_key)
            
            if cache_path.exists():
                cache_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
        except Exception as e:
            self.error_handler.handle_error(e)
            return False
    
    async def _ensure_cache_space(self, needed_size: int) -> None:
        """Ensure there's enough space in cache."""
        current_size = await self._get_cache_size()
        
        if current_size + needed_size > self.max_size:
            await self._evict_entries(needed_size)
    
    async def _get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            total_size += cache_file.stat().st_size
        return total_size
    
    async def _evict_entries(self, needed_size: int) -> None:
        """Evict cache entries to make space."""
        # Get all metadata files with their last access times
        entries = []
        for meta_file in self.cache_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                entries.append((meta_file.stem, metadata))
            except Exception:
                continue
        
        # Sort by creation time (LRU eviction)
        entries.sort(key=lambda x: x[1].get("created_at", 0))
        
        freed_size = 0
        for cache_key, metadata in entries:
            if freed_size >= needed_size:
                break
            
            await self._remove_cache_entry(cache_key)
            freed_size += metadata.get("size", 0)
            self._cache_stats["evictions"] += 1
    
    async def cleanup(self) -> None:
        """Clean up expired cache entries."""
        current_time = time.time()
        
        # Only run cleanup if enough time has passed
        if current_time - self._last_cleanup < self.cleanup_interval:
            return
        
        self._last_cleanup = current_time
        
        # Find and remove expired entries
        for meta_file in self.cache_dir.glob("*.meta"):
            try:
                with open(meta_file, 'r') as f:
                    metadata = json.load(f)
                
                if self._is_expired(metadata):
                    await self._remove_cache_entry(meta_file.stem)
                    
            except Exception as e:
                self.error_handler.handle_error(e)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests 
            if total_requests > 0 else 0
        )
        
        return {
            **self._cache_stats,
            "hit_rate": hit_rate,
            "cache_size": asyncio.run(self._get_cache_size()) if asyncio.get_event_loop().is_running() else 0,
            "cache_files": len(list(self.cache_dir.glob("*.cache")))
        }


class MemoryCache:
    """In-memory cache with TTL support for small, frequently accessed data."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """Initialize memory cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default time-to-live in seconds
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._access_order = []  # For LRU eviction
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from memory cache."""
        if key not in self._cache:
            return default
        
        entry = self._cache[key]
        
        # Check if expired
        if self._is_expired(entry):
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return default
        
        # Update access order for LRU
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
        
        return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in memory cache."""
        if ttl is None:
            ttl = self.default_ttl
        
        # Ensure space
        while len(self._cache) >= self.max_size:
            self._evict_lru()
        
        self._cache[key] = {
            "value": value,
            "created_at": time.time(),
            "ttl": ttl
        }
        
        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache."""
        if key in self._cache:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        self._access_order.clear()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired."""
        if entry.get("ttl") == -1:  # Never expires
            return False
        
        created_at = entry.get("created_at", 0)
        ttl = entry.get("ttl", self.default_ttl)
        return time.time() - created_at > ttl
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if self._access_order:
            lru_key = self._access_order.pop(0)
            del self._cache[lru_key]
    
    def cleanup(self) -> None:
        """Remove expired entries."""
        expired_keys = [
            key for key, entry in self._cache.items() 
            if self._is_expired(entry)
        ]
        
        for key in expired_keys:
            self.delete(key)


def cached(
    ttl: int = 3600,
    key_func: Optional[Callable] = None,
    use_memory: bool = False
):
    """Decorator for caching function results.
    
    Args:
        ttl: Time-to-live in seconds
        key_func: Function to generate cache key from args
        use_memory: Use memory cache instead of file cache
    """
    def decorator(func: Callable) -> Callable:
        cache = MemoryCache() if use_memory else CacheManager()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            if use_memory:
                result = cache.get(cache_key)
            else:
                result = await cache.get(cache_key)
            
            if result is not None:
                return result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            if use_memory:
                cache.set(cache_key, result, ttl)
            else:
                await cache.set(cache_key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            if use_memory:
                result = cache.get(cache_key)
            else:
                result = asyncio.run(cache.get(cache_key))
            
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            if use_memory:
                cache.set(cache_key, result, ttl)
            else:
                asyncio.run(cache.set(cache_key, result, ttl))
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global cache instances
file_cache = CacheManager()
memory_cache = MemoryCache()