"""
Base repository implementation for database operations.

This module provides a unified repository base that can be used
with or without UnoObj in the Uno framework.
"""

from typing import TypeVar, Generic, Type, Optional, List, Dict, Any, Tuple, Union, TYPE_CHECKING
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, text, Result, RowMapping

from uno.model import UnoModel

# Forward references for type checking to avoid circular imports
if TYPE_CHECKING:
    from uno.obj import UnoObj


ModelT = TypeVar('ModelT', bound=UnoModel)
ObjT = TypeVar('ObjT', bound='UnoObj')


class UnoBaseRepository(Generic[ModelT]):
    """
    Base repository for database operations.
    
    This class provides a foundation for repository implementations,
    with methods for common database operations.
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
            model_class: Model class this repository works with
            logger: Optional logger instance
        """
        self.session = session
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)
    
    async def get(self, id: str) -> Optional[ModelT]:
        """
        Get a model by ID.
        
        Args:
            id: The model's unique identifier
            
        Returns:
            The model if found, None otherwise
        """
        stmt = select(self.model_class).where(self.model_class.id == id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
    
    async def list(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[ModelT]:
        """
        List models with optional filtering, ordering, and pagination.
        
        Args:
            filters: Dictionary of filters to apply
            order_by: List of fields to order by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of models matching the criteria
        """
        stmt = select(self.model_class)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)
        
        # Apply ordering
        if order_by:
            for field in order_by:
                descending = field.startswith('-')
                field_name = field[1:] if descending else field
                
                if hasattr(self.model_class, field_name):
                    column = getattr(self.model_class, field_name)
                    stmt = stmt.order_by(column.desc() if descending else column)
        
        # Apply pagination
        if limit is not None:
            stmt = stmt.limit(limit)
        
        if offset is not None:
            stmt = stmt.offset(offset)
        
        # Execute and return results
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def create(self, data: Dict[str, Any]) -> ModelT:
        """
        Create a new model.
        
        Args:
            data: Dictionary of field values
            
        Returns:
            The created model
        """
        stmt = insert(self.model_class).values(**data).returning(self.model_class)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.scalars().first()
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelT]:
        """
        Update an existing model.
        
        Args:
            id: The model's unique identifier
            data: Dictionary of field values to update
            
        Returns:
            The updated model if found, None otherwise
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
        Delete a model.
        
        Args:
            id: The model's unique identifier
            
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
    
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Result:
        """
        Execute a raw SQL query.
        
        Args:
            query: The SQL query to execute
            params: Parameters for the query
            
        Returns:
            The query result
        """
        stmt = text(query)
        result = await self.session.execute(stmt, params or {})
        return result
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count models matching the given filters.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            The number of matching models
        """
        from sqlalchemy import func
        
        stmt = select(func.count()).select_from(self.model_class)
        
        # Apply filters
        if filters:
            for field, value in filters.items():
                if hasattr(self.model_class, field):
                    stmt = stmt.where(getattr(self.model_class, field) == value)
        
        # Execute and return result
        result = await self.session.execute(stmt)
        return result.scalar_one()
    
    # Integration with UnoObj
    def to_dict(self, obj: Union['UnoObj', Dict[str, Any]]) -> Dict[str, Any]:
        """
        Convert an object to a dictionary for database operations.
        
        This method supports both UnoObj instances and dictionaries.
        
        Args:
            obj: UnoObj instance or dictionary
            
        Returns:
            Dictionary of field values
        """
        if isinstance(obj, UnoObj):
            return obj.model_dump(exclude={'id'} if obj.id is None else set())
        elif isinstance(obj, dict):
            return obj
        else:
            raise TypeError(f"Expected UnoObj or dict, got {type(obj)}")
    
    async def save(self, obj: Union['UnoObj', Dict[str, Any]]) -> ModelT:
        """
        Save an object to the database.
        
        This method handles both creation and update based on whether
        the object has an ID.
        
        Args:
            obj: UnoObj instance or dictionary
            
        Returns:
            The saved model
        """
        data = self.to_dict(obj)
        
        if isinstance(obj, UnoObj) and obj.id:
            # Update existing object
            return await self.update(obj.id, data)
        elif isinstance(obj, dict) and 'id' in obj and obj['id']:
            # Update existing object from dict
            return await self.update(obj['id'], data)
        else:
            # Create new object
            return await self.create(data)