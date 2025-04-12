"""
Core protocol definitions for the Uno framework.

This module defines the core protocols used throughout the Uno framework,
providing a foundation for dependency injection and loose coupling.
"""

from typing import (
    Protocol, TypeVar, Generic, Any, Dict, List, Optional, 
    Callable, Awaitable, AsyncContextManager, Union, runtime_checkable,
    Type, Tuple, get_origin, get_args
)
from datetime import datetime
from uuid import UUID

# Type variables for generic protocols
T = TypeVar('T')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)
EntityT = TypeVar('EntityT')
EntityT_co = TypeVar('EntityT_co', covariant=True)
EntityT_contra = TypeVar('EntityT_contra', contravariant=True)
QueryT = TypeVar('QueryT')
QueryT_contra = TypeVar('QueryT_contra', contravariant=True)
ResultT = TypeVar('ResultT')
ResultT_co = TypeVar('ResultT_co', covariant=True)
KeyT = TypeVar('KeyT')
KeyT_co = TypeVar('KeyT_co', covariant=True)
KeyT_contra = TypeVar('KeyT_contra', contravariant=True)
ValueT = TypeVar('ValueT')
ValueT_co = TypeVar('ValueT_co', covariant=True)
ValueT_contra = TypeVar('ValueT_contra', contravariant=True)
EventT_co = TypeVar('EventT_co', covariant=True)
EventT_contra = TypeVar('EventT_contra', contravariant=True)
CommandT_co = TypeVar('CommandT_co', covariant=True)
CommandT_contra = TypeVar('CommandT_contra', contravariant=True)

# Type variables for repository pattern
FilterT = TypeVar('FilterT')
FilterT_contra = TypeVar('FilterT_contra', contravariant=True)
DataT = TypeVar('DataT', bound=Dict[str, Any])
DataT_contra = TypeVar('DataT_contra', bound=Dict[str, Any], contravariant=True)
MergeResultT = TypeVar('MergeResultT')
MergeResultT_co = TypeVar('MergeResultT_co', covariant=True)


# Core domain protocols
@runtime_checkable
class Entity(Protocol, Generic[KeyT_co]):
    """Protocol for domain entities with identity."""
    
    @property
    def id(self) -> KeyT_co:
        """Get the entity's unique identifier."""
        ...


@runtime_checkable
class AggregateRoot(Entity[KeyT_co], Protocol[KeyT_co]):
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
class EventHandler(Protocol[EventT_contra]):
    """Protocol for event handlers."""
    
    async def handle(self, event: EventT_contra) -> None:
        """Handle an event."""
        ...


@runtime_checkable
class EventBus(Protocol):
    """Protocol for the event bus."""
    
    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to the event bus."""
        ...
    
    def subscribe(self, event_type: Type[Any], handler: EventHandler[Any]) -> None:
        """Subscribe a handler to an event type."""
        ...
    
    def unsubscribe(self, event_type: Type[Any], handler: EventHandler[Any]) -> None:
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
class CommandHandler(Protocol[CommandT_contra, ResultT_co]):
    """Protocol for command handlers in the CQRS pattern."""
    
    async def handle(self, command: CommandT_contra) -> ResultT_co:
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
class QueryHandler(Protocol[QueryT_contra, ResultT_co]):
    """Protocol for query handlers in the CQRS pattern."""
    
    async def handle(self, query: QueryT_contra) -> ResultT_co:
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


# Remove these duplicated type variables as they're now defined at the top
# (The actual type variables are now defined at the top of the file)

@runtime_checkable
class DatabaseRepository(Protocol[EntityT, KeyT, FilterT, DataT, MergeResultT]):
    """
    Protocol for database repositories.
    
    Type Parameters:
        EntityT: Type of entity managed by this repository
        KeyT: Type of entity key/identifier
        FilterT: Type of filter criteria
        DataT: Type of data for merge operations
        MergeResultT: Type of result from merge operations
    """
    
    @classmethod
    async def get(cls, **kwargs: Any) -> Optional[EntityT]:
        """
        Get an entity by keyword arguments.
        
        Args:
            **kwargs: Key-value pairs for lookup conditions
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    @classmethod
    async def create(cls, entity: EntityT) -> Tuple[EntityT, bool]:
        """
        Create a new entity.
        
        Args:
            entity: The entity to create
            
        Returns:
            Tuple of (created entity, success flag)
        """
        ...
    
    @classmethod
    async def update(cls, entity: EntityT, **kwargs: Any) -> EntityT:
        """
        Update an existing entity.
        
        Args:
            entity: The entity with updated values
            **kwargs: Key-value pairs for lookup conditions
            
        Returns:
            The updated entity
        """
        ...
    
    @classmethod
    async def delete(cls, **kwargs: Any) -> bool:
        """
        Delete an entity by keyword arguments.
        
        Args:
            **kwargs: Key-value pairs for lookup conditions
            
        Returns:
            True if deletion was successful, False otherwise
        """
        ...
    
    @classmethod
    async def filter(cls, filters: Optional[FilterT] = None) -> List[EntityT]:
        """
        Filter entities by criteria.
        
        Args:
            filters: Filter criteria
            
        Returns:
            List of entities matching the criteria
        """
        ...
    
    @classmethod
    async def merge(cls, data: DataT) -> MergeResultT:
        """
        Merge data into an entity.
        
        Args:
            data: Data to merge
            
        Returns:
            Result of the merge operation
        """
        ...


# Type variables for unit of work pattern
RepoT = TypeVar('RepoT')
RepoKeyT = TypeVar('RepoKeyT', bound=Type[Any])

@runtime_checkable
class UnitOfWork(Protocol[RepoT, RepoKeyT]):
    """
    Protocol for the unit of work pattern.
    
    Type Parameters:
        RepoT: Type of repositories managed by this unit of work
        RepoKeyT: Type of repository keys/identifiers (typically Type[Repository])
    """
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        ...
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...
    
    def get_repository(self, repository_type: RepoKeyT) -> RepoT:
        """
        Get a repository of the specified type.
        
        Args:
            repository_type: Type of repository to get
            
        Returns:
            Repository instance
        """
        ...
    
    async def __aenter__(self) -> 'UnitOfWork[RepoT, RepoKeyT]':
        """Enter the unit of work context."""
        ...
    
    async def __aexit__(self, 
                      exc_type: Optional[Type[BaseException]], 
                      exc_val: Optional[BaseException], 
                      exc_tb: Optional[Any]) -> None:
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
TTLT = TypeVar('TTLT', int, float)
TTLT_contra = TypeVar('TTLT_contra', int, float, contravariant=True)
PrefixT = TypeVar('PrefixT', bound=str)
PrefixT_contra = TypeVar('PrefixT_contra', bound=str, contravariant=True)

@runtime_checkable
class Cache(Protocol[KeyT, ValueT, TTLT, PrefixT]):
    """
    Protocol for cache implementations.
    
    Type Parameters:
        KeyT: Type of cache keys
        ValueT: Type of cache values
        TTLT: Type of time-to-live value (int or float)
        PrefixT: Type of cache key prefix (string)
    """
    
    async def get(self, key: KeyT) -> Optional[ValueT]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            The cached value if found, None otherwise
        """
        ...
    
    async def set(self, key: KeyT, value: ValueT, ttl: Optional[TTLT] = None) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional time-to-live in seconds
        """
        ...
    
    async def delete(self, key: KeyT) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key to delete
        """
        ...
    
    async def clear(self) -> None:
        """Clear the entire cache."""
        ...
    
    async def get_many(self, keys: List[KeyT]) -> Dict[KeyT, ValueT]:
        """
        Get multiple values from the cache.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dictionary mapping keys to cached values (missing keys are omitted)
        """
        ...
    
    async def set_many(self, items: Dict[KeyT, ValueT], ttl: Optional[TTLT] = None) -> None:
        """
        Set multiple values in the cache.
        
        Args:
            items: Dictionary of key-value pairs to cache
            ttl: Optional time-to-live in seconds
        """
        ...
    
    async def delete_many(self, keys: List[KeyT]) -> None:
        """
        Delete multiple values from the cache.
        
        Args:
            keys: List of cache keys to delete
        """
        ...
    
    async def delete_by_prefix(self, prefix: PrefixT) -> None:
        """
        Delete all keys with the given prefix.
        
        Args:
            prefix: Key prefix to match
        """
        ...


# Configuration
# Using the already defined KeyT_contra and ValueT_co from above
ConfigKeyT = TypeVar('ConfigKeyT', bound=str, contravariant=True)
SectionT = TypeVar('SectionT', bound=str)
SectionT_contra = TypeVar('SectionT_contra', bound=str, contravariant=True)
DefaultT = TypeVar('DefaultT')
DefaultT_contra = TypeVar('DefaultT_contra', contravariant=True)

@runtime_checkable
class ConfigProvider(Protocol[ConfigKeyT, ValueT, SectionT, DefaultT]):
    """
    Protocol for configuration providers.
    
    Type Parameters:
        ConfigKeyT: Type of configuration keys
        ValueT: Type of configuration values
        SectionT: Type of section identifiers
        DefaultT: Type of default values
    """
    
    def get(self, key: ConfigKeyT, default: Optional[DefaultT] = None) -> Union[ValueT, DefaultT]:
        """
        Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value to return if key is not found
            
        Returns:
            The configuration value or the default
        """
        ...
    
    def get_section(self, section: SectionT) -> Dict[str, ValueT]:
        """
        Get a configuration section.
        
        Args:
            section: Section identifier
            
        Returns:
            Dictionary containing all configuration values in the section
        """
        ...
    
    def reload(self) -> None:
        """Reload the configuration from its source."""
        ...
    
    def get_bool(self, key: ConfigKeyT, default: Optional[bool] = None) -> bool:
        """
        Get a boolean configuration value.
        
        Args:
            key: Configuration key
            default: Default boolean value
            
        Returns:
            The boolean configuration value or the default
        """
        ...
    
    def get_int(self, key: ConfigKeyT, default: Optional[int] = None) -> int:
        """
        Get an integer configuration value.
        
        Args:
            key: Configuration key
            default: Default integer value
            
        Returns:
            The integer configuration value or the default
        """
        ...
    
    def get_float(self, key: ConfigKeyT, default: Optional[float] = None) -> float:
        """
        Get a float configuration value.
        
        Args:
            key: Configuration key
            default: Default float value
            
        Returns:
            The float configuration value or the default
        """
        ...
    
    def get_list(self, key: ConfigKeyT, default: Optional[List[Any]] = None) -> List[Any]:
        """
        Get a list configuration value.
        
        Args:
            key: Configuration key
            default: Default list value
            
        Returns:
            The list configuration value or the default
        """
        ...


# Type variables for database protocols
ConfigT = TypeVar('ConfigT')
ConfigT_contra = TypeVar('ConfigT_contra', contravariant=True)
StatementT = TypeVar('StatementT')
StatementT_contra = TypeVar('StatementT_contra', contravariant=True)
DbResultT_co = TypeVar('DbResultT_co', covariant=True)
ModelT = TypeVar('ModelT')
ModelT_contra = TypeVar('ModelT_contra', contravariant=True)

# Database protocols
@runtime_checkable
class DatabaseSessionProtocol(Protocol[StatementT_contra, DbResultT_co, ModelT_contra]):
    """
    Protocol for database sessions.
    
    Type Parameters:
        StatementT_contra: Type of statement (e.g., SQLAlchemy statement) (contravariant)
        DbResultT_co: Type of result from statement execution (covariant)
        ModelT_contra: Type of model/entity instances (contravariant)
    """
    
    async def execute(self, statement: StatementT_contra, *args: Any, **kwargs: Any) -> DbResultT_co:
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
    
    def add(self, instance: ModelT_contra) -> None:
        """Add an instance to the session."""
        ...


@runtime_checkable
class DatabaseSessionFactoryProtocol(Protocol[ConfigT_contra, StatementT_contra, DbResultT_co, ModelT_contra]):
    """
    Protocol for session factories.
    
    Type Parameters:
        ConfigT_contra: Type of configuration object (contravariant)
        StatementT_contra: Type of statement (e.g., SQLAlchemy statement) (contravariant)
        DbResultT_co: Type of result from statement execution (covariant)
        ModelT_contra: Type of model/entity instances (contravariant)
    """
    
    def create_session(self, config: ConfigT_contra) -> DatabaseSessionProtocol[StatementT_contra, DbResultT_co, ModelT_contra]:
        """Create a database session."""
        ...
    
    def get_scoped_session(self, config: ConfigT_contra) -> Any:
        """Get a scoped session."""
        ...
    
    async def remove_all_scoped_sessions(self) -> None:
        """Remove all scoped sessions."""
        ...


@runtime_checkable
class DatabaseSessionContextProtocol(Protocol[StatementT_contra, DbResultT_co, ModelT_contra]):
    """
    Protocol for database session context managers.
    
    Type Parameters:
        StatementT_contra: Type of statement (e.g., SQLAlchemy statement) (contravariant)
        DbResultT_co: Type of result from statement execution (covariant)
        ModelT_contra: Type of model/entity instances (contravariant)
    """
    
    async def __aenter__(self) -> DatabaseSessionProtocol[StatementT_contra, DbResultT_co, ModelT_contra]:
        """Enter the context manager."""
        ...
    
    async def __aexit__(self, exc_type: Optional[Type[BaseException]], 
                       exc_val: Optional[BaseException], 
                       exc_tb: Optional[Any]) -> None:
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
MessageT = TypeVar('MessageT')
MessageT_contra = TypeVar('MessageT_contra', contravariant=True)
MessageT_co = TypeVar('MessageT_co', covariant=True)

@runtime_checkable
class MessagePublisher(Protocol[MessageT_contra]):
    """Protocol for message publishers."""
    
    async def publish(self, topic: str, message: MessageT_contra) -> None:
        """Publish a message to a topic."""
        ...


@runtime_checkable
class MessageConsumer(Protocol[MessageT_co]):
    """Protocol for message consumers."""
    
    async def subscribe(self, topic: str, handler: Callable[[MessageT_co], Awaitable[None]]) -> None:
        """Subscribe to a topic."""
        ...
    
    async def unsubscribe(self, topic: str, handler: Callable[[MessageT_co], Awaitable[None]]) -> None:
        """Unsubscribe from a topic."""
        ...
    
    async def start(self) -> None:
        """Start consuming messages."""
        ...
    
    async def stop(self) -> None:
        """Stop consuming messages."""
        ...


# Plugin architecture
PluginContextT = TypeVar('PluginContextT')
PluginContextT_contra = TypeVar('PluginContextT_contra', contravariant=True)
PluginConfigT = TypeVar('PluginConfigT')
PluginConfigT_contra = TypeVar('PluginConfigT_contra', contravariant=True)
PluginEventT = TypeVar('PluginEventT')
PluginEventT_contra = TypeVar('PluginEventT_contra', contravariant=True)
PluginNameT = TypeVar('PluginNameT', bound=str)
PluginNameT_co = TypeVar('PluginNameT_co', bound=str, covariant=True)
PluginNameT_contra = TypeVar('PluginNameT_contra', bound=str, contravariant=True)
PluginVersionT = TypeVar('PluginVersionT', bound=str)
PluginVersionT_co = TypeVar('PluginVersionT_co', bound=str, covariant=True)

@runtime_checkable
class Plugin(Protocol[PluginContextT, PluginConfigT, PluginEventT, PluginNameT, PluginVersionT]):
    """
    Protocol for plugins.
    
    Type Parameters:
        PluginContextT: Type of plugin context
        PluginConfigT: Type of plugin configuration
        PluginEventT: Type of events the plugin handles
        PluginNameT: Type of plugin name (bound to str)
        PluginVersionT: Type of plugin version (bound to str)
    """
    
    @property
    def name(self) -> PluginNameT:
        """Get the name of the plugin."""
        ...
    
    @property
    def version(self) -> PluginVersionT:
        """Get the version of the plugin."""
        ...
    
    @property
    def description(self) -> str:
        """Get the description of the plugin."""
        ...
    
    @property
    def dependencies(self) -> List[PluginNameT]:
        """Get the dependencies of the plugin."""
        ...
    
    async def initialize(self, context: PluginContextT) -> None:
        """
        Initialize the plugin.
        
        Args:
            context: The plugin context
        """
        ...
    
    async def shutdown(self) -> None:
        """Shut down the plugin."""
        ...
    
    async def configure(self, config: PluginConfigT) -> None:
        """
        Configure the plugin.
        
        Args:
            config: The plugin configuration
        """
        ...
    
    async def on_event(self, event: PluginEventT) -> None:
        """
        Handle an event.
        
        Args:
            event: The event to handle
        """
        ...


@runtime_checkable
class PluginManager(Protocol[PluginContextT, PluginNameT]):
    """
    Protocol for plugin managers.
    
    Type Parameters:
        PluginContextT: Type of plugin context
        PluginNameT: Type of plugin name (bound to str)
    """
    
    def register_plugin(self, plugin: Plugin[PluginContextT, Any, Any, PluginNameT, Any]) -> None:
        """
        Register a plugin.
        
        Args:
            plugin: The plugin to register
        """
        ...
    
    def unregister_plugin(self, plugin_name: PluginNameT) -> None:
        """
        Unregister a plugin.
        
        Args:
            plugin_name: The name of the plugin to unregister
        """
        ...
    
    def get_plugin(self, plugin_name: PluginNameT) -> Optional[Plugin[PluginContextT, Any, Any, PluginNameT, Any]]:
        """
        Get a plugin by name.
        
        Args:
            plugin_name: The name of the plugin to get
            
        Returns:
            The plugin if found, None otherwise
        """
        ...
    
    def list_plugins(self) -> List[Plugin[PluginContextT, Any, Any, PluginNameT, Any]]:
        """
        List all registered plugins.
        
        Returns:
            List of registered plugins
        """
        ...
    
    async def initialize_all(self, context: PluginContextT) -> None:
        """
        Initialize all registered plugins.
        
        Args:
            context: The plugin context
        """
        ...
    
    async def shutdown_all(self) -> None:
        """Shut down all registered plugins."""
        ...
    
    async def send_event(self, event: Any) -> None:
        """
        Send an event to all plugins.
        
        Args:
            event: The event to send
        """
        ...


# Health checks
HealthStatusT = TypeVar('HealthStatusT')
HealthStatusT_co = TypeVar('HealthStatusT_co', covariant=True)
HealthDetailsT = TypeVar('HealthDetailsT')
HealthDetailsT_co = TypeVar('HealthDetailsT_co', covariant=True)
HealthComponentT = TypeVar('HealthComponentT', bound=str)
HealthComponentT_co = TypeVar('HealthComponentT_co', bound=str, covariant=True)

@runtime_checkable
class HealthCheck(Protocol[HealthStatusT, HealthDetailsT, HealthComponentT]):
    """
    Protocol for health checks.
    
    Type Parameters:
        HealthStatusT: Type of health status (typically bool or enum)
        HealthDetailsT: Type of health check details
        HealthComponentT: Type of component name (bound to str)
    """
    
    @property
    def name(self) -> HealthComponentT:
        """Get the name of the health check."""
        ...
    
    @property
    def description(self) -> str:
        """Get the description of the health check."""
        ...
    
    @property
    def is_critical(self) -> bool:
        """Determine if this health check is critical for system operation."""
        ...
    
    async def check(self) -> Tuple[HealthStatusT, Optional[HealthDetailsT]]:
        """
        Perform the health check.
        
        Returns:
            Tuple of (status, details) where details may be None
        """
        ...


@runtime_checkable
class HealthCheckRegistry(Protocol[HealthStatusT, HealthDetailsT, HealthComponentT]):
    """
    Protocol for health check registries.
    
    Type Parameters:
        HealthStatusT: Type of health status (typically bool or enum)
        HealthDetailsT: Type of health check details
        HealthComponentT: Type of component name (bound to str)
    """
    
    def register(self, health_check: HealthCheck[HealthStatusT, HealthDetailsT, HealthComponentT]) -> None:
        """
        Register a health check.
        
        Args:
            health_check: The health check to register
        """
        ...
    
    def unregister(self, name: HealthComponentT) -> None:
        """
        Unregister a health check.
        
        Args:
            name: The name of the health check to unregister
        """
        ...
    
    async def check_all(self) -> Dict[HealthComponentT, Tuple[HealthStatusT, Optional[HealthDetailsT]]]:
        """
        Check all registered health checks.
        
        Returns:
            Dictionary mapping component names to (status, details) tuples
        """
        ...
    
    async def check_critical(self) -> Dict[HealthComponentT, Tuple[HealthStatusT, Optional[HealthDetailsT]]]:
        """
        Check only critical health checks.
        
        Returns:
            Dictionary mapping critical component names to (status, details) tuples
        """
        ...