# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain entities for the Schema module.

This module defines the core domain entities, value objects, and aggregates for the Schema module,
representing the domain model for schema management, validation, and transformation.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Set, Any, Optional, Type, List, TypeVar, Generic, cast, Union, get_origin, get_args

from pydantic import BaseModel, Field as PydanticField, create_model, model_validator

from uno.core.errors.result import Result, Success, Failure, ErrorDetails


# Value Objects

@dataclass(frozen=True)
class SchemaId:
    """Value object representing a unique schema identifier."""
    
    value: str
    
    def __post_init__(self):
        if not self.value:
            raise ValueError("SchemaId cannot be empty")
    
    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FieldDefinition:
    """Value object representing a field definition in a schema."""
    
    name: str
    annotation: Any
    description: str = ""
    required: bool = True
    default: Any = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "annotation": self.annotation,
            "description": self.description,
            "required": self.required,
            "default": self.default
        }
    
    @classmethod
    def from_pydantic_field(cls, name: str, field_info: Any) -> 'FieldDefinition':
        """Create from a Pydantic field."""
        return cls(
            name=name,
            annotation=field_info.annotation,
            description=field_info.description or "",
            required=field_info.is_required(),
            default=field_info.get_default() if not field_info.is_required() else None
        )


class SchemaType(Enum):
    """Enum representing different schema types/purposes."""
    
    ENTITY = auto()  # For domain entities
    DTO = auto()     # For data transfer objects
    DETAIL = auto()  # For detailed views
    LIST = auto()    # For list views
    CREATE = auto()  # For creation operations
    UPDATE = auto()  # For update operations
    CUSTOM = auto()  # For custom schemas


# Entities and Aggregates

@dataclass
class SchemaDefinition:
    """Entity representing a schema definition."""
    
    id: SchemaId
    name: str
    fields: Dict[str, FieldDefinition] = field(default_factory=dict)
    type: SchemaType = SchemaType.CUSTOM
    description: str = ""
    base_class: Optional[Type] = None
    
    def add_field(self, field_def: FieldDefinition) -> Result[None, ErrorDetails]:
        """
        Add a field to the schema.
        
        Args:
            field_def: The field definition to add
            
        Returns:
            Result indicating success or failure
        """
        if field_def.name in self.fields:
            return Failure(ErrorDetails(
                code="SCHEMA_FIELD_ALREADY_EXISTS",
                message=f"Field {field_def.name} already exists in schema {self.name}"
            ))
        
        self.fields[field_def.name] = field_def
        return Success(None)
    
    def remove_field(self, field_name: str) -> Result[None, ErrorDetails]:
        """
        Remove a field from the schema.
        
        Args:
            field_name: The name of the field to remove
            
        Returns:
            Result indicating success or failure
        """
        if field_name not in self.fields:
            return Failure(ErrorDetails(
                code="SCHEMA_FIELD_NOT_FOUND",
                message=f"Field {field_name} not found in schema {self.name}"
            ))
        
        del self.fields[field_name]
        return Success(None)
    
    def update_field(self, field_def: FieldDefinition) -> Result[None, ErrorDetails]:
        """
        Update a field in the schema.
        
        Args:
            field_def: The updated field definition
            
        Returns:
            Result indicating success or failure
        """
        if field_def.name not in self.fields:
            return Failure(ErrorDetails(
                code="SCHEMA_FIELD_NOT_FOUND",
                message=f"Field {field_def.name} not found in schema {self.name}"
            ))
        
        self.fields[field_def.name] = field_def
        return Success(None)
    
    def get_field(self, field_name: str) -> Result[FieldDefinition, ErrorDetails]:
        """
        Get a field by name.
        
        Args:
            field_name: The name of the field to get
            
        Returns:
            Result containing the field definition if found
        """
        if field_name not in self.fields:
            return Failure(ErrorDetails(
                code="SCHEMA_FIELD_NOT_FOUND",
                message=f"Field {field_name} not found in schema {self.name}"
            ))
        
        return Success(self.fields[field_name])
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": str(self.id),
            "name": self.name,
            "type": self.type.name,
            "description": self.description,
            "fields": {name: field.to_dict() for name, field in self.fields.items()}
        }
    
    @classmethod
    def from_pydantic_model(cls, model_cls: Type[BaseModel], schema_type: SchemaType = SchemaType.DTO) -> 'SchemaDefinition':
        """Create a schema definition from a Pydantic model."""
        schema_id = SchemaId(f"{model_cls.__name__}Schema")
        schema_def = cls(
            id=schema_id,
            name=model_cls.__name__,
            type=schema_type,
            description=model_cls.__doc__ or "",
            base_class=model_cls
        )
        
        # Add fields from the model
        for name, field_info in model_cls.model_fields.items():
            field_def = FieldDefinition.from_pydantic_field(name, field_info)
            schema_def.add_field(field_def)
        
        return schema_def


@dataclass
class SchemaConfiguration:
    """Entity representing configuration for schema creation."""
    
    schema_base: Type = BaseModel
    exclude_fields: Set[str] = field(default_factory=set)
    include_fields: Set[str] = field(default_factory=set)
    
    def validate(self) -> Result[None, ErrorDetails]:
        """
        Validate the configuration.
        
        Returns:
            Result indicating success or failure
        """
        if self.exclude_fields and self.include_fields:
            return Failure(ErrorDetails(
                code="INVALID_SCHEMA_CONFIG",
                message="Cannot specify both include_fields and exclude_fields"
            ))
        
        return Success(None)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "schema_base": self.schema_base.__name__,
            "exclude_fields": list(self.exclude_fields),
            "include_fields": list(self.include_fields)
        }


# Generic type for list schemas
T = TypeVar('T', bound=BaseModel)

@dataclass
class PaginationParams:
    """Value object representing pagination parameters."""
    
    page: int = 1
    page_size: int = 25
    
    def __post_init__(self):
        if self.page < 1:
            raise ValueError("Page must be a positive integer")
        if self.page_size < 1:
            raise ValueError("Page size must be a positive integer")
    
    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary representation."""
        return {
            "page": self.page,
            "page_size": self.page_size
        }


@dataclass
class PaginationMetadata:
    """Value object representing pagination metadata."""
    
    total: int
    page: int
    page_size: int
    
    @property
    def pages(self) -> int:
        """Calculate the total number of pages."""
        return (self.total + self.page_size - 1) // self.page_size if self.page_size > 0 else 1
    
    @property
    def has_next(self) -> bool:
        """Check if there are more pages."""
        return self.page < self.pages
    
    @property
    def has_previous(self) -> bool:
        """Check if there are previous pages."""
        return self.page > 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_previous": self.has_previous
        }


@dataclass
class PaginatedResult(Generic[T]):
    """Entity representing a paginated list of items."""
    
    items: List[T]
    metadata: PaginationMetadata
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "items": [item.model_dump() if hasattr(item, "model_dump") else item for item in self.items],
            **self.metadata.to_dict()
        }


@dataclass
class MetadataFields:
    """Value object representing common metadata fields."""
    
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    version: Optional[int] = None
    additional_metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "version": self.version
        }
        if self.additional_metadata:
            result["metadata"] = self.additional_metadata
        return result


# Domain Service Models (for API)

class SchemaCreationRequest(BaseModel):
    """Request model for creating a schema."""
    
    name: str = PydanticField(..., description="The name of the schema")
    type: str = PydanticField(..., description="The type of schema (ENTITY, DTO, etc.)")
    description: str = PydanticField("", description="Description of the schema")
    fields: Dict[str, Dict[str, Any]] = PydanticField(
        ..., description="Dictionary of field definitions"
    )
    exclude_fields: List[str] = PydanticField(
        [], description="Fields to exclude from the schema"
    )
    include_fields: List[str] = PydanticField(
        [], description="Fields to include in the schema (if specified, excludes all others)"
    )
    
    @model_validator(mode="after")
    def validate_include_exclude(self) -> "SchemaCreationRequest":
        """Validate that include_fields and exclude_fields are not both specified."""
        if self.include_fields and self.exclude_fields:
            raise ValueError("Cannot specify both include_fields and exclude_fields")
        return self


class SchemaUpdateRequest(BaseModel):
    """Request model for updating a schema."""
    
    description: Optional[str] = PydanticField(None, description="Updated description")
    fields_to_add: Dict[str, Dict[str, Any]] = PydanticField(
        {}, description="Fields to add to the schema"
    )
    fields_to_update: Dict[str, Dict[str, Any]] = PydanticField(
        {}, description="Fields to update in the schema"
    )
    fields_to_remove: List[str] = PydanticField(
        [], description="Fields to remove from the schema"
    )


class SchemaValidationRequest(BaseModel):
    """Request model for schema validation."""
    
    data: Dict[str, Any] = PydanticField(..., description="Data to validate")
    schema_id: str = PydanticField(..., description="ID of the schema to validate against")


class ApiSchemaCreationRequest(BaseModel):
    """Request model for creating a set of API schemas."""
    
    entity_name: str = PydanticField(..., description="Name of the entity")
    fields: Dict[str, Dict[str, Any]] = PydanticField(
        ..., description="Field definitions for the entity"
    )
    create_list_schema: bool = PydanticField(
        True, description="Whether to create a list schema"
    )
    create_detail_schema: bool = PydanticField(
        True, description="Whether to create a detail schema"
    )
    create_create_schema: bool = PydanticField(
        True, description="Whether to create a creation schema"
    )
    create_update_schema: bool = PydanticField(
        True, description="Whether to create an update schema"
    )