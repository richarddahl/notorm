"""
Filterable endpoint classes for the unified endpoint framework.

This module provides endpoint classes with filtering capabilities for the unified endpoint framework.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request, Response, status
from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success
from uno.domain.entity.service import ApplicationService, CrudService, DomainService

from ..base import BaseEndpoint, CrudEndpoint
from ..cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from ..response import PaginatedResponse, paginated_response

from .protocol import FilterBackend, FilterProtocol, QueryParameter
from .models import FilterCriteria, FilterRequest, FilterResponse, FilterResult
from .query_parser import QueryParser


# Type variables
RequestModel = TypeVar("RequestModel", bound=BaseModel)
ResponseModel = TypeVar("ResponseModel", bound=BaseModel)
IdType = TypeVar("IdType")


def get_filter_backend(request: Request) -> FilterBackend:
    """
    Get the filter backend from the request state.
    
    Args:
        request: The request
        
    Returns:
        The filter backend
        
    Raises:
        HTTPException: If no filter backend is available
    """
    if not hasattr(request.state, "filter_backend"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {"code": "FILTER_BACKEND_NOT_FOUND", "message": "No filter backend available"}},
        )
    
    return request.state.filter_backend


def get_filter_criteria(
    request: Request,
    filter_field: Optional[List[str]] = Query(None, description="Filter field in format field:operator:value"),
    sort: Optional[List[str]] = Query(None, description="Sort fields in format field:direction"),
    limit: Optional[int] = Query(None, description="Maximum number of results to return"),
    offset: Optional[int] = Query(None, description="Offset for pagination"),
) -> FilterCriteria:
    """
    Get filter criteria from the request.
    
    Args:
        request: The request
        filter_field: List of filter fields
        sort: List of sort fields
        limit: Maximum number of results
        offset: Offset for pagination
        
    Returns:
        The filter criteria
    """
    # If filter criteria is already in the request state, use it
    if hasattr(request.state, "filter_criteria"):
        return request.state.filter_criteria
    
    # Otherwise, parse from query parameters
    return QueryParser.parse_filter_params(
        filter_field=filter_field,
        sort=sort,
        limit=limit,
        offset=offset,
    )


class FilterableEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Base class for filterable API endpoints.
    
    This class extends BaseEndpoint to add filtering capabilities.
    """
    
    def __init__(
        self,
        *,
        filter_backend: FilterBackend,
        entity_type: str,
        repository: Any,
        **kwargs,
    ):
        """
        Initialize a new filterable endpoint.
        
        Args:
            filter_backend: The filter backend to use
            entity_type: The type of entity to filter
            repository: The repository for fetching entities
            **kwargs: Additional arguments for the parent class
        """
        super().__init__(**kwargs)
        self.filter_backend = filter_backend
        self.entity_type = entity_type
        self.repository = repository
    
    def register_filter_route(self, path: str = "/filter", response_model: Type = None):
        """
        Register a route for filtering entities.
        
        Args:
            path: The path for the filter endpoint
            response_model: The response model for the filter endpoint
        """
        # If no response model is provided, use the standard FilterResponse
        if response_model is None:
            response_model = FilterResponse[self.response_model]
        
        @self.router.post(path, response_model=response_model)
        async def filter_entities(
            request: FilterRequest,
            filter_backend: FilterBackend = Depends(get_filter_backend),
        ):
            """Filter entities based on criteria."""
            # Get query parameters from the request
            query_params = QueryParser.convert_to_query_parameters(request.criteria)
            
            # Get sort parameters
            sort_by = None
            sort_dir = None
            if request.criteria.sort:
                sort_by = [sort_field.name for sort_field in request.criteria.sort]
                sort_dir = [sort_field.direction for sort_field in request.criteria.sort]
            
            # Get limit and offset
            limit = request.criteria.limit
            offset = request.criteria.offset
            
            # Filter entities
            entities, total = await filter_backend.get_entities(
                entity_type=self.entity_type,
                filter_criteria=query_params,
                repository=self.repository,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                include_count=request.include_count,
            )
            
            # Return filtered entities
            return {
                "data": {
                    "items": entities,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            }
        
        @self.router.get(path, response_model=PaginatedResponse[self.response_model])
        async def filter_entities_get(
            request: Request,
            filter_criteria: FilterCriteria = Depends(get_filter_criteria),
            filter_backend: FilterBackend = Depends(get_filter_backend),
        ):
            """Filter entities based on query parameters."""
            # Get query parameters from the filter criteria
            query_params = QueryParser.convert_to_query_parameters(filter_criteria)
            
            # Get sort parameters
            sort_by = None
            sort_dir = None
            if filter_criteria.sort:
                sort_by = [sort_field.name for sort_field in filter_criteria.sort]
                sort_dir = [sort_field.direction for sort_field in filter_criteria.sort]
            
            # Get limit and offset
            limit = filter_criteria.limit
            offset = filter_criteria.offset
            
            # Filter entities
            entities, total = await filter_backend.get_entities(
                entity_type=self.entity_type,
                filter_criteria=query_params,
                repository=self.repository,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                include_count=True,
            )
            
            # Return paginated response
            return paginated_response(
                items=entities,
                page=(offset // limit) + 1 if offset is not None and limit is not None else 1,
                page_size=limit or len(entities),
                total_items=total or len(entities),
            )


class FilterableCrudEndpoint(CrudEndpoint[RequestModel, ResponseModel, IdType]):
    """
    Base class for filterable CRUD endpoints.
    
    This class extends CrudEndpoint to add filtering capabilities.
    """
    
    def __init__(
        self,
        *,
        filter_backend: FilterBackend,
        entity_type: str,
        **kwargs,
    ):
        """
        Initialize a new filterable CRUD endpoint.
        
        Args:
            filter_backend: The filter backend to use
            entity_type: The type of entity to filter
            **kwargs: Additional arguments for the parent class
        """
        super().__init__(**kwargs)
        self.filter_backend = filter_backend
        self.entity_type = entity_type
        
        # Override the list route to use filtering
        self._register_list_route()
        
        # Add a filter route
        self._register_filter_route()
    
    def _register_list_route(self) -> None:
        """Register the route for listing entities with filtering."""
        @self.router.get(
            self.path,
            response_model=PaginatedResponse[self.response_model],
        )
        async def list_entities(
            request: Request,
            filter_criteria: FilterCriteria = Depends(get_filter_criteria),
        ):
            # Set the filter backend in the request state
            request.state.filter_backend = self.filter_backend
            
            # Get query parameters from the filter criteria
            query_params = QueryParser.convert_to_query_parameters(filter_criteria)
            
            # Get sort parameters
            sort_by = None
            sort_dir = None
            if filter_criteria.sort:
                sort_by = [sort_field.name for sort_field in filter_criteria.sort]
                sort_dir = [sort_field.direction.value for sort_field in filter_criteria.sort]
            
            # Get limit and offset
            limit = filter_criteria.limit
            offset = filter_criteria.offset
            
            # Filter entities
            entities, total = await self.filter_backend.get_entities(
                entity_type=self.entity_type,
                filter_criteria=query_params,
                repository=self.service,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                include_count=True,
            )
            
            # Return paginated response
            return paginated_response(
                items=entities,
                page=(offset // limit) + 1 if offset is not None and limit is not None else 1,
                page_size=limit or len(entities),
                total_items=total or len(entities),
            )
    
    def _register_filter_route(self) -> None:
        """Register the route for filtering entities."""
        @self.router.post(
            f"{self.path}/filter",
            response_model=FilterResponse[self.response_model],
        )
        async def filter_entities(
            request: FilterRequest,
        ):
            # Set the filter backend in the request state
            request.state.filter_backend = self.filter_backend
            
            # Get query parameters from the request
            query_params = QueryParser.convert_to_query_parameters(request.criteria)
            
            # Get sort parameters
            sort_by = None
            sort_dir = None
            if request.criteria.sort:
                sort_by = [sort_field.name for sort_field in request.criteria.sort]
                sort_dir = [sort_field.direction.value for sort_field in request.criteria.sort]
            
            # Get limit and offset
            limit = request.criteria.limit
            offset = request.criteria.offset
            
            # Filter entities
            entities, total = await self.filter_backend.get_entities(
                entity_type=self.entity_type,
                filter_criteria=query_params,
                repository=self.service,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                include_count=request.include_count,
            )
            
            # Return filtered entities
            return {
                "data": {
                    "items": entities,
                    "total": total,
                    "limit": limit,
                    "offset": offset,
                }
            }


class FilterableCqrsEndpoint(CqrsEndpoint[RequestModel, ResponseModel, IdType]):
    """
    CQRS endpoint with filtering capabilities.
    
    This class extends CqrsEndpoint to add filtering capabilities.
    """
    
    def __init__(
        self,
        *,
        filter_backend: FilterBackend,
        entity_type: str,
        repository: Any,
        **kwargs,
    ):
        """
        Initialize a new filterable CQRS endpoint.
        
        Args:
            filter_backend: The filter backend to use
            entity_type: The type of entity to filter
            repository: The repository for fetching entities
            **kwargs: Additional arguments for the parent class
        """
        super().__init__(**kwargs)
        self.filter_backend = filter_backend
        self.entity_type = entity_type
        self.repository = repository
        
        # Add a filter query
        self._register_filter_query()
    
    def _register_filter_query(self) -> None:
        """Register a query for filtering entities."""
        # Add a filter query handler
        filter_query = QueryHandler(
            service=self._create_filter_service(),
            response_model=FilterResult[self.response_model],
            query_model=FilterRequest,
            path="/filter",
            method="post",
        )
        
        # Add the query handler
        self.add_query(filter_query)
    
    def _create_filter_service(self) -> ApplicationService:
        """
        Create a service for filtering entities.
        
        Returns:
            An application service for filtering entities
        """
        filter_backend = self.filter_backend
        entity_type = self.entity_type
        repository = self.repository
        
        class FilterService(ApplicationService):
            """Service for filtering entities."""
            
            async def execute(self, request: FilterRequest) -> Result[FilterResult]:
                """Execute the filter operation."""
                # Get query parameters from the request
                query_params = QueryParser.convert_to_query_parameters(request.criteria)
                
                # Get sort parameters
                sort_by = None
                sort_dir = None
                if request.criteria.sort:
                    sort_by = [sort_field.name for sort_field in request.criteria.sort]
                    sort_dir = [sort_field.direction.value for sort_field in request.criteria.sort]
                
                # Get limit and offset
                limit = request.criteria.limit
                offset = request.criteria.offset
                
                # Filter entities
                entities, total = await filter_backend.get_entities(
                    entity_type=entity_type,
                    filter_criteria=query_params,
                    repository=repository,
                    sort_by=sort_by,
                    sort_dir=sort_dir,
                    limit=limit,
                    offset=offset,
                    include_count=request.include_count,
                )
                
                # Return filtered entities
                return Success(FilterResult(
                    items=entities,
                    total=total,
                    limit=limit,
                    offset=offset,
                ))