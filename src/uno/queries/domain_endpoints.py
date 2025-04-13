"""Domain endpoints for the Queries module."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Body, Query
from pydantic import BaseModel, Field

from uno.api.endpoint import DomainRouter, domain_endpoint
from uno.core.errors.result import Result
from uno.queries.domain_provider import (
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


class QueryPathCreate(BaseModel):
    """Schema for creating a query path."""

    path_name: str = Field(..., description="The name of the path")
    meta_type_id: str = Field(..., description="The ID of the meta type")
    attribute_id: Optional[str] = Field(None, description="The ID of the attribute")
    description: Optional[str] = Field(None, description="A description of the path")


class QueryPathUpdate(BaseModel):
    """Schema for updating a query path."""

    path_name: Optional[str] = Field(None, description="The name of the path")
    meta_type_id: Optional[str] = Field(None, description="The ID of the meta type")
    attribute_id: Optional[str] = Field(None, description="The ID of the attribute")
    description: Optional[str] = Field(None, description="A description of the path")


class QueryPathResponse(BaseModel):
    """Schema for a query path response."""

    id: str = Field(..., description="The ID of the query path")
    path_name: str = Field(..., description="The name of the path")
    meta_type_id: str = Field(..., description="The ID of the meta type")
    attribute_id: Optional[str] = Field(None, description="The ID of the attribute")
    description: Optional[str] = Field(None, description="A description of the path")


class QueryValueCreate(BaseModel):
    """Schema for creating a query value."""

    query_path_id: str = Field(..., description="The ID of the query path")
    value: Any = Field(..., description="The value to filter by")
    lookup_type: str = Field("eq", description="The lookup type (eq, lt, gt, etc.)")


class QueryValueUpdate(BaseModel):
    """Schema for updating a query value."""

    query_path_id: Optional[str] = Field(None, description="The ID of the query path")
    value: Optional[Any] = Field(None, description="The value to filter by")
    lookup_type: Optional[str] = Field(None, description="The lookup type (eq, lt, gt, etc.)")


class QueryValueResponse(BaseModel):
    """Schema for a query value response."""

    id: str = Field(..., description="The ID of the query value")
    query_path_id: str = Field(..., description="The ID of the query path")
    query_id: str = Field(..., description="The ID of the query")
    value: Any = Field(..., description="The value to filter by")
    lookup_type: str = Field(..., description="The lookup type (eq, lt, gt, etc.)")


class QueryCreate(BaseModel):
    """Schema for creating a query."""

    name: str = Field(..., description="The name of the query")
    query_meta_type_id: str = Field(..., description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: str = Field("INCLUDE", description="Whether to include or exclude values")
    match_values: str = Field("AND", description="Whether to match any or all values")
    include_queries: str = Field("INCLUDE", description="Whether to include or exclude queries")
    match_queries: str = Field("AND", description="Whether to match any or all queries")
    values: List[Dict[str, Any]] = Field([], description="The values for the query")


class QueryUpdate(BaseModel):
    """Schema for updating a query."""

    name: Optional[str] = Field(None, description="The name of the query")
    query_meta_type_id: Optional[str] = Field(None, description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: Optional[str] = Field(None, description="Whether to include or exclude values")
    match_values: Optional[str] = Field(None, description="Whether to match any or all values")
    include_queries: Optional[str] = Field(None, description="Whether to include or exclude queries")
    match_queries: Optional[str] = Field(None, description="Whether to match any or all queries")
    values: Optional[List[Dict[str, Any]]] = Field(None, description="The values for the query")


class QueryResponse(BaseModel):
    """Schema for a query response."""

    id: str = Field(..., description="The ID of the query")
    name: str = Field(..., description="The name of the query")
    query_meta_type_id: str = Field(..., description="The ID of the meta type")
    description: Optional[str] = Field(None, description="A description of the query")
    include_values: str = Field(..., description="Whether to include or exclude values")
    match_values: str = Field(..., description="Whether to match any or all values")
    include_queries: str = Field(..., description="Whether to include or exclude queries")
    match_queries: str = Field(..., description="Whether to match any or all queries")
    query_values: List[QueryValueResponse] = Field([], description="The values for the query")


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
    meta_type_id: Optional[str] = Query(None, description="Filter by meta type ID"),
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
    data_dict = query_data.dict(exclude_unset=True)
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


@query_router.post("/{query_id}/execute/{entity_type}")
async def execute_query(
    query_id: str = Path(..., description="The ID of the query"),
    entity_type: str = Path(..., description="The type of entity to filter"),
    filters: Optional[Dict[str, Any]] = Body(None, description="Additional filters to apply"),
    query_service: QueryService = Depends(get_query_service),
):
    """Execute a query to filter entities."""
    result = await query_service.execute_query(query_id, entity_type, filters)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return {"results": result.value}