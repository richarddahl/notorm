"""Server-Sent Events (SSE) event definitions.

This module defines the event structure for SSE communication.
"""

import json
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any, List, Union, ClassVar


class EventPriority(Enum):
    """Priority levels for SSE events."""
    
    LOWEST = 0
    LOW = 1
    NORMAL = 2  # Default
    HIGH = 3
    HIGHEST = 4
    CRITICAL = 5


@dataclass
class Event:
    """Represents a Server-Sent Event.
    
    Attributes:
        data: The event data payload.
        id: The event ID, automatically generated if not provided.
        event: The event type name, defaults to "message".
        retry: Optional reconnection time in milliseconds.
        priority: Event priority for delivery order.
        timestamp: The event creation timestamp.
    """
    
    data: Any
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event: Optional[str] = "message"
    retry: Optional[int] = None  # Reconnection time in milliseconds
    priority: EventPriority = field(default=EventPriority.NORMAL)
    timestamp: float = field(default_factory=lambda: __import__('time').time())
    
    def to_sse_format(self) -> str:
        """Convert the event to SSE format.
        
        Server-Sent Events format:
        - Lines starting with a colon (:) are comments and ignored
        - Each field has format "field: value"
        - Empty line marks the end of an event
        
        Returns:
            A string in SSE format.
        """
        lines = []
        
        # Add optional comment with timestamp
        lines.append(f": timestamp={self.timestamp}")
        
        # Add event ID if present
        if self.id:
            lines.append(f"id: {self.id}")
        
        # Add event type if present and not default
        if self.event and self.event != "message":
            lines.append(f"event: {self.event}")
        
        # Add retry if present
        if self.retry is not None:
            lines.append(f"retry: {self.retry}")
        
        # Add data - serialize complex objects
        data_str = self.data
        if not isinstance(self.data, str):
            try:
                data_str = json.dumps(self.data)
            except (TypeError, ValueError):
                data_str = str(self.data)
        
        # Handle multiline data (each line must be prefixed with "data: ")
        for line in data_str.split("\n"):
            lines.append(f"data: {line}")
        
        # End with an empty line to mark the end of the event
        lines.append("")
        
        return "\n".join(lines)
    
    @classmethod
    def create(cls, 
              data: Any, 
              event_type: Optional[str] = None,
              retry: Optional[int] = None,
              priority: EventPriority = EventPriority.NORMAL) -> "Event":
        """Create a new event.
        
        Args:
            data: The event data payload.
            event_type: The type of the event, defaults to "message".
            retry: Optional reconnection time in milliseconds.
            priority: Event priority, defaults to NORMAL.
            
        Returns:
            A new Event instance.
        """
        return cls(
            data=data,
            event=event_type or "message",
            retry=retry,
            priority=priority
        )


# Convenience functions for common event types

def create_data_event(resource: str, data: Any, 
                     priority: EventPriority = EventPriority.NORMAL) -> Event:
    """Create a data event.
    
    Args:
        resource: The resource the data belongs to.
        data: The data payload.
        priority: Event priority, defaults to NORMAL.
        
    Returns:
        A "data" Event instance.
    """
    return Event(
        data={
            "resource": resource,
            "data": data
        },
        event="data",
        priority=priority
    )


def create_notification_event(title: str, message: str, level: str = "info",
                            actions: Optional[List[Dict[str, Any]]] = None,
                            priority: EventPriority = EventPriority.HIGH) -> Event:
    """Create a notification event.
    
    Args:
        title: The notification title.
        message: The notification message.
        level: The notification level (info, warning, error, etc.).
        actions: Optional list of actions the user can take.
        priority: Event priority, defaults to HIGH.
        
    Returns:
        A "notification" Event instance.
    """
    return Event(
        data={
            "title": title,
            "message": message,
            "level": level,
            **({"actions": actions} if actions else {})
        },
        event="notification",
        priority=priority
    )


class KeepAliveEvent(Event):
    """Special event class for keep-alive comments."""
    
    def to_sse_format(self) -> str:
        """Override to provide a simple keepalive comment."""
        return ": keepalive\n"

def create_keep_alive_event() -> Event:
    """Create a keep-alive comment event.
    
    Returns:
        A comment-only Event with no data.
    """
    return KeepAliveEvent(data="", event=None)