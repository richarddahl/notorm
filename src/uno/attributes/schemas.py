"""
Schema managers for the Attributes module.

This module contains schema managers that handle the conversion between domain entities
and DTOs (Data Transfer Objects) for the Attributes module. Schema managers are responsible
for selecting the appropriate schema for different operations and converting between
entity and DTO representations.
"""

from typing import Dict, Type, Any, Optional, List, cast
from pydantic import BaseModel

from uno.attributes.entities import Attribute, AttributeType, MetaTypeRef, QueryRef
from uno.attributes.dtos import (
    AttributeTypeCreateDto, AttributeTypeViewDto, AttributeTypeUpdateDto,
    AttributeCreateDto, AttributeViewDto, AttributeUpdateDto,
    AttributeTypeFilterParams, AttributeFilterParams
)


class AttributeTypeSchemaManager:
    """Schema manager for attribute type entities."""
    
    def __init__(self):
        self.schemas = {
            "view_schema": AttributeTypeViewDto,
            "edit_schema": AttributeTypeCreateDto,
            "update_schema": AttributeTypeUpdateDto,
            "filter_schema": AttributeTypeFilterParams,
        }
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema to retrieve
            
        Returns:
            The schema class if found, None otherwise
        """
        return self.schemas.get(schema_name)
    
    def entity_to_dto(self, entity: AttributeType) -> AttributeTypeViewDto:
        """
        Convert an entity to a DTO.
        
        Args:
            entity: The domain entity to convert
            
        Returns:
            A DTO representation of the entity
        """
        # Base fields
        dto_data = {
            "id": entity.id,
            "name": entity.name,
            "text": entity.text,
            "description_limiting_query_id": entity.description_limiting_query_id,
            "value_type_limiting_query_id": entity.value_type_limiting_query_id,
            "parent_id": entity.parent_id,
            "required": entity.required,
            "multiple_allowed": entity.multiple_allowed,
            "comment_required": entity.comment_required,
            "display_with_objects": entity.display_with_objects,
            "initial_comment": entity.initial_comment,
            "group_id": entity.group_id,
            "tenant_id": entity.tenant_id,
        }
        
        # Relationship fields
        if entity.parent:
            dto_data["parent"] = self.entity_to_dto(entity.parent)
            
        dto_data["children"] = [self.entity_to_dto(child) for child in entity.children]
        
        # Convert references
        dto_data["describes"] = [
            {"id": ref.id, "name": ref.name} for ref in entity.describes
        ]
        dto_data["value_types"] = [
            {"id": ref.id, "name": ref.name} for ref in entity.value_types
        ]
        
        return AttributeTypeViewDto(**dto_data)
    
    def dto_to_entity(self, dto: BaseModel) -> AttributeType:
        """
        Convert a DTO to an entity.
        
        Args:
            dto: The DTO to convert
            
        Returns:
            A domain entity created from the DTO
        """
        if isinstance(dto, AttributeTypeCreateDto):
            # Creation DTO
            return AttributeType(
                name=dto.name,
                text=dto.text,
                description_limiting_query_id=dto.description_limiting_query_id,
                value_type_limiting_query_id=dto.value_type_limiting_query_id,
                parent_id=dto.parent_id,
                required=dto.required,
                multiple_allowed=dto.multiple_allowed,
                comment_required=dto.comment_required,
                display_with_objects=dto.display_with_objects,
                initial_comment=dto.initial_comment,
                group_id=dto.group_id,
                tenant_id=dto.tenant_id,
            )
        elif isinstance(dto, AttributeTypeUpdateDto):
            # For updates, we'll need the existing entity to update fields
            # This would typically be handled in the service layer
            raise ValueError("Update DTOs should be handled by updating existing entities")
        else:
            # Generic fallback using model_dump
            data = dto.model_dump()
            
            # Handle parent conversion
            if "parent" in data:
                del data["parent"]
                
            # Handle children conversion
            if "children" in data:
                del data["children"]
                
            # Handle reference lists
            if "describes" in data:
                del data["describes"]
                
            if "value_types" in data:
                del data["value_types"]
            
            return AttributeType(**data)
    
    def create_filter_params(self) -> Type[BaseModel]:
        """
        Create filter parameters schema.
        
        Returns:
            The filter parameters schema class
        """
        return AttributeTypeFilterParams
    
    def validate_filter_params(self, params: Optional[BaseModel]) -> Dict[str, Any]:
        """
        Validate and process filter parameters.
        
        Args:
            params: The filter parameters to validate
            
        Returns:
            A dictionary of validated filter parameters
        """
        if params is None:
            return {}
            
        if not isinstance(params, AttributeTypeFilterParams):
            raise ValueError(f"Expected AttributeTypeFilterParams, got {type(params)}")
            
        filters = {}
        
        # Add non-None parameters to filters
        for field, value in params.model_dump().items():
            if value is not None:
                filters[field] = value
                
        return filters


class AttributeSchemaManager:
    """Schema manager for attribute entities."""
    
    def __init__(self):
        self.schemas = {
            "view_schema": AttributeViewDto,
            "edit_schema": AttributeCreateDto,
            "update_schema": AttributeUpdateDto,
            "filter_schema": AttributeFilterParams,
        }
        
        # Reference to the attribute type schema manager for nested conversions
        self.attribute_type_schema_manager = AttributeTypeSchemaManager()
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """
        Get a schema by name.
        
        Args:
            schema_name: Name of the schema to retrieve
            
        Returns:
            The schema class if found, None otherwise
        """
        return self.schemas.get(schema_name)
    
    def entity_to_dto(self, entity: Attribute) -> AttributeViewDto:
        """
        Convert an entity to a DTO.
        
        Args:
            entity: The domain entity to convert
            
        Returns:
            A DTO representation of the entity
        """
        # Base fields
        dto_data = {
            "id": entity.id,
            "attribute_type_id": entity.attribute_type_id,
            "comment": entity.comment,
            "follow_up_required": entity.follow_up_required,
            "group_id": entity.group_id,
            "tenant_id": entity.tenant_id,
            "value_ids": list(entity.value_ids),
            "meta_record_ids": list(entity.meta_record_ids),
        }
        
        # Add attribute type if available
        if entity.attribute_type:
            dto_data["attribute_type"] = self.attribute_type_schema_manager.entity_to_dto(entity.attribute_type)
        
        return AttributeViewDto(**dto_data)
    
    def dto_to_entity(self, dto: BaseModel) -> Attribute:
        """
        Convert a DTO to an entity.
        
        Args:
            dto: The DTO to convert
            
        Returns:
            A domain entity created from the DTO
        """
        if isinstance(dto, AttributeCreateDto):
            # Creation DTO
            return Attribute(
                attribute_type_id=dto.attribute_type_id,
                comment=dto.comment,
                follow_up_required=dto.follow_up_required,
                group_id=dto.group_id,
                tenant_id=dto.tenant_id,
            )
        elif isinstance(dto, AttributeUpdateDto):
            # For updates, we'll need the existing entity to update fields
            # This would typically be handled in the service layer
            raise ValueError("Update DTOs should be handled by updating existing entities")
        else:
            # Generic fallback using model_dump
            data = dto.model_dump()
            
            # Handle attribute_type conversion
            if "attribute_type" in data:
                del data["attribute_type"]
            
            return Attribute(**data)
    
    def create_filter_params(self) -> Type[BaseModel]:
        """
        Create filter parameters schema.
        
        Returns:
            The filter parameters schema class
        """
        return AttributeFilterParams
    
    def validate_filter_params(self, params: Optional[BaseModel]) -> Dict[str, Any]:
        """
        Validate and process filter parameters.
        
        Args:
            params: The filter parameters to validate
            
        Returns:
            A dictionary of validated filter parameters
        """
        if params is None:
            return {}
            
        if not isinstance(params, AttributeFilterParams):
            raise ValueError(f"Expected AttributeFilterParams, got {type(params)}")
            
        filters = {}
        
        # Add non-None parameters to filters
        for field, value in params.model_dump().items():
            if value is not None:
                filters[field] = value
                
        return filters