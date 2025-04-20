"""
Factory for creating API endpoints.

This module provides factory classes for creating API endpoints that integrate
with the domain entity framework.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from fastapi import (
    APIRouter,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from pydantic import BaseModel, create_model

from uno.core.errors.result import Result
from uno.domain.entity.service import CrudService, ServiceFactory

from . import EndpointProtocol, IdType, RequestModel, ResponseModel
from .base import BaseEndpoint, CrudEndpoint

__all__ = [
    "EndpointFactory",
    "CrudEndpointFactory",
]


class EndpointFactory:
    """
    Factory for creating API endpoints.

    This class provides methods for creating API endpoints that integrate
    with the domain entity framework.
    """

    @staticmethod
    def create_crud_endpoint(
        service: CrudService,
        create_model: Type[RequestModel],
        response_model: Type[ResponseModel],
        update_model: Optional[Type[RequestModel]] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        path: str = "",
        id_field: str = "id",
    ) -> CrudEndpoint[RequestModel, ResponseModel, IdType]:
        """
        Create a new CRUD endpoint.

        Args:
            service: The CrudService to use for operations.
            create_model: The Pydantic model for creation requests.
            response_model: The Pydantic model for responses.
            update_model: Optional separate model for update requests.
            router: Optional router to use. If not provided, a new one will be created.
            tags: Optional tags for OpenAPI documentation.
            path: The base path for routes, defaults to "".
            id_field: The name of the ID field in the entity.

        Returns:
            A new CrudEndpoint instance.
        """
        return CrudEndpoint(
            service=service,
            create_model=create_model,
            response_model=response_model,
            update_model=update_model,
            router=router,
            tags=tags,
            path=path,
            id_field=id_field,
        )


class CrudEndpointFactory(Generic[RequestModel, ResponseModel, IdType]):
    """
    Factory for creating CRUD endpoints.

    This class provides methods for creating CRUD endpoints that interact
    with a specific domain entity type.
    """

    def __init__(
        self,
        *,
        service_factory: ServiceFactory,
        entity_name: str,
        create_model: Type[RequestModel],
        response_model: Type[ResponseModel],
        update_model: Optional[Type[RequestModel]] = None,
        tags: list[str] | None = None,
        path_prefix: str = "/api",
    ):
        """
        Initialize a new CRUD endpoint factory.

        Args:
            service_factory: The ServiceFactory to use for creating services.
            entity_name: The name of the entity to create endpoints for.
            create_model: The Pydantic model for creation requests.
            response_model: The Pydantic model for responses.
            update_model: Optional separate model for update requests.
            tags: Optional tags for OpenAPI documentation.
            path_prefix: The prefix to add to all paths, defaults to "/api".
        """
        self.service_factory = service_factory
        self.entity_name = entity_name
        self.create_model = create_model
        self.response_model = response_model
        self.update_model = update_model
        self.tags = tags or [entity_name]
        self.path_prefix = path_prefix

    def create_endpoints(
        self,
        app: FastAPI,
        *,
        router: Optional[APIRouter] = None,
        path: str | None = None,
    ) -> CrudEndpoint[RequestModel, ResponseModel, IdType]:
        """
        Create and register CRUD endpoints for the entity.

        Args:
            app: The FastAPI application to register the endpoints with.
            router: Optional router to use. If not provided, a new one will be created.
            path: Optional path to use. If not provided, it will be generated from the entity name.

        Returns:
            The created CrudEndpoint instance.
        """
        # Create the service for the entity
        service = self.service_factory.create_crud_service(self.entity_name)

        # Generate the path if not provided
        if path is None:
            path = f"{self.path_prefix}/{self.entity_name.lower()}s"

        # Create the endpoint
        endpoint = CrudEndpoint(
            service=service,
            create_model=self.create_model,
            response_model=self.response_model,
            update_model=self.update_model,
            router=router,
            tags=self.tags,
            path=path,
        )

        # Register the endpoint with the FastAPI app
        endpoint.register(app)

        return endpoint

    @classmethod
    def from_schema(
        cls,
        *,
        service_factory: ServiceFactory,
        entity_name: str,
        schema: Type[BaseModel],
        tags: list[str] | None = None,
        path_prefix: str = "/api",
        exclude_fields: list[str] | None = None,
        readonly_fields: list[str] | None = None,
    ) -> "CrudEndpointFactory":
        """
        Create a CrudEndpointFactory from a Pydantic schema.

        This method automatically generates the create and update models
        from a response schema, making it easy to create CRUD endpoints
        from a single schema definition.

        Args:
            service_factory: The ServiceFactory to use for creating services.
            entity_name: The name of the entity to create endpoints for.
            schema: The Pydantic schema to use for generating models.
            tags: Optional tags for OpenAPI documentation.
            path_prefix: The prefix to add to all paths, defaults to "/api".
            exclude_fields: Fields to exclude from create/update models.
            readonly_fields: Fields that are readonly and should be excluded from create/update models.

        Returns:
            A new CrudEndpointFactory instance.
        """
        # Set default values
        exclude_fields = exclude_fields or []
        readonly_fields = readonly_fields or []

        # Combine all fields to exclude
        all_exclude = set(
            exclude_fields + readonly_fields + ["id", "created_at", "updated_at"]
        )

        # Generate field definitions for create model
        create_fields = {}
        for name, field in schema.__annotations__.items():
            if name not in all_exclude:
                create_fields[name] = (field, ...)

        # Generate field definitions for update model
        update_fields = {}
        for name, field in schema.__annotations__.items():
            if name not in all_exclude:
                update_fields[name] = (Optional[field], None)

        # Create models
        create_model_name = f"Create{entity_name}Request"
        update_model_name = f"Update{entity_name}Request"

        create_model_cls = create_model(create_model_name, **create_fields)
        update_model_cls = create_model(update_model_name, **update_fields)

        # Return factory
        return cls(
            service_factory=service_factory,
            entity_name=entity_name,
            create_model=create_model_cls,
            response_model=schema,
            update_model=update_model_cls,
            tags=tags,
            path_prefix=path_prefix,
        )
