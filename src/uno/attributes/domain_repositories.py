"""
Repository implementations for the Attributes module.

This module provides repository implementations for persisting and retrieving
attribute entities from the database.
"""

from typing import List, Dict, Any, Optional, Type, TypeVar, Generic, Set, cast
import logging

from uno.domain.repository import UnoDBRepository
from uno.core.errors.result import Result, Success, Failure
from uno.attributes.entities import Attribute, AttributeType, MetaTypeRef, QueryRef
from uno.attributes.models import AttributeModel, AttributeTypeModel


# Type variables
T = TypeVar('T')


class AttributeRepositoryError(Exception):
    """Base error class for attribute repository errors."""
    pass


class AttributeTypeRepository(UnoDBRepository[AttributeType]):
    """Repository for attribute type entities."""
    
    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=AttributeType, db_factory=db_factory)
    
    async def find_by_name(self, name: str, group_id: Optional[str] = None) -> Optional[AttributeType]:
        """
        Find an attribute type by name.
        
        Args:
            name: The name to search for
            group_id: Optional group ID to filter by
            
        Returns:
            The attribute type if found, None otherwise
        """
        filters = {'name': {'lookup': 'eq', 'val': name}}
        if group_id:
            filters['group_id'] = {'lookup': 'eq', 'val': group_id}
            
        results = await self.list(filters=filters, limit=1)
        return results[0] if results else None
    
    async def find_by_parent(self, parent_id: str) -> List[AttributeType]:
        """
        Find attribute types by parent ID.
        
        Args:
            parent_id: The parent ID to search for
            
        Returns:
            List of attribute types with the given parent
        """
        filters = {'parent_id': {'lookup': 'eq', 'val': parent_id}}
        return await self.list(filters=filters)
    
    async def get_with_relationships(self, id: str) -> Optional[AttributeType]:
        """
        Get an attribute type with its related entities.
        
        Args:
            id: The ID of the attribute type
            
        Returns:
            The attribute type with loaded relationships if found, None otherwise
        """
        # First get the basic attribute type
        attr_type = await self.get(id)
        if not attr_type:
            return None
        
        # Load parent if exists
        if attr_type.parent_id:
            attr_type.parent = await self.get(attr_type.parent_id)
        
        # Load children
        attr_type.children = await self.find_by_parent(attr_type.id)
        
        # Load meta types and queries
        # In a real implementation, these would be loaded from the database
        # Here we'll just set up the basic structure
        if attr_type.description_limiting_query_id:
            attr_type.description_limiting_query = QueryRef(
                id=attr_type.description_limiting_query_id
            )
            
        if attr_type.value_type_limiting_query_id:
            attr_type.value_type_limiting_query = QueryRef(
                id=attr_type.value_type_limiting_query_id
            )
        
        # Load value types and describes relationships
        # This would require additional database queries in a real implementation
        
        return attr_type
    
    async def _convert_to_entity(self, data: Dict[str, Any]) -> AttributeType:
        """Override to handle the complex relationships."""
        entity = await super()._convert_to_entity(data)
        
        # Set up empty collections for relationships
        entity.children = []
        entity.describes = []
        entity.value_types = []
        
        return entity


class AttributeRepository(UnoDBRepository[Attribute]):
    """Repository for attribute entities."""
    
    def __init__(self, db_factory=None):
        """Initialize the repository."""
        super().__init__(entity_type=Attribute, db_factory=db_factory)
    
    async def find_by_attribute_type(self, attribute_type_id: str) -> List[Attribute]:
        """
        Find attributes by attribute type ID.
        
        Args:
            attribute_type_id: The attribute type ID to search for
            
        Returns:
            List of attributes with the given attribute type
        """
        filters = {'attribute_type_id': {'lookup': 'eq', 'val': attribute_type_id}}
        return await self.list(filters=filters)
    
    async def find_by_meta_record(self, meta_record_id: str) -> List[Attribute]:
        """
        Find attributes associated with a meta record.
        
        Args:
            meta_record_id: The meta record ID to search for
            
        Returns:
            List of attributes associated with the meta record
        """
        # This would require a join query in a real implementation
        # For now, we'll use a placeholder
        return []
    
    async def get_with_relationships(self, id: str, attribute_type_repo=None) -> Optional[Attribute]:
        """
        Get an attribute with its related entities.
        
        Args:
            id: The ID of the attribute
            attribute_type_repo: Optional repository for loading attribute types
            
        Returns:
            The attribute with loaded relationships if found, None otherwise
        """
        # First get the basic attribute
        attr = await self.get(id)
        if not attr:
            return None
        
        # Load attribute type if repository is provided
        if attribute_type_repo and attr.attribute_type_id:
            attr.attribute_type = await attribute_type_repo.get(attr.attribute_type_id)
        
        # Load values and meta records
        # This would require additional database queries in a real implementation
        
        return attr
    
    async def _convert_to_entity(self, data: Dict[str, Any]) -> Attribute:
        """Override to handle the complex relationships."""
        entity = await super()._convert_to_entity(data)
        
        # Set up empty collections for relationships
        entity.value_ids = []
        entity.meta_record_ids = []
        
        return entity