"""
CQRS performance optimization components.

This module provides performance optimizations for the CQRS (Command Query 
Responsibility Segregation) pattern in uno, including:

1. Command batching - Execute multiple commands in a single transaction
2. Parallel command execution - Execute independent commands in parallel
3. Cached commands - Cache command results for idempotent commands
4. Command throttling - Limit command execution rate
5. Command priority queues - Prioritize important commands
"""

import asyncio
import time
import logging
from datetime import datetime, UTC, timedelta
from typing import (
    Any, Callable, Dict, Generic, List, Optional, Set, Type, TypeVar, Union
)
from dataclasses import dataclass, field

from uno.core.cqrs import (
    Command, CommandBus, CommandHandler, Query, QueryBus, QueryHandler,
    Mediator, get_mediator
)
from uno.core.result import Result, Success, Failure, Error
from uno.domain.unit_of_work import UnitOfWork, AbstractUnitOfWork
from uno.core.di import inject_dependency

# Type variables for generic classes
TCommand = TypeVar('TCommand', bound=Command)
TResult = TypeVar('TResult')
TQuery = TypeVar('TQuery', bound=Query)

# Configure logger
logger = logging.getLogger(__name__)


class BatchCommandBus(CommandBus):
    """
    Command bus that supports batching commands for improved performance.

    Batching commands can significantly improve performance by:
    1. Reducing transaction overhead by executing multiple commands in a single transaction
    2. Minimizing database round-trips
    3. Improving throughput for high-volume operations

    Use this when you need to execute multiple related commands as a single unit.
    """

    async def execute_batch(
        self, 
        commands: List[Command], 
        unit_of_work: Optional[AbstractUnitOfWork] = None
    ) -> List[Result[Any]]:
        """
        Execute multiple commands in a single batch.

        Args:
            commands: List of commands to execute
            unit_of_work: Optional unit of work to use for all commands.
                          If not provided, a new one will be created.

        Returns:
            List of results for each command
        """
        if not commands:
            return []

        results = []
        external_uow = unit_of_work is not None

        try:
            # If no unit of work provided, create one
            if not external_uow:
                unit_of_work_factory = inject_dependency("unit_of_work_factory")
                unit_of_work = unit_of_work_factory()
                await unit_of_work.begin()

            # Process each command in the batch
            for command in commands:
                command_type = type(command)
                handler = self._get_handler_for_command(command_type)
                
                if not handler:
                    results.append(Failure(Error(
                        code="command_handler_not_found",
                        message=f"No handler registered for command type: {command_type.__name__}"
                    )))
                    continue

                # Execute the command
                result = await handler.handle(command)
                results.append(result)
                
                # If any command fails, stop processing
                if not result.is_success():
                    logger.warning(
                        f"Command batch execution failed at command {command_type.__name__}. "
                        f"Error: {result.error.message}"
                    )
                    if not external_uow:
                        await unit_of_work.rollback()
                    return results

            # Commit the transaction if we created the unit of work
            if not external_uow:
                await unit_of_work.commit()
                
            return results

        except Exception as e:
            logger.exception(f"Error executing command batch: {e}")
            # Rollback the transaction if we created the unit of work
            if not external_uow and unit_of_work:
                await unit_of_work.rollback()
            
            # For any commands that haven't been processed, add failure results
            while len(results) < len(commands):
                results.append(Failure(Error(
                    code="command_batch_execution_error",
                    message=f"Batch execution error: {str(e)}"
                )))
            
            return results


class ParallelCommandBus(CommandBus):
    """
    Command bus that executes independent commands in parallel.

    This can significantly improve performance when:
    1. Commands are independent (don't affect the same aggregates)
    2. The system has multiple CPU cores
    3. The operations are IO-bound

    Use this when you have multiple unrelated commands to execute.
    """

    async def execute_parallel(
        self, 
        commands: List[Command],
        max_concurrency: int = 10
    ) -> List[Result[Any]]:
        """
        Execute multiple commands in parallel.

        Args:
            commands: List of commands to execute
            max_concurrency: Maximum number of commands to execute concurrently

        Returns:
            List of results for each command in the same order as the commands
        """
        if not commands:
            return []

        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrency)

        async def execute_with_semaphore(command: Command) -> Result[Any]:
            """Execute a command with the semaphore."""
            async with semaphore:
                try:
                    command_type = type(command)
                    handler = self._get_handler_for_command(command_type)
                    
                    if not handler:
                        return Failure(Error(
                            code="command_handler_not_found",
                            message=f"No handler registered for command type: {command_type.__name__}"
                        ))
                    
                    return await handler.handle(command)
                except Exception as e:
                    logger.exception(f"Error executing command in parallel: {e}")
                    return Failure(Error(
                        code="parallel_command_execution_error",
                        message=f"Parallel execution error: {str(e)}"
                    ))

        # Execute commands in parallel
        tasks = [execute_with_semaphore(command) for command in commands]
        return await asyncio.gather(*tasks)


class IdempotentCommandBus(CommandBus):
    """
    Command bus that ensures commands are executed exactly once, 
    using an idempotency key.

    This is useful for:
    1. Retry scenarios where a command might be sent multiple times
    2. Distributed systems where command delivery might be duplicated
    3. User interfaces where users might submit the same form multiple times

    Use this when you need to ensure commands are not executed multiple times.
    """

    def __init__(
        self,
        result_cache: Dict[str, Result[Any]] = None,
        ttl_seconds: int = 3600  # 1 hour default
    ):
        """
        Initialize the idempotent command bus.

        Args:
            result_cache: Optional dict to store results
            ttl_seconds: Time to live for cached results in seconds
        """
        super().__init__()
        self.result_cache = result_cache or {}
        self.ttl_seconds = ttl_seconds
        self.expiry_times: Dict[str, datetime] = {}

    def _get_idempotency_key(self, command: Command) -> str:
        """
        Get an idempotency key for a command.

        By default, uses the command's idempotency_key attribute if present,
        otherwise generates a key based on the command type and attributes.

        Args:
            command: The command to get a key for

        Returns:
            A string idempotency key
        """
        if hasattr(command, "idempotency_key") and command.idempotency_key:
            return str(command.idempotency_key)
        
        # Create a key based on command type and attributes
        command_dict = command.dict()
        # Remove any transient fields that shouldn't affect idempotency
        for field in ["created_at", "request_id", "correlation_id"]:
            command_dict.pop(field, None)
        
        # Create a string representation of the command
        key_parts = [command.__class__.__name__]
        for k, v in sorted(command_dict.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)

    async def execute(self, command: Command) -> Result[Any]:
        """
        Execute a command with idempotency control.

        Args:
            command: The command to execute

        Returns:
            The command result
        """
        # Get idempotency key
        key = self._get_idempotency_key(command)
        
        # Check if we have a cached result
        if key in self.result_cache:
            # Check if the result has expired
            if self.expiry_times.get(key, datetime.max) > datetime.now(UTC):
                logger.debug(f"Using cached result for idempotent command: {key}")
                return self.result_cache[key]
            
            # Result has expired, remove it
            del self.result_cache[key]
            if key in self.expiry_times:
                del self.expiry_times[key]
        
        # Execute the command
        command_type = type(command)
        handler = self._get_handler_for_command(command_type)
        
        if not handler:
            return Failure(Error(
                code="command_handler_not_found",
                message=f"No handler registered for command type: {command_type.__name__}"
            ))
        
        # Execute the command
        result = await handler.handle(command)
        
        # Cache the result for future calls
        if getattr(command, "cacheable", True):
            self.result_cache[key] = result
            self.expiry_times[key] = datetime.now(UTC) + timedelta(seconds=self.ttl_seconds)
            
            # Cleanup old entries
            self._cleanup_expired_entries()
        
        return result
    
    def _cleanup_expired_entries(self):
        """Clean up expired entries from the cache."""
        now = datetime.now(UTC)
        expired_keys = [
            k for k, expiry in self.expiry_times.items() 
            if expiry <= now
        ]
        
        for key in expired_keys:
            del self.result_cache[key]
            del self.expiry_times[key]


@dataclass
class CommandPriority:
    """Priority levels for command execution."""
    HIGH: int = 0
    NORMAL: int = 10
    LOW: int = 20


@dataclass(order=True)
class PrioritizedCommand:
    """A command with an associated priority."""
    priority: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    command: Command = field(compare=False)


class PrioritizedCommandBus(CommandBus):
    """
    Command bus that processes commands according to priority.

    This is useful when:
    1. Some commands are more important than others
    2. You need to ensure critical operations take precedence
    3. You want to balance system load by prioritizing work

    Use this when you have commands with different levels of importance.
    """

    def __init__(self):
        """Initialize the prioritized command bus."""
        super().__init__()
        self.queue: asyncio.PriorityQueue[PrioritizedCommand] = asyncio.PriorityQueue()
        self.running = False
        self.worker_task = None

    async def start(self, worker_count: int = 1):
        """
        Start the command bus workers.

        Args:
            worker_count: Number of worker tasks to start
        """
        self.running = True
        self.worker_tasks = []
        
        for _ in range(worker_count):
            task = asyncio.create_task(self._worker())
            self.worker_tasks.append(task)
    
    async def stop(self):
        """Stop the command bus workers."""
        self.running = False
        
        # Clear any remaining commands
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
                self.queue.task_done()
            except asyncio.QueueEmpty:
                break
        
        # Wait for workers to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks)
            self.worker_tasks = []
    
    async def enqueue(
        self, 
        command: Command, 
        priority: int = CommandPriority.NORMAL
    ) -> None:
        """
        Enqueue a command for processing.

        Args:
            command: The command to enqueue
            priority: The command priority (lower is higher priority)
        """
        prioritized_command = PrioritizedCommand(
            priority=priority,
            command=command
        )
        await self.queue.put(prioritized_command)
    
    async def execute(self, command: Command) -> Result[Any]:
        """
        Execute a command directly (bypassing the queue).

        Args:
            command: The command to execute

        Returns:
            The command result
        """
        command_type = type(command)
        handler = self._get_handler_for_command(command_type)
        
        if not handler:
            return Failure(Error(
                code="command_handler_not_found",
                message=f"No handler registered for command type: {command_type.__name__}"
            ))
        
        return await handler.handle(command)
    
    async def _worker(self):
        """Worker task that processes commands from the queue."""
        while self.running:
            try:
                # Get a command from the queue
                prioritized_command = await self.queue.get()
                
                try:
                    # Execute the command
                    command = prioritized_command.command
                    command_type = type(command)
                    handler = self._get_handler_for_command(command_type)
                    
                    if handler:
                        await handler.handle(command)
                    else:
                        logger.warning(
                            f"No handler registered for command type: {command_type.__name__}"
                        )
                except Exception as e:
                    logger.exception(f"Error executing command: {e}")
                finally:
                    # Mark the command as done
                    self.queue.task_done()
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Error in command worker: {e}")
                # Sleep briefly to avoid tight loop in case of persistent errors
                await asyncio.sleep(0.1)


class ThrottledCommandBus(CommandBus):
    """
    Command bus that limits the rate of command execution.

    This is useful when:
    1. You need to limit the load on external systems
    2. You want to prevent resource exhaustion
    3. You need to comply with API rate limits

    Use this when you need to control how many commands execute per unit of time.
    """

    def __init__(
        self,
        max_commands_per_second: float = 10.0,
        max_burst: int = 50
    ):
        """
        Initialize the throttled command bus.

        Args:
            max_commands_per_second: Maximum number of commands to execute per second
            max_burst: Maximum number of commands to execute in a burst
        """
        super().__init__()
        self.rate_limit = max_commands_per_second
        self.max_tokens = max_burst
        self.tokens = max_burst
        self.last_refill = time.time()
        self.lock = asyncio.Lock()
    
    async def execute(self, command: Command) -> Result[Any]:
        """
        Execute a command with rate limiting.

        Args:
            command: The command to execute

        Returns:
            The command result
        """
        # Update token bucket
        await self._update_tokens()
        
        # Check if we have tokens available
        async with self.lock:
            if self.tokens < 1:
                return Failure(Error(
                    code="command_rate_limit_exceeded",
                    message="Command rate limit exceeded"
                ))
            
            # Consume a token
            self.tokens -= 1
        
        # Execute the command
        command_type = type(command)
        handler = self._get_handler_for_command(command_type)
        
        if not handler:
            return Failure(Error(
                code="command_handler_not_found",
                message=f"No handler registered for command type: {command_type.__name__}"
            ))
        
        return await handler.handle(command)
    
    async def _update_tokens(self):
        """Update the token bucket based on elapsed time."""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.last_refill = now
            
            # Add new tokens based on elapsed time
            new_tokens = elapsed * self.rate_limit
            self.tokens = min(self.tokens + new_tokens, self.max_tokens)


class CachedQueryHandler(QueryHandler[TQuery, TResult]):
    """
    Query handler that caches results to improve performance.

    This is useful when:
    1. Queries are expensive to execute
    2. Query results don't change frequently
    3. The same query is executed multiple times

    Use this to avoid redundant database queries for frequently requested data.
    """

    def __init__(
        self,
        delegate: QueryHandler[TQuery, TResult],
        cache: Dict[str, tuple[Result[TResult], datetime]] = None,
        ttl_seconds: int = 300  # 5 minutes default
    ):
        """
        Initialize the cached query handler.

        Args:
            delegate: The actual query handler to delegate to
            cache: Optional dict to store results
            ttl_seconds: Time to live for cached results in seconds
        """
        self.delegate = delegate
        self.cache = cache or {}
        self.ttl_seconds = ttl_seconds
    
    def _get_cache_key(self, query: TQuery) -> str:
        """
        Get a cache key for a query.

        Args:
            query: The query to get a key for

        Returns:
            A string cache key
        """
        # Create a key based on query type and attributes
        query_dict = query.dict()
        
        # Create a string representation of the query
        key_parts = [query.__class__.__name__]
        for k, v in sorted(query_dict.items()):
            key_parts.append(f"{k}:{v}")
        
        return ":".join(key_parts)
    
    async def handle(self, query: TQuery) -> Result[TResult]:
        """
        Handle a query with caching.

        Args:
            query: The query to handle

        Returns:
            The query result
        """
        # Get cache key
        key = self._get_cache_key(query)
        now = datetime.now(UTC)
        
        # Check if we have a cached result
        if key in self.cache:
            result, expiry = self.cache[key]
            
            # Check if the result has expired
            if expiry > now:
                logger.debug(f"Using cached result for query: {key}")
                return result
            
            # Result has expired, remove it
            del self.cache[key]
        
        # Execute the query
        result = await self.delegate.handle(query)
        
        # Cache the result for future calls
        if getattr(query, "cacheable", True) and result.is_success():
            expiry = now + timedelta(seconds=self.ttl_seconds)
            self.cache[key] = (result, expiry)
            
            # Cleanup old entries
            self._cleanup_expired_entries()
        
        return result
    
    def _cleanup_expired_entries(self):
        """Clean up expired entries from the cache."""
        now = datetime.now(UTC)
        expired_keys = [
            k for k, (_, expiry) in self.cache.items() 
            if expiry <= now
        ]
        
        for key in expired_keys:
            del self.cache[key]


class ParallelQueryBus(QueryBus):
    """
    Query bus that executes multiple queries in parallel.

    This is useful when:
    1. Multiple independent queries need to be executed
    2. You want to reduce the total request time
    3. Queries are primarily IO-bound

    Use this when you need to retrieve multiple sets of data concurrently.
    """

    async def execute_parallel(
        self, 
        queries: List[Query]
    ) -> List[Result[Any]]:
        """
        Execute multiple queries in parallel.

        Args:
            queries: List of queries to execute

        Returns:
            List of results for each query
        """
        if not queries:
            return []

        async def execute_query(query: Query) -> Result[Any]:
            """Execute a single query."""
            try:
                query_type = type(query)
                handler = self._get_handler_for_query(query_type)
                
                if not handler:
                    return Failure(Error(
                        code="query_handler_not_found",
                        message=f"No handler registered for query type: {query_type.__name__}"
                    ))
                
                return await handler.handle(query)
            except Exception as e:
                logger.exception(f"Error executing query in parallel: {e}")
                return Failure(Error(
                    code="parallel_query_execution_error",
                    message=f"Parallel execution error: {str(e)}"
                ))

        # Execute queries in parallel
        tasks = [execute_query(query) for query in queries]
        return await asyncio.gather(*tasks)


class OptimizedMediator(Mediator):
    """
    Optimized mediator implementation that integrates performance enhancements.

    This combines multiple optimization strategies:
    1. Command batching
    2. Parallel query execution
    3. Idempotent command handling
    4. Command prioritization
    5. Rate limiting
    6. Query result caching
    """

    def __init__(self):
        """Initialize the optimized mediator."""
        super().__init__()
        self.batch_command_bus = BatchCommandBus()
        self.parallel_query_bus = ParallelQueryBus()
        self.idempotent_command_bus = IdempotentCommandBus()
    
    def register_command_handler(
        self, 
        command_type: Type[Command], 
        handler: CommandHandler
    ) -> None:
        """
        Register a command handler with the mediator.

        Args:
            command_type: Type of command to register the handler for
            handler: The handler to register
        """
        super().register_command_handler(command_type, handler)
        self.batch_command_bus.register_handler(command_type, handler)
        self.parallel_query_bus.register_handler(command_type, handler)
        self.idempotent_command_bus.register_handler(command_type, handler)
    
    def register_query_handler(
        self, 
        query_type: Type[Query], 
        handler: QueryHandler
    ) -> None:
        """
        Register a query handler with the mediator.

        Args:
            query_type: Type of query to register the handler for
            handler: The handler to register
        """
        super().register_query_handler(query_type, handler)
        self.parallel_query_bus.register_handler(query_type, handler)
    
    async def execute_batch(
        self, 
        commands: List[Command],
        unit_of_work: Optional[AbstractUnitOfWork] = None
    ) -> List[Result[Any]]:
        """
        Execute multiple commands in a batch.

        Args:
            commands: List of commands to execute
            unit_of_work: Optional unit of work to use

        Returns:
            List of results for each command
        """
        return await self.batch_command_bus.execute_batch(commands, unit_of_work)
    
    async def execute_parallel_queries(
        self, 
        queries: List[Query]
    ) -> List[Result[Any]]:
        """
        Execute multiple queries in parallel.

        Args:
            queries: List of queries to execute

        Returns:
            List of results for each query
        """
        return await self.parallel_query_bus.execute_parallel(queries)
    
    async def execute_idempotent_command(
        self, 
        command: Command
    ) -> Result[Any]:
        """
        Execute a command with idempotency control.

        Args:
            command: The command to execute

        Returns:
            The command result
        """
        return await self.idempotent_command_bus.execute(command)


def get_optimized_mediator(new_instance: bool = False) -> OptimizedMediator:
    """
    Get the optimized mediator instance.

    Args:
        new_instance: Whether to create a new instance even if one exists

    Returns:
        The optimized mediator instance
    """
    global _optimized_mediator_instance
    
    if new_instance or not _optimized_mediator_instance:
        _optimized_mediator_instance = OptimizedMediator()
    
    return _optimized_mediator_instance


# Global mediator instance
_optimized_mediator_instance = None


# Handler decorators for optimization

def cached_query(ttl_seconds: int = 300):
    """
    Decorator that caches query results.

    Args:
        ttl_seconds: Time to live for cached results in seconds

    Returns:
        A decorator function
    """
    def decorator(handler_class):
        original_init = handler_class.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Create a cache for this handler instance
            self._result_cache = {}
            # Wrap the handle method with caching
            self._original_handle = self.handle
            
            async def cached_handle(query):
                # Create a key from the query
                query_dict = query.dict()
                key_parts = [query.__class__.__name__]
                for k, v in sorted(query_dict.items()):
                    key_parts.append(f"{k}:{v}")
                key = ":".join(key_parts)
                
                # Check cache
                now = datetime.now(UTC)
                if key in self._result_cache:
                    result, expiry = self._result_cache[key]
                    if expiry > now:
                        return result
                
                # Execute query
                result = await self._original_handle(query)
                
                # Cache result
                if result.is_success():
                    expiry = now + timedelta(seconds=ttl_seconds)
                    self._result_cache[key] = (result, expiry)
                
                return result
            
            self.handle = cached_handle
        
        handler_class.__init__ = new_init
        return handler_class
    
    return decorator


def idempotent_command(key_fn: Optional[Callable[[Command], str]] = None):
    """
    Decorator that makes a command handler idempotent.

    Args:
        key_fn: Optional function to generate idempotency keys

    Returns:
        A decorator function
    """
    def decorator(handler_class):
        original_init = handler_class.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            # Create a store for processed commands
            self._processed_commands = set()
            # Wrap the handle method with idempotency check
            self._original_handle = self.handle
            
            async def idempotent_handle(command):
                # Generate idempotency key
                if key_fn:
                    key = key_fn(command)
                elif hasattr(command, "idempotency_key") and command.idempotency_key:
                    key = str(command.idempotency_key)
                else:
                    # Default key generation
                    command_dict = command.dict()
                    key_parts = [command.__class__.__name__]
                    for k, v in sorted(command_dict.items()):
                        if k not in ["created_at", "request_id", "correlation_id"]:
                            key_parts.append(f"{k}:{v}")
                    key = ":".join(key_parts)
                
                # Check if already processed
                if key in self._processed_commands:
                    return Success("Command already processed")
                
                # Execute command
                result = await self._original_handle(command)
                
                # Store successful commands
                if result.is_success():
                    self._processed_commands.add(key)
                
                return result
            
            self.handle = idempotent_handle
        
        handler_class.__init__ = new_init
        return handler_class
    
    return decorator


def batch_commands(handler_class):
    """
    Decorator that adds batch processing capability to a command handler.

    Args:
        handler_class: The command handler class to decorate

    Returns:
        The decorated class
    """
    original_init = handler_class.__init__
    
    def new_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        
        async def handle_batch(commands, unit_of_work=None):
            results = []
            external_uow = unit_of_work is not None
            
            try:
                # Create unit of work if needed
                if not external_uow:
                    unit_of_work_factory = inject_dependency("unit_of_work_factory")
                    unit_of_work = unit_of_work_factory()
                    await unit_of_work.begin()
                
                # Process each command
                for command in commands:
                    result = await self._handle(command, unit_of_work)
                    results.append(result)
                    
                    # If any command fails, stop processing
                    if not result.is_success():
                        if not external_uow:
                            await unit_of_work.rollback()
                        return results
                
                # Commit the transaction if we created the unit of work
                if not external_uow:
                    await unit_of_work.commit()
                
                return results
                
            except Exception as e:
                logger.exception(f"Error executing command batch: {e}")
                # Rollback if we created the unit of work
                if not external_uow and unit_of_work:
                    await unit_of_work.rollback()
                
                # Add failure results for remaining commands
                while len(results) < len(commands):
                    results.append(Failure(Error(
                        code="batch_execution_error",
                        message=f"Batch execution error: {str(e)}"
                    )))
                
                return results
        
        # Add batch handling method
        self.handle_batch = handle_batch
    
    handler_class.__init__ = new_init
    return handler_class