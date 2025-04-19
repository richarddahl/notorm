"""
JWT token caching module.

This module provides caching mechanisms for JWT tokens to improve
performance and reduce load on authentication services.
"""

import logging
import time
from typing import Dict, Optional, Any, Callable, Tuple, Union, List
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from uno.caching import MemoryCache, RedisCache, DistributedCache
from uno.caching.config import CacheConfig
from uno.security.config import SecurityConfig, AuthenticationConfig


@dataclass
class TokenCacheConfig:
    """Configuration for JWT token cache."""
    
    enabled: bool = True
    """Whether token caching is enabled."""
    
    cache_type: str = "memory"
    """Type of cache to use: memory, redis, or memcached."""
    
    ttl: int = 300  # 5 minutes
    """Time-to-live for cached tokens in seconds."""
    
    max_size: int = 10000
    """Maximum number of tokens to store in the cache."""
    
    redis_url: Optional[str] = None
    """Redis connection URL for Redis cache."""
    
    blacklist_enabled: bool = False
    """Whether to enable token blacklisting for revoked tokens."""
    
    blacklist_ttl: int = 86400  # 24 hours
    """Time-to-live for blacklisted tokens in seconds."""


class TokenCache(ABC):
    """
    Base class for JWT token caches.
    
    Token caches store validated tokens to avoid re-validating tokens
    on each request, improving performance for high-traffic applications.
    """
    
    @abstractmethod
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get token claims from cache if available.
        
        Args:
            token: The token string
            
        Returns:
            Token claims if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set(self, token: str, claims: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """
        Cache token claims.
        
        Args:
            token: The token string
            claims: Token claims to cache
            ttl: Optional time-to-live in seconds
        """
        pass
    
    @abstractmethod
    def invalidate(self, token: str) -> None:
        """
        Invalidate a cached token.
        
        Args:
            token: The token string
        """
        pass
    
    @abstractmethod
    def is_blacklisted(self, jti: str) -> bool:
        """
        Check if a token ID is blacklisted.
        
        Args:
            jti: JWT ID to check
            
        Returns:
            True if blacklisted, False otherwise
        """
        pass
    
    @abstractmethod
    def blacklist(self, jti: str, expiry: int) -> None:
        """
        Blacklist a token ID.
        
        Args:
            jti: JWT ID to blacklist
            expiry: Token expiry timestamp
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all cached tokens."""
        pass


class MemoryTokenCache(TokenCache):
    """
    In-memory implementation of token cache.
    
    This implementation stores tokens in memory using an LRU cache.
    """
    
    def __init__(self, config: TokenCacheConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the memory token cache.
        
        Args:
            config: Token cache configuration
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.auth.token_cache")
        
        # Initialize memory caches
        self.token_cache = MemoryCache(
            name="token_cache",
            max_size=config.max_size,
            ttl=config.ttl
        )
        
        self.blacklist = MemoryCache(
            name="token_blacklist",
            max_size=config.max_size,
            ttl=config.blacklist_ttl
        )
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token claims from cache."""
        if not self.config.enabled:
            return None
        
        return self.token_cache.get(token)
    
    def set(self, token: str, claims: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache token claims."""
        if not self.config.enabled:
            return
        
        # Use TTL from claims['exp'] if available
        if ttl is None and 'exp' in claims:
            ttl = max(0, int(claims['exp'] - time.time()))
        
        ttl = ttl or self.config.ttl
        self.token_cache.set(token, claims, ttl)
    
    def invalidate(self, token: str) -> None:
        """Invalidate a cached token."""
        if not self.config.enabled:
            return
        
        self.token_cache.delete(token)
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token ID is blacklisted."""
        if not self.config.enabled or not self.config.blacklist_enabled:
            return False
        
        return self.blacklist.exists(jti)
    
    def blacklist(self, jti: str, expiry: int) -> None:
        """Blacklist a token ID."""
        if not self.config.enabled or not self.config.blacklist_enabled:
            return
        
        # Calculate TTL as time until expiry
        now = int(time.time())
        ttl = max(expiry - now, 60)  # At least 60 seconds
        ttl = min(ttl, self.config.blacklist_ttl)  # At most blacklist_ttl
        
        self.blacklist.set(jti, True, ttl)
    
    def clear(self) -> None:
        """Clear all cached tokens."""
        self.token_cache.clear()
        self.blacklist.clear()


class RedisTokenCache(TokenCache):
    """
    Redis implementation of token cache.
    
    This implementation stores tokens in Redis for distributed caching.
    """
    
    def __init__(self, config: TokenCacheConfig, logger: Optional[logging.Logger] = None):
        """
        Initialize the Redis token cache.
        
        Args:
            config: Token cache configuration
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger("uno.security.auth.token_cache")
        
        if not config.redis_url:
            raise ValueError("Redis URL must be provided for Redis token cache")
        
        # Initialize Redis caches
        self.token_cache = RedisCache(
            name="token_cache",
            redis_url=config.redis_url,
            ttl=config.ttl,
            prefix="token:"
        )
        
        self.blacklist = RedisCache(
            name="token_blacklist",
            redis_url=config.redis_url,
            ttl=config.blacklist_ttl,
            prefix="blacklist:"
        )
    
    def get(self, token: str) -> Optional[Dict[str, Any]]:
        """Get token claims from cache."""
        if not self.config.enabled:
            return None
        
        return self.token_cache.get(token)
    
    def set(self, token: str, claims: Dict[str, Any], ttl: Optional[int] = None) -> None:
        """Cache token claims."""
        if not self.config.enabled:
            return
        
        # Use TTL from claims['exp'] if available
        if ttl is None and 'exp' in claims:
            ttl = max(0, int(claims['exp'] - time.time()))
        
        ttl = ttl or self.config.ttl
        self.token_cache.set(token, claims, ttl)
    
    def invalidate(self, token: str) -> None:
        """Invalidate a cached token."""
        if not self.config.enabled:
            return
        
        self.token_cache.delete(token)
    
    def is_blacklisted(self, jti: str) -> bool:
        """Check if a token ID is blacklisted."""
        if not self.config.enabled or not self.config.blacklist_enabled:
            return False
        
        return self.blacklist.exists(jti)
    
    def blacklist(self, jti: str, expiry: int) -> None:
        """Blacklist a token ID."""
        if not self.config.enabled or not self.config.blacklist_enabled:
            return
        
        # Calculate TTL as time until expiry
        now = int(time.time())
        ttl = max(expiry - now, 60)  # At least 60 seconds
        ttl = min(ttl, self.config.blacklist_ttl)  # At most blacklist_ttl
        
        self.blacklist.set(jti, True, ttl)
    
    def clear(self) -> None:
        """Clear all cached tokens."""
        self.token_cache.clear()
        self.blacklist.clear()


def create_token_cache(
    config: Union[TokenCacheConfig, SecurityConfig, AuthenticationConfig],
    logger: Optional[logging.Logger] = None
) -> TokenCache:
    """
    Create a token cache based on configuration.
    
    Args:
        config: Token cache configuration or security configuration
        logger: Optional logger
        
    Returns:
        Token cache instance
    """
    logger = logger or logging.getLogger("uno.security.auth.token_cache")
    
    # Extract token cache config from various config types
    if isinstance(config, TokenCacheConfig):
        token_cache_config = config
    elif isinstance(config, SecurityConfig):
        auth_config = config.authentication
        token_cache_config = TokenCacheConfig(
            enabled=getattr(auth_config, "token_cache_enabled", True),
            cache_type=getattr(auth_config, "token_cache_type", "memory"),
            ttl=getattr(auth_config, "token_cache_ttl", 300),
            max_size=getattr(auth_config, "token_cache_max_size", 10000),
            redis_url=getattr(auth_config, "redis_url", None),
            blacklist_enabled=getattr(auth_config, "token_blacklist_enabled", False),
            blacklist_ttl=getattr(auth_config, "token_blacklist_ttl", 86400)
        )
    elif isinstance(config, AuthenticationConfig):
        token_cache_config = TokenCacheConfig(
            enabled=getattr(config, "token_cache_enabled", True),
            cache_type=getattr(config, "token_cache_type", "memory"),
            ttl=getattr(config, "token_cache_ttl", 300),
            max_size=getattr(config, "token_cache_max_size", 10000),
            redis_url=getattr(config, "redis_url", None),
            blacklist_enabled=getattr(config, "token_blacklist_enabled", False),
            blacklist_ttl=getattr(config, "token_blacklist_ttl", 86400)
        )
    else:
        raise TypeError(f"Unsupported config type: {type(config)}")
    
    # Create cache based on cache type
    if not token_cache_config.enabled:
        logger.info("Token caching is disabled")
        token_cache_config.enabled = False
        return MemoryTokenCache(token_cache_config, logger)
    
    cache_type = token_cache_config.cache_type.lower()
    if cache_type == "memory":
        logger.info("Using in-memory token cache")
        return MemoryTokenCache(token_cache_config, logger)
    elif cache_type == "redis":
        logger.info("Using Redis token cache")
        return RedisTokenCache(token_cache_config, logger)
    else:
        logger.warning(f"Unsupported cache type: {cache_type}, falling back to memory cache")
        return MemoryTokenCache(token_cache_config, logger)