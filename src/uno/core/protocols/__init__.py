# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the Uno framework.

This module contains protocol definitions for components used throughout the framework.
Protocols provide interface definitions that help break circular dependencies
and improve code organization.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    Set,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
    Tuple,
    Generic,
    TypedDict,
    NotRequired,
    Literal,
    TypeGuard,
)
from types import TracebackType
import asyncio
from datetime import datetime
from pydantic import BaseModel

# Type variables
ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T", covariant=True)
Self = TypeVar("Self")

# Import other protocol types
from uno.core.protocols.filter_protocols import UnoFilterProtocol

# Define core protocols directly to avoid circular imports


@runtime_checkable
class ConfigProvider(Protocol):
    """
    Protocol for configuration providers.

    Configuration providers are responsible for managing application
    settings and configuration values.
    """

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.

        Args:
            key: The configuration key
            default: Default value if the key is not found

        Returns:
            The configuration value
        """
        ...

    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.

        Args:
            key: The configuration key
            value: The value to set
        """
        ...

    def load(self, path: str) -> None:
        """
        Load configuration from a path.

        Args:
            path: The path to load configuration from
        """
        ...

    def reload(self) -> None:
        """Reload the configuration."""
        ...


# Domain model protocols
@runtime_checkable
class Entity(Protocol):
    """
    Protocol for entities in the domain model.

    Entities are objects that have a distinct identity that runs through time
    and different representations. They are defined by their identity, not by
    their attributes.
    """

    id: Any
    created_at: datetime
    updated_at: datetime | None

    def __eq__(self, other: object) -> bool:
        """Compare entities by identity."""
        ...

    def __hash__(self) -> int:
        """Hash entities by identity."""
        ...


@runtime_checkable
class ValueObject(Protocol):
    """
    Protocol for value objects in the domain model.

    Value objects are immutable objects that describe aspects of the domain.
    They have no identity and are defined by their attributes.
    """

    def equals(self, other: Any) -> bool:
        """
        Check if this value object equals another.

        Args:
            other: Value object to compare with

        Returns:
            True if equal, False otherwise
        """
        ...

    def __eq__(self, other: object) -> bool:
        """Compare value objects by attributes."""
        ...

    def __hash__(self) -> int:
        """Hash value objects by attributes."""
        ...


@runtime_checkable
class UnoEvent(Protocol):
    """
    Protocol for domain events.

    Domain events represent something that happened in the domain that
    domain experts care about. They are immutable and named in the past tense.
    """

    event_id: str
    event_type: str
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert event to dictionary representation.

        Returns:
            Dictionary representation of the event
        """
        ...

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Self:
        """
        Create event from dictionary representation.

        Args:
            data: Dictionary representation of the event

        Returns:
            Event instance
        """
        ...


@runtime_checkable
class AggregateRoot(Entity, Protocol):
    """
    Protocol for aggregate roots in the domain model.

    Aggregate roots are the entry point to an aggregate - a cluster of domain objects
    that can be treated as a single unit. They ensure consistency within the aggregate
    and handle domain events.
    """

    @property
    def events(self) -> List[UnoEvent]:
        """Get the domain events raised by this aggregate."""
        ...

    def add_event(self, event: UnoEvent) -> None:
        """
        Add a domain event to this aggregate.

        Args:
            event: The domain event to add
        """
        ...

    def clear_events(self) -> List[UnoEvent]:
        """
        Clear all domain events from this aggregate.

        Returns:
            The list of events that were cleared
        """
        ...


# Repository Protocols
T_Entity = TypeVar("T_Entity")
T_ID = TypeVar("T_ID")


class Repository(Protocol, Generic[T_Entity, T_ID]):
    """
    Protocol for repositories in the domain model.

    Repositories mediate between the domain and data mapping layers,
    providing collection-like access to aggregates.

    Type Parameters:
        T_Entity: The type of entity this repository manages
        T_ID: The type of entity identifier
    """

    async def get_by_id(self, id: T_ID) -> T_Entity | None:
        """
        Get an entity by its identifier.

        Args:
            id: The entity identifier

        Returns:
            The entity if found, None otherwise
        """
        ...

    async def list(
        self,
        filters: Dict[str, Any] | None = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> List[T_Entity]:
        """
        List entities based on filters and options.

        Args:
            filters: Optional filter criteria
            options: Optional listing options (limit, offset, ordering)

        Returns:
            List of matching entities
        """
        ...

    async def add(self, entity: T_Entity) -> T_Entity:
        """
        Add an entity to the repository.

        Args:
            entity: The entity to add

        Returns:
            The added entity (with generated ID if applicable)
        """
        ...

    async def update(self, entity: T_Entity) -> T_Entity:
        """
        Update an entity in the repository.

        Args:
            entity: The entity to update

        Returns:
            The updated entity
        """
        ...

    async def delete(self, id: T_ID) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            id: The entity identifier

        Returns:
            True if the entity was deleted, False otherwise
        """
        ...


# Unit of Work Protocol
class UnitOfWork(Protocol):
    """
    Protocol for the Unit of Work pattern.

    The Unit of Work maintains a list of objects affected by a business transaction
    and coordinates the writing out of changes and the resolution of concurrency problems.
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

    async def __aenter__(self) -> Self:
        """Enter the Unit of Work context."""
        ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        """Exit the Unit of Work context."""
        ...


# Command and Query Protocols
T_Result = TypeVar("T_Result")


# Command and Query Protocols removed


# Event System Protocols
T_Event = TypeVar("T_Event")


class EventHandler(Protocol, Generic[T_Event]):
    """
    Protocol for event handlers.

    Event handlers process events and perform actions in response.

    Type Parameters:
        T_Event: The type of event this handler processes
    """

    async def handle(self, event: T_Event) -> None:
        """
        Handle an event.

        Args:
            event: The event to handle
        """
        ...


class EventBus(Protocol):
    """
    Protocol for event buses.

    Event buses distribute events to interested handlers.
    """

    def subscribe(self, event_type: Type[Any], handler: EventHandler[Any]) -> None:
        """
        Subscribe a handler to events of a specific type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when events occur
        """
        ...

    def unsubscribe(self, event_type: Type[Any], handler: EventHandler[Any]) -> None:
        """
        Unsubscribe a handler from events of a specific type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        ...

    async def publish(self, event: Any) -> None:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: The event to publish
        """
        ...


# Dependency Injection Protocols
class ServiceProvider(Protocol):
    """
    Protocol for service providers.

    Service providers resolve and manage services in the application.
    """

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service of the specified type.

        Args:
            service_type: The type of service to get

        Returns:
            Instance of the requested service
        """
        ...

    def register_singleton(
        self, service_type: Type[T], implementation: Type[T] | T | None = None
    ) -> None:
        """
        Register a singleton service.

        Args:
            service_type: The type of service to register
            implementation: The implementation or instance to use
        """
        ...

    def register_scoped(
        self, service_type: Type[T], implementation: Type[T] | None = None
    ) -> None:
        """
        Register a scoped service.

        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        ...

    def register_transient(
        self, service_type: Type[T], implementation: Type[T] | None = None
    ) -> None:
        """
        Register a transient service.

        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        ...

    def create_scope(self) -> "ServiceScope":
        """
        Create a new service scope.

        Returns:
            The new service scope
        """
        ...


class ServiceScope(Protocol):
    """
    Protocol for service scopes.

    Service scopes provide a context for resolving scoped services.
    """

    def get_service(self, service_type: Type[T]) -> T:
        """
        Get a service of the specified type.

        Args:
            service_type: The type of service to get

        Returns:
            Instance of the requested service
        """
        ...

    def dispose(self) -> None:
        """Dispose of the scope and its services."""
        ...

    def __enter__(self) -> Self:
        """Enter the scope context."""
        ...

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        """Exit the scope context."""
        ...


# Lifecycle Protocols
class Initializable(Protocol):
    """
    Protocol for services that need initialization.

    Initializable services can perform asynchronous setup operations.
    """

    async def initialize(self) -> None:
        """Initialize the service."""
        ...


class Disposable(Protocol):
    """
    Protocol for services that need cleanup.

    Disposable services can perform cleanup operations.
    """

    def dispose(self) -> None:
        """Dispose of the service's resources."""
        ...


class AsyncDisposable(Protocol):
    """
    Protocol for services that need asynchronous cleanup.

    AsyncDisposable services can perform asynchronous cleanup operations.
    """

    async def dispose_async(self) -> None:
        """Dispose of the service's resources asynchronously."""
        ...


# Error Handling Protocols
T_Success = TypeVar("T_Success")
T_Error = TypeVar("T_Error")


class Result(Protocol, Generic[T_Success, T_Error]):
    """
    Protocol for the Result pattern.

    Results represent the outcome of an operation that can either succeed with a value
    or fail with an error.

    Type Parameters:
        T_Success: The type of successful result
        T_Error: The type of error result
    """

    @property
    def is_success(self) -> bool:
        """Whether the result is successful."""
        ...

    @property
    def is_failure(self) -> bool:
        """Whether the result is a failure."""
        ...

    @property
    def value(self) -> T_Success | None:
        """The success value, or None if failure."""
        ...

    @property
    def error(self) -> T_Error | None:
        """The error value, or None if success."""
        ...


# Logging Protocols
class Logger(Protocol):
    """
    Protocol for loggers.

    Loggers provide a consistent interface for logging messages.
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log a critical message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...


# Monitoring Protocols
class Metric(Protocol):
    """
    Protocol for metrics.

    Metrics provide a way to measure and track application behavior.
    """

    def increment(self, amount: int = 1, **tags: str) -> None:
        """
        Increment the metric.

        Args:
            amount: The amount to increment by
            **tags: Additional tags for the metric
        """
        ...

    def decrement(self, amount: int = 1, **tags: str) -> None:
        """
        Decrement the metric.

        Args:
            amount: The amount to decrement by
            **tags: Additional tags for the metric
        """
        ...

    def set(self, value: float, **tags: str) -> None:
        """
        Set the metric to a specific value.

        Args:
            value: The value to set
            **tags: Additional tags for the metric
        """
        ...

    def record(self, value: float, **tags: str) -> None:
        """
        Record a value for the metric.

        Args:
            value: The value to record
            **tags: Additional tags for the metric
        """
        ...


class MetricsProvider(Protocol):
    """
    Protocol for metrics providers.

    Metrics providers create and manage metrics.
    """

    def counter(self, name: str, description: str = "") -> Metric:
        """
        Create a counter metric.

        Args:
            name: The metric name
            description: Optional description

        Returns:
            The counter metric
        """
        ...

    def gauge(self, name: str, description: str = "") -> Metric:
        """
        Create a gauge metric.

        Args:
            name: The metric name
            description: Optional description

        Returns:
            The gauge metric
        """
        ...

    def histogram(self, name: str, description: str = "") -> Metric:
        """
        Create a histogram metric.

        Args:
            name: The metric name
            description: Optional description

        Returns:
            The histogram metric
        """
        ...

    def timer(self, name: str, description: str = "") -> Metric:
        """
        Create a timer metric.

        Args:
            name: The metric name
            description: Optional description

        Returns:
            The timer metric
        """
        ...


# Common type definitions
class Pagination(TypedDict, total=False):
    """Pagination options for queries."""

    limit: int
    offset: int


class Sorting(TypedDict, total=False):
    """Sorting options for queries."""

    field: str
    direction: Literal["asc", "desc"]


class QueryOptions(TypedDict, total=False):
    """Options for querying data."""

    pagination: Pagination
    sorting: NotRequired[List[Sorting]]
    include_deleted: NotRequired[bool]
    include_relations: NotRequired[bool | List[str]]


# Type guards
def is_entity(obj: Any) -> TypeGuard[Entity]:
    """
    Type guard to check if an object is an Entity.

    Args:
        obj: The object to check

    Returns:
        True if the object is an Entity, False otherwise
    """
    return (
        hasattr(obj, "id")
        and hasattr(obj, "created_at")
        and hasattr(obj, "__eq__")
        and hasattr(obj, "__hash__")
    )


def is_value_object(obj: Any) -> TypeGuard[ValueObject]:
    """
    Type guard to check if an object is a ValueObject.

    Args:
        obj: The object to check

    Returns:
        True if the object is a ValueObject, False otherwise
    """
    return (
        hasattr(obj, "__eq__")
        and hasattr(obj, "__hash__")
        and hasattr(obj, "equals")
        and not hasattr(obj, "id")  # Value objects don't have identity
    )


def is_aggregate_root(obj: Any) -> TypeGuard[AggregateRoot]:
    """
    Type guard to check if an object is an AggregateRoot.

    Args:
        obj: The object to check

    Returns:
        True if the object is an AggregateRoot, False otherwise
    """
    return (
        is_entity(obj)
        and hasattr(obj, "events")
        and hasattr(obj, "add_event")
        and hasattr(obj, "clear_events")
    )


@runtime_checkable
class DatabaseSessionProtocol(Protocol):
    """Protocol for database session objects."""

    async def execute(self, query: str, *args: Any, **kwargs: Any) -> Any:
        """
        Execute a query.

        Args:
            query: The query to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Query result
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def rollback(self) -> None:
        """Roll back the current transaction."""
        ...

    async def close(self) -> None:
        """Close the session."""
        ...

    async def fetchone(self) -> Optional[Dict[str, Any]]:
        """
        Fetch one result row.

        Returns:
            A row as a dictionary, or None if no rows available
        """
        ...

    async def fetchall(self) -> List[Dict[str, Any]]:
        """
        Fetch all result rows.

        Returns:
            A list of rows as dictionaries
        """
        ...


@runtime_checkable
class DatabaseSessionContextProtocol(Protocol):
    """Protocol for database session context objects."""

    async def __aenter__(self) -> DatabaseSessionProtocol:
        """
        Enter the context.

        Returns:
            The session object
        """
        ...

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        """
        Exit the context.

        Args:
            exc_type: Exception type, if an exception was raised
            exc_val: Exception value, if an exception was raised
            exc_tb: Exception traceback, if an exception was raised

        Returns:
            True if the exception was handled, False otherwise
        """
        ...


@runtime_checkable
class DatabaseSessionFactoryProtocol(Protocol):
    """Protocol for database session factory objects."""

    def __call__(self, **kwargs: Any) -> DatabaseSessionContextProtocol:
        """
        Create a session context.

        Args:
            **kwargs: Additional options for the session

        Returns:
            A session context object
        """
        ...


T_Model = TypeVar("T_Model")
T_Key = TypeVar("T_Key")
T_Schema = TypeVar("T_Schema")
T_Result = TypeVar("T_Result")
T_Extra = TypeVar("T_Extra")


@runtime_checkable
class DatabaseRepository(
    Protocol, Generic[T_Model, T_Key, T_Schema, T_Result, T_Extra]
):
    """Protocol for database repositories."""

    async def get(self, **kwargs: Any) -> T_Model:
        """
        Get an entity by parameters.

        Args:
            **kwargs: Filter parameters

        Returns:
            The entity if found

        Raises:
            NotFoundException: If no entity is found
        """
        ...

    async def filter(self, filters: Optional[Any] = None) -> List[T_Model]:
        """
        Filter entities by parameters.

        Args:
            filters: Filter parameters

        Returns:
            A list of matching entities
        """
        ...

    async def create(self, schema: T_Schema) -> List[T_Model]:
        """
        Create a new entity.

        Args:
            schema: The schema containing entity data

        Returns:
            A list containing the created entity
        """
        ...

    async def update(self, to_db_model: T_Model) -> T_Model:
        """
        Update an entity.

        Args:
            to_db_model: The model to update

        Returns:
            The updated model
        """
        ...

    async def delete(self, model: T_Model) -> None:
        """
        Delete an entity.

        Args:
            model: The model to delete
        """
        ...

    async def merge(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Merge entity data.

        Args:
            data: The data to merge

        Returns:
            A list containing the merged entity data and action
        """
        ...


@runtime_checkable
class FilterManagerProtocol(Protocol):
    """Protocol for filter managers."""

    def create_filters_from_table(
        self,
        model_class: Type[BaseModel],
        exclude_from_filters: bool = False,
        exclude_fields: Optional[List[str]] = None,
    ) -> Dict[str, UnoFilterProtocol]:
        """
        Create filters from a model's table.

        Args:
            model_class: The model class to create filters from
            exclude_from_filters: Whether to exclude this model from filters
            exclude_fields: List of field names to exclude from filtering

        Returns:
            A dictionary of filter names to filter objects
        """
        ...

    def create_filter_params(
        self,
        model_class: Type[BaseModel],
    ) -> Type[BaseModel]:
        """
        Create a filter parameters model for a model class.

        Args:
            model_class: The model class to create filter parameters for

        Returns:
            A Pydantic model class for filter parameters
        """
        ...

    def validate_filter_params(
        self,
        filter_params: BaseModel,
        model_class: Type[BaseModel],
    ) -> List[Any]:
        """
        Validate filter parameters.

        Args:
            filter_params: The filter parameters to validate
            model_class: The model class to validate against

        Returns:
            A list of validated filter tuples
        """
        ...


@runtime_checkable
class SchemaManagerProtocol(Protocol):
    """Protocol for schema managers."""

    def get_schema(self, schema_type: str) -> Type[BaseModel]:
        """
        Get a schema by type.

        Args:
            schema_type: The type of schema to get

        Returns:
            The schema class
        """
        ...


@runtime_checkable
class DBClientProtocol(Protocol):
    """Protocol for database clients."""

    async def query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a query and return the results.

        Args:
            query: The query to execute
            params: Optional query parameters

        Returns:
            A list of dictionaries representing the query results
        """
        ...
