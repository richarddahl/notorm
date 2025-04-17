"""
Repository operation results for the domain layer.

This module provides result objects for repository operations, following
the Result pattern for error handling.
"""

from typing import Generic, TypeVar, List, Optional, Any, Dict, Set
from dataclasses import dataclass, field

from uno.domain.protocols import EntityProtocol

# Type variables
T = TypeVar('T', bound=EntityProtocol)  # Entity type


class RepositoryResult(Generic[T]):
    """Base class for repository operation results."""
    
    def __init__(
        self,
        is_success: bool,
        error: Optional[Exception] = None
    ):
        """
        Initialize a repository result.
        
        Args:
            is_success: Whether the operation was successful
            error: Optional error if the operation failed
        """
        self._is_success = is_success
        self._error = error
    
    @property
    def is_success(self) -> bool:
        """
        Check if the operation was successful.
        
        Returns:
            True if successful, False otherwise
        """
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        """
        Check if the operation failed.
        
        Returns:
            True if failed, False otherwise
        """
        return not self._is_success
    
    @property
    def error(self) -> Optional[Exception]:
        """
        Get the error if the operation failed.
        
        Returns:
            The error if failed, None otherwise
        """
        return self._error
    
    @classmethod
    def success(cls) -> 'RepositoryResult[T]':
        """
        Create a successful result.
        
        Returns:
            A successful result
        """
        return cls(is_success=True)
    
    @classmethod
    def failure(cls, error: Exception) -> 'RepositoryResult[T]':
        """
        Create a failed result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed result
        """
        return cls(is_success=False, error=error)


class GetResult(RepositoryResult[T]):
    """Result of a get operation."""
    
    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a get result.
        
        Args:
            is_success: Whether the operation was successful
            entity: The entity if found, None otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entity = entity
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        return self._entity
    
    @classmethod
    def success(cls, entity: Optional[T] = None) -> 'GetResult[T]':
        """
        Create a successful get result.
        
        Args:
            entity: The entity if found, None otherwise
            
        Returns:
            A successful get result
        """
        return cls(is_success=True, entity=entity)
    
    @classmethod
    def not_found(cls) -> 'GetResult[T]':
        """
        Create a result for a get operation where the entity was not found.
        
        Returns:
            A successful get result with no entity
        """
        return cls(is_success=True, entity=None)
    
    @classmethod
    def failure(cls, error: Exception) -> 'GetResult[T]':
        """
        Create a failed get result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed get result
        """
        return cls(is_success=False, error=error)


class FindResult(RepositoryResult[T]):
    """Result of a find operation."""
    
    def __init__(
        self,
        is_success: bool,
        entities: Optional[List[T]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a find result.
        
        Args:
            is_success: Whether the operation was successful
            entities: The entities if found, empty list otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entities = entities or []
    
    @property
    def entities(self) -> List[T]:
        """
        Get the entities if the operation was successful.
        
        Returns:
            The entities if successful, empty list otherwise
        """
        return self._entities
    
    @classmethod
    def success(cls, entities: Optional[List[T]] = None) -> 'FindResult[T]':
        """
        Create a successful find result.
        
        Args:
            entities: The entities if found, empty list otherwise
            
        Returns:
            A successful find result
        """
        return cls(is_success=True, entities=entities or [])
    
    @classmethod
    def not_found(cls) -> 'FindResult[T]':
        """
        Create a result for a find operation where no entities were found.
        
        Returns:
            A successful find result with an empty list
        """
        return cls(is_success=True, entities=[])
    
    @classmethod
    def failure(cls, error: Exception) -> 'FindResult[T]':
        """
        Create a failed find result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed find result
        """
        return cls(is_success=False, error=error)


class FindOneResult(RepositoryResult[T]):
    """Result of a find_one operation."""
    
    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a find_one result.
        
        Args:
            is_success: Whether the operation was successful
            entity: The entity if found, None otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entity = entity
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        return self._entity
    
    @classmethod
    def success(cls, entity: Optional[T] = None) -> 'FindOneResult[T]':
        """
        Create a successful find_one result.
        
        Args:
            entity: The entity if found, None otherwise
            
        Returns:
            A successful find_one result
        """
        return cls(is_success=True, entity=entity)
    
    @classmethod
    def not_found(cls) -> 'FindOneResult[T]':
        """
        Create a result for a find_one operation where the entity was not found.
        
        Returns:
            A successful find_one result with no entity
        """
        return cls(is_success=True, entity=None)
    
    @classmethod
    def failure(cls, error: Exception) -> 'FindOneResult[T]':
        """
        Create a failed find_one result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed find_one result
        """
        return cls(is_success=False, error=error)


class CountResult(RepositoryResult[T]):
    """Result of a count operation."""
    
    def __init__(
        self,
        is_success: bool,
        count: int = 0,
        error: Optional[Exception] = None
    ):
        """
        Initialize a count result.
        
        Args:
            is_success: Whether the operation was successful
            count: The count if successful, 0 otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._count = count
    
    @property
    def count(self) -> int:
        """
        Get the count if the operation was successful.
        
        Returns:
            The count if successful, 0 otherwise
        """
        return self._count
    
    @classmethod
    def success(cls, count: int = 0) -> 'CountResult[T]':
        """
        Create a successful count result.
        
        Args:
            count: The count
            
        Returns:
            A successful count result
        """
        return cls(is_success=True, count=count)
    
    @classmethod
    def failure(cls, error: Exception) -> 'CountResult[T]':
        """
        Create a failed count result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed count result
        """
        return cls(is_success=False, error=error)


class ExistsResult(RepositoryResult[T]):
    """Result of an exists operation."""
    
    def __init__(
        self,
        is_success: bool,
        exists: bool = False,
        error: Optional[Exception] = None
    ):
        """
        Initialize an exists result.
        
        Args:
            is_success: Whether the operation was successful
            exists: Whether the entity exists
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._exists = exists
    
    @property
    def exists(self) -> bool:
        """
        Check if the entity exists if the operation was successful.
        
        Returns:
            True if exists and successful, False otherwise
        """
        return self._exists
    
    @classmethod
    def success(cls, exists: bool = False) -> 'ExistsResult[T]':
        """
        Create a successful exists result.
        
        Args:
            exists: Whether the entity exists
            
        Returns:
            A successful exists result
        """
        return cls(is_success=True, exists=exists)
    
    @classmethod
    def failure(cls, error: Exception) -> 'ExistsResult[T]':
        """
        Create a failed exists result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed exists result
        """
        return cls(is_success=False, error=error)


class AddResult(RepositoryResult[T]):
    """Result of an add operation."""
    
    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize an add result.
        
        Args:
            is_success: Whether the operation was successful
            entity: The added entity if successful, None otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entity = entity
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the added entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        return self._entity
    
    @classmethod
    def success(cls, entity: T) -> 'AddResult[T]':
        """
        Create a successful add result.
        
        Args:
            entity: The added entity
            
        Returns:
            A successful add result
        """
        return cls(is_success=True, entity=entity)
    
    @classmethod
    def failure(cls, error: Exception) -> 'AddResult[T]':
        """
        Create a failed add result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed add result
        """
        return cls(is_success=False, error=error)


class UpdateResult(RepositoryResult[T]):
    """Result of an update operation."""
    
    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize an update result.
        
        Args:
            is_success: Whether the operation was successful
            entity: The updated entity if successful, None otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entity = entity
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the updated entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        return self._entity
    
    @classmethod
    def success(cls, entity: T) -> 'UpdateResult[T]':
        """
        Create a successful update result.
        
        Args:
            entity: The updated entity
            
        Returns:
            A successful update result
        """
        return cls(is_success=True, entity=entity)
    
    @classmethod
    def failure(cls, error: Exception) -> 'UpdateResult[T]':
        """
        Create a failed update result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed update result
        """
        return cls(is_success=False, error=error)


class RemoveResult(RepositoryResult[T]):
    """Result of a remove operation."""
    
    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a remove result.
        
        Args:
            is_success: Whether the operation was successful
            entity: The removed entity if successful, None otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entity = entity
    
    @property
    def entity(self) -> Optional[T]:
        """
        Get the removed entity if the operation was successful.
        
        Returns:
            The entity if successful, None otherwise
        """
        return self._entity
    
    @classmethod
    def success(cls, entity: T) -> 'RemoveResult[T]':
        """
        Create a successful remove result.
        
        Args:
            entity: The removed entity
            
        Returns:
            A successful remove result
        """
        return cls(is_success=True, entity=entity)
    
    @classmethod
    def failure(cls, error: Exception) -> 'RemoveResult[T]':
        """
        Create a failed remove result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed remove result
        """
        return cls(is_success=False, error=error)


class BatchGetResult(RepositoryResult[T]):
    """Result of a batch get operation."""
    
    def __init__(
        self,
        is_success: bool,
        entities: Optional[Dict[Any, T]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a batch get result.
        
        Args:
            is_success: Whether the operation was successful
            entities: Dictionary mapping IDs to entities if successful, empty dict otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entities = entities or {}
    
    @property
    def entities(self) -> Dict[Any, T]:
        """
        Get the entities if the operation was successful.
        
        Returns:
            Dictionary mapping IDs to entities if successful, empty dict otherwise
        """
        return self._entities
    
    @classmethod
    def success(cls, entities: Optional[Dict[Any, T]] = None) -> 'BatchGetResult[T]':
        """
        Create a successful batch get result.
        
        Args:
            entities: Dictionary mapping IDs to entities
            
        Returns:
            A successful batch get result
        """
        return cls(is_success=True, entities=entities or {})
    
    @classmethod
    def failure(cls, error: Exception) -> 'BatchGetResult[T]':
        """
        Create a failed batch get result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed batch get result
        """
        return cls(is_success=False, error=error)


class BatchAddResult(RepositoryResult[T]):
    """Result of a batch add operation."""
    
    def __init__(
        self,
        is_success: bool,
        entities: Optional[List[T]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a batch add result.
        
        Args:
            is_success: Whether the operation was successful
            entities: The added entities if successful, empty list otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entities = entities or []
    
    @property
    def entities(self) -> List[T]:
        """
        Get the added entities if the operation was successful.
        
        Returns:
            The entities if successful, empty list otherwise
        """
        return self._entities
    
    @classmethod
    def success(cls, entities: Optional[List[T]] = None) -> 'BatchAddResult[T]':
        """
        Create a successful batch add result.
        
        Args:
            entities: The added entities
            
        Returns:
            A successful batch add result
        """
        return cls(is_success=True, entities=entities or [])
    
    @classmethod
    def failure(cls, error: Exception) -> 'BatchAddResult[T]':
        """
        Create a failed batch add result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed batch add result
        """
        return cls(is_success=False, error=error)


class BatchUpdateResult(RepositoryResult[T]):
    """Result of a batch update operation."""
    
    def __init__(
        self,
        is_success: bool,
        entities: Optional[List[T]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a batch update result.
        
        Args:
            is_success: Whether the operation was successful
            entities: The updated entities if successful, empty list otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entities = entities or []
    
    @property
    def entities(self) -> List[T]:
        """
        Get the updated entities if the operation was successful.
        
        Returns:
            The entities if successful, empty list otherwise
        """
        return self._entities
    
    @classmethod
    def success(cls, entities: Optional[List[T]] = None) -> 'BatchUpdateResult[T]':
        """
        Create a successful batch update result.
        
        Args:
            entities: The updated entities
            
        Returns:
            A successful batch update result
        """
        return cls(is_success=True, entities=entities or [])
    
    @classmethod
    def failure(cls, error: Exception) -> 'BatchUpdateResult[T]':
        """
        Create a failed batch update result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed batch update result
        """
        return cls(is_success=False, error=error)


class BatchRemoveResult(RepositoryResult[T]):
    """Result of a batch remove operation."""
    
    def __init__(
        self,
        is_success: bool,
        entities: Optional[List[T]] = None,
        error: Optional[Exception] = None
    ):
        """
        Initialize a batch remove result.
        
        Args:
            is_success: Whether the operation was successful
            entities: The removed entities if successful, empty list otherwise
            error: Optional error if the operation failed
        """
        super().__init__(is_success, error)
        self._entities = entities or []
    
    @property
    def entities(self) -> List[T]:
        """
        Get the removed entities if the operation was successful.
        
        Returns:
            The entities if successful, empty list otherwise
        """
        return self._entities
    
    @classmethod
    def success(cls, entities: Optional[List[T]] = None) -> 'BatchRemoveResult[T]':
        """
        Create a successful batch remove result.
        
        Args:
            entities: The removed entities
            
        Returns:
            A successful batch remove result
        """
        return cls(is_success=True, entities=entities or [])
    
    @classmethod
    def failure(cls, error: Exception) -> 'BatchRemoveResult[T]':
        """
        Create a failed batch remove result.
        
        Args:
            error: The error that caused the failure
            
        Returns:
            A failed batch remove result
        """
        return cls(is_success=False, error=error)