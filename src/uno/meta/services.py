"""
Service implementations for meta domain.

This module provides services that implement business logic
for the meta domain, which handles entity metadata.
"""

from typing import List, Optional, Dict, Any, Union
import logging

from uno.dependencies.service import UnoService
from uno.dependencies.interfaces import UnoRepositoryProtocol
from uno.meta.models import MetaTypeModel, MetaRecordModel


class MetaTypeService(UnoService[MetaTypeModel, List[MetaTypeModel]]):
    """
    Service for MetaType management.
    
    Encapsulates business logic for metadata type operations.
    """
    
    def __init__(
        self,
        repository: UnoRepositoryProtocol[MetaTypeModel],
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the service with a repository."""
        super().__init__(repository, logger)
    
    async def execute(
        self, 
        type_id: Optional[str] = None
    ) -> List[MetaTypeModel]:
        """
        Execute a meta type query.
        
        Args:
            type_id: Optional specific type ID to retrieve
            
        Returns:
            List of meta types (or a single-item list if type_id is provided)
        """
        if type_id:
            # If specific type is requested
            if hasattr(self.repository, 'get_type_by_id'):
                result = await self.repository.get_type_by_id(type_id)
                return [result] if result else []
            else:
                result = await self.repository.get(type_id)
                return [result] if result else []
        else:
            # Return all types
            if hasattr(self.repository, 'get_all_types'):
                return await self.repository.get_all_types()
            else:
                return await self.repository.list()
    
    async def get_type(self, type_id: str) -> Optional[MetaTypeModel]:
        """
        Get a specific meta type by ID.
        
        Args:
            type_id: The type ID to look up
            
        Returns:
            The meta type if found, None otherwise
        """
        if hasattr(self.repository, 'get_type_by_id'):
            return await self.repository.get_type_by_id(type_id)
        else:
            return await self.repository.get(type_id)


class MetaRecordService(UnoService[MetaRecordModel, List[MetaRecordModel]]):
    """
    Service for MetaRecord management.
    
    Encapsulates business logic for entity metadata records.
    """
    
    def __init__(
        self,
        repository: UnoRepositoryProtocol[MetaRecordModel],
        type_service: Optional[MetaTypeService] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the service.
        
        Args:
            repository: Repository for meta records
            type_service: Optional service for meta types
            logger: Optional logger
        """
        super().__init__(repository, logger)
        self.type_service = type_service
    
    async def execute(
        self, 
        record_id: Optional[str] = None,
        type_id: Optional[str] = None,
        record_ids: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[MetaRecordModel]:
        """
        Execute a meta record query based on criteria.
        
        Args:
            record_id: Optional record ID to look up
            type_id: Optional type ID to filter by
            record_ids: Optional list of record IDs to look up
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of meta records matching the criteria
        """
        # Prioritize specific record lookup
        if record_id:
            result = await self.repository.get(record_id)
            return [result] if result else []
            
        # Then check for multiple record lookup by IDs
        if record_ids and hasattr(self.repository, 'find_by_ids'):
            return await self.repository.find_by_ids(record_ids)
            
        # Then filter by type if specified
        if type_id and hasattr(self.repository, 'find_by_type'):
            return await self.repository.find_by_type(
                type_id=type_id,
                limit=limit,
                offset=offset
            )
            
        # Default to standard list with filtering
        filters = {}
        if type_id:
            filters['meta_type_id'] = type_id
            
        return await self.repository.list(
            filters=filters,
            limit=limit,
            offset=offset
        )
    
    async def create_record(
        self, 
        record_id: str, 
        type_id: str
    ) -> Optional[MetaRecordModel]:
        """
        Create a new meta record.
        
        This method verifies that the meta type exists before creating
        the record.
        
        Args:
            record_id: The record ID
            type_id: The meta type ID
            
        Returns:
            The created meta record, or None if the type doesn't exist
        """
        # Verify that the type exists if type_service is available
        if self.type_service:
            type_model = await self.type_service.get_type(type_id)
            if not type_model:
                self.logger.warning(f"Attempted to create meta record with non-existent type: {type_id}")
                return None
        
        # Create the record
        if hasattr(self.repository, 'create_with_type'):
            return await self.repository.create_with_type(record_id, type_id)
        else:
            return await self.repository.create({
                "id": record_id,
                "meta_type_id": type_id
            })