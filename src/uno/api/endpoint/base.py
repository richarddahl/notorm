"""
Base endpoint classes for the unified endpoint framework.

This module provides the foundation for creating standardized API endpoints
that integrate with the domain entity framework.
"""

from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
)

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel

from uno.core.errors.result import Result, Success
from uno.domain.entity.service import ApplicationService, CrudService, DomainService

from . import EndpointProtocol, IdType, RequestModel, ResponseModel

__all__ = [
    "BaseEndpoint",
    "CrudEndpoint",
    "QueryEndpoint",
    "CommandEndpoint",
]


class BaseEndpoint(Generic[RequestModel, ResponseModel, IdType]):
    """
    Base class for all API endpoints.

    This class provides the core functionality for registering routes with FastAPI
    and handling responses from domain services.
    """

    def __init__(
        self,
        *,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
    ):
        """
        Initialize a new endpoint instance.

        Args:
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
        """
        self.router = router or APIRouter()
        self.tags = tags or []

    def register(self, app: FastAPI, prefix: str = "") -> None:
        """
        Register this endpoint with a FastAPI application.

        Args:
            app: The FastAPI application to register with.
            prefix: An optional URL prefix to add to all routes.
        """
        app.include_router(self.router, prefix=prefix, tags=self.tags)

    def get_router(self) -> APIRouter:
        """
        Get the router for this endpoint.

        Returns:
            The APIRouter instance used by this endpoint.
        """
        return self.router

    def handle_result(
        self,
        result: Result[ResponseModel],
        *,
        success_status: int = status.HTTP_200_OK,
    ) -> ResponseModel:
        """
        Handle a Result object from a domain service.

        This method provides standardized error handling for domain service results,
        converting domain errors to appropriate HTTP responses.

        Args:
            result: The Result object from a domain service.
            success_status: The HTTP status code to use for successful responses.

        Returns:
            The value from a successful Result.

        Raises:
            HTTPException: If the Result contains an error.
        """
        if isinstance(result, Success):
            return result.value

        # Handle specific error types
        error = cast(Error, result).error
        status_code = status.HTTP_400_BAD_REQUEST

        # Map domain errors to HTTP status codes
        if hasattr(error, "status_code"):
            status_code = error.status_code
        elif hasattr(error, "code"):
            error_code = error.code
            if error_code.startswith("NOT_FOUND"):
                status_code = status.HTTP_404_NOT_FOUND
            elif error_code.startswith("UNAUTHORIZED"):
                status_code = status.HTTP_401_UNAUTHORIZED
            elif error_code.startswith("FORBIDDEN"):
                status_code = status.HTTP_403_FORBIDDEN
            elif error_code.startswith("CONFLICT"):
                status_code = status.HTTP_409_CONFLICT

        raise HTTPException(
            status_code=status_code,
            detail={"message": str(error), "code": getattr(error, "code", "ERROR")},
        )


class CrudEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Base class for CRUD endpoints that work with domain entities.

    This class provides standardized endpoint creation for common CRUD operations,
    integrating with CrudService from the domain entity framework.
    """

    def __init__(
        self,
        *,
        service: CrudService,
        create_model: Type[RequestModel],
        response_model: Type[ResponseModel],
        update_model: Optional[Type[RequestModel]] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        path: str = "",
        id_field: str = "id",
    ):
        """
        Initialize a new CRUD endpoint instance.

        Args:
            service: The CrudService to use for operations.
            create_model: The Pydantic model for creation requests.
            response_model: The Pydantic model for responses.
            update_model: Optional separate model for update requests.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The base path for routes, defaults to "".
            id_field: The name of the ID field in the entity.
        """
        super().__init__(router=router, tags=tags)
        self.service = service
        self.create_model = create_model
        self.response_model = response_model
        self.update_model = update_model or create_model
        self.path = path
        self.id_field = id_field

        # Register the default routes
        self._register_routes()

    def _register_routes(self) -> None:
        """Register the default CRUD routes."""
        self._register_create_route()
        self._register_get_route()
        self._register_list_route()
        self._register_update_route()
        self._register_delete_route()

    def _register_create_route(self) -> None:
        """Register the route for creating a new entity."""

        @self.router.post(
            self.path,
            response_model=self.response_model,
            status_code=status.HTTP_201_CREATED,
        )
        async def create(data: self.create_model) -> ResponseModel:
            result = await self.service.create(data)
            return self.handle_result(result, success_status=status.HTTP_201_CREATED)

    def _register_get_route(self) -> None:
        """Register the route for retrieving a single entity."""

        @self.router.get(
            f"{self.path}/{{id}}",
            response_model=self.response_model,
        )
        async def get(id: IdType) -> ResponseModel:
            result = await self.service.get_by_id(id)
            return self.handle_result(result)

    def _register_list_route(self) -> None:
        """Register the route for listing entities."""

        @self.router.get(
            self.path,
            response_model=list[self.response_model],
        )
        async def list_entities() -> list[ResponseModel]:
            result = await self.service.get_all()
            return self.handle_result(result)

    def _register_update_route(self) -> None:
        """Register the route for updating an entity."""

        @self.router.put(
            f"{self.path}/{{id}}",
            response_model=self.response_model,
        )
        async def update(id: IdType, data: self.update_model) -> ResponseModel:
            result = await self.service.update(id, data)
            return self.handle_result(result)

    def _register_delete_route(self) -> None:
        """Register the route for deleting an entity."""

        @self.router.delete(
            f"{self.path}/{{id}}",
            status_code=status.HTTP_204_NO_CONTENT,
        )
        async def delete(id: IdType) -> None:
            result = await self.service.delete(id)
            if isinstance(result, Success):
                return None
            self.handle_result(result)  # Will raise HTTPException


class QueryEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Base class for query endpoints.

    This class provides standardized endpoint creation for query operations,
    integrating with domain services that follow the CQRS pattern.
    """

    def __init__(
        self,
        *,
        service: Union[ApplicationService, DomainService],
        response_model: Type[ResponseModel],
        query_model: Optional[Type[RequestModel]] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        path: str = "",
        method: str = "get",
    ):
        """
        Initialize a new query endpoint instance.

        Args:
            service: The service to use for query operations.
            response_model: The Pydantic model for responses.
            query_model: Optional model for query parameters.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The path for the query endpoint.
            method: The HTTP method to use (default: "get").
        """
        super().__init__(router=router, tags=tags)
        self.service = service
        self.response_model = response_model
        self.query_model = query_model
        self.path = path
        self.method = method.lower()

        # Register the query route
        self._register_query_route()

    def _register_query_route(self) -> None:
        """Register the route for the query operation."""
        handler = getattr(self.router, self.method)

        if self.query_model:

            @handler(
                self.path,
                response_model=self.response_model,
            )
            async def query(data: self.query_model) -> ResponseModel:
                result = await self.service.execute(data)
                return self.handle_result(result)

        else:

            @handler(
                self.path,
                response_model=self.response_model,
            )
            async def query() -> ResponseModel:
                result = await self.service.execute()
                return self.handle_result(result)


class CommandEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Base class for command endpoints.

    This class provides standardized endpoint creation for command operations,
    integrating with domain services that follow the CQRS pattern.
    """

    def __init__(
        self,
        *,
        service: Union[ApplicationService, DomainService],
        command_model: Type[RequestModel],
        response_model: Optional[Type[ResponseModel]] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        path: str = "",
        method: str = "post",
    ):
        """
        Initialize a new command endpoint instance.

        Args:
            service: The service to use for command operations.
            command_model: The Pydantic model for command data.
            response_model: Optional model for command responses.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The path for the command endpoint.
            method: The HTTP method to use (default: "post").
        """
        super().__init__(router=router, tags=tags)
        self.service = service
        self.command_model = command_model
        self.response_model = response_model
        self.path = path
        self.method = method.lower()

        # Register the command route
        self._register_command_route()

    def _register_command_route(self) -> None:
        """Register the route for the command operation."""
        handler = getattr(self.router, self.method)

        if self.response_model:

            @handler(
                self.path,
                response_model=self.response_model,
                status_code=(
                    status.HTTP_201_CREATED
                    if self.method == "post"
                    else status.HTTP_200_OK
                ),
            )
            async def command(data: self.command_model) -> ResponseModel:
                result = await self.service.execute(data)
                success_status = (
                    status.HTTP_201_CREATED
                    if self.method == "post"
                    else status.HTTP_200_OK
                )
                return self.handle_result(result, success_status=success_status)

        else:

            @handler(
                self.path,
                status_code=status.HTTP_204_NO_CONTENT,
            )
            async def command(data: self.command_model) -> None:
                result = await self.service.execute(data)
                if isinstance(result, Success):
                    return None
                self.handle_result(result)  # Will raise HTTPException
