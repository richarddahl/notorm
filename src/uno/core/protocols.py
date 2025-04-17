"""
Core protocol definitions for the Uno framework.

This module provides the foundational protocol definitions that form the
contracts between different parts of the system. These protocols enable
loose coupling and dependency injection throughout the application.

Using protocols instead of abstract base classes allows for structural typing,
where compatibility is determined by API shape rather than inheritance hierarchy.
"""

from abc import abstractmethod
from datetime import datetime
import uuid
import logging
from typing import (
    Protocol,
    runtime_checkable,
    Any,
    TypeVar,
    Self,
    ClassVar,
    TypedDict,
    NotRequired,
    TypeGuard,
    cast,
    Literal,
    overload,
    get_origin,
    get_args,
    get_type_hints,
    Annotated,
)


# =============================================================================
# Common Type Variables
# =============================================================================

T = TypeVar("T")
T_co = TypeVar("T_co", covariant=True)
T_contra = TypeVar("T_contra", contravariant=True)
ID = TypeVar("ID")


# =============================================================================
# Common TypedDict definitions
# =============================================================================


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
    sorting: NotRequired[list[Sorting]]
    include_deleted: NotRequired[bool]
    include_relations: NotRequired[bool | list[str]]


# =============================================================================
# Type Guards
# =============================================================================


def is_entity(obj: Any) -> TypeGuard["Entity"]:
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


def is_aggregate_root(obj: Any) -> TypeGuard["AggregateRoot"]:
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


def is_value_object(obj: Any) -> TypeGuard["ValueObject"]:
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


# =============================================================================
# Core Domain Protocols
# =============================================================================


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


# Import domain event protocol from the canonical implementation
import warnings
from uno.core.unified_events import DomainEventProtocol

# Protocol alias for backward compatibility, but with a deprecation warning
@runtime_checkable
class UnoDomainEvent(DomainEventProtocol, Protocol):
    """
    Protocol for domain events. (DEPRECATED)

    This is a compatibility alias for DomainEventProtocol from unified_events.
    Domain events represent something that happened in the domain that
    domain experts care about. They are immutable and named in the past tense.
    """
    
    def __new__(cls, *args, **kwargs):
        warnings.warn(
            "UnoDomainEvent in uno.core.protocols is deprecated. "
            "Please use DomainEventProtocol from uno.core.unified_events instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return super().__new__(cls)


@runtime_checkable
class AggregateRoot(Entity, Protocol):
    """
    Protocol for aggregate roots in the domain model.

    Aggregate roots are the entry point to an aggregate - a cluster of domain objects
    that can be treated as a single unit. They ensure consistency within the aggregate
    and handle domain events.
    """

    @property
    def events(self) -> list[UnoDomainEvent]:
        """Get the domain events raised by this aggregate."""
        ...

    def add_event(self, event: UnoDomainEvent) -> None:
        """
        Add a domain event to this aggregate.

        Args:
            event: The domain event to add
        """
        ...

    def clear_events(self) -> list[UnoDomainEvent]:
        """
        Clear all domain events from this aggregate.

        Returns:
            The list of events that were cleared
        """
        ...


# =============================================================================
# Repository Protocols
# =============================================================================


class Repository[T_Entity, T_ID](Protocol):
    """
    Protocol for repositories in the domain model.

    Repositories mediate between the domain and data mapping layers,
    providing collection-like access to aggregates.

    Type Parameters:
        T_Entity: The type of entity this repository manages
        T_ID: The type of entity identifier
    """

    @abstractmethod
    async def get_by_id(self, id: T_ID) -> T_Entity | None:
        """
        Get an entity by its identifier.

        Args:
            id: The entity identifier

        Returns:
            The entity if found, None otherwise
        """
        ...

    @abstractmethod
    async def list(
        self, filters: dict[str, Any] | None = None, options: QueryOptions | None = None
    ) -> list[T_Entity]:
        """
        List entities based on filters and options.

        Args:
            filters: Optional filter criteria
            options: Optional listing options (limit, offset, ordering)

        Returns:
            List of matching entities
        """
        ...

    @abstractmethod
    async def add(self, entity: T_Entity) -> T_Entity:
        """
        Add an entity to the repository.

        Args:
            entity: The entity to add

        Returns:
            The added entity (with generated ID if applicable)
        """
        ...

    @abstractmethod
    async def update(self, entity: T_Entity) -> T_Entity:
        """
        Update an entity in the repository.

        Args:
            entity: The entity to update

        Returns:
            The updated entity
        """
        ...

    @abstractmethod
    async def delete(self, id: T_ID) -> bool:
        """
        Delete an entity by its identifier.

        Args:
            id: The entity identifier

        Returns:
            True if the entity was deleted, False otherwise
        """
        ...

    @abstractmethod
    async def exists(self, id: T_ID) -> bool:
        """
        Check if an entity with the given ID exists.

        Args:
            id: The ID to check

        Returns:
            True if the entity exists, False otherwise
        """
        ...

    @abstractmethod
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Count entities matching the given filters.

        Args:
            filters: Optional filter criteria

        Returns:
            Number of matching entities
        """
        ...


# =============================================================================
# Unit of Work Protocol
# =============================================================================


class UnitOfWork(Protocol):
    """
    Protocol for the Unit of Work pattern.

    The Unit of Work maintains a list of objects affected by a business transaction
    and coordinates the writing out of changes and the resolution of concurrency problems.
    """

    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Enter the Unit of Work context."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the Unit of Work context."""
        ...


# =============================================================================
# Command and Query Protocols
# =============================================================================


class Command[T_Result](Protocol):
    """
    Protocol for commands in the CQRS pattern.

    Commands represent intentions to change the state of the system.
    They are named in the imperative and should be processed exactly once.

    Type Parameters:
        T_Result: The type of result after command execution
    """

    command_id: str
    command_type: str


class Query[T_Result](Protocol):
    """
    Protocol for queries in the CQRS pattern.

    Queries represent intentions to retrieve data without changing state.
    They are named as questions and can be processed multiple times.

    Type Parameters:
        T_Result: The type of result after query execution
    """

    query_id: str
    query_type: str


class CommandHandler[T_Command, T_Result](Protocol):
    """
    Protocol for command handlers in the CQRS pattern.

    Command handlers process commands and produce results.

    Type Parameters:
        T_Command: The type of command this handler processes
        T_Result: The type of result after command execution
    """

    @abstractmethod
    async def handle(self, command: T_Command) -> T_Result:
        """
        Handle a command.

        Args:
            command: The command to handle

        Returns:
            Result of command execution
        """
        ...


class QueryHandler[T_Query, T_Result](Protocol):
    """
    Protocol for query handlers in the CQRS pattern.

    Query handlers process queries and produce results.

    Type Parameters:
        T_Query: The type of query this handler processes
        T_Result: The type of result after query execution
    """

    @abstractmethod
    async def handle(self, query: T_Query) -> T_Result:
        """
        Handle a query.

        Args:
            query: The query to handle

        Returns:
            Result of query execution
        """
        ...


# =============================================================================
# Event System Protocols
# =============================================================================


class EventHandler[T_Event](Protocol):
    """
    Protocol for event handlers.

    Event handlers process events and perform actions in response.

    Type Parameters:
        T_Event: The type of event this handler processes
    """

    @abstractmethod
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

    @abstractmethod
    def subscribe(self, event_type: type[Any], handler: EventHandler[Any]) -> None:
        """
        Subscribe a handler to events of a specific type.

        Args:
            event_type: The type of event to subscribe to
            handler: The handler to call when events occur
        """
        ...

    @abstractmethod
    def unsubscribe(self, event_type: type[Any], handler: EventHandler[Any]) -> None:
        """
        Unsubscribe a handler from events of a specific type.

        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler to remove
        """
        ...

    @abstractmethod
    async def publish(self, event: Any) -> None:
        """
        Publish an event to all subscribed handlers.

        Args:
            event: The event to publish
        """
        ...


# =============================================================================
# Dependency Injection Protocols
# =============================================================================


class ServiceProvider(Protocol):
    """
    Protocol for service providers.

    Service providers resolve and manage services in the application.
    """

    @abstractmethod
    def get_service(self, service_type: type[T]) -> T:
        """
        Get a service of the specified type.

        Args:
            service_type: The type of service to get

        Returns:
            Instance of the requested service
        """
        ...

    @abstractmethod
    def register_singleton(
        self, service_type: type[T], implementation: type[T] | T | None = None
    ) -> None:
        """
        Register a singleton service.

        Args:
            service_type: The type of service to register
            implementation: The implementation or instance to use
        """
        ...

    @abstractmethod
    def register_scoped(
        self, service_type: type[T], implementation: type[T] | None = None
    ) -> None:
        """
        Register a scoped service.

        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        ...

    @abstractmethod
    def register_transient(
        self, service_type: type[T], implementation: type[T] | None = None
    ) -> None:
        """
        Register a transient service.

        Args:
            service_type: The type of service to register
            implementation: The implementation to use
        """
        ...

    @abstractmethod
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

    @abstractmethod
    def get_service(self, service_type: type[T]) -> T:
        """
        Get a service of the specified type.

        Args:
            service_type: The type of service to get

        Returns:
            Instance of the requested service
        """
        ...

    @abstractmethod
    def dispose(self) -> None:
        """Dispose of the scope and its services."""
        ...

    @abstractmethod
    def __enter__(self) -> Self:
        """Enter the scope context."""
        ...

    @abstractmethod
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the scope context."""
        ...


# =============================================================================
# Lifecycle Protocols
# =============================================================================


class Initializable(Protocol):
    """
    Protocol for services that need initialization.

    Initializable services can perform asynchronous setup operations.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the service."""
        ...


class Disposable(Protocol):
    """
    Protocol for services that need cleanup.

    Disposable services can perform cleanup operations.
    """

    @abstractmethod
    def dispose(self) -> None:
        """Dispose of the service's resources."""
        ...


class AsyncDisposable(Protocol):
    """
    Protocol for services that need asynchronous cleanup.

    AsyncDisposable services can perform asynchronous cleanup operations.
    """

    @abstractmethod
    async def dispose_async(self) -> None:
        """Dispose of the service's resources asynchronously."""
        ...


# =============================================================================
# Error Handling Protocols
# =============================================================================


class Result[T_Success, T_Error](Protocol):
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

    def map(self, func: Any) -> "Result":
        """Map the success value using a function."""
        ...

    def flat_map(self, func: Any) -> "Result":
        """Apply a function that itself returns a Result."""
        ...


# =============================================================================
# Logging and Monitoring Protocols
# =============================================================================


class Logger(Protocol):
    """
    Protocol for loggers.

    Loggers provide a consistent interface for logging messages.
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """
        Log a debug message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """
        Log an info message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """
        Log a warning message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """
        Log an error message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """
        Log a critical message.

        Args:
            message: The message to log
            **kwargs: Additional context data
        """
        ...


class Metric(Protocol):
    """
    Protocol for metrics.

    Metrics provide a way to measure and track application behavior.
    """

    @abstractmethod
    def increment(self, amount: int = 1, **tags: str) -> None:
        """
        Increment the metric.

        Args:
            amount: The amount to increment by
            **tags: Additional tags for the metric
        """
        ...

    @abstractmethod
    def decrement(self, amount: int = 1, **tags: str) -> None:
        """
        Decrement the metric.

        Args:
            amount: The amount to decrement by
            **tags: Additional tags for the metric
        """
        ...

    @abstractmethod
    def set(self, value: float, **tags: str) -> None:
        """
        Set the metric to a specific value.

        Args:
            value: The value to set
            **tags: Additional tags for the metric
        """
        ...

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
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
