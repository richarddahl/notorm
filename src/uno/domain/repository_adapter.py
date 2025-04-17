"""
Repository adapters for migrating from legacy repositories to the standard pattern.

This module provides adapter classes that allow legacy repositories to be used
with the standardized repository pattern and vice versa, enabling a smooth
migration path for modules using older repository implementations.
"""

import logging
from typing import TypeVar, Generic, Dict, List, Optional, Any, Type, Union, cast

from uno.domain.repository import Repository, SQLAlchemyRepository
from uno.model import UnoModel

# Type variables
EntityT = TypeVar('EntityT')
ModelT = TypeVar('ModelT', bound=UnoModel)


class LegacyRepositoryAdapter(Repository[EntityT]):
    """
    Adapter for using legacy repositories with the standardized repository interface.
    
    This adapter wraps a legacy repository implementation and exposes it through the
    standardized Repository interface, allowing code that expects the standardized
    interface to work with legacy repositories.
    """
    
    def __init__(
        self, 
        legacy_repo: Any, 
        entity_type: Type[EntityT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the legacy repository adapter.
        
        Args:
            legacy_repo: The legacy repository to adapt
            entity_type: The entity type this repository manages
            logger: Optional logger for diagnostic output
        """
        self.legacy_repo = legacy_repo
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: Any) -> Optional[EntityT]:
        """Get an entity by ID."""
        if hasattr(self.legacy_repo, "get_by_id"):
            return await self.legacy_repo.get_by_id(id)
        elif hasattr(self.legacy_repo, "get"):
            return await self.legacy_repo.get(id)
        else:
            self.logger.error(f"Legacy repository does not support get operation")
            return None
    
    async def find(
        self, 
        specification: Any = None, 
        order_by: Optional[List[str]] = None, 
        limit: Optional[int] = None, 
        offset: Optional[int] = None
    ) -> List[EntityT]:
        """Find entities matching a specification."""
        if hasattr(self.legacy_repo, "list"):
            # Convert specification to filters dict if needed
            filters = specification
            if not isinstance(specification, dict) and hasattr(specification, "to_dict"):
                filters = specification.to_dict()
            elif not isinstance(specification, dict):
                filters = {}
                
            return await self.legacy_repo.list(filters, order_by, limit, offset)
        else:
            self.logger.error(f"Legacy repository does not support find operation")
            return []
    
    async def add(self, entity: EntityT) -> EntityT:
        """Add a new entity."""
        if hasattr(self.legacy_repo, "add"):
            return await self.legacy_repo.add(entity)
        elif hasattr(self.legacy_repo, "save"):
            return await self.legacy_repo.save(entity)
        else:
            self.logger.error(f"Legacy repository does not support add operation")
            return entity
    
    async def update(self, entity: EntityT) -> EntityT:
        """Update an existing entity."""
        if hasattr(self.legacy_repo, "update"):
            return await self.legacy_repo.update(entity)
        elif hasattr(self.legacy_repo, "save"):
            return await self.legacy_repo.save(entity)
        else:
            self.logger.error(f"Legacy repository does not support update operation")
            return entity
    
    async def remove(self, entity: EntityT) -> None:
        """Remove an entity."""
        if hasattr(self.legacy_repo, "remove"):
            await self.legacy_repo.remove(entity)
        elif hasattr(self.legacy_repo, "delete"):
            await self.legacy_repo.delete(entity)
        else:
            self.logger.error(f"Legacy repository does not support remove operation")


class StandardRepositoryAdapter:
    """
    Adapter for using standardized repositories with legacy code.
    
    This adapter wraps a standardized Repository implementation and exposes it through
    an interface compatible with legacy repository patterns, allowing legacy code to
    work with standardized repositories.
    """
    
    def __init__(
        self, 
        standard_repo: Repository[EntityT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the standard repository adapter.
        
        Args:
            standard_repo: The standardized repository to adapt
            logger: Optional logger for diagnostic output
        """
        self.standard_repo = standard_repo
        self.logger = logger or logging.getLogger(__name__)
    
    async def get_by_id(self, id: Any) -> Optional[EntityT]:
        """Get an entity by ID."""
        return await self.standard_repo.get(id)
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[EntityT]:
        """List entities with filtering and pagination."""
        return await self.standard_repo.find(filters, order_by, limit, offset)
    
    async def add(self, entity: EntityT) -> EntityT:
        """Add a new entity."""
        return await self.standard_repo.add(entity)
    
    async def save(self, entity: EntityT) -> EntityT:
        """Save an entity (create or update)."""
        if hasattr(entity, "id") and entity.id:
            return await self.standard_repo.update(entity)
        else:
            return await self.standard_repo.add(entity)
    
    async def update(self, entity: EntityT) -> EntityT:
        """Update an existing entity."""
        return await self.standard_repo.update(entity)
    
    async def remove(self, entity: EntityT) -> None:
        """Remove an entity."""
        await self.standard_repo.remove(entity)
    
    async def delete(self, entity: EntityT) -> None:
        """Delete an entity (alias for remove)."""
        await self.standard_repo.remove(entity)


# Registry of repository implementations by module
_repository_registry: Dict[str, Type[Repository]] = {}


def register_repository_implementation(module_name: str, repo_class: Type[Repository]) -> None:
    """
    Register a repository implementation for a module.
    
    This function allows modules to register their repository implementations
    for use by the central repository factory.
    
    Args:
        module_name: The name of the module (e.g., 'attributes', 'values')
        repo_class: The repository class to register
    """
    _repository_registry[module_name] = repo_class


def get_repository_implementation(module_name: str) -> Optional[Type[Repository]]:
    """
    Get the registered repository implementation for a module.
    
    Args:
        module_name: The name of the module
        
    Returns:
        The repository class if registered, None otherwise
    """
    return _repository_registry.get(module_name)


# Example registration for module repositories
# This would typically be done in each module's __init__.py
"""
from uno.domain.repository_adapter import register_repository_implementation
from my_module.repository import MyModuleRepository

register_repository_implementation('my_module', MyModuleRepository)
"""