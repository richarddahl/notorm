"""
Data Transfer Objects (DTOs) for the Attributes module.

This module contains Pydantic models that represent the API contract for attribute
entities. These DTOs are used for serialization/deserialization in API requests and responses.
"""

from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any

# AttributeType DTOs

class AttributeTypeCreateDto(BaseModel):
    """DTO for creating attribute types."""
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Display text for the attribute type")
    description_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting description")
    value_type_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting value types")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(False, description="Whether this attribute is required")
    multiple_allowed: bool = Field(False, description="Whether multiple values are allowed")
    comment_required: bool = Field(False, description="Whether a comment is required")
    display_with_objects: bool = Field(False, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "color",
                "text": "Product Color",
                "required": True,
                "multiple_allowed": False,
                "comment_required": False,
                "display_with_objects": True
            }
        }
    }
    
    @model_validator(mode='after')
    def validate_comment_required(self):
        """Validate that initial comment is provided if comment is required."""
        if self.comment_required and not self.initial_comment:
            raise ValueError("Initial comment must be provided when comment is required")
        return self


class AttributeTypeViewDto(BaseModel):
    """DTO for viewing attribute types."""
    id: str = Field(..., description="Unique identifier")
    name: str = Field(..., description="Name of the attribute type")
    text: str = Field(..., description="Display text for the attribute type")
    description_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting description")
    value_type_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting value types")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: bool = Field(..., description="Whether this attribute is required")
    multiple_allowed: bool = Field(..., description="Whether multiple values are allowed")
    comment_required: bool = Field(..., description="Whether a comment is required")
    display_with_objects: bool = Field(..., description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    # Optional relationship fields
    parent: Optional["AttributeTypeViewDto"] = Field(None, description="Parent attribute type")
    children: List["AttributeTypeViewDto"] = Field(default_factory=list, description="Child attribute types")
    describes: List[Dict[str, Any]] = Field(default_factory=list, description="Meta types this attribute can describe")
    value_types: List[Dict[str, Any]] = Field(default_factory=list, description="Valid value types for this attribute")


class AttributeTypeUpdateDto(BaseModel):
    """DTO for updating attribute types."""
    name: Optional[str] = Field(None, description="Name of the attribute type")
    text: Optional[str] = Field(None, description="Display text for the attribute type")
    description_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting description")
    value_type_limiting_query_id: Optional[str] = Field(None, description="ID of the query limiting value types")
    parent_id: Optional[str] = Field(None, description="ID of the parent attribute type")
    required: Optional[bool] = Field(None, description="Whether this attribute is required")
    multiple_allowed: Optional[bool] = Field(None, description="Whether multiple values are allowed")
    comment_required: Optional[bool] = Field(None, description="Whether a comment is required")
    display_with_objects: Optional[bool] = Field(None, description="Whether to display with objects")
    initial_comment: Optional[str] = Field(None, description="Initial comment text")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "text": "Updated Product Color",
                "required": False,
                "multiple_allowed": True
            }
        }
    }
    
    @model_validator(mode='after')
    def validate_comment_required(self):
        """Validate that initial comment is provided if comment is required."""
        if self.comment_required and self.initial_comment is None:
            raise ValueError("Initial comment must be provided when comment is required")
        return self


# Attribute DTOs

class AttributeCreateDto(BaseModel):
    """DTO for creating attributes."""
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: bool = Field(False, description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "attribute_type_id": "attr_type_123",
                "comment": "This is a blue color variant",
                "follow_up_required": False
            }
        }
    }


class AttributeViewDto(BaseModel):
    """DTO for viewing attributes."""
    id: str = Field(..., description="Unique identifier")
    attribute_type_id: str = Field(..., description="ID of the attribute type")
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: bool = Field(..., description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    # Optional relationship fields
    attribute_type: Optional[AttributeTypeViewDto] = Field(None, description="The attribute type")
    value_ids: List[str] = Field(default_factory=list, description="IDs of values for this attribute")
    meta_record_ids: List[str] = Field(default_factory=list, description="IDs of meta records for this attribute")


class AttributeUpdateDto(BaseModel):
    """DTO for updating attributes."""
    comment: Optional[str] = Field(None, description="Comment for this attribute")
    follow_up_required: Optional[bool] = Field(None, description="Whether follow-up is required")
    group_id: Optional[str] = Field(None, description="ID of the group this attribute belongs to")
    tenant_id: Optional[str] = Field(None, description="ID of the tenant this attribute belongs to")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "comment": "Updated comment for blue color variant",
                "follow_up_required": True
            }
        }
    }


# Filter parameter DTOs

class AttributeTypeFilterParams(BaseModel):
    """Filter parameters for attribute types."""
    name: Optional[str] = Field(None, description="Filter by name")
    text: Optional[str] = Field(None, description="Filter by display text")
    parent_id: Optional[str] = Field(None, description="Filter by parent ID")
    required: Optional[bool] = Field(None, description="Filter by required flag")
    multiple_allowed: Optional[bool] = Field(None, description="Filter by multiple_allowed flag")
    comment_required: Optional[bool] = Field(None, description="Filter by comment_required flag")
    group_id: Optional[str] = Field(None, description="Filter by group ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")
    

class AttributeFilterParams(BaseModel):
    """Filter parameters for attributes."""
    attribute_type_id: Optional[str] = Field(None, description="Filter by attribute type ID")
    follow_up_required: Optional[bool] = Field(None, description="Filter by follow_up_required flag")
    group_id: Optional[str] = Field(None, description="Filter by group ID")
    tenant_id: Optional[str] = Field(None, description="Filter by tenant ID")


# Support recursive references for parent/child relationships
AttributeTypeViewDto.model_rebuild()