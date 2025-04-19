"""
Filtering protocols for the unified endpoint framework.

This module defines the protocols for filtering operations in the unified endpoint framework.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Generic, List, Optional, Protocol, TypeVar, Union

from pydantic import BaseModel

T = TypeVar("T")
IdType = TypeVar("IdType")


class QueryParameter(BaseModel):
    """
    Query parameter for filtering operations.
    
    This class represents a single query parameter with a field, operator, and value.
    """
    
    field: str
    operator: str
    value: Any


class FilterProtocol(Protocol, Generic[T, IdType]):
    """
    Protocol for filtering operations.
    
    This protocol defines the interface for filtering entities in the unified endpoint framework.
    """
    
    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
        *,
        sort_by: Optional[List[str]] = None,
        sort_dir: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[List[IdType], Optional[int]]:
        """
        Filter entities based on criteria and return IDs.
        
        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities
            
        Returns:
            Tuple of (list of entity IDs, total count if include_count is True)
        """
        ...
    
    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
    ) -> int:
        """
        Count entities based on criteria.
        
        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            
        Returns:
            Total count of matching entities
        """
        ...
    
    async def get_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
        repository: Any,
        *,
        sort_by: Optional[List[str]] = None,
        sort_dir: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[List[T], Optional[int]]:
        """
        Get entities based on criteria.
        
        Args:
            entity_type: The type of entity to get
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            repository: Repository for fetching entities
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities
            
        Returns:
            Tuple of (list of entities, total count if include_count is True)
        """
        ...


class FilterBackend(ABC, Generic[T, IdType]):
    """
    Abstract base class for filter backends.
    
    This class provides a base implementation for filter backends.
    """
    
    @abstractmethod
    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
        *,
        sort_by: Optional[List[str]] = None,
        sort_dir: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[List[IdType], Optional[int]]:
        """
        Filter entities based on criteria and return IDs.
        
        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities
            
        Returns:
            Tuple of (list of entity IDs, total count if include_count is True)
        """
        pass
    
    @abstractmethod
    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
    ) -> int:
        """
        Count entities based on criteria.
        
        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            
        Returns:
            Total count of matching entities
        """
        pass
    
    async def get_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], List[QueryParameter]],
        repository: Any,
        *,
        sort_by: Optional[List[str]] = None,
        sort_dir: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[List[T], Optional[int]]:
        """
        Get entities based on criteria.
        
        Args:
            entity_type: The type of entity to get
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            repository: Repository for fetching entities
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities
            
        Returns:
            Tuple of (list of entities, total count if include_count is True)
        """
        # Get entity IDs from filter
        entity_ids, total = await self.filter_entities(
            entity_type=entity_type,
            filter_criteria=filter_criteria,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            offset=offset,
            include_count=include_count,
        )
        
        # If no entities match, return empty list
        if not entity_ids:
            return [], total if include_count else None
        
        # Get entities from repository
        entities = await repository.get_by_ids(entity_ids)
        
        # Return entities and total count
        return entities, total if include_count else None