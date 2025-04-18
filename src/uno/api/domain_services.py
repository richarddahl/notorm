"""
Service implementations for the API module.

This module defines service protocols and implementations for the API module,
including services for API resource management, endpoint configuration, and
integration with FastAPI.
"""

from typing import (
    Dict,
    List,
    Optional,
    Any,
    Protocol,
    Type,
    TypeVar,
    Generic,
    Union,
    Callable,
)
from dataclasses import dataclass
import logging
import uuid
from pydantic import BaseModel, create_model
import re

from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.catalog import ErrorCodes, BaseError
from uno.domain.service import Service
from uno.domain.core import Entity
from uno.core.protocols import Repository
from uno.queries.filter_manager import UnoFilterManager, get_filter_manager

from .entities import ApiResource, EndpointConfig, HttpMethod
from .domain_repositories import (
    ApiResourceRepositoryProtocol,
    EndpointConfigRepositoryProtocol,
)


# Type variables
EntityT = TypeVar("EntityT", bound=Entity)
SchemaT = TypeVar("SchemaT", bound=BaseModel)
ResultT = TypeVar("ResultT")


class ApiResourceServiceProtocol(Service, Protocol):
    """
    Protocol for API resource management service.

    This protocol defines the interface for the service that manages API resources,
    including methods for creating, retrieving, updating, and deleting resources.
    """

    async def create_resource(
        self,
        name: str,
        path_prefix: str,
        entity_type_name: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Create a new API resource.

        Args:
            name: Name of the resource
            path_prefix: URL path prefix for all endpoints in this resource
            entity_type_name: Name of the entity type this resource operates on
            tags: Optional OpenAPI tags for all endpoints
            description: Optional description of the resource

        Returns:
            Result containing the created API resource
        """
        ...

    async def get_resource(self, resource_id: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by ID.

        Args:
            resource_id: The ID of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        ...

    async def get_resource_by_name(self, name: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by name.

        Args:
            name: The name of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        ...

    async def get_resource_by_path_prefix(
        self, path_prefix: str
    ) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by path prefix.

        Args:
            path_prefix: The path prefix of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        ...

    async def get_resources_by_entity_type(
        self, entity_type_name: str
    ) -> Result[List[ApiResource]]:
        """
        Get all API resources for a specific entity type.

        Args:
            entity_type_name: The name of the entity type

        Returns:
            Result containing a list of API resources for the entity type
        """
        ...

    async def list_resources(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Result[List[ApiResource]]:
        """
        List API resources, optionally filtered.

        Args:
            filters: Optional filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Result containing a list of API resources
        """
        ...

    async def update_resource(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Update an existing API resource.

        Args:
            resource: The API resource to update

        Returns:
            Result containing the updated API resource
        """
        ...

    async def delete_resource(self, resource_id: str) -> Result[bool]:
        """
        Delete an API resource.

        Args:
            resource_id: The ID of the resource to delete

        Returns:
            Result containing a boolean indicating success
        """
        ...

    async def add_endpoint_to_resource(
        self,
        resource_id: str,
        path: str,
        method: Union[str, HttpMethod],
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        operation_id: Optional[str] = None,
        deprecated: bool = False,
    ) -> Result[ApiResource]:
        """
        Add an endpoint to an API resource.

        Args:
            resource_id: The ID of the resource to add the endpoint to
            path: URL path for the endpoint
            method: HTTP method for the endpoint
            tags: Optional OpenAPI tags
            summary: Optional OpenAPI summary
            description: Optional OpenAPI description
            operation_id: Optional OpenAPI operationId
            deprecated: Whether the endpoint is deprecated

        Returns:
            Result containing the updated API resource
        """
        ...

    async def remove_endpoint_from_resource(
        self, resource_id: str, endpoint_id: str
    ) -> Result[ApiResource]:
        """
        Remove an endpoint from an API resource.

        Args:
            resource_id: The ID of the resource to remove the endpoint from
            endpoint_id: The ID of the endpoint to remove

        Returns:
            Result containing the updated API resource
        """
        ...


class EndpointFactoryServiceProtocol(Service, Protocol):
    """
    Protocol for endpoint factory service.

    This protocol defines the interface for the service that creates endpoints
    for repositories and entity types, automating the creation of standard CRUD
    endpoints.
    """

    async def create_crud_endpoints(
        self,
        resource_name: str,
        entity_type_name: str,
        path_prefix: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Create standard CRUD endpoints for an entity type.

        Args:
            resource_name: Name of the resource
            entity_type_name: Name of the entity type
            path_prefix: URL path prefix for all endpoints
            tags: Optional OpenAPI tags for all endpoints
            description: Optional description of the resource

        Returns:
            Result containing the created API resource with endpoints
        """
        ...

    async def register_repository(
        self,
        repository: Repository,
        entity_type: Type[EntityT],
        schema_type: Type[SchemaT],
        resource_name: Optional[str] = None,
        path_prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Register a repository for endpoint generation.

        Args:
            repository: The domain repository to use
            entity_type: The entity type the repository works with
            schema_type: The schema type for API requests/responses
            resource_name: Optional name of the resource (defaults to entity_type name)
            path_prefix: Optional URL path prefix (defaults to lowercase entity_type name)
            tags: Optional OpenAPI tags
            description: Optional description

        Returns:
            Result containing the created API resource with endpoints
        """
        ...


class RepositoryAdapterServiceProtocol(Service, Protocol):
    """
    Protocol for repository adapter service.

    This protocol defines the interface for the service that creates repository
    adapters, which bridge domain repositories with the API endpoint system.
    """

    def create_adapter(
        self,
        repository: Repository,
        entity_type: Type[EntityT],
        schema_type: Type[SchemaT],
        filter_manager: Optional[Any] = None,
        read_only: bool = False,
        batch_support: bool = False,
    ) -> Any:
        """
        Create a repository adapter for a domain repository.

        Args:
            repository: The domain repository to adapt
            entity_type: The entity type the repository works with
            schema_type: The schema type for API requests/responses
            filter_manager: Optional filter manager for query filtering
            read_only: Whether the adapter should be read-only
            batch_support: Whether the adapter should support batch operations

        Returns:
            A repository adapter instance
        """
        ...


@dataclass
class ApiResourceService(ApiResourceServiceProtocol):
    """
    Implementation of the API resource management service.

    This service manages API resources, including methods for creating, retrieving,
    updating, and deleting resources and their associated endpoints.
    """

    resource_repository: ApiResourceRepositoryProtocol
    endpoint_repository: EndpointConfigRepositoryProtocol
    logger: logging.Logger = None

    def __post_init__(self):
        """Initialize the service with default values."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)

    async def create_resource(
        self,
        name: str,
        path_prefix: str,
        entity_type_name: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Create a new API resource.

        Args:
            name: Name of the resource
            path_prefix: URL path prefix for all endpoints in this resource
            entity_type_name: Name of the entity type this resource operates on
            tags: Optional OpenAPI tags for all endpoints
            description: Optional description of the resource

        Returns:
            Result containing the created API resource
        """
        # Check if resource with same name already exists
        existing_result = await self.resource_repository.get_by_name(name)
        if existing_result.is_failure():
            return Failure(existing_result.error)

        if existing_result.value is not None:
            return Failure(
                BaseError(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"API resource with name '{name}' already exists",
                    context={"name": name},
                )
            )

        # Check if resource with same path prefix already exists
        existing_result = await self.resource_repository.get_by_path_prefix(path_prefix)
        if existing_result.is_failure():
            return Failure(existing_result.error)

        if existing_result.value is not None:
            return Failure(
                BaseError(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"API resource with path prefix '{path_prefix}' already exists",
                    context={"path_prefix": path_prefix},
                )
            )

        # Create a new resource
        resource_id = str(uuid.uuid4())
        resource = ApiResource(
            id=resource_id,
            name=name,
            path_prefix=path_prefix,
            entity_type_name=entity_type_name,
            tags=tags or [],
            description=description,
        )

        # Add to repository
        result = await self.resource_repository.add(resource)
        return result

    async def get_resource(self, resource_id: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by ID.

        Args:
            resource_id: The ID of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        return await self.resource_repository.get_by_id(resource_id)

    async def get_resource_by_name(self, name: str) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by name.

        Args:
            name: The name of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        return await self.resource_repository.get_by_name(name)

    async def get_resource_by_path_prefix(
        self, path_prefix: str
    ) -> Result[Optional[ApiResource]]:
        """
        Get an API resource by path prefix.

        Args:
            path_prefix: The path prefix of the resource to retrieve

        Returns:
            Result containing the API resource if found, or None if not found
        """
        return await self.resource_repository.get_by_path_prefix(path_prefix)

    async def get_resources_by_entity_type(
        self, entity_type_name: str
    ) -> Result[List[ApiResource]]:
        """
        Get all API resources for a specific entity type.

        Args:
            entity_type_name: The name of the entity type

        Returns:
            Result containing a list of API resources for the entity type
        """
        return await self.resource_repository.get_by_entity_type(entity_type_name)

    async def list_resources(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> Result[List[ApiResource]]:
        """
        List API resources, optionally filtered.

        Args:
            filters: Optional filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Result containing a list of API resources
        """
        options = {"pagination": {"limit": page_size, "offset": (page - 1) * page_size}}

        return await self.resource_repository.list(filters=filters, options=options)

    async def update_resource(self, resource: ApiResource) -> Result[ApiResource]:
        """
        Update an existing API resource.

        Args:
            resource: The API resource to update

        Returns:
            Result containing the updated API resource
        """
        # Check if resource exists
        existing_result = await self.resource_repository.get_by_id(resource.id)
        if existing_result.is_failure():
            return Failure(existing_result.error)

        if existing_result.value is None:
            return Failure(
                BaseError(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"API resource with ID '{resource.id}' not found",
                    context={"resource_id": resource.id},
                )
            )

        # Update resource
        return await self.resource_repository.update(resource)

    async def delete_resource(self, resource_id: str) -> Result[bool]:
        """
        Delete an API resource.

        Args:
            resource_id: The ID of the resource to delete

        Returns:
            Result containing a boolean indicating success
        """
        # Check if resource exists
        existing_result = await self.resource_repository.get_by_id(resource_id)
        if existing_result.is_failure():
            return Failure(existing_result.error)

        if existing_result.value is None:
            return Success(False)  # Not an error if resource doesn't exist

        # Delete resource
        return await self.resource_repository.delete(resource_id)

    async def add_endpoint_to_resource(
        self,
        resource_id: str,
        path: str,
        method: Union[str, HttpMethod],
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        operation_id: Optional[str] = None,
        deprecated: bool = False,
    ) -> Result[ApiResource]:
        """
        Add an endpoint to an API resource.

        Args:
            resource_id: The ID of the resource to add the endpoint to
            path: URL path for the endpoint
            method: HTTP method for the endpoint
            tags: Optional OpenAPI tags
            summary: Optional OpenAPI summary
            description: Optional OpenAPI description
            operation_id: Optional OpenAPI operationId
            deprecated: Whether the endpoint is deprecated

        Returns:
            Result containing the updated API resource
        """
        # Check if resource exists
        resource_result = await self.resource_repository.get_by_id(resource_id)
        if resource_result.is_failure():
            return Failure(resource_result.error)

        resource = resource_result.value
        if resource is None:
            return Failure(
                BaseError(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"API resource with ID '{resource_id}' not found",
                    context={"resource_id": resource_id},
                )
            )

        # Convert method to enum if needed
        if isinstance(method, str):
            try:
                method = HttpMethod(method.upper())
            except ValueError:
                return Failure(
                    BaseError(
                        code=ErrorCodes.VALIDATION_ERROR,
                        message=f"Invalid HTTP method: {method}",
                        context={"method": method},
                    )
                )

        # Create a new endpoint
        endpoint_id = str(uuid.uuid4())
        endpoint = EndpointConfig(
            id=endpoint_id,
            path=path,
            method=method,
            tags=tags or resource.tags.copy(),
            summary=summary,
            description=description,
            operation_id=operation_id,
            deprecated=deprecated,
        )

        # Set resource_id for indexing
        endpoint.resource_id = resource_id

        # Add endpoint to resource
        resource.add_endpoint(endpoint)

        # Save endpoint
        endpoint_result = await self.endpoint_repository.add(endpoint)
        if endpoint_result.is_failure():
            return Failure(endpoint_result.error)

        # Update resource
        return await self.resource_repository.update(resource)

    async def remove_endpoint_from_resource(
        self, resource_id: str, endpoint_id: str
    ) -> Result[ApiResource]:
        """
        Remove an endpoint from an API resource.

        Args:
            resource_id: The ID of the resource to remove the endpoint from
            endpoint_id: The ID of the endpoint to remove

        Returns:
            Result containing the updated API resource
        """
        # Check if resource exists
        resource_result = await self.resource_repository.get_by_id(resource_id)
        if resource_result.is_failure():
            return Failure(resource_result.error)

        resource = resource_result.value
        if resource is None:
            return Failure(
                BaseError(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"API resource with ID '{resource_id}' not found",
                    context={"resource_id": resource_id},
                )
            )

        # Check if endpoint exists
        endpoint_result = await self.endpoint_repository.get_by_id(endpoint_id)
        if endpoint_result.is_failure():
            return Failure(endpoint_result.error)

        endpoint = endpoint_result.value
        if endpoint is None:
            return Failure(
                BaseError(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"Endpoint configuration with ID '{endpoint_id}' not found",
                    context={"endpoint_id": endpoint_id},
                )
            )

        # Remove endpoint from resource
        for i, ep in enumerate(resource.endpoints):
            if ep.id == endpoint_id:
                resource.endpoints.pop(i)
                break

        # Delete endpoint
        await self.endpoint_repository.delete(endpoint_id)

        # Update resource
        return await self.resource_repository.update(resource)


@dataclass
class EndpointFactoryService(EndpointFactoryServiceProtocol):
    """
    Implementation of the endpoint factory service.

    This service creates endpoints for repositories and entity types, automating
    the creation of standard CRUD endpoints.
    """

    api_service: ApiResourceServiceProtocol
    filter_manager: Optional[Any] = None
    logger: logging.Logger = None

    def __post_init__(self):
        """Initialize the service with default values."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
        if self.filter_manager is None:
            self.filter_manager = get_filter_manager()

    async def create_crud_endpoints(
        self,
        resource_name: str,
        entity_type_name: str,
        path_prefix: str,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Create standard CRUD endpoints for an entity type.

        Args:
            resource_name: Name of the resource
            entity_type_name: Name of the entity type
            path_prefix: URL path prefix for all endpoints
            tags: Optional OpenAPI tags for all endpoints
            description: Optional description of the resource

        Returns:
            Result containing the created API resource with endpoints
        """
        # Create the resource
        resource_result = await self.api_service.create_resource(
            name=resource_name,
            path_prefix=path_prefix,
            entity_type_name=entity_type_name,
            tags=tags,
            description=description,
        )

        if resource_result.is_failure():
            return Failure(resource_result.error)

        resource = resource_result.value

        # Normalize path to remove trailing slash
        path_prefix = resource.path_prefix.rstrip("/")

        # Add standard CRUD endpoints
        # GET /{resource} - List
        list_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}",
            method=HttpMethod.GET,
            summary=f"List {resource.display_name_plural}",
            description=f"Get a list of {resource.display_name_plural}, with filtering and pagination",
            operation_id=f"list_{self._to_snake_case(resource.name)}",
        )

        if list_result.is_failure():
            return Failure(list_result.error)

        # GET /{resource}/{id} - Get by ID
        get_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}/{{id}}",
            method=HttpMethod.GET,
            summary=f"Get {resource.display_name} by ID",
            description=f"Get a single {resource.display_name} by its unique identifier",
            operation_id=f"get_{self._to_snake_case(resource.name)}",
        )

        if get_result.is_failure():
            return Failure(get_result.error)

        # POST /{resource} - Create
        create_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}",
            method=HttpMethod.POST,
            summary=f"Create {resource.display_name}",
            description=f"Create a new {resource.display_name}",
            operation_id=f"create_{self._to_snake_case(resource.name)}",
        )

        if create_result.is_failure():
            return Failure(create_result.error)

        # PATCH /{resource}/{id} - Update
        update_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}/{{id}}",
            method=HttpMethod.PATCH,
            summary=f"Update {resource.display_name}",
            description=f"Update an existing {resource.display_name}",
            operation_id=f"update_{self._to_snake_case(resource.name)}",
        )

        if update_result.is_failure():
            return Failure(update_result.error)

        # DELETE /{resource}/{id} - Delete
        delete_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}/{{id}}",
            method=HttpMethod.DELETE,
            summary=f"Delete {resource.display_name}",
            description=f"Delete an existing {resource.display_name}",
            operation_id=f"delete_{self._to_snake_case(resource.name)}",
        )

        if delete_result.is_failure():
            return Failure(delete_result.error)

        # PUT /{resource} - Batch import
        import_result = await self.api_service.add_endpoint_to_resource(
            resource_id=resource.id,
            path=f"{path_prefix}/batch",
            method=HttpMethod.PUT,
            summary=f"Batch import {resource.display_name_plural}",
            description=f"Import multiple {resource.display_name_plural} (create or update)",
            operation_id=f"import_{self._to_snake_case(resource.name)}",
        )

        if import_result.is_failure():
            return Failure(import_result.error)

        return Success(import_result.value)

    async def register_repository(
        self,
        repository: Repository,
        entity_type: Type[EntityT],
        schema_type: Type[SchemaT],
        resource_name: Optional[str] = None,
        path_prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> Result[ApiResource]:
        """
        Register a repository for endpoint generation.

        Args:
            repository: The domain repository to use
            entity_type: The entity type the repository works with
            schema_type: The schema type for API requests/responses
            resource_name: Optional name of the resource (defaults to entity_type name)
            path_prefix: Optional URL path prefix (defaults to lowercase entity_type name)
            tags: Optional OpenAPI tags
            description: Optional description

        Returns:
            Result containing the created API resource with endpoints
        """
        # Derive resource name and path prefix if not provided
        entity_type_name = entity_type.__name__
        if not resource_name:
            resource_name = entity_type_name

        if not path_prefix:
            path_prefix = f"/api/v1/{self._to_snake_case(entity_type_name)}"

        # Create resource with CRUD endpoints
        return await self.create_crud_endpoints(
            resource_name=resource_name,
            entity_type_name=entity_type_name,
            path_prefix=path_prefix,
            tags=tags,
            description=description,
        )

    def _to_snake_case(self, name: str) -> str:
        """
        Convert a string to snake_case.

        Args:
            name: The string to convert

        Returns:
            The string in snake_case
        """
        # Add underscore before uppercase letters and convert to lowercase
        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


@dataclass
class RepositoryAdapterService(RepositoryAdapterServiceProtocol):
    """
    Implementation of the repository adapter service.

    This service creates repository adapters, which bridge domain repositories
    with the API endpoint system.
    """

    logger: logging.Logger = None

    def __post_init__(self):
        """Initialize the service with default values."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)

    def create_adapter(
        self,
        repository: Repository,
        entity_type: Type[EntityT],
        schema_type: Type[SchemaT],
        filter_manager: Optional[Any] = None,
        read_only: bool = False,
        batch_support: bool = False,
    ) -> Any:
        """
        Create a repository adapter for a domain repository.

        Args:
            repository: The domain repository to adapt
            entity_type: The entity type the repository works with
            schema_type: The schema type for API requests/responses
            filter_manager: Optional filter manager for query filtering
            read_only: Whether the adapter should be read-only
            batch_support: Whether the adapter should support batch operations

        Returns:
            A repository adapter instance
        """
        from .repository_adapter import (
            RepositoryAdapter,
            ReadOnlyRepositoryAdapter,
            BatchRepositoryAdapter,
        )

        # Create a schema manager for the adapter
        schema_manager = self._create_schema_manager(entity_type, schema_type)

        # Create the appropriate adapter type
        if read_only:
            return ReadOnlyRepositoryAdapter(
                repository=repository,
                entity_type=entity_type,
                schema_manager=schema_manager,
                filter_manager=filter_manager,
            )
        elif batch_support:
            return BatchRepositoryAdapter(
                repository=repository,
                entity_type=entity_type,
                schema_manager=schema_manager,
                filter_manager=filter_manager,
            )
        else:
            return RepositoryAdapter(
                repository=repository,
                entity_type=entity_type,
                schema_manager=schema_manager,
                filter_manager=filter_manager,
            )

    def _create_schema_manager(
        self, entity_type: Type[EntityT], schema_type: Type[SchemaT]
    ) -> Any:
        """
        Create a schema manager for converting between entities and DTOs.

        Args:
            entity_type: The entity type
            schema_type: The schema type

        Returns:
            A schema manager instance
        """

        class SchemaManager:
            def create_entity(
                self, entity_cls: Type[EntityT], data: Dict[str, Any]
            ) -> EntityT:
                """Create an entity from data."""
                return entity_cls(**data)

            def entity_to_dto(self, entity: EntityT) -> SchemaT:
                """Convert entity to DTO."""
                # Use Pydantic's model_validate if available, otherwise construct manually
                if hasattr(schema_type, "model_validate"):
                    return schema_type.model_validate(entity)
                return schema_type(
                    **{k: getattr(entity, k) for k in entity.__dataclass_fields__}
                )

            def dto_to_entity(self, dto: SchemaT) -> EntityT:
                """Convert DTO to entity."""
                data = dto.model_dump()
                return entity_cls(**data)

        return SchemaManager()
