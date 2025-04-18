"""
Domain repository adapter implementations.

This module provides adapter classes that help integrate different repository
implementations with domain entities.
"""

import logging
from typing import TypeVar, Generic, Dict, List, Optional, Any, Type, Union, cast

from uno.core.base.repository import BaseRepository, RepositoryProtocol
from uno.domain.base.model import BaseModel

# Type variables
EntityT = TypeVar('EntityT')  # Domain entity type
ModelT = TypeVar('ModelT', bound=BaseModel)  # Database model type
IDT = TypeVar('IDT')  # ID type


class RepositoryAdapter(BaseRepository[EntityT, IDT], Generic[EntityT, ModelT, IDT]):
    """
    Adapter that bridges domain entities with infrastructure repositories.
    
    This adapter allows domain entities to be used with infrastructure repositories
    that work with database models, handling the translation between the two.
    """
    
    def __init__(
        self, 
        entity_type: Type[EntityT],
        model_type: Type[ModelT],
        infrastructure_repo: RepositoryProtocol[ModelT, IDT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository adapter.
        
        Args:
            entity_type: The domain entity type this repository works with
            model_type: The database model type
            infrastructure_repo: The underlying infrastructure repository
            logger: Optional logger for diagnostic output
        """
        super().__init__(entity_type, logger)
        self.model_type = model_type
        self.infrastructure_repo = infrastructure_repo
    
    async def get(self, id: IDT) -> Optional[EntityT]:
        """Get an entity by ID."""
        model = await self.infrastructure_repo.get(id)
        if model is None:
            return None
        return self._to_entity(model)
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[EntityT]:
        """List entities matching filter criteria."""
        models = await self.infrastructure_repo.list(
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
        return [self._to_entity(model) for model in models]
    
    async def add(self, entity: EntityT) -> EntityT:
        """Add a new entity."""
        model = self._to_model(entity)
        saved_model = await self.infrastructure_repo.add(model)
        return self._to_entity(saved_model)
    
    async def update(self, entity: EntityT) -> EntityT:
        """Update an existing entity."""
        model = self._to_model(entity)
        updated_model = await self.infrastructure_repo.update(model)
        return self._to_entity(updated_model)
    
    async def delete(self, entity: EntityT) -> None:
        """Delete an entity."""
        model = self._to_model(entity)
        await self.infrastructure_repo.delete(model)
    
    async def exists(self, id: IDT) -> bool:
        """Check if an entity with the given ID exists."""
        return await self.infrastructure_repo.exists(id)
    
    def _to_entity(self, model: ModelT) -> EntityT:
        """
        Convert a database model to a domain entity.
        
        Override this method in derived classes to customize the conversion.
        
        Args:
            model: The database model
            
        Returns:
            The domain entity
        """
        # Basic implementation that assumes entity accepts model attributes as kwargs
        data = {}
        if hasattr(model, "__table__"):
            # SQLAlchemy model
            data = {
                c.name: getattr(model, c.name)
                for c in model.__table__.columns
                if not c.name.startswith("_")
            }
        elif hasattr(model, "__dict__"):
            # Object with __dict__
            data = {
                k: v
                for k, v in model.__dict__.items()
                if not k.startswith("_") and k != "_sa_instance_state"
            }
        else:
            # Try to convert to dict as a last resort
            try:
                data = dict(model)
            except (TypeError, ValueError):
                pass
        
        return self.entity_type(**data)
    
    def _to_model(self, entity: EntityT) -> ModelT:
        """
        Convert a domain entity to a database model.
        
        Override this method in derived classes to customize the conversion.
        
        Args:
            entity: The domain entity
            
        Returns:
            The database model
        """
        # Basic implementation that assumes model accepts entity attributes as kwargs
        data = {}
        if hasattr(entity, "model_dump"):
            # Pydantic v2
            data = entity.model_dump()
        elif hasattr(entity, "to_dict"):
            # Custom to_dict method
            data = entity.to_dict()
        elif hasattr(entity, "__dict__"):
            # Object with __dict__
            data = {
                k: v
                for k, v in entity.__dict__.items()
                if not k.startswith("_")
            }
        else:
            # Try to convert to dict as a last resort
            try:
                data = dict(entity)
            except (TypeError, ValueError):
                pass
        
        return self.model_type(**data)