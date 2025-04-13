"""
CQRS (Command Query Responsibility Segregation) implementation for the Uno framework.

This module provides the core components for implementing the CQRS pattern,
which separates the command (write) and query (read) sides of the application.
"""

import inspect
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, Callable, Awaitable, Union
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from uno.domain.events import DomainEvent, EventBus, get_event_bus
from uno.domain.exceptions import DomainError
from uno.domain.unit_of_work import UnitOfWork


# Type variables
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')
CommandT = TypeVar('CommandT', bound='Command')


class CommandStatus(Enum):
    """Status of a command execution."""
    
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()
    REJECTED = auto()


@dataclass
class CommandResult:
    """
    Result of a command execution.
    
    This class encapsulates the result of a command execution,
    including the status, output data, and any error information.
    """
    
    status: CommandStatus
    command_id: str
    command_type: str
    output: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    events: List[DomainEvent] = field(default_factory=list)
    
    @property
    def is_success(self) -> bool:
        """Check if the command execution was successful."""
        return self.status == CommandStatus.COMPLETED
    
    @property
    def is_failure(self) -> bool:
        """Check if the command execution failed."""
        return self.status in (CommandStatus.FAILED, CommandStatus.REJECTED)
    
    @classmethod
    def success(
        cls, command_id: str, command_type: str, output: Any = None, events: List[DomainEvent] = None
    ) -> 'CommandResult':
        """Create a successful command result."""
        return cls(
            status=CommandStatus.COMPLETED,
            command_id=command_id,
            command_type=command_type,
            output=output,
            events=events or []
        )
    
    @classmethod
    def failure(
        cls, command_id: str, command_type: str, error: str, error_code: Optional[str] = None
    ) -> 'CommandResult':
        """Create a failed command result."""
        return cls(
            status=CommandStatus.FAILED,
            command_id=command_id,
            command_type=command_type,
            error=error,
            error_code=error_code
        )
    
    @classmethod
    def rejection(
        cls, command_id: str, command_type: str, error: str, error_code: Optional[str] = None
    ) -> 'CommandResult':
        """Create a rejected command result."""
        return cls(
            status=CommandStatus.REJECTED,
            command_id=command_id,
            command_type=command_type,
            error=error,
            error_code=error_code
        )


class Command(BaseModel):
    """
    Base class for commands in the CQRS pattern.
    
    Commands represent intentions to change the system state. They are
    named with imperative verbs and are handled by command handlers.
    """
    
    model_config = ConfigDict(frozen=True)
    
    command_id: str = Field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CommandHandler(Generic[CommandT, OutputT], ABC):
    """
    Abstract base class for command handlers.
    
    Command handlers process commands by executing business logic
    that changes the system state.
    """
    
    def __init__(
        self, 
        command_type: Type[CommandT],
        unit_of_work_factory: Callable[[], UnitOfWork],
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the command handler.
        
        Args:
            command_type: The type of command this handler can process
            unit_of_work_factory: Factory function that creates units of work
            event_bus: Optional event bus for publishing events
            logger: Optional logger instance
        """
        self.command_type = command_type
        self.unit_of_work_factory = unit_of_work_factory
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, command: CommandT) -> CommandResult:
        """
        Execute a command.
        
        This method validates the command, executes it within a unit of work,
        and publishes any resulting events.
        
        Args:
            command: The command to execute
            
        Returns:
            The result of the command execution
        """
        # Validate the command
        try:
            self.validate(command)
        except Exception as e:
            self.logger.error(f"Command validation failed: {str(e)}")
            return CommandResult.rejection(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code=getattr(e, "code", "VALIDATION_ERROR")
            )
        
        # Execute the command within a unit of work
        try:
            async with self.unit_of_work_factory() as uow:
                # Execute the handler
                result = await self._handle(command, uow)
                
                # If the handler returned events, publish them
                events = result.events if isinstance(result, CommandResult) else []
                
                return CommandResult.success(
                    command_id=command.command_id,
                    command_type=command.__class__.__name__,
                    output=result if not isinstance(result, CommandResult) else result.output,
                    events=events
                )
        except DomainError as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return CommandResult.failure(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code=e.code
            )
        except Exception as e:
            self.logger.error(f"Command execution failed: {str(e)}")
            return CommandResult.failure(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code="COMMAND_EXECUTION_ERROR"
            )
    
    def validate(self, command: CommandT) -> None:
        """
        Validate a command before execution.
        
        This method can be overridden by subclasses to implement
        custom validation logic.
        
        Args:
            command: The command to validate
            
        Raises:
            DomainError: If validation fails
        """
        pass
    
    @abstractmethod
    async def _handle(self, command: CommandT, uow: UnitOfWork) -> OutputT:
        """
        Handle a command.
        
        This method should be implemented by subclasses to provide
        the specific command handling logic.
        
        Args:
            command: The command to handle
            uow: The unit of work for transaction management
            
        Returns:
            The result of the command execution
        """
        pass


class QueryStatus(Enum):
    """Status of a query execution."""
    
    PENDING = auto()
    PROCESSING = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass
class QueryResult(Generic[OutputT]):
    """
    Result of a query execution.
    
    This class encapsulates the result of a query execution,
    including the status, output data, and any error information.
    """
    
    status: QueryStatus
    query_id: str
    query_type: str
    output: Optional[OutputT] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    
    @property
    def is_success(self) -> bool:
        """Check if the query execution was successful."""
        return self.status == QueryStatus.COMPLETED
    
    @property
    def is_failure(self) -> bool:
        """Check if the query execution failed."""
        return self.status == QueryStatus.FAILED
    
    @classmethod
    def success(
        cls, query_id: str, query_type: str, output: OutputT
    ) -> 'QueryResult[OutputT]':
        """Create a successful query result."""
        return cls(
            status=QueryStatus.COMPLETED,
            query_id=query_id,
            query_type=query_type,
            output=output
        )
    
    @classmethod
    def failure(
        cls, query_id: str, query_type: str, error: str, error_code: Optional[str] = None
    ) -> 'QueryResult[OutputT]':
        """Create a failed query result."""
        return cls(
            status=QueryStatus.FAILED,
            query_id=query_id,
            query_type=query_type,
            error=error,
            error_code=error_code
        )


class Query(BaseModel, Generic[OutputT]):
    """
    Base class for queries in the CQRS pattern.
    
    Queries represent requests for information. They do not change
    the system state and are handled by query handlers.
    
    Type Parameters:
        OutputT: The type of the query result
    """
    
    model_config = ConfigDict(frozen=True)
    
    query_id: str = Field(default_factory=lambda: str(uuid4()))


QueryT = TypeVar('QueryT', bound=Query)


class QueryHandler(Generic[QueryT, OutputT], ABC):
    """
    Abstract base class for query handlers.
    
    Query handlers process queries by executing business logic
    that retrieves information without changing the system state.
    """
    
    def __init__(
        self,
        query_type: Type[QueryT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query handler.
        
        Args:
            query_type: The type of query this handler can process
            logger: Optional logger instance
        """
        self.query_type = query_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, query: QueryT) -> QueryResult[OutputT]:
        """
        Execute a query.
        
        This method validates the query and executes it.
        
        Args:
            query: The query to execute
            
        Returns:
            The result of the query execution
        """
        # Validate the query
        try:
            self.validate(query)
        except Exception as e:
            self.logger.error(f"Query validation failed: {str(e)}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=str(e),
                error_code=getattr(e, "code", "VALIDATION_ERROR")
            )
        
        # Execute the query
        try:
            result = await self._handle(query)
            return QueryResult.success(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                output=result
            )
        except Exception as e:
            self.logger.error(f"Query execution failed: {str(e)}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=str(e),
                error_code=getattr(e, "code", "QUERY_EXECUTION_ERROR")
            )
    
    def validate(self, query: QueryT) -> None:
        """
        Validate a query before execution.
        
        This method can be overridden by subclasses to implement
        custom validation logic.
        
        Args:
            query: The query to validate
            
        Raises:
            DomainError: If validation fails
        """
        pass
    
    @abstractmethod
    async def _handle(self, query: QueryT) -> OutputT:
        """
        Handle a query.
        
        This method should be implemented by subclasses to provide
        the specific query handling logic.
        
        Args:
            query: The query to handle
            
        Returns:
            The result of the query execution
        """
        pass


class Dispatcher:
    """
    Dispatcher for commands and queries.
    
    The dispatcher routes commands and queries to their respective handlers.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the dispatcher.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._command_handlers: Dict[Type[Command], CommandHandler] = {}
        self._query_handlers: Dict[Type[Query], QueryHandler] = {}
    
    def register_command_handler(self, handler: CommandHandler) -> None:
        """
        Register a command handler.
        
        Args:
            handler: The command handler to register
        """
        self._command_handlers[handler.command_type] = handler
        self.logger.debug(f"Registered command handler for {handler.command_type.__name__}")
    
    def register_query_handler(self, handler: QueryHandler) -> None:
        """
        Register a query handler.
        
        Args:
            handler: The query handler to register
        """
        self._query_handlers[handler.query_type] = handler
        self.logger.debug(f"Registered query handler for {handler.query_type.__name__}")
    
    async def dispatch_command(self, command: Command) -> CommandResult:
        """
        Dispatch a command to its handler.
        
        Args:
            command: The command to dispatch
            
        Returns:
            The result of the command execution
            
        Raises:
            ValueError: If no handler is registered for the command
        """
        handler = self._command_handlers.get(command.__class__)
        if not handler:
            self.logger.error(f"No handler registered for command {command.__class__.__name__}")
            return CommandResult.rejection(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=f"No handler registered for command {command.__class__.__name__}",
                error_code="HANDLER_NOT_FOUND"
            )
        
        return await handler.execute(command)
    
    async def dispatch_query(self, query: Query) -> QueryResult:
        """
        Dispatch a query to its handler.
        
        Args:
            query: The query to dispatch
            
        Returns:
            The result of the query execution
            
        Raises:
            ValueError: If no handler is registered for the query
        """
        handler = self._query_handlers.get(query.__class__)
        if not handler:
            self.logger.error(f"No handler registered for query {query.__class__.__name__}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=f"No handler registered for query {query.__class__.__name__}",
                error_code="HANDLER_NOT_FOUND"
            )
        
        return await handler.execute(query)


# Create a default dispatcher
default_dispatcher = Dispatcher()


def get_dispatcher() -> Dispatcher:
    """Get the default dispatcher."""
    return default_dispatcher


def register_command_handler(handler: CommandHandler) -> CommandHandler:
    """
    Register a command handler with the default dispatcher.
    
    Args:
        handler: The command handler to register
        
    Returns:
        The command handler
    """
    default_dispatcher.register_command_handler(handler)
    return handler


def register_query_handler(handler: QueryHandler) -> QueryHandler:
    """
    Register a query handler with the default dispatcher.
    
    Args:
        handler: The query handler to register
        
    Returns:
        The query handler
    """
    default_dispatcher.register_query_handler(handler)
    return handler