"""Query service implementation for the Uno framework.

This module defines query services that use read models for efficient querying
as part of the CQRS pattern's query side.
"""

import logging
from typing import (
    Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Protocol,
    cast
)
from uuid import uuid4

from pydantic import ConfigDict
from uno.domain.cqrs import Query, QueryHandler, QueryResult
from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.cache_service import ReadModelCache

# Type variables
T = TypeVar('T', bound=ReadModel)
QueryT = TypeVar('QueryT', bound=Query)
ResultT = TypeVar('ResultT')


class ReadModelQuery(Query[T]):
    """
    Base class for read model queries.
    
    Read model queries are used to retrieve read models in a type-safe way.
    
    Type Parameters:
        T: The type of read model this query returns
    """
    pass


class GetByIdQuery(ReadModelQuery[T]):
    """Query to get a read model by ID."""
    
    model_config = ConfigDict(frozen=False)
    id: str
    
    def __init__(self, id: str):
        """
        Initialize the query.
        
        Args:
            id: The read model ID
        """
        super().__init__(id=id, query_id=str(uuid4()))


class FindByQuery(ReadModelQuery[T]):
    """Query to find read models by criteria."""
    
    model_config = ConfigDict(frozen=False)
    criteria: Dict[str, Any]
    
    def __init__(self, criteria: Dict[str, Any]):
        """
        Initialize the query.
        
        Args:
            criteria: The query criteria
        """
        super().__init__(criteria=criteria, query_id=str(uuid4()))


class ReadModelQueryService(Generic[T]):
    """
    Service for querying read models.
    
    This service provides a high-level API for querying read models,
    with support for caching and other optimizations.
    """
    
    def __init__(
        self,
        repository: ReadModelRepository[T],
        model_type: Type[T],
        cache: Optional[ReadModelCache[T]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query service.
        
        Args:
            repository: The repository for retrieving read models
            model_type: The type of read model this service handles
            cache: Optional cache for read models
            logger: Optional logger instance
        """
        self.repository = repository
        self.model_type = model_type
        self.cache = cache
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        # Try to get from cache first
        if self.cache:
            cached_model = await self.cache.get(id)
            if cached_model:
                self.logger.debug(f"Cache hit for read model {id}")
                return cached_model
        
        # Get from repository
        model = await self.repository.get(id)
        
        # Cache the result if found
        if model and self.cache:
            await self.cache.set(id, model)
        
        return model
    
    async def find(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            List of matching read models
        """
        # Currently we don't cache find results, as it would be complex
        # to invalidate them correctly
        return await self.repository.find(criteria)
    
    async def handle_query(self, query: ReadModelQuery[T]) -> Any:
        """
        Handle a read model query.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        if isinstance(query, GetByIdQuery):
            return await self.get_by_id(query.id)
        elif isinstance(query, FindByQuery):
            return await self.find(query.criteria)
        else:
            raise ValueError(f"Unsupported query type: {type(query).__name__}")


class ReadModelQueryHandler(QueryHandler[QueryT, ResultT]):
    """
    Query handler for read model queries.
    
    This handler delegates to a query service to handle read model queries.
    """
    
    def __init__(
        self,
        query_type: Type[QueryT],
        query_service: ReadModelQueryService[Any],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query handler.
        
        Args:
            query_type: The type of query this handler processes
            query_service: The query service to delegate to
            logger: Optional logger instance
        """
        self.query_type = query_type
        self.query_service = query_service
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def handle(self, query: QueryT) -> ResultT:
        """
        Handle a query.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        if not isinstance(query, ReadModelQuery):
            raise ValueError(f"Query {query} is not a ReadModelQuery")
        
        return cast(ResultT, await self.query_service.handle_query(query))