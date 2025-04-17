"""
API integration layer for the Uno framework.

This module provides the integration between the application service layer
and the API layer, connecting HTTP endpoints to application services.
"""

import logging
from enum import Enum
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    cast,
    Union,
    Callable,
    get_type_hints,
)

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, create_model

from uno.domain.application_services import (
    ApplicationService,
    EntityService,
    AggregateService,
    ServiceContext,
    ServiceRegistry,
    get_service_registry,
)
from uno.domain.models import Entity, AggregateRoot
from uno.domain.cqrs import CommandResult, QueryResult
from uno.core.errors.base import AuthorizationError, ValidationError


# Type variables
T = TypeVar("T")
EntityT = TypeVar("EntityT", bound=Entity)
AggregateT = TypeVar("AggregateT", bound=AggregateRoot)


class ApiErrorCode(str, Enum):
    """API error codes."""

    BAD_REQUEST = "API-0001"
    UNAUTHORIZED = "API-0002"
    FORBIDDEN = "API-0003"
    NOT_FOUND = "API-0004"
    CONFLICT = "API-0005"
    INTERNAL_ERROR = "API-0006"
    VALIDATION_ERROR = "API-0007"


class ApiError(BaseModel):
    """API error response model."""

    code: ApiErrorCode
    message: str
    details: Optional[Dict[str, Any]] = None


class PaginationParams(BaseModel):
    """Pagination parameters."""

    page: int = Field(1, description="Page number (1-indexed)", ge=1)
    page_size: int = Field(50, description="Number of items per page", ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""

    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool


class ContextProvider:
    """
    Provider for service context.

    This class provides the service context for API operations,
    extracting information from the HTTP request.
    """

    async def __call__(self, request: Request) -> ServiceContext:
        """
        Create a service context from the HTTP request.

        Args:
            request: The HTTP request

        Returns:
            Service context
        """
        # Extract user ID from request
        user_id = self._get_user_id(request)

        # Check if user is authenticated
        is_authenticated = user_id is not None

        # Extract tenant ID from request
        tenant_id = self._get_tenant_id(request)

        # Get permissions from request
        permissions = self._get_permissions(request)

        # Create request metadata
        metadata = {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "path": request.url.path,
            "method": request.method,
        }

        # Create the service context
        return ServiceContext(
            user_id=user_id,
            tenant_id=tenant_id,
            is_authenticated=is_authenticated,
            permissions=permissions,
            request_metadata=metadata,
        )

    def _get_user_id(self, request: Request) -> Optional[str]:
        """
        Get the user ID from the request.

        This method can be overridden by subclasses to extract
        the user ID from the request.

        Args:
            request: The HTTP request

        Returns:
            User ID if authenticated, None otherwise
        """
        # Default implementation - can be overridden
        return getattr(request.state, "user_id", None)

    def _get_tenant_id(self, request: Request) -> Optional[str]:
        """
        Get the tenant ID from the request.

        This method can be overridden by subclasses to extract
        the tenant ID from the request.

        Args:
            request: The HTTP request

        Returns:
            Tenant ID if available, None otherwise
        """
        # Default implementation - can be overridden
        return getattr(request.state, "tenant_id", None)

    def _get_permissions(self, request: Request) -> List[str]:
        """
        Get the permissions from the request.

        This method can be overridden by subclasses to extract
        permissions from the request.

        Args:
            request: The HTTP request

        Returns:
            List of permission strings
        """
        # Default implementation - can be overridden
        return getattr(request.state, "permissions", [])


# Default context provider
default_context_provider = ContextProvider()


def get_context(request: Request) -> ServiceContext:
    """
    Dependency for getting the service context.

    Args:
        request: The HTTP request

    Returns:
        Service context
    """
    return default_context_provider(request)


class ApiEndpoint:
    """
    Base class for API endpoints.

    API endpoints connect HTTP endpoints to application services,
    handling conversion between HTTP and application service formats.
    """

    def __init__(
        self,
        service: ApplicationService,
        router: APIRouter,
        path: str,
        response_model: Optional[Type[BaseModel]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the API endpoint.

        Args:
            service: The application service
            router: The FastAPI router
            path: The endpoint path
            response_model: Optional response model
            logger: Optional logger instance
        """
        self.service = service
        self.router = router
        self.path = path
        self.response_model = response_model
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def handle_result(
        self,
        result: Union[CommandResult, QueryResult],
        fields: Optional[List[str]] = None,
        stream_response: bool = False,
    ) -> Union[Response, Dict[str, Any]]:
        """
        Handle a command or query result.

        This method converts a command or query result to an HTTP response.

        Args:
            result: The command or query result
            fields: Optional list of fields to include in the response (partial response)
            stream_response: Whether to return a streaming response

        Returns:
            HTTP response or data
        """
        if result.is_success:
            # Return the output
            if hasattr(result, "output") and result.output is not None:
                # Handle streaming response if requested and supported
                if (
                    stream_response
                    and isinstance(result.output, (list, tuple))
                    and hasattr(result.output, "__iter__")
                ):
                    from fastapi.responses import StreamingResponse
                    import json

                    async def stream_results():
                        # Initial response with content type header
                        yield '{"type":"meta","total_count":null,"streaming":true}\n'

                        count = 0
                        # Stream entities
                        for item in result.output:
                            # Convert item to dict if possible
                            if hasattr(item, "to_dict"):
                                item_dict = item.to_dict()
                            else:
                                item_dict = item

                            # Apply field selection if specified
                            if fields:
                                item_dict = {
                                    k: v for k, v in item_dict.items() if k in fields
                                }

                            # Stream as newline-delimited JSON
                            yield f"{json.dumps(item_dict)}\n"
                            count += 1

                            # Add progress updates every 1000 items
                            if count % 1000 == 0:
                                yield f'{{"type":"progress","count":{count}}}\n'

                        # Final count
                        yield f'{{"type":"end","total_count":{count}}}\n'

                    # Return streaming response
                    return StreamingResponse(
                        stream_results(), media_type="application/x-ndjson"
                    )

                # Convert output to dict if it's an entity
                if isinstance(result.output, (Entity, AggregateRoot)) and hasattr(
                    result.output, "to_dict"
                ):
                    entity_dict = result.output.to_dict()
                    # Apply field selection if specified
                    if fields:
                        return {k: v for k, v in entity_dict.items() if k in fields}
                    return entity_dict

                # Handle paginated results
                elif hasattr(result.output, "items") and hasattr(
                    result.output, "total"
                ):
                    # Convert entity items to dicts with field selection
                    items = []
                    for item in result.output.items:
                        if hasattr(item, "to_dict"):
                            item_dict = item.to_dict()
                            # Apply field selection if specified
                            if fields:
                                item_dict = {
                                    k: v for k, v in item_dict.items() if k in fields
                                }
                            items.append(item_dict)
                        else:
                            items.append(item)

                    # Create paginated response
                    return {
                        "items": items,
                        "total": result.output.total,
                        "page": result.output.page,
                        "page_size": result.output.page_size,
                        "total_pages": result.output.total_pages,
                        "has_next": result.output.has_next,
                        "has_previous": result.output.has_previous,
                    }

                # Handle lists of entities
                elif isinstance(result.output, list):
                    items = []
                    for item in result.output:
                        if hasattr(item, "to_dict"):
                            item_dict = item.to_dict()
                            # Apply field selection if specified
                            if fields:
                                item_dict = {
                                    k: v for k, v in item_dict.items() if k in fields
                                }
                            items.append(item_dict)
                        else:
                            items.append(item)
                    return items

                # Return output as is
                return result.output

            # Return empty response for success without output
            return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=None)
        else:
            # Determine error code and status
            error_code = ApiErrorCode.BAD_REQUEST
            status_code = status.HTTP_400_BAD_REQUEST

            if hasattr(result, "error_code"):
                if result.error_code == "AUTHORIZATION_ERROR":
                    error_code = ApiErrorCode.UNAUTHORIZED
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif result.error_code == "PERMISSION_ERROR":
                    error_code = ApiErrorCode.FORBIDDEN
                    status_code = status.HTTP_403_FORBIDDEN
                elif result.error_code == "ENTITY_NOT_FOUND":
                    error_code = ApiErrorCode.NOT_FOUND
                    status_code = status.HTTP_404_NOT_FOUND
                elif result.error_code == "CONCURRENCY_ERROR":
                    error_code = ApiErrorCode.CONFLICT
                    status_code = status.HTTP_409_CONFLICT
                elif result.error_code == "VALIDATION_ERROR":
                    error_code = ApiErrorCode.VALIDATION_ERROR
                    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
                elif result.error_code and "ERROR" in result.error_code:
                    error_code = ApiErrorCode.INTERNAL_ERROR
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

            # Create error response
            error = ApiError(
                code=error_code,
                message=result.error if hasattr(result, "error") else "Unknown error",
                details={},
            )

            # Return error response
            return JSONResponse(status_code=status_code, content=error.dict())

    def handle_exception(self, exception: Exception) -> Response:
        """
        Handle an exception.

        This method converts an exception to an HTTP response.

        Args:
            exception: The exception

        Returns:
            HTTP response
        """
        # Log the exception
        self.logger.exception("Error in API endpoint")

        # Determine error code and status
        error_code = ApiErrorCode.INTERNAL_ERROR
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        if isinstance(exception, (AuthorizationError, PermissionError)):
            error_code = ApiErrorCode.FORBIDDEN
            status_code = status.HTTP_403_FORBIDDEN
        elif isinstance(exception, ValidationError):
            error_code = ApiErrorCode.VALIDATION_ERROR
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif isinstance(exception, HTTPException):
            error_code = ApiErrorCode.BAD_REQUEST
            status_code = exception.status_code

            # Refine error code based on status
            if status_code == 401:
                error_code = ApiErrorCode.UNAUTHORIZED
            elif status_code == 403:
                error_code = ApiErrorCode.FORBIDDEN
            elif status_code == 404:
                error_code = ApiErrorCode.NOT_FOUND
            elif status_code == 409:
                error_code = ApiErrorCode.CONFLICT
            elif status_code == 422:
                error_code = ApiErrorCode.VALIDATION_ERROR

        # Create error response
        error = ApiError(code=error_code, message=str(exception), details={})

        # Return error response
        return JSONResponse(status_code=status_code, content=error.dict())


class EntityApi(Generic[EntityT]):
    """
    API endpoints for entity operations.

    This class provides standard CRUD endpoints for entities.
    """

    def __init__(
        self,
        entity_type: Type[EntityT],
        service: EntityService[EntityT],
        router: APIRouter,
        prefix: str,
        tags: List[str],
        create_dto: Optional[Type[BaseModel]] = None,
        update_dto: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the entity API.

        Args:
            entity_type: The entity type
            service: The entity service
            router: The FastAPI router
            prefix: The API route prefix
            tags: API tags for documentation
            create_dto: Optional DTO for create operations
            update_dto: Optional DTO for update operations
            response_model: Optional response model
            logger: Optional logger instance
        """
        self.entity_type = entity_type
        self.service = service
        self.router = router
        self.prefix = prefix
        self.tags = tags
        self.create_dto = create_dto
        self.update_dto = update_dto
        self.response_model = response_model
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

        # Register routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register API routes."""

        # Create endpoint
        @self.router.post(
            f"{self.prefix}",
            response_model=self.response_model,
            tags=self.tags,
            status_code=status.HTTP_201_CREATED,
        )
        async def create_entity(
            data: self.create_dto if self.create_dto else Dict[str, Any],
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Convert DTO to dict if needed
                entity_data = data.dict() if hasattr(data, "dict") else data

                # Execute the create operation
                result = await self.service.create(entity_data, context)

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)

        # Get by ID endpoint
        @self.router.get(
            f"{self.prefix}/{{entity_id}}",
            response_model=self.response_model,
            tags=self.tags,
        )
        async def get_entity_by_id(
            entity_id: str,
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Execute the get operation
                result = await self.service.get_by_id(entity_id, context)

                # Handle the result
                response = self._handle_result(result)

                # Return 404 if entity not found
                if result.is_success and result.output is None:
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={
                            "code": "NOT_FOUND",
                            "message": f"{self.entity_type.__name__} not found",
                        },
                    )

                return response
            except Exception as e:
                return self._handle_exception(e)

        # Update endpoint
        @self.router.put(
            f"{self.prefix}/{{entity_id}}",
            response_model=self.response_model,
            tags=self.tags,
        )
        async def update_entity(
            entity_id: str,
            data: self.update_dto if self.update_dto else Dict[str, Any],
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Convert DTO to dict if needed
                entity_data = data.dict() if hasattr(data, "dict") else data

                # Execute the update operation
                result = await self.service.update(entity_id, entity_data, context)

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)

        # Delete endpoint
        @self.router.delete(
            f"{self.prefix}/{{entity_id}}",
            tags=self.tags,
            status_code=status.HTTP_204_NO_CONTENT,
        )
        async def delete_entity(
            entity_id: str,
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Execute the delete operation
                result = await self.service.delete(entity_id, context)

                # Handle the result
                response = self._handle_result(result)

                # Return 204 for successful deletion
                if result.is_success and result.output:
                    return Response(status_code=status.HTTP_204_NO_CONTENT)

                return response
            except Exception as e:
                return self._handle_exception(e)

        # List endpoint
        @self.router.get(
            f"{self.prefix}",
            response_model=List[self.response_model] if self.response_model else None,
            tags=self.tags,
        )
        async def list_entities(
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Execute the list operation
                result = await self.service.list(context=context)

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)

        # Paginated list endpoint
        @self.router.get(
            f"{self.prefix}/paginated",
            response_model=(
                PaginatedResponse[self.response_model] if self.response_model else None
            ),
            tags=self.tags,
        )
        async def paginated_list_entities(
            pagination: PaginationParams = Depends(),
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Execute the paginated list operation
                result = await self.service.paginated_list(
                    page=pagination.page,
                    page_size=pagination.page_size,
                    context=context,
                )

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)

    def _handle_result(
        self, result: Union[CommandResult, QueryResult]
    ) -> Union[Response, Dict[str, Any]]:
        """
        Handle a command or query result.

        Args:
            result: The command or query result

        Returns:
            HTTP response or data
        """
        endpoint = ApiEndpoint(
            service=self.service,
            router=self.router,
            path=self.prefix,
            response_model=self.response_model,
            logger=self.logger,
        )
        return endpoint.handle_result(result)

    def _handle_exception(self, exception: Exception) -> Response:
        """
        Handle an exception.

        Args:
            exception: The exception

        Returns:
            HTTP response
        """
        endpoint = ApiEndpoint(
            service=self.service,
            router=self.router,
            path=self.prefix,
            response_model=self.response_model,
            logger=self.logger,
        )
        return endpoint.handle_exception(exception)


class AggregateApi(EntityApi[AggregateT], Generic[AggregateT]):
    """
    API endpoints for aggregate operations.

    This class extends entity API with aggregate-specific operations.
    """

    def __init__(
        self,
        aggregate_type: Type[AggregateT],
        service: AggregateService[AggregateT],
        router: APIRouter,
        prefix: str,
        tags: List[str],
        create_dto: Optional[Type[BaseModel]] = None,
        update_dto: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the aggregate API.

        Args:
            aggregate_type: The aggregate type
            service: The aggregate service
            router: The FastAPI router
            prefix: The API route prefix
            tags: API tags for documentation
            create_dto: Optional DTO for create operations
            update_dto: Optional DTO for update operations
            response_model: Optional response model
            logger: Optional logger instance
        """
        super().__init__(
            entity_type=aggregate_type,
            service=service,
            router=router,
            prefix=prefix,
            tags=tags,
            create_dto=create_dto,
            update_dto=update_dto,
            response_model=response_model,
            logger=logger,
        )

        # Register additional aggregate routes
        self._register_aggregate_routes()

    def _register_aggregate_routes(self) -> None:
        """Register aggregate-specific API routes."""

        # Override update endpoint to handle versioning
        @self.router.put(
            f"{self.prefix}/{{entity_id}}",
            response_model=self.response_model,
            tags=self.tags,
        )
        async def update_aggregate(
            entity_id: str,
            data: self.update_dto if self.update_dto else Dict[str, Any],
            version: int,
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Convert DTO to dict if needed
                entity_data = data.dict() if hasattr(data, "dict") else data

                # Execute the update operation
                result = await self.service.update(
                    entity_id, version, entity_data, context
                )

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)


class ServiceApiRegistry:
    """
    Registry for API endpoints.

    This registry provides a central place to register and retrieve API endpoints.
    """

    def __init__(
        self, router: APIRouter, service_registry: Optional[ServiceRegistry] = None
    ):
        """
        Initialize the API registry.

        Args:
            router: The FastAPI router
            service_registry: Optional service registry
        """
        self.router = router
        self.service_registry = service_registry or get_service_registry()
        self._apis: Dict[str, Union[EntityApi, AggregateApi]] = {}
        self._logger = logging.getLogger(__name__)

    def register_entity_api(
        self,
        entity_type: Type[EntityT],
        prefix: str,
        tags: List[str],
        service_name: Optional[str] = None,
        create_dto: Optional[Type[BaseModel]] = None,
        update_dto: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> EntityApi[EntityT]:
        """
        Register an entity API.

        Args:
            entity_type: The entity type
            prefix: The API route prefix
            tags: API tags for documentation
            service_name: Optional service name (defaults to entity type name + "Service")
            create_dto: Optional DTO for create operations
            update_dto: Optional DTO for update operations
            response_model: Optional response model

        Returns:
            Entity API
        """
        # Get service name if not provided
        if service_name is None:
            service_name = f"{entity_type.__name__}Service"

        # Get the service
        service = self.service_registry.get(service_name)

        # Create the API
        api = EntityApi(
            entity_type=entity_type,
            service=service,
            router=self.router,
            prefix=prefix,
            tags=tags,
            create_dto=create_dto,
            update_dto=update_dto,
            response_model=response_model,
        )

        # Register the API
        api_name = f"{entity_type.__name__}Api"
        self._apis[api_name] = api
        self._logger.debug(f"Registered entity API: {api_name}")

        return api

    def register_aggregate_api(
        self,
        aggregate_type: Type[AggregateT],
        prefix: str,
        tags: List[str],
        service_name: Optional[str] = None,
        create_dto: Optional[Type[BaseModel]] = None,
        update_dto: Optional[Type[BaseModel]] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> AggregateApi[AggregateT]:
        """
        Register an aggregate API.

        Args:
            aggregate_type: The aggregate type
            prefix: The API route prefix
            tags: API tags for documentation
            service_name: Optional service name (defaults to aggregate type name + "Service")
            create_dto: Optional DTO for create operations
            update_dto: Optional DTO for update operations
            response_model: Optional response model

        Returns:
            Aggregate API
        """
        # Get service name if not provided
        if service_name is None:
            service_name = f"{aggregate_type.__name__}Service"

        # Get the service
        service = self.service_registry.get(service_name)

        # Create the API
        api = AggregateApi(
            aggregate_type=aggregate_type,
            service=service,
            router=self.router,
            prefix=prefix,
            tags=tags,
            create_dto=create_dto,
            update_dto=update_dto,
            response_model=response_model,
        )

        # Register the API
        api_name = f"{aggregate_type.__name__}Api"
        self._apis[api_name] = api
        self._logger.debug(f"Registered aggregate API: {api_name}")

        return api

    def get_api(self, name: str) -> Union[EntityApi, AggregateApi]:
        """
        Get an API by name.

        Args:
            name: API name

        Returns:
            API

        Raises:
            KeyError: If API not found
        """
        if name not in self._apis:
            raise KeyError(f"API not found: {name}")

        return self._apis[name]


# Utility functions for creating DTOs


def create_dto_for_entity(
    entity_type: Type[EntityT],
    name: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    optional: Optional[List[str]] = None,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> Type[BaseModel]:
    """
    Create a DTO model for an entity.

    Args:
        entity_type: The entity type
        name: The DTO model name
        include: Optional list of fields to include
        exclude: Optional list of fields to exclude
        optional: Optional list of fields to make optional
        additional_fields: Optional additional fields

    Returns:
        DTO model
    """
    # Get entity fields
    entity_fields = {}
    for field_name, field_type in get_type_hints(entity_type).items():
        # Skip private fields
        if field_name.startswith("_"):
            continue

        # Skip excluded fields
        if exclude and field_name in exclude:
            continue

        # Only include specified fields if include is provided
        if include and field_name not in include:
            continue

        # Add field to DTO
        entity_fields[field_name] = (
            field_type,
            ... if optional is None or field_name not in optional else None,
        )

    # Add additional fields
    if additional_fields:
        entity_fields.update(additional_fields)

    # Create and return the DTO model
    return create_model(name, **entity_fields)


def create_response_model_for_entity(
    entity_type: Type[EntityT],
    name: str,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> Type[BaseModel]:
    """
    Create a response model for an entity.

    Args:
        entity_type: The entity type
        name: The response model name
        include: Optional list of fields to include
        exclude: Optional list of fields to exclude
        additional_fields: Optional additional fields

    Returns:
        Response model
    """
    # Use create_dto_for_entity with no optional fields
    return create_dto_for_entity(
        entity_type=entity_type,
        name=name,
        include=include,
        exclude=exclude,
        optional=None,
        additional_fields=additional_fields,
    )
