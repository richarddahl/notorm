"""
API endpoints for the Values module using the Domain approach.

This module provides FastAPI endpoints for value entities using the domain-driven
design approach with domain services and entities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Path, Query, Body
import datetime
import decimal

from uno.domain.api_integration import (
    create_domain_router,
    DomainRouter,
    domain_endpoint,
)
from uno.dependencies.scoped_container import get_service
from uno.values.domain_services import (
    AttachmentService,
    BooleanValueService,
    DateTimeValueService,
    DateValueService,
    DecimalValueService,
    IntegerValueService,
    TextValueService,
    TimeValueService,
)
from uno.values.entities import (
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)


# Create routers using the DomainRouter factory
attachment_router = create_domain_router(
    entity_type=Attachment,
    service_type=AttachmentService,
    prefix="/api/values/attachments",
    tags=["Values", "Attachments"],
)

boolean_value_router = create_domain_router(
    entity_type=BooleanValue,
    service_type=BooleanValueService,
    prefix="/api/values/booleans",
    tags=["Values", "Boolean Values"],
)

datetime_value_router = create_domain_router(
    entity_type=DateTimeValue,
    service_type=DateTimeValueService,
    prefix="/api/values/datetimes",
    tags=["Values", "DateTime Values"],
)

date_value_router = create_domain_router(
    entity_type=DateValue,
    service_type=DateValueService,
    prefix="/api/values/dates",
    tags=["Values", "Date Values"],
)

decimal_value_router = create_domain_router(
    entity_type=DecimalValue,
    service_type=DecimalValueService,
    prefix="/api/values/decimals",
    tags=["Values", "Decimal Values"],
)

integer_value_router = create_domain_router(
    entity_type=IntegerValue,
    service_type=IntegerValueService,
    prefix="/api/values/integers",
    tags=["Values", "Integer Values"],
)

text_value_router = create_domain_router(
    entity_type=TextValue,
    service_type=TextValueService,
    prefix="/api/values/texts",
    tags=["Values", "Text Values"],
)

time_value_router = create_domain_router(
    entity_type=TimeValue,
    service_type=TimeValueService,
    prefix="/api/values/times",
    tags=["Values", "Time Values"],
)


# Additional custom endpoints for attachments
@attachment_router.get("/by-path/{file_path:path}")
@domain_endpoint(entity_type=Attachment, service_type=AttachmentService)
async def get_attachment_by_path(
    file_path: str = Path(..., description="The file path to search for"),
    service: AttachmentService = Depends(lambda: get_service(AttachmentService))
):
    """Get an attachment by file path."""
    result = await service.find_by_file_path(file_path)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    if not result.value:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    return result.value.to_dict()


# Search endpoints for all value types
@text_value_router.get("/search")
@domain_endpoint(entity_type=TextValue, service_type=TextValueService)
async def search_text_values(
    term: str = Query(..., description="Search term"),
    limit: int = Query(20, description="Maximum number of results to return"),
    service: TextValueService = Depends(lambda: get_service(TextValueService))
):
    """Search for text values."""
    result = await service.search(term, limit)
    
    if result.is_failure:
        raise HTTPException(status_code=400, detail=str(result.error))
    
    return [value.to_dict() for value in result.value]


def register_values_routers(app):
    """
    Register all value routers with a FastAPI application.
    
    Args:
        app: The FastAPI application
    """
    app.include_router(attachment_router)
    app.include_router(boolean_value_router)
    app.include_router(datetime_value_router)
    app.include_router(date_value_router)
    app.include_router(decimal_value_router)
    app.include_router(integer_value_router)
    app.include_router(text_value_router)
    app.include_router(time_value_router)