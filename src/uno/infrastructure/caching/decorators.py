"""Cache decorators module.

This module provides decorators for caching function results.
"""

import functools
import inspect
import asyncio
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, TypeVar, cast

from uno.caching.manager import get_cache_manager
from uno.caching.key import get_function_cache_key

T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])
AsyncF = TypeVar('AsyncF', bound=Callable[..., Any])


def cached(ttl: Optional[int] = None, key_prefix: Optional[str] = None,
          region: Optional[str] = None, arg_preprocessors: Optional[Dict[str, Callable]] = None,
          invalidate_on_args: Optional[List[Union[int, str]]] = None):
    """Decorator for caching function results.
    
    Args:
        ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
        key_prefix: Optional prefix for the cache key.
        region: Optional cache region name.
        arg_preprocessors: Optional mapping of argument names/positions to preprocessor functions.
        invalidate_on_args: Optional list of argument names/positions that trigger cache invalidation.
    
    Returns:
        Decorated function that uses caching.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the cache manager
            cache_manager = get_cache_manager()
            
            # Check if caching is enabled
            if not cache_manager.initialized or not cache_manager.config.enabled:
                return func(*args, **kwargs)
            
            # Check if we should invalidate based on arguments
            if invalidate_on_args:
                sig = inspect.signature(func)
                params = sig.bind(*args, **kwargs).arguments
                
                for arg_name in invalidate_on_args:
                    if isinstance(arg_name, int):
                        # Positional argument - check if it's True or a special value
                        if arg_name < len(args) and (args[arg_name] is True or 
                                                  args[arg_name] == 'invalidate'):
                            # Generate a cache key and invalidate it
                            cache_key = get_function_cache_key(
                                func, args[:arg_name] + args[arg_name+1:], kwargs,
                                key_prefix or "", True, arg_preprocessors
                            )
                            cache_manager.invalidate_pattern(f"*{cache_key}*")
                            # Execute the function without caching
                            return func(*args, **kwargs)
                    else:
                        # Keyword argument - check if it's True or a special value
                        if arg_name in params and (params[arg_name] is True or 
                                                params[arg_name] == 'invalidate'):
                            # Make a copy of kwargs without the invalidation flag
                            kwargs_copy = kwargs.copy()
                            kwargs_copy.pop(arg_name, None)
                            # Generate a cache key and invalidate it
                            cache_key = get_function_cache_key(
                                func, args, kwargs_copy,
                                key_prefix or "", True, arg_preprocessors
                            )
                            cache_manager.invalidate_pattern(f"*{cache_key}*")
                            # Execute the function without caching
                            return func(*args, **kwargs)
            
            # Create cache key
            cache_key = get_function_cache_key(
                func, args, kwargs, key_prefix or "", True, arg_preprocessors
            )
            
            # Try to get from cache
            with cache_manager.cache_context(region):
                cached_value = cache_manager.get(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute the function
                result = func(*args, **kwargs)
                
                # Cache the result
                cache_manager.set(cache_key, result, ttl)
                
                return result
        
        return cast(F, wrapper)
    
    return decorator


def async_cached(ttl: Optional[int] = None, key_prefix: Optional[str] = None,
                region: Optional[str] = None, arg_preprocessors: Optional[Dict[str, Callable]] = None,
                invalidate_on_args: Optional[List[Union[int, str]]] = None):
    """Decorator for caching async function results.
    
    Args:
        ttl: Optional time-to-live in seconds. If not provided, the default TTL is used.
        key_prefix: Optional prefix for the cache key.
        region: Optional cache region name.
        arg_preprocessors: Optional mapping of argument names/positions to preprocessor functions.
        invalidate_on_args: Optional list of argument names/positions that trigger cache invalidation.
    
    Returns:
        Decorated async function that uses caching.
    """
    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the cache manager
            cache_manager = get_cache_manager()
            
            # Check if caching is enabled
            if not cache_manager.initialized or not cache_manager.config.enabled:
                return await func(*args, **kwargs)
            
            # Check if we should invalidate based on arguments
            if invalidate_on_args:
                sig = inspect.signature(func)
                params = sig.bind(*args, **kwargs).arguments
                
                for arg_name in invalidate_on_args:
                    if isinstance(arg_name, int):
                        # Positional argument - check if it's True or a special value
                        if arg_name < len(args) and (args[arg_name] is True or 
                                                  args[arg_name] == 'invalidate'):
                            # Generate a cache key and invalidate it
                            cache_key = get_function_cache_key(
                                func, args[:arg_name] + args[arg_name+1:], kwargs,
                                key_prefix or "", True, arg_preprocessors
                            )
                            await cache_manager.invalidate_pattern_async(f"*{cache_key}*")
                            # Execute the function without caching
                            return await func(*args, **kwargs)
                    else:
                        # Keyword argument - check if it's True or a special value
                        if arg_name in params and (params[arg_name] is True or 
                                                params[arg_name] == 'invalidate'):
                            # Make a copy of kwargs without the invalidation flag
                            kwargs_copy = kwargs.copy()
                            kwargs_copy.pop(arg_name, None)
                            # Generate a cache key and invalidate it
                            cache_key = get_function_cache_key(
                                func, args, kwargs_copy,
                                key_prefix or "", True, arg_preprocessors
                            )
                            await cache_manager.invalidate_pattern_async(f"*{cache_key}*")
                            # Execute the function without caching
                            return await func(*args, **kwargs)
            
            # Create cache key
            cache_key = get_function_cache_key(
                func, args, kwargs, key_prefix or "", True, arg_preprocessors
            )
            
            # Try to get from cache
            async with cache_manager.cache_context_async(region):
                cached_value = await cache_manager.get_async(cache_key)
                if cached_value is not None:
                    return cached_value
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Cache the result
                await cache_manager.set_async(cache_key, result, ttl)
                
                return result
        
        return cast(AsyncF, wrapper)
    
    return decorator


def invalidate_cache(key_pattern: str, region: Optional[str] = None):
    """Decorator for invalidating cache entries matching a pattern.
    
    Args:
        key_pattern: The pattern to match against cache keys.
        region: Optional cache region name.
    
    Returns:
        Decorated function that invalidates cache entries before execution.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the cache manager
            cache_manager = get_cache_manager()
            
            # Check if caching is enabled
            if not cache_manager.initialized or not cache_manager.config.enabled:
                return func(*args, **kwargs)
            
            # Invalidate cache entries
            with cache_manager.cache_context(region):
                cache_manager.invalidate_pattern(key_pattern)
            
            # Execute the function
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def async_invalidate_cache(key_pattern: str, region: Optional[str] = None):
    """Decorator for invalidating cache entries matching a pattern in async functions.
    
    Args:
        key_pattern: The pattern to match against cache keys.
        region: Optional cache region name.
    
    Returns:
        Decorated async function that invalidates cache entries before execution.
    """
    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the cache manager
            cache_manager = get_cache_manager()
            
            # Check if caching is enabled
            if not cache_manager.initialized or not cache_manager.config.enabled:
                return await func(*args, **kwargs)
            
            # Invalidate cache entries
            async with cache_manager.cache_context_async(region):
                await cache_manager.invalidate_pattern_async(key_pattern)
            
            # Execute the function
            return await func(*args, **kwargs)
        
        return cast(AsyncF, wrapper)
    
    return decorator


def cache_aside(get_from_cache: Callable[[Any], Any], 
               save_to_cache: Callable[[Any, Any], None]):
    """Decorator for implementing the cache-aside pattern.
    
    Args:
        get_from_cache: Function to get a value from cache, takes the request as input.
        save_to_cache: Function to save a value to cache, takes the request and result as input.
    
    Returns:
        Decorated function that implements the cache-aside pattern.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to get from cache
            cached_value = get_from_cache((args, kwargs))
            if cached_value is not None:
                return cached_value
            
            # Execute the function
            result = func(*args, **kwargs)
            
            # Save to cache
            save_to_cache((args, kwargs), result)
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def async_cache_aside(get_from_cache: Callable[[Any], Any], 
                     save_to_cache: Callable[[Any, Any], None]):
    """Decorator for implementing the cache-aside pattern in async functions.
    
    Args:
        get_from_cache: Function to get a value from cache, takes the request as input.
        save_to_cache: Function to save a value to cache, takes the request and result as input.
    
    Returns:
        Decorated async function that implements the cache-aside pattern.
    """
    def decorator(func: AsyncF) -> AsyncF:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Try to get from cache
            cached_value = get_from_cache((args, kwargs))
            if cached_value is not None:
                return cached_value
            
            # Execute the function
            result = await func(*args, **kwargs)
            
            # Save to cache
            save_to_cache((args, kwargs), result)
            
            return result
        
        return cast(AsyncF, wrapper)
    
    return decorator