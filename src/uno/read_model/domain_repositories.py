"""
Domain repositories for the Read Model module.

This module defines the repository interfaces and implementations for the Read Model module,
providing data access capabilities for read model domain entities.
"""

import logging
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Generic, Type, TypeVar, Protocol, cast
from datetime import datetime, timedelta, UTC

from uno.core.result import Result, Success, Failure
from uno.core.errors import ErrorCode, ErrorDetails
from uno.domain.core import Entity

from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, Query, QueryId,
    CacheEntry, ProjectorConfiguration, CacheLevel
)

# Type variables
T = TypeVar('T', bound=ReadModel)
P = TypeVar('P', bound=Projection)
Q = TypeVar('Q', bound=Query)

# Repository Protocols

class ReadModelRepositoryProtocol(Protocol[T]):
    """Protocol defining operations for read model repositories."""
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        ...
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        ...
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        ...
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        ...


class ProjectionRepositoryProtocol(Protocol[P]):
    """Protocol defining operations for projection repositories."""
    
    async def get_by_id(self, id: ProjectionId) -> Result[Optional[P]]:
        """
        Get a projection by ID.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing the projection if found, None otherwise
        """
        ...
    
    async def get_by_event_type(self, event_type: str) -> Result[List[P]]:
        """
        Get projections by event type.
        
        Args:
            event_type: The event type
            
        Returns:
            Result containing list of projections for the event type
        """
        ...
    
    async def get_by_read_model_type(self, read_model_type: str) -> Result[List[P]]:
        """
        Get projections by read model type.
        
        Args:
            read_model_type: The read model type
            
        Returns:
            Result containing list of projections for the read model type
        """
        ...
    
    async def save(self, projection: P) -> Result[P]:
        """
        Save a projection.
        
        Args:
            projection: The projection to save
            
        Returns:
            Result containing the saved projection
        """
        ...
    
    async def delete(self, id: ProjectionId) -> Result[bool]:
        """
        Delete a projection.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing True if the projection was deleted, False otherwise
        """
        ...


class QueryRepositoryProtocol(Protocol[Q]):
    """Protocol defining operations for query repositories."""
    
    async def get_by_id(self, id: QueryId) -> Result[Optional[Q]]:
        """
        Get a query by ID.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing the query if found, None otherwise
        """
        ...
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[Q]]:
        """
        Find queries matching criteria.
        
        Args:
            criteria: The search criteria
            
        Returns:
            Result containing list of matching queries
        """
        ...
    
    async def save(self, query: Q) -> Result[Q]:
        """
        Save a query.
        
        Args:
            query: The query to save
            
        Returns:
            Result containing the saved query
        """
        ...
    
    async def delete(self, id: QueryId) -> Result[bool]:
        """
        Delete a query.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing True if the query was deleted, False otherwise
        """
        ...


class CacheRepositoryProtocol(Protocol):
    """Protocol defining operations for cache repositories."""
    
    async def get(self, key: str, model_type: str) -> Result[Optional[CacheEntry]]:
        """
        Get a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing the cache entry if found, None otherwise
        """
        ...
    
    async def set(self, entry: CacheEntry) -> Result[CacheEntry]:
        """
        Set a cache entry.
        
        Args:
            entry: The cache entry to set
            
        Returns:
            Result containing the saved cache entry
        """
        ...
    
    async def delete(self, key: str, model_type: str) -> Result[bool]:
        """
        Delete a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing True if the cache entry was deleted, False otherwise
        """
        ...
    
    async def clear(self, model_type: Optional[str] = None) -> Result[bool]:
        """
        Clear cache entries.
        
        Args:
            model_type: Optional model type to clear entries for. If None, clears all entries.
            
        Returns:
            Result containing True if the operation was successful
        """
        ...


class ProjectorConfigurationRepositoryProtocol(Protocol):
    """Protocol defining operations for projector configuration repositories."""
    
    async def get_by_id(self, id: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by ID.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by name.
        
        Args:
            name: The configuration name
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        ...
    
    async def save(self, config: ProjectorConfiguration) -> Result[ProjectorConfiguration]:
        """
        Save a projector configuration.
        
        Args:
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        ...
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete a projector configuration.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing True if the configuration was deleted, False otherwise
        """
        ...

# Repository Implementations

class InMemoryReadModelRepository(Generic[T], ReadModelRepositoryProtocol[T]):
    """
    In-memory implementation of the read model repository.
    
    This implementation stores read models in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(
        self,
        model_type: Type[T],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._models: Dict[str, T] = {}
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        try:
            model = self._models.get(id.value)
            return Success(model)
        except Exception as e:
            self.logger.error(f"Error getting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        try:
            result = []
            for model in self._models.values():
                # Simple property matching
                matches = True
                for key, value in criteria.items():
                    if not hasattr(model, key) or getattr(model, key) != value:
                        matches = False
                        break
                
                if matches:
                    result.append(model)
            
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding read models: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find read models: {str(e)}",
                    context={"criteria": criteria}
                )
            )
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        try:
            self._models[model.id.value] = model
            return Success(model)
        except Exception as e:
            self.logger.error(f"Error saving read model {model.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save read model: {str(e)}",
                    context={"id": model.id.value}
                )
            )
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        try:
            if id.value in self._models:
                del self._models[id.value]
                return Success(True)
            return Success(False)
        except Exception as e:
            self.logger.error(f"Error deleting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete read model: {str(e)}",
                    context={"id": id.value}
                )
            )


class InMemoryProjectionRepository(Generic[P], ProjectionRepositoryProtocol[P]):
    """
    In-memory implementation of the projection repository.
    
    This implementation stores projections in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(
        self,
        model_type: Type[P],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of projection this repository manages
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._projections: Dict[str, P] = {}
    
    async def get_by_id(self, id: ProjectionId) -> Result[Optional[P]]:
        """
        Get a projection by ID.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing the projection if found, None otherwise
        """
        try:
            projection = self._projections.get(id.value)
            return Success(projection)
        except Exception as e:
            self.logger.error(f"Error getting projection {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projection: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def get_by_event_type(self, event_type: str) -> Result[List[P]]:
        """
        Get projections by event type.
        
        Args:
            event_type: The event type
            
        Returns:
            Result containing list of projections for the event type
        """
        try:
            result = [
                p for p in self._projections.values()
                if p.event_type == event_type
            ]
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting projections for event type {event_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projections by event type: {str(e)}",
                    context={"event_type": event_type}
                )
            )
    
    async def get_by_read_model_type(self, read_model_type: str) -> Result[List[P]]:
        """
        Get projections by read model type.
        
        Args:
            read_model_type: The read model type
            
        Returns:
            Result containing list of projections for the read model type
        """
        try:
            result = [
                p for p in self._projections.values()
                if p.read_model_type == read_model_type
            ]
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error getting projections for read model type {read_model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projections by read model type: {str(e)}",
                    context={"read_model_type": read_model_type}
                )
            )
    
    async def save(self, projection: P) -> Result[P]:
        """
        Save a projection.
        
        Args:
            projection: The projection to save
            
        Returns:
            Result containing the saved projection
        """
        try:
            self._projections[projection.id.value] = projection
            return Success(projection)
        except Exception as e:
            self.logger.error(f"Error saving projection {projection.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save projection: {str(e)}",
                    context={"id": projection.id.value}
                )
            )
    
    async def delete(self, id: ProjectionId) -> Result[bool]:
        """
        Delete a projection.
        
        Args:
            id: The projection ID
            
        Returns:
            Result containing True if the projection was deleted, False otherwise
        """
        try:
            if id.value in self._projections:
                del self._projections[id.value]
                return Success(True)
            return Success(False)
        except Exception as e:
            self.logger.error(f"Error deleting projection {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete projection: {str(e)}",
                    context={"id": id.value}
                )
            )


class InMemoryQueryRepository(Generic[Q], QueryRepositoryProtocol[Q]):
    """
    In-memory implementation of the query repository.
    
    This implementation stores queries in memory, which is useful for
    testing and simple applications.
    """
    
    def __init__(
        self,
        model_type: Type[Q],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of query this repository manages
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._queries: Dict[str, Q] = {}
    
    async def get_by_id(self, id: QueryId) -> Result[Optional[Q]]:
        """
        Get a query by ID.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing the query if found, None otherwise
        """
        try:
            query = self._queries.get(id.value)
            return Success(query)
        except Exception as e:
            self.logger.error(f"Error getting query {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get query: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[Q]]:
        """
        Find queries matching criteria.
        
        Args:
            criteria: The search criteria
            
        Returns:
            Result containing list of matching queries
        """
        try:
            result = []
            for query in self._queries.values():
                # Simple property matching
                matches = True
                for key, value in criteria.items():
                    if not hasattr(query, key) or getattr(query, key) != value:
                        matches = False
                        break
                
                if matches:
                    result.append(query)
            
            return Success(result)
        except Exception as e:
            self.logger.error(f"Error finding queries: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find queries: {str(e)}",
                    context={"criteria": criteria}
                )
            )
    
    async def save(self, query: Q) -> Result[Q]:
        """
        Save a query.
        
        Args:
            query: The query to save
            
        Returns:
            Result containing the saved query
        """
        try:
            self._queries[query.id.value] = query
            return Success(query)
        except Exception as e:
            self.logger.error(f"Error saving query {query.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save query: {str(e)}",
                    context={"id": query.id.value}
                )
            )
    
    async def delete(self, id: QueryId) -> Result[bool]:
        """
        Delete a query.
        
        Args:
            id: The query ID
            
        Returns:
            Result containing True if the query was deleted, False otherwise
        """
        try:
            if id.value in self._queries:
                del self._queries[id.value]
                return Success(True)
            return Success(False)
        except Exception as e:
            self.logger.error(f"Error deleting query {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete query: {str(e)}",
                    context={"id": id.value}
                )
            )


class InMemoryCacheRepository(CacheRepositoryProtocol):
    """
    In-memory implementation of the cache repository.
    
    This implementation provides memory-based caching for read models.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the repository.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._entries: Dict[str, CacheEntry] = {}
    
    def _get_key(self, key: str, model_type: str) -> str:
        """
        Get the combined cache key.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            The combined key
        """
        return f"{model_type}:{key}"
    
    async def get(self, key: str, model_type: str) -> Result[Optional[CacheEntry]]:
        """
        Get a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing the cache entry if found, None otherwise
        """
        try:
            combined_key = self._get_key(key, model_type)
            entry = self._entries.get(combined_key)
            
            if entry and entry.is_expired():
                # Remove expired entry
                del self._entries[combined_key]
                return Success(None)
            
            return Success(entry)
        except Exception as e:
            self.logger.error(f"Error getting cache entry {key}, {model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get cache entry: {str(e)}",
                    context={"key": key, "model_type": model_type}
                )
            )
    
    async def set(self, entry: CacheEntry) -> Result[CacheEntry]:
        """
        Set a cache entry.
        
        Args:
            entry: The cache entry to set
            
        Returns:
            Result containing the saved cache entry
        """
        try:
            combined_key = self._get_key(entry.key, entry.read_model_type)
            self._entries[combined_key] = entry
            return Success(entry)
        except Exception as e:
            self.logger.error(f"Error setting cache entry {entry.key}, {entry.read_model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to set cache entry: {str(e)}",
                    context={"key": entry.key, "model_type": entry.read_model_type}
                )
            )
    
    async def delete(self, key: str, model_type: str) -> Result[bool]:
        """
        Delete a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing True if the cache entry was deleted, False otherwise
        """
        try:
            combined_key = self._get_key(key, model_type)
            if combined_key in self._entries:
                del self._entries[combined_key]
                return Success(True)
            return Success(False)
        except Exception as e:
            self.logger.error(f"Error deleting cache entry {key}, {model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete cache entry: {str(e)}",
                    context={"key": key, "model_type": model_type}
                )
            )
    
    async def clear(self, model_type: Optional[str] = None) -> Result[bool]:
        """
        Clear cache entries.
        
        Args:
            model_type: Optional model type to clear entries for. If None, clears all entries.
            
        Returns:
            Result containing True if the operation was successful
        """
        try:
            if model_type:
                # Clear entries for a specific model type
                prefix = f"{model_type}:"
                keys_to_delete = [
                    key for key in self._entries.keys()
                    if key.startswith(prefix)
                ]
                for key in keys_to_delete:
                    del self._entries[key]
            else:
                # Clear all entries
                self._entries.clear()
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error clearing cache entries: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to clear cache entries: {str(e)}",
                    context={"model_type": model_type}
                )
            )


class InMemoryProjectorConfigurationRepository(ProjectorConfigurationRepositoryProtocol):
    """
    In-memory implementation of the projector configuration repository.
    
    This implementation stores projector configurations in memory.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the repository.
        
        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._configs: Dict[str, ProjectorConfiguration] = {}
        self._config_by_name: Dict[str, ProjectorConfiguration] = {}
    
    async def get_by_id(self, id: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by ID.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        try:
            config = self._configs.get(id)
            return Success(config)
        except Exception as e:
            self.logger.error(f"Error getting projector configuration {id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projector configuration: {str(e)}",
                    context={"id": id}
                )
            )
    
    async def get_by_name(self, name: str) -> Result[Optional[ProjectorConfiguration]]:
        """
        Get a projector configuration by name.
        
        Args:
            name: The configuration name
            
        Returns:
            Result containing the configuration if found, None otherwise
        """
        try:
            config = self._config_by_name.get(name)
            return Success(config)
        except Exception as e:
            self.logger.error(f"Error getting projector configuration by name {name}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get projector configuration by name: {str(e)}",
                    context={"name": name}
                )
            )
    
    async def save(self, config: ProjectorConfiguration) -> Result[ProjectorConfiguration]:
        """
        Save a projector configuration.
        
        Args:
            config: The configuration to save
            
        Returns:
            Result containing the saved configuration
        """
        try:
            self._configs[config.id] = config
            self._config_by_name[config.name] = config
            return Success(config)
        except Exception as e:
            self.logger.error(f"Error saving projector configuration {config.id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save projector configuration: {str(e)}",
                    context={"id": config.id, "name": config.name}
                )
            )
    
    async def delete(self, id: str) -> Result[bool]:
        """
        Delete a projector configuration.
        
        Args:
            id: The configuration ID
            
        Returns:
            Result containing True if the configuration was deleted, False otherwise
        """
        try:
            if id in self._configs:
                config = self._configs[id]
                del self._configs[id]
                
                # Also remove from name index
                if config.name in self._config_by_name:
                    del self._config_by_name[config.name]
                
                return Success(True)
            return Success(False)
        except Exception as e:
            self.logger.error(f"Error deleting projector configuration {id}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete projector configuration: {str(e)}",
                    context={"id": id}
                )
            )


# Database-backed repository implementations

class DatabaseReadModelRepository(Generic[T], ReadModelRepositoryProtocol[T]):
    """
    Database implementation of the read model repository.
    
    This implementation stores read models in a database, suitable for
    production applications.
    """
    
    def __init__(
        self, 
        model_type: Type[T],
        db_provider: Any,  # Using Any since we don't know the concrete type
        table_name: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            model_type: The type of read model this repository manages
            db_provider: The database provider
            table_name: Optional table name, defaults to model_type.__name__.lower()
            logger: Optional logger instance
        """
        self.model_type = model_type
        self.db_provider = db_provider
        self.table_name = table_name or model_type.__name__.lower()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: ReadModelId) -> Result[Optional[T]]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing the read model if found, None otherwise
        """
        try:
            async with self.db_provider.get_session() as session:
                query = f"SELECT * FROM {self.table_name} WHERE id = :id"
                result = await session.execute(query, {"id": id.value})
                data = result.first()
                
                if data:
                    # Convert column dict to entity
                    model_data = dict(data)
                    model_data["id"] = ReadModelId(value=model_data["id"])
                    return Success(self.model_type(**model_data))
                return Success(None)
        except Exception as e:
            self.logger.error(f"Error getting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    async def find(self, criteria: Dict[str, Any]) -> Result[List[T]]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            Result containing list of matching read models
        """
        try:
            async with self.db_provider.get_session() as session:
                # Build WHERE clause from criteria
                conditions = []
                params = {}
                
                for key, value in criteria.items():
                    conditions.append(f"{key} = :{key}")
                    params[key] = value
                
                where_clause = " AND ".join(conditions) if conditions else "1=1"
                query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
                
                result = await session.execute(query, params)
                models = []
                
                for row in result.fetchall():
                    # Convert column dict to entity
                    model_data = dict(row)
                    model_data["id"] = ReadModelId(value=model_data["id"])
                    model = self.model_type(**model_data)
                    models.append(model)
                
                return Success(models)
        except Exception as e:
            self.logger.error(f"Error finding read models: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to find read models: {str(e)}",
                    context={"criteria": criteria}
                )
            )
    
    async def save(self, model: T) -> Result[T]:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            Result containing the saved read model
        """
        try:
            # Convert model to dict, handling domain objects
            model_dict = self._entity_to_dict(model)
            
            async with self.db_provider.get_session() as session:
                # Check if the model exists
                query = f"SELECT id FROM {self.table_name} WHERE id = :id"
                result = await session.execute(query, {"id": model_dict["id"]})
                exists = result.first() is not None
                
                model_dict["updated_at"] = datetime.now(UTC)
                
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
                return Success(model)
        except Exception as e:
            self.logger.error(f"Error saving read model {model.id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to save read model: {str(e)}",
                    context={"id": model.id.value}
                )
            )
    
    async def delete(self, id: ReadModelId) -> Result[bool]:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            Result containing True if the read model was deleted, False otherwise
        """
        try:
            async with self.db_provider.get_session() as session:
                query = f"DELETE FROM {self.table_name} WHERE id = :id"
                result = await session.execute(query, {"id": id.value})
                await session.commit()
                
                return Success(result.rowcount > 0)
        except Exception as e:
            self.logger.error(f"Error deleting read model {id.value}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete read model: {str(e)}",
                    context={"id": id.value}
                )
            )
    
    def _entity_to_dict(self, entity: Entity) -> Dict[str, Any]:
        """
        Convert an entity to a dictionary for database storage.
        
        Args:
            entity: The entity to convert
            
        Returns:
            Dictionary representation of the entity
        """
        # Basic conversion
        result = {}
        
        for key, value in entity.__dict__.items():
            if isinstance(value, ValueObject):
                # Handle value objects like IDs
                result[key] = value.value
            elif isinstance(value, Entity):
                # Handle nested entities (simplified, might need more complex handling)
                result[key] = str(value.id)
            elif isinstance(value, (datetime, dict, list, str, int, float, bool)) or value is None:
                # Handle primitive types directly
                result[key] = value
            else:
                # For other types, convert to string
                result[key] = str(value)
        
        return result


class RedisCacheRepository(CacheRepositoryProtocol):
    """
    Redis implementation of the cache repository.
    
    This implementation uses Redis for caching, which is suitable for
    distributed applications.
    """
    
    def __init__(
        self,
        redis_client: Any,  # Using Any since we don't know the concrete type
        prefix: str = "read_model_cache:",
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the repository.
        
        Args:
            redis_client: The Redis client
            prefix: Prefix for Redis keys
            logger: Optional logger instance
        """
        self.redis_client = redis_client
        self.prefix = prefix
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _get_key(self, key: str, model_type: str) -> str:
        """
        Get the Redis key for a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            The Redis key
        """
        return f"{self.prefix}{model_type}:{key}"
    
    async def get(self, key: str, model_type: str) -> Result[Optional[CacheEntry]]:
        """
        Get a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing the cache entry if found, None otherwise
        """
        try:
            redis_key = self._get_key(key, model_type)
            data = await self.redis_client.get(redis_key)
            
            if data:
                try:
                    # Deserialize JSON and create cache entry
                    cache_data = json.loads(data)
                    
                    # Convert dates from strings
                    if "created_at" in cache_data:
                        cache_data["created_at"] = datetime.fromisoformat(cache_data["created_at"])
                    if "expires_at" in cache_data and cache_data["expires_at"]:
                        cache_data["expires_at"] = datetime.fromisoformat(cache_data["expires_at"])
                    
                    if "read_model_id" in cache_data:
                        cache_data["read_model_id"] = ReadModelId(value=cache_data["read_model_id"])
                    
                    entry = CacheEntry(**cache_data)
                    
                    # Check if expired
                    if entry.is_expired():
                        await self.delete(key, model_type)
                        return Success(None)
                    
                    return Success(entry)
                except Exception as e:
                    self.logger.error(f"Error deserializing cache entry: {str(e)}")
                    return Success(None)
            
            return Success(None)
        except Exception as e:
            self.logger.error(f"Error getting cache entry {key}, {model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to get cache entry: {str(e)}",
                    context={"key": key, "model_type": model_type}
                )
            )
    
    async def set(self, entry: CacheEntry) -> Result[CacheEntry]:
        """
        Set a cache entry.
        
        Args:
            entry: The cache entry to set
            
        Returns:
            Result containing the saved cache entry
        """
        try:
            redis_key = self._get_key(entry.key, entry.read_model_type)
            
            # Convert entry to dict for serialization
            entry_dict = self._entity_to_dict(entry)
            
            # Serialize to JSON
            data = json.dumps(entry_dict)
            
            # Set TTL if expires_at is provided
            if entry.expires_at:
                ttl = (entry.expires_at - datetime.now(UTC)).total_seconds()
                if ttl > 0:
                    await self.redis_client.setex(redis_key, int(ttl), data)
                else:
                    # Already expired
                    return Success(entry)
            else:
                await self.redis_client.set(redis_key, data)
            
            return Success(entry)
        except Exception as e:
            self.logger.error(f"Error setting cache entry {entry.key}, {entry.read_model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to set cache entry: {str(e)}",
                    context={"key": entry.key, "read_model_type": entry.read_model_type}
                )
            )
    
    async def delete(self, key: str, model_type: str) -> Result[bool]:
        """
        Delete a cache entry.
        
        Args:
            key: The cache key
            model_type: The model type
            
        Returns:
            Result containing True if the cache entry was deleted, False otherwise
        """
        try:
            redis_key = self._get_key(key, model_type)
            result = await self.redis_client.delete(redis_key)
            return Success(result > 0)
        except Exception as e:
            self.logger.error(f"Error deleting cache entry {key}, {model_type}: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to delete cache entry: {str(e)}",
                    context={"key": key, "model_type": model_type}
                )
            )
    
    async def clear(self, model_type: Optional[str] = None) -> Result[bool]:
        """
        Clear cache entries.
        
        Args:
            model_type: Optional model type to clear entries for. If None, clears all entries.
            
        Returns:
            Result containing True if the operation was successful
        """
        try:
            pattern = (
                f"{self.prefix}{model_type}:*" if model_type 
                else f"{self.prefix}*"
            )
            
            # Scan for keys matching the pattern
            cursor = "0"
            total_deleted = 0
            
            while cursor:
                cursor, keys = await self.redis_client.scan(cursor, match=pattern, count=100)
                
                if keys:
                    result = await self.redis_client.delete(*keys)
                    total_deleted += result
                
                if cursor == "0":
                    break
            
            return Success(True)
        except Exception as e:
            self.logger.error(f"Error clearing cache entries: {str(e)}")
            return Failure(
                ErrorCode.REPOSITORY_ERROR,
                ErrorDetails(
                    message=f"Failed to clear cache entries: {str(e)}",
                    context={"model_type": model_type}
                )
            )
    
    def _entity_to_dict(self, entity: Entity) -> Dict[str, Any]:
        """
        Convert an entity to a dictionary for serialization.
        
        Args:
            entity: The entity to convert
            
        Returns:
            Dictionary representation of the entity
        """
        # Basic conversion
        result = {}
        
        for key, value in entity.__dict__.items():
            if isinstance(value, ValueObject):
                # Handle value objects like IDs
                result[key] = value.value
            elif isinstance(value, Entity):
                # Handle nested entities (simplified, might need more complex handling)
                result[key] = str(value.id)
            elif isinstance(value, datetime):
                # Handle datetime objects
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list, str, int, float, bool)) or value is None:
                # Handle primitive types directly
                result[key] = value
            else:
                # For other types, convert to string
                result[key] = str(value)
        
        return result