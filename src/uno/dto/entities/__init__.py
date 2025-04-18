# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema entity definitions for the DTO module.

This module provides the entity classes that represent schema definitions
and related objects in the DTO system.
"""

import uuid
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic
from enum import Enum
from datetime import datetime, UTC

from pydantic import BaseModel, Field

# Reexport the core entities
from uno.core.base.dto import BaseDTO

# Generic type parameter for paginated results
T = TypeVar('T')


class SchemaType(str, Enum):
    """Schema type enumeration."""
    JSON = "json"
    AVRO = "avro"
    PROTOBUF = "protobuf"
    GRAPHQL = "graphql"
    XML = "xml"
    CUSTOM = "custom"


class SchemaId(BaseModel):
    """Schema identifier."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)


class FieldDefinition(BaseModel):
    """Schema field definition."""
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
    validators: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


class SchemaDefinition(BaseModel):
    """Schema definition containing fields and metadata."""
    id: SchemaId
    type: SchemaType = SchemaType.JSON
    fields: List[FieldDefinition] = Field(..., min_items=1)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def get_field(self, field_name: str) -> Optional[FieldDefinition]:
        """
        Get a field by name.
        
        Args:
            field_name: The name of the field to get
            
        Returns:
            The field if found, None otherwise
        """
        for field in self.fields:
            if field.name == field_name:
                return field
        return None


class SchemaConfiguration(BaseModel):
    """Configuration for schema validation and transformation."""
    strict_validation: bool = True
    allow_additional_fields: bool = False
    case_sensitive: bool = True
    field_policies: Optional[Dict[str, Dict[str, Any]]] = None
    transformations: Optional[List[Dict[str, Any]]] = None


class PaginationMetadata(BaseModel):
    """Pagination metadata for paginated results."""
    page: int = Field(1, ge=1)
    page_size: int = Field(10, ge=1, le=1000)
    total: int = Field(0, ge=0)
    pages: int = Field(1, ge=1)


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated result containing items and pagination metadata."""
    items: List[T] = Field(default_factory=list)
    metadata: PaginationMetadata = Field(default_factory=PaginationMetadata)


# API request/response models
class SchemaCreationRequest(BaseModel):
    """Request for schema creation."""
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    type: SchemaType = SchemaType.JSON
    fields: List[FieldDefinition] = Field(..., min_items=1)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SchemaUpdateRequest(BaseModel):
    """Request for schema update."""
    fields: Optional[List[FieldDefinition]] = None
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SchemaValidationRequest(BaseModel):
    """Request for schema validation."""
    schema_id: Optional[SchemaId] = None
    schema_name: Optional[str] = None
    schema_version: Optional[str] = None
    data: Dict[str, Any] = Field(...)
    configuration: Optional[SchemaConfiguration] = None


class ApiSchemaCreationRequest(BaseModel):
    """API request for schema creation with simplified fields."""
    name: str = Field(..., min_length=1, max_length=255)
    version: str = Field(..., min_length=1, max_length=50)
    type: SchemaType = SchemaType.JSON
    fields: Dict[str, Dict[str, Any]] = Field(...)
    description: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_schema_creation_request(self) -> SchemaCreationRequest:
        """
        Convert to a SchemaCreationRequest.
        
        Returns:
            A SchemaCreationRequest
        """
        field_definitions = []
        for name, field_info in self.fields.items():
            field_definitions.append(
                FieldDefinition(
                    name=name,
                    **field_info
                )
            )
        
        return SchemaCreationRequest(
            name=self.name,
            version=self.version,
            type=self.type,
            fields=field_definitions,
            description=self.description,
            metadata=self.metadata
        )