"""
Unified domain service pattern for the Uno framework.

This module provides a standardized implementation of domain services that
combines the best features of existing implementations and integrates with
the unified event system.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    TypeVar,
    Generic,
    Dict,
    List,
    Optional,
    Any,
    Type,
    Union,
    Protocol,
    runtime_checkable,
    cast,
)

from uno.core.errors.result import Result, Success, Failure
from uno.core.unified_events import (
    UnoDomainEvent,
    get_event_bus,
    collect_event,
    EventBus,
    publish_event,
)
from uno.core.errors.base import UnoError
from uno.domain.core import Entity, AggregateRoot
from uno.domain.repository import Repository
from uno.domain.unit_of_work import UnitOfWork


# Type variables
T = TypeVar("T")
E = TypeVar("E", bound=Entity)
A = TypeVar("A", bound=AggregateRoot)
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")
RepoT = TypeVar("RepoT", bound=Repository)
UowT = TypeVar("UowT", bound=UnitOfWork)


@runtime_checkable
class DomainServiceProtocol(Protocol[InputT, OutputT]):
    """
    Protocol for domain services.

    This protocol defines the interface for domain services that
    encapsulate domain operations and business logic.
    """

    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the domain service operation.

        Args:
            input_data: Input data for the operation

        Returns:
            Result containing the operation output or error details
        """
        ...


class DomainService(Generic[InputT, OutputT, UowT], ABC):
    """
    Base class for domain services that require transactions.

    Domain services encapsulate operations that don't naturally belong to
    entities or value objects. They are typically stateless and operate on
    multiple domain objects, providing a clear boundary for business logic.

    Type Parameters:
        InputT: Type of input data for the service operation
        OutputT: Type of output data from the service operation
        UowT: Type of unit of work for transaction management
    """

    def __init__(
        self,
        uow: UowT,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize domain service.

        Args:
            uow: Unit of work for transaction management
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostic information
        """
        self.uow = uow
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the domain service operation within a transaction.

        This method provides transactional boundaries and error handling
        for the domain operation.

        Args:
            input_data: Input data for the operation

        Returns:
            Result with operation output or failure details
        """
        try:
            # Validate input
            validation_result = self.validate(input_data)
            if validation_result and validation_result.is_failure:
                return validation_result

            # Start transaction
            async with self.uow:
                # Execute the domain operation
                result = await self._execute_internal(input_data)

                # If successful, commit transaction
                if result.is_success:
                    # Collect events from repositories if they implement collect_events
                    events: List[UnoDomainEvent] = []
                    for repo in self.uow.repositories:
                        if hasattr(repo, "collect_events") and callable(
                            repo.collect_events
                        ):
                            events.extend(repo.collect_events())

                    # Collect events from result if it contains events
                    if hasattr(result, "events") and result.events:
                        events.extend(result.events)

                    # Commit the transaction
                    await self.uow.commit()

                    # Publish events after successful commit
                    for event in events:
                        collect_event(event)

                return result

        except UnoError as e:
            # Known domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))

        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True,
            )
            return Failure(str(e))

    def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate the input data before execution.

        This method can be overridden by derived classes to implement
        input validation logic. Return None if validation passes,
        or a Failure result if validation fails.

        Args:
            input_data: Input data to validate

        Returns:
            None if validation passes, or a Failure result if validation fails
        """
        return None

    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the domain service operation.

        This method should be implemented by derived classes to provide
        the specific domain operation logic.

        Args:
            input_data: Input data for the operation

        Returns:
            Result with operation output or failure details
        """
        pass


class ReadOnlyDomainService(Generic[InputT, OutputT, UowT], ABC):
    """
    Base class for read-only domain services.

    Read-only domain services perform operations that don't modify domain state,
    such as complex queries or calculations. They don't require transaction
    management but still operate within the domain model.

    Type Parameters:
        InputT: Type of input data for the service operation
        OutputT: Type of output data from the service operation
        UowT: Type of unit of work for accessing repositories
    """

    def __init__(self, uow: UowT, logger: Optional[logging.Logger] = None):
        """
        Initialize read-only domain service.

        Args:
            uow: Unit of work for accessing repositories
            logger: Optional logger for diagnostic information
        """
        self.uow = uow
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the read-only domain service operation.

        Args:
            input_data: Input data for the operation

        Returns:
            Result with operation output or failure details
        """
        try:
            # Validate input
            validation_result = self.validate(input_data)
            if validation_result and validation_result.is_failure:
                return validation_result

            # Execute the query operation - no transaction needed
            return await self._execute_internal(input_data)

        except UnoError as e:
            # Known domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))

        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True,
            )
            return Failure(str(e))

    def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate the input data before execution.

        This method can be overridden by derived classes to implement
        input validation logic. Return None if validation passes,
        or a Failure result if validation fails.

        Args:
            input_data: Input data to validate

        Returns:
            None if validation passes, or a Failure result if validation fails
        """
        return None

    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the read-only domain service operation.

        This method should be implemented by derived classes to provide
        the specific domain operation logic.

        Args:
            input_data: Input data for the operation

        Returns:
            Result with operation output or failure details
        """
        pass


class EntityService(Generic[E]):
    """
    Service for working with domain entities.

    This service provides standard CRUD operations for domain entities,
    using a repository for data access and supporting domain events.

    Type Parameters:
        E: The type of entity this service manages
    """

    def __init__(
        self,
        entity_type: Type[E],
        repository: Repository[E],
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the entity service.

        Args:
            entity_type: The type of entity this service manages
            repository: Repository for data access
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostic information
        """
        self.entity_type = entity_type
        self.repository = repository
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def get_by_id(self, id: Any) -> Result[Optional[E]]:
        """
        Get an entity by ID.

        Args:
            id: The entity ID

        Returns:
            Result containing the entity if found
        """
        try:
            entity = await self.repository.get(id)
            return Success(entity)
        except Exception as e:
            self.logger.error(f"Error retrieving entity by ID: {str(e)}")
            return Failure(str(e))

    async def find(self, filters: Dict[str, Any]) -> Result[List[E]]:
        """
        Find entities matching filters.

        Args:
            filters: Filter criteria

        Returns:
            Result containing matching entities
        """
        try:
            entities = await self.repository.list(filters)
            return Success(entities)
        except Exception as e:
            self.logger.error(f"Error finding entities: {str(e)}")
            return Failure(str(e))

    async def list_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[str]] = None,
    ) -> Result[List[E]]:
        """
        List all entities with pagination.

        Args:
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            order_by: Fields to order by

        Returns:
            Result containing entities
        """
        try:
            entities = await self.repository.list(
                filters={}, order_by=order_by, limit=limit, offset=offset
            )
            return Success(entities)
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return Failure(str(e))

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count entities.

        Args:
            filters: Optional filter criteria

        Returns:
            Result containing count
        """
        try:
            count = await self.repository.count(filters or {})
            return Success(count)
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            return Failure(str(e))

    async def create(self, data: Dict[str, Any]) -> Result[E]:
        """
        Create a new entity.

        Args:
            data: Entity data

        Returns:
            Result containing the created entity
        """
        try:
            # Create entity instance
            entity = self.entity_type(**data)

            # Save to repository
            saved_entity = await self.repository.add(entity)

            # Publish events
            if hasattr(saved_entity, "get_events"):
                events = saved_entity.get_events()
                for event in events:
                    publish_event(event)

            return Success(saved_entity)
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return Failure(str(e))

    async def update(self, id: Any, data: Dict[str, Any]) -> Result[E]:
        """
        Update an existing entity.

        Args:
            id: Entity ID
            data: Updated entity data

        Returns:
            Result containing the updated entity
        """
        try:
            # Get existing entity
            entity = await self.repository.get(id)
            if not entity:
                return Failure(f"Entity with ID {id} not found")

            # Update fields
            for key, value in data.items():
                if hasattr(entity, key):
                    setattr(entity, key, value)

            # Update timestamp if applicable
            if hasattr(entity, "update") and callable(entity.update):
                entity.update()

            # Save to repository
            updated_entity = await self.repository.update(entity)

            # Publish events
            if hasattr(updated_entity, "get_events"):
                events = updated_entity.get_events()
                for event in events:
                    publish_event(event)

            return Success(updated_entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return Failure(str(e))

    async def delete(self, id: Any) -> Result[bool]:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            Result indicating success or failure
        """
        try:
            # Get existing entity
            entity = await self.repository.get(id)
            if not entity:
                return Failure(f"Entity with ID {id} not found")

            # Remove from repository
            await self.repository.remove(entity)

            # Publish deletion event if applicable
            if hasattr(entity, "id") and hasattr(entity, "__class__"):
                # Create a generic deletion event
                from uno.core.unified_events import UnoDomainEvent

                event = UnoDomainEvent(
                    event_type=f"{entity.__class__.__name__.lower()}_deleted",
                    aggregate_id=str(entity.id),
                    aggregate_type=entity.__class__.__name__,
                )
                publish_event(event)

            return Success(True)
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return Failure(str(e))


class AggregateService(Generic[A]):
    """
    Service for working with aggregate roots.

    This service provides operations for aggregate roots, ensuring
    proper event handling and transaction boundaries.

    Type Parameters:
        A: The type of aggregate root this service manages
    """

    def __init__(
        self,
        aggregate_type: Type[A],
        repository: Repository[A],
        unit_of_work: UnitOfWork,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the aggregate service.

        Args:
            aggregate_type: The type of aggregate this service manages
            repository: Repository for data access
            unit_of_work: Unit of work for transaction management
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostic information
        """
        self.aggregate_type = aggregate_type
        self.repository = repository
        self.unit_of_work = unit_of_work
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def get_by_id(self, id: Any) -> Result[Optional[A]]:
        """
        Get an aggregate by ID.

        Args:
            id: The aggregate ID

        Returns:
            Result containing the aggregate if found
        """
        try:
            aggregate = await self.repository.get(id)
            return Success(aggregate)
        except Exception as e:
            self.logger.error(f"Error retrieving aggregate by ID: {str(e)}")
            return Failure(str(e))

    async def find(self, filters: Dict[str, Any]) -> Result[List[A]]:
        """
        Find aggregates matching filters.

        Args:
            filters: Filter criteria

        Returns:
            Result containing matching aggregates
        """
        try:
            aggregates = await self.repository.list(filters)
            return Success(aggregates)
        except Exception as e:
            self.logger.error(f"Error finding aggregates: {str(e)}")
            return Failure(str(e))

    async def create(self, data: Dict[str, Any]) -> Result[A]:
        """
        Create a new aggregate.

        Args:
            data: Aggregate data

        Returns:
            Result containing the created aggregate
        """
        try:
            async with self.unit_of_work:
                # Create aggregate instance
                aggregate = self.aggregate_type(**data)

                # Apply changes to ensure invariants and increment version
                aggregate.apply_changes()

                # Save to repository
                saved_aggregate = await self.repository.add(aggregate)

                # Collect events
                events = []
                if hasattr(saved_aggregate, "clear_events"):
                    events = saved_aggregate.clear_events()

                # Commit transaction
                await self.unit_of_work.commit()

                # Publish events after successful commit
                for event in events:
                    publish_event(event)

                return Success(saved_aggregate)

        except Exception as e:
            self.logger.error(f"Error creating aggregate: {str(e)}")
            return Failure(str(e))

    async def update(self, id: Any, version: int, data: Dict[str, Any]) -> Result[A]:
        """
        Update an existing aggregate with optimistic concurrency.

        Args:
            id: Aggregate ID
            version: Expected current version for concurrency control
            data: Updated aggregate data

        Returns:
            Result containing the updated aggregate
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")

                # Check version for optimistic concurrency
                if hasattr(aggregate, "version") and aggregate.version != version:
                    return Failure(
                        f"Concurrency conflict: expected version {version}, found {aggregate.version}"
                    )

                # Update fields
                for key, value in data.items():
                    if hasattr(aggregate, key):
                        setattr(aggregate, key, value)

                # Apply changes to ensure invariants and increment version
                aggregate.apply_changes()

                # Save to repository
                updated_aggregate = await self.repository.update(aggregate)

                # Collect events
                events = []
                if hasattr(updated_aggregate, "clear_events"):
                    events = updated_aggregate.clear_events()

                # Commit transaction
                await self.unit_of_work.commit()

                # Publish events after successful commit
                for event in events:
                    publish_event(event)

                return Success(updated_aggregate)

        except Exception as e:
            self.logger.error(f"Error updating aggregate: {str(e)}")
            return Failure(str(e))

    async def delete(self, id: Any, version: Optional[int] = None) -> Result[bool]:
        """
        Delete an aggregate with optional optimistic concurrency.

        Args:
            id: Aggregate ID
            version: Optional expected current version for concurrency control

        Returns:
            Result indicating success or failure
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")

                # Check version for optimistic concurrency if provided
                if (
                    version is not None
                    and hasattr(aggregate, "version")
                    and aggregate.version != version
                ):
                    return Failure(
                        f"Concurrency conflict: expected version {version}, found {aggregate.version}"
                    )

                # Generate deletion event before removing
                from uno.core.unified_events import UnoDomainEvent

                event = UnoDomainEvent(
                    event_type=f"{aggregate.__class__.__name__.lower()}_deleted",
                    aggregate_id=str(aggregate.id),
                    aggregate_type=aggregate.__class__.__name__,
                )

                # Remove from repository
                await self.repository.remove(aggregate)

                # Commit transaction
                await self.unit_of_work.commit()

                # Publish deletion event
                publish_event(event)

                return Success(True)

        except Exception as e:
            self.logger.error(f"Error deleting aggregate: {str(e)}")
            return Failure(str(e))


class DomainServiceFactory:
    """
    Factory for creating domain services.

    This factory creates and configures domain services with appropriate
    dependencies, such as repositories, units of work, and event bus.
    """

    def __init__(
        self,
        unit_of_work_factory: Any,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize domain service factory.

        Args:
            unit_of_work_factory: Factory for creating units of work
            event_bus: Optional event bus for publishing domain events
            logger: Optional logger for diagnostic information
        """
        self.unit_of_work_factory = unit_of_work_factory
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(__name__)
        self._registered_entity_types: Dict[Type[Entity], Repository] = {}

    def register_entity_type(
        self, entity_type: Type[Entity], repository: Repository
    ) -> None:
        """
        Register an entity type with its repository.

        Args:
            entity_type: The entity type to register
            repository: The repository for the entity type
        """
        self._registered_entity_types[entity_type] = repository
        self.logger.debug(f"Registered entity type {entity_type.__name__}")

    def create_domain_service(
        self, service_class: Type[DomainService], **kwargs: Any
    ) -> DomainService:
        """
        Create a domain service instance.

        Args:
            service_class: Domain service class to instantiate
            **kwargs: Additional constructor arguments

        Returns:
            Domain service instance
        """
        # Create a unit of work
        uow = self.unit_of_work_factory.create_uow()

        # Create the service with dependencies
        service = service_class(uow=uow, event_bus=self.event_bus, **kwargs)

        return service

    def create_read_only_service(
        self, service_class: Type[ReadOnlyDomainService], **kwargs: Any
    ) -> ReadOnlyDomainService:
        """
        Create a read-only domain service instance.

        Args:
            service_class: Read-only domain service class to instantiate
            **kwargs: Additional constructor arguments

        Returns:
            Read-only domain service instance
        """
        # Create a unit of work
        uow = self.unit_of_work_factory.create_uow()

        # Create the service with dependencies
        service = service_class(uow=uow, **kwargs)

        return service

    def create_entity_service(
        self, entity_type: Type[E], **kwargs: Any
    ) -> EntityService[E]:
        """
        Create an entity service for a specific entity type.

        Args:
            entity_type: The entity type to create a service for
            **kwargs: Additional constructor arguments

        Returns:
            Entity service instance
        """
        # Get the repository for this entity type
        if entity_type not in self._registered_entity_types:
            raise ValueError(
                f"No repository registered for entity type {entity_type.__name__}"
            )

        repository = self._registered_entity_types[entity_type]

        # Create the service
        service = EntityService(
            entity_type=entity_type,
            repository=repository,
            event_bus=self.event_bus,
            **kwargs,
        )

        return service

    def create_aggregate_service(
        self, aggregate_type: Type[A], **kwargs: Any
    ) -> AggregateService[A]:
        """
        Create an aggregate service for a specific aggregate type.

        Args:
            aggregate_type: The aggregate type to create a service for
            **kwargs: Additional constructor arguments

        Returns:
            Aggregate service instance
        """
        # Get the repository for this aggregate type
        if aggregate_type not in self._registered_entity_types:
            raise ValueError(
                f"No repository registered for aggregate type {aggregate_type.__name__}"
            )

        repository = self._registered_entity_types[aggregate_type]

        # Create a unit of work
        uow = self.unit_of_work_factory.create_uow()

        # Create the service
        service = AggregateService(
            aggregate_type=aggregate_type,
            repository=repository,
            unit_of_work=uow,
            event_bus=self.event_bus,
            **kwargs,
        )

        return service


# Default service factory instance
_service_factory: Optional[DomainServiceFactory] = None


def get_service_factory() -> DomainServiceFactory:
    """
    Get the default domain service factory.

    Returns:
        The default domain service factory

    Raises:
        RuntimeError: If the service factory has not been initialized
    """
    if _service_factory is None:
        raise RuntimeError("Domain service factory has not been initialized")

    return _service_factory


def initialize_service_factory(
    unit_of_work_factory: Any,
    event_bus: Optional[EventBus] = None,
    logger: Optional[logging.Logger] = None,
) -> None:
    """
    Initialize the default domain service factory.

    Args:
        unit_of_work_factory: Factory for creating units of work
        event_bus: Optional event bus for publishing domain events
        logger: Optional logger for diagnostic information

    Raises:
        RuntimeError: If the service factory has already been initialized
    """
    global _service_factory

    if _service_factory is not None:
        raise RuntimeError("Domain service factory is already initialized")

    _service_factory = DomainServiceFactory(
        unit_of_work_factory=unit_of_work_factory, event_bus=event_bus, logger=logger
    )


def reset_service_factory() -> None:
    """
    Reset the default domain service factory.

    This function is primarily intended for testing scenarios where
    you need to reset the service factory between tests.
    """
    global _service_factory
    _service_factory = None
