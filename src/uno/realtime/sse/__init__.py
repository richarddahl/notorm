"""Server-Sent Events (SSE) module for the Uno framework.

This module provides support for Server-Sent Events (SSE) for pushing real-time
updates to clients. SSE is a server push technology that allows a client to
receive automatic updates from a server via an HTTP connection.
"""

from uno.realtime.sse.connection import SSEConnection
from uno.realtime.sse.manager import SSEManager
from uno.realtime.sse.event import Event, EventPriority
from uno.realtime.sse.errors import SSEError, SSEErrorCode

__all__ = [
    'SSEConnection',
    'SSEManager',
    'Event',
    'EventPriority',
    'SSEError',
    'SSEErrorCode',
]