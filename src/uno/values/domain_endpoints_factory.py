# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain-driven API endpoints for the Values module.

This module provides FastAPI endpoints for value operations using 
the domain-driven design approach with repositories, entities, and DTOs.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime, time
from decimal import Decimal
import os

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    File, 
    UploadFile, 
    Form, 
    Request, 
    Response, 
    status
)
from fastapi.responses import FileResponse

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.core.errors.result import Result
from uno.values.repositories import (
    BooleanValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
from uno.values.entities import (
    BaseValue,
    BooleanValue,
    IntegerValue,
    TextValue,
    DecimalValue,
    DateValue,
    DateTimeValue,
    TimeValue,
    Attachment,
)
from uno.values.schemas import ValueSchemaManagerFactory
from uno.values.dtos import (
    # Base DTOs
    CreateValueDto,
    UpdateValueDto,
    ValueFilterParams,
    
    # Value type-specific view DTOs
    BooleanValueViewDto,
    IntegerValueViewDto,
    TextValueViewDto,
    DecimalValueViewDto,
    DateValueViewDto,
    DateTimeValueViewDto,
    TimeValueViewDto,
    AttachmentViewDto,
)


def register_domain_value_endpoints(
    router: APIRouter,
    boolean_repository: BooleanValueRepository,
    integer_repository: IntegerValueRepository,
    text_repository: TextValueRepository,
    decimal_repository: DecimalValueRepository,
    date_repository: DateValueRepository,
    datetime_repository: DateTimeValueRepository,
    time_repository: TimeValueRepository,
    attachment_repository: AttachmentRepository,
    prefix: str = "/values",
    tags: List[str] = ["Values"],
    dependencies: List[Any] = None,
):
    """
    Register value endpoints with a FastAPI router using domain-driven design.
    
    This function creates and registers standardized CRUD endpoints for each value type,
    providing a consistent API interface while following domain-driven design principles.
    
    Args:
        router: FastAPI router to register endpoints with
        boolean_repository: Repository for boolean values
        integer_repository: Repository for integer values
        text_repository: Repository for text values
        decimal_repository: Repository for decimal values
        date_repository: Repository for date values
        datetime_repository: Repository for datetime values
        time_repository: Repository for time values
        attachment_repository: Repository for file attachments
        prefix: API route prefix
        tags: API tags for documentation
        dependencies: List of FastAPI dependencies for all endpoints
    
    Returns:
        Dict mapping value types to their respective endpoints
    """
    # Initialize endpoint factory
    endpoint_factory = UnoEndpointFactory()
    
    # Create schema managers for each value type
    boolean_schema_manager = ValueSchemaManagerFactory.create_schema_manager("boolean")
    integer_schema_manager = ValueSchemaManagerFactory.create_schema_manager("integer")
    text_schema_manager = ValueSchemaManagerFactory.create_schema_manager("text")
    decimal_schema_manager = ValueSchemaManagerFactory.create_schema_manager("decimal")
    date_schema_manager = ValueSchemaManagerFactory.create_schema_manager("date")
    datetime_schema_manager = ValueSchemaManagerFactory.create_schema_manager("datetime")
    time_schema_manager = ValueSchemaManagerFactory.create_schema_manager("time")
    attachment_schema_manager = ValueSchemaManagerFactory.create_schema_manager("attachment")
    
    # Ensure dependencies list exists
    if dependencies is None:
        dependencies = []
    
    # Create standard CRUD endpoints for each value type
    endpoints = {}
    
    # Boolean Value endpoints
    endpoints["boolean"] = endpoint_factory.create_endpoints(
        app=router,
        repository=boolean_repository,
        entity_type=BooleanValue,
        schema_manager=boolean_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/boolean",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Integer Value endpoints
    endpoints["integer"] = endpoint_factory.create_endpoints(
        app=router,
        repository=integer_repository,
        entity_type=IntegerValue,
        schema_manager=integer_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/integer",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Text Value endpoints
    endpoints["text"] = endpoint_factory.create_endpoints(
        app=router,
        repository=text_repository,
        entity_type=TextValue,
        schema_manager=text_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/text",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Decimal Value endpoints
    endpoints["decimal"] = endpoint_factory.create_endpoints(
        app=router,
        repository=decimal_repository,
        entity_type=DecimalValue,
        schema_manager=decimal_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/decimal",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Date Value endpoints
    endpoints["date"] = endpoint_factory.create_endpoints(
        app=router,
        repository=date_repository,
        entity_type=DateValue,
        schema_manager=date_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/date",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # DateTime Value endpoints
    endpoints["datetime"] = endpoint_factory.create_endpoints(
        app=router,
        repository=datetime_repository,
        entity_type=DateTimeValue,
        schema_manager=datetime_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/datetime",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Time Value endpoints
    endpoints["time"] = endpoint_factory.create_endpoints(
        app=router,
        repository=time_repository,
        entity_type=TimeValue,
        schema_manager=time_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/time",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Attachment endpoints
    endpoints["attachment"] = endpoint_factory.create_endpoints(
        app=router,
        repository=attachment_repository,
        entity_type=Attachment,
        schema_manager=attachment_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{prefix}/attachment",
        endpoint_tags=tags,
        dependencies=dependencies,
    )
    
    # Add specialized endpoints
    
    # Upload attachment endpoint
    @router.post(
        f"{prefix}/attachments/upload",
        response_model=AttachmentViewDto,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        summary="Upload a file attachment",
        description="Upload and create a new file attachment using multipart form data",
        dependencies=dependencies
    )
    async def upload_attachment(
        file: UploadFile = File(...),
        name: str = Form(...),
    ):
        # Define upload directory
        upload_dir = os.path.join(os.getcwd(), "uploads")
        
        # Create directory if it doesn't exist
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        
        try:
            with open(file_path, "wb") as f:
                contents = await file.read()
                f.write(contents)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save file: {str(e)}",
            )
        
        # Create attachment entity
        attachment = Attachment(
            id=None,  # Will be generated by repository
            name=name,
            file_path=file_path
        )
        
        # Save attachment
        result = await attachment_repository.create(attachment)
        
        if result.is_failure:
            # Clean up file if attachment creation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.error),
            )
        
        saved_attachment = result.value
        
        # Convert to DTO
        schema_manager = ValueSchemaManagerFactory.create_schema_manager("attachment")
        attachment_dto = schema_manager.entity_to_dto(saved_attachment)
        
        return attachment_dto
    
    # Download attachment endpoint
    @router.get(
        f"{prefix}/attachments/{{attachment_id}}/download",
        tags=tags,
        summary="Download an attachment",
        description="Download a file attachment by its ID",
        dependencies=dependencies
    )
    async def download_attachment(attachment_id: str):
        # Get attachment
        result = await attachment_repository.get_by_id(attachment_id)
        
        if result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.error),
            )
        
        attachment = result.value
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment with ID {attachment_id} not found",
            )
        
        # Check if file exists
        if not os.path.exists(attachment.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {os.path.basename(attachment.file_path)}",
            )
        
        # Return file response
        return FileResponse(
            path=attachment.file_path,
            filename=os.path.basename(attachment.file_path),
            media_type="application/octet-stream",
        )
    
    # Search endpoint
    @router.get(
        f"{prefix}/{{value_type}}/search",
        response_model=List[Union[
            BooleanValueViewDto,
            IntegerValueViewDto,
            TextValueViewDto,
            DecimalValueViewDto,
            DateValueViewDto,
            DateTimeValueViewDto,
            TimeValueViewDto,
            AttachmentViewDto,
        ]],
        tags=tags,
        summary="Search values by type",
        description="Search for values of a specific type matching the search term",
        dependencies=dependencies
    )
    async def search_values(value_type: str, term: str, limit: int = 20):
        # Determine repository
        repo_mapping = {
            "boolean": boolean_repository,
            "integer": integer_repository,
            "text": text_repository,
            "decimal": decimal_repository,
            "date": date_repository,
            "datetime": datetime_repository,
            "time": time_repository,
            "attachment": attachment_repository,
        }
        
        repository = repo_mapping.get(value_type.lower())
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {value_type}. Must be one of {', '.join(repo_mapping.keys())}",
            )
        
        # Search values
        result = await repository.search(term, limit)
        
        if result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(result.error),
            )
        
        values = result.value
        
        # Convert to DTOs
        schema_manager = ValueSchemaManagerFactory.create_schema_manager(value_type.lower())
        response = [schema_manager.entity_to_dto(value) for value in values]
        
        return response
    
    # Get or create endpoint
    @router.post(
        f"{prefix}/get-or-create",
        response_model=Union[
            BooleanValueViewDto,
            IntegerValueViewDto,
            TextValueViewDto,
            DecimalValueViewDto,
            DateValueViewDto,
            DateTimeValueViewDto,
            TimeValueViewDto,
        ],
        tags=tags,
        summary="Get or create a value",
        description="Get a value by its actual value, or create it if it doesn't exist",
        dependencies=dependencies
    )
    async def get_or_create_value(data: CreateValueDto):
        # Determine repository
        repo_mapping = {
            "boolean": boolean_repository,
            "integer": integer_repository,
            "text": text_repository,
            "decimal": decimal_repository,
            "date": date_repository,
            "datetime": datetime_repository,
            "time": time_repository,
        }
        
        repository = repo_mapping.get(data.value_type.lower())
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {data.value_type}. Must be one of {', '.join(repo_mapping.keys())}",
            )
        
        # Get schema manager
        schema_manager = ValueSchemaManagerFactory.create_schema_manager(data.value_type.lower())
        
        # Convert input to appropriate value entity
        value_class_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue,
        }
        
        value_class = value_class_mapping.get(data.value_type.lower())
        
        # Create entity with value and name
        entity = value_class(
            id=None,  # Will be generated by repository
            value=data.value,
            name=data.name or str(data.value)
        )
        
        # Try to find by value first
        result = await repository.find_by_value(entity.value)
        
        if result.is_success and result.value:
            # Found existing value
            existing_entity = result.value
            return schema_manager.entity_to_dto(existing_entity)
        
        # Create new value
        create_result = await repository.create(entity)
        
        if create_result.is_failure:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(create_result.error),
            )
        
        new_entity = create_result.value
        return schema_manager.entity_to_dto(new_entity)
    
    # Add all specialized endpoints to the dict
    endpoints["specialized"] = {
        "upload_attachment": upload_attachment,
        "download_attachment": download_attachment,
        "search_values": search_values,
        "get_or_create_value": get_or_create_value,
    }
    
    return endpoints