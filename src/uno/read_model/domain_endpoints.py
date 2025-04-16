"""
Domain endpoints for the Read Model module.

This module defines FastAPI endpoints for the Read Model module,
providing HTTP API access to read model functionality.
"""

import logging
from typing import Dict, List, Optional, Any, Type, TypeVar, Generic, Union
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from pydantic import BaseModel, Field

from uno.core.di_fastapi import inject_dependency
from uno.core.result import Result, Success, Failure
from uno.domain.events import DomainEvent

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId,
    Query as DomainQuery, QueryId, QueryResult, CacheEntry,
    ProjectorConfiguration, ProjectionType, QueryType
)
from uno.read_model.domain_services import (
    ReadModelServiceProtocol, ProjectionServiceProtocol,
    QueryServiceProtocol, ProjectorServiceProtocol
)

# Type variables
T = TypeVar('T', bound=ReadModel)
P = TypeVar('P', bound=Projection)
Q = TypeVar('Q', bound=DomainQuery)


# Pydantic models for API requests/responses

class ReadModelResponse(BaseModel):
    """API response model for read models."""
    
    id: str
    version: int
    created_at: datetime
    updated_at: datetime
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    model_type: str


class ReadModelListResponse(BaseModel):
    """API response model for lists of read models."""
    
    items: List[ReadModelResponse]
    count: int


class ProjectionResponse(BaseModel):
    """API response model for projections."""
    
    id: str
    name: str
    event_type: str
    read_model_type: str
    projection_type: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    configuration: Dict[str, Any]


class ProjectionListResponse(BaseModel):
    """API response model for lists of projections."""
    
    items: List[ProjectionResponse]
    count: int


class QueryResponse(BaseModel):
    """API response model for queries."""
    
    id: str
    query_type: str
    read_model_type: str
    parameters: Dict[str, Any]
    created_at: datetime


class QueryResultResponse(BaseModel):
    """API response model for query results."""
    
    id: str
    query_id: str
    execution_time_ms: float
    result_count: int
    results: Optional[Union[ReadModelResponse, List[ReadModelResponse]]]
    created_at: datetime
    is_cached: bool


class ProjectorConfigResponse(BaseModel):
    """API response model for projector configurations."""
    
    id: str
    name: str
    async_processing: bool
    batch_size: int
    cache_enabled: bool
    cache_ttl_seconds: int
    rebuild_on_startup: bool
    created_at: datetime
    updated_at: datetime
    projections: List[ProjectionResponse]


class CreateProjectionRequest(BaseModel):
    """API request model for creating projections."""
    
    name: str
    event_type: str
    read_model_type: str
    projection_type: str = Field(default="standard")
    is_active: bool = True
    configuration: Dict[str, Any] = Field(default_factory=dict)


class UpdateProjectionRequest(BaseModel):
    """API request model for updating projections."""
    
    name: Optional[str] = None
    is_active: Optional[bool] = None
    configuration: Optional[Dict[str, Any]] = None


class CreateQueryRequest(BaseModel):
    """API request model for creating queries."""
    
    query_type: str
    read_model_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class CreateReadModelRequest(BaseModel):
    """API request model for creating read models."""
    
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UpdateReadModelRequest(BaseModel):
    """API request model for updating read models."""
    
    data: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


# Domain-to-API model converters

def domain_read_model_to_api(model: ReadModel) -> ReadModelResponse:
    """
    Convert a domain read model to an API response model.
    
    Args:
        model: The domain read model
        
    Returns:
        API response model
    """
    return ReadModelResponse(
        id=model.id.value,
        version=model.version,
        created_at=model.created_at,
        updated_at=model.updated_at,
        data=model.data,
        metadata=model.metadata,
        model_type=model.model_type
    )


def domain_projection_to_api(projection: Projection) -> ProjectionResponse:
    """
    Convert a domain projection to an API response model.
    
    Args:
        projection: The domain projection
        
    Returns:
        API response model
    """
    return ProjectionResponse(
        id=projection.id.value,
        name=projection.name,
        event_type=projection.event_type,
        read_model_type=projection.read_model_type,
        projection_type=projection.projection_type,
        created_at=projection.created_at,
        updated_at=projection.updated_at,
        is_active=projection.is_active,
        configuration=projection.configuration
    )


def domain_query_to_api(query: DomainQuery) -> QueryResponse:
    """
    Convert a domain query to an API response model.
    
    Args:
        query: The domain query
        
    Returns:
        API response model
    """
    return QueryResponse(
        id=query.id.value,
        query_type=query.query_type,
        read_model_type=query.read_model_type,
        parameters=query.parameters,
        created_at=query.created_at
    )


def domain_query_result_to_api(result: QueryResult) -> QueryResultResponse:
    """
    Convert a domain query result to an API response model.
    
    Args:
        result: The domain query result
        
    Returns:
        API response model
    """
    # Convert results to API models
    api_results = None
    
    if result.results:
        if isinstance(result.results, list):
            api_results = [domain_read_model_to_api(model) for model in result.results]
        else:
            api_results = domain_read_model_to_api(result.results)
    
    return QueryResultResponse(
        id=result.id,
        query_id=result.query_id.value,
        execution_time_ms=result.execution_time_ms,
        result_count=result.result_count,
        results=api_results,
        created_at=result.created_at,
        is_cached=result.is_cached
    )


def domain_projector_config_to_api(config: ProjectorConfiguration) -> ProjectorConfigResponse:
    """
    Convert a domain projector configuration to an API response model.
    
    Args:
        config: The domain projector configuration
        
    Returns:
        API response model
    """
    return ProjectorConfigResponse(
        id=config.id,
        name=config.name,
        async_processing=config.async_processing,
        batch_size=config.batch_size,
        cache_enabled=config.cache_enabled,
        cache_ttl_seconds=config.cache_ttl_seconds,
        rebuild_on_startup=config.rebuild_on_startup,
        created_at=config.created_at,
        updated_at=config.updated_at,
        projections=[domain_projection_to_api(p) for p in config.projections]
    )


# FastAPI endpoint factory

class ReadModelEndpoints:
    """
    Factory for creating FastAPI endpoints for read models.
    
    This class provides methods to create API routers for different read model types.
    """
    
    @staticmethod
    def create_router(
        model_type: Type[T],
        prefix: str,
        read_model_service: ReadModelServiceProtocol[T],
        query_service: Optional[QueryServiceProtocol[Any, T]] = None,
        tags: Optional[List[str]] = None
    ) -> APIRouter:
        """
        Create a FastAPI router for a specific read model type.
        
        Args:
            model_type: The read model type
            prefix: The URL prefix for the endpoints
            read_model_service: The read model service
            query_service: Optional query service
            tags: Optional API tags
            
        Returns:
            FastAPI router
        """
        if tags is None:
            tags = [model_type.__name__]
        
        router = APIRouter(prefix=prefix, tags=tags)
        
        # Helper function to handle service results
        def handle_result(result: Result[Any], not_found_message: str = "Item not found") -> Any:
            """Handle a service result, raising appropriate HTTP exceptions."""
            if not result.is_success():
                if result.error.code.value == "not_found":
                    raise HTTPException(status_code=404, detail=not_found_message)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {result.error.message}"
                )
            return result.value
        
        # Get a read model by ID
        @router.get("/{id}", response_model=ReadModelResponse)
        async def get_read_model(id: str = Path(..., description="The read model ID")) -> ReadModelResponse:
            """Get a read model by ID."""
            model_id = ReadModelId(value=id)
            result = await read_model_service.get_by_id(model_id)
            model = handle_result(result, f"Read model with ID {id} not found")
            
            if model is None:
                raise HTTPException(status_code=404, detail=f"Read model with ID {id} not found")
                
            return domain_read_model_to_api(model)
        
        # Find read models by criteria
        @router.get("/", response_model=ReadModelListResponse)
        async def find_read_models(
            limit: int = Query(10, description="Maximum number of items to return"),
            offset: int = Query(0, description="Number of items to skip"),
            criteria: Dict[str, Any] = Query({}, description="Search criteria")
        ) -> ReadModelListResponse:
            """Find read models by criteria."""
            result = await read_model_service.find(criteria)
            models = handle_result(result, "Failed to find read models")
            
            # Apply pagination
            paginated = models[offset:offset + limit]
            
            return ReadModelListResponse(
                items=[domain_read_model_to_api(model) for model in paginated],
                count=len(paginated)
            )
        
        # Create a new read model
        @router.post("/", response_model=ReadModelResponse, status_code=201)
        async def create_read_model(
            request: CreateReadModelRequest = Body(..., description="Read model data")
        ) -> ReadModelResponse:
            """Create a new read model."""
            # Create a new read model
            model = model_type(
                id=ReadModelId(value=str(datetime.now(UTC).timestamp())),
                version=1,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                data=request.data,
                metadata=request.metadata
            )
            
            result = await read_model_service.save(model)
            saved_model = handle_result(result, "Failed to create read model")
            
            return domain_read_model_to_api(saved_model)
        
        # Update a read model
        @router.patch("/{id}", response_model=ReadModelResponse)
        async def update_read_model(
            id: str = Path(..., description="The read model ID"),
            request: UpdateReadModelRequest = Body(..., description="Updated read model data")
        ) -> ReadModelResponse:
            """Update a read model."""
            # Get the existing read model
            model_id = ReadModelId(value=id)
            get_result = await read_model_service.get_by_id(model_id)
            model = handle_result(get_result, f"Read model with ID {id} not found")
            
            if model is None:
                raise HTTPException(status_code=404, detail=f"Read model with ID {id} not found")
            
            # Update the data and metadata if provided
            updated_model = model
            
            if request.data is not None:
                updated_model = updated_model.update(request.data)
            
            if request.metadata is not None:
                for key, value in request.metadata.items():
                    updated_model = updated_model.set_metadata(key, value)
            
            # Save the updated model
            save_result = await read_model_service.save(updated_model)
            saved_model = handle_result(save_result, "Failed to update read model")
            
            return domain_read_model_to_api(saved_model)
        
        # Delete a read model
        @router.delete("/{id}", status_code=204)
        async def delete_read_model(id: str = Path(..., description="The read model ID")) -> None:
            """Delete a read model."""
            model_id = ReadModelId(value=id)
            result = await read_model_service.delete(model_id)
            handle_result(result, f"Read model with ID {id} not found")
        
        # If a query service is provided, add query endpoints
        if query_service:
            # Execute a query
            @router.post("/query", response_model=QueryResultResponse)
            async def execute_query(
                request: CreateQueryRequest = Body(..., description="Query to execute")
            ) -> QueryResultResponse:
                """Execute a query."""
                # Create a domain query
                query = DomainQuery(
                    id=QueryId(value=str(datetime.now(UTC).timestamp())),
                    query_type=request.query_type,
                    read_model_type=request.read_model_type,
                    parameters=request.parameters,
                    created_at=datetime.now(UTC)
                )
                
                # Execute the query with metrics
                result = await query_service.execute_with_metrics(query)
                query_result = handle_result(result, "Failed to execute query")
                
                return domain_query_result_to_api(query_result)
        
        return router


class ProjectionEndpoints:
    """
    Factory for creating FastAPI endpoints for projections.
    
    This class provides methods to create API routers for projection management.
    """
    
    @staticmethod
    def create_router(
        projection_type: Type[P],
        prefix: str,
        projection_service: ProjectionServiceProtocol[P],
        projector_service: ProjectorServiceProtocol,
        tags: Optional[List[str]] = None
    ) -> APIRouter:
        """
        Create a FastAPI router for projection management.
        
        Args:
            projection_type: The projection type
            prefix: The URL prefix for the endpoints
            projection_service: The projection service
            projector_service: The projector service
            tags: Optional API tags
            
        Returns:
            FastAPI router
        """
        if tags is None:
            tags = ["Projections"]
        
        router = APIRouter(prefix=prefix, tags=tags)
        
        # Helper function to handle service results
        def handle_result(result: Result[Any], not_found_message: str = "Item not found") -> Any:
            """Handle a service result, raising appropriate HTTP exceptions."""
            if not result.is_success():
                if result.error.code.value == "not_found":
                    raise HTTPException(status_code=404, detail=not_found_message)
                raise HTTPException(
                    status_code=500,
                    detail=f"Internal server error: {result.error.message}"
                )
            return result.value
        
        # Get a projection by ID
        @router.get("/{id}", response_model=ProjectionResponse)
        async def get_projection(id: str = Path(..., description="The projection ID")) -> ProjectionResponse:
            """Get a projection by ID."""
            projection_id = ProjectionId(value=id)
            result = await projection_service.get_by_id(projection_id)
            projection = handle_result(result, f"Projection with ID {id} not found")
            
            if projection is None:
                raise HTTPException(status_code=404, detail=f"Projection with ID {id} not found")
                
            return domain_projection_to_api(projection)
        
        # Get projections by event type
        @router.get("/by-event-type/{event_type}", response_model=ProjectionListResponse)
        async def get_projections_by_event_type(
            event_type: str = Path(..., description="The event type")
        ) -> ProjectionListResponse:
            """Get projections by event type."""
            result = await projection_service.get_by_event_type(event_type)
            projections = handle_result(result, f"Failed to get projections for event type {event_type}")
            
            return ProjectionListResponse(
                items=[domain_projection_to_api(p) for p in projections],
                count=len(projections)
            )
        
        # Create a new projection
        @router.post("/", response_model=ProjectionResponse, status_code=201)
        async def create_projection(
            request: CreateProjectionRequest = Body(..., description="Projection data")
        ) -> ProjectionResponse:
            """Create a new projection."""
            # Create a new projection
            projection = projection_type(
                id=ProjectionId(value=str(datetime.now(UTC).timestamp())),
                name=request.name,
                event_type=request.event_type,
                read_model_type=request.read_model_type,
                projection_type=ProjectionType(request.projection_type),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                is_active=request.is_active,
                configuration=request.configuration
            )
            
            # Save the projection
            save_result = await projection_service.save(projection)
            saved_projection = handle_result(save_result, "Failed to create projection")
            
            # Register with projector
            register_result = await projector_service.register_projection(saved_projection)
            handle_result(register_result, "Failed to register projection with projector")
            
            return domain_projection_to_api(saved_projection)
        
        # Update a projection
        @router.patch("/{id}", response_model=ProjectionResponse)
        async def update_projection(
            id: str = Path(..., description="The projection ID"),
            request: UpdateProjectionRequest = Body(..., description="Updated projection data")
        ) -> ProjectionResponse:
            """Update a projection."""
            # Get the existing projection
            projection_id = ProjectionId(value=id)
            get_result = await projection_service.get_by_id(projection_id)
            projection = handle_result(get_result, f"Projection with ID {id} not found")
            
            if projection is None:
                raise HTTPException(status_code=404, detail=f"Projection with ID {id} not found")
            
            # Update the projection
            if request.name is not None:
                projection.name = request.name
            
            if request.is_active is not None:
                if request.is_active:
                    projection.activate()
                else:
                    projection.deactivate()
            
            if request.configuration is not None:
                projection.update_configuration(request.configuration)
            
            projection.updated_at = datetime.now(UTC)
            
            # Save the updated projection
            save_result = await projection_service.save(projection)
            saved_projection = handle_result(save_result, "Failed to update projection")
            
            return domain_projection_to_api(saved_projection)
        
        # Delete a projection
        @router.delete("/{id}", status_code=204)
        async def delete_projection(id: str = Path(..., description="The projection ID")) -> None:
            """Delete a projection."""
            projection_id = ProjectionId(value=id)
            
            # Unregister from projector first
            unregister_result = await projector_service.unregister_projection(projection_id)
            handle_result(unregister_result, f"Failed to unregister projection with ID {id}")
            
            # Then delete the projection
            delete_result = await projection_service.delete(projection_id)
            handle_result(delete_result, f"Projection with ID {id} not found")
        
        # Projector control endpoints
        @router.post("/projector/start", status_code=204)
        async def start_projector() -> None:
            """Start the projector."""
            result = await projector_service.start()
            handle_result(result, "Failed to start projector")
        
        @router.post("/projector/stop", status_code=204)
        async def stop_projector() -> None:
            """Stop the projector."""
            result = await projector_service.stop()
            handle_result(result, "Failed to stop projector")
        
        @router.post("/projector/rebuild", status_code=204)
        async def rebuild_projector() -> None:
            """Rebuild all read models."""
            result = await projector_service.rebuild_all()
            handle_result(result, "Failed to rebuild read models")
        
        return router


# Export a function to create all read model related endpoints

def create_read_model_endpoints(app: APIRouter) -> None:
    """
    Create all read model related endpoints.
    
    Args:
        app: The FastAPI router to attach endpoints to
    """
    # This function would be customized for the specific read model types
    # in a real application. This is just an example.
    
    # Example: Create endpoints for a specific read model type
    # read_model_service = inject_dependency(ReadModelServiceProtocol[ExampleReadModel])
    # query_service = inject_dependency(QueryServiceProtocol[ExampleQuery, ExampleReadModel])
    # app.include_router(
    #     ReadModelEndpoints.create_router(
    #         model_type=ExampleReadModel,
    #         prefix="/api/read-models/example",
    #         read_model_service=read_model_service,
    #         query_service=query_service,
    #         tags=["Example Read Models"]
    #     )
    # )
    
    # Example: Create endpoints for projection management
    # projection_service = inject_dependency(ProjectionServiceProtocol[ExampleProjection])
    # projector_service = inject_dependency(ProjectorServiceProtocol)
    # app.include_router(
    #     ProjectionEndpoints.create_router(
    #         projection_type=ExampleProjection,
    #         prefix="/api/projections",
    #         projection_service=projection_service,
    #         projector_service=projector_service,
    #         tags=["Projections"]
    #     )
    # )
    
    # In a real application, you would include multiple routers for different
    # read model types based on your domain requirements.
    pass