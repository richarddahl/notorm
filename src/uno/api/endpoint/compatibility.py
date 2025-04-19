"""
Compatibility layer for legacy API endpoint implementations.

This module provides adapters between the legacy endpoint implementations and the new unified
endpoint framework. It ensures backward compatibility while encouraging migration to the new
approach.

IMPORTANT: This module is deprecated and will be removed in a future version. Applications
should migrate to the unified endpoint framework in `uno.api.endpoint`.
"""

import warnings
import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request, Response, status
from pydantic import BaseModel

from uno.core.errors.result import Result, Success, Error
from uno.domain.entity.service import ApplicationService, CrudService, DomainService

from .base import BaseEndpoint, CrudEndpoint
from .cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from .factory import CrudEndpointFactory, EndpointFactory

__all__ = [
    "LegacyUnoEndpoint",
    "LegacyEndpointAdapter",
    "LegacyServiceEndpointAdapter",
    "LegacyEntityEndpointAdapter",
    "create_legacy_endpoint",
]

# Display deprecation warning for this module
warnings.warn(
    "The uno.api.endpoint.compatibility module is deprecated and will be removed in a future version. "
    "Applications should migrate to the unified endpoint framework in uno.api.endpoint.",
    DeprecationWarning,
    stacklevel=2,
)

# Type variables for compatibility
T = TypeVar("T")
InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)
IdType = TypeVar("IdType")

# Logger for this module
logger = logging.getLogger(__name__)


class LegacyUnoEndpoint:
    """
    Compatibility wrapper for legacy UnoEndpoint.
    
    DEPRECATED: Use BaseEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(
        self,
        model: Any,
        app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        path_prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_in_schema: bool = True,
        dependencies: Optional[List[Depends]] = None,
        status_code: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize a legacy UnoEndpoint instance.
        
        Args:
            model: The model or adapter to use for operations
            app: FastAPI app to add endpoint to
            router: Optional router to use instead of app
            path_prefix: Prefix for endpoint paths
            tags: OpenAPI tags
            include_in_schema: Whether to include in OpenAPI schema
            dependencies: Optional list of dependencies
            status_code: HTTP status code for successful responses
            **kwargs: Additional parameters
        """
        warnings.warn(
            "LegacyUnoEndpoint is deprecated. Use BaseEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        self.model = model
        self.app = app
        self.router = router or APIRouter()
        self.path_prefix = path_prefix or ""
        self.tags = tags or []
        self.include_in_schema = include_in_schema
        self.dependencies = dependencies or []
        self.status_code = status_code
        self.kwargs = kwargs
        
        # Register this endpoint if app is provided
        if app:
            self.register(app)
    
    def register(self, app: FastAPI, prefix: str = "") -> None:
        """Register this endpoint with a FastAPI application."""
        app.include_router(
            self.router, 
            prefix=prefix + self.path_prefix, 
            tags=self.tags, 
            dependencies=self.dependencies
        )


class LegacyEndpointAdapter:
    """
    Base adapter for connecting legacy endpoints to the new framework.
    
    DEPRECATED: Use the unified endpoint framework in uno.api.endpoint instead.
    """
    
    def __init__(self):
        """Initialize a legacy endpoint adapter."""
        warnings.warn(
            "LegacyEndpointAdapter is deprecated. Use the unified endpoint framework in uno.api.endpoint instead.",
            DeprecationWarning,
            stacklevel=2,
        )


class LegacyServiceEndpointAdapter:
    """
    Adapter for legacy DomainServiceAdapter.
    
    DEPRECATED: Use CommandEndpoint or QueryEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        input_model: Optional[Type[BaseModel]] = None,
        output_model: Optional[Type[BaseModel]] = None,
        error_handler: Optional[callable] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a legacy service endpoint adapter.
        
        Args:
            service: The service to adapt
            input_model: Input model for the service
            output_model: Output model for the service
            error_handler: Optional error handler
            logger: Optional logger
        """
        warnings.warn(
            "LegacyServiceEndpointAdapter is deprecated. Use CommandEndpoint or QueryEndpoint instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        self.service = service
        self.input_model = input_model
        self.output_model = output_model
        self.error_handler = error_handler
        self.logger = logger or logging.getLogger(__name__)
    
    async def execute(self, input_data: Union[Dict[str, Any], BaseModel]) -> Any:
        """
        Execute the service operation.
        
        Args:
            input_data: Input data for the operation
            
        Returns:
            The operation result
            
        Raises:
            HTTPException: If the operation fails
        """
        try:
            # Convert to input model if needed
            if isinstance(input_data, dict) and self.input_model:
                input_obj = self.input_model(**input_data)
            elif isinstance(input_data, BaseModel) and self.input_model:
                if not isinstance(input_data, self.input_model):
                    input_obj = self.input_model(**input_data.dict())
                else:
                    input_obj = input_data
            else:
                input_obj = input_data
            
            # Execute the service operation
            result = await self.service.execute(input_obj)
            
            # Handle errors
            if self.error_handler:
                self.error_handler(result)
            else:
                self._default_error_handler(result)
            
            # Return the result value
            return result.value
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            # Log and wrap other exceptions
            self.logger.error(f"Error executing service: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={"error": "INTERNAL_ERROR", "message": str(e)},
            )
    
    def _default_error_handler(self, result: Result) -> None:
        """
        Default error handler for Result objects.
        
        Args:
            result: The Result object to check for errors
            
        Raises:
            HTTPException: If the Result contains an error
        """
        if not isinstance(result, Success):
            error = cast(Error, result).error
            status_code = status.HTTP_400_BAD_REQUEST
            error_dict = {"message": str(error)}
            
            # Extract more information if available
            if hasattr(error, "code"):
                error_dict["error"] = error.code
                
                # Map error codes to status codes
                if error.code in {"NOT_FOUND", "ENTITY_NOT_FOUND", "RESOURCE_NOT_FOUND"}:
                    status_code = status.HTTP_404_NOT_FOUND
                elif error.code in {"UNAUTHORIZED", "UNAUTHENTICATED"}:
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif error.code in {"FORBIDDEN", "ACCESS_DENIED", "PERMISSION_DENIED"}:
                    status_code = status.HTTP_403_FORBIDDEN
                elif error.code in {"VALIDATION_ERROR", "INVALID_INPUT"}:
                    status_code = status.HTTP_400_BAD_REQUEST
                elif error.code in {"INTERNAL_ERROR", "SYSTEM_ERROR"}:
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                elif error.code in {"CONFLICT", "ALREADY_EXISTS", "DUPLICATE"}:
                    status_code = status.HTTP_409_CONFLICT
            
            if hasattr(error, "details"):
                error_dict["detail"] = error.details
            
            raise HTTPException(status_code=status_code, detail=error_dict)


class LegacyEntityEndpointAdapter:
    """
    Adapter for legacy EntityServiceAdapter.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(
        self,
        service: CrudService,
        entity_type: Type[T],
        input_model: Optional[Type[BaseModel]] = None,
        output_model: Optional[Type[BaseModel]] = None,
        error_handler: Optional[callable] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize a legacy entity endpoint adapter.
        
        Args:
            service: The entity service to adapt
            entity_type: The entity type
            input_model: Optional input model
            output_model: Optional output model
            error_handler: Optional error handler
            logger: Optional logger
        """
        warnings.warn(
            "LegacyEntityEndpointAdapter is deprecated. Use CrudEndpoint instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        self.service = service
        self.entity_type = entity_type
        self.input_model = input_model
        self.output_model = output_model
        self.error_handler = error_handler
        self.logger = logger or logging.getLogger(__name__)
        
        # Compatibility attributes
        self.display_name = getattr(entity_type, "__name__", "Entity")
        self.display_name_plural = getattr(entity_type, "display_name_plural", f"{self.display_name}s")
    
    async def get(self, id: Any, **kwargs) -> Any:
        """
        Get an entity by ID.
        
        Args:
            id: The entity ID
            **kwargs: Additional parameters
            
        Returns:
            The entity if found
            
        Raises:
            HTTPException: If the entity is not found
        """
        result = await self.service.get_by_id(id)
        self._handle_result(result)
        
        entity = result.value
        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "ENTITY_NOT_FOUND",
                    "message": f"{self.display_name} with ID {id} not found",
                },
            )
        
        return entity
    
    async def filter(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
        **kwargs,
    ) -> Union[List[T], Dict[str, Any]]:
        """
        Filter entities based on criteria.
        
        Args:
            filters: Filter criteria
            page: Page number
            page_size: Items per page
            **kwargs: Additional parameters
            
        Returns:
            List of entities or paginated result
        """
        result = await self.service.find(filters or {})
        self._handle_result(result)
        
        entities = result.value
        
        # Get total count
        count_result = await self.service.count(filters or {})
        self._handle_result(count_result)
        total = count_result.value
        
        # Return paginated results if requested
        if kwargs.get("paginated", True):
            return {
                "items": entities,
                "page": page,
                "page_size": page_size,
                "total": total,
            }
        
        return entities
    
    async def save(self, data: Union[Dict[str, Any], BaseModel], **kwargs) -> T:
        """
        Create or update an entity.
        
        Args:
            data: The entity data
            **kwargs: Additional parameters
            
        Returns:
            The created or updated entity
        """
        # Convert to dict if it's a Pydantic model
        if isinstance(data, BaseModel):
            data_dict = data.dict()
        else:
            data_dict = data
        
        # Check if this is an update (has ID) or create
        entity_id = data_dict.get("id")
        
        if entity_id:
            # Update
            result = await self.service.update(entity_id, data_dict)
        else:
            # Create
            result = await self.service.create(data_dict)
        
        self._handle_result(result)
        return result.value
    
    async def delete_(self, id: Any, **kwargs) -> bool:
        """
        Delete an entity.
        
        Args:
            id: The entity ID
            **kwargs: Additional parameters
            
        Returns:
            True if successful
        """
        result = await self.service.delete(id)
        self._handle_result(result)
        return result.value
    
    def _handle_result(self, result: Result) -> None:
        """
        Handle a Result object.
        
        Args:
            result: The Result object to check for errors
            
        Raises:
            HTTPException: If the Result contains an error
        """
        if self.error_handler:
            self.error_handler(result)
        else:
            self._default_error_handler(result)
    
    def _default_error_handler(self, result: Result) -> None:
        """
        Default error handler for Result objects.
        
        Args:
            result: The Result object to check for errors
            
        Raises:
            HTTPException: If the Result contains an error
        """
        if not isinstance(result, Success):
            error = cast(Error, result).error
            status_code = status.HTTP_400_BAD_REQUEST
            error_dict = {"message": str(error)}
            
            # Extract more information if available
            if hasattr(error, "code"):
                error_dict["error"] = error.code
                
                # Map error codes to status codes
                if error.code in {"NOT_FOUND", "ENTITY_NOT_FOUND", "RESOURCE_NOT_FOUND"}:
                    status_code = status.HTTP_404_NOT_FOUND
                elif error.code in {"UNAUTHORIZED", "UNAUTHENTICATED"}:
                    status_code = status.HTTP_401_UNAUTHORIZED
                elif error.code in {"FORBIDDEN", "ACCESS_DENIED", "PERMISSION_DENIED"}:
                    status_code = status.HTTP_403_FORBIDDEN
                elif error.code in {"VALIDATION_ERROR", "INVALID_INPUT"}:
                    status_code = status.HTTP_400_BAD_REQUEST
                elif error.code in {"INTERNAL_ERROR", "SYSTEM_ERROR"}:
                    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                elif error.code in {"CONFLICT", "ALREADY_EXISTS", "DUPLICATE"}:
                    status_code = status.HTTP_409_CONFLICT
            
            if hasattr(error, "details"):
                error_dict["detail"] = error.details
            
            raise HTTPException(status_code=status_code, detail=error_dict)


def create_legacy_endpoint(
    service: Union[CrudService, ApplicationService, DomainService],
    app: Optional[FastAPI] = None,
    router: Optional[APIRouter] = None,
    **kwargs,
) -> Union[CrudEndpoint, BaseEndpoint]:
    """
    Create a modern endpoint from a legacy service.
    
    This function bridges the gap between legacy service adapters and the new unified endpoint framework.
    
    Args:
        service: The service to create an endpoint for
        app: Optional FastAPI app to register the endpoint with
        router: Optional router to use
        **kwargs: Additional parameters for the endpoint
        
    Returns:
        The created endpoint
    """
    warnings.warn(
        "create_legacy_endpoint is deprecated. Use the unified endpoint framework in uno.api.endpoint directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    
    # Create an appropriate endpoint based on service type
    if isinstance(service, CrudService):
        # Use CrudEndpoint for CRUD services
        endpoint = CrudEndpoint(
            service=service,
            create_model=kwargs.get("input_model") or kwargs.get("create_model"),
            response_model=kwargs.get("output_model") or kwargs.get("response_model"),
            update_model=kwargs.get("update_model"),
            router=router,
            tags=kwargs.get("tags"),
            path=kwargs.get("path_prefix") or kwargs.get("path") or "",
        )
    else:
        # Use CommandEndpoint or QueryEndpoint via CQRS
        is_query = kwargs.get("method", "post").lower() == "get"
        
        if is_query:
            handler = QueryHandler(
                service=service,
                response_model=kwargs.get("output_model") or kwargs.get("response_model"),
                query_model=kwargs.get("input_model"),
                path=kwargs.get("path") or "",
                method=kwargs.get("method", "get"),
            )
            
            endpoint = CqrsEndpoint(
                queries=[handler],
                router=router,
                tags=kwargs.get("tags"),
                base_path=kwargs.get("path_prefix") or "",
            )
        else:
            handler = CommandHandler(
                service=service,
                command_model=kwargs.get("input_model"),
                response_model=kwargs.get("output_model") or kwargs.get("response_model"),
                path=kwargs.get("path") or "",
                method=kwargs.get("method", "post"),
            )
            
            endpoint = CqrsEndpoint(
                commands=[handler],
                router=router,
                tags=kwargs.get("tags"),
                base_path=kwargs.get("path_prefix") or "",
            )
    
    # Register if app is provided
    if app:
        endpoint.register(app)
    
    return endpoint