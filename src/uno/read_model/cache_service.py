"""Cache service implementation for the Uno framework.

This module defines caching mechanisms for read models to improve
query performance in the CQRS pattern's query side.
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from typing import (
    Any, Dict, Generic, List, Optional, Set, Type, TypeVar, Union, Protocol,
    cast
)

from uno.read_model.read_model import ReadModel

# Type variables
T = TypeVar('T', bound=ReadModel)


class ReadModelCache(Generic[T], ABC):
    """
    Abstract base class for read model caches.
    
    Read model caches provide a way to cache read models for improved
    query performance.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the cache.
        
        Args:
            model_type: The type of read model this cache stores
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model from the cache.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found in the cache, None otherwise
        """
        pass
    
    @abstractmethod
    async def set(self, id: str, model: T, ttl: Optional[int] = None) -> None:
        """
        Set a read model in the cache.
        
        Args:
            id: The read model ID
            model: The read model to cache
            ttl: Optional time-to-live in seconds
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> None:
        """
        Delete a read model from the cache.
        
        Args:
            id: The read model ID
        """
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear the entire cache."""
        pass


class InMemoryReadModelCache(ReadModelCache[T]):
    """
    In-memory implementation of the read model cache.
    
    This implementation stores read models in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        default_ttl: Optional[int] = 3600,  # 1 hour default TTL
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the cache.
        
        Args:
            model_type: The type of read model this cache stores
            default_ttl: Optional default time-to-live in seconds
            logger: Optional logger instance
        """
        super().__init__(model_type, logger)
        self.default_ttl = default_ttl
        self._cache: Dict[str, T] = {}
        self._expiry: Dict[str, float] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model from the cache.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found in the cache, None otherwise
        """
        # Check if entry exists and is not expired
        if id in self._cache:
            if id in self._expiry and self._expiry[id] < time.time():
                # Entry has expired
                del self._cache[id]
                del self._expiry[id]
                return None
            
            return self._cache[id]
        
        return None
    
    async def set(self, id: str, model: T, ttl: Optional[int] = None) -> None:
        """
        Set a read model in the cache.
        
        Args:
            id: The read model ID
            model: The read model to cache
            ttl: Optional time-to-live in seconds
        """
        self._cache[id] = model
        
        # Set expiry if TTL is provided or a default exists
        if ttl is not None or self.default_ttl is not None:
            ttl_value = ttl if ttl is not None else self.default_ttl
            if ttl_value is not None:  # Additional check to ensure ttl_value is not None
                self._expiry[id] = time.time() + ttl_value
        
        # Start the cleanup task if it's not running
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired())
    
    async def delete(self, id: str) -> None:
        """
        Delete a read model from the cache.
        
        Args:
            id: The read model ID
        """
        if id in self._cache:
            del self._cache[id]
        
        if id in self._expiry:
            del self._expiry[id]
    
    async def clear(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()
        self._expiry.clear()
    
    async def _cleanup_expired(self) -> None:
        """Periodically clean up expired cache entries."""
        while True:
            try:
                # Sleep for a while
                await asyncio.sleep(60)  # Check every minute
                
                # Find expired entries
                now = time.time()
                expired_ids = [
                    id for id, expiry in self._expiry.items()
                    if expiry < now
                ]
                
                # Remove expired entries
                for id in expired_ids:
                    if id in self._cache:
                        del self._cache[id]
                    if id in self._expiry:
                        del self._expiry[id]
                
                if expired_ids:
                    self.logger.debug(f"Cleaned up {len(expired_ids)} expired cache entries")
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in cache cleanup task: {str(e)}")


class RedisReadModelCache(ReadModelCache[T]):
    """
    Redis implementation of the read model cache.
    
    This implementation uses Redis for caching read models, which is suitable
    for production applications and distributed environments.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        redis_client: Any,  # Using Any since we don't know the concrete type
        prefix: str = "read_model:",
        default_ttl: Optional[int] = 3600,  # 1 hour default TTL
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the cache.
        
        Args:
            model_type: The type of read model this cache stores
            redis_client: The Redis client
            prefix: Prefix for Redis keys
            default_ttl: Optional default time-to-live in seconds
            logger: Optional logger instance
        """
        super().__init__(model_type, logger)
        self.redis_client = redis_client
        self.prefix = prefix
        self.default_ttl = default_ttl
    
    def _get_key(self, id: str) -> str:
        """
        Get the Redis key for a read model ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The Redis key
        """
        return f"{self.prefix}{self.model_type.__name__}:{id}"
    
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model from the cache.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found in the cache, None otherwise
        """
        key = self._get_key(id)
        data = await self.redis_client.get(key)
        
        if data:
            try:
                # Deserialize the JSON and create the model
                model_data = json.loads(data)
                return self.model_type(**model_data)
            except Exception as e:
                self.logger.error(f"Error deserializing cached model {id}: {str(e)}")
                return None
        
        return None
    
    async def set(self, id: str, model: T, ttl: Optional[int] = None) -> None:
        """
        Set a read model in the cache.
        
        Args:
            id: The read model ID
            model: The read model to cache
            ttl: Optional time-to-live in seconds
        """
        key = self._get_key(id)
        
        try:
            # Serialize the model to JSON
            data = model.model_dump_json()
            
            # Set in Redis with TTL
            ttl_value = ttl if ttl is not None else self.default_ttl
            if ttl_value is not None:
                await self.redis_client.setex(key, ttl_value, data)
            else:
                await self.redis_client.set(key, data)
        except Exception as e:
            self.logger.error(f"Error caching model {id}: {str(e)}")
    
    async def delete(self, id: str) -> None:
        """
        Delete a read model from the cache.
        
        Args:
            id: The read model ID
        """
        key = self._get_key(id)
        await self.redis_client.delete(key)
    
    async def clear(self) -> None:
        """Clear all cached models of this type."""
        pattern = f"{self.prefix}{self.model_type.__name__}:*"
        cursor = 0
        
        while True:
            cursor, keys = await self.redis_client.scan(cursor, match=pattern)
            if keys:
                await self.redis_client.delete(*keys)
            
            if cursor == 0:
                break