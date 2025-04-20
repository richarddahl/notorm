"""
Service pattern implementation for the domain entity framework.

This module provides base classes for implementing the Service pattern with domain entities.
Domain services represent the operations and business logic that don't naturally fit on entities.
"""

import logging
from abc import ABC
from typing import Any, Generic, TypeVar, cast, type

from uno.core.errors.result import Result
from uno.core.uow.base import AbstractUnitOfWork
from uno.domain.entity.base import EntityBase
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.specification.base import Specification

ID = TypeVar("ID")  # ID type variable
T = TypeVar("T", bound=EntityBase)  # Entity type variable
E = TypeVar("E")  # Error type variable
R = TypeVar("R")  # Result type variable


from uno.domain.event_bus import EventBusProtocol
from typing import Any, Mapping


async def publish_and_clear_events(
    aggregate: Any,
    event_bus: EventBusProtocol,
    *,
    metadata: Mapping[str, Any] | None = None,
    correlation_id: str | None = None,
) -> None:
    """
    Publish all uncommitted domain events from the aggregate root via the event bus, then clear them.
    Supports batch publishing, metadata, and correlation IDs for robust event handling.

    Args:
        aggregate: The aggregate root (must have get_uncommitted_events and clear_events)
        event_bus: The event bus implementing EventBusProtocol
        metadata: Optional metadata to attach to events
        correlation_id: Optional correlation/causation ID
    """
    if (
        aggregate
        and hasattr(aggregate, "get_uncommitted_events")
        and hasattr(event_bus, "publish_many")
    ):
        events = aggregate.get_uncommitted_events()
        if events:
            await event_bus.publish_many(
                events, metadata=metadata, correlation_id=correlation_id
            )
        if hasattr(aggregate, "clear_events"):
            aggregate.clear_events()


class DomainService(Generic[T, ID], ABC):
    """
    Base class for domain services.

    Domain services encapsulate business logic that doesn't naturally belong on an entity.
    They operate on entities and value objects, but are not entities themselves.
    """

    def __init__(
        self,
        entity_type: type[T],
        repository: EntityRepository[T, ID],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the domain service.

        Args:
            entity_type: The type of entity this service works with
            repository: Repository for accessing entities
            logger: Optional logger instance
        """
        self.entity_type = entity_type
        self.repository = repository
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def get_by_id(self, id: ID) -> Result[T, str]:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Success with entity or Failure if not found
        """
        entity = await self.repository.get(id)
        if entity is None:
            return Failure[T, str](f"Entity with ID {id} not found", convert=True)
        return Success[T, str](entity, convert=True)

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> Result[list[T], str]:
        """
        List entities matching filter criteria.

        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination

        Returns:
            Success with list of entities or Failure if an error occurs
        """
        try:
            entities = await self.repository.list(filters, order_by, limit, offset)
            return Success[list[T], str](entities, convert=True)
        except Exception as e:
            self.logger.error(f"Error listing entities: {e}", exc_info=True)
            return Failure[list[T], str](f"Error listing entities: {str(e)}")

    async def find(self, specification: Specification[T]) -> Result[list[T], str]:
        """
        Find entities matching a specification.

        Args:
            specification: The specification to match against

        Returns:
            Success with list of entities or Failure if an error occurs
        """
        try:
            entities = await self.repository.find(specification)
            return Success[list[T], str](entities, convert=True)
        except Exception as e:
            self.logger.error(f"Error finding entities: {e}", exc_info=True)
            return Failure[list[T], str](f"Error finding entities: {str(e)}")

    async def find_one(self, specification: Specification[T]) -> Result[T | None, str]:
        """
        Find a single entity matching a specification.

        Args:
            specification: The specification to match against

        Returns:
            Success with entity or None, or Failure if an error occurs
        """
        try:
            entity = await self.repository.find_one(specification)
            return Success[T | None, str](entity, convert=True)
        except Exception as e:
            self.logger.error(f"Error finding entity: {e}", exc_info=True)
            return Failure[T | None, str](
                f"Error finding entity: {str(e)}", convert=True
            )

    async def count(
        self, specification: Specification[T] | None = None
    ) -> Result[int, str]:
        """
        Count entities matching a specification.

        Args:
            specification: Optional specification to match against

        Returns:
            Success with count or Failure if an error occurs
        """
        try:
            count = await self.repository.count(specification)
            return Success[int, str](count, convert=True)
        except Exception as e:
            self.logger.error(f"Error counting entities: {e}", exc_info=True)
            return Failure[int, str](f"Error counting entities: {str(e)}", convert=True)


class DomainServiceWithUnitOfWork(DomainService[T, ID], Generic[T, ID]):
    """
    Domain service that uses the Unit of Work pattern.

    This service uses a Unit of Work to manage transactions and ensure
    consistency when operating on multiple repositories or entities.
    """

    def __init__(
        self,
        entity_type: type[T],
        unit_of_work: AbstractUnitOfWork,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the domain service with a unit of work.

        Args:
            entity_type: The type of entity this service works with
            unit_of_work: Unit of Work for managing transactions
            logger: Optional logger instance
        """
        self.entity_type = entity_type
        self.unit_of_work = unit_of_work
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

        # Repository will be initialized when the UoW is started
        self._repository: EntityRepository[T, ID] | None = None

    @property
    def repository(self) -> Result[EntityRepository[T, ID], str]:
        """
        Get the repository from the unit of work.

        Returns:
            Result containing the repository for the entity type or an error message
        """
        if self._repository is None:
            return Failure(
                "Repository not available. The unit of work must be started first."
            )
        return Success(self._repository)

    async def _ensure_repository(self) -> Result[EntityRepository[T, ID], str]:
        """
        Ensure that the repository is initialized.

        If the unit of work is not active, this method will try to get it.

        Returns:
            Result containing the repository or an error message
        """
        if self._repository is not None:
            return Success[EntityRepository[T, ID], str](self._repository)

        # Try to get the repository from the unit of work
        repo_result = self.unit_of_work.get_repository(self.entity_type)

        if repo_result.is_failure():
            error_msg = f"Repository for {self.entity_type.__name__} not found in unit of work. Make sure to register the repository."
            self.logger.warning(error_msg)
            return Failure[EntityRepository[T, ID], str](error_msg)

        self._repository = cast("EntityRepository[T, ID]", repo_result.value())
        return Success(self._repository)

    async def with_uow(self, action_name: str) -> AbstractUnitOfWork:
        """
        Create a Unit of Work context manager.

        This method is useful when you need to execute multiple repository
        operations in a single transaction.

        Args:
            action_name: Name of the action for logging

        Returns:
            Unit of Work context manager
        """
        return self.unit_of_work.with_logging(action_name)

    async def create(self, entity: T) -> Result[T, str]:
        """
        Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            Success with created entity or Failure if an error occurs
        """
        async with self.with_uow(f"create_{self.entity_type.__name__}"):
            # Ensure repository is available
            repo_result = await self._ensure_repository()
            if repo_result.is_failure():
                return Failure(f"Could not create entity: {repo_result.error()}")

            repository = repo_result.value()

            # Use the repository to add the entity
            try:
                created = await repository.add(entity)
                if isinstance(created, Result):
                    return created
                return Success[T, str](created)
            except Exception as e:
                self.logger.error("Error creating entity: %s", e, exc_info=True)
                return Failure[T, str](f"Error creating entity: {str(e)}")

    async def update(self, entity: T) -> Result[T, str]:
        """
        Update an existing entity.

        Args:
            entity: The entity to update

        Returns:
            Success with updated entity or Failure if an error occurs
        """
        async with self.with_uow(f"update_{self.entity_type.__name__}"):
            # Ensure repository is available
            repo_result = await self._ensure_repository()
            if repo_result.is_failure():
                return Failure(f"Could not update entity: {repo_result.error()}")

            repository = repo_result.value()

            # Use the repository to update the entity
            try:
                updated = await repository.update(entity)
                if isinstance(updated, Result):
                    return updated
                return Success[T, str](updated)
            except Exception as e:
                self.logger.error("Error updating entity: %s", e, exc_info=True)
                return Failure[T, str](f"Error updating entity: {str(e)}")

    async def delete(self, entity: T) -> Result[None, str]:
        """
        Delete an entity.

        Args:
            entity: The entity to delete

        Returns:
            Success or Failure if an error occurs
        """
        async with self.with_uow(f"delete_{self.entity_type.__name__}"):
            # Ensure repository is available
            repo_result = await self._ensure_repository()
            if repo_result.is_failure():
                return Failure[None, str](
                    f"Could not delete entity: {repo_result.error()}"
                )

            repository = repo_result.value()

            # Use the repository to delete the entity
            try:
                result = await repository.delete(entity)
                if isinstance(result, Result):
                    return result
                return Success[None, str](None)
            except Exception as e:
                self.logger.error("Error deleting entity: %s", e, exc_info=True)
                return Failure[None, str](
                    f"Error deleting entity: {str(e)}", convert=True
                )

    async def delete_by_id(self, id: ID) -> Result[bool, str]:
        """
        Delete an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Success with True if deleted, False if not found, or Failure if an error occurs
        """
        async with self.with_uow(f"delete_{self.entity_type.__name__}_by_id"):
            # Ensure repository is available
            repo_result = await self._ensure_repository()
            if repo_result.is_failure():
                return Failure[bool, str](
                    f"Could not delete entity by ID: {repo_result.error()}"
                )

            repository = repo_result.value()

            try:
                # Use the repository to delete the entity by ID
                result = await repository.delete_by_id(id)
                if isinstance(result, Result):
                    return result
                # If the repository doesn't return a Result yet, convert it
                return Success[bool, str](bool(result))
            except Exception as e:
                self.logger.error("Error deleting entity by ID: %s", e, exc_info=True)
                return Failure[bool, str](f"Error deleting entity by ID: {str(e)}")


class ApplicationService(Generic[R, E]):
    """
    Base class for application services.

    Application services coordinate the execution of operations that span multiple domain
    services, repositories, or external systems. They implement the command and query operations
    of the application, orchestrating the use of domain objects and infrastructure.
    """

    def __init__(self, logger: logging.Logger | None = None):
        """
        Initialize the application service.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def log_request(self, method: str, request: Any) -> None:
        """
        Log an incoming request.

        Args:
            method: Method name
            request: Request data
        """
        self.logger.info(f"Received request '{method}': {request}")

    def log_response(self, method: str, result: Result[R, E]) -> None:
        """
        Log the result of a request.

        Args:
            method: Method name
            result: Operation result
        """
        if result.is_success():
            self.logger.info(f"Request '{method}' succeeded")
        else:
            self.logger.warning(f"Request '{method}' failed: {result.error}")

    def log_error(self, method: str, error: Exception) -> None:
        """
        Log an exception.

        Args:
            method: Method name
            error: Exception that occurred
        """
        self.logger.error(f"Error in '{method}': {error}", exc_info=True)


class CrudService(ApplicationService[T, str], Generic[T, ID]):
    """
    Base class for CRUD application services.

    CRUD services provide a standardized interface for creating, reading, updating,
    and deleting entities. They delegate the actual operations to domain services.
    """

    def __init__(
        self, domain_service: DomainService[T, ID], logger: logging.Logger | None = None
    ):
        """
        Initialize the CRUD service.

        Args:
            domain_service: Domain service to delegate operations to
            logger: Optional logger instance
        """
        super().__init__(logger)
        self.domain_service = domain_service

    async def get(self, id: ID) -> Result[T, str]:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Success with entity or Failure if not found or an error occurs
        """
        self.log_request("get", id)
        try:
            result = await self.domain_service.get_by_id(id)
            self.log_response("get", result)
            return result
        except Exception as e:
            self.log_error("get", e)
            return Failure[T | None, str](f"Error getting entity: {str(e)}")

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = 0,
    ) -> Result[list[T], str]:
        """
        List entities matching filter criteria.

        Args:
            filters: Optional filter criteria as a dictionary
            order_by: Optional list of fields to order by
            limit: Optional limit on number of results
            offset: Optional offset for pagination

        Returns:
            Success with list of entities or Failure if an error occurs
        """
        self.log_request(
            "list",
            {
                "filters": filters,
                "order_by": order_by,
                "limit": limit,
                "offset": offset,
            },
        )
        try:
            result = await self.domain_service.list(filters, order_by, limit, offset)
            self.log_response("list", result)
            return result
        except Exception as e:
            self.log_error("list", e)
            return Failure[list[T], str](f"Error listing entities: {str(e)}")

    async def find(self, specification: Specification[T]) -> Result[list[T], str]:
        """
        Find entities matching a specification.

        Args:
            specification: The specification to match against

        Returns:
            Success with list of entities or Failure if an error occurs
        """
        self.log_request("find", specification)
        try:
            result = await self.domain_service.find(specification)
            self.log_response("find", result)
            return result
        except Exception as e:
            self.log_error("find", e)
            return Failure[list[T], str](f"Error finding entities: {str(e)}")

    async def create(self, entity: T) -> Result[T, str]:
        """
        Create a new entity.

        Args:
            entity: The entity to create

        Returns:
            Success with created entity or Failure if an error occurs
        """
        self.log_request("create", entity)

        # Validate entity if domain service supports it
        if hasattr(self.domain_service, "validate"):
            validation_result = await self.domain_service.validate(entity)
            if not validation_result.is_success():
                self.logger.warning(f"Validation failed: {validation_result.error}")
                return cast("Result[T, str]", validation_result)

        try:
            # Use domain service with UoW if available
            if isinstance(self.domain_service, DomainServiceWithUnitOfWork):
                result = await self.domain_service.create(entity)
            else:
                # Otherwise, use repository directly
                created = await self.domain_service.repository.add(entity)
                result = Success(created)

            self.log_response("create", result)
            return result
        except Exception as e:
            self.log_error("create", e)
            return Failure[T, str](f"Error creating entity: {str(e)}")

    async def update(self, entity: T) -> Result[T, str]:
        """
        Update an existing entity.

        Args:
            entity: The entity to update

        Returns:
            Success with updated entity or Failure if an error occurs
        """
        self.log_request("update", entity)

        # Validate entity if domain service supports it
        if hasattr(self.domain_service, "validate"):
            validation_result = await self.domain_service.validate(entity)
            if not validation_result.is_success():
                self.logger.warning(f"Validation failed: {validation_result.error}")
                return cast("Result[T, str]", validation_result)

        try:
            # Use domain service with UoW if available
            if isinstance(self.domain_service, DomainServiceWithUnitOfWork):
                result = await self.domain_service.update(entity)
            else:
                # Otherwise, use repository directly
                updated = await self.domain_service.repository.update(entity)
                result = Success(updated)

            self.log_response("update", result)
            return result
        except Exception as e:
            self.log_error("update", e)
            return Failure[T, str](f"Error updating entity: {str(e)}")

    async def delete(self, id: ID) -> Result[bool, str]:
        """
        Delete an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Success with True if deleted, False if not found, or Failure if an error occurs
        """
        self.log_request("delete", id)
        try:
            # Use domain service with UoW if available
            if isinstance(self.domain_service, DomainServiceWithUnitOfWork):
                result = await self.domain_service.delete_by_id(id)
            else:
                # Otherwise, use repository directly
                deleted = await self.domain_service.repository.delete_by_id(id)
                result = Success(deleted)

            self.log_response("delete", result)
            return result
        except Exception as e:
            self.log_error("delete", e)
            return Failure[bool, str](f"Error deleting entity: {str(e)}")


class ServiceFactory(Generic[T, ID]):
    """
    Factory for creating service instances.

    This factory creates and configures services for a given entity type,
    handling the creation of repositories and other dependencies.
    """

    def __init__(
        self,
        entity_type: type[T],
        repository_factory: callable | None = None,
        unit_of_work_factory: callable | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the service factory.

        Args:
            entity_type: The type of entity the services will work with
            repository_factory: Optional factory function for creating repositories
            unit_of_work_factory: Optional factory function for creating units of work
            logger: Optional logger instance
        """
        self.entity_type = entity_type
        self.repository_factory = repository_factory
        self.unit_of_work_factory = unit_of_work_factory
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def create_domain_service(
        self,
        repository: EntityRepository[T, ID] | None = None,
        logger: logging.Logger | None = None,
    ) -> DomainService[T, ID]:
        """
        Create a domain service.

        Args:
            repository: Optional repository to use, otherwise one will be created
            logger: Optional logger instance

        Returns:
            Domain service instance
        """
        repo = repository
        if repo is None and self.repository_factory is not None:
            repo = self.repository_factory(self.entity_type)

        if repo is None:
            raise ValueError(
                "Repository must be provided or repository_factory must be set"
            )

        return DomainService(self.entity_type, repo, logger or self.logger)

    def create_domain_service_with_uow(
        self,
        unit_of_work: AbstractUnitOfWork | None = None,
        logger: logging.Logger | None = None,
    ) -> DomainServiceWithUnitOfWork[T, ID]:
        """
        Create a domain service with unit of work.

        Args:
            unit_of_work: Optional unit of work to use, otherwise one will be created
            logger: Optional logger instance

        Returns:
            Domain service with UoW instance
        """
        uow = unit_of_work
        if uow is None and self.unit_of_work_factory is not None:
            uow = self.unit_of_work_factory()

        if uow is None:
            raise ValueError(
                "Unit of work must be provided or unit_of_work_factory must be set"
            )

        return DomainServiceWithUnitOfWork(self.entity_type, uow, logger or self.logger)

    def create_crud_service(
        self,
        domain_service: DomainService[T, ID] | None = None,
        logger: logging.Logger | None = None,
    ) -> CrudService[T, ID]:
        """
        Create a CRUD service.

        Args:
            domain_service: Optional domain service to use, otherwise one will be created
            logger: Optional logger instance

        Returns:
            CRUD service instance
        """
        service = domain_service
        if service is None:
            # Prefer domain service with UoW if unit_of_work_factory is available
            if self.unit_of_work_factory is not None:
                service = self.create_domain_service_with_uow()
            elif self.repository_factory is not None:
                service = self.create_domain_service()
            else:
                raise ValueError(
                    "Domain service must be provided or repository_factory or unit_of_work_factory must be set"
                )

        return CrudService(service, logger or self.logger)
