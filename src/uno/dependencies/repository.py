"""
Base repository implementation for Uno framework.

This module provides a base repository implementation that can be
extended for specific model types. Repositories handle data access
operations and are injectable via the DI container.
"""

from typing import Dict, List, Optional, Type, TypeVar, Any, Generic
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete

from uno.model import UnoModel
from uno.dependencies.interfaces import UnoRepositoryProtocol

ModelT = TypeVar('ModelT', bound=UnoModel)


class UnoRepository(UnoRepositoryProtocol, Generic[ModelT]):
    """
    Base repository implementation for Uno models.
    
    Provides standard CRUD operations for UnoModel instances.
    """
    
    def __init__(
        self, 
        session: AsyncSession,
        model_class: Type[ModelT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            session: SQLAlchemy async session
            model_class: The model class this repository works with
            logger: Optional logger instance
        """
        self.session = session
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: str) -> Optional[ModelT]:
        """
        Get a model by ID.
        
        Args:
            id: The unique identifier of the model
            
        Returns:
            The model instance if found, None otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelT]:
        """
        List models with optional filtering and pagination.
        
        Args:
            filters: Dictionary of field name to value pairs for filtering
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of model instances
        """
        stmt = select(self.model_class)
        
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)
        
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, data: Dict[str, Any]) -> ModelT:
        """
        Create a new model instance.
        
        Args:
            data: Dictionary of field name to value pairs
            
        Returns:
            The created model instance
        """
        stmt = insert(self.model_class).values(**data).returning(self.model_class)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelT]:
        """
        Update an existing model by ID.
        
        Args:
            id: The unique identifier of the model
            data: Dictionary of field name to value pairs to update
            
        Returns:
            The updated model instance if found, None otherwise
        """
        # First check if the model exists
        model = await self.get(id)
        if not model:
            return None
        
        # Perform the update
        stmt = (
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**data)
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()
    
    async def delete(self, id: str) -> bool:
        """
        Delete a model by ID.
        
        Args:
            id: The unique identifier of the model
            
        Returns:
            True if the model was deleted, False if it wasn't found
        """
        # First check if the model exists
        model = await self.get(id)
        if not model:
            return False
        
        # Perform the delete
        stmt = delete(self.model_class).where(self.model_class.id == id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True