"""
Repository Protocol Definitions

This module defines the repository pattern protocols used throughout the system.
Repositories provide a collection-like interface for accessing domain entities.
"""

from typing import Protocol, Generic, TypeVar, List, Optional, Any, Dict, runtime_checkable
from uuid import UUID

# Type variables for entity types and ID types
T = TypeVar('T')  # Entity type
ID = TypeVar('ID')  # ID type (typically str, UUID, or int)


@runtime_checkable
class RepositoryProtocol(Protocol[T, ID]):
    """
    Protocol defining the repository pattern interface.
    
    Repositories are responsible for storing and retrieving domain entities.
    They abstract the underlying data source and provide a collection-like
    interface for working with domain objects.
    
    Type parameters:
        T: The entity type this repository manages
        ID: The type of the entity's identifier
    """
    
    async def get_by_id(self, id: ID) -> Optional[T]:
        """
        Retrieve an entity by its unique identifier.
        
        Args:
            id: The unique identifier of the entity
            
        Returns:
            The entity if found, None otherwise
        """
        ...
    
    async def find_all(self) -> List[T]:
        """
        Retrieve all entities of this type.
        
        Returns:
            A list of all entities
        """
        ...
    
    async def save(self, entity: T) -> T:
        """
        Save an entity (create or update).
        
        Args:
            entity: The entity to save
            
        Returns:
            The saved entity with any modifications (e.g., generated ID)
        """
        ...
    
    async def delete(self, entity: T) -> None:
        """
        Delete an entity.
        
        Args:
            entity: The entity to delete
        """
        ...
    
    async def delete_by_id(self, id: ID) -> None:
        """
        Delete an entity by its unique identifier.
        
        Args:
            id: The unique identifier of the entity to delete
        """
        ...


@runtime_checkable
class QueryableRepositoryProtocol(RepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Extended repository protocol with querying capabilities.
    
    This protocol adds methods for more complex querying beyond simple
    CRUD operations.
    
    Type parameters:
        T: The entity type this repository manages
        ID: The type of the entity's identifier
    """
    
    async def find_by(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find entities matching the given criteria.
        
        Args:
            criteria: A dictionary of field-value pairs to match
            
        Returns:
            A list of entities matching the criteria
        """
        ...
    
    async def find_one_by(self, criteria: Dict[str, Any]) -> Optional[T]:
        """
        Find a single entity matching the given criteria.
        
        Args:
            criteria: A dictionary of field-value pairs to match
            
        Returns:
            The matching entity if found, None otherwise
        """
        ...
    
    async def count(self, criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Count entities matching the given criteria.
        
        Args:
            criteria: Optional dictionary of field-value pairs to match
            
        Returns:
            The number of matching entities
        """
        ...
    
    async def exists(self, id: ID) -> bool:
        """
        Check if an entity with the given ID exists.
        
        Args:
            id: The unique identifier to check
            
        Returns:
            True if an entity with the given ID exists, False otherwise
        """
        ...


@runtime_checkable
class PageableRepositoryProtocol(QueryableRepositoryProtocol[T, ID], Protocol[T, ID]):
    """
    Repository protocol with pagination support.
    
    This protocol adds methods for paginated queries, which is essential
    for dealing with large data sets.
    
    Type parameters:
        T: The entity type this repository manages
        ID: The type of the entity's identifier
    """
    
    async def find_all_paged(
        self,
        page: int = 0,
        size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Retrieve a page of entities.
        
        Args:
            page: The page number (0-based)
            size: The page size
            sort_by: Optional field to sort by
            sort_order: Sort direction ("asc" or "desc")
            
        Returns:
            A dictionary containing the items, total count, and page info
        """
        ...
    
    async def find_by_paged(
        self,
        criteria: Dict[str, Any],
        page: int = 0,
        size: int = 20,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """
        Retrieve a page of entities matching the given criteria.
        
        Args:
            criteria: A dictionary of field-value pairs to match
            page: The page number (0-based)
            size: The page size
            sort_by: Optional field to sort by
            sort_order: Sort direction ("asc" or "desc")
            
        Returns:
            A dictionary containing the items, total count, and page info
        """
        ...