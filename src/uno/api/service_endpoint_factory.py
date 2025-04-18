"""
Endpoint factory for creating FastAPI endpoints from domain services.

This module provides a factory that creates standardized FastAPI endpoints from domain services,
providing a consistent integration between domain-driven design and API endpoints.
"""

import logging
import inspect
import traceback
from typing import Dict, Type, List, Optional, Any, Union, Callable, Set, TypeVar, Generic, get_type_hints

from pydantic import BaseModel, create_model
from fastapi import FastAPI, APIRouter, Depends, Path, Query, Body, HTTPException, status
from fastapi.responses import JSONResponse

from uno.api.endpoint import (
    UnoEndpoint,
    CreateEndpoint,
    ViewEndpoint,
    ListEndpoint,
    UpdateEndpoint,
    DeleteEndpoint,
)
from uno.core.errors.result import Result, Success, Failure
from uno.domain.unified_services import (
    DomainService, ReadOnlyDomainService, EntityService, AggregateService,
    DomainServiceFactory, get_service_factory
)
from uno.api.service_endpoint_adapter import (
    DomainServiceAdapter, EntityServiceAdapter, convert_to_pydantic_model
)
from uno.dependencies.fastapi import get_service, inject_dependency

# Type variables
T = TypeVar('T')
InputT = TypeVar('InputT')
OutputT = TypeVar('OutputT')

# Configure logger
logger = logging.getLogger(__name__)


class DomainServiceEndpointFactory:
    """
    Factory for creating FastAPI endpoints from domain services.
    
    This class provides methods to create endpoints from different types of domain services,
    ensuring a consistent API interface for domain-driven design patterns.
    """
    
    def __init__(
        self,
        service_factory: Optional[DomainServiceFactory] = None,
        error_handler: Optional[Callable[[Result], None]] = None
    ):
        """
        Initialize the endpoint factory.
        
        Args:
            service_factory: Optional domain service factory for creating services
            error_handler: Optional error handler for Result objects
        """
        self.service_factory = service_factory or get_service_factory()
        self.error_handler = error_handler
        
    def create_entity_service_endpoints(
        self,
        app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        entity_type: Type[T] = None,
        path_prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        input_model: Optional[Type[BaseModel]] = None,
        output_model: Optional[Type[BaseModel]] = None,
        endpoints: Optional[List[str]] = None,
        include_in_schema: bool = True,
        dependencies: Optional[List[Depends]] = None,
        status_codes: Optional[Dict[str, int]] = None,
        **kwargs
    ) -> Dict[str, UnoEndpoint]:
        """
        Create endpoints for an entity service.
        
        Args:
            app: FastAPI app to add endpoints to
            router: Optional router to use instead of app
            entity_type: Entity type managed by the service
            path_prefix: Prefix for endpoint paths
            tags: OpenAPI tags for the endpoints
            input_model: Optional input model for create/update operations
            output_model: Optional output model for responses
            endpoints: List of endpoint types to create (Create, View, List, Update, Delete)
            include_in_schema: Whether to include endpoints in OpenAPI schema
            dependencies: Optional list of dependencies for all endpoints
            status_codes: Optional map of endpoint types to status codes
            **kwargs: Additional parameters for the endpoints
            
        Returns:
            Dictionary mapping endpoint types to endpoint instances
        """
        # Validate inputs
        if not app and not router:
            raise ValueError("Either app or router must be provided")
            
        if not entity_type:
            raise ValueError("Entity type must be provided")
            
        # Use standard endpoints if none specified
        if endpoints is None:
            endpoints = ["Create", "View", "List", "Update", "Delete"]
            
        # Create entity service
        entity_service = self.service_factory.create_entity_service(entity_type)
        
        # Create adapter
        adapter = EntityServiceAdapter(
            service=entity_service,
            entity_type=entity_type,
            input_model=input_model,
            output_model=output_model,
            error_handler=self.error_handler,
            logger=logger
        )
        
        # Create endpoints
        created_endpoints = {}
        
        for endpoint_type in endpoints:
            try:
                if endpoint_type == "Create":
                    endpoint = CreateEndpoint(
                        model=adapter,
                        app=app,
                        router=router,
                        path_prefix=path_prefix,
                        tags=tags,
                        include_in_schema=include_in_schema,
                        dependencies=dependencies,
                        status_code=status_codes.get("Create", status.HTTP_201_CREATED) if status_codes else None,
                        **kwargs
                    )
                    created_endpoints["Create"] = endpoint
                    
                elif endpoint_type == "View":
                    endpoint = ViewEndpoint(
                        model=adapter,
                        app=app,
                        router=router,
                        path_prefix=path_prefix,
                        tags=tags,
                        include_in_schema=include_in_schema,
                        dependencies=dependencies,
                        status_code=status_codes.get("View") if status_codes else None,
                        **kwargs
                    )
                    created_endpoints["View"] = endpoint
                    
                elif endpoint_type == "List":
                    endpoint = ListEndpoint(
                        model=adapter,
                        app=app,
                        router=router,
                        path_prefix=path_prefix,
                        tags=tags,
                        include_in_schema=include_in_schema,
                        dependencies=dependencies,
                        status_code=status_codes.get("List") if status_codes else None,
                        **kwargs
                    )
                    created_endpoints["List"] = endpoint
                    
                elif endpoint_type == "Update":
                    endpoint = UpdateEndpoint(
                        model=adapter,
                        app=app,
                        router=router,
                        path_prefix=path_prefix,
                        tags=tags,
                        include_in_schema=include_in_schema,
                        dependencies=dependencies,
                        status_code=status_codes.get("Update") if status_codes else None,
                        **kwargs
                    )
                    created_endpoints["Update"] = endpoint
                    
                elif endpoint_type == "Delete":
                    endpoint = DeleteEndpoint(
                        model=adapter,
                        app=app,
                        router=router,
                        path_prefix=path_prefix,
                        tags=tags,
                        include_in_schema=include_in_schema,
                        dependencies=dependencies,
                        status_code=status_codes.get("Delete", status.HTTP_204_NO_CONTENT) if status_codes else None,
                        **kwargs
                    )
                    created_endpoints["Delete"] = endpoint
                    
                else:
                    logger.warning(f"Unknown endpoint type: {endpoint_type}")
                    
            except Exception as e:
                logger.error(f"Error creating {endpoint_type} endpoint: {str(e)}")
                logger.debug(traceback.format_exc())
        
        return created_endpoints
    
    def create_domain_service_endpoint(
        self,
        app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        service_class: Type[DomainService],
        path: str,
        method: str = "POST",
        tags: Optional[List[str]] = None,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        operation_id: Optional[str] = None,
        response_model: Optional[Type[BaseModel]] = None,
        status_code: int = 200,
        dependencies: Optional[List[Depends]] = None,
        include_in_schema: bool = True,
        **service_kwargs
    ):
        """
        Create an endpoint for a domain service.
        
        Args:
            app: FastAPI app to add endpoint to
            router: Optional router to use instead of app
            service_class: Domain service class
            path: Endpoint path
            method: HTTP method
            tags: OpenAPI tags
            summary: OpenAPI summary
            description: OpenAPI description
            operation_id: OpenAPI operationId
            response_model: Response model for the endpoint
            status_code: HTTP status code for successful responses
            dependencies: Optional list of dependencies
            include_in_schema: Whether to include in OpenAPI schema
            **service_kwargs: Additional parameters for the service
            
        Returns:
            The created endpoint handler function
        """
        # Validate inputs
        if not app and not router:
            raise ValueError("Either app or router must be provided")
            
        if not service_class:
            raise ValueError("Service class must be provided")
            
        # Get input and output models from service class
        hints = get_type_hints(service_class.execute)
        
        if "input_data" in hints:
            input_model = hints["input_data"]
            
            # Convert to Pydantic if needed
            if not issubclass(input_model, BaseModel):
                input_model = convert_to_pydantic_model(input_model)
        else:
            # Create a generic input model
            input_model = create_model(
                f"{service_class.__name__}Input",
                __base__=BaseModel
            )
        
        # Use provided response model or extract from service
        if response_model is None:
            # Try to extract from Result type
            return_type = hints.get("return")
            if return_type and hasattr(return_type, "__origin__") and return_type.__origin__ is Result:
                output_model = return_type.__args__[0]
                
                # Convert to Pydantic if needed
                if output_model is not None and not issubclass(output_model, BaseModel):
                    response_model = convert_to_pydantic_model(output_model)
                else:
                    response_model = output_model
                    
        # Create the domain service
        service = self.service_factory.create_domain_service(service_class, **service_kwargs)
        
        # Create adapter
        service_adapter = DomainServiceAdapter(
            service=service,
            input_model=input_model,
            output_model=response_model,
            error_handler=self.error_handler,
            logger=logger
        )
        
        # Define the endpoint handler
        async def endpoint_handler(data: input_model = Body(...)):
            """Handle domain service endpoint request."""
            return await service_adapter.execute(data)
        
        # Set function name and docstring
        endpoint_handler.__name__ = operation_id or f"{service_class.__name__}Endpoint"
        endpoint_handler.__doc__ = description or service_class.__doc__ or f"Endpoint for {service_class.__name__}"
        
        # Add the endpoint to the app or router
        target = router or app
        
        # Add the endpoint with the appropriate method
        method = method.lower()
        if method == "get":
            target.get(
                path,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )(endpoint_handler)
        elif method == "post":
            target.post(
                path,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )(endpoint_handler)
        elif method == "put":
            target.put(
                path,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )(endpoint_handler)
        elif method == "patch":
            target.patch(
                path,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )(endpoint_handler)
        elif method == "delete":
            target.delete(
                path,
                response_model=response_model,
                status_code=status_code,
                summary=summary,
                description=description,
                operation_id=operation_id,
                tags=tags,
                dependencies=dependencies,
                include_in_schema=include_in_schema,
            )(endpoint_handler)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
            
        return endpoint_handler


# Default error handler
def default_result_error_handler(result: Result) -> None:
    """
    Default error handler for Result objects.
    
    Args:
        result: The Result object to check for errors
        
    Raises:
        HTTPException: If the Result contains an error
    """
    if not result.is_success:
        error = result.error
        status_code = status.HTTP_400_BAD_REQUEST
        error_dict = {"message": str(error)}
        
        # Extract more information if it's a BaseError
        if hasattr(error, "error_code"):
            error_dict["error"] = error.error_code
            
            # Map error codes to status codes
            if error.error_code in {"NOT_FOUND", "ENTITY_NOT_FOUND", "RESOURCE_NOT_FOUND"}:
                status_code = status.HTTP_404_NOT_FOUND
            elif error.error_code in {"UNAUTHORIZED", "UNAUTHENTICATED"}:
                status_code = status.HTTP_401_UNAUTHORIZED
            elif error.error_code in {"FORBIDDEN", "ACCESS_DENIED", "PERMISSION_DENIED"}:
                status_code = status.HTTP_403_FORBIDDEN
            elif error.error_code in {"VALIDATION_ERROR", "INVALID_INPUT"}:
                status_code = status.HTTP_400_BAD_REQUEST
            elif error.error_code in {"INTERNAL_ERROR", "SYSTEM_ERROR"}:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            elif error.error_code in {"CONFLICT", "ALREADY_EXISTS", "DUPLICATE"}:
                status_code = status.HTTP_409_CONFLICT
                
        if hasattr(error, "context"):
            error_dict["detail"] = error.context
        
        raise HTTPException(status_code=status_code, detail=error_dict)


# Global factory instance
_domain_service_endpoint_factory: Optional[DomainServiceEndpointFactory] = None


def get_domain_service_endpoint_factory() -> DomainServiceEndpointFactory:
    """
    Get the global domain service endpoint factory instance.
    
    Returns:
        The global factory instance
    """
    global _domain_service_endpoint_factory
    if _domain_service_endpoint_factory is None:
        _domain_service_endpoint_factory = DomainServiceEndpointFactory(
            error_handler=default_result_error_handler
        )
    return _domain_service_endpoint_factory


def set_domain_service_endpoint_factory(factory: DomainServiceEndpointFactory) -> None:
    """
    Set the global domain service endpoint factory instance.
    
    Args:
        factory: The factory instance to set as global
    """
    global _domain_service_endpoint_factory
    _domain_service_endpoint_factory = factory