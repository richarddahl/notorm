"""
Application service layer implementation for the Uno framework.

This module provides the application service layer, which acts as a facade
coordinating the execution of commands and queries, and enforcing
application-specific business rules.
"""

import logging
from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
    Protocol,
    Union,
    Callable,
)

from uno.domain.cqrs import (
    Command,
    Query,
    CommandResult,
    QueryResult,
    Dispatcher,
    get_dispatcher,
)
from uno.domain.models import Entity, AggregateRoot
from uno.domain.unit_of_work import UnitOfWork
from uno.core.errors.base import UnoError
from uno.core.errors.validation import ValidationError
from uno.core.errors.security import AuthorizationError


# Type variables
T = TypeVar("T")
EntityT = TypeVar("EntityT", bound=Entity)
AggregateT = TypeVar("AggregateT", bound=AggregateRoot)


class ServiceContext:
    """
    Context for service operations.

    This class provides context information for service operations,
    such as the current user, tenant, and request information.
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        is_authenticated: bool = False,
        permissions: Optional[List[str]] = None,
        request_metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the service context.

        Args:
            user_id: ID of the current user
            tenant_id: ID of the current tenant
            is_authenticated: Whether the user is authenticated
            permissions: List of permission codes the user has
            request_metadata: Additional request metadata
        """
        self.user_id = user_id
        self.tenant_id = tenant_id
        self.is_authenticated = is_authenticated
        self.permissions = permissions or []
        self.request_metadata = request_metadata or {}

    def has_permission(self, permission: str) -> bool:
        """
        Check if the context has a specific permission.

        Args:
            permission: The permission to check

        Returns:
            True if the permission is granted, False otherwise
        """
        return "*" in self.permissions or permission in self.permissions

    def require_authentication(self) -> None:
        """
        Require that the user is authenticated.

        Raises:
            AuthorizationError: If the user is not authenticated
        """
        if not self.is_authenticated:
            raise AuthorizationError("Authentication required")

    def require_permission(self, permission: str) -> None:
        """
        Require that the user has a specific permission.

        Args:
            permission: The permission to check

        Raises:
            AuthorizationError: If the user does not have the permission
        """
        if not self.has_permission(permission):
            raise AuthorizationError(f"Permission required: {permission}")

    @classmethod
    def create_anonymous(cls) -> "ServiceContext":
        """
        Create an anonymous service context.

        Returns:
            Anonymous service context
        """
        return cls()

    @classmethod
    def create_system(cls) -> "ServiceContext":
        """
        Create a service context for system operations.

        System operations bypass normal permission checks.

        Returns:
            System service context
        """
        return cls(
            user_id="system",
            is_authenticated=True,
            permissions=["*"],  # Wildcard permission
        )


class ApplicationService(ABC):
    """
    Base class for application services.

    Application services coordinate the execution of commands and queries,
    enforce application-specific business rules, and handle
    cross-cutting concerns like authorization.
    """

    def __init__(
        self,
        dispatcher: Optional[Dispatcher] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the service.

        Args:
            dispatcher: CQRS dispatcher for commands and queries
            logger: Optional logger instance
        """
        self.dispatcher = dispatcher or get_dispatcher()
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def execute_command(
        self, command: Command, context: ServiceContext
    ) -> CommandResult:
        """
        Execute a command.

        This method applies authorization, validation, and other
        cross-cutting concerns before dispatching the command.

        Args:
            command: The command to execute
            context: The service context

        Returns:
            The result of the command execution
        """
        try:
            # Apply service-specific authorization
            self.authorize_command(command, context)

            # Apply service-specific validation
            self.validate_command(command, context)

            # Add context information to the command if needed
            self.enrich_command(command, context)

            # Dispatch the command
            return await self.dispatcher.dispatch_command(command)
        except AuthorizationError as e:
            self.logger.warning(f"Authorization failed: {str(e)}")
            return CommandResult.rejection(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code=e.code,
            )
        except ValidationError as e:
            self.logger.warning(f"Validation failed: {str(e)}")
            return CommandResult.rejection(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code=e.code,
            )
        except Exception as e:
            self.logger.error(f"Error executing command: {str(e)}")
            return CommandResult.failure(
                command_id=command.command_id,
                command_type=command.__class__.__name__,
                error=str(e),
                error_code=getattr(e, "code", "SERVICE_ERROR"),
            )

    async def execute_query(self, query: Query, context: ServiceContext) -> QueryResult:
        """
        Execute a query.

        This method applies authorization, validation, and other
        cross-cutting concerns before dispatching the query.

        Args:
            query: The query to execute
            context: The service context

        Returns:
            The result of the query execution
        """
        try:
            # Apply service-specific authorization
            self.authorize_query(query, context)

            # Apply service-specific validation
            self.validate_query(query, context)

            # Add context information to the query if needed
            self.enrich_query(query, context)

            # Dispatch the query
            return await self.dispatcher.dispatch_query(query)
        except AuthorizationError as e:
            self.logger.warning(f"Authorization failed: {str(e)}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=str(e),
                error_code=e.code,
            )
        except ValidationError as e:
            self.logger.warning(f"Validation failed: {str(e)}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=str(e),
                error_code=e.code,
            )
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            return QueryResult.failure(
                query_id=query.query_id,
                query_type=query.__class__.__name__,
                error=str(e),
                error_code=getattr(e, "code", "SERVICE_ERROR"),
            )

    def authorize_command(self, command: Command, context: ServiceContext) -> None:
        """
        Authorize a command.

        This method can be overridden by subclasses to implement
        command-specific authorization logic.

        Args:
            command: The command to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        pass

    def validate_command(self, command: Command, context: ServiceContext) -> None:
        """
        Validate a command.

        This method can be overridden by subclasses to implement
        command-specific validation logic.

        Args:
            command: The command to validate
            context: The service context

        Raises:
            ValidationError: If validation fails
        """
        pass

    def enrich_command(self, command: Command, context: ServiceContext) -> None:
        """
        Enrich a command with context information.

        This method can be overridden by subclasses to add context
        information to commands before they are dispatched.

        Args:
            command: The command to enrich
            context: The service context
        """
        pass

    def authorize_query(self, query: Query, context: ServiceContext) -> None:
        """
        Authorize a query.

        This method can be overridden by subclasses to implement
        query-specific authorization logic.

        Args:
            query: The query to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        pass

    def validate_query(self, query: Query, context: ServiceContext) -> None:
        """
        Validate a query.

        This method can be overridden by subclasses to implement
        query-specific validation logic.

        Args:
            query: The query to validate
            context: The service context

        Raises:
            ValidationError: If validation fails
        """
        pass

    def enrich_query(self, query: Query, context: ServiceContext) -> None:
        """
        Enrich a query with context information.

        This method can be overridden by subclasses to add context
        information to queries before they are dispatched.

        Args:
            query: The query to enrich
            context: The service context
        """
        pass


class EntityService(ApplicationService, Generic[EntityT]):
    """
    Base service for entity operations.

    This service provides common operations for working with entities,
    such as creating, updating, deleting, and querying.
    """

    def __init__(
        self,
        entity_type: Type[EntityT],
        dispatcher: Optional[Dispatcher] = None,
        logger: Optional[logging.Logger] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
    ):
        """
        Initialize the entity service.

        Args:
            entity_type: The type of entity this service manages
            dispatcher: CQRS dispatcher for commands and queries
            logger: Optional logger instance
            read_permission: Permission required for read operations
            write_permission: Permission required for write operations
        """
        super().__init__(dispatcher, logger)
        self.entity_type = entity_type
        self.read_permission = read_permission
        self.write_permission = write_permission

    def authorize_command(self, command: Command, context: ServiceContext) -> None:
        """
        Authorize a command.

        Requires authentication and write permission.

        Args:
            command: The command to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        context.require_authentication()
        if self.write_permission:
            context.require_permission(self.write_permission)

    def authorize_query(self, query: Query, context: ServiceContext) -> None:
        """
        Authorize a query.

        Requires authentication and read permission.

        Args:
            query: The query to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        context.require_authentication()
        if self.read_permission:
            context.require_permission(self.read_permission)

    async def create(
        self, data: Dict[str, Any], context: ServiceContext
    ) -> CommandResult:
        """
        Create a new entity.

        Args:
            data: Entity data
            context: Service context

        Returns:
            Command result with the created entity
        """
        from uno.domain.command_handlers import CreateEntityCommand

        command = CreateEntityCommand(entity_data=data)
        return await self.execute_command(command, context)

    async def update(
        self, id: str, data: Dict[str, Any], context: ServiceContext
    ) -> CommandResult:
        """
        Update an existing entity.

        Args:
            id: Entity ID
            data: Entity data to update
            context: Service context

        Returns:
            Command result with the updated entity
        """
        from uno.domain.command_handlers import UpdateEntityCommand

        command = UpdateEntityCommand(id=id, entity_data=data)
        return await self.execute_command(command, context)

    async def delete(self, id: str, context: ServiceContext) -> CommandResult:
        """
        Delete an entity.

        Args:
            id: Entity ID
            context: Service context

        Returns:
            Command result indicating success or failure
        """
        from uno.domain.command_handlers import DeleteEntityCommand

        command = DeleteEntityCommand(id=id)
        return await self.execute_command(command, context)

    async def get_by_id(self, id: str, context: ServiceContext) -> QueryResult:
        """
        Get an entity by ID.

        Args:
            id: Entity ID
            context: Service context

        Returns:
            Query result with the entity if found
        """
        from uno.domain.query_handlers import EntityByIdQuery

        query = EntityByIdQuery[self.entity_type](id=id)
        return await self.execute_query(query, context)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        context: ServiceContext = None,
    ) -> QueryResult:
        """
        List entities.

        Args:
            filters: Optional filter criteria
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip
            context: Service context

        Returns:
            Query result with the list of entities
        """
        from uno.domain.query_handlers import EntityListQuery

        query = EntityListQuery[self.entity_type](
            filters=filters, order_by=order_by, limit=limit, offset=offset
        )
        return await self.execute_query(query, context)

    async def paginated_list(
        self,
        page: int = 1,
        page_size: int = 50,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        context: ServiceContext = None,
    ) -> QueryResult:
        """
        Get a paginated list of entities.

        Args:
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional filter criteria
            order_by: Optional ordering
            context: Service context

        Returns:
            Query result with paginated entities
        """
        from uno.domain.query_handlers import PaginatedEntityQuery

        query = PaginatedEntityQuery[self.entity_type](
            page=page, page_size=page_size, filters=filters, order_by=order_by
        )
        return await self.execute_query(query, context)


class AggregateService(ApplicationService, Generic[AggregateT]):
    """
    Base service for aggregate operations.

    This service provides common operations for working with aggregates,
    such as creating, updating, deleting, and querying.
    """

    def __init__(
        self,
        aggregate_type: Type[AggregateT],
        dispatcher: Optional[Dispatcher] = None,
        logger: Optional[logging.Logger] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
    ):
        """
        Initialize the aggregate service.

        Args:
            aggregate_type: The type of aggregate this service manages
            dispatcher: CQRS dispatcher for commands and queries
            logger: Optional logger instance
            read_permission: Permission required for read operations
            write_permission: Permission required for write operations
        """
        super().__init__(dispatcher, logger)
        self.aggregate_type = aggregate_type
        self.read_permission = read_permission
        self.write_permission = write_permission

    def authorize_command(self, command: Command, context: ServiceContext) -> None:
        """
        Authorize a command.

        Requires authentication and write permission.

        Args:
            command: The command to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        context.require_authentication()
        if self.write_permission:
            context.require_permission(self.write_permission)

    def authorize_query(self, query: Query, context: ServiceContext) -> None:
        """
        Authorize a query.

        Requires authentication and read permission.

        Args:
            query: The query to authorize
            context: The service context

        Raises:
            AuthorizationError: If authorization fails
        """
        context.require_authentication()
        if self.read_permission:
            context.require_permission(self.read_permission)

    async def create(
        self, data: Dict[str, Any], context: ServiceContext
    ) -> CommandResult:
        """
        Create a new aggregate.

        Args:
            data: Aggregate data
            context: Service context

        Returns:
            Command result with the created aggregate
        """
        from uno.domain.command_handlers import CreateAggregateCommand

        command = CreateAggregateCommand(aggregate_data=data)
        return await self.execute_command(command, context)

    async def update(
        self, id: str, version: int, data: Dict[str, Any], context: ServiceContext
    ) -> CommandResult:
        """
        Update an existing aggregate.

        Args:
            id: Aggregate ID
            version: Current version for optimistic concurrency
            data: Aggregate data to update
            context: Service context

        Returns:
            Command result with the updated aggregate
        """
        from uno.domain.command_handlers import UpdateAggregateCommand

        command = UpdateAggregateCommand(id=id, version=version, aggregate_data=data)
        return await self.execute_command(command, context)

    async def delete(
        self, id: str, version: Optional[int] = None, context: ServiceContext = None
    ) -> CommandResult:
        """
        Delete an aggregate.

        Args:
            id: Aggregate ID
            version: Optional version for optimistic concurrency
            context: Service context

        Returns:
            Command result indicating success or failure
        """
        from uno.domain.command_handlers import DeleteAggregateCommand

        command = DeleteAggregateCommand(id=id, version=version)
        return await self.execute_command(command, context)

    async def get_by_id(self, id: str, context: ServiceContext) -> QueryResult:
        """
        Get an aggregate by ID.

        Args:
            id: Aggregate ID
            context: Service context

        Returns:
            Query result with the aggregate if found
        """
        from uno.domain.query_handlers import EntityByIdQuery

        query = EntityByIdQuery[self.aggregate_type](id=id)
        return await self.execute_query(query, context)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        context: ServiceContext = None,
    ) -> QueryResult:
        """
        List aggregates.

        Args:
            filters: Optional filter criteria
            order_by: Optional ordering
            limit: Maximum number of aggregates to return
            offset: Number of aggregates to skip
            context: Service context

        Returns:
            Query result with the list of aggregates
        """
        from uno.domain.query_handlers import EntityListQuery

        query = EntityListQuery[self.aggregate_type](
            filters=filters, order_by=order_by, limit=limit, offset=offset
        )
        return await self.execute_query(query, context)


class ServiceRegistry:
    """
    Registry for application services.

    This registry provides a central place to register and retrieve services.
    """

    def __init__(self):
        """Initialize the service registry."""
        self._services: Dict[str, ApplicationService] = {}
        self._logger = logging.getLogger(__name__)

    def register(self, name: str, service: ApplicationService) -> None:
        """
        Register a service.

        Args:
            name: Service name
            service: Service instance
        """
        self._services[name] = service
        self._logger.debug(f"Registered service: {name}")

    def get(self, name: str) -> ApplicationService:
        """
        Get a service by name.

        Args:
            name: Service name

        Returns:
            Service instance

        Raises:
            KeyError: If service not found
        """
        if name not in self._services:
            raise KeyError(f"Service not found: {name}")

        return self._services[name]

    def register_entity_service(
        self,
        entity_type: Type[EntityT],
        name: Optional[str] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
    ) -> EntityService[EntityT]:
        """
        Register an entity service.

        Args:
            entity_type: The type of entity this service manages
            name: Optional service name (defaults to entity type name)
            read_permission: Permission required for read operations
            write_permission: Permission required for write operations

        Returns:
            Entity service instance
        """
        # Generate service name if not provided
        service_name = name or f"{entity_type.__name__}Service"

        # Create the service
        service = EntityService(
            entity_type=entity_type,
            read_permission=read_permission,
            write_permission=write_permission,
        )

        # Register the service
        self.register(service_name, service)

        return service

    def register_aggregate_service(
        self,
        aggregate_type: Type[AggregateT],
        name: Optional[str] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
    ) -> AggregateService[AggregateT]:
        """
        Register an aggregate service.

        Args:
            aggregate_type: The type of aggregate this service manages
            name: Optional service name (defaults to aggregate type name)
            read_permission: Permission required for read operations
            write_permission: Permission required for write operations

        Returns:
            Aggregate service instance
        """
        # Generate service name if not provided
        service_name = name or f"{aggregate_type.__name__}Service"

        # Create the service
        service = AggregateService(
            aggregate_type=aggregate_type,
            read_permission=read_permission,
            write_permission=write_permission,
        )

        # Register the service
        self.register(service_name, service)

        return service


# Create a default service registry
default_service_registry = ServiceRegistry()


def get_service_registry() -> ServiceRegistry:
    """Get the default service registry."""
    return default_service_registry
