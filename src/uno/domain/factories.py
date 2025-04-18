"""
Entity factory pattern implementation for domain models.

This module provides a modern approach to entity creation using the factory pattern,
with support for complex entity creation logic, validation, and dependency injection.
"""

from typing import (
    TypeVar,
    Generic,
    Dict,
    Type,
    Any,
    Optional,
    List,
    Protocol,
    runtime_checkable,
    ClassVar,
    Set,
)
import logging
from datetime import datetime, timezone
from uuid import uuid4

from uno.domain.models import (
    Entity,
    AggregateRoot,
    ValueObject,
    UnoEvent,
    CommandResult,
)
from uno.domain.protocols import (
    EntityProtocol,
    AggregateRootProtocol,
    ValueObjectProtocol,
    EntityFactoryProtocol,
    DomainEventProtocol,
)
from uno.core.base.error import DomainValidationError


# Type variables
T = TypeVar("T", bound=Entity)
A = TypeVar("A", bound=AggregateRoot)
V = TypeVar("V", bound=ValueObject)


class EntityFactory(Generic[T]):
    """
    Base factory for creating domain entities.

    This factory provides methods for creating and reconstituting entities,
    with support for validation and event registration.
    """

    entity_class: ClassVar[Type[T]]

    @classmethod
    def create(cls, **kwargs: Any) -> T:
        """
        Create a new entity with a new ID.

        Args:
            **kwargs: Entity attributes

        Returns:
            A new entity instance

        Raises:
            DomainValidationError: If entity validation fails
        """
        # Generate ID if not provided
        if "id" not in kwargs:
            kwargs["id"] = str(uuid4())

        # Set creation timestamp if not provided
        if "created_at" not in kwargs:
            kwargs["created_at"] = datetime.now(timezone.utc)

        # Create the entity
        return cls.entity_class(**kwargs)

    @classmethod
    def create_with_events(cls, events: List[DomainEventProtocol], **kwargs: Any) -> T:
        """
        Create a new entity and register domain events.

        Args:
            events: Domain events to register with the entity
            **kwargs: Entity attributes

        Returns:
            A new entity instance with registered events

        Raises:
            DomainValidationError: If entity validation fails
        """
        entity = cls.create(**kwargs)

        # Register the events
        for event in events:
            entity.register_event(event)

        return entity

    @classmethod
    def reconstitute(cls, data: Dict[str, Any]) -> T:
        """
        Reconstitute an entity from a dictionary representation.

        This is typically used when loading entities from persistence.

        Args:
            data: Dictionary containing entity data

        Returns:
            A reconstituted entity instance

        Raises:
            DomainValidationError: If entity validation fails
        """
        return cls.entity_class.from_dict(data)


class AggregateFactory(EntityFactory[A], Generic[A]):
    """
    Factory for creating aggregate roots.

    This factory extends the entity factory with aggregate-specific functionality,
    such as handling child entities and checking invariants.
    """

    entity_class: ClassVar[Type[A]]

    @classmethod
    def create_with_children(
        cls, children: Optional[List[EntityProtocol]] = None, **kwargs: Any
    ) -> A:
        """
        Create a new aggregate root with child entities.

        Args:
            children: Optional list of child entities
            **kwargs: Aggregate attributes

        Returns:
            A new aggregate instance with child entities

        Raises:
            DomainValidationError: If aggregate validation fails
        """
        aggregate = cls.create(**kwargs)

        # Add child entities if provided
        if children:
            for child in children:
                aggregate.add_child_entity(child)

            # Ensure aggregate invariants are satisfied
            aggregate.check_invariants()

        return aggregate

    @classmethod
    def reconstitute_with_children(
        cls, data: Dict[str, Any], children: Optional[List[EntityProtocol]] = None
    ) -> A:
        """
        Reconstitute an aggregate root with child entities.

        Args:
            data: Dictionary containing aggregate data
            children: Optional list of child entities

        Returns:
            A reconstituted aggregate instance with child entities

        Raises:
            DomainValidationError: If aggregate validation fails
        """
        aggregate = cls.reconstitute(data)

        # Add child entities if provided
        if children:
            for child in children:
                aggregate.add_child_entity(child)

            # Ensure aggregate invariants are satisfied
            aggregate.check_invariants()

        return aggregate


class ValueObjectFactory(Generic[V]):
    """
    Factory for creating value objects.

    This factory provides methods for creating and validating value objects.
    """

    value_class: ClassVar[Type[V]]

    @classmethod
    def create(cls, **kwargs: Any) -> V:
        """
        Create a new value object.

        Args:
            **kwargs: Value object attributes

        Returns:
            A new value object instance

        Raises:
            DomainValidationError: If value object validation fails
        """
        return cls.value_class(**kwargs)

    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> V:
        """
        Create a value object from a dictionary.

        Args:
            data: Dictionary containing value object data

        Returns:
            A value object instance

        Raises:
            DomainValidationError: If value object validation fails
        """
        return cls.value_class.from_dict(data)


class FactoryRegistry:
    """
    Registry for entity and value object factories.

    This registry provides a central place to register and access factories
    for domain entities, aggregates, and value objects.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the factory registry.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self._entity_factories: Dict[Type[EntityProtocol], EntityFactoryProtocol] = {}
        self._value_factories: Dict[Type[ValueObjectProtocol], ValueObjectFactory] = {}

    def register_entity_factory(
        self, entity_type: Type[EntityProtocol], factory: EntityFactoryProtocol
    ) -> None:
        """
        Register an entity factory.

        Args:
            entity_type: The entity type to register a factory for
            factory: The factory instance
        """
        if entity_type in self._entity_factories:
            self.logger.warning(f"Overriding factory for {entity_type.__name__}")

        self._entity_factories[entity_type] = factory
        self.logger.debug(f"Registered factory for {entity_type.__name__}")

    def register_value_factory(
        self, value_type: Type[ValueObjectProtocol], factory: ValueObjectFactory
    ) -> None:
        """
        Register a value object factory.

        Args:
            value_type: The value object type to register a factory for
            factory: The factory instance
        """
        if value_type in self._value_factories:
            self.logger.warning(f"Overriding factory for {value_type.__name__}")

        self._value_factories[value_type] = factory
        self.logger.debug(f"Registered factory for {value_type.__name__}")

    def get_entity_factory(
        self, entity_type: Type[EntityProtocol]
    ) -> EntityFactoryProtocol:
        """
        Get the factory for an entity type.

        Args:
            entity_type: The entity type to get a factory for

        Returns:
            The entity factory

        Raises:
            KeyError: If no factory is registered for the entity type
        """
        if entity_type not in self._entity_factories:
            raise KeyError(f"No factory registered for {entity_type.__name__}")

        return self._entity_factories[entity_type]

    def get_value_factory(
        self, value_type: Type[ValueObjectProtocol]
    ) -> ValueObjectFactory:
        """
        Get the factory for a value object type.

        Args:
            value_type: The value object type to get a factory for

        Returns:
            The value object factory

        Raises:
            KeyError: If no factory is registered for the value object type
        """
        if value_type not in self._value_factories:
            raise KeyError(f"No factory registered for {value_type.__name__}")

        return self._value_factories[value_type]


def create_entity_factory(entity_cls: Type[T]) -> Type[EntityFactory[T]]:
    """
    Create a factory class for a specific entity type.

    Args:
        entity_cls: The entity class to create a factory for

    Returns:
        A factory class for the entity type
    """

    # Create a new factory class with the entity_class set
    class ConcreteEntityFactory(EntityFactory[entity_cls]):
        entity_class = entity_cls

    # Set a more descriptive name
    ConcreteEntityFactory.__name__ = f"{entity_cls.__name__}Factory"

    return ConcreteEntityFactory


def create_aggregate_factory(aggregate_cls: Type[A]) -> Type[AggregateFactory[A]]:
    """
    Create a factory class for a specific aggregate root type.

    Args:
        aggregate_cls: The aggregate class to create a factory for

    Returns:
        A factory class for the aggregate type
    """

    # Create a new factory class with the entity_class set
    class ConcreteAggregateFactory(AggregateFactory[aggregate_cls]):
        entity_class = aggregate_cls

    # Set a more descriptive name
    ConcreteAggregateFactory.__name__ = f"{aggregate_cls.__name__}Factory"

    return ConcreteAggregateFactory


def create_value_factory(value_cls: Type[V]) -> Type[ValueObjectFactory[V]]:
    """
    Create a factory class for a specific value object type.

    Args:
        value_cls: The value object class to create a factory for

    Returns:
        A factory class for the value object type
    """

    # Create a new factory class with the value_class set
    class ConcreteValueFactory(ValueObjectFactory[value_cls]):
        value_class = value_cls

    # Set a more descriptive name
    ConcreteValueFactory.__name__ = f"{value_cls.__name__}Factory"

    return ConcreteValueFactory
