"""
DataLoader for efficient batch loading of data.

This module provides a DataLoader implementation for batching and caching
database queries and other expensive operations, similar to Facebook's
DataLoader for GraphQL.
"""

from typing import TypeVar, Generic, Dict, Any, Optional, List, Set, Callable, Awaitable, Union, cast, Tuple
import asyncio
import logging
import time
import hashlib
import json
import pickle
import functools
import inspect
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from uno.core.async import (
    AsyncLock, 
    AsyncEvent,
    AsyncSemaphore,
    TaskGroup,
    timeout,
)
from uno.core.async_integration import (
    cancellable,
    retry,
    AsyncBatcher,
)
from uno.core.caching import (
    Cache,
    CacheStrategy,
)


K = TypeVar('K')
V = TypeVar('V')
T = TypeVar('T')


class DataLoader(Generic[K, V]):
    """
    DataLoader for efficient batch loading of data.
    
    The DataLoader provides:
    - Batching of similar load operations
    - Caching of load results
    - Request deduplication
    - Proper promise API (async/await based)
    """
    
    def __init__(
        self,
        batch_load_fn: Callable[[List[K]], Awaitable[List[V]]],
        batch_size: int = 100,
        max_batch_delay: float = 0.01,
        cache_enabled: bool = True,
        cache_ttl: Optional[float] = 300.0,
        cache_strategy: CacheStrategy = CacheStrategy.LRU,
        cache_max_size: Optional[int] = 10000,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the DataLoader.
        
        Args:
            batch_load_fn: Function to load items in batch
                           Should accept a list of keys and return a list of values
                           in the same order
            batch_size: Maximum batch size
            max_batch_delay: Maximum delay before processing a batch (seconds)
            cache_enabled: Whether to cache results
            cache_ttl: Time-to-live for cache entries (seconds)
            cache_strategy: Cache eviction strategy
            cache_max_size: Maximum cache size
            logger: Optional logger instance
        """
        self.batch_load_fn = batch_load_fn
        self.batch_size = batch_size
        self.max_batch_delay = max_batch_delay
        self.cache_enabled = cache_enabled
        self.logger = logger or logging.getLogger(__name__)
        
        # Create cache if enabled
        self.cache = None
        if cache_enabled:
            self.cache = Cache[K, V](
                name=f"dataloader_{id(self)}",
                strategy=cache_strategy,
                max_size=cache_max_size,
                ttl=cache_ttl,
                logger=logger,
            )
        
        # Batch state
        self._batch_promise: Optional[asyncio.Future[Dict[K, V]]] = None
        self._batch_keys: List[K] = []
        self._batch_futures: Dict[K, asyncio.Future[V]] = {}
        self._batch_lock = AsyncLock()
        self._batch_timer: Optional[asyncio.TimerHandle] = None
        
        # Statistics
        self._cache_hits = 0
        self._cache_misses = 0
        self._batches_dispatched = 0
        self._total_keys_requested = 0
        self._batch_sizes: List[int] = []
        self._load_times: List[float] = []
    
    async def load(self, key: K) -> V:
        """
        Load a single value by key.
        
        This method batches multiple load requests that occur within
        the same event loop tick or within the max_batch_delay.
        
        Args:
            key: The key to load
            
        Returns:
            The loaded value
            
        Raises:
            Exception: Any error that occurs during loading
        """
        self._total_keys_requested += 1
        
        # Check cache first if enabled
        if self.cache_enabled and self.cache is not None:
            cached_value = await self.cache.get(key)
            
            if cached_value is not None:
                self._cache_hits += 1
                return cached_value
            
            self._cache_misses += 1
        
        # Create a future for this key
        future: asyncio.Future[V] = asyncio.Future()
        
        # Add to batch
        async with self._batch_lock:
            if key in self._batch_futures:
                # Key already in batch, return existing future
                return await self._batch_futures[key]
            
            # Add to batch
            self._batch_keys.append(key)
            self._batch_futures[key] = future
            
            # Create batch promise if needed
            if self._batch_promise is None:
                self._batch_promise = asyncio.Future()
                
                # Schedule batch dispatch
                if self.max_batch_delay > 0:
                    loop = asyncio.get_event_loop()
                    self._batch_timer = loop.call_later(
                        self.max_batch_delay,
                        lambda: asyncio.create_task(self._dispatch_batch())
                    )
                else:
                    # Dispatch immediately in the next event loop tick
                    asyncio.create_task(self._dispatch_batch())
            
            # Dispatch batch if full
            if len(self._batch_keys) >= self.batch_size:
                if self._batch_timer is not None:
                    self._batch_timer.cancel()
                    self._batch_timer = None
                
                asyncio.create_task(self._dispatch_batch())
        
        # Wait for the result
        return await future
    
    async def load_many(self, keys: List[K]) -> List[V]:
        """
        Load multiple values by keys.
        
        Args:
            keys: The keys to load
            
        Returns:
            List of loaded values in the same order as keys
            
        Raises:
            Exception: Any error that occurs during loading
        """
        # Use a task group to concurrently load all keys
        tasks = []
        
        async with TaskGroup(name="load_many") as group:
            # Create a task for each key
            for key in keys:
                task = group.create_task(self.load(key))
                tasks.append(task)
            
            # Wait for all tasks to complete
            return [await task for task in tasks]
    
    async def _dispatch_batch(self) -> None:
        """
        Dispatch the current batch for loading.
        
        This method is called either when:
        1. The batch is full
        2. The batch delay has elapsed
        3. The dataloader is cleared
        """
        # Get current batch state
        async with self._batch_lock:
            # Check if batch is empty
            if not self._batch_keys:
                return
            
            # Cancel timer if active
            if self._batch_timer is not None:
                self._batch_timer.cancel()
                self._batch_timer = None
            
            # Get batch data
            batch_keys = list(self._batch_keys)
            batch_futures = dict(self._batch_futures)
            batch_promise = self._batch_promise
            
            # Reset batch state
            self._batch_keys = []
            self._batch_futures = {}
            self._batch_promise = None
        
        # Load batch
        try:
            # Track batch statistics
            batch_size = len(batch_keys)
            self._batches_dispatched += 1
            self._batch_sizes.append(batch_size)
            
            start_time = time.time()
            
            # Call batch load function
            values = await self.batch_load_fn(batch_keys)
            
            # Track load time
            load_time = time.time() - start_time
            self._load_times.append(load_time)
            
            # Validate results
            if len(values) != len(batch_keys):
                raise ValueError(
                    f"DataLoader batch_load_fn returned {len(values)} values, "
                    f"but {len(batch_keys)} keys were requested"
                )
            
            # Create result map
            result_map: Dict[K, V] = {}
            
            for i, key in enumerate(batch_keys):
                value = values[i]
                result_map[key] = value
                
                # Cache result if enabled
                if self.cache_enabled and self.cache is not None:
                    await self.cache.set(key, value)
            
            # Resolve batch promise
            batch_promise.set_result(result_map)
            
            # Resolve individual futures
            for key, future in batch_futures.items():
                future.set_result(result_map[key])
        
        except Exception as e:
            # Reject batch promise
            batch_promise.set_exception(e)
            
            # Reject individual futures
            for future in batch_futures.values():
                if not future.done():
                    future.set_exception(e)
    
    async def clear(self, key: Optional[K] = None) -> None:
        """
        Clear the dataloader cache.
        
        Args:
            key: Specific key to clear, or None for all keys
        """
        if not self.cache_enabled or self.cache is None:
            return
        
        if key is not None:
            # Clear specific key
            await self.cache.delete(key)
        else:
            # Clear all keys
            await self.cache.clear()
    
    async def prime(self, key: K, value: V) -> None:
        """
        Prime the cache with a key/value pair.
        
        Args:
            key: The key to prime
            value: The value to prime
        """
        if not self.cache_enabled or self.cache is None:
            return
        
        # Store in cache
        await self.cache.set(key, value)
        
        # Also fulfill any pending requests for this key
        async with self._batch_lock:
            if key in self._batch_futures and not self._batch_futures[key].done():
                # Remove from batch
                try:
                    self._batch_keys.remove(key)
                except ValueError:
                    pass
                
                # Resolve future
                future = self._batch_futures.pop(key)
                future.set_result(value)
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get dataloader statistics.
        
        Returns:
            Dictionary of dataloader statistics
        """
        # Calculate hit rate
        hit_rate = 0.0
        total_requests = self._cache_hits + self._cache_misses
        if total_requests > 0:
            hit_rate = self._cache_hits / total_requests
        
        # Calculate average batch size
        avg_batch_size = 0.0
        if self._batch_sizes:
            avg_batch_size = sum(self._batch_sizes) / len(self._batch_sizes)
        
        # Calculate average load time
        avg_load_time = 0.0
        if self._load_times:
            avg_load_time = sum(self._load_times) / len(self._load_times)
        
        # Calculate efficiency
        efficiency = 0.0
        if self._total_keys_requested > 0:
            # Higher is better - perfect batching would be 1.0
            efficiency = avg_batch_size * self._batches_dispatched / self._total_keys_requested
        
        # Get cache stats if available
        cache_stats = {}
        if self.cache_enabled and self.cache is not None:
            cache_stats = await self.cache.get_stats()
        
        return {
            "total_keys_requested": self._total_keys_requested,
            "batches_dispatched": self._batches_dispatched,
            "avg_batch_size": avg_batch_size,
            "avg_load_time": avg_load_time,
            "max_batch_size": self.batch_size,
            "cache_enabled": self.cache_enabled,
            "cache_hits": self._cache_hits,
            "cache_misses": self._cache_misses,
            "hit_rate": hit_rate,
            "efficiency": efficiency,
            "cache_stats": cache_stats,
        }


class BatchLoader(Generic[K, V]):
    """
    Batch loader for efficiently loading data in batches.
    
    Unlike DataLoader, BatchLoader does not implement caching, but is
    designed to be composed with the AsyncBatcher for more flexibility.
    """
    
    def __init__(
        self,
        batch_load_fn: Callable[[List[K]], Awaitable[List[V]]],
        keys_fn: Optional[Callable[[List[Dict[str, Any]]], List[K]]] = None,
        results_fn: Optional[Callable[[List[Dict[str, Any]], List[V]], List[Any]]] = None,
        batch_size: int = 100,
        max_batch_delay: float = 0.01,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the BatchLoader.
        
        Args:
            batch_load_fn: Function to load items in batch
                           Should accept a list of keys and return a list of values
            keys_fn: Function to extract keys from items
            results_fn: Function to combine items with results
            batch_size: Maximum batch size
            max_batch_delay: Maximum delay before processing a batch (seconds)
            logger: Optional logger instance
        """
        self.batch_load_fn = batch_load_fn
        self.keys_fn = keys_fn
        self.results_fn = results_fn
        self.batch_size = batch_size
        self.max_batch_delay = max_batch_delay
        self.logger = logger or logging.getLogger(__name__)
        
        # Create batcher
        self.batcher = AsyncBatcher[List[Dict[str, Any]], List[Any]](
            batch_operation=self._process_batch,
            max_batch_size=batch_size,
            max_wait_time=max_batch_delay,
            logger=logger,
        )
    
    async def _process_batch(
        self,
        items_batch: List[List[Dict[str, Any]]],
    ) -> List[List[Any]]:
        """
        Process a batch of items.
        
        Args:
            items_batch: Batch of items (batches of batches)
            
        Returns:
            Batch of results
        """
        # Flatten items
        flattened_items: List[Dict[str, Any]] = []
        batch_sizes: List[int] = []
        
        for items in items_batch:
            flattened_items.extend(items)
            batch_sizes.append(len(items))
        
        # Extract keys
        if self.keys_fn:
            keys = self.keys_fn(flattened_items)
        else:
            # Default to using 'id' field
            keys = [item.get('id') for item in flattened_items]
        
        # Load data
        results = await self.batch_load_fn(keys)
        
        # Combine items with results
        if self.results_fn:
            combined_results = self.results_fn(flattened_items, results)
        else:
            # Default to returning results directly
            combined_results = results
        
        # Split back into batches
        result_batches: List[List[Any]] = []
        start_idx = 0
        
        for size in batch_sizes:
            end_idx = start_idx + size
            result_batches.append(combined_results[start_idx:end_idx])
            start_idx = end_idx
        
        return result_batches
    
    async def load_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[Any]:
        """
        Load a batch of items.
        
        Args:
            items: Items to load
            
        Returns:
            Loaded results
        """
        return await self.batcher.add_item(items)
    
    async def shutdown(self) -> None:
        """
        Shut down the batch loader.
        """
        await self.batcher.shutdown()
    
    async def close(self) -> None:
        """
        Close the batch loader (alias for shutdown).
        """
        await self.shutdown()


class DataLoaderRegistry:
    """
    Registry for DataLoader instances.
    
    This provides centralized management of DataLoaders,
    enabling reuse and lifecycle management.
    """
    
    # Singleton instance
    _instance: Optional['DataLoaderRegistry'] = None
    
    @classmethod
    def get_instance(cls) -> 'DataLoaderRegistry':
        """
        Get the singleton instance of the registry.
        
        Returns:
            The registry instance
        """
        if cls._instance is None:
            cls._instance = DataLoaderRegistry()
        return cls._instance
    
    def __init__(
        self,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the registry.
        
        Args:
            logger: Optional logger instance
        """
        # Validate singleton
        if DataLoaderRegistry._instance is not None:
            raise RuntimeError(
                "DataLoaderRegistry is a singleton. Use get_instance() instead."
            )
        
        DataLoaderRegistry._instance = self
        
        self.logger = logger or logging.getLogger(__name__)
        self._loaders: Dict[str, DataLoader] = {}
        self._batch_loaders: Dict[str, BatchLoader] = {}
        self._registry_lock = AsyncLock()
    
    async def get_loader(
        self,
        name: str,
        factory_fn: Optional[Callable[[], DataLoader]] = None,
    ) -> Optional[DataLoader]:
        """
        Get a DataLoader by name.
        
        Args:
            name: The loader name
            factory_fn: Factory function to create the loader if not found
            
        Returns:
            The DataLoader or None if not found and no factory provided
        """
        async with self._registry_lock:
            # Return existing loader if found
            if name in self._loaders:
                return self._loaders[name]
            
            # Create new loader if factory provided
            if factory_fn is not None:
                loader = factory_fn()
                self._loaders[name] = loader
                return loader
            
            # Not found and no factory
            return None
    
    async def register_loader(
        self,
        name: str,
        loader: DataLoader,
    ) -> None:
        """
        Register a DataLoader.
        
        Args:
            name: The loader name
            loader: The DataLoader instance
            
        Raises:
            ValueError: If loader with this name already exists
        """
        async with self._registry_lock:
            if name in self._loaders:
                raise ValueError(f"DataLoader '{name}' already registered")
            
            self._loaders[name] = loader
    
    async def get_batch_loader(
        self,
        name: str,
        factory_fn: Optional[Callable[[], BatchLoader]] = None,
    ) -> Optional[BatchLoader]:
        """
        Get a BatchLoader by name.
        
        Args:
            name: The loader name
            factory_fn: Factory function to create the loader if not found
            
        Returns:
            The BatchLoader or None if not found and no factory provided
        """
        async with self._registry_lock:
            # Return existing loader if found
            if name in self._batch_loaders:
                return self._batch_loaders[name]
            
            # Create new loader if factory provided
            if factory_fn is not None:
                loader = factory_fn()
                self._batch_loaders[name] = loader
                return loader
            
            # Not found and no factory
            return None
    
    async def register_batch_loader(
        self,
        name: str,
        loader: BatchLoader,
    ) -> None:
        """
        Register a BatchLoader.
        
        Args:
            name: The loader name
            loader: The BatchLoader instance
            
        Raises:
            ValueError: If loader with this name already exists
        """
        async with self._registry_lock:
            if name in self._batch_loaders:
                raise ValueError(f"BatchLoader '{name}' already registered")
            
            self._batch_loaders[name] = loader
    
    async def clear_loader(
        self,
        name: str,
        key: Optional[Any] = None,
    ) -> bool:
        """
        Clear a loader's cache.
        
        Args:
            name: The loader name
            key: Specific key to clear, or None for all keys
            
        Returns:
            True if loader was found and cleared, False otherwise
        """
        async with self._registry_lock:
            if name in self._loaders:
                await self._loaders[name].clear(key)
                return True
            
            return False
    
    async def clear_all_loaders(self) -> int:
        """
        Clear all loaders' caches.
        
        Returns:
            Number of loaders cleared
        """
        count = 0
        
        async with self._registry_lock:
            for loader in self._loaders.values():
                await loader.clear()
                count += 1
        
        return count
    
    async def close(self) -> None:
        """
        Close all loaders.
        """
        async with self._registry_lock:
            # Clear DataLoaders
            for loader in self._loaders.values():
                await loader.clear()
            
            # Close BatchLoaders
            for loader in self._batch_loaders.values():
                await loader.close()
            
            # Clear collections
            self._loaders.clear()
            self._batch_loaders.clear()
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary of registry statistics
        """
        stats = {
            "dataloader_count": 0,
            "batchloader_count": 0,
            "dataloaders": {},
            "batchloaders": {},
        }
        
        async with self._registry_lock:
            # DataLoader stats
            stats["dataloader_count"] = len(self._loaders)
            
            for name, loader in self._loaders.items():
                stats["dataloaders"][name] = await loader.get_stats()
            
            # BatchLoader stats
            stats["batchloader_count"] = len(self._batch_loaders)
            
            # We don't include BatchLoader stats as they don't expose them
        
        return stats


def get_dataloader_registry() -> DataLoaderRegistry:
    """
    Get the global DataLoader registry.
    
    Returns:
        The registry instance
    """
    return DataLoaderRegistry.get_instance()


def with_dataloader(
    loader_name: str,
    batch_load_fn: Optional[Callable[[List[Any]], Awaitable[List[Any]]]] = None,
    batch_size: int = 100,
    max_batch_delay: float = 0.01,
    cache_enabled: bool = True,
    cache_ttl: Optional[float] = 300.0,
) -> Callable:
    """
    Decorator for methods that use a DataLoader.
    
    This decorator automatically creates or reuses a DataLoader
    and passes it to the decorated method.
    
    Args:
        loader_name: Name of the loader
        batch_load_fn: Function to load items in batch
        batch_size: Maximum batch size
        max_batch_delay: Maximum delay before processing a batch
        cache_enabled: Whether to cache results
        cache_ttl: Time-to-live for cache entries
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get registry
            registry = get_dataloader_registry()
            
            # Get or create loader
            if batch_load_fn is not None:
                # Factory function to create loader if needed
                def create_loader() -> DataLoader:
                    return DataLoader(
                        batch_load_fn=batch_load_fn,
                        batch_size=batch_size,
                        max_batch_delay=max_batch_delay,
                        cache_enabled=cache_enabled,
                        cache_ttl=cache_ttl,
                    )
                
                loader = await registry.get_loader(loader_name, create_loader)
            else:
                # Just get existing loader
                loader = await registry.get_loader(loader_name)
                
                if loader is None:
                    raise ValueError(
                        f"DataLoader '{loader_name}' not found and no batch_load_fn provided"
                    )
            
            # Add loader to kwargs
            kwargs['loader'] = loader
            
            # Call the function
            return await func(*args, **kwargs)
        
        # Only works for async functions
        if not asyncio.iscoroutinefunction(func):
            raise TypeError("with_dataloader can only be used with async functions")
        
        return wrapper
    
    return decorator