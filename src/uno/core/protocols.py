"""
Core protocol definitions for the Uno framework.

This module defines the core protocols used throughout the Uno framework,
providing a foundation for dependency injection and loose coupling.
"""

from typing import (
    Protocol, TypeVar, Generic, Any, Dict, List, Optional, 
    Callable, Awaitable, AsyncContextManager, Union, runtime_checkable
)
from datetime import datetime
from uuid import UUID

# Type variables for generic protocols
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
EntityT = TypeVar('EntityT')
QueryT = TypeVar('QueryT')
ResultT = TypeVar('ResultT')
KeyT = TypeVar('KeyT')
ValueT = TypeVar('ValueT')
EventT = TypeVar('EventT')
CommandT = TypeVar('CommandT')


# Core domain protocols
@runtime_checkable
class Entity(Protocol, Generic[KeyT]):
    """Protocol for domain entities with identity."""
    
    @property
    def id(self) -> KeyT:
        """Get the entity's unique identifier."""
        ...


@runtime_checkable
class AggregateRoot(Entity[KeyT], Protocol[KeyT]):
    """Protocol for aggregate roots in the domain."""
    
    def register_event(self, event: 'DomainEvent') -> None:
        """Register a domain event to be published after the aggregate is saved."""
        ...
    
    def clear_events(self) -> List['DomainEvent']:
        """Clear and return all registered events."""
        ...


@runtime_checkable
class ValueObject(Protocol):
    """Protocol for value objects in the domain."""
    
    def equals(self, other: Any) -> bool:
        """Check if this value object equals another."""
        ...


# Event-driven architecture protocols
@runtime_checkable
class DomainEvent(Protocol):
    """Protocol for domain events."""
    
    @property
    def event_id(self) -> UUID:
        """Get the unique identifier for this event."""
        ...
    
    @property
    def event_type(self) -> str:
        """Get the type of this event."""
        ...
    
    @property
    def aggregate_id(self) -> Any:
        """Get the identifier of the aggregate that raised this event."""
        ...
    
    @property
    def timestamp(self) -> datetime:
        """Get the timestamp when this event occurred."""
        ...
    
    @property
    def data(self) -> Dict[str, Any]:
        """Get the event data."""
        ...


@runtime_checkable
class EventHandler(Protocol[EventT]):
    """Protocol for event handlers."""
    
    async def handle(self, event: EventT) -> None:
        """Handle an event."""
        ...


@runtime_checkable
class EventBus(Protocol):
    """Protocol for the event bus."""
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to the event bus."""
        ...
    
    def subscribe(self, event_type: str, handler: EventHandler[Any]) -> None:
        """Subscribe a handler to an event type."""
        ...
    
    def unsubscribe(self, event_type: str, handler: EventHandler[Any]) -> None:
        """Unsubscribe a handler from an event type."""
        ...


# CQRS patterns
@runtime_checkable
class Command(Protocol):
    """Protocol for commands in the CQRS pattern."""
    
    @property
    def command_id(self) -> UUID:
        """Get the unique identifier for this command."""
        ...
    
    @property
    def command_type(self) -> str:
        """Get the type of this command."""
        ...


@runtime_checkable
class CommandHandler(Protocol[CommandT, ResultT]):
    """Protocol for command handlers in the CQRS pattern."""
    
    async def handle(self, command: CommandT) -> ResultT:
        """Handle a command."""
        ...


@runtime_checkable
class Query(Protocol):
    """Protocol for queries in the CQRS pattern."""
    
    @property
    def query_id(self) -> UUID:
        """Get the unique identifier for this query."""
        ...
    
    @property
    def query_type(self) -> str:
        """Get the type of this query."""
        ...


@runtime_checkable
class QueryHandler(Protocol[QueryT, ResultT]):
    """Protocol for query handlers in the CQRS pattern."""
    
    async def handle(self, query: QueryT) -> ResultT:
        """Handle a query."""
        ...


# Repository pattern
@runtime_checkable
class Repository(Protocol[EntityT, KeyT]):
    """Protocol for repositories."""
    
    async def get(self, id: KeyT) -> Optional[EntityT]:
        """Get an entity by its ID."""
        ...
    
    async def save(self, entity: EntityT) -> None:
        """Save an entity."""
        ...
    
    async def delete(self, id: KeyT) -> bool:
        """Delete an entity by its ID."""
        ...


@runtime_checkable
class DatabaseRepository(Protocol[EntityT, KeyT]):
    """Protocol for database repositories."""
    
    @classmethod
    async def get(cls, **kwargs: Any) -> Optional[EntityT]:
        """Get an entity by keyword arguments."""
        ...
    
    @classmethod
    async def create(cls, entity: EntityT) -> tuple[EntityT, bool]:
        """Create a new entity."""
        ...
    
    @classmethod
    async def update(cls, entity: EntityT, **kwargs: Any) -> EntityT:
        """Update an existing entity."""
        ...
    
    @classmethod
    async def delete(cls, **kwargs: Any) -> bool:
        """Delete an entity by keyword arguments."""
        ...
    
    @classmethod
    async def filter(cls, filters: Any = None) -> list[EntityT]:
        """Filter entities by criteria."""
        ...
    
    @classmethod
    async def merge(cls, data: dict) -> Any:
        """Merge data into an entity."""
        ...


@runtime_checkable
class UnitOfWork(Protocol):
    """Protocol for the unit of work pattern."""
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        ...
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
    
    def get_repository(self, repository_type: type) -> Any:
        """Get a repository."""
        ...
    
    async def __aenter__(self) -> 'UnitOfWork':
        """Enter the unit of work context."""
        ...
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the unit of work context."""
        ...


# Error handling
@runtime_checkable
class Result(Protocol[T_co]):
    """Protocol for the Result pattern (Either pattern)."""
    
    @property
    def is_success(self) -> bool:
        """Check if the result is successful."""
        ...
    
    @property
    def is_failure(self) -> bool:
        """Check if the result is a failure."""
        ...
    
    @property
    def error(self) -> Optional[Exception]:
        """Get the error if the result is a failure."""
        ...
    
    @property
    def value(self) -> Optional[T_co]:
        """Get the value if the result is successful."""
        ...


# Caching
@runtime_checkable
class Cache(Protocol[KeyT, ValueT]):
    """Protocol for cache implementations."""
    
    async def get(self, key: KeyT) -> Optional[ValueT]:
        """Get a value from the cache."""
        ...
    
    async def set(self, key: KeyT, value: ValueT, ttl: Optional[int] = None) -> None:
        """Set a value in the cache."""
        ...
    
    async def delete(self, key: KeyT) -> None:
        """Delete a value from the cache."""
        ...
    
    async def clear(self) -> None:
        """Clear the cache."""
        ...


# Configuration
@runtime_checkable
class ConfigProvider(Protocol):
    """Protocol for configuration providers."""
    
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value."""
        ...
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a configuration section."""
        ...
    
    def reload(self) -> None:
        """Reload the configuration."""
        ...


# Database protocols
@runtime_checkable
class DatabaseSessionProtocol(Protocol):
    """Protocol for database sessions."""
    
    async def execute(self, statement: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a statement."""
        ...
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
    
    async def close(self) -> None:
        """Close the session."""
        ...
    
    def add(self, instance: Any) -> None:
        """Add an instance to the session."""
        ...


@runtime_checkable
class DatabaseSessionFactoryProtocol(Protocol):
    """Protocol for session factories."""
    
    def create_session(self, config: Any) -> DatabaseSessionProtocol:
        """Create a database session."""
        ...
    
    def get_scoped_session(self, config: Any) -> Any:
        """Get a scoped session."""
        ...
    
    async def remove_all_scoped_sessions(self) -> None:
        """Remove all scoped sessions."""
        ...


@runtime_checkable
class DatabaseSessionContextProtocol(Protocol):
    """Protocol for database session context managers."""
    
    async def __aenter__(self) -> DatabaseSessionProtocol:
        """Enter the context manager."""
        ...
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager."""
        ...


# Resource management
@runtime_checkable
class ResourceManager(Protocol[T]):
    """Protocol for resource managers."""
    
    async def acquire(self) -> T:
        """Acquire a resource."""
        ...
    
    async def release(self, resource: T) -> None:
        """Release a resource."""
        ...
    
    async def close(self) -> None:
        """Close the resource manager."""
        ...
    
    def contextual(self) -> AsyncContextManager[T]:
        """Get a context manager for this resource."""
        ...


# Messaging
@runtime_checkable
class MessagePublisher(Protocol[T]):
    """Protocol for message publishers."""
    
    async def publish(self, topic: str, message: T) -> None:
        """Publish a message to a topic."""
        ...


@runtime_checkable
class MessageConsumer(Protocol[T]):
    """Protocol for message consumers."""
    
    async def subscribe(self, topic: str, handler: Callable[[T], Awaitable[None]]) -> None:
        """Subscribe to a topic."""
        ...
    
    async def unsubscribe(self, topic: str, handler: Callable[[T], Awaitable[None]]) -> None:
        """Unsubscribe from a topic."""
        ...
    
    async def start(self) -> None:
        """Start consuming messages."""
        ...
    
    async def stop(self) -> None:
        """Stop consuming messages."""
        ...


# Plugin architecture
@runtime_checkable
class Plugin(Protocol):
    """Protocol for plugins."""
    
    @property
    def name(self) -> str:
        """Get the name of the plugin."""
        ...
    
    @property
    def version(self) -> str:
        """Get the version of the plugin."""
        ...
    
    async def initialize(self) -> None:
        """Initialize the plugin."""
        ...
    
    async def shutdown(self) -> None:
        """Shut down the plugin."""
        ...


@runtime_checkable
class PluginManager(Protocol):
    """Protocol for plugin managers."""
    
    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin."""
        ...
    
    def unregister_plugin(self, plugin_name: str) -> None:
        """Unregister a plugin."""
        ...
    
    def get_plugin(self, plugin_name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        ...
    
    async def initialize_all(self) -> None:
        """Initialize all registered plugins."""
        ...
    
    async def shutdown_all(self) -> None:
        """Shut down all registered plugins."""
        ...


# Health checks
@runtime_checkable
class HealthCheck(Protocol):
    """Protocol for health checks."""
    
    @property
    def name(self) -> str:
        """Get the name of the health check."""
        ...
    
    async def check(self) -> bool:
        """Perform the health check."""
        ...


@runtime_checkable
class HealthCheckRegistry(Protocol):
    """Protocol for health check registries."""
    
    def register(self, health_check: HealthCheck) -> None:
        """Register a health check."""
        ...
    
    def unregister(self, name: str) -> None:
        """Unregister a health check."""
        ...
    
    async def check_all(self) -> Dict[str, bool]:
        """Check all registered health checks."""
        ...