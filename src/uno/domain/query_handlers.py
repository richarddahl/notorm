"""
Specialized query handlers for the CQRS pattern in the Uno framework.

This module provides optimized query handlers for common query patterns,
supporting the query side of the CQRS pattern.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, cast, Protocol, Union

from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from uno.domain.cqrs import Query, QueryHandler, QueryResult
from uno.domain.model import Entity


# Type variables
T = TypeVar('T')
EntityT = TypeVar('EntityT', bound=Entity)
ModelT = TypeVar('ModelT')


class SessionProvider(Protocol):
    """Protocol for objects that can provide a database session."""
    
    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        ...


QT = TypeVar('QT', bound=Query[Any])

class SqlQueryHandler(QueryHandler[QT, T], Generic[QT, T, ModelT], ABC):
    """
    Base class for SQL-based query handlers.
    
    These handlers execute optimized SQL queries directly on the database,
    bypassing the domain model for improved performance.
    """
    
    def __init__(
        self,
        query_type: Type[QT],
        session_provider: SessionProvider,
        model_class: Type[ModelT],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the SQL query handler.
        
        Args:
            query_type: The type of query this handler can process
            session_provider: Provider for database sessions
            model_class: The SQLAlchemy model class
            logger: Optional logger instance
        """
        super().__init__(query_type, logger)
        self.session_provider = session_provider
        self.model_class = model_class
    
    @abstractmethod
    def build_query(self, query: QT) -> Select:
        """
        Build an SQLAlchemy query for the given domain query.
        
        Args:
            query: The domain query
            
        Returns:
            An SQLAlchemy Select object
        """
        pass
    
    @abstractmethod
    def map_result(self, result: Any) -> T:
        """
        Map the query result to the expected output type.
        
        Args:
            result: The raw query result
            
        Returns:
            The mapped result
        """
        pass
    
    async def _handle(self, query: QT) -> T:
        """
        Handle a query by executing an optimized SQL query.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        # Build the query
        sql_query = self.build_query(query)
        
        # Execute the query
        async with self.session_provider.get_session() as session:
            result = await session.execute(sql_query)
            
            # Map the result
            return self.map_result(result)


class EntityByIdQuery(Query[EntityT]):
    """Query to get an entity by ID."""
    
    id: str


class EntityByIdQueryHandler(QueryHandler[EntityByIdQuery[EntityT], Optional[EntityT]], Generic[EntityT]):
    """Handler for the EntityByIdQuery."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        repository: Any,  # Repository[EntityT]
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the entity by ID query handler.
        
        Args:
            entity_type: The type of entity to retrieve
            repository: The repository to use for retrieval
            logger: Optional logger instance
        """
        super().__init__(EntityByIdQuery[entity_type], logger)
        self.entity_type = entity_type
        self.repository = repository
    
    async def _handle(self, query: EntityByIdQuery[EntityT]) -> Optional[EntityT]:
        """
        Handle the query by retrieving the entity from the repository.
        
        Args:
            query: The query to handle
            
        Returns:
            The entity if found, None otherwise
        """
        return await self.repository.get(query.id)


class EntityListQuery(Query[List[EntityT]], Generic[EntityT]):
    """Query to get a list of entities with filtering and pagination."""
    
    filters: Optional[Dict[str, Any]] = None
    order_by: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class EntityListQueryHandler(QueryHandler[EntityListQuery[EntityT], List[EntityT]], Generic[EntityT]):
    """Handler for the EntityListQuery."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        repository: Any,  # Repository[EntityT]
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the entity list query handler.
        
        Args:
            entity_type: The type of entity to retrieve
            repository: The repository to use for retrieval
            logger: Optional logger instance
        """
        super().__init__(EntityListQuery[entity_type], logger)
        self.entity_type = entity_type
        self.repository = repository
    
    async def _handle(self, query: EntityListQuery[EntityT]) -> List[EntityT]:
        """
        Handle the query by retrieving entities from the repository.
        
        Args:
            query: The query to handle
            
        Returns:
            List of entities matching the criteria
        """
        return await self.repository.list(
            filters=query.filters,
            order_by=query.order_by,
            limit=query.limit,
            offset=query.offset
        )


class CountQuery(Query[int], Generic[EntityT]):
    """Query to count entities matching a filter."""
    
    filters: Optional[Dict[str, Any]] = None


class CountQueryHandler(QueryHandler[CountQuery[EntityT], int], Generic[EntityT]):
    """Handler for the CountQuery."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        repository: Any,  # Repository[EntityT]
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the count query handler.
        
        Args:
            entity_type: The type of entity to count
            repository: The repository to use for counting
            logger: Optional logger instance
        """
        super().__init__(CountQuery[entity_type], logger)
        self.entity_type = entity_type
        self.repository = repository
    
    async def _handle(self, query: CountQuery[EntityT]) -> int:
        """
        Handle the query by counting entities in the repository.
        
        Args:
            query: The query to handle
            
        Returns:
            The count of matching entities
        """
        return await self.repository.count(filters=query.filters)


class SqlCountQuery(Query[int]):
    """Query to count records using direct SQL."""
    
    table_name: str
    filters: Optional[Dict[str, Any]] = None


class SqlCountQueryHandler(SqlQueryHandler[SqlCountQuery, int, Any]):
    """Handler for the SqlCountQuery."""
    
    def build_query(self, query: SqlCountQuery) -> Select:
        """
        Build an SQLAlchemy count query.
        
        Args:
            query: The domain query
            
        Returns:
            An SQLAlchemy Select object
        """
        # Start with a base count query
        sql_query = select(func.count()).select_from(text(query.table_name))
        
        # Apply filters
        if query.filters:
            for key, value in query.filters.items():
                sql_query = sql_query.where(text(f"{key} = :{key}"))
        
        return sql_query
    
    def map_result(self, result: Any) -> int:
        """
        Map the query result to an integer count.
        
        Args:
            result: The raw query result
            
        Returns:
            The count as an integer
        """
        return result.scalar() or 0


@dataclass
class PaginatedResult(Generic[T]):
    """
    Paginated query result.
    
    This class represents a paginated list of items along with
    metadata about the pagination.
    """
    
    items: List[T]
    total: int
    page: int
    page_size: int
    
    @property
    def total_pages(self) -> int:
        """Calculate the total number of pages."""
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size
    
    @property
    def has_previous(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.total_pages


class PaginatedQuery(Query[PaginatedResult[T]], Generic[T]):
    """Base class for queries that return paginated results."""
    
    page: int = 1
    page_size: int = 50
    
    @property
    def offset(self) -> int:
        """Calculate the offset from page and page_size."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get the page size as the limit."""
        return self.page_size


class PaginatedEntityQuery(PaginatedQuery[EntityT], Generic[EntityT]):
    """Query to get a paginated list of entities."""
    
    filters: Optional[Dict[str, Any]] = None
    order_by: Optional[List[str]] = None


class PaginatedEntityQueryHandler(QueryHandler[PaginatedEntityQuery[EntityT], PaginatedResult[EntityT]], Generic[EntityT]):
    """Handler for the PaginatedEntityQuery."""
    
    def __init__(
        self,
        entity_type: Type[EntityT],
        repository: Any,  # Repository[EntityT]
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the paginated entity query handler.
        
        Args:
            entity_type: The type of entity to retrieve
            repository: The repository to use for retrieval
            logger: Optional logger instance
        """
        super().__init__(PaginatedEntityQuery[entity_type], logger)
        self.entity_type = entity_type
        self.repository = repository
    
    async def _handle(self, query: PaginatedEntityQuery[EntityT]) -> PaginatedResult[EntityT]:
        """
        Handle the query by retrieving a paginated list of entities.
        
        Args:
            query: The query to handle
            
        Returns:
            A paginated result with entities
        """
        # Get the items for the current page
        items = await self.repository.list(
            filters=query.filters,
            order_by=query.order_by,
            limit=query.page_size,
            offset=query.offset
        )
        
        # Get the total count
        total = await self.repository.count(filters=query.filters)
        
        # Create the paginated result
        return PaginatedResult(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size
        )


class SqlPaginatedQuery(PaginatedQuery[Dict[str, Any]]):
    """Query to get a paginated list of records using direct SQL."""
    
    table_name: str
    select_columns: List[str]
    filters: Optional[Dict[str, Any]] = None
    order_by: Optional[List[str]] = None


class SqlPaginatedQueryHandler(SqlQueryHandler[SqlPaginatedQuery, PaginatedResult[Dict[str, Any]], Any]):
    """Handler for the SqlPaginatedQuery."""
    
    def build_query(self, query: SqlPaginatedQuery) -> Select:
        """
        Build an SQLAlchemy query for paginated results.
        
        Args:
            query: The domain query
            
        Returns:
            An SQLAlchemy Select object
        """
        # Select columns
        columns = [text(col) for col in query.select_columns]
        sql_query = select(*columns).select_from(text(query.table_name))
        
        # Apply filters
        if query.filters:
            for key, value in query.filters.items():
                sql_query = sql_query.where(text(f"{key} = :{key}"))
        
        # Apply ordering
        if query.order_by:
            for field in query.order_by:
                if field.startswith('-'):
                    sql_query = sql_query.order_by(text(f"{field[1:]} DESC"))
                else:
                    sql_query = sql_query.order_by(text(field))
        
        # Apply pagination
        sql_query = sql_query.limit(query.limit).offset(query.offset)
        
        return sql_query
    
    async def _handle(self, query: SqlPaginatedQuery) -> PaginatedResult[Dict[str, Any]]:
        """
        Handle the query by executing it and counting the total results.
        
        Args:
            query: The query to handle
            
        Returns:
            A paginated result with dictionary items
        """
        # Build the query for items
        items_query = self.build_query(query)
        
        # Build a count query
        count_query = select(func.count()).select_from(text(query.table_name))
        if query.filters:
            for key, value in query.filters.items():
                count_query = count_query.where(text(f"{key} = :{key}"))
        
        # Execute both queries
        async with self.session_provider.get_session() as session:
            # Get items
            items_result = await session.execute(items_query, query.filters or {})
            items = [dict(row) for row in items_result]
            
            # Get total count
            count_result = await session.execute(count_query, query.filters or {})
            total = count_result.scalar() or 0
        
        # Create paginated result
        return PaginatedResult(
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
    
    def map_result(self, result: Any) -> PaginatedResult[Dict[str, Any]]:
        """Not used as _handle is overridden."""
        pass