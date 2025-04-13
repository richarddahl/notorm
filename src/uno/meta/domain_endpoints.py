"""
API endpoints for the Meta module using the Domain approach.

This module provides FastAPI endpoints for meta entities using the domain-driven
design approach with domain services and entities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body

from uno.domain.api_integration import (
    create_domain_router,
    domain_endpoint,
)
from uno.dependencies.scoped_container import get_service
from uno.meta.domain_services import (
    MetaTypeService,
    MetaRecordService,
)
from uno.meta.entities import (
    MetaType,
    MetaRecord,
)


# Create routers using the domain_router factory
meta_type_router = create_domain_router(
    entity_type=MetaType,
    service_type=MetaTypeService,
    prefix="/api/meta-types",
    tags=["Meta", "Meta Types"],
)

meta_record_router = create_domain_router(
    entity_type=MetaRecord,
    service_type=MetaRecordService,
    prefix="/api/meta-records",
    tags=["Meta", "Meta Records"],
)


# Custom endpoints for meta types

@meta_type_router.post("/register")
@domain_endpoint(entity_type=MetaType, service_type=MetaTypeService)
async def register_meta_type(
    id: str = Query(..., description="The ID of the meta type (typically a table name)"),
    name: Optional[str] = Query(None, description="Optional display name"),
    description: Optional[str] = Query(None, description="Optional description"),
    service: MetaTypeService = Depends(lambda: get_service(MetaTypeService))
):
    """Register a new meta type in the system."""
    result = await service.register_meta_type(id, name, description)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@meta_type_router.get("/all")
@domain_endpoint(entity_type=MetaType, service_type=MetaTypeService)
async def get_all_meta_types(
    service: MetaTypeService = Depends(lambda: get_service(MetaTypeService))
):
    """Get all meta types in the system."""
    result = await service.get_all_types()
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [meta_type.to_dict() for meta_type in result.value]


@meta_type_router.get("/{id}/records")
@domain_endpoint(entity_type=MetaType, service_type=MetaTypeService)
async def get_meta_type_with_records(
    id: str = Path(..., description="The ID of the meta type"),
    limit: int = Query(100, description="Maximum number of records to retrieve"),
    service: MetaTypeService = Depends(lambda: get_service(MetaTypeService))
):
    """Get a meta type with its associated records."""
    result = await service.get_with_records(id, limit)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


# Custom endpoints for meta records

@meta_record_router.post("/create")
@domain_endpoint(entity_type=MetaRecord, service_type=MetaRecordService)
async def create_meta_record(
    meta_type_id: str = Query(..., description="The ID of the meta type"),
    record_id: Optional[str] = Query(None, description="Optional record ID (will be generated if not provided)"),
    service: MetaRecordService = Depends(lambda: get_service(MetaRecordService))
):
    """Create a new meta record."""
    result = await service.create_record(meta_type_id, record_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@meta_record_router.get("/by-type/{meta_type_id}")
@domain_endpoint(entity_type=MetaRecord, service_type=MetaRecordService)
async def get_records_by_meta_type(
    meta_type_id: str = Path(..., description="The ID of the meta type"),
    limit: int = Query(100, description="Maximum number of records to retrieve"),
    service: MetaRecordService = Depends(lambda: get_service(MetaRecordService))
):
    """Get meta records by meta type."""
    result = await service.find_by_meta_type(meta_type_id, limit)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [record.to_dict() for record in result.value]


@meta_record_router.get("/{id}/with-type")
@domain_endpoint(entity_type=MetaRecord, service_type=MetaRecordService)
async def get_meta_record_with_type(
    id: str = Path(..., description="The ID of the meta record"),
    service: MetaRecordService = Depends(lambda: get_service(MetaRecordService))
):
    """Get a meta record with its associated meta type."""
    result = await service.get_with_meta_type(id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


@meta_record_router.post("/{id}/attributes/{attribute_id}")
@domain_endpoint(entity_type=MetaRecord, service_type=MetaRecordService)
async def add_attribute_to_meta_record(
    id: str = Path(..., description="The ID of the meta record"),
    attribute_id: str = Path(..., description="The ID of the attribute to add"),
    service: MetaRecordService = Depends(lambda: get_service(MetaRecordService))
):
    """Add an attribute to a meta record."""
    result = await service.add_attribute(id, attribute_id)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return result.value.to_dict()


def register_meta_routers(app):
    """
    Register all meta routers with a FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    app.include_router(meta_type_router)
    app.include_router(meta_record_router)