# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API endpoints for the attributes module.

This module provides FastAPI endpoints for attribute and attribute type operations,
following the project's API design pattern.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
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
from uno.attributes.services import AttributeService, AttributeTypeService, AttributeServiceError, AttributeTypeServiceError
from uno.attributes.objs import Attribute, AttributeType
from uno.meta.objs import MetaType, MetaRecord


# DTO models for attributes
class AttributeCreateDTO(BaseModel):
    """DTO for creating an attribute."""
    
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment about the attribute")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    value_ids: Optional[List[str]] = Field(None, description="IDs of values associated with this attribute")
    
    class Config:
        schema_extra = {
            "example": {
                "attribute_type_id": "01H3ZEVKXN7PQWGW5KVS77PJ0Y",
                "comment": "This is a test attribute",
                "follow_up_required": False,
                "value_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z", "01H3ZEVKY9PDSF51K5HS77PJ2A"]
            }
        }


class AttributeUpdateDTO(BaseModel):
    """DTO for updating an attribute."""
    
    comment: Optional[str] = Field(None, description="Comment about the attribute")
    follow_up_required: Optional[bool] = Field(None, description="Whether follow-up is required")
    value_ids: Optional[List[str]] = Field(None, description="IDs of values associated with this attribute")
    
    class Config:
        schema_extra = {
            "example": {
                "comment": "Updated comment",
                "follow_up_required": True,
                "value_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z"]
            }
        }


class AttributeResponseDTO(BaseModel):
    """Response DTO for attributes."""
    
    id: str = Field(..., description="Unique identifier for the attribute")
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment about the attribute")
    follow_up_required: bool = Field(..., description="Whether follow-up is required")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    values: Optional[List[dict]] = Field(None, description="Values associated with this attribute")


# DTO models for attribute types
class AttributeTypeCreateDTO(BaseModel):
    """DTO for creating an attribute type."""
    
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Text description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(False, description="Whether attributes of this type are required")
    multiple_allowed: bool = Field(False, description="Whether multiple values are allowed")
    comment_required: bool = Field(False, description="Whether a comment is required")
    display_with_objects: bool = Field(False, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment template")
    meta_type_ids: Optional[List[str]] = Field(None, description="IDs of meta types this attribute type applies to")
    value_type_ids: Optional[List[str]] = Field(None, description="IDs of meta types allowed as values")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Priority",
                "text": "What is the priority of this item?",
                "required": True,
                "multiple_allowed": False,
                "comment_required": False,
                "display_with_objects": True,
                "meta_type_ids": ["01H3ZEVKY6ZH3F41K5GS77PJ1Z"],
                "value_type_ids": ["01H3ZEVKY9PDSF51K5HS77PJ2A"]
            }
        }


class AttributeTypeUpdateDTO(BaseModel):
    """DTO for updating an attribute type."""
    
    name: Optional[str] = Field(None, description="Name of the attribute type")
    text: Optional[str] = Field(None, description="Text description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: Optional[bool] = Field(None, description="Whether attributes of this type are required")
    multiple_allowed: Optional[bool] = Field(None, description="Whether multiple values are allowed")
    comment_required: Optional[bool] = Field(None, description="Whether a comment is required")
    display_with_objects: Optional[bool] = Field(None, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment template")
    meta_type_ids: Optional[List[str]] = Field(None, description="IDs of meta types this attribute type applies to")
    value_type_ids: Optional[List[str]] = Field(None, description="IDs of meta types allowed as values")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Priority",
                "text": "What is the priority level of this item?",
                "required": True,
                "multiple_allowed": True
            }
        }


class AttributeTypeResponseDTO(BaseModel):
    """Response DTO for attribute types."""
    
    id: str = Field(..., description="Unique identifier for the attribute type")
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Text description of the attribute type")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(..., description="Whether attributes of this type are required")
    multiple_allowed: bool = Field(..., description="Whether multiple values are allowed")
    comment_required: bool = Field(..., description="Whether a comment is required")
    display_with_objects: bool = Field(..., description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment template")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    describes: Optional[List[dict]] = Field(None, description="Meta types this attribute type applies to")
    value_types: Optional[List[dict]] = Field(None, description="Meta types allowed as values")


# Attribute endpoints
def create_attribute_endpoints(
    router: APIRouter,
    attribute_service: AttributeService,
    prefix: str = "/attributes",
    tags: List[str] = ["Attributes"]
):
    """
    Create and register attribute API endpoints.
    
    Args:
        router: FastAPI router
        attribute_service: Attribute service instance
        prefix: API route prefix
        tags: API tags for documentation
    """
    
    @router.post(
        f"{prefix}",
        response_model=AttributeResponseDTO,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        summary="Create a new attribute",
        description="Create a new attribute with optional values"
    )
    async def create_attribute(
        data: AttributeCreateDTO,
        context=Depends(get_context)
    ):
        # Create attribute object
        attribute = Attribute(
            attribute_type_id=data.attribute_type_id,
            comment=data.comment,
            follow_up_required=data.follow_up_required
        )
        
        # Get values if provided
        values = None
        if data.value_ids:
            values = []
            for value_id in data.value_ids:
                # Get meta record by ID
                meta_record = await MetaRecord.get(value_id)
                if meta_record:
                    values.append(meta_record)
        
        # Create attribute
        result = await attribute_service.create_attribute(attribute, values)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        # Format response
        created_attribute = result.unwrap()
        response = AttributeResponseDTO(
            id=created_attribute.id,
            attribute_type_id=created_attribute.attribute_type_id,
            comment=created_attribute.comment,
            follow_up_required=created_attribute.follow_up_required,
            created_at=created_attribute.created_at.isoformat() if created_attribute.created_at else None,
            updated_at=created_attribute.updated_at.isoformat() if created_attribute.updated_at else None,
            values=[{
                "id": value.id,
                "name": getattr(value, "name", None),
                "meta_type_id": getattr(value, "meta_type_id", None)
            } for value in created_attribute.values] if created_attribute.values else None
        )
        
        return response
    
    @router.get(
        f"{prefix}/{{attribute_id}}",
        response_model=AttributeResponseDTO,
        tags=tags,
        summary="Get an attribute by ID",
        description="Retrieve an attribute by its unique identifier"
    )
    async def get_attribute(
        attribute_id: str,
        context=Depends(get_context)
    ):
        # Get attribute from repository
        async with attribute_service.db_manager.get_enhanced_session() as session:
            result = await attribute_service.attribute_repository.get_by_id(attribute_id, session)
            
            if result.is_err():
                error = result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            attribute = result.unwrap()
            
            if not attribute:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute with ID {attribute_id} not found"
                )
            
            # Format response
            response = AttributeResponseDTO(
                id=attribute.id,
                attribute_type_id=attribute.attribute_type_id,
                comment=attribute.comment,
                follow_up_required=attribute.follow_up_required,
                created_at=attribute.created_at.isoformat() if attribute.created_at else None,
                updated_at=attribute.updated_at.isoformat() if attribute.updated_at else None,
                values=[{
                    "id": value.id,
                    "name": getattr(value, "name", None),
                    "meta_type_id": getattr(value, "meta_type_id", None)
                } for value in attribute.values] if attribute.values else None
            )
            
            return response
    
    @router.patch(
        f"{prefix}/{{attribute_id}}",
        response_model=AttributeResponseDTO,
        tags=tags,
        summary="Update an attribute",
        description="Update an existing attribute"
    )
    async def update_attribute(
        attribute_id: str,
        data: AttributeUpdateDTO,
        context=Depends(get_context)
    ):
        # Get existing attribute
        async with attribute_service.db_manager.get_enhanced_session() as session:
            get_result = await attribute_service.attribute_repository.get_by_id(attribute_id, session)
            
            if get_result.is_err():
                error = get_result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            attribute = get_result.unwrap()
            
            if not attribute:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute with ID {attribute_id} not found"
                )
            
            # Update fields
            if data.comment is not None:
                attribute.comment = data.comment
                
            if data.follow_up_required is not None:
                attribute.follow_up_required = data.follow_up_required
            
            # Update values if provided
            values = None
            if data.value_ids is not None:
                values = []
                for value_id in data.value_ids:
                    # Get meta record by ID
                    meta_record = await MetaRecord.get(value_id)
                    if meta_record:
                        values.append(meta_record)
                
                # Set values directly
                attribute.values = values
            
            # Update attribute
            update_result = await attribute_service.attribute_repository.update(attribute, session)
            
            if update_result.is_err():
                error = update_result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            updated_attribute = update_result.unwrap()
            
            # Format response
            response = AttributeResponseDTO(
                id=updated_attribute.id,
                attribute_type_id=updated_attribute.attribute_type_id,
                comment=updated_attribute.comment,
                follow_up_required=updated_attribute.follow_up_required,
                created_at=updated_attribute.created_at.isoformat() if updated_attribute.created_at else None,
                updated_at=updated_attribute.updated_at.isoformat() if updated_attribute.updated_at else None,
                values=[{
                    "id": value.id,
                    "name": getattr(value, "name", None),
                    "meta_type_id": getattr(value, "meta_type_id", None)
                } for value in updated_attribute.values] if updated_attribute.values else None
            )
            
            return response
    
    @router.post(
        f"{prefix}/{{attribute_id}}/values",
        response_model=AttributeResponseDTO,
        tags=tags,
        summary="Add values to an attribute",
        description="Add values to an existing attribute"
    )
    async def add_attribute_values(
        attribute_id: str,
        value_ids: List[str],
        context=Depends(get_context)
    ):
        # Get values
        values = []
        for value_id in value_ids:
            # Get meta record by ID
            meta_record = await MetaRecord.get(value_id)
            if meta_record:
                values.append(meta_record)
        
        # Add values
        result = await attribute_service.add_values(attribute_id, values)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        updated_attribute = result.unwrap()
        
        # Format response
        response = AttributeResponseDTO(
            id=updated_attribute.id,
            attribute_type_id=updated_attribute.attribute_type_id,
            comment=updated_attribute.comment,
            follow_up_required=updated_attribute.follow_up_required,
            created_at=updated_attribute.created_at.isoformat() if updated_attribute.created_at else None,
            updated_at=updated_attribute.updated_at.isoformat() if updated_attribute.updated_at else None,
            values=[{
                "id": value.id,
                "name": getattr(value, "name", None),
                "meta_type_id": getattr(value, "meta_type_id", None)
            } for value in updated_attribute.values] if updated_attribute.values else None
        )
        
        return response
    
    @router.delete(
        f"{prefix}/{{attribute_id}}/values",
        response_model=AttributeResponseDTO,
        tags=tags,
        summary="Remove values from an attribute",
        description="Remove values from an existing attribute"
    )
    async def remove_attribute_values(
        attribute_id: str,
        value_ids: List[str],
        context=Depends(get_context)
    ):
        # Remove values
        result = await attribute_service.remove_values(attribute_id, value_ids)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        updated_attribute = result.unwrap()
        
        # Format response
        response = AttributeResponseDTO(
            id=updated_attribute.id,
            attribute_type_id=updated_attribute.attribute_type_id,
            comment=updated_attribute.comment,
            follow_up_required=updated_attribute.follow_up_required,
            created_at=updated_attribute.created_at.isoformat() if updated_attribute.created_at else None,
            updated_at=updated_attribute.updated_at.isoformat() if updated_attribute.updated_at else None,
            values=[{
                "id": value.id,
                "name": getattr(value, "name", None),
                "meta_type_id": getattr(value, "meta_type_id", None)
            } for value in updated_attribute.values] if updated_attribute.values else None
        )
        
        return response
    
    @router.delete(
        f"{prefix}/{{attribute_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        summary="Delete an attribute",
        description="Delete an attribute by its ID"
    )
    async def delete_attribute(
        attribute_id: str,
        context=Depends(get_context)
    ):
        # Delete attribute
        async with attribute_service.db_manager.get_enhanced_session() as session:
            result = await attribute_service.attribute_repository.delete(attribute_id, session)
            
            if result.is_err():
                error = result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            success = result.unwrap()
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute with ID {attribute_id} not found"
                )
            
            return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    @router.get(
        f"{prefix}/by-record/{{record_id}}",
        response_model=List[AttributeResponseDTO],
        tags=tags,
        summary="Get attributes for a record",
        description="Get all attributes associated with a record"
    )
    async def get_attributes_for_record(
        record_id: str,
        include_values: bool = True,
        context=Depends(get_context)
    ):
        # Get attributes
        result = await attribute_service.get_attributes_for_record(record_id, include_values)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        attributes = result.unwrap()
        
        # Format response
        response = [
            AttributeResponseDTO(
                id=attribute.id,
                attribute_type_id=attribute.attribute_type_id,
                comment=attribute.comment,
                follow_up_required=attribute.follow_up_required,
                created_at=attribute.created_at.isoformat() if attribute.created_at else None,
                updated_at=attribute.updated_at.isoformat() if attribute.updated_at else None,
                values=[{
                    "id": value.id,
                    "name": getattr(value, "name", None),
                    "meta_type_id": getattr(value, "meta_type_id", None)
                } for value in attribute.values] if attribute.values else None
            )
            for attribute in attributes
        ]
        
        return response


# Attribute type endpoints
def create_attribute_type_endpoints(
    router: APIRouter,
    attribute_type_service: AttributeTypeService,
    prefix: str = "/attribute-types",
    tags: List[str] = ["Attribute Types"]
):
    """
    Create and register attribute type API endpoints.
    
    Args:
        router: FastAPI router
        attribute_type_service: Attribute type service instance
        prefix: API route prefix
        tags: API tags for documentation
    """
    
    @router.post(
        f"{prefix}",
        response_model=AttributeTypeResponseDTO,
        status_code=status.HTTP_201_CREATED,
        tags=tags,
        summary="Create a new attribute type",
        description="Create a new attribute type with optional related meta types"
    )
    async def create_attribute_type(
        data: AttributeTypeCreateDTO,
        context=Depends(get_context)
    ):
        # Create attribute type object
        attribute_type = AttributeType(
            name=data.name,
            text=data.text,
            parent_id=data.parent_id,
            required=data.required,
            multiple_allowed=data.multiple_allowed,
            comment_required=data.comment_required,
            display_with_objects=data.display_with_objects,
            initial_comment=data.initial_comment
        )
        
        # Get meta types if provided
        applicable_meta_types = None
        if data.meta_type_ids:
            applicable_meta_types = []
            for meta_type_id in data.meta_type_ids:
                # Get meta type by ID
                meta_type = await MetaType.get(meta_type_id)
                if meta_type:
                    applicable_meta_types.append(meta_type)
        
        # Get value meta types if provided
        value_meta_types = None
        if data.value_type_ids:
            value_meta_types = []
            for meta_type_id in data.value_type_ids:
                # Get meta type by ID
                meta_type = await MetaType.get(meta_type_id)
                if meta_type:
                    value_meta_types.append(meta_type)
        
        # Create attribute type
        result = await attribute_type_service.create_attribute_type(
            attribute_type,
            applicable_meta_types,
            value_meta_types
        )
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        # Format response
        created_type = result.unwrap()
        response = AttributeTypeResponseDTO(
            id=created_type.id,
            name=created_type.name,
            text=created_type.text,
            parent_id=created_type.parent_id,
            required=created_type.required,
            multiple_allowed=created_type.multiple_allowed,
            comment_required=created_type.comment_required,
            display_with_objects=created_type.display_with_objects,
            initial_comment=created_type.initial_comment,
            created_at=created_type.created_at.isoformat() if created_type.created_at else None,
            updated_at=created_type.updated_at.isoformat() if created_type.updated_at else None,
            describes=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in created_type.describes] if created_type.describes else None,
            value_types=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in created_type.value_types] if created_type.value_types else None
        )
        
        return response
    
    @router.get(
        f"{prefix}/{{attribute_type_id}}",
        response_model=AttributeTypeResponseDTO,
        tags=tags,
        summary="Get an attribute type by ID",
        description="Retrieve an attribute type by its unique identifier"
    )
    async def get_attribute_type(
        attribute_type_id: str,
        context=Depends(get_context)
    ):
        # Get attribute type from repository
        async with attribute_type_service.db_manager.get_enhanced_session() as session:
            result = await attribute_type_service.attribute_type_repository.get_by_id(attribute_type_id, session)
            
            if result.is_err():
                error = result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            attribute_type = result.unwrap()
            
            if not attribute_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute type with ID {attribute_type_id} not found"
                )
            
            # Format response
            response = AttributeTypeResponseDTO(
                id=attribute_type.id,
                name=attribute_type.name,
                text=attribute_type.text,
                parent_id=attribute_type.parent_id,
                required=attribute_type.required,
                multiple_allowed=attribute_type.multiple_allowed,
                comment_required=attribute_type.comment_required,
                display_with_objects=attribute_type.display_with_objects,
                initial_comment=attribute_type.initial_comment,
                created_at=attribute_type.created_at.isoformat() if attribute_type.created_at else None,
                updated_at=attribute_type.updated_at.isoformat() if attribute_type.updated_at else None,
                describes=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in attribute_type.describes] if attribute_type.describes else None,
                value_types=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in attribute_type.value_types] if attribute_type.value_types else None
            )
            
            return response
    
    @router.patch(
        f"{prefix}/{{attribute_type_id}}",
        response_model=AttributeTypeResponseDTO,
        tags=tags,
        summary="Update an attribute type",
        description="Update an existing attribute type"
    )
    async def update_attribute_type(
        attribute_type_id: str,
        data: AttributeTypeUpdateDTO,
        context=Depends(get_context)
    ):
        # Get existing attribute type
        async with attribute_type_service.db_manager.get_enhanced_session() as session:
            get_result = await attribute_type_service.attribute_type_repository.get_by_id(attribute_type_id, session)
            
            if get_result.is_err():
                error = get_result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            attribute_type = get_result.unwrap()
            
            if not attribute_type:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute type with ID {attribute_type_id} not found"
                )
            
            # Update fields
            if data.name is not None:
                attribute_type.name = data.name
                
            if data.text is not None:
                attribute_type.text = data.text
                
            if data.parent_id is not None:
                attribute_type.parent_id = data.parent_id
                
            if data.required is not None:
                attribute_type.required = data.required
                
            if data.multiple_allowed is not None:
                attribute_type.multiple_allowed = data.multiple_allowed
                
            if data.comment_required is not None:
                attribute_type.comment_required = data.comment_required
                
            if data.display_with_objects is not None:
                attribute_type.display_with_objects = data.display_with_objects
                
            if data.initial_comment is not None:
                attribute_type.initial_comment = data.initial_comment
            
            # Update attribute type
            update_result = await attribute_type_service.attribute_type_repository.update(attribute_type, session)
            
            if update_result.is_err():
                error = update_result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            updated_type = update_result.unwrap()
            
            # Update meta types if provided
            if data.meta_type_ids is not None:
                meta_type_result = await attribute_type_service.update_applicable_meta_types(
                    attribute_type_id, 
                    data.meta_type_ids
                )
                
                if meta_type_result.is_err():
                    error = meta_type_result.unwrap_err()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to update applicable meta types: {str(error)}"
                    )
                
                updated_type = meta_type_result.unwrap()
            
            # Update value types if provided
            if data.value_type_ids is not None:
                value_type_result = await attribute_type_service.update_value_meta_types(
                    attribute_type_id, 
                    data.value_type_ids
                )
                
                if value_type_result.is_err():
                    error = value_type_result.unwrap_err()
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to update value meta types: {str(error)}"
                    )
                
                updated_type = value_type_result.unwrap()
            
            # Format response
            response = AttributeTypeResponseDTO(
                id=updated_type.id,
                name=updated_type.name,
                text=updated_type.text,
                parent_id=updated_type.parent_id,
                required=updated_type.required,
                multiple_allowed=updated_type.multiple_allowed,
                comment_required=updated_type.comment_required,
                display_with_objects=updated_type.display_with_objects,
                initial_comment=updated_type.initial_comment,
                created_at=updated_type.created_at.isoformat() if updated_type.created_at else None,
                updated_at=updated_type.updated_at.isoformat() if updated_type.updated_at else None,
                describes=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in updated_type.describes] if updated_type.describes else None,
                value_types=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in updated_type.value_types] if updated_type.value_types else None
            )
            
            return response
    
    @router.post(
        f"{prefix}/{{attribute_type_id}}/applicable-meta-types",
        response_model=AttributeTypeResponseDTO,
        tags=tags,
        summary="Update applicable meta types",
        description="Update the meta types this attribute type applies to"
    )
    async def update_applicable_meta_types(
        attribute_type_id: str,
        meta_type_ids: List[str],
        context=Depends(get_context)
    ):
        # Update applicable meta types
        result = await attribute_type_service.update_applicable_meta_types(attribute_type_id, meta_type_ids)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        updated_type = result.unwrap()
        
        # Format response
        response = AttributeTypeResponseDTO(
            id=updated_type.id,
            name=updated_type.name,
            text=updated_type.text,
            parent_id=updated_type.parent_id,
            required=updated_type.required,
            multiple_allowed=updated_type.multiple_allowed,
            comment_required=updated_type.comment_required,
            display_with_objects=updated_type.display_with_objects,
            initial_comment=updated_type.initial_comment,
            created_at=updated_type.created_at.isoformat() if updated_type.created_at else None,
            updated_at=updated_type.updated_at.isoformat() if updated_type.updated_at else None,
            describes=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in updated_type.describes] if updated_type.describes else None,
            value_types=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in updated_type.value_types] if updated_type.value_types else None
        )
        
        return response
    
    @router.post(
        f"{prefix}/{{attribute_type_id}}/value-meta-types",
        response_model=AttributeTypeResponseDTO,
        tags=tags,
        summary="Update value meta types",
        description="Update the meta types allowed as values for this attribute type"
    )
    async def update_value_meta_types(
        attribute_type_id: str,
        meta_type_ids: List[str],
        context=Depends(get_context)
    ):
        # Update value meta types
        result = await attribute_type_service.update_value_meta_types(attribute_type_id, meta_type_ids)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        updated_type = result.unwrap()
        
        # Format response
        response = AttributeTypeResponseDTO(
            id=updated_type.id,
            name=updated_type.name,
            text=updated_type.text,
            parent_id=updated_type.parent_id,
            required=updated_type.required,
            multiple_allowed=updated_type.multiple_allowed,
            comment_required=updated_type.comment_required,
            display_with_objects=updated_type.display_with_objects,
            initial_comment=updated_type.initial_comment,
            created_at=updated_type.created_at.isoformat() if updated_type.created_at else None,
            updated_at=updated_type.updated_at.isoformat() if updated_type.updated_at else None,
            describes=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in updated_type.describes] if updated_type.describes else None,
            value_types=[{
                "id": meta_type.id,
                "name": meta_type.name,
                "description": getattr(meta_type, "description", None)
            } for meta_type in updated_type.value_types] if updated_type.value_types else None
        )
        
        return response
    
    @router.get(
        f"{prefix}/applicable-for/{{meta_type_id}}",
        response_model=List[AttributeTypeResponseDTO],
        tags=tags,
        summary="Get applicable attribute types",
        description="Get all attribute types applicable to a meta type"
    )
    async def get_applicable_attribute_types(
        meta_type_id: str,
        context=Depends(get_context)
    ):
        # Get applicable attribute types
        result = await attribute_type_service.get_applicable_attribute_types(meta_type_id)
        
        if result.is_err():
            error = result.unwrap_err()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(error)
            )
        
        attribute_types = result.unwrap()
        
        # Format response
        response = [
            AttributeTypeResponseDTO(
                id=attribute_type.id,
                name=attribute_type.name,
                text=attribute_type.text,
                parent_id=attribute_type.parent_id,
                required=attribute_type.required,
                multiple_allowed=attribute_type.multiple_allowed,
                comment_required=attribute_type.comment_required,
                display_with_objects=attribute_type.display_with_objects,
                initial_comment=attribute_type.initial_comment,
                created_at=attribute_type.created_at.isoformat() if attribute_type.created_at else None,
                updated_at=attribute_type.updated_at.isoformat() if attribute_type.updated_at else None,
                describes=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in attribute_type.describes] if attribute_type.describes else None,
                value_types=[{
                    "id": meta_type.id,
                    "name": meta_type.name,
                    "description": getattr(meta_type, "description", None)
                } for meta_type in attribute_type.value_types] if attribute_type.value_types else None
            )
            for attribute_type in attribute_types
        ]
        
        return response
    
    @router.delete(
        f"{prefix}/{{attribute_type_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=tags,
        summary="Delete an attribute type",
        description="Delete an attribute type by its ID"
    )
    async def delete_attribute_type(
        attribute_type_id: str,
        context=Depends(get_context)
    ):
        # Delete attribute type
        async with attribute_type_service.db_manager.get_enhanced_session() as session:
            result = await attribute_type_service.attribute_type_repository.delete(attribute_type_id, session)
            
            if result.is_err():
                error = result.unwrap_err()
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(error)
                )
            
            success = result.unwrap()
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Attribute type with ID {attribute_type_id} not found"
                )
            
            return Response(status_code=status.HTTP_204_NO_CONTENT)