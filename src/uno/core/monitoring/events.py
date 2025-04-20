# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Structured event logging for the Uno application.

This module provides utilities for structured event logging, allowing
tracking of significant events across the application.
"""

from typing import Dict, List, Any, Optional, Callable, TypeVar, Generic, Set, Union, Protocol
import asyncio
import time
import logging
import uuid
import json
import contextvars
from enum import Enum, auto
from dataclasses import dataclass, field

from uno.core.errors import get_error_context, add_error_context
from uno.core.monitoring.tracing import get_current_trace_id, get_current_span_id


T = TypeVar('T')


class EventLevel(Enum):
    """Level of importance for an event."""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()
    
    @classmethod
    def from_string(cls, level_str: str) -> 'EventLevel':
        """
        Convert string to EventLevel.
        
        Args:
            level_str: Level string (case insensitive)
            
        Returns:
            EventLevel value
        """
        level_map = {
            "debug": cls.DEBUG,
            "info": cls.INFO,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "critical": cls.CRITICAL
        }
        return level_map.get(level_str.lower(), cls.INFO)


class EventType(Enum):
    """Type of event."""
    SYSTEM = auto()     # System events (startup, shutdown, etc.)
    SECURITY = auto()   # Security events (login, logout, permission changes)
    AUDIT = auto()      # Audit events (record changes, significant actions)
    BUSINESS = auto()   # Business events (order placed, payment processed)
    TECHNICAL = auto()  # Technical events (database operations, cache events)
    MONITORING = auto() # Monitoring events (health checks, metrics)
    
    @classmethod
    def from_string(cls, type_str: str) -> 'EventType':
        """
        Convert string to EventType.
        
        Args:
            type_str: Type string (case insensitive)
            
        Returns:
            EventType value
        """
        type_map = {
            "system": cls.SYSTEM,
            "security": cls.SECURITY,
            "audit": cls.AUDIT,
            "business": cls.BUSINESS,
            "technical": cls.TECHNICAL,
            "monitoring": cls.MONITORING
        }
        return type_map.get(type_str.lower(), cls.SYSTEM)


@dataclass
class EventContext:
    """Context for an event."""
    user_id: Optional[str] = None
    source: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)


from uno.core.events.event import Event as BaseEvent

class MonitoringEvent(BaseEvent):
    """
    Monitoring event that extends the canonical Event class.
    Inherits all canonical event metadata fields and supports full metadata/context propagation.
    Adds a 'level' field for monitoring/logging importance.
    """
    level: EventLevel

    def to_dict(self) -> dict:
        base = super().to_dict()
        base["level"] = self.level.name if hasattr(self.level, 'name') else str(self.level)
        return base

    def to_json(self) -> str:
        return super().to_json()


class EventFilter(Protocol):
    """
    Protocol for event filters.
    
    Event filters determine which events to process.
    """
    
    def __call__(self, event: Event) -> bool:
        """
        Check if an event should be processed.
        
        Args:
            event: The event to check
            
        Returns:
            True if the event should be processed, False otherwise
        """
        ...


class EventHandler(Protocol):
    """
    Protocol for event handlers.
    
    Event handlers process events, e.g., by logging them
    or sending them to an observability system.
    """
    
    async def handle_event(self, event: Event) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        ...


class LoggingEventHandler:
    """
    Event handler that logs events.
    
    This handler logs events to a Python logger.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the logging event handler.
        
        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger("events")
    
    async def handle_event(self, event: Event) -> None:
        """
        Log an event.
        
        Args:
            event: The event to log
        """
        # Map event level to logging level
        level_map = {
            EventLevel.DEBUG: logging.DEBUG,
            EventLevel.INFO: logging.INFO,
            EventLevel.WARNING: logging.WARNING,
            EventLevel.ERROR: logging.ERROR,
            EventLevel.CRITICAL: logging.CRITICAL
        }
        level = level_map.get(event.level, logging.INFO)
        
        # Format event context
        context_str = ""
        if event.context.user_id:
            context_str += f" user={event.context.user_id}"
        if event.context.trace_id:
            context_str += f" trace={event.context.trace_id}"
        
        # Log the event
        self.logger.log(
            level,
            f"[{event.type.name}] {event.message}{context_str}",
            extra={"event": event.to_dict()}
        )


class EventLogger:
    """
    Logger for structured events.
    
    This class creates and processes events, dispatching them
    to registered handlers.
    """
    
    def __init__(
        self,
        service_name: str,
        logger: Optional[logging.Logger] = None,
        min_level: EventLevel = EventLevel.INFO,
    ):
        """
        Initialize the event logger.
        
        Args:
            service_name: Name of the service
            logger: Logger for internal logging
            min_level: Minimum event level to log
        """
        self.service_name = service_name
        self.logger = logger or logging.getLogger(__name__)
        self.min_level = min_level
        self._handlers: List[EventHandler] = []
        self._filters: List[EventFilter] = []
        
        # Add default handler
        self._handlers.append(LoggingEventHandler())
    
    def add_handler(self, handler: EventHandler) -> None:
        """
        Add an event handler.
        
        Args:
            handler: The handler to add
        """
        self._handlers.append(handler)
    
    def add_filter(self, filter_func: EventFilter) -> None:
        """
        Add an event filter.
        
        Args:
            filter_func: The filter to add
        """
        self._filters.append(filter_func)
    
    def _create_context(self) -> EventContext:
        """
        Create an event context from current execution context.
        
        Returns:
            Event context with trace, request, and error context
        """
        # Get trace context
        trace_id = get_current_trace_id()
        span_id = get_current_span_id()
        
        # Get error context
        error_context = get_error_context()
        
        # Create event context
        context = EventContext(
            source=self.service_name,
            trace_id=trace_id,
            span_id=span_id,
            request_id=error_context.get("request_id"),
            user_id=error_context.get("user_id"),
            attributes=error_context
        )
        
        return context
    
    async def _should_log(self, event: Event) -> bool:
        """
        Check if an event should be logged.
        
        Args:
            event: The event to check
            
        Returns:
            True if the event should be logged, False otherwise
        """
        # Check minimum level
        if event.level.value < self.min_level.value:
            return False
        
        # Check filters
        for filter_func in self._filters:
            try:
                if not filter_func(event):
                    return False
            except Exception as e:
                self.logger.warning(f"Error in event filter: {str(e)}")
        
        return True
    
    async def log_event(
        self,
        name: str,
        message: str,
        level: EventLevel = EventLevel.INFO,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        context: Optional[EventContext] = None,
    ) -> str:
        """
        Log an event.
        
        Args:
            name: Name of the event
            message: Event message
            level: Event importance level
            event_type: Type of event
            data: Additional event data
            context: Override for event context
            
        Returns:
            ID of the logged event
        """
        # Create the event
        event_id = str(uuid.uuid4())
        event = Event(
            id=event_id,
            name=name,
            message=message,
            timestamp=time.time(),
            level=level,
            type=event_type,
            context=context or self._create_context(),
            data=data or {}
        )
        
        # Check if we should log this event
        if not await self._should_log(event):
            return event_id
        
        # Handle the event with all handlers
        for handler in self._handlers:
            try:
                await handler.handle_event(event)
            except Exception as e:
                self.logger.warning(f"Error in event handler: {str(e)}")
        
        return event_id
    
    async def debug(
        self,
        name: str,
        message: str,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a debug event.
        
        Args:
            name: Name of the event
            message: Event message
            event_type: Type of event
            data: Additional event data
            
        Returns:
            ID of the logged event
        """
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.DEBUG,
            event_type=event_type,
            data=data
        )
    
    async def info(
        self,
        name: str,
        message: str,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an info event.
        
        Args:
            name: Name of the event
            message: Event message
            event_type: Type of event
            data: Additional event data
            
        Returns:
            ID of the logged event
        """
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.INFO,
            event_type=event_type,
            data=data
        )
    
    async def warning(
        self,
        name: str,
        message: str,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a warning event.
        
        Args:
            name: Name of the event
            message: Event message
            event_type: Type of event
            data: Additional event data
            
        Returns:
            ID of the logged event
        """
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.WARNING,
            event_type=event_type,
            data=data
        )
    
    async def error(
        self,
        name: str,
        message: str,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> str:
        """
        Log an error event.
        
        Args:
            name: Name of the event
            message: Event message
            event_type: Type of event
            data: Additional event data
            exception: Optional exception that caused the error
            
        Returns:
            ID of the logged event
        """
        event_data = data or {}
        
        # Add exception details if provided
        if exception:
            event_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }
            
            # Add exception attributes
            if hasattr(exception, "__dict__"):
                for key, value in exception.__dict__.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        event_data["exception"][key] = value
        
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.ERROR,
            event_type=event_type,
            data=event_data
        )
    
    async def critical(
        self,
        name: str,
        message: str,
        event_type: EventType = EventType.SYSTEM,
        data: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
    ) -> str:
        """
        Log a critical event.
        
        Args:
            name: Name of the event
            message: Event message
            event_type: Type of event
            data: Additional event data
            exception: Optional exception that caused the error
            
        Returns:
            ID of the logged event
        """
        event_data = data or {}
        
        # Add exception details if provided
        if exception:
            event_data["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception)
            }
            
            # Add exception attributes
            if hasattr(exception, "__dict__"):
                for key, value in exception.__dict__.items():
                    if isinstance(value, (str, int, float, bool, type(None))):
                        event_data["exception"][key] = value
        
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.CRITICAL,
            event_type=event_type,
            data=event_data
        )
    
    async def audit(
        self,
        name: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log an audit event.
        
        Args:
            name: Name of the event
            message: Event message
            data: Additional event data
            
        Returns:
            ID of the logged event
        """
        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.INFO,
            event_type=EventType.AUDIT,
            data=data
        )
    
    async def security(
        self,
        name: str,
        message: str,
        level: EventLevel = EventLevel.INFO,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Log a security event.
        
        Args:
            name: Name of the event
            message: Event message
            level: Event importance level
            data: Additional event data
            
        Returns:
            ID of the logged event
        """
        return await self.log_event(
            name=name,
            message=message,
            level=level,
            event_type=EventType.SECURITY,
            data=data
        )


# Global event logger
event_logger: Optional[EventLogger] = None


def get_event_logger() -> EventLogger:
    """
    Get the global event logger.
    
    Returns:
        The global event logger
    """
    global event_logger
    if event_logger is None:
        event_logger = EventLogger(service_name="uno")
    return event_logger


async def log_event(
    name: str,
    message: str,
    level: Union[EventLevel, str] = EventLevel.INFO,
    event_type: Union[EventType, str] = EventType.SYSTEM,
    data: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Log an event using the global event logger.
    
    Args:
        name: Name of the event
        message: Event message
        level: Event importance level
        event_type: Type of event
        data: Additional event data
        
    Returns:
        ID of the logged event
    """
    logger = get_event_logger()
    
    # Convert string level/type to enum if needed
    if isinstance(level, str):
        level = EventLevel.from_string(level)
    if isinstance(event_type, str):
        event_type = EventType.from_string(event_type)
    
    return await logger.log_event(
        name=name,
        message=message,
        level=level,
        event_type=event_type,
        data=data
    )