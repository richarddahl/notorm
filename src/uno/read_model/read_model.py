"""Read Model implementation for the Uno framework.

This module defines the base read model interface and implementations
for the CQRS pattern's query side. Read models are optimized data structures
for specific query use cases.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

# Type variables
T = TypeVar('T', bound='ReadModel')
KeyT = TypeVar('KeyT')
ValueT = TypeVar('ValueT')


class ReadModel(BaseModel):
    """
    Base class for read models.
    
    Read models are optimized data structures for specific query use cases.
    They are updated by projections based on domain events.
    """
    
    model_config = ConfigDict(frozen=True)
    
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @property
    def model_type(self) -> str:
        """Get the type of this read model."""
        return self.__class__.__name__


class ReadModelRepository(Generic[T], ABC):
    """
    Abstract base class for read model repositories.
    
    Read model repositories are responsible for storing and retrieving
    read models of a specific type.
    """
    
    def __init__(self, model_type: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    @abstractmethod
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        pass
    
    @abstractmethod
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """
        Find read models matching a query.
        
        Args:
            query: The query criteria
            
        Returns:
            List of matching read models
        """
        pass
    
    @abstractmethod
    async def save(self, model: T) -> T:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            The saved read model
        """
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            True if the read model was deleted, False otherwise
        """
        pass


class InMemoryReadModelRepository(ReadModelRepository[T]):
    """
    In-memory implementation of the read model repository.
    
    This implementation stores read models in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(self, model_type: Type[T], logger: Optional[logging.Logger] = None):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            logger: Optional logger instance
        """
        super().__init__(model_type, logger)
        self._models: Dict[str, T] = {}
    
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        return self._models.get(id)
    
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """
        Find read models matching a query.
        
        Args:
            query: The query criteria
            
        Returns:
            List of matching read models
        """
        result = []
        for model in self._models.values():
            # Simple property matching
            matches = True
            for key, value in query.items():
                if not hasattr(model, key) or getattr(model, key) != value:
                    matches = False
                    break
            
            if matches:
                result.append(model)
        
        return result
    
    async def save(self, model: T) -> T:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            The saved read model
        """
        # Set updated_at timestamp if model is mutable
        if hasattr(model, "updated_at") and not getattr(model, "model_config", {}).get("frozen", False):
            model.updated_at = datetime.utcnow()
        
        self._models[model.id] = model
        return model
    
    async def delete(self, id: str) -> bool:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            True if the read model was deleted, False otherwise
        """
        if id in self._models:
            del self._models[id]
            return True
        return False


class DatabaseReadModelRepository(ReadModelRepository[T]):
    """
    Database implementation of the read model repository.
    
    This implementation stores read models in a database, suitable for
    production applications.
    """
    
    def __init__(
        self, 
        model_type: Type[T], 
        database_provider: Any,  # Using Any since we don't know the concrete type
        table_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            database_provider: The database provider
            table_name: Optional table name, defaults to model_type.__name__.lower()
            logger: Optional logger instance
        """
        super().__init__(model_type, logger)
        self.database_provider = database_provider
        self.table_name = table_name or model_type.__name__.lower()
    
    async def get(self, id: str) -> Optional[T]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        # Implementation would depend on the database provider
        # This is a simplified example
        async with self.database_provider.get_session() as session:
            query = f"SELECT * FROM {self.table_name} WHERE id = :id"
            result = await session.execute(query, {"id": id})
            data = result.first()
            
            if data:
                return self.model_type(**data)
            return None
    
    async def find(self, query: Dict[str, Any]) -> List[T]:
        """
        Find read models matching a query.
        
        Args:
            query: The query criteria
            
        Returns:
            List of matching read models
        """
        # Implementation would depend on the database provider
        # This is a simplified example
        async with self.database_provider.get_session() as session:
            conditions = []
            params = {}
            
            for key, value in query.items():
                conditions.append(f"{key} = :{key}")
                params[key] = value
            
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query_str = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
            
            result = await session.execute(query_str, params)
            return [self.model_type(**row) for row in result.fetchall()]
    
    async def save(self, model: T) -> T:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            The saved read model
        """
        # Implementation would depend on the database provider
        # This is a simplified example
        model_dict = model.model_dump()
        
        # Set updated_at timestamp
        model_dict["updated_at"] = datetime.utcnow()
        
        async with self.database_provider.get_session() as session:
            # Check if the model exists
            query = f"SELECT id FROM {self.table_name} WHERE id = :id"
            result = await session.execute(query, {"id": model_dict["id"]})
            exists = result.first() is not None
            
            if exists:
                # Update
                set_clause = ", ".join([f"{key} = :{key}" for key in model_dict])
                query = f"UPDATE {self.table_name} SET {set_clause} WHERE id = :id"
            else:
                # Insert
                columns = ", ".join(model_dict.keys())
                placeholders = ", ".join([f":{key}" for key in model_dict])
                query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            
            await session.execute(query, model_dict)
            await session.commit()
            
            # Return the updated model
            updated_model = model.model_copy(update={"updated_at": model_dict["updated_at"]})
            return updated_model
    
    async def delete(self, id: str) -> bool:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            True if the read model was deleted, False otherwise
        """
        # Implementation would depend on the database provider
        # This is a simplified example
        async with self.database_provider.get_session() as session:
            query = f"DELETE FROM {self.table_name} WHERE id = :id"
            result = await session.execute(query, {"id": id})
            await session.commit()
            
            # In SQLAlchemy, rowcount would tell us if a row was deleted
            return result.rowcount > 0