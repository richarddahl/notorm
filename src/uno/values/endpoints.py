# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API endpoints for the values module.

This module provides FastAPI endpoints for value operations,
following the project's API design pattern.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import date, datetime, time
from decimal import Decimal
import os

from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from uno.core.errors.result import Result
from uno.api.service_api import (
    ServiceApiRegistry,
    PaginationParams,
    get_context,
    ApiError,
    create_dto_for_entity,
    create_response_model_for_entity,
)
from uno.values.services import ValueService, ValueServiceError
from uno.values.objs import (
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)


# Base value DTO
class ValueResponseDTO(BaseModel):
    """Base response DTO for values."""
    
    id: str = Field(..., description="Unique identifier for the value")
    name: str = Field(..., description="Name of the value")
    value_type: str = Field(..., description="Type of the value")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


# Specific value DTOs
class BooleanValueDTO(ValueResponseDTO):
    """DTO for boolean values."""
    
    value: bool = Field(..., description="The boolean value")
    value_type: str = Field("boolean", description="Type of the value")


class IntegerValueDTO(ValueResponseDTO):
    """DTO for integer values."""
    
    value: int = Field(..., description="The integer value")
    value_type: str = Field("integer", description="Type of the value")


class TextValueDTO(ValueResponseDTO):
    """DTO for text values."""
    
    value: str = Field(..., description="The text value")
    value_type: str = Field("text", description="Type of the value")


class DecimalValueDTO(ValueResponseDTO):
    """DTO for decimal values."""
    
    value: float = Field(..., description="The decimal value")
    value_type: str = Field("decimal", description="Type of the value")


class DateValueDTO(ValueResponseDTO):
    """DTO for date values."""
    
    value: str = Field(..., description="The date value in ISO format (YYYY-MM-DD)")
    value_type: str = Field("date", description="Type of the value")


class DateTimeValueDTO(ValueResponseDTO):
    """DTO for datetime values."""
    
    value: str = Field(..., description="The datetime value in ISO format")
    value_type: str = Field("datetime", description="Type of the value")


class TimeValueDTO(ValueResponseDTO):
    """DTO for time values."""
    
    value: str = Field(..., description="The time value in ISO format (HH:MM:SS)")
    value_type: str = Field("time", description="Type of the value")


class AttachmentDTO(ValueResponseDTO):
    """DTO for file attachments."""
    
    file_path: str = Field(..., description="Path to the file")
    value_type: str = Field("attachment", description="Type of the value")


# Value creation DTO
class CreateValueDTO(BaseModel):
    """DTO for creating a value."""
    
    value_type: str = Field(..., description="Type of the value (boolean, integer, text, decimal, date, datetime, time)")
    value: Any = Field(..., description="The actual value")
    name: Optional[str] = Field(None, description="Optional name for the value (defaults to string representation of value)")
    
    class Config:
        schema_extra = {
            "example": {
                "value_type": "text",
                "value": "Example value",
                "name": "Example Text"
            }
        }


# Value endpoints
def create_value_endpoints(
    router: APIRouter,
    value_service: ValueService,
    prefix: str = "/values",
    tags: List[str] = ["Values"]
):
    """
    Create and register value API endpoints.
    
    Args:
        router: FastAPI router
        value_service: Value service instance
        prefix: API route prefix
        tags: API tags for documentation
    """
    
    @router.post(
        f"{prefix}",
        response_model=Union[
            BooleanValueDTO,
            IntegerValueDTO,
            TextValueDTO,
            DecimalValueDTO,
            DateValueDTO,
            DateTimeValueDTO,
            TimeValueDTO
        ],
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        summary="Create a new value",
        description="Create a new value of the specified type"
    )
    async def create_value(
        data: CreateValueDTO,
        context=Depends(get_context)
    ):
        # Determine value type class
        value_type_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue
        }
        
        value_type_class = value_type_mapping.get(data.value_type.lower())
        
        if not value_type_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {data.value_type}. Must be one of {', '.join(value_type_mapping.keys())}"
            )
        
        # Convert the value if needed
        converted_value = data.value
        
        if data.value_type.lower() == "date" and isinstance(data.value, str):
            try:
                converted_value = date.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format: {data.value}. Must be in ISO format (YYYY-MM-DD)"
                )
                
        elif data.value_type.lower() == "datetime" and isinstance(data.value, str):
            try:
                converted_value = datetime.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid datetime format: {data.value}. Must be in ISO format"
                )
                
        elif data.value_type.lower() == "time" and isinstance(data.value, str):
            try:
                converted_value = time.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid time format: {data.value}. Must be in ISO format (HH:MM:SS)"
                )
                
        elif data.value_type.lower() == "decimal" and isinstance(data.value, (int, float, str)):
            try:
                if isinstance(data.value, str):
                    converted_value = Decimal(data.value)
                else:
                    converted_value = Decimal(str(data.value))
            except (ValueError, decimal.InvalidOperation):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid decimal value: {data.value}"
                )
        
        # Create value
        result = await value_service.create_value(
            value_type_class,
            converted_value,
            data.name
        )
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        value_obj = result.value
        
        # Prepare response based on value type
        if data.value_type.lower() == "boolean":
            return BooleanValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "integer":
            return IntegerValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "text":
            return TextValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "decimal":
            return DecimalValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=float(value_obj.value),  # Convert Decimal to float for JSON serialization
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "date":
            return DateValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "datetime":
            return DateTimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "time":
            return TimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
    
    @router.post(
        f"{prefix}/get-or-create",
        response_model=Union[
            BooleanValueDTO,
            IntegerValueDTO,
            TextValueDTO,
            DecimalValueDTO,
            DateValueDTO,
            DateTimeValueDTO,
            TimeValueDTO
        ],
        tags=tags,
        summary="Get or create a value",
        description="Get a value by its actual value, or create it if it doesn't exist"
    )
    async def get_or_create_value(
        data: CreateValueDTO,
        context=Depends(get_context)
    ):
        # Determine value type class
        value_type_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue
        }
        
        value_type_class = value_type_mapping.get(data.value_type.lower())
        
        if not value_type_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {data.value_type}. Must be one of {', '.join(value_type_mapping.keys())}"
            )
        
        # Convert the value if needed
        converted_value = data.value
        
        if data.value_type.lower() == "date" and isinstance(data.value, str):
            try:
                converted_value = date.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid date format: {data.value}. Must be in ISO format (YYYY-MM-DD)"
                )
                
        elif data.value_type.lower() == "datetime" and isinstance(data.value, str):
            try:
                converted_value = datetime.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid datetime format: {data.value}. Must be in ISO format"
                )
                
        elif data.value_type.lower() == "time" and isinstance(data.value, str):
            try:
                converted_value = time.fromisoformat(data.value)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid time format: {data.value}. Must be in ISO format (HH:MM:SS)"
                )
                
        elif data.value_type.lower() == "decimal" and isinstance(data.value, (int, float, str)):
            try:
                if isinstance(data.value, str):
                    converted_value = Decimal(data.value)
                else:
                    converted_value = Decimal(str(data.value))
            except (ValueError, decimal.InvalidOperation):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid decimal value: {data.value}"
                )
        
        # Get or create value
        result = await value_service.get_or_create_value(
            value_type_class,
            converted_value,
            data.name
        )
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        value_obj = result.value
        
        # Prepare response based on value type
        if data.value_type.lower() == "boolean":
            return BooleanValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "integer":
            return IntegerValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "text":
            return TextValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "decimal":
            return DecimalValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=float(value_obj.value),  # Convert Decimal to float for JSON serialization
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "date":
            return DateValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "datetime":
            return DateTimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif data.value_type.lower() == "time":
            return TimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
    
    @router.get(
        f"{prefix}/{{value_type}}/{{value_id}}",
        response_model=Union[
            BooleanValueDTO,
            IntegerValueDTO,
            TextValueDTO,
            DecimalValueDTO,
            DateValueDTO,
            DateTimeValueDTO,
            TimeValueDTO,
            AttachmentDTO
        ],
        tags=tags,
        summary="Get a value by ID",
        description="Retrieve a value by its type and unique identifier"
    )
    async def get_value(
        value_type: str,
        value_id: str,
        context=Depends(get_context)
    ):
        # Determine value type class
        value_type_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue,
            "attachment": Attachment
        }
        
        value_type_class = value_type_mapping.get(value_type.lower())
        
        if not value_type_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {value_type}. Must be one of {', '.join(value_type_mapping.keys())}"
            )
        
        # Get value
        result = await value_service.get_value_by_id(value_type_class, value_id)
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        value_obj = result.value
        
        if not value_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{value_type.capitalize()} value with ID {value_id} not found"
            )
        
        # Prepare response based on value type
        if value_type.lower() == "boolean":
            return BooleanValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "integer":
            return IntegerValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "text":
            return TextValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "decimal":
            return DecimalValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=float(value_obj.value),  # Convert Decimal to float for JSON serialization
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "date":
            return DateValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "datetime":
            return DateTimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "time":
            return TimeValueDTO(
                id=value_obj.id,
                name=value_obj.name,
                value=value_obj.value.isoformat(),
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
        elif value_type.lower() == "attachment":
            return AttachmentDTO(
                id=value_obj.id,
                name=value_obj.name,
                file_path=value_obj.file_path,
                created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
            )
    
    @router.post(
        f"{prefix}/attachments",
        response_model=AttachmentDTO,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        summary="Upload a file attachment",
        description="Upload and create a new file attachment"
    )
    async def create_attachment(
        file: UploadFile = File(...),
        name: str = Form(...),
        context=Depends(get_context)
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
                detail=f"Failed to save file: {str(e)}"
            )
        
        # Create attachment
        result = await value_service.create_attachment(file_path, name)
        
        if result.is_failure:
            error = result.error
            # Clean up file if attachment creation fails
            if os.path.exists(file_path):
                os.remove(file_path)
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        attachment = result.value
        
        # Format response
        return AttachmentDTO(
            id=attachment.id,
            name=attachment.name,
            file_path=attachment.file_path,
            created_at=attachment.created_at.isoformat() if attachment.created_at else None,
            updated_at=attachment.updated_at.isoformat() if attachment.updated_at else None
        )
    
    @router.get(
        f"{prefix}/attachments/{{attachment_id}}/download",
        tags=tags,
        summary="Download an attachment",
        description="Download a file attachment by its ID"
    )
    async def download_attachment(
        attachment_id: str,
        context=Depends(get_context)
    ):
        # Get attachment
        result = await value_service.get_value_by_id(Attachment, attachment_id)
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        attachment = result.value
        
        if not attachment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Attachment with ID {attachment_id} not found"
            )
        
        # Check if file exists
        if not os.path.exists(attachment.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {os.path.basename(attachment.file_path)}"
            )
        
        # Return file response
        return FileResponse(
            path=attachment.file_path,
            filename=os.path.basename(attachment.file_path),
            media_type="application/octet-stream"
        )
    
    @router.delete(
        f"{prefix}/{{value_type}}/{{value_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        summary="Delete a value",
        description="Delete a value by its type and ID"
    )
    async def delete_value(
        value_type: str,
        value_id: str,
        context=Depends(get_context)
    ):
        # Determine value type class
        value_type_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue,
            "attachment": Attachment
        }
        
        value_type_class = value_type_mapping.get(value_type.lower())
        
        if not value_type_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {value_type}. Must be one of {', '.join(value_type_mapping.keys())}"
            )
        
        # Get repository
        repository = value_service._get_repository(value_type_class)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No repository found for value type {value_type}"
            )
        
        # If it's an attachment, get it first to get the file path
        file_path = None
        if value_type_class == Attachment:
            get_result = await value_service.get_value_by_id(Attachment, value_id)
            
            if get_result.is_success and get_result.value:
                attachment = get_result.value
                file_path = attachment.file_path
        
        # Delete value
        result = await repository.delete(value_id)
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        success = result.value
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{value_type.capitalize()} value with ID {value_id} not found"
            )
        
        # If it's an attachment, delete the file too
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                # Log error but don't fail the request since the value is already deleted
                print(f"Error deleting attachment file {file_path}: {str(e)}")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    @router.get(
        f"{prefix}/{{value_type}}/search",
        response_model=List[Union[
            BooleanValueDTO,
            IntegerValueDTO,
            TextValueDTO,
            DecimalValueDTO,
            DateValueDTO,
            DateTimeValueDTO,
            TimeValueDTO,
            AttachmentDTO
        ]],
        tags=tags,
        summary="Search values",
        description="Search for values of a specific type matching a term"
    )
    async def search_values(
        value_type: str,
        term: str,
        limit: int = 20,
        context=Depends(get_context)
    ):
        # Determine value type class
        value_type_mapping = {
            "boolean": BooleanValue,
            "integer": IntegerValue,
            "text": TextValue,
            "decimal": DecimalValue,
            "date": DateValue,
            "datetime": DateTimeValue,
            "time": TimeValue,
            "attachment": Attachment
        }
        
        value_type_class = value_type_mapping.get(value_type.lower())
        
        if not value_type_class:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid value type: {value_type}. Must be one of {', '.join(value_type_mapping.keys())}"
            )
        
        # Get repository
        repository = value_service._get_repository(value_type_class)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No repository found for value type {value_type}"
            )
        
        # Search values
        result = await repository.search(term, limit)
        
        if result.is_failure:
            error = result.error
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        values = result.value
        
        # Format response based on value type
        response = []
        
        for value_obj in values:
            if value_type.lower() == "boolean":
                response.append(BooleanValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value,
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "integer":
                response.append(IntegerValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value,
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "text":
                response.append(TextValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value,
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "decimal":
                response.append(DecimalValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=float(value_obj.value),  # Convert Decimal to float for JSON serialization
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "date":
                response.append(DateValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value.isoformat(),
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "datetime":
                response.append(DateTimeValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value.isoformat(),
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "time":
                response.append(TimeValueDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    value=value_obj.value.isoformat(),
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
            elif value_type.lower() == "attachment":
                response.append(AttachmentDTO(
                    id=value_obj.id,
                    name=value_obj.name,
                    file_path=value_obj.file_path,
                    created_at=value_obj.created_at.isoformat() if value_obj.created_at else None,
                    updated_at=value_obj.updated_at.isoformat() if value_obj.updated_at else None
                ))
        
        return response