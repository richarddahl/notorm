"""Domain endpoints for the Queries module."""
from typing import Any, Dict, List, Optional, Tuple, Type, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query as QueryParam
from pydantic import BaseModel, Field

from uno.api.endpoint import DomainRouter, domain_endpoint
from uno.core.errors.result import Result

    get_query_path_service,
    get_query_value_service,
    get_query_service,
)
from uno.queries.domain_services import (
    QueryPathService,
    QueryValueService,
    QueryService,
)
from uno.queries.entities import Query, QueryPath, QueryValue
from uno.enums import Include, Match


class QueryPathCreate(BaseModel):
    """Schema for creating a query path."""

    source_meta_type_id: str = Field(..., description="The ID of the source meta type")
    target_meta_type_id: str = Field(..., description="The ID of the target meta type")
    cypher_path: str = Field(..., description="The Cypher path expression")
    data_type: str = Field(..., description="The data type of the path result")
    path_name: Optional[str] = Field(None, description="The name of the path")


class QueryPathUpdate(BaseModel):
    """Schema for updating a query path."""

    source_meta_type_id: Optional[str] = Field(None, description="The ID of the source meta type")
    target_meta_type_id: Optional[str] = Field(None, description="The ID of the target meta type")
    cypher_path: Optional[str] = Field(None, description="The Cypher path expression")
    data_type: Optional[str] = Field(None, description="The data type of the path result")
    path_name: Optional[str] = Field(None, description="The name of the path")


class QueryPathResponse(BaseModel):
    """Schema for a query path response."""

    id: str = Field(..., description="The ID of the query path")
    source_meta_type_id: str = Field(..., description="The ID of the source meta type")
    target_meta_type_id: str = Field(..., description="The ID of the target meta type")
    cypher_path: str = Field(..., description="The Cypher path expression")
    data_type: str = Field(..., description="The data type of the path result")
    path_name: Optional[str] = Field(None, description="The name of the path")


class QueryPathGenerateRequest(BaseModel):
    """Schema for generating query paths for a model."""

    model_name: str = Field(..., description="The name of the model to generate paths for")


class QueryValueCreate(BaseModel):
    """Schema for creating a query value."""

    query_path_id: str = Field(..., description="The ID of the query path")
    include: Include = Field(Include.INCLUDE, description="Whether to include or exclude matches")
    match: Match = Field(Match.AND, description="AND/OR match type")
    lookup: str = Field("equal", description="The lookup type (equal, contains, etc.)")
    values: List[Any] = Field(default_factory=list, description="The values to filter by")


class QueryValueUpdate(BaseModel):
    """Schema for updating a query value."""

    query_path_id: Optional[str] = Field(None, description="The ID of the query path")
    include: Optional[Include] = Field(None, description="Whether to include or exclude matches")
    match: Optional[Match] = Field(None, description="AND/OR match type")
    lookup: Optional[str] = Field(None, description="The lookup type (equal, contains, etc.)")
    values: Optional[List[Any]] = Field(None, description="The values to filter by")


class QueryValueResponse(BaseModel):
    """Schema for a query value response."""

    id: str = Field(..., description="The ID of the query value")
    query_path_id: str = Field(..., description="The ID of the query path")
    include: Include = Field(..., description="Whether to include or exclude matches")
    match: Match = Field(..., description="AND/OR match type")
    lookup: str = Field(..., description="The lookup type (equal, contains, etc.)")
    values: List[Any] = Field(..., description="The values to filter by")


class QueryCreate(BaseModel):
    """Schema for creating a query."""

    name: str = Field(..., description="The name of the query")
    query_meta_type_id: str = Field(..., description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: Include = Field(Include.INCLUDE, description="Whether to include or exclude values")
    match_values: Match = Field(Match.AND, description="Whether to match any or all values")
    include_queries: Include = Field(Include.INCLUDE, description="Whether to include or exclude queries")
    match_queries: Match = Field(Match.AND, description="Whether to match any or all queries")
    values: List[Dict[str, Any]] = Field(default_factory=list, description="The values for the query")


class QueryUpdate(BaseModel):
    """Schema for updating a query."""

    name: Optional[str] = Field(None, description="The name of the query")
    query_meta_type_id: Optional[str] = Field(None, description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: Optional[Include] = Field(None, description="Whether to include or exclude values")
    match_values: Optional[Match] = Field(None, description="Whether to match any or all values")
    include_queries: Optional[Include] = Field(None, description="Whether to include or exclude queries")
    match_queries: Optional[Match] = Field(None, description="Whether to match any or all queries")
    values: Optional[List[Dict[str, Any]]] = Field(None, description="The values for the query")


class QueryResponse(BaseModel):
    """Schema for a query response."""

    id: str = Field(..., description="The ID of the query")
    name: str = Field(..., description="The name of the query")
    query_meta_type_id: str = Field(..., description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: Include = Field(..., description="Whether to include or exclude values")
    match_values: Match = Field(..., description="Whether to match any or all values")
    include_queries: Include = Field(..., description="Whether to include or exclude queries")
    match_queries: Match = Field(..., description="Whether to match any or all queries")
    query_values: List[QueryValueResponse] = Field(default_factory=list, description="The values for the query")


class QueryExecuteRequest(BaseModel):
    """Schema for executing a query."""

    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters to apply")
    force_refresh: bool = Field(False, description="Whether to bypass the cache")


class QueryExecuteResponse(BaseModel):
    """Schema for query execution results."""

    results: List[str] = Field(..., description="The IDs of matching records")
    count: int = Field(..., description="The number of matching records")


class QueryCountResponse(BaseModel):
    """Schema for query count results."""

    count: int = Field(..., description="The number of matching records")


class QueryCheckRecordRequest(BaseModel):
    """Schema for checking if a record matches a query."""

    record_id: str = Field(..., description="The ID of the record to check")
    force_refresh: bool = Field(False, description="Whether to bypass the cache")


class QueryCheckRecordResponse(BaseModel):
    """Schema for record match check results."""

    matches: bool = Field(..., description="Whether the record matches the query")


class QueryCacheInvalidateRequest(BaseModel):
    """Schema for invalidating the query cache."""

    meta_type_id: Optional[str] = Field(None, description="The ID of the meta type to invalidate cache for")


class QueryCacheInvalidateResponse(BaseModel):
    """Schema for cache invalidation results."""

    invalidated_count: int = Field(..., description="The number of cache entries invalidated")


class QueryWithFiltersRequest(BaseModel):
    """Schema for executing a query with filters."""

    entity_type: str = Field(..., description="The type of entity to filter")
    filters: Dict[str, Any] = Field(default_factory=dict, description="The filters to apply")


class QueryWithFiltersResponse(BaseModel):
    """Schema for query with filters results."""

    results: List[Dict[str, Any]] = Field(..., description="The matching entities")
    count: int = Field(..., description="The number of matching entities")


# Create routers
query_path_router = DomainRouter[QueryPath, QueryPathCreate, QueryPathUpdate, QueryPathResponse](
    prefix="/query-paths",
    tags=["Query Paths"],
    entity_type=QueryPath,
    service_type=QueryPathService,
    create_schema=QueryPathCreate,
    update_schema=QueryPathUpdate,
    response_schema=QueryPathResponse,
    get_service=get_query_path_service,
)

query_value_router = DomainRouter[QueryValue, QueryValueCreate, QueryValueUpdate, QueryValueResponse](
    prefix="/query-values",
    tags=["Query Values"],
    entity_type=QueryValue,
    service_type=QueryValueService,
    create_schema=QueryValueCreate,
    update_schema=QueryValueUpdate,
    response_schema=QueryValueResponse,
    get_service=get_query_value_service,
)

query_router = APIRouter(
    prefix="/queries",
    tags=["Queries"],
)


@query_router.post("", response_model=QueryResponse)
async def create_query(
    query_data: QueryCreate = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Create a new query with values."""
    # Create a query entity
    query = Query(
        name=query_data.name,
        query_meta_type_id=query_data.query_meta_type_id,
        description=query_data.description,
        include_values=query_data.include_values,
        match_values=query_data.match_values,
        include_queries=query_data.include_queries,
        match_queries=query_data.match_queries,
    )
    
    # Create the query with values
    result = await query_service.create_with_values(query, query_data.values)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value


@query_router.get("", response_model=List[QueryResponse])
async def list_queries(
    meta_type_id: Optional[str] = QueryParam(None, description="Filter by meta type ID"),
    query_service: QueryService = Depends(get_query_service),
):
    """List all queries with values."""
    result = await query_service.list_with_values(meta_type_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value


@query_router.get("/{query_id}", response_model=QueryResponse)
async def get_query(
    query_id: str = Path(..., description="The ID of the query"),
    query_service: QueryService = Depends(get_query_service),
):
    """Get a query with values by ID."""
    result = await query_service.get_with_values(query_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value


@query_router.put("/{query_id}", response_model=QueryResponse)
async def update_query(
    query_id: str = Path(..., description="The ID of the query"),
    query_data: QueryUpdate = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Update a query with values."""
    data_dict = query_data.model_dump(exclude_unset=True)
    values = data_dict.pop("values", [])
    
    result = await query_service.update_with_values(query_id, data_dict, values)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value


@query_router.delete("/{query_id}")
async def delete_query(
    query_id: str = Path(..., description="The ID of the query"),
    query_service: QueryService = Depends(get_query_service),
):
    """Delete a query with values."""
    result = await query_service.delete_with_values(query_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return {"status": "success", "message": "Query deleted"}


@query_router.post("/{query_id}/execute", response_model=QueryExecuteResponse)
async def execute_query(
    query_id: str = Path(..., description="The ID of the query"),
    execute_request: QueryExecuteRequest = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Execute a query and return matching record IDs."""
    result = await query_service.execute_query(
        query_id=query_id,
        filters=execute_request.filters,
        force_refresh=execute_request.force_refresh,
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    # Return the results with a count
    record_ids = result.value
    return QueryExecuteResponse(results=record_ids, count=len(record_ids))


@query_router.post("/{query_id}/count", response_model=QueryCountResponse)
async def count_query_matches(
    query_id: str = Path(..., description="The ID of the query"),
    count_request: Optional[QueryExecuteRequest] = Body(None),
    query_service: QueryService = Depends(get_query_service),
):
    """Count the number of records that match a query."""
    force_refresh = False
    if count_request:
        force_refresh = count_request.force_refresh
        
    result = await query_service.count_query_matches(
        query_id=query_id,
        force_refresh=force_refresh,
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return QueryCountResponse(count=result.value)


@query_router.post("/{query_id}/check-record", response_model=QueryCheckRecordResponse)
async def check_record_matches_query(
    query_id: str = Path(..., description="The ID of the query"),
    check_request: QueryCheckRecordRequest = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Check if a record matches a query."""
    result = await query_service.check_record_matches_query(
        query_id=query_id,
        record_id=check_request.record_id,
        force_refresh=check_request.force_refresh,
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return QueryCheckRecordResponse(matches=result.value)


@query_router.post("/cache/invalidate", response_model=QueryCacheInvalidateResponse)
async def invalidate_cache(
    invalidate_request: QueryCacheInvalidateRequest = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Invalidate the query cache."""
    result = await query_service.invalidate_cache(
        meta_type_id=invalidate_request.meta_type_id,
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return QueryCacheInvalidateResponse(invalidated_count=result.value)


@query_router.post("/execute-with-filters", response_model=QueryWithFiltersResponse)
async def execute_query_with_filters(
    filters_request: QueryWithFiltersRequest = Body(...),
    query_service: QueryService = Depends(get_query_service),
):
    """Execute a query with filters."""
    result = await query_service.execute_query_with_filters(
        entity_type=filters_request.entity_type,
        filters=filters_request.filters,
    )
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    entities, count = result.value
    return QueryWithFiltersResponse(results=entities, count=count)


@query_path_router.post("/generate", response_model=List[QueryPathResponse])
async def generate_query_paths(
    generate_request: QueryPathGenerateRequest = Body(...),
    query_path_service: QueryPathService = Depends(get_query_path_service),
):
    """Generate query paths for a model."""
    # Import the model class dynamically
    try:
        from uno.dependencies.service import get_entity_model_class
        model_class = get_entity_model_class(generate_request.model_name)
        
        if not model_class:
            raise HTTPException(status_code=400, detail=f"Unknown model: {generate_request.model_name}")
        
        result = await query_path_service.generate_for_model(model_class)
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
        
        return result.value
    except ImportError as e:
        raise HTTPException(status_code=400, detail=f"Could not import model: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating query paths: {str(e)}")