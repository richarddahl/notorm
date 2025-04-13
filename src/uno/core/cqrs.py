"""
CQRS (Command Query Responsibility Segregation) implementation for the Uno framework.

This module provides a comprehensive implementation of the CQRS pattern, which
separates read operations (queries) from write operations (commands). This separation
allows for optimization of each path and better scalability.
"""

import inspect
import logging
import uuid
from abc import abstractmethod
from datetime import datetime
from enum import Enum, auto
from typing import (
    Any, Dict, List, Optional, Type, TypeVar, Generic, Protocol, Union,
    Callable, Awaitable, get_type_hints, cast, runtime_checkable, ClassVar,
    Self
)

from .errors.base import ErrorCategory, UnoError
from .errors import with_error_context, with_async_error_context
from .events import Event, EventPublisher, get_event_publisher
from .protocols import Command, Query, CommandHandler, QueryHandler


# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T")
TResult = TypeVar("TResult")
TCommand = TypeVar("TCommand", bound=Command)
TQuery = TypeVar("TQuery", bound=Query)


# =============================================================================
# Base Command Implementation
# =============================================================================

class BaseCommand[T_Result](Command[T_Result]):
    """
    Base implementation of a command.
    
    Commands represent intentions to change the state of the system.
    They are named in the imperative and should be processed exactly once.
    
    Type Parameters:
        T_Result: The type of result after command execution
    """
    
    def __init__(self, command_id: str = None):
        """
        Initialize a command.
        
        Args:
            command_id: Unique identifier for the command (generated if not provided)
        """
        self.command_id = command_id or str(uuid.uuid4())
        self.command_type = self.__class__.__name__
        self.timestamp = datetime.utcnow()
    
    def __str__(self) -> str:
        """String representation of the command."""
        return f"{self.command_type}(id={self.command_id})"


# =============================================================================
# Base Query Implementation
# =============================================================================

class BaseQuery[T_Result](Query[T_Result]):
    """
    Base implementation of a query.
    
    Queries represent intentions to retrieve data without changing state.
    They are named as questions and can be processed multiple times.
    
    Type Parameters:
        T_Result: The type of result after query execution
    """
    
    def __init__(self, query_id: str = None):
        """
        Initialize a query.
        
        Args:
            query_id: Unique identifier for the query (generated if not provided)
        """
        self.query_id = query_id or str(uuid.uuid4())
        self.query_type = self.__class__.__name__
        self.timestamp = datetime.utcnow()
    
    def __str__(self) -> str:
        """String representation of the query."""
        return f"{self.query_type}(id={self.query_id})"


# =============================================================================
# Command Bus Implementation
# =============================================================================

class CommandBus:
    """
    Command bus for dispatching commands to their handlers.
    
    The command bus routes commands to the appropriate handlers based on
    their type and ensures that each command is handled exactly once.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the command bus.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self._logger = logger or logging.getLogger("uno.cqrs.commands")
        self._handlers: Dict[Type[Command], CommandHandler] = {}
    
    def register[TCmd, TRes](self, command_type: Type[TCmd], handler: CommandHandler[TCmd, TRes]) -> None:
        """
        Register a handler for a command type.
        
        Args:
            command_type: The type of command to register
            handler: The handler for the command
            
        Raises:
            UnoError: If the command type is already registered
        """
        if command_type in self._handlers:
            raise UnoError(
                message=f"Command handler already registered for {command_type.__name__}",
                code="COMMAND_HANDLER_ALREADY_REGISTERED",
                category=ErrorCategory.CONFLICT
            )
        
        self._handlers[command_type] = handler
        self._logger.debug(f"Registered handler for command {command_type.__name__}")
    
    def unregister[TCmd](self, command_type: Type[TCmd]) -> None:
        """
        Unregister a handler for a command type.
        
        Args:
            command_type: The type of command to unregister
        """
        if command_type in self._handlers:
            del self._handlers[command_type]
            self._logger.debug(f"Unregistered handler for command {command_type.__name__}")
    
    async def execute[TResult](self, command: Command[TResult]) -> TResult:
        """
        Execute a command with its registered handler.
        
        Args:
            command: The command to execute
            
        Returns:
            The result of command execution
            
        Raises:
            UnoError: If no handler is registered for the command type
        """
        command_type = type(command)
        self._logger.debug(f"Executing command {command_type.__name__} ({command.command_id})")
        
        # Find handler for this command type
        handler = self._get_handler_for_command(command)
        
        # Execute handler with error context
        with with_error_context(
            command_type=command_type.__name__, 
            command_id=command.command_id
        ):
            try:
                result = await handler.handle(command)
                return cast(TResult, result)
            except Exception as e:
                # Wrap in UnoError if not already
                if not isinstance(e, UnoError):
                    raise UnoError(
                        message=f"Error executing command {command_type.__name__}: {str(e)}",
                        code="COMMAND_EXECUTION_ERROR",
                        category=ErrorCategory.UNEXPECTED,
                        cause=e
                    )
                raise
    
    def _get_handler_for_command[TCmd](self, command: TCmd) -> CommandHandler[TCmd, Any]:
        """
        Get the handler for a command.
        
        Args:
            command: The command to get the handler for
            
        Returns:
            The command handler
            
        Raises:
            UnoError: If no handler is registered for the command type
        """
        command_type = type(command)
        
        # Check for direct handler
        if command_type in self._handlers:
            return self._handlers[command_type]
        
        # Check for handler for parent class
        for base in command_type.__mro__[1:]:  # Skip the command type itself
            if base in self._handlers and base != object:
                return self._handlers[base]
        
        # No handler found
        raise UnoError(
            message=f"No handler registered for command {command_type.__name__}",
            code="COMMAND_HANDLER_NOT_FOUND",
            category=ErrorCategory.NOT_FOUND
        )


# =============================================================================
# Query Bus Implementation
# =============================================================================

class QueryBus:
    """
    Query bus for dispatching queries to their handlers.
    
    The query bus routes queries to the appropriate handlers based on
    their type and can optimize for read operations.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the query bus.
        
        Args:
            logger: Optional logger for diagnostic information
        """
        self._logger = logger or logging.getLogger("uno.cqrs.queries")
        self._handlers: Dict[Type[Query], QueryHandler] = {}
    
    def register[TQry, TRes](self, query_type: Type[TQry], handler: QueryHandler[TQry, TRes]) -> None:
        """
        Register a handler for a query type.
        
        Args:
            query_type: The type of query to register
            handler: The handler for the query
            
        Raises:
            UnoError: If the query type is already registered
        """
        if query_type in self._handlers:
            raise UnoError(
                message=f"Query handler already registered for {query_type.__name__}",
                code="QUERY_HANDLER_ALREADY_REGISTERED",
                category=ErrorCategory.CONFLICT
            )
        
        self._handlers[query_type] = handler
        self._logger.debug(f"Registered handler for query {query_type.__name__}")
    
    def unregister[TQry](self, query_type: Type[TQry]) -> None:
        """
        Unregister a handler for a query type.
        
        Args:
            query_type: The type of query to unregister
        """
        if query_type in self._handlers:
            del self._handlers[query_type]
            self._logger.debug(f"Unregistered handler for query {query_type.__name__}")
    
    async def execute[TResult](self, query: Query[TResult]) -> TResult:
        """
        Execute a query with its registered handler.
        
        Args:
            query: The query to execute
            
        Returns:
            The result of query execution
            
        Raises:
            UnoError: If no handler is registered for the query type
        """
        query_type = type(query)
        self._logger.debug(f"Executing query {query_type.__name__} ({query.query_id})")
        
        # Find handler for this query type
        handler = self._get_handler_for_query(query)
        
        # Execute handler with error context
        with with_error_context(
            query_type=query_type.__name__, 
            query_id=query.query_id
        ):
            try:
                result = await handler.handle(query)
                return cast(TResult, result)
            except Exception as e:
                # Wrap in UnoError if not already
                if not isinstance(e, UnoError):
                    raise UnoError(
                        message=f"Error executing query {query_type.__name__}: {str(e)}",
                        code="QUERY_EXECUTION_ERROR",
                        category=ErrorCategory.UNEXPECTED,
                        cause=e
                    )
                raise
    
    def _get_handler_for_query[TQry](self, query: TQry) -> QueryHandler[TQry, Any]:
        """
        Get the handler for a query.
        
        Args:
            query: The query to get the handler for
            
        Returns:
            The query handler
            
        Raises:
            UnoError: If no handler is registered for the query type
        """
        query_type = type(query)
        
        # Check for direct handler
        if query_type in self._handlers:
            return self._handlers[query_type]
        
        # Check for handler for parent class
        for base in query_type.__mro__[1:]:  # Skip the query type itself
            if base in self._handlers and base != object:
                return self._handlers[base]
        
        # No handler found
        raise UnoError(
            message=f"No handler registered for query {query_type.__name__}",
            code="QUERY_HANDLER_NOT_FOUND",
            category=ErrorCategory.NOT_FOUND
        )


# =============================================================================
# Base Handler Implementations
# =============================================================================

class BaseCommandHandler[TCommand, TResult](CommandHandler[TCommand, TResult]):
    """
    Base implementation of a command handler.
    
    Command handlers process commands and produce results. They can also
    publish events as a result of command execution.
    
    Type Parameters:
        TCommand: The type of command this handler processes
        TResult: The type of result after command execution
    """
    
    def __init__(self, event_publisher: Optional[EventPublisher] = None):
        """
        Initialize a command handler.
        
        Args:
            event_publisher: Optional event publisher for raising events
        """
        self._event_publisher = event_publisher
        self._pending_events: List[Event] = []
    
    @abstractmethod
    async def handle(self, command: TCommand) -> TResult:
        """
        Handle a command.
        
        Args:
            command: The command to handle
            
        Returns:
            Result of command execution
        """
        raise NotImplementedError("Command handlers must implement handle")
    
    def add_event(self, event: Event) -> None:
        """
        Add an event to be published after command execution.
        
        Args:
            event: The event to add
        """
        self._pending_events.append(event)
    
    async def publish_events(self) -> None:
        """Publish all pending events."""
        if not self._pending_events:
            return
        
        publisher = self._event_publisher or get_event_publisher()
        for event in self._pending_events:
            publisher.publish(event)
        
        self._pending_events.clear()


class BaseQueryHandler[TQuery, TResult](QueryHandler[TQuery, TResult]):
    """
    Base implementation of a query handler.
    
    Query handlers process queries and produce results. They should not
    change the state of the system.
    
    Type Parameters:
        TQuery: The type of query this handler processes
        TResult: The type of result after query execution
    """
    
    @abstractmethod
    async def handle(self, query: TQuery) -> TResult:
        """
        Handle a query.
        
        Args:
            query: The query to handle
            
        Returns:
            Result of query execution
        """
        raise NotImplementedError("Query handlers must implement handle")


# =============================================================================
# Handler Decorators
# =============================================================================

def command_handler[TCommand, TResult](command_type: Type[TCommand]):
    """
    Decorator for marking a method as a command handler.
    
    This decorator can be used to mark methods as command handlers and 
    register them with the command bus.
    
    Args:
        command_type: The type of command to handle
        
    Returns:
        Decorated method with command handler metadata
    """
    def decorator(func):
        # Store metadata on the function
        func.__command_handler__ = True
        func.__command_type__ = command_type
        return func
    
    return decorator


def query_handler[TQuery, TResult](query_type: Type[TQuery]):
    """
    Decorator for marking a method as a query handler.
    
    This decorator can be used to mark methods as query handlers and 
    register them with the query bus.
    
    Args:
        query_type: The type of query to handle
        
    Returns:
        Decorated method with query handler metadata
    """
    def decorator(func):
        # Store metadata on the function
        func.__query_handler__ = True
        func.__query_type__ = query_type
        return func
    
    return decorator


# =============================================================================
# Handler Registry
# =============================================================================

class HandlerRegistry:
    """
    Registry for command and query handlers.
    
    The handler registry scans classes and modules for command and query handlers
    and registers them with the appropriate buses.
    """
    
    def __init__(
        self,
        command_bus: Optional[CommandBus] = None,
        query_bus: Optional[QueryBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the handler registry.
        
        Args:
            command_bus: Optional command bus to register command handlers with
            query_bus: Optional query bus to register query handlers with
            logger: Optional logger for diagnostic information
        """
        self._command_bus = command_bus or CommandBus()
        self._query_bus = query_bus or QueryBus()
        self._logger = logger or logging.getLogger("uno.cqrs.registry")
    
    def register_command_handler[TCommand, TResult](
        self,
        command_type: Type[TCommand],
        handler: CommandHandler[TCommand, TResult]
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_type: The type of command to register
            handler: The handler for the command
        """
        self._command_bus.register(command_type, handler)
    
    def register_query_handler[TQuery, TResult](
        self,
        query_type: Type[TQuery],
        handler: QueryHandler[TQuery, TResult]
    ) -> None:
        """
        Register a query handler.
        
        Args:
            query_type: The type of query to register
            handler: The handler for the query
        """
        self._query_bus.register(query_type, handler)
    
    def scan_instance(self, instance: Any) -> int:
        """
        Scan an instance for command and query handlers.
        
        Args:
            instance: The instance to scan
            
        Returns:
            Number of handlers registered
        """
        count = 0
        
        # Find all methods in the instance
        for name, method in inspect.getmembers(instance, inspect.ismethod):
            # Check for command handlers
            if hasattr(method, "__command_handler__"):
                command_type = getattr(method, "__command_type__", None)
                
                if command_type is not None:
                    # Create a handler class dynamically
                    handler_class = type(
                        f"{instance.__class__.__name__}_{name}_CommandHandler",
                        (BaseCommandHandler,),
                        {"handle": method}
                    )
                    
                    # Register the handler
                    self._command_bus.register(command_type, handler_class())
                    count += 1
                    self._logger.debug(f"Registered command handler {instance.__class__.__name__}.{name} for {command_type.__name__}")
            
            # Check for query handlers
            if hasattr(method, "__query_handler__"):
                query_type = getattr(method, "__query_type__", None)
                
                if query_type is not None:
                    # Create a handler class dynamically
                    handler_class = type(
                        f"{instance.__class__.__name__}_{name}_QueryHandler",
                        (BaseQueryHandler,),
                        {"handle": method}
                    )
                    
                    # Register the handler
                    self._query_bus.register(query_type, handler_class())
                    count += 1
                    self._logger.debug(f"Registered query handler {instance.__class__.__name__}.{name} for {query_type.__name__}")
        
        return count
    
    def scan_module(self, module: Any) -> int:
        """
        Scan a module for command and query handlers.
        
        Args:
            module: The module to scan
            
        Returns:
            Number of handlers registered
        """
        count = 0
        
        # Find all handler classes in the module
        for name, obj in inspect.getmembers(module):
            # Only process classes
            if not inspect.isclass(obj):
                continue
            
            # Check if it's a command handler
            if (
                issubclass(obj, CommandHandler) and 
                obj != CommandHandler and 
                obj != BaseCommandHandler
            ):
                # Find the command type from type hints
                handle_method = obj.handle
                hints = get_type_hints(handle_method)
                
                if "command" in hints:
                    command_type = hints["command"]
                    
                    # Create instance and register
                    try:
                        handler = obj()
                        self._command_bus.register(command_type, handler)
                        count += 1
                        self._logger.debug(f"Registered command handler {obj.__name__} for {command_type.__name__}")
                    except Exception as e:
                        self._logger.error(f"Error creating command handler {obj.__name__}: {str(e)}")
            
            # Check if it's a query handler
            if (
                issubclass(obj, QueryHandler) and 
                obj != QueryHandler and 
                obj != BaseQueryHandler
            ):
                # Find the query type from type hints
                handle_method = obj.handle
                hints = get_type_hints(handle_method)
                
                if "query" in hints:
                    query_type = hints["query"]
                    
                    # Create instance and register
                    try:
                        handler = obj()
                        self._query_bus.register(query_type, handler)
                        count += 1
                        self._logger.debug(f"Registered query handler {obj.__name__} for {query_type.__name__}")
                    except Exception as e:
                        self._logger.error(f"Error creating query handler {obj.__name__}: {str(e)}")
        
        return count
    
    @property
    def command_bus(self) -> CommandBus:
        """Get the command bus."""
        return self._command_bus
    
    @property
    def query_bus(self) -> QueryBus:
        """Get the query bus."""
        return self._query_bus


# =============================================================================
# CQRS Mediator
# =============================================================================

class Mediator:
    """
    Mediator for CQRS operations.
    
    The mediator provides a single entry point for executing commands and queries,
    encapsulating the command and query buses.
    """
    
    def __init__(
        self,
        command_bus: Optional[CommandBus] = None,
        query_bus: Optional[QueryBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the mediator.
        
        Args:
            command_bus: Optional command bus for executing commands
            query_bus: Optional query bus for executing queries
            logger: Optional logger for diagnostic information
        """
        self._command_bus = command_bus or CommandBus()
        self._query_bus = query_bus or QueryBus()
        self._logger = logger or logging.getLogger("uno.cqrs.mediator")
    
    async def execute_command[TResult](self, command: Command[TResult]) -> TResult:
        """
        Execute a command.
        
        Args:
            command: The command to execute
            
        Returns:
            The result of command execution
        """
        return await self._command_bus.execute(command)
    
    async def execute_query[TResult](self, query: Query[TResult]) -> TResult:
        """
        Execute a query.
        
        Args:
            query: The query to execute
            
        Returns:
            The result of query execution
        """
        return await self._query_bus.execute(query)
    
    @property
    def command_bus(self) -> CommandBus:
        """Get the command bus."""
        return self._command_bus
    
    @property
    def query_bus(self) -> QueryBus:
        """Get the query bus."""
        return self._query_bus


# =============================================================================
# Global Mediator
# =============================================================================

_mediator: Optional[Mediator] = None


def get_mediator() -> Mediator:
    """
    Get the global mediator instance.
    
    Returns:
        The global mediator instance
        
    Raises:
        UnoError: If the mediator is not initialized
    """
    global _mediator
    if _mediator is None:
        raise UnoError(
            message="Mediator is not initialized",
            code="MEDIATOR_NOT_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    return _mediator


def initialize_mediator(
    command_bus: Optional[CommandBus] = None,
    query_bus: Optional[QueryBus] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Initialize the global mediator.
    
    Args:
        command_bus: Optional command bus for executing commands
        query_bus: Optional query bus for executing queries
        logger: Optional logger for diagnostic information
        
    Raises:
        UnoError: If the mediator is already initialized
    """
    global _mediator
    if _mediator is not None:
        raise UnoError(
            message="Mediator is already initialized",
            code="MEDIATOR_ALREADY_INITIALIZED",
            category=ErrorCategory.UNEXPECTED,
        )
    
    _mediator = Mediator(command_bus, query_bus, logger)


def reset_mediator() -> None:
    """Reset the global mediator (primarily for testing)."""
    global _mediator
    _mediator = None


# =============================================================================
# Public API Functions
# =============================================================================

async def execute_command[TResult](command: Command[TResult]) -> TResult:
    """
    Execute a command using the global mediator.
    
    Args:
        command: The command to execute
        
    Returns:
        The result of command execution
    """
    return await get_mediator().execute_command(command)


async def execute_query[TResult](query: Query[TResult]) -> TResult:
    """
    Execute a query using the global mediator.
    
    Args:
        query: The query to execute
        
    Returns:
        The result of query execution
    """
    return await get_mediator().execute_query(query)