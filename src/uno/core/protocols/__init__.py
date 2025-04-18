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


# Import the unified ConfigProtocol
from uno.dependencies.interfaces import ConfigProtocol as BaseConfigProtocol

# Re-export ConfigProtocol with runtime_checkable decorator
@runtime_checkable
class ConfigProvider(BaseConfigProtocol, Protocol):
    """
    Protocol for configuration providers.

    Configuration providers are responsible for managing application
    settings and configuration values.
    
    This is an alias for ConfigProtocol from uno.dependencies.interfaces for 
    backwards compatibility and to add runtime checking capabilities.
    """
    pass


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
