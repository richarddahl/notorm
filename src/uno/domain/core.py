"""
Core domain components for the Uno framework.

This module provides the foundational classes for implementing a domain-driven design
approach in the Uno framework, including entities, value objects, aggregates, and events.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from functools import wraps
from typing import (
    Dict,
    Any,
    Optional,
    List,
    TypeVar,
    Generic,
    Set,
    ClassVar,
    Type,
    cast,
)

from pydantic import BaseModel, Field, ConfigDict, model_validator

# Python 3.13 compatibility workaround
import sys

if sys.version_info[:2] >= (3, 13):
    # For Python 3.13+, we patch the abc module's update_abstractmethods function
    # to avoid the dictionary keys changed during iteration error
    import abc

    _original_update_abstractmethods = abc.update_abstractmethods

    def _patched_update_abstractmethods(cls):
        """
        A patched version of abc.update_abstractmethods that handles dictionary modification safely.

        This is a workaround for a Python 3.13 issue with dataclasses where the original
        implementation can cause a "dictionary keys changed during iteration" error.
        """
        try:
            return _original_update_abstractmethods(cls)
        except RuntimeError as e:
            if "dictionary keys changed during iteration" in str(e):
                # Just return cls without modifying abstract methods
                # This is safe for our use case with dataclasses
                return cls
            # Re-raise any other RuntimeError
            raise

    # Apply the patch
    abc.update_abstractmethods = _patched_update_abstractmethods


# Keep the safe_dataclass decorator for additional safety
def safe_dataclass(cls: Type) -> Type:
    """
    A decorator to safely create dataclasses from classes that might have abstract methods.

    This adds extra safety by ensuring proper collection initialization, especially
    for Python 3.13 compatibility.

    Usage:
        @safe_dataclass
        @dataclass
        class MyClass(Entity):
            # class definition...

    Args:
        cls: The class to decorate

    Returns:
        The decorated class
    """
    # Store original __annotations__ to avoid modification during iteration
    orig_annotations = getattr(cls, "__annotations__", {}).copy()

    # Get the original __post_init__ if it exists
    orig_post_init = getattr(cls, "__post_init__", None)

    # Define a safe post_init method that ensures all collections are initialized
    def safe_post_init(self):
        """Safe initialization after dataclass processing."""
        # Call original __post_init__ if it exists
        if orig_post_init is not None:
            orig_post_init(self)

        # Initialize collections based on annotations
        for field_name, field_type in orig_annotations.items():
            if not hasattr(self, field_name) or getattr(self, field_name) is None:
                # Handle dictionary fields
                if (
                    field_type == Dict
                    or isinstance(field_type, type)
                    and issubclass(field_type, Dict)
                ):
                    setattr(self, field_name, {})
                # Handle list fields
                elif (
                    field_type == List
                    or isinstance(field_type, type)
                    and issubclass(field_type, List)
                ):
                    setattr(self, field_name, [])
                # Handle set fields
                elif (
                    field_type == Set
                    or isinstance(field_type, type)
                    and issubclass(field_type, Set)
                ):
                    setattr(self, field_name, set())

    # Set the safe __post_init__ on the class
    cls.__post_init__ = safe_post_init

    return cls


class DomainException(Exception):
    """
    Base exception for domain-related errors.

    Domain exceptions represent business rule violations or domain logic errors.
    They should be specific and meaningful to the domain.
    """

    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        """
        Initialize a domain exception.

        Args:
            message: A descriptive error message
            code: An error code for categorizing the error
        """
        self.code = code
        super().__init__(message)


class DomainEvent(BaseModel):
    """
    Base class for domain events.

    Domain events represent something significant that occurred within the domain.
    They are used to communicate between different parts of the application
    and to enable event-driven architectures.
    """

    model_config = ConfigDict(frozen=True)

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(default="domain_event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create an event from a dictionary."""
        return cls(**data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to a dictionary."""
        return self.model_dump()


class ValueObject(BaseModel):
    """
    Base class for value objects.

    Value objects are immutable objects that contain attributes but lack a conceptual identity.
    They are used to represent concepts within your domain that are defined by their attributes
    rather than by an identity.

    Examples include Money, Address, and DateRange.
    """

    model_config = ConfigDict(frozen=True)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self):
        return hash(tuple(sorted(self.model_dump().items())))


T_ID = TypeVar("T_ID")  # Entity ID type


class Entity(BaseModel, Generic[T_ID]):
    """
    Base class for domain entities.

    Entities are objects that have a distinct identity that runs through time and
    different states. They are defined by their identity, not by their attributes.

    Examples include User, Order, and Product.
    """

    # Allow arbitrary types to support rich domain models
    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: T_ID = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = Field(default=None)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)

    @model_validator(mode="before")
    def set_updated_at(cls, values):
        """Update the updated_at field whenever the entity is modified."""
        # Handle Pydantic v2 ValidationInfo objects
        if hasattr(values, 'get_default_value'):
            # We're dealing with a ValidationInfo object in Pydantic v2
            # In this case, we're in the before validator and values is the data dict
            data = values
            # Only set updated_at for existing entities that are being modified
            if isinstance(data, dict) and 'id' in data and 'created_at' in data and data['id'] and data['created_at']:
                data['updated_at'] = datetime.now(timezone.utc)
            return data
        
        # Handle regular dict (for backward compatibility)
        if isinstance(values, dict) and values.get("id") and values.get("created_at"):
            values["updated_at"] = datetime.now(timezone.utc)
        
        return values

    # Python 3.13 compatibility methods for dataclasses
    def __post_init__(self):
        """
        Handle initialization after dataclass processing.

        This method is called by dataclasses after the object is initialized.
        Override it in subclasses to handle additional initialization
        requirements, but be sure to call super().__post_init__() first.
        """
        # Ensure object attributes are properly initialized
        for field_name, field_value in self.__annotations__.items():
            # Check if this is a collection that might need initialization
            if hasattr(self, field_name):
                continue  # Field already exists

            # Handle dictionary fields
            if (
                field_value == Dict
                or isinstance(field_value, type)
                and issubclass(field_value, Dict)
            ):
                setattr(self, field_name, {})
            # Handle list fields
            elif (
                field_value == List
                or isinstance(field_value, type)
                and issubclass(field_value, List)
            ):
                setattr(self, field_name, [])
            # Handle set fields
            elif (
                field_value == Set
                or isinstance(field_value, type)
                and issubclass(field_value, Set)
            ):
                setattr(self, field_name, set())


T = TypeVar("T", bound=Entity)
T_Child = TypeVar("T_Child", bound=Entity)


class AggregateRoot(Entity[T_ID]):
    """
    Base class for aggregate roots.

    Aggregate roots are the entry point to an aggregate - a cluster of domain objects
    that can be treated as a single unit. They encapsulate related domain objects and
    define boundaries for transactions and consistency.

    Examples include Order (which contains OrderLines), User (which contains Addresses).
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Add type annotations to mark class attributes
    # These can be used to hold instance attributes that should be properly initialized
    _events: List[DomainEvent]
    _child_entities: Set[Entity]

    def __init__(self, **data):
        super().__init__(**data)
        # Initialize instance-specific collections
        self._events = []
        self._child_entities = set()

    # Override __post_init__ from Entity to handle dataclass compatibility
    def __post_init__(self):
        """
        Handle initialization after dataclass processing for aggregate roots.

        This method ensures that all necessary collections are properly initialized,
        even when the object is created through dataclass processing.
        """
        super().__post_init__()

        # Explicitly initialize our instance collections
        if not hasattr(self, "_events") or self._events is None:
            self._events = []
        if not hasattr(self, "_child_entities") or self._child_entities is None:
            self._child_entities = set()

    def add_event(self, event: DomainEvent) -> None:
        """
        Add a domain event to this aggregate.

        Domain events are collected within the aggregate and can be processed
        after the aggregate is saved.

        Args:
            event: The domain event to add
        """
        if not hasattr(self, "_events") or self._events is None:
            self._events = []
        self._events.append(event)

    def clear_events(self) -> List[DomainEvent]:
        """
        Clear all domain events from this aggregate.

        Returns:
            The list of events that were cleared
        """
        if not hasattr(self, "_events") or self._events is None:
            self._events = []
            return []

        events = self._events.copy()
        self._events.clear()
        return events

    def register_child_entity(self, entity: Entity) -> None:
        """
        Register a child entity with this aggregate root.

        Args:
            entity: The child entity to register
        """
        if not hasattr(self, "_child_entities") or self._child_entities is None:
            self._child_entities = set()
        self._child_entities.add(entity)

    def get_child_entities(self) -> Set[Entity]:
        """
        Get all child entities of this aggregate root.

        Returns:
            The set of child entities
        """
        if not hasattr(self, "_child_entities") or self._child_entities is None:
            self._child_entities = set()
        return self._child_entities
