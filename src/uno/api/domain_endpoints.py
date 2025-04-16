"""
FastAPI endpoints for the API module.

This module defines FastAPI endpoints for managing API resources, including endpoints
for creating, retrieving, updating, and deleting resources and their associated endpoints.
"""

from typing import List, Optional, Dict, Any, Type, Union
from enum import Enum
from pydantic import BaseModel, Field, create_model

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from fastapi.responses import JSONResponse

from uno.dependencies.fastapi import get_service, inject_dependency
from uno.core.errors import UnoError, ErrorCodes
from uno.core.errors.result import Result

from .domain_services import (
    ApiResourceServiceProtocol,
    EndpointFactoryServiceProtocol,
    RepositoryAdapterServiceProtocol
)
from .entities import ApiResource, EndpointConfig, HttpMethod


# API request/response models
class EndpointConfigCreate(BaseModel):
    """Model for creating a new endpoint configuration."""
    path: str = Field(..., description="URL path for the endpoint")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, PATCH, DELETE)")
    tags: Optional[List[str]] = Field(None, description="OpenAPI tags")
    summary: Optional[str] = Field(None, description="OpenAPI summary")
    description: Optional[str] = Field(None, description="OpenAPI description")
    operation_id: Optional[str] = Field(None, description="OpenAPI operationId")
    deprecated: bool = Field(False, description="Whether the endpoint is deprecated")


class EndpointConfigResponse(BaseModel):
    """Model for endpoint configuration responses."""
    id: str = Field(..., description="Unique identifier")
    path: str = Field(..., description="URL path for the endpoint")
    method: str = Field(..., description="HTTP method")
    tags: List[str] = Field(default_factory=list, description="OpenAPI tags")
    summary: Optional[str] = Field(None, description="OpenAPI summary")
    description: Optional[str] = Field(None, description="OpenAPI description")
    operation_id: Optional[str] = Field(None, description="OpenAPI operationId")
    deprecated: bool = Field(False, description="Whether the endpoint is deprecated")
    
    @classmethod
    def from_entity(cls, entity: EndpointConfig) -> "EndpointConfigResponse":
        """Create response model from endpoint entity."""
        return cls(
            id=entity.id,
            path=entity.path,
            method=entity.method.value,
            tags=entity.tags,
            summary=entity.summary,
            description=entity.description,
            operation_id=entity.operation_id,
            deprecated=entity.deprecated
        )


class ApiResourceCreate(BaseModel):
    """Model for creating a new API resource."""
    name: str = Field(..., description="Name of the resource")
    path_prefix: str = Field(..., description="URL path prefix for all endpoints")
    entity_type_name: str = Field(..., description="Name of the entity type")
    tags: Optional[List[str]] = Field(None, description="OpenAPI tags")
    description: Optional[str] = Field(None, description="Description of the resource")


class ApiResourceResponse(BaseModel):
    """Model for API resource responses."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the resource")
    path_prefix: str = Field(..., description="URL path prefix for all endpoints")
    entity_type_name: str = Field(..., description="Name of the entity type")
    tags: List[str] = Field(default_factory=list, description="OpenAPI tags")
    description: Optional[str] = Field(None, description="Description of the resource")
    endpoints: List[EndpointConfigResponse] = Field(
        default_factory=list, description="Endpoints in this resource"
    )
    
    @classmethod
    def from_entity(cls, entity: ApiResource) -> "ApiResourceResponse":
        """Create response model from resource entity."""
        return cls(
            id=entity.id,
            name=entity.name,
            path_prefix=entity.path_prefix,
            entity_type_name=entity.entity_type_name,
            tags=entity.tags,
            description=entity.description,
            endpoints=[EndpointConfigResponse.from_entity(e) for e in entity.endpoints]
        )


class CrudEndpointCreate(BaseModel):
    """Model for creating CRUD endpoints for an entity type."""
    resource_name: str = Field(..., description="Name of the resource")
    entity_type_name: str = Field(..., description="Name of the entity type")
    path_prefix: str = Field(..., description="URL path prefix for all endpoints")
    tags: Optional[List[str]] = Field(None, description="OpenAPI tags")
    description: Optional[str] = Field(None, description="Description of the resource")


class PaginatedResponse(BaseModel, Generic=List[ApiResourceResponse]):
    """Paginated response model."""
    items: List[ApiResourceResponse] = Field(
        default_factory=list, description="List of items in this page"
    )
    total: Optional[int] = Field(None, description="Total number of items")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")
    next_page: Optional[int] = Field(None, description="Next page number, if available")
    prev_page: Optional[int] = Field(None, description="Previous page number, if available")


# Create API router
router = APIRouter(
    prefix="/api/v1/api-resources",
    tags=["API Resources"],
    responses={
        400: {"description": "Bad Request"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"}
    }
)


# Error response models
class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    detail: Optional[Dict[str, Any]] = Field(None, description="Error details")


# Error handler
def handle_result_error(result: Result) -> None:
    """
    Handle errors from Result objects.
    
    Args:
        result: The Result object to check for errors
        
    Raises:
        HTTPException: If the Result contains an error
    """
    if result.is_failure():
        error: UnoError = result.error
        status_code = status.HTTP_400_BAD_REQUEST
        
        # Map error codes to status codes
        if error.code == ErrorCodes.RESOURCE_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif error.code == ErrorCodes.UNAUTHORIZED:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif error.code == ErrorCodes.FORBIDDEN:
            status_code = status.HTTP_403_FORBIDDEN
        elif error.code == ErrorCodes.VALIDATION_ERROR:
            status_code = status.HTTP_400_BAD_REQUEST
        elif error.code == ErrorCodes.INTERNAL_ERROR:
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": error.code,
                "message": error.message,
                "detail": error.context
            }
        )


# Endpoint routes
@router.get(
    "",
    response_model=PaginatedResponse,
    summary="List API resources",
    description="Get a list of API resources with pagination"
)
async def list_resources(
    page: int = Query(1, gt=0, description="Page number"),
    page_size: int = Query(50, gt=0, le=100, description="Items per page"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """List API resources with pagination and filtering."""
    # Create filters
    filters = {}
    if entity_type:
        filters["entity_type_name"] = entity_type
    
    # Get resources
    result = await api_service.list_resources(
        filters=filters,
        page=page,
        page_size=page_size
    )
    
    # Handle errors
    handle_result_error(result)
    
    # Convert to response model
    resources = result.value
    
    # Count total resources for pagination
    count_result = await api_service.resource_repository.count(filters=filters)
    handle_result_error(count_result)
    total = count_result.value
    
    # Create paginated response
    response = PaginatedResponse(
        items=[ApiResourceResponse.from_entity(r) for r in resources],
        total=total,
        page=page,
        page_size=page_size
    )
    
    # Add next/prev page links if applicable
    if page > 1:
        response.prev_page = page - 1
    
    if (page * page_size) < total:
        response.next_page = page + 1
    
    return response


@router.get(
    "/{resource_id}",
    response_model=ApiResourceResponse,
    summary="Get API resource",
    description="Get details of an API resource by ID"
)
async def get_resource(
    resource_id: str = Path(..., description="API resource ID"),
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """Get API resource by ID."""
    result = await api_service.get_resource(resource_id)
    handle_result_error(result)
    
    resource = result.value
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCodes.RESOURCE_NOT_FOUND,
                "message": f"API resource with ID '{resource_id}' not found",
                "detail": {"resource_id": resource_id}
            }
        )
    
    return ApiResourceResponse.from_entity(resource)


@router.post(
    "",
    response_model=ApiResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API resource",
    description="Create a new API resource"
)
async def create_resource(
    resource_data: ApiResourceCreate,
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """Create a new API resource."""
    result = await api_service.create_resource(
        name=resource_data.name,
        path_prefix=resource_data.path_prefix,
        entity_type_name=resource_data.entity_type_name,
        tags=resource_data.tags,
        description=resource_data.description
    )
    
    handle_result_error(result)
    
    return ApiResourceResponse.from_entity(result.value)


@router.post(
    "/crud-endpoints",
    response_model=ApiResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create CRUD endpoints",
    description="Create standard CRUD endpoints for an entity type"
)
async def create_crud_endpoints(
    data: CrudEndpointCreate,
    endpoint_factory: EndpointFactoryServiceProtocol = Depends(
        get_service(EndpointFactoryServiceProtocol)
    )
):
    """Create standard CRUD endpoints for an entity type."""
    result = await endpoint_factory.create_crud_endpoints(
        resource_name=data.resource_name,
        entity_type_name=data.entity_type_name,
        path_prefix=data.path_prefix,
        tags=data.tags,
        description=data.description
    )
    
    handle_result_error(result)
    
    return ApiResourceResponse.from_entity(result.value)


@router.delete(
    "/{resource_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete API resource",
    description="Delete an API resource and all its endpoints"
)
async def delete_resource(
    resource_id: str = Path(..., description="API resource ID"),
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """Delete an API resource by ID."""
    result = await api_service.delete_resource(resource_id)
    handle_result_error(result)
    
    if not result.value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": ErrorCodes.RESOURCE_NOT_FOUND,
                "message": f"API resource with ID '{resource_id}' not found",
                "detail": {"resource_id": resource_id}
            }
        )
    
    return None


@router.post(
    "/{resource_id}/endpoints",
    response_model=ApiResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add endpoint to resource",
    description="Add a new endpoint to an API resource"
)
async def add_endpoint(
    resource_id: str = Path(..., description="API resource ID"),
    endpoint_data: EndpointConfigCreate = Body(...),
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """Add an endpoint to an API resource."""
    result = await api_service.add_endpoint_to_resource(
        resource_id=resource_id,
        path=endpoint_data.path,
        method=endpoint_data.method,
        tags=endpoint_data.tags,
        summary=endpoint_data.summary,
        description=endpoint_data.description,
        operation_id=endpoint_data.operation_id,
        deprecated=endpoint_data.deprecated
    )
    
    handle_result_error(result)
    
    return ApiResourceResponse.from_entity(result.value)


@router.delete(
    "/{resource_id}/endpoints/{endpoint_id}",
    response_model=ApiResourceResponse,
    summary="Remove endpoint from resource",
    description="Remove an endpoint from an API resource"
)
async def remove_endpoint(
    resource_id: str = Path(..., description="API resource ID"),
    endpoint_id: str = Path(..., description="Endpoint ID"),
    api_service: ApiResourceServiceProtocol = Depends(get_service(ApiResourceServiceProtocol))
):
    """Remove an endpoint from an API resource."""
    result = await api_service.remove_endpoint_from_resource(
        resource_id=resource_id,
        endpoint_id=endpoint_id
    )
    
    handle_result_error(result)
    
    return ApiResourceResponse.from_entity(result.value)


# Register error handlers
@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom exception handler for HTTPExceptions."""
    if hasattr(exc, "detail") and isinstance(exc.detail, dict) and "error" in exc.detail:
        # Use our standardized error format
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    
    # Default error format for other exceptions
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "ERROR",
            "message": str(exc.detail),
            "detail": None
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": ErrorCodes.INTERNAL_ERROR,
            "message": "An unexpected error occurred",
            "detail": {"error_type": type(exc).__name__}
        }
    )