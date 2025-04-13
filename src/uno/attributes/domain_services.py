"""
Domain services for the Attributes module.

This module provides domain services that implement business logic for attribute entities,
coordinating entity validation and persistence through repositories.
"""

from typing import List, Dict, Any, Optional, Set, cast
import logging

from uno.core.errors.result import Result, Success, Failure
from uno.domain.service import UnoEntityService
from uno.attributes.entities import Attribute, AttributeType, MetaTypeRef, QueryRef
from uno.attributes.domain_repositories import AttributeRepository, AttributeTypeRepository


class AttributeServiceError(Exception):
    """Base error class for attribute service errors."""
    pass


class AttributeTypeService(UnoEntityService[AttributeType]):
    """Service for attribute type entities."""
    
    def __init__(
        self, 
        repository: Optional[AttributeTypeRepository] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the attribute type service.
        
        Args:
            repository: The repository for data access
            logger: Optional logger
        """
        if repository is None:
            repository = AttributeTypeRepository()
            
        super().__init__(AttributeType, repository, logger)
    
    async def find_by_name(self, name: str, group_id: Optional[str] = None) -> Result[Optional[AttributeType]]:
        """
        Find an attribute type by name.
        
        Args:
            name: The name to search for
            group_id: Optional group ID to filter by
            
        Returns:
            Result containing the attribute type if found
        """
        try:
            repository = cast(AttributeTypeRepository, self.repository)
            result = await repository.find_by_name(name, group_id)
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding attribute type by name: {e}")
            return Failure(AttributeServiceError(f"Error finding attribute type: {str(e)}"))
    
    async def get_hierarchy(self, root_id: str) -> Result[List[AttributeType]]:
        """
        Get a hierarchy of attribute types starting from a root.
        
        Args:
            root_id: The ID of the root attribute type
            
        Returns:
            Result containing the attribute type hierarchy
        """
        try:
            # Get the root attribute type
            repository = cast(AttributeTypeRepository, self.repository)
            root = await repository.get_with_relationships(root_id)
            
            if not root:
                return Failure(AttributeServiceError(f"Attribute type {root_id} not found"))
            
            # Build the hierarchy
            hierarchy = [root]
            
            # Process children recursively
            for child in root.children:
                child_result = await self.get_hierarchy(child.id)
                if child_result.is_failure:
                    return child_result
                hierarchy.extend(child_result.value)
            
            return Success(hierarchy)
        except Exception as e:
            self.logger.error(f"Error getting attribute type hierarchy: {e}")
            return Failure(AttributeServiceError(f"Error getting attribute type hierarchy: {str(e)}"))
    
    async def add_value_type(self, attribute_type_id: str, meta_type_id: str) -> Result[AttributeType]:
        """
        Add a value type to an attribute type.
        
        Args:
            attribute_type_id: The ID of the attribute type
            meta_type_id: The ID of the meta type to add
            
        Returns:
            Result containing the updated attribute type
        """
        try:
            repository = cast(AttributeTypeRepository, self.repository)
            attr_type = await repository.get(attribute_type_id)
            
            if not attr_type:
                return Failure(AttributeServiceError(f"Attribute type {attribute_type_id} not found"))
            
            # Add the value type
            attr_type.add_value_type(meta_type_id)
            
            # Save the changes
            # In a real implementation, this would update the many-to-many relationship
            await repository.save(attr_type)
            
            return Success(attr_type)
        except Exception as e:
            self.logger.error(f"Error adding value type: {e}")
            return Failure(AttributeServiceError(f"Error adding value type: {str(e)}"))
    
    async def add_describable_type(self, attribute_type_id: str, meta_type_id: str) -> Result[AttributeType]:
        """
        Add a meta type that an attribute type can describe.
        
        Args:
            attribute_type_id: The ID of the attribute type
            meta_type_id: The ID of the meta type to add
            
        Returns:
            Result containing the updated attribute type
        """
        try:
            repository = cast(AttributeTypeRepository, self.repository)
            attr_type = await repository.get(attribute_type_id)
            
            if not attr_type:
                return Failure(AttributeServiceError(f"Attribute type {attribute_type_id} not found"))
            
            # Add the describable type
            attr_type.add_describable_type(meta_type_id)
            
            # Save the changes
            # In a real implementation, this would update the many-to-many relationship
            await repository.save(attr_type)
            
            return Success(attr_type)
        except Exception as e:
            self.logger.error(f"Error adding describable type: {e}")
            return Failure(AttributeServiceError(f"Error adding describable type: {str(e)}"))


class AttributeService(UnoEntityService[Attribute]):
    """Service for attribute entities."""
    
    def __init__(
        self, 
        repository: Optional[AttributeRepository] = None,
        attribute_type_service: Optional[AttributeTypeService] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the attribute service.
        
        Args:
            repository: The repository for data access
            attribute_type_service: Service for attribute types
            logger: Optional logger
        """
        if repository is None:
            repository = AttributeRepository()
            
        super().__init__(Attribute, repository, logger)
        
        # Store the attribute type service for loading related data
        self.attribute_type_service = attribute_type_service
    
    async def find_by_attribute_type(self, attribute_type_id: str) -> Result[List[Attribute]]:
        """
        Find attributes by attribute type.
        
        Args:
            attribute_type_id: The ID of the attribute type
            
        Returns:
            Result containing attributes with the given type
        """
        try:
            repository = cast(AttributeRepository, self.repository)
            results = await repository.find_by_attribute_type(attribute_type_id)
            return Success(results)
        except Exception as e:
            self.logger.error(f"Error finding attributes by type: {e}")
            return Failure(AttributeServiceError(f"Error finding attributes: {str(e)}"))
    
    async def get_with_related_data(self, id: str) -> Result[Attribute]:
        """
        Get an attribute with its related data (attribute type, values, etc.).
        
        Args:
            id: The ID of the attribute
            
        Returns:
            Result containing the attribute with related data
        """
        try:
            repository = cast(AttributeRepository, self.repository)
            
            # Get the attribute type repository if needed
            attribute_type_repo = None
            if self.attribute_type_service:
                attribute_type_repo = cast(AttributeTypeRepository, self.attribute_type_service.repository)
            
            # Get the attribute with relationships
            result = await repository.get_with_relationships(id, attribute_type_repo)
            
            if not result:
                return Failure(AttributeServiceError(f"Attribute {id} not found"))
                
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting attribute with related data: {e}")
            return Failure(AttributeServiceError(f"Error getting attribute: {str(e)}"))
    
    async def add_value(self, attribute_id: str, value_id: str) -> Result[Attribute]:
        """
        Add a value to an attribute.
        
        Args:
            attribute_id: The ID of the attribute
            value_id: The ID of the value to add
            
        Returns:
            Result containing the updated attribute
        """
        try:
            repository = cast(AttributeRepository, self.repository)
            attribute = await repository.get(attribute_id)
            
            if not attribute:
                return Failure(AttributeServiceError(f"Attribute {attribute_id} not found"))
            
            # If attribute type service is available, validate the value type
            if self.attribute_type_service and attribute.attribute_type_id:
                # Get the attribute type
                attr_type_result = await self.attribute_type_service.get_by_id(attribute.attribute_type_id)
                if attr_type_result.is_failure:
                    return Failure(AttributeServiceError(f"Error loading attribute type: {attr_type_result.error}"))
                
                # Set the attribute type on the attribute for validation
                attribute.attribute_type = attr_type_result.value
                
            # Add the value
            attribute.add_value(value_id)
            
            # Save the changes
            # In a real implementation, this would update the many-to-many relationship
            await repository.save(attribute)
            
            return Success(attribute)
        except Exception as e:
            self.logger.error(f"Error adding value to attribute: {e}")
            return Failure(AttributeServiceError(f"Error adding value: {str(e)}"))
    
    async def add_meta_record(self, attribute_id: str, meta_record_id: str) -> Result[Attribute]:
        """
        Add a meta record to an attribute.
        
        Args:
            attribute_id: The ID of the attribute
            meta_record_id: The ID of the meta record to add
            
        Returns:
            Result containing the updated attribute
        """
        try:
            repository = cast(AttributeRepository, self.repository)
            attribute = await repository.get(attribute_id)
            
            if not attribute:
                return Failure(AttributeServiceError(f"Attribute {attribute_id} not found"))
            
            # Add the meta record
            attribute.add_meta_record(meta_record_id)
            
            # Save the changes
            # In a real implementation, this would update the many-to-many relationship
            await repository.save(attribute)
            
            return Success(attribute)
        except Exception as e:
            self.logger.error(f"Error adding meta record to attribute: {e}")
            return Failure(AttributeServiceError(f"Error adding meta record: {str(e)}"))