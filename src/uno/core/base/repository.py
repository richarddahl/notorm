"""
Base repository protocols and classes for the Uno framework.

DEPRECATED: This module has been deprecated and replaced by the new domain entity framework
in uno.domain.entity.repository. Please use the new implementation instead.

This module now serves as a redirection layer to the new implementation.
"""

import warnings
import importlib
from typing import Any, Dict, Generic, Iterable, List, Optional, Type, TypeVar, AsyncIterator, Protocol, runtime_checkable

# Emit a strong deprecation warning
warnings.warn(
    "IMPORTANT: The uno.core.base.repository module is deprecated and will be removed in a future release. "
    "Use uno.domain.entity.repository instead for all repository implementations.",
    DeprecationWarning,
    stacklevel=2
)

# Import from the new implementation to re-export
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.base import EntityBase
from uno.core.errors.result import Result, Success, Failure

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type

# Re-export FilterProtocol for backward compatibility
@runtime_checkable
class FilterProtocol(Protocol):
    """
    Protocol for filter objects that can be converted to dict form.
    
    DEPRECATED: Use specifications from uno.domain.entity.specification instead.
    """
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert filter to dictionary form."""
        ...


# Type alias for filter arguments
FilterType = Dict[str, Any]


# Re-export RepositoryProtocol for backward compatibility
@runtime_checkable
class RepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol defining the standard repository interface.
    
    DEPRECATED: Use uno.domain.entity.repository.EntityRepository instead.
    """
    
    async def get(self, id: ID) -> Optional[T]:
        """Get an entity by ID."""
        ...
    
    async def list(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[T]:
        """List entities matching filter criteria."""
        ...
    
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        ...
    
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        ...
    
    async def delete(self, entity: T) -> None:
        """Delete an entity."""
        ...
    
    async def exists(self, id: ID) -> bool:
        """Check if an entity with the given ID exists."""
        ...


# Re-export SpecificationRepositoryProtocol for backward compatibility
@runtime_checkable
class SpecificationRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for the Specification pattern.
    
    DEPRECATED: Use uno.domain.entity.repository.EntityRepository instead.
    """
    
    async def find(self, specification: Any) -> List[T]:
        """Find entities matching a specification."""
        ...
    
    async def find_one(self, specification: Any) -> Optional[T]:
        """Find a single entity matching a specification."""
        ...
    
    async def count(self, specification: Optional[Any] = None) -> int:
        """Count entities matching a specification."""
        ...


# Re-export BatchRepositoryProtocol for backward compatibility
@runtime_checkable
class BatchRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for batch operations.
    
    DEPRECATED: Use uno.domain.entity.repository.EntityRepository instead.
    """
    
    async def add_many(self, entities: Iterable[T]) -> List[T]:
        """Add multiple entities."""
        ...
    
    async def update_many(self, entities: Iterable[T]) -> List[T]:
        """Update multiple entities."""
        ...
    
    async def delete_many(self, entities: Iterable[T]) -> None:
        """Delete multiple entities."""
        ...
    
    async def delete_by_ids(self, ids: Iterable[ID]) -> int:
        """Delete entities by their IDs."""
        ...


# Re-export StreamingRepositoryProtocol for backward compatibility
@runtime_checkable
class StreamingRepositoryProtocol(Protocol[T, ID]):
    """
    Repository protocol for streaming large result sets.
    
    DEPRECATED: Use uno.domain.entity.repository.EntityRepository instead.
    """
    
    async def stream(
        self,
        filters: Optional[FilterType] = None,
        order_by: Optional[List[str]] = None,
        batch_size: int = 100,
    ) -> AsyncIterator[T]:
        """Stream entities matching filter criteria."""
        ...


# Redirect base classes to the new EntityRepository
class BaseRepository(EntityRepository[T, ID], Generic[T, ID]):
    """
    Abstract base repository implementation.
    
    DEPRECATED: Use uno.domain.entity.repository.EntityRepository instead.
    """
    
    def __init__(self, *args, **kwargs):
        """
        Initialize with a deprecation warning.
        """
        warnings.warn(
            "BaseRepository is deprecated. "
            "Use uno.domain.entity.repository.EntityRepository instead.",
            DeprecationWarning,
            stacklevel=2
        )
        super().__init__(*args, **kwargs)


# Backward compatibility classes
SpecificationRepository = BaseRepository
BatchRepository = BaseRepository
StreamingRepository = BaseRepository
CompleteRepository = BaseRepository