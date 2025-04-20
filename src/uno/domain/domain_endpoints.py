"""
API endpoints for the Attributes module using the Domain approach.

This module provides FastAPI endpoints for attribute entities using the domain-driven
design approach with domain services and entities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, Path, Query, Body
from fastapi.responses import JSONResponse

from uno.domain.api_integration import (
    create_domain_router,
    domain_endpoint,
)
from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.framework import FrameworkError
from uno.dependencies.scoped_container import get_service
from uno.attributes.domain_services import (
    AttributeService,
    AttributeTypeService,
)
from uno.attributes.entities import (
    Attribute,
    AttributeType,
)


# Create routers using the domain_router factory
attribute_router = create_domain_router(
    entity_type=Attribute,
    service_type=AttributeService,
    prefix="/api/attributes",
    tags=["Attributes"],
)

attribute_type_router = create_domain_router(
    entity_type=AttributeType,
    service_type=AttributeTypeService,
    prefix="/api/attribute-types",
    tags=["Attributes", "Attribute Types"],
)


# Add custom endpoints for attribute types


@attribute_type_router.get("/by-name/{name}")
@domain_endpoint(entity_type=AttributeType, service_type=AttributeTypeService)
async def get_attribute_type_by_name(
    name: str = Path(..., description="The name of the attribute type"),
    group_id: str | None = Query(None, description="Optional group ID to filter by"),
    service: AttributeTypeService = Depends(lambda: get_service(AttributeTypeService)),
):
    """Get an attribute type by name."""
    result = await service.find_by_name(name, group_id)

    if result.is_failure:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    if not result.value:
        return JSONResponse(
            status_code=404,
            content={
                "error": {
                    "code": "ATTRIBUTE_TYPE_NOT_FOUND",
                    "message": "Attribute type not found",
                    "details": {"name": name, "group_id": group_id}
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )


@attribute_type_router.get("/{id}/hierarchy")
@domain_endpoint(entity_type=AttributeType, service_type=AttributeTypeService)
async def get_attribute_type_hierarchy(
    id: str = Path(..., description="The ID of the root attribute type"),
    service: AttributeTypeService = Depends(lambda: get_service(AttributeTypeService)),
):
    """Get a hierarchy of attribute types starting from a root."""
    result = await service.get_hierarchy(id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=[attr_type.to_dict() for attr_type in result.value]
    )


@attribute_type_router.post("/{id}/value-types/{meta_type_id}")
@domain_endpoint(entity_type=AttributeType, service_type=AttributeTypeService)
async def add_value_type(
    id: str = Path(..., description="The ID of the attribute type"),
    meta_type_id: str = Path(..., description="The ID of the meta type to add"),
    service: AttributeTypeService = Depends(lambda: get_service(AttributeTypeService)),
):
    """Add a value type to an attribute type."""
    result = await service.add_value_type(id, meta_type_id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )


@attribute_type_router.post("/{id}/describes/{meta_type_id}")
@domain_endpoint(entity_type=AttributeType, service_type=AttributeTypeService)
async def add_describable_type(
    id: str = Path(..., description="The ID of the attribute type"),
    meta_type_id: str = Path(..., description="The ID of the meta type to add"),
    service: AttributeTypeService = Depends(lambda: get_service(AttributeTypeService)),
):
    """Add a meta type that an attribute type can describe."""
    result = await service.add_describable_type(id, meta_type_id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )


# Add custom endpoints for attributes


@attribute_router.get("/by-type/{attribute_type_id}")
@domain_endpoint(entity_type=Attribute, service_type=AttributeService)
async def get_attributes_by_type(
    attribute_type_id: str = Path(..., description="The ID of the attribute type"),
    service: AttributeService = Depends(lambda: get_service(AttributeService)),
):
    """Get attributes by attribute type."""
    result = await service.find_by_attribute_type(attribute_type_id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return [attr.to_dict() for attr in result.value]


@attribute_router.get("/{id}/with-related")
@domain_endpoint(entity_type=Attribute, service_type=AttributeService)
async def get_attribute_with_related(
    id: str = Path(..., description="The ID of the attribute"),
    service: AttributeService = Depends(lambda: get_service(AttributeService)),
):
    """Get an attribute with its related data."""
    result = await service.get_with_related_data(id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )


@attribute_router.post("/{id}/values/{value_id}")
@domain_endpoint(entity_type=Attribute, service_type=AttributeService)
async def add_value_to_attribute(
    id: str = Path(..., description="The ID of the attribute"),
    value_id: str = Path(..., description="The ID of the value to add"),
    service: AttributeService = Depends(lambda: get_service(AttributeService)),
):
    """Add a value to an attribute."""
    result = await service.add_value(id, value_id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )


@attribute_router.post("/{id}/meta-records/{meta_record_id}")
@domain_endpoint(entity_type=Attribute, service_type=AttributeService)
async def add_meta_record_to_attribute(
    id: str = Path(..., description="The ID of the attribute"),
    meta_record_id: str = Path(..., description="The ID of the meta record to add"),
    service: AttributeService = Depends(lambda: get_service(AttributeService)),
):
    """Add a meta record to an attribute."""
    result = await service.add_meta_record(id, meta_record_id)

    if result.is_failure:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": result.error.code,
                    "message": result.error.message,
                    "details": result.error.details
                }
            }
        )

    return JSONResponse(
        status_code=200,
        content=result.value.to_dict()
    )
