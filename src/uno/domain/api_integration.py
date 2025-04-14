"""
API integration layer for the Domain-Driven Design approach in the Uno framework.

This module provides utilities for integrating domain services with FastAPI endpoints,
facilitating the transition from UnoObj patterns to the Domain approach.
"""

from typing import Type, List, Dict, Any, Optional, Generic, TypeVar, get_type_hints, Union, cast
import inspect
from functools import wraps

from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from pydantic import BaseModel, create_model

from uno.domain.service import DomainService
from uno.domain.repository import Repository
from uno.domain.core import Entity, AggregateRoot
from uno.core.errors.result import Result, Success, Failure
from uno.dependencies.scoped_container import get_service
from uno.dependencies.database import get_db_session

# Type variables
T = TypeVar('T', bound=Entity)
SvcT = TypeVar('SvcT', bound=DomainService)


class DomainRouter(Generic[T, SvcT]):
    """
    Router factory for creating standardized FastAPI endpoints for domain entities.
    
    This class generates a complete set of CRUD endpoints for a domain entity,
    using its corresponding domain service to handle business logic.
    
    Type Parameters:
        T: The domain entity type
        SvcT: The domain service type for this entity
    """

    def __init__(
        self,
        entity_type: Type[T],
        service_type: Type[SvcT],
        prefix: str,
        tags: List[str],
        create_dto: Optional[Type[BaseModel]] = None,
        update_dto: Optional[Type[BaseModel]] = None,
        response_dto: Optional[Type[BaseModel]] = None,
        generate_schemas: bool = True,
        base_router: Optional[APIRouter] = None,
    ):
        """
        Initialize a domain router.
        
        Args:
            entity_type: The domain entity class
            service_type: The domain service class
            prefix: The URL prefix for all routes
            tags: Tags for API documentation
            create_dto: DTO model for create operations
            update_dto: DTO model for update operations
            response_dto: DTO model for responses
            generate_schemas: Whether to auto-generate DTOs if not provided
            base_router: Optional existing router to extend
        """
        self.entity_type = entity_type
        self.service_type = service_type
        self.prefix = prefix
        self.tags = tags

        # Create or use provided router
        self.router = base_router or APIRouter(prefix=prefix, tags=tags)
        
        # Generate or use provided DTOs
        self.create_dto = create_dto
        self.update_dto = update_dto
        self.response_dto = response_dto
        
        if generate_schemas and (not create_dto or not update_dto or not response_dto):
            self._generate_schemas()
        
        # Ensure we have DTOs defined
        if not all([self.create_dto, self.update_dto, self.response_dto]):
            raise ValueError(
                "DTOs must be provided or generated. Set generate_schemas=True or provide all DTOs."
            )
            
        # Register endpoints
        self._register_endpoints()

    def _generate_schemas(self) -> None:
        """
        Generate Pydantic schemas (DTOs) based on the entity type.
        
        This method automatically creates reasonable DTOs if they weren't provided.
        """
        entity_name = self.entity_type.__name__
        entity_fields = get_type_hints(self.entity_type)
        
        # Filter out private fields and methods
        filtered_fields = {
            k: v for k, v in entity_fields.items() 
            if not k.startswith('_') and k not in ['id', 'created_at', 'updated_at']
        }
        
        # Create response model (includes all fields)
        if not self.response_dto:
            self.response_dto = create_model(
                f"{entity_name}Response",
                id=(str, ...),
                created_at=(Optional[Any], None),
                updated_at=(Optional[Any], None),
                **filtered_fields
            )
            
        # Create model for creation (no id required)
        if not self.create_dto:
            self.create_dto = create_model(
                f"{entity_name}Create",
                **filtered_fields
            )
            
        # Create model for updates (all fields optional)
        if not self.update_dto:
            self.update_dto = create_model(
                f"{entity_name}Update",
                **{k: (Optional[v], None) for k, v in filtered_fields.items()}
            )

    def _register_endpoints(self) -> None:
        """Register all standard CRUD endpoints."""
        
        @self.router.post("", response_model=self.response_dto)
        async def create_entity(
            data: self.create_dto,
            service: SvcT = Depends(lambda: get_service(self.service_type))
        ):
            """Create a new entity."""
            result = await service.create(**data.model_dump())
            if isinstance(result, Result):
                if result.is_failure:
                    raise HTTPException(status_code=400, detail=str(result.error))
                return result.value.to_dict()
            return result.to_dict()
            
        @self.router.get("/{id}", response_model=self.response_dto)
        async def get_entity(
            id: str = Path(..., description=f"The ID of the {self.entity_type.__name__}"),
            service: SvcT = Depends(lambda: get_service(self.service_type))
        ):
            """Get an entity by ID."""
            result = await service.get_by_id(id)
            if isinstance(result, Result):
                if result.is_failure:
                    raise HTTPException(status_code=404, detail=str(result.error))
                return result.value.to_dict()
            elif result is None:
                raise HTTPException(status_code=404, detail=f"{self.entity_type.__name__} not found")
            return result.to_dict()
            
        @self.router.get("", response_model=List[self.response_dto])
        async def list_entities(
            service: SvcT = Depends(lambda: get_service(self.service_type)),
            limit: int = Query(100, description="Maximum number of items to return"),
            offset: int = Query(0, description="Number of items to skip"),
        ):
            """List all entities with pagination."""
            result = await service.list(limit=limit, offset=offset)
            if isinstance(result, Result):
                if result.is_failure:
                    raise HTTPException(status_code=400, detail=str(result.error))
                entities = result.value
            else:
                entities = result
                
            return [entity.to_dict() for entity in entities]
            
        @self.router.patch("/{id}", response_model=self.response_dto)
        async def update_entity(
            id: str = Path(..., description=f"The ID of the {self.entity_type.__name__}"),
            data: self.update_dto = Body(...),
            service: SvcT = Depends(lambda: get_service(self.service_type))
        ):
            """Update an entity by ID."""
            result = await service.update_by_id(id, **data.model_dump(exclude_unset=True))
            if isinstance(result, Result):
                if result.is_failure:
                    if "not found" in str(result.error).lower():
                        raise HTTPException(status_code=404, detail=str(result.error))
                    raise HTTPException(status_code=400, detail=str(result.error))
                return result.value.to_dict()
            elif result is None:
                raise HTTPException(status_code=404, detail=f"{self.entity_type.__name__} not found")
            return result.to_dict()
            
        @self.router.delete("/{id}")
        async def delete_entity(
            id: str = Path(..., description=f"The ID of the {self.entity_type.__name__}"),
            service: SvcT = Depends(lambda: get_service(self.service_type))
        ):
            """Delete an entity by ID."""
            result = await service.delete_by_id(id)
            if isinstance(result, Result):
                if result.is_failure:
                    if "not found" in str(result.error).lower():
                        raise HTTPException(status_code=404, detail=str(result.error))
                    raise HTTPException(status_code=400, detail=str(result.error))
                return {"success": True, "message": f"{self.entity_type.__name__} deleted"}
            elif not result:
                raise HTTPException(status_code=404, detail=f"{self.entity_type.__name__} not found")
            return {"success": True, "message": f"{self.entity_type.__name__} deleted"}
                
    def add_custom_endpoint(
        self,
        path: str,
        method: str,
        endpoint_function,
        response_model=None,
        **kwargs
    ):
        """
        Add a custom endpoint to the router.
        
        Args:
            path: The URL path
            method: The HTTP method (get, post, etc.)
            endpoint_function: The endpoint handler function
            response_model: The Pydantic model for responses
            **kwargs: Additional parameters for the endpoint
        """
        method = method.lower()
        if not hasattr(self.router, method):
            raise ValueError(f"Invalid HTTP method: {method}")
            
        router_method = getattr(self.router, method)
        router_method(path, response_model=response_model, **kwargs)(endpoint_function)
        
    def include_router(self, app):
        """
        Include this router in a FastAPI application.
        
        Args:
            app: The FastAPI application
        """
        app.include_router(self.router)
        return self.router


def create_domain_router(
    entity_type: Type[T],
    service_type: Type[SvcT],
    prefix: str,
    tags: List[str],
    **kwargs
) -> APIRouter:
    """
    Create a domain router for a entity and service.
    
    This is a convenience function for creating a DomainRouter instance
    and returning its router for direct use with FastAPI.
    
    Args:
        entity_type: The domain entity class
        service_type: The domain service class
        prefix: The URL prefix for all routes
        tags: Tags for API documentation
        **kwargs: Additional parameters for DomainRouter
        
    Returns:
        A FastAPI router with all CRUD endpoints registered
    """
    domain_router = DomainRouter(
        entity_type=entity_type,
        service_type=service_type,
        prefix=prefix,
        tags=tags,
        **kwargs
    )
    return domain_router.router


def domain_endpoint(
    entity_type: Type[T] = None, 
    service_type: Type[SvcT] = None,
    response_model=None
):
    """
    Decorator for creating domain-aware FastAPI endpoint functions.
    
    This decorator simplifies creating custom endpoints that work with
    domain services and entities, automatically handling common tasks like
    service injection and result handling.
    
    Args:
        entity_type: The domain entity type this endpoint works with
        service_type: The domain service type to inject
        response_model: The Pydantic model for the response
        
    Returns:
        Decorated endpoint function
    """
    def decorator(func):
        # Determine the service type from type hints if not specified
        nonlocal service_type
        if not service_type:
            hints = get_type_hints(func)
            for param_name, param_type in hints.items():
                if param_name != 'return' and issubclass(param_type, DomainService):
                    service_type = param_type
                    break
        
        if not service_type:
            raise ValueError(
                "Service type must be specified or inferable from function signature"
            )
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Inject the service if not provided
            if 'service' not in kwargs or kwargs['service'] is None:
                kwargs['service'] = get_service(service_type)
                
            # Call the original function
            result = await func(*args, **kwargs)
            
            # Handle Result types
            if isinstance(result, Result):
                if result.is_failure:
                    status_code = 404 if "not found" in str(result.error).lower() else 400
                    raise HTTPException(status_code=status_code, detail=str(result.error))
                return result.value
                
            return result
            
        return wrapper
    
    # Allow use as @domain_endpoint or @domain_endpoint()
    if callable(entity_type) and service_type is None:
        func, entity_type = entity_type, None
        return decorator(func)
        
    return decorator