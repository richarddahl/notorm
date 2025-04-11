"""
API endpoints for the meta domain.

This module provides FastAPI endpoints for the meta domain,
using dependency injection for services and repositories.

IMPORTANT NOTE:
This module uses the dependency injection pattern as an alternative 
to the standard UnoObj approach. It demonstrates how to build API
endpoints with repositories and services.
"""

from typing import List, Optional, Dict, Any
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.fastapi import get_db_session, get_repository
from uno.meta.models import MetaTypeModel, MetaRecordModel
from uno.meta.repositories import MetaTypeRepository, MetaRecordRepository
from uno.meta.services import MetaTypeService, MetaRecordService
from uno.schema.schema_manager import UnoSchemaManager

# Create schema manager for generating response models
schema_manager = UnoSchemaManager()

# Generate Pydantic schemas for our models
MetaTypeSchema = schema_manager.get_schema(MetaTypeModel)
MetaTypeListSchema = schema_manager.get_list_schema(MetaTypeModel)
MetaRecordSchema = schema_manager.get_schema(MetaRecordModel)
MetaRecordListSchema = schema_manager.get_list_schema(MetaRecordModel)

# Create router
router = APIRouter(prefix="/api/v1.0", tags=["Metadata"])


# Dependencies for services
def get_meta_type_service(
    repository: MetaTypeRepository = Depends(get_repository(MetaTypeRepository))
) -> MetaTypeService:
    """Get a MetaTypeService instance."""
    return MetaTypeService(repository)


def get_meta_record_service(
    repository: MetaRecordRepository = Depends(get_repository(MetaRecordRepository)),
    type_service: MetaTypeService = Depends(get_meta_type_service)
) -> MetaRecordService:
    """Get a MetaRecordService instance."""
    return MetaRecordService(repository, type_service=type_service)


@router.get(
    "/meta-types",
    response_model=MetaTypeListSchema,
    summary="List meta types",
    description="Retrieve a list of all meta types"
)
async def list_meta_types(
    service: MetaTypeService = Depends(get_meta_type_service)
):
    """List all meta types."""
    types = await service.execute()
    
    # Convert to schema
    type_schemas = [MetaTypeSchema.model_validate(t) for t in types]
    return {"items": type_schemas, "count": len(type_schemas)}


@router.get(
    "/meta-types/{type_id}",
    response_model=MetaTypeSchema,
    summary="Get meta type",
    description="Retrieve a specific meta type by ID"
)
async def get_meta_type(
    type_id: str,
    service: MetaTypeService = Depends(get_meta_type_service)
):
    """Get a specific meta type by ID."""
    meta_type = await service.get_type(type_id)
    
    if not meta_type:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta type with ID {type_id} not found"
        )
    
    return MetaTypeSchema.model_validate(meta_type)


@router.get(
    "/meta-records",
    response_model=MetaRecordListSchema,
    summary="List meta records",
    description="Retrieve a list of meta records with optional filtering"
)
async def list_meta_records(
    type_id: Optional[str] = Query(None, description="Filter by meta type ID"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    service: MetaRecordService = Depends(get_meta_record_service)
):
    """List meta records with optional filtering."""
    records = await service.execute(
        type_id=type_id,
        limit=limit,
        offset=offset
    )
    
    # Convert to schema
    record_schemas = [MetaRecordSchema.model_validate(r) for r in records]
    return {"items": record_schemas, "count": len(record_schemas)}


@router.get(
    "/meta-records/{record_id}",
    response_model=MetaRecordSchema,
    summary="Get meta record",
    description="Retrieve a specific meta record by ID"
)
async def get_meta_record(
    record_id: str,
    service: MetaRecordService = Depends(get_meta_record_service)
):
    """Get a specific meta record by ID."""
    records = await service.execute(record_id=record_id)
    
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Meta record with ID {record_id} not found"
        )
    
    return MetaRecordSchema.model_validate(records[0])


@router.post(
    "/meta-records",
    response_model=MetaRecordSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create meta record",
    description="Create a new meta record"
)
async def create_meta_record(
    record_id: str = Query(..., description="The record ID"),
    type_id: str = Query(..., description="The meta type ID"),
    service: MetaRecordService = Depends(get_meta_record_service)
):
    """Create a new meta record."""
    record = await service.create_record(record_id, type_id)
    
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not create meta record. Type '{type_id}' may not exist."
        )
    
    return MetaRecordSchema.model_validate(record)