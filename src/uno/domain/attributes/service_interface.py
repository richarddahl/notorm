"""
Domain service interfaces for the Attributes module.

This module defines the service interfaces for attribute-related operations,
establishing a clean contract between the domain and application layers.
"""

from typing import List, Dict, Any, Optional, Protocol, TypeVar, runtime_checkable
from uno.core.errors.result import Result

# Type variables
AttributeT = TypeVar('AttributeT')
AttributeTypeT = TypeVar('AttributeTypeT')
IDT = TypeVar('IDT')  # ID type


@runtime_checkable
class AttributeServiceProtocol(Protocol[AttributeT, AttributeTypeT, IDT]):
    """
    Protocol defining the interface for attribute services.
    
    This protocol establishes the operations that any attribute service
    must support, regardless of implementation.
    """
    
    async def get_attribute(self, attribute_id: IDT) -> Result[Optional[AttributeT]]:
        """
        Get an attribute by ID.
        
        Args:
            attribute_id: The attribute ID
            
        Returns:
            Result containing the attribute or None if not found
        """
        ...
    
    async def list_attributes(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Result[List[AttributeT]]:
        """
        List attributes with optional filtering, ordering, and pagination.
        
        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of attributes to return
            offset: Number of attributes to skip
            
        Returns:
            Result containing the list of matching attributes
        """
        ...
    
    async def create_attribute(self, data: Dict[str, Any]) -> Result[AttributeT]:
        """
        Create a new attribute.
        
        Args:
            data: Attribute data
            
        Returns:
            Result containing the created attribute
        """
        ...
    
    async def update_attribute(self, attribute_id: IDT, data: Dict[str, Any]) -> Result[AttributeT]:
        """
        Update an existing attribute.
        
        Args:
            attribute_id: The attribute ID
            data: Updated attribute data
            
        Returns:
            Result containing the updated attribute
        """
        ...
    
    async def delete_attribute(self, attribute_id: IDT) -> Result[bool]:
        """
        Delete an attribute.
        
        Args:
            attribute_id: The attribute ID
            
        Returns:
            Result indicating success or failure
        """
        ...
    
    async def get_attribute_type(self, type_id: IDT) -> Result[Optional[AttributeTypeT]]:
        """
        Get an attribute type by ID.
        
        Args:
            type_id: The attribute type ID
            
        Returns:
            Result containing the attribute type or None if not found
        """
        ...
    
    async def list_attribute_types(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> Result[List[AttributeTypeT]]:
        """
        List attribute types with optional filtering, ordering, and pagination.
        
        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of attribute types to return
            offset: Number of attribute types to skip
            
        Returns:
            Result containing the list of matching attribute types
        """
        ...
    
    async def create_attribute_type(self, data: Dict[str, Any]) -> Result[AttributeTypeT]:
        """
        Create a new attribute type.
        
        Args:
            data: Attribute type data
            
        Returns:
            Result containing the created attribute type
        """
        ...
    
    async def update_attribute_type(self, type_id: IDT, data: Dict[str, Any]) -> Result[AttributeTypeT]:
        """
        Update an existing attribute type.
        
        Args:
            type_id: The attribute type ID
            data: Updated attribute type data
            
        Returns:
            Result containing the updated attribute type
        """
        ...
    
    async def delete_attribute_type(self, type_id: IDT) -> Result[bool]:
        """
        Delete an attribute type.
        
        Args:
            type_id: The attribute type ID
            
        Returns:
            Result indicating success or failure
        """
        ...