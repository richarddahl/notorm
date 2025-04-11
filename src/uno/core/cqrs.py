"""
CQRS pattern implementation for the Uno framework.

This module implements the Command Query Responsibility Segregation (CQRS) pattern,
separating write operations (commands) from read operations (queries).
"""

import inspect
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, TypeVar, Generic, Type, Optional, Callable, Dict, List, Set, cast

from uno.core.protocols import Command, CommandHandler, Query, QueryHandler
from uno.core.result import Result, Success, Failure

T = TypeVar('T')
CommandT = TypeVar('CommandT', bound=Command)
QueryT = TypeVar('QueryT', bound=Query)
ResultT = TypeVar('ResultT')


@dataclass
class BaseCommand:
    """Base class for commands."""
    
    command_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def command_type(self) -> str:
        """Get the type of this command."""
        return self.__class__.__name__


@dataclass
class BaseQuery:
    """Base class for queries."""
    
    query_id: uuid.UUID = field(default_factory=uuid.uuid4)
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def query_type(self) -> str:
        """Get the type of this query."""
        return self.__class__.__name__


class BaseCommandHandler(Generic[CommandT, ResultT]):
    """Base class for command handlers."""
    
    async def handle(self, command: CommandT) -> Result[ResultT]:
        """
        Handle a command.
        
        Args:
            command: The command to handle
            
        Returns:
            A Result with the operation result
        """
        raise NotImplementedError("Subclasses must implement handle")


class BaseQueryHandler(Generic[QueryT, ResultT]):
    """Base class for query handlers."""
    
    async def handle(self, query: QueryT) -> Result[ResultT]:
        """
        Handle a query.
        
        Args:
            query: The query to handle
            
        Returns:
            A Result with the query result
        """
        raise NotImplementedError("Subclasses must implement handle")


class CommandBus:
    """Command bus for dispatching commands to handlers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the command bus.
        
        Args:
            logger: Optional logger
        """
        self._handlers: Dict[str, CommandHandler[Any, Any]] = {}
        self._logger = logger or logging.getLogger(__name__)
    
    def register_handler(self, command_type: str, handler: CommandHandler[Any, Any]) -> None:
        """
        Register a handler for a command type.
        
        Args:
            command_type: The command type
            handler: The handler
        """
        if command_type in self._handlers:
            self._logger.warning(f"Overriding existing handler for command: {command_type}")
        self._handlers[command_type] = handler
        self._logger.debug(f"Registered handler for command: {command_type}")
    
    def register_handler_for_type(self, command_class: Type[Command], handler: CommandHandler[Any, Any]) -> None:
        """
        Register a handler for a command class.
        
        Args:
            command_class: The command class
            handler: The handler
        """
        command_type = command_class.__name__
        self.register_handler(command_type, handler)
    
    async def dispatch(self, command: Command) -> Result[Any]:
        """
        Dispatch a command to its handler.
        
        Args:
            command: The command to dispatch
            
        Returns:
            A Result with the operation result
        """
        command_type = command.command_type
        self._logger.debug(f"Dispatching command: {command_type} ({command.command_id})")
        
        if command_type not in self._handlers:
            error_msg = f"No handler registered for command: {command_type}"
            self._logger.error(error_msg)
            return Failure(ValueError(error_msg))
        
        handler = self._handlers[command_type]
        try:
            return await handler.handle(command)
        except Exception as e:
            self._logger.error(f"Error handling command {command_type}: {e}")
            return Failure(e)


class QueryBus:
    """Query bus for dispatching queries to handlers."""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the query bus.
        
        Args:
            logger: Optional logger
        """
        self._handlers: Dict[str, QueryHandler[Any, Any]] = {}
        self._logger = logger or logging.getLogger(__name__)
    
    def register_handler(self, query_type: str, handler: QueryHandler[Any, Any]) -> None:
        """
        Register a handler for a query type.
        
        Args:
            query_type: The query type
            handler: The handler
        """
        if query_type in self._handlers:
            self._logger.warning(f"Overriding existing handler for query: {query_type}")
        self._handlers[query_type] = handler
        self._logger.debug(f"Registered handler for query: {query_type}")
    
    def register_handler_for_type(self, query_class: Type[Query], handler: QueryHandler[Any, Any]) -> None:
        """
        Register a handler for a query class.
        
        Args:
            query_class: The query class
            handler: The handler
        """
        query_type = query_class.__name__
        self.register_handler(query_type, handler)
    
    async def dispatch(self, query: Query) -> Result[Any]:
        """
        Dispatch a query to its handler.
        
        Args:
            query: The query to dispatch
            
        Returns:
            A Result with the query result
        """
        query_type = query.query_type
        self._logger.debug(f"Dispatching query: {query_type} ({query.query_id})")
        
        if query_type not in self._handlers:
            error_msg = f"No handler registered for query: {query_type}"
            self._logger.error(error_msg)
            return Failure(ValueError(error_msg))
        
        handler = self._handlers[query_type]
        try:
            return await handler.handle(query)
        except Exception as e:
            self._logger.error(f"Error handling query {query_type}: {e}")
            return Failure(e)


class HandlerRegistry:
    """Registry for command and query handlers."""
    
    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the registry.
        
        Args:
            command_bus: The command bus
            query_bus: The query bus
            logger: Optional logger
        """
        self._command_bus = command_bus
        self._query_bus = query_bus
        self._logger = logger or logging.getLogger(__name__)
        self._registered_handlers: Set[Any] = set()
    
    def register_handler(self, handler: Any) -> None:
        """
        Register a handler.
        
        This method inspects the handler to determine if it's a command handler,
        a query handler, or both, and registers it accordingly.
        
        Args:
            handler: The handler to register
        """
        if handler in self._registered_handlers:
            return
        
        # Check if the handler is a command handler
        for command_class in self._get_handled_command_types(handler):
            self._command_bus.register_handler_for_type(command_class, cast(CommandHandler[Any, Any], handler))
        
        # Check if the handler is a query handler
        for query_class in self._get_handled_query_types(handler):
            self._query_bus.register_handler_for_type(query_class, cast(QueryHandler[Any, Any], handler))
        
        self._registered_handlers.add(handler)
    
    def register_command_handler(self, command_class: Type[Command], handler: CommandHandler[Any, Any]) -> None:
        """
        Register a command handler.
        
        Args:
            command_class: The command class
            handler: The handler
        """
        self._command_bus.register_handler_for_type(command_class, handler)
        self._registered_handlers.add(handler)
    
    def register_query_handler(self, query_class: Type[Query], handler: QueryHandler[Any, Any]) -> None:
        """
        Register a query handler.
        
        Args:
            query_class: The query class
            handler: The handler
        """
        self._query_bus.register_handler_for_type(query_class, handler)
        self._registered_handlers.add(handler)
    
    def register_handlers(self, handlers: List[Any]) -> None:
        """
        Register multiple handlers.
        
        Args:
            handlers: The handlers to register
        """
        for handler in handlers:
            self.register_handler(handler)
    
    def _get_handled_command_types(self, handler: Any) -> List[Type[Command]]:
        """
        Get the command types handled by a handler.
        
        Args:
            handler: The handler
            
        Returns:
            A list of command types
        """
        result = []
        
        # Check if the handler has explicit command type information
        if hasattr(handler, "handled_command_types"):
            return handler.handled_command_types()
        
        # Check the class hierarchy
        bases = inspect.getmro(handler.__class__)
        for base in bases:
            if (hasattr(base, "__origin__") and 
                base.__origin__ is Generic and 
                len(base.__args__) >= 1 and
                issubclass(base.__args__[0], Command)):
                result.append(base.__args__[0])
        
        return result
    
    def _get_handled_query_types(self, handler: Any) -> List[Type[Query]]:
        """
        Get the query types handled by a handler.
        
        Args:
            handler: The handler
            
        Returns:
            A list of query types
        """
        result = []
        
        # Check if the handler has explicit query type information
        if hasattr(handler, "handled_query_types"):
            return handler.handled_query_types()
        
        # Check the class hierarchy
        bases = inspect.getmro(handler.__class__)
        for base in bases:
            if (hasattr(base, "__origin__") and 
                base.__origin__ is Generic and 
                len(base.__args__) >= 1 and
                issubclass(base.__args__[0], Query)):
                result.append(base.__args__[0])
        
        return result


def command_handler(command_class: Type[CommandT]):
    """
    Decorator for command handler classes.
    
    This decorator marks a class as a command handler for a specific command type.
    
    Args:
        command_class: The command class
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        handled_types = getattr(cls, "_handled_command_types", [])
        handled_types.append(command_class)
        setattr(cls, "_handled_command_types", handled_types)
        
        # Add a method to get the handled command types
        def handled_command_types(self) -> List[Type[Command]]:
            return getattr(self.__class__, "_handled_command_types", [])
        setattr(cls, "handled_command_types", handled_command_types)
        
        return cls
    return decorator


def query_handler(query_class: Type[QueryT]):
    """
    Decorator for query handler classes.
    
    This decorator marks a class as a query handler for a specific query type.
    
    Args:
        query_class: The query class
    """
    def decorator(cls: Type[Any]) -> Type[Any]:
        handled_types = getattr(cls, "_handled_query_types", [])
        handled_types.append(query_class)
        setattr(cls, "_handled_query_types", handled_types)
        
        # Add a method to get the handled query types
        def handled_query_types(self) -> List[Type[Query]]:
            return getattr(self.__class__, "_handled_query_types", [])
        setattr(cls, "handled_query_types", handled_query_types)
        
        return cls
    return decorator