"""
Data Transfer Objects (DTOs) for the Meta module.

These DTOs are used to transfer data between the API layer and the domain layer,
providing a clear contract for the API and a clean separation of concerns following
the domain-driven design approach.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class MetaTypeBaseDto(BaseModel):
    """Base DTO for meta type data with common fields."""
    id: str = Field(..., description="Unique identifier for the meta type, used as table name")
    name: Optional[str] = Field(None, description="Human-readable name (derived from ID if not provided)")
    description: Optional[str] = Field(None, description="Optional description of the meta type")
    
    @model_validator(mode='after')
    def validate_id(self) -> 'MetaTypeBaseDto':
        """Validate that the ID meets requirements."""
        if not self.id.isalnum() and "_" not in self.id:
            raise ValueError("ID must contain only alphanumeric characters and underscores")
        return self


class MetaTypeCreateDto(MetaTypeBaseDto):
    """DTO for creating a new meta type."""
    pass


class MetaTypeUpdateDto(BaseModel):
    """DTO for updating an existing meta type."""
    name: Optional[str] = Field(None, description="Human-readable name")
    description: Optional[str] = Field(None, description="Optional description of the meta type")
    
    @model_validator(mode='after')
    def validate_fields(self) -> 'MetaTypeUpdateDto':
        """Validate that at least one field is provided for update."""
        if self.name is None and self.description is None:
            raise ValueError("At least one field must be provided for update")
        return self


class MetaTypeViewDto(MetaTypeBaseDto):
    """DTO for viewing meta type data."""
    display_name: str = Field(..., description="Human-readable display name")
    record_count: int = Field(0, description="Number of records of this type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "user_profile",
                "name": "User Profile",
                "description": "Stores user profile information",
                "display_name": "User Profile",
                "record_count": 42
            }
        }


class MetaTypeFilterParams(BaseModel):
    """Parameters for filtering meta types."""
    id: Optional[str] = Field(None, description="Filter by ID (exact match)")
    id_contains: Optional[str] = Field(None, description="Filter by ID (contains)")
    name_contains: Optional[str] = Field(None, description="Filter by name (contains)")
    description_contains: Optional[str] = Field(None, description="Filter by description (contains)")
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class MetaTypeListDto(BaseModel):
    """DTO for a list of meta types with pagination data."""
    items: List[MetaTypeViewDto] = Field(..., description="List of meta types")
    total: int = Field(..., description="Total number of meta types matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")


class MetaRecordBaseDto(BaseModel):
    """Base DTO for meta record data with common fields."""
    id: str = Field(..., description="Unique identifier for the meta record")
    meta_type_id: str = Field(..., description="ID of the meta type this record belongs to")


class MetaRecordCreateDto(MetaRecordBaseDto):
    """DTO for creating a new meta record."""
    attributes: List[str] = Field(default_factory=list, description="IDs of attributes to associate with this record")


class MetaRecordUpdateDto(BaseModel):
    """DTO for updating an existing meta record."""
    attributes: Optional[List[str]] = Field(None, description="IDs of attributes to associate with this record")


class MetaRecordViewDto(MetaRecordBaseDto):
    """DTO for viewing meta record data."""
    type_name: str = Field(..., description="Display name of the meta type")
    attributes: List[str] = Field(default_factory=list, description="IDs of attributes associated with this record")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prof_12345abcde",
                "meta_type_id": "user_profile",
                "type_name": "User Profile",
                "attributes": ["attr_12345abcde", "attr_67890fghij"]
            }
        }


class MetaRecordFilterParams(BaseModel):
    """Parameters for filtering meta records."""
    id: Optional[str] = Field(None, description="Filter by ID (exact match)")
    meta_type_id: Optional[str] = Field(None, description="Filter by meta type ID")
    has_attribute: Optional[str] = Field(None, description="Filter by having a specific attribute")
    limit: int = Field(50, description="Maximum number of results to return")
    offset: int = Field(0, description="Number of results to skip")


class MetaRecordListDto(BaseModel):
    """DTO for a list of meta records with pagination data."""
    items: List[MetaRecordViewDto] = Field(..., description="List of meta records")
    total: int = Field(..., description="Total number of meta records matching the query")
    limit: int = Field(..., description="Maximum number of results returned")
    offset: int = Field(..., description="Number of results skipped")