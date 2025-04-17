from abc import ABC, abstractmethod
from typing import Dict, Callable, TypeVar, Generic, Optional
import logging
from logging import Logger

from uno.database.config import ConnectionConfig

# Type for connection callback functions
T = TypeVar("T")
C = TypeVar("C")  # Connection type
E = TypeVar("E")  # Engine type
ConnectionCallback = Callable[[C], None]


class EngineFactory(Generic[E, C], ABC):
    """Base class for engine factories."""

    def __init__(
        self,
        logger: Optional[Logger] = None,
        config: Optional[ConnectionConfig] = None,
    ):
        """Initialize the engine factory."""
        self.logger = logger or logging.getLogger(__name__)
        self.connection_callbacks: Dict[str, ConnectionCallback] = {}

    @abstractmethod
    def create_engine(self, config: ConnectionConfig) -> E:
        """Create an engine with the given configuration."""
        pass

    def register_callback(self, name: str, callback: ConnectionCallback) -> None:
        """Register a callback for new connections."""
        self.connection_callbacks[name] = callback

    def unregister_callback(self, name: str) -> None:
        """Unregister a connection callback."""
        if name in self.connection_callbacks:
            del self.connection_callbacks[name]

    def execute_callbacks(self, connection: C) -> None:
        """Execute all registered callbacks with the connection."""
        for name, callback in self.connection_callbacks.items():
            try:
                callback(connection)
            except Exception as e:
                self.logger.error(f"Error in connection callback '{name}': {e}")
