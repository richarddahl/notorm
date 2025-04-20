# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Structured event logging for the Uno application.

This module provides utilities for structured event logging, allowing
tracking of significant events across the application.
"""

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Protocol, TypeVar

from uno.core.events.event import Event as BaseEvent

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
    user_id: str | None = None
    source: str | None = None
    request_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


class MonitoringEvent(BaseEvent):
    """
    Monitoring event that extends the canonical Event class.
    Inherits all canonical event metadata fields and supports full metadata/context propagation.
    Adds a 'level' field for monitoring/logging importance.
    """
    level: EventLevel

    def to_dict(self) -> dict[str, Any]:
        """Serialize MonitoringEvent to a dictionary, including the level field."""
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
    
    def __call__(self, event: BaseEvent) -> bool:
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
    
    async def handle_event(self, event: BaseEvent) -> None:
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
    
    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the logging event handler.
        
        Args:
            logger: Logger to use
        """
        self.logger = logger or logging.getLogger("events")
    
    async def handle_event(self, event: BaseEvent) -> None:
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
        *,
        logger: logging.Logger | None = None,
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
        self._handlers: list[EventHandler] = []
        self._filters: list[EventFilter] = []
        
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
    
    def get_event_context(
        self,
        *,
        user_id: str | None = None,
        source: str | None = None,
        request_id: str | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> EventContext:
        """
        Create an EventContext object.
        """
        return EventContext(
            user_id=user_id,
            source=source,
            request_id=request_id,
            trace_id=trace_id,
            span_id=span_id,
            attributes=attributes or {},
        )
    
    async def _should_log(self, event: BaseEvent) -> bool:
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
                self.logger.warning(f"Error in event filter: {e}")
        
        return True
    
    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        id: str | None = None,
        name: str | None = None,
        message: str | None = None,
        timestamp: float | None = None,
        level: EventLevel | None = None,
        event_type: EventType | None = None,
        user_id: str | None = None,
        source: str | None = None,
        context: EventContext | None = None,
    ) -> BaseEvent:
        """
        Create a BaseEvent object from a dictionary.
        
        Args:
            data: Dictionary containing event data
            id: Event ID
            name: Event name
            message: Event message
            timestamp: Event timestamp
            level: Event level
            event_type: Event type
            user_id: User ID
            source: Event source
            context: Event context
            
        Returns:
            BaseEvent object
        """
        return BaseEvent(
            id=id or data.get("id"),
            name=name or data.get("name"),
            message=message or data.get("message"),
            timestamp=timestamp or data.get("timestamp"),
            level=level or EventLevel.from_string(data.get("level")),
            type=event_type or EventType.from_string(data.get("type")),
            context=context or EventContext(
                user_id=user_id or data.get("user_id"),
                source=source or data.get("source"),
                request_id=data.get("request_id"),
                trace_id=data.get("trace_id"),
                span_id=data.get("span_id"),
                attributes=data.get("attributes", {}),
            ),
            data=data.get("data", {}),
        )
    
    async def log_event(
        self,
        name: str,
        message: str,
        *,
        level: EventLevel = EventLevel.INFO,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
        context: EventContext | None = None,
    ) -> str:
        """
        Log an event with the specified parameters.
        
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
        event = BaseEvent(
            id=event_id,
            name=name,
            message=message,
            timestamp=time.time(),
            level=level,
            type=event_type,
            context=context or self.get_event_context(),
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

    async def log_debug(
        self,
        name: str,
        message: str,
        *,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
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

    async def log_info(
        self,
        name: str,
        message: str,
        *,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
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

    async def log_warning(
        self,
        name: str,
        message: str,
        *,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
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

    async def log_error(
        self,
        name: str,
        message: str,
        *,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
        exception: Exception | None = None,
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
                    if isinstance(value, (str | int | float | bool | type(None))):
                        event_data["exception"][key] = value

        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.ERROR,
            event_type=event_type,
            data=event_data
        )

    async def log_critical(
        self,
        name: str,
        message: str,
        *,
        event_type: EventType = EventType.SYSTEM,
        data: dict[str, Any] | None = None,
        exception: Exception | None = None,
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
                    if isinstance(value, (str | int | float | bool | type(None))):
                        event_data["exception"][key] = value

        return await self.log_event(
            name=name,
            message=message,
            level=EventLevel.CRITICAL,
            event_type=event_type,
            data=event_data
        )

    async def log_audit(
        self,
        name: str,
        message: str,
        *,
        data: dict[str, Any] | None = None,
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

    async def log_security(
        self,
        name: str,
        message: str,
        *,
        level: EventLevel = EventLevel.INFO,
        data: dict[str, Any] | None = None,
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

    async def get_events_by_time_range(
        self,
        start_time: float,
        end_time: float,
        *,
        event_type: str | None = None,
        user_id: str | None = None,
    ) -> list[BaseEvent]:
        """
        Get events by time range.

        Args:
            start_time: Start time of the range
            end_time: End time of the range
            event_type: Type of event
            user_id: User ID

        Returns:
            List of events
        """
        # TO DO: implement this method
        return []

    async def get_events(
        self,
        *,
        filter_by: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort_by: str | None = None,
        sort_desc: bool = False,
    ) -> list[BaseEvent]:
        """
        Filter a list of events based on criteria.
        
        Args:
            filter_by: Filter by field
            limit: Maximum number of events
            offset: Offset for pagination
            sort_by: Field to sort by
            sort_desc: Sort in descending order
            
        Returns:
            List of events
        """
        # TO DO: implement this method
        return []



# Module-level singleton pattern for event logger
_event_logger: EventLogger | None = None


def get_event_logger() -> EventLogger:
    """
    Get the singleton event logger instance.
    """
    if not hasattr(get_event_logger, "_instance"):
        get_event_logger._instance = EventLogger()
    return get_event_logger._instance


async def log_event(
    name: str,
    message: str,
    level: EventLevel | str = EventLevel.INFO,
    event_type: EventType | str = EventType.SYSTEM,
    data: dict[str, Any] | None = None,
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