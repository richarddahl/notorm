# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain repositories for the Database module.

This module defines repository interfaces and implementations for the Database module,
providing data access for database entities and managing persistence operations.
"""

from abc import ABC, abstractmethod
from contextlib import asynccontextmanager, contextmanager
from typing import (
    Generic,
    Protocol,
    TypeVar,
    List,
    Any,
    Union,
    Type,
    AsyncIterator,
    Iterator,
    cast,
)
import logging
from datetime import datetime, UTC

from sqlalchemy import (
    select,
    insert,
    update,
    delete,
    text,
    create_engine,
    MetaData,
    Table,
    Column,
)
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    AsyncConnection,
)
from sqlalchemy.engine import Result, Row, Connection, Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql.expression import Select

from uno.core.errors.result import Success, Failure
from uno.core.errors.framework import FrameworkError
from uno.database.entities import (
    DatabaseId,
    ConnectionConfig,
    Transaction,
    TransactionId,
    TransactionIsolationLevel,
    QueryStatistics,
    QueryId,
    QueryPlan,
    IndexRecommendation,
    ConnectionPoolConfig,
    PoolStatistics,
    CachedResult,
    CacheKey,
    CacheConfig,
)


# Type variables for improved type safety
ModelT = TypeVar("ModelT")
EntityT = TypeVar("EntityT")


# Repository Protocols


class DatabaseSessionRepositoryProtocol(Protocol):
    """Repository protocol for database session management."""

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """
        Get a database session.

        Yields:
            An asynchronous database session
        """
        ...

    @contextmanager
    def get_sync_session(self) -> Iterator[Session]:
        """
        Get a synchronous database session.

        Yields:
            A synchronous database session
        """
        ...

    async def execute_query(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[Result, FrameworkError]:
        """
        Execute a database query.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the query result
        """
        ...

    async def fetch_all(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[List[dict[str, Any]], FrameworkError]:
        """
        Fetch all rows as dictionaries.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the rows as dictionaries
        """
        ...

    async def fetch_one(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[dict[str, Any] | None, FrameworkError]:
        """
        Fetch a single row as a dictionary.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the row as a dictionary or None
        """
        ...

    async def execute(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> int | FrameworkError:
        """
        Execute a query and return the number of affected rows.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the number of affected rows
        """
        ...


class DatabaseTransactionRepositoryProtocol(Protocol):
    """Repository protocol for database transaction management."""

    async def begin_transaction(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Begin a new transaction.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Returns:
            Result containing the transaction
        """
        ...

    async def commit_transaction(
        self, transaction_id: TransactionId | None
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Commit a transaction.

        Args:
            transaction_id: ID of the transaction to commit

        Returns:
            Result containing the committed transaction
        """
        ...

    async def rollback_transaction(
        self, transaction_id: TransactionId | None
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Rollback a transaction.

        Args:
            transaction_id: ID of the transaction to rollback

        Returns:
            Result containing the rolled back transaction
        """
        ...

    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> AsyncIterator[Transaction | None]:
        """
        Context manager for transaction management.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Yields:
            A transaction object
        """
        ...


class ModelRepositoryProtocol(Generic[ModelT, EntityT], Protocol):
    """Generic repository protocol for model operations."""

    async def get_by_id(
        self, id: Union[str, DatabaseId]
    ) -> EntityT | None | FrameworkError:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Result containing the entity if found
        """
        ...

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Result[list[EntityT | None], FrameworkError]:
        """
        List entities with optional filtering.

        Args:
            filters: Optional filters to apply
            order_by: Optional fields to order by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Result containing a list of entities
        """
        ...

    async def create(self, entity: EntityT) -> EntityT | FrameworkError:
        """
        Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Result containing the created entity
        """
        ...

    async def update(self, entity: EntityT) -> EntityT | FrameworkError:
        """
        Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Result containing the updated entity
        """
        ...

    async def delete(self, id: Union[str, DatabaseId]) -> bool | FrameworkError:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            Result containing success indicator
        """
        ...

    async def count(
        self, filters: dict[str, Any] | None = None
    ) -> int | FrameworkError:
        """
        Count entities with optional filtering.

        Args:
            filters: Optional filters to apply

        Returns:
            Result containing the count
        """
        ...


class QueryStatisticsRepositoryProtocol(Protocol):
    """Repository protocol for query statistics."""

    async def save_statistics(
        self, statistics: QueryStatistics
    ) -> Result[QueryStatistics, FrameworkError]:
        """
        Save query statistics.

        Args:
            statistics: Query statistics to save

        Returns:
            Result containing the saved statistics
        """
        ...

    async def get_statistics(
        self, query_id: QueryId
    ) -> QueryStatistics | None | FrameworkError:
        """
        Get query statistics by ID.

        Args:
            query_id: Query ID

        Returns:
            Result containing the statistics if found
        """
        ...

    async def list_statistics(
        self, limit: int = 100, offset: int = 0
    ) -> list[QueryStatistics] | FrameworkError:
        """
        List query statistics.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Result containing a list of statistics
        """
        ...

    async def get_slow_queries(
        self, threshold: float = 1.0, limit: int = 100  # seconds
    ) -> list[QueryStatistics] | FrameworkError:
        """
        Get slow queries.

        Args:
            threshold: Threshold in seconds for slow queries
            limit: Maximum number of results

        Returns:
            Result containing a list of slow query statistics
        """
        ...


class QueryPlanRepositoryProtocol(Protocol):
    """Repository protocol for query plans."""

    async def save_plan(self, plan: QueryPlan) -> Result[QueryPlan, FrameworkError]:
        """
        Save a query plan.

        Args:
            plan: Query plan to save

        Returns:
            Result containing the saved plan
        """
        ...

    async def get_plan(
        self, query_id: QueryId
    ) -> QueryPlan | None | FrameworkError:
        """
        Get a query plan by ID.

        Args:
            query_id: Query ID

        Returns:
            Result containing the plan if found
        """
        ...


class IndexRecommendationRepositoryProtocol(Protocol):
    """Repository protocol for index recommendations."""

    async def save_recommendation(
        self, recommendation: IndexRecommendation
    ) -> Result[IndexRecommendation, FrameworkError]:
        """
        Save an index recommendation.

        Args:
            recommendation: Index recommendation to save

        Returns:
            Result containing the saved recommendation
        """
        ...

    async def list_recommendations(
        self, table_name: str | None = None, limit: int = 100
    ) -> list[IndexRecommendation] | FrameworkError:
        """
        List index recommendations.

        Args:
            table_name: Optional table name to filter by
            limit: Maximum number of results

        Returns:
            Result containing a list of recommendations
        """
        ...


class QueryCacheRepositoryProtocol(Protocol):
    """Repository protocol for query cache management."""

    async def get_cached_result(
        self, key: CacheKey
    ) -> CachedResult | None | FrameworkError:
        """
        Get a cached query result.

        Args:
            key: Cache key

        Returns:
            Result containing the cached result if found
        """
        ...

    async def set_cached_result(
        self, result: CachedResult
    ) -> Result[CachedResult, FrameworkError]:
        """
        Set a cached query result.

        Args:
            result: Cached result to store

        Returns:
            Result containing the stored cached result
        """
        ...

    async def invalidate_cache(
        self, key: CacheKey | None = None
    ) -> int | FrameworkError:
        """
        Invalidate cache entries.

        Args:
            key: Optional cache key to invalidate (invalidates all if None)

        Returns:
            Result containing the number of invalidated entries
        """
        ...

    async def get_cache_size(self) -> int | FrameworkError:
        """
        Get the current cache size.

        Returns:
            Result containing the cache size
        """
        ...


class PoolStatisticsRepositoryProtocol(Protocol):
    """Repository protocol for connection pool statistics."""

    async def save_statistics(
        self, statistics: PoolStatistics
    ) -> Result[PoolStatistics, FrameworkError]:
        """
        Save pool statistics.

        Args:
            statistics: Pool statistics to save

        Returns:
            Result containing the saved statistics
        """
        ...

    async def get_recent_statistics(
        self, limit: int = 100
    ) -> list[PoolStatistics] | FrameworkError:
        """
        Get recent pool statistics.

        Args:
            limit: Maximum number of results

        Returns:
            Result containing a list of statistics
        """
        ...


# Repository Implementations


class SqlAlchemyDatabaseSessionRepository:
    """SQLAlchemy implementation of the database session repository."""

    def __init__(self, config: ConnectionConfig, logger: logging.Logger | None = None):
        """
        Initialize the repository.

        Args:
            config: Database connection configuration
            logger: Optional logger
        """
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

        # Create engine and session factory
        self.engine = self._create_engine()
        self.async_session_factory = sessionmaker(
            bind=self.engine, class_=AsyncSession, expire_on_commit=False
        )

        # Create sync engine and session factory
        self.sync_engine = self._create_sync_engine()
        self.sync_session_factory = sessionmaker(
            bind=self.sync_engine, expire_on_commit=False
        )

    def _create_engine(self) -> AsyncEngine:
        """
        Create the SQLAlchemy async engine.

        Returns:
            SQLAlchemy async engine
        """
        uri = str(self.config.get_uri())

        # Create the engine with pooling configuration
        engine = create_async_engine(
            uri,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,
            connect_args=self.config.connect_args or {},
        )

        return engine

    def _create_sync_engine(self) -> Engine:
        """
        Create the SQLAlchemy sync engine.

        Returns:
            SQLAlchemy sync engine
        """
        uri = str(self.config.get_uri())

        # Modify URI for sync connection if needed
        if "asyncpg" in uri:
            uri = uri.replace("asyncpg", "psycopg2")

        # Create the engine with pooling configuration
        engine = create_engine(
            uri,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            pool_pre_ping=True,
            connect_args=self.config.connect_args or {},
        )

        return engine

    @asynccontextmanager
    async def get_session(self) -> AsyncIterator[AsyncSession]:
        """
        Get a database session.

        Yields:
            An asynchronous database session
        """
        session = self.async_session_factory()
        try:
            yield session
        finally:
            await session.close()

    @contextmanager
    def get_sync_session(self) -> Iterator[Session]:
        """
        Get a synchronous database session.

        Yields:
            A synchronous database session
        """
        session = self.sync_session_factory()
        try:
            yield session
        finally:
            session.close()

    async def execute_query(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[Result, FrameworkError]:
        """
        Execute a database query.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the query result
        """
        try:
            async with self.get_session() as session:
                if isinstance(query, str):
                    stmt = text(query)
                    result = await session.execute(stmt, parameters or {})
                else:
                    result = await session.execute(query)
                return Success(result)
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error executing query: {str(e)}",
                )
            )

    async def fetch_all(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[List[dict[str, Any]], FrameworkError]:
        """
        Fetch all rows as dictionaries.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the rows as dictionaries
        """
        result = await self.execute_query(query, parameters)
        if isinstance(result, Failure):
            return result

        try:
            rows = result.value.mappings().all()
            return Success([dict(row) for row in rows])
        except Exception as e:
            self.logger.error(f"Error converting query results: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_RESULT_ERROR",
                    message=f"Error converting query results: {str(e)}",
                )
            )

    async def fetch_one(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> Result[dict[str, Any] | None, FrameworkError]:
        """
        Fetch a single row as a dictionary.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the row as a dictionary or None
        """
        result = await self.execute_query(query, parameters)
        if isinstance(result, Failure):
            return result

        try:
            row = result.value.mappings().first()
            return Success(dict(row) if row else None)
        except Exception as e:
            self.logger.error(f"Error converting query result: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_RESULT_ERROR",
                    message=f"Error converting query result: {str(e)}",
                )
            )

    async def execute(
        self, query: Union[str, Select], parameters: dict[str, Any] | None = None
    ) -> int | FrameworkError:
        """
        Execute a query and return the number of affected rows.

        Args:
            query: SQL query string or SQLAlchemy Select object
            parameters: Query parameters

        Returns:
            Result containing the number of affected rows
        """
        try:
            async with self.get_session() as session:
                if isinstance(query, str):
                    stmt = text(query)
                    result = await session.execute(stmt, parameters or {})
                else:
                    result = await session.execute(query)

                await session.commit()
                return Success(result.rowcount)
        except Exception as e:
            self.logger.error(f"Query execution error: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error executing query: {str(e)}",
                )
            )


class SqlAlchemyDatabaseTransactionRepository:
    """SQLAlchemy implementation of the database transaction repository."""

    def __init__(
        self,
        session_repository: DatabaseSessionRepositoryProtocol,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the repository.

        Args:
            session_repository: Database session repository
            logger: Optional logger
        """
        self.session_repository = session_repository
        self.logger = logger or logging.getLogger(__name__)

        # Track active transactions
        self._active_transactions: dict[str, Tuple[Transaction, AsyncSession]] = {}

    async def begin_transaction(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Begin a new transaction.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Returns:
            Result containing the transaction
        """
        try:
            # Create a new transaction object
            transaction_id = TransactionId.generate()
            transaction = Transaction(
                id=transaction_id,
                isolation_level=isolation_level,
                read_only=read_only,
                start_time=datetime.now(UTC),
            )

            # Get a session
            session = self.session_repository.async_session_factory()

            # Begin the transaction with specified isolation level
            await session.begin()

            # Set transaction options
            isolation_str = str(isolation_level.value)
            await session.execute(
                text(f"SET TRANSACTION ISOLATION LEVEL {isolation_str}")
            )

            if read_only:
                await session.execute(text("SET TRANSACTION READ ONLY"))

            # Store the active transaction
            self._active_transactions[str(transaction_id)] = (transaction, session)

            return Success(transaction)
        except Exception as e:
            self.logger.error(f"Error beginning transaction: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_TRANSACTION_ERROR",
                    message=f"Error beginning transaction: {str(e)}",
                )
            )

    async def commit_transaction(
        self, transaction_id: TransactionId | None
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Commit a transaction.

        Args:
            transaction_id: ID of the transaction to commit

        Returns:
            Result containing the committed transaction
        """
        try:
            # Check if the transaction exists
            transaction_key = str(transaction_id)
            if transaction_key not in self._active_transactions:
                return Failure(
                    FrameworkError(
                        code="TRANSACTION_NOT_FOUND",
                        message=f"Transaction {transaction_id} not found",
                    )
                )

            # Get the transaction and session
            transaction, session = self._active_transactions[transaction_key]

            # Commit the transaction
            await session.commit()

            # Update the transaction object
            transaction.complete(True)

            # Clean up
            await session.close()
            del self._active_transactions[transaction_key]

            return Success(transaction)
        except Exception as e:
            self.logger.error(f"Error committing transaction: {str(e)}")

            # Try to rollback
            try:
                if transaction_key in self._active_transactions:
                    _, session = self._active_transactions[transaction_key]
                    await session.rollback()
            except:
                pass

            return Failure(
                FrameworkError(
                    code="DATABASE_TRANSACTION_COMMIT_ERROR",
                    message=f"Error committing transaction: {str(e)}",
                )
            )

    async def rollback_transaction(
        self, transaction_id: TransactionId | None
    ) -> Result[Transaction | None, FrameworkError]:
        """
        Rollback a transaction.

        Args:
            transaction_id: ID of the transaction to rollback

        Returns:
            Result containing the rolled back transaction
        """
        try:
            # Check if the transaction exists
            transaction_key = str(transaction_id)
            if transaction_key not in self._active_transactions:
                return Failure(
                    FrameworkError(
                        code="TRANSACTION_NOT_FOUND",
                        message=f"Transaction {transaction_id} not found",
                    )
                )

            # Get the transaction and session
            transaction, session = self._active_transactions[transaction_key]

            # Rollback the transaction
            await session.rollback()

            # Update the transaction object
            transaction.complete(False)

            # Clean up
            await session.close()
            del self._active_transactions[transaction_key]

            return Success(transaction)
        except Exception as e:
            self.logger.error(f"Error rolling back transaction: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_TRANSACTION_ROLLBACK_ERROR",
                    message=f"Error rolling back transaction: {str(e)}",
                )
            )

    @asynccontextmanager
    async def transaction(
        self,
        isolation_level: TransactionIsolationLevel = TransactionIsolationLevel.READ_COMMITTED,
        read_only: bool = False,
    ) -> AsyncIterator[Transaction | None]:
        """
        Context manager for transaction management.

        Args:
            isolation_level: Transaction isolation level
            read_only: Whether the transaction is read-only

        Yields:
            A transaction object
        """
        # Begin the transaction
        transaction_result = await self.begin_transaction(isolation_level, read_only)
        if isinstance(transaction_result, Failure):
            raise Exception(
                f"Failed to begin transaction: {transaction_result.error.message}"
            )

        transaction = transaction_result.value

        try:
            # Yield the transaction for use
            yield transaction

            # Commit the transaction if no exceptions were raised
            commit_result = await self.commit_transaction(transaction.id)
            if isinstance(commit_result, Failure):
                raise Exception(
                    f"Failed to commit transaction: {commit_result.error.message}"
                )
        except Exception as e:
            # Rollback the transaction on exception
            self.logger.error(f"Transaction error, rolling back: {str(e)}")
            rollback_result = await self.rollback_transaction(transaction.id)
            if isinstance(rollback_result, Failure):
                self.logger.error(f"Rollback failed: {rollback_result.error.message}")

            # Re-raise the original exception
            raise


class SqlAlchemyModelRepository(Generic[ModelT, EntityT]):
    """Generic SQLAlchemy implementation of the model repository."""

    def __init__(
        self,
        session_repository: DatabaseSessionRepositoryProtocol,
        model_class: Type[ModelT],
        entity_class: type[EntityT],
        id_field: str = "id",
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the repository.

        Args:
            session_repository: Database session repository
            model_class: SQLAlchemy model class
            entity_class: Domain entity class
            id_field: Name of the ID field
            logger: Optional logger
        """
        self.session_repository = session_repository
        self.model_class = model_class
        self.entity_class = entity_class
        self.id_field = id_field
        self.logger = logger or logging.getLogger(__name__)

    def _entity_to_dict(self, entity: EntityT) -> dict[str, Any]:
        """
        Convert an entity to a dictionary for database operations.

        Args:
            entity: Domain entity

        Returns:
            Dictionary representation
        """
        if hasattr(entity, "to_dict"):
            return entity.to_dict()
        elif hasattr(entity, "model_dump"):
            return entity.model_dump()
        elif hasattr(entity, "__dict__"):
            return {k: v for k, v in entity.__dict__.items() if not k.startswith("_")}
        else:
            raise TypeError(f"Unable to convert {type(entity)} to dictionary")

    def _model_to_entity(self, model: ModelT) -> EntityT:
        """
        Convert a model to a domain entity.

        Args:
            model: Database model

        Returns:
            Domain entity
        """
        if hasattr(model, "to_dict"):
            data = model.to_dict()
        elif hasattr(model, "__dict__"):
            data = {k: v for k, v in model.__dict__.items() if not k.startswith("_")}
        else:
            raise TypeError(f"Unable to convert {type(model)} to dictionary")

        # Create the entity from the data
        return self.entity_class(**data)

    async def get_by_id(
        self, id: Union[str, DatabaseId]
    ) -> EntityT | None | FrameworkError:
        """
        Get an entity by ID.

        Args:
            id: Entity ID

        Returns:
            Result containing the entity if found
        """
        id_value = str(id)

        try:
            async with self.session_repository.get_session() as session:
                stmt = select(self.model_class).where(
                    getattr(self.model_class, self.id_field) == id_value
                )
                result = await session.execute(stmt)
                model = result.scalars().first()

                if model is None:
                    return Success(None)

                entity = self._model_to_entity(model)
                return Success(entity)
        except Exception as e:
            self.logger.error(f"Error getting entity by ID: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error getting entity by ID: {str(e)}",
                )
            )

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        order_by: list[str] | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Result[list[EntityT | None], FrameworkError]:
        """
        List entities with optional filtering.

        Args:
            filters: Optional filters to apply
            order_by: Optional fields to order by
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Result containing a list of entities
        """
        try:
            stmt = select(self.model_class)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        stmt = stmt.where(getattr(self.model_class, field) == value)

            # Apply ordering
            if order_by:
                for field in order_by:
                    descending = field.startswith("-")
                    field_name = field[1:] if descending else field

                    if hasattr(self.model_class, field_name):
                        column = getattr(self.model_class, field_name)
                        stmt = stmt.order_by(column.desc() if descending else column)

            # Apply pagination
            if limit is not None:
                stmt = stmt.limit(limit)

            if offset is not None:
                stmt = stmt.offset(offset)

            # Execute the query
            async with self.session_repository.get_session() as session:
                result = await session.execute(stmt)
                models = result.scalars().all()

                # Convert models to entities
                entities = [self._model_to_entity(model) for model in models]
                return Success(entities)
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error listing entities: {str(e)}",
                )
            )

    async def create(self, entity: EntityT) -> EntityT | FrameworkError:
        """
        Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Result containing the created entity
        """
        try:
            # Convert entity to dict
            data = self._entity_to_dict(entity)

            # Remove ID if it's None or empty
            id_value = data.get(self.id_field)
            if id_value is None or id_value == "":
                data.pop(self.id_field, None)

            # Create the model
            async with self.session_repository.get_session() as session:
                model = self.model_class(**data)
                session.add(model)
                await session.commit()
                await session.refresh(model)

                # Convert back to entity
                created_entity = self._model_to_entity(model)
                return Success(created_entity)
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error creating entity: {str(e)}",
                )
            )

    async def update(self, entity: EntityT) -> EntityT | FrameworkError:
        """
        Update an existing entity.

        Args:
            entity: Entity to update

        Returns:
            Result containing the updated entity
        """
        try:
            # Convert entity to dict
            data = self._entity_to_dict(entity)

            # Extract ID
            id_value = data.get(self.id_field)
            if id_value is None:
                return Failure(
                    FrameworkError(
                        code="INVALID_ENTITY", message=f"Entity has no ID value"
                    )
                )

            # Check if entity exists
            async with self.session_repository.get_session() as session:
                stmt = select(self.model_class).where(
                    getattr(self.model_class, self.id_field) == id_value
                )
                result = await session.execute(stmt)
                model = result.scalars().first()

                if model is None:
                    return Failure(
                        FrameworkError(
                            code="ENTITY_NOT_FOUND",
                            message=f"Entity with ID {id_value} not found",
                        )
                    )

                # Update model attributes
                for key, value in data.items():
                    if hasattr(model, key):
                        setattr(model, key, value)

                await session.commit()
                await session.refresh(model)

                # Convert back to entity
                updated_entity = self._model_to_entity(model)
                return Success(updated_entity)
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error updating entity: {str(e)}",
                )
            )

    async def delete(self, id: Union[str, DatabaseId]) -> bool | FrameworkError:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            Result containing success indicator
        """
        id_value = str(id)

        try:
            async with self.session_repository.get_session() as session:
                # Check if entity exists
                stmt = select(self.model_class).where(
                    getattr(self.model_class, self.id_field) == id_value
                )
                result = await session.execute(stmt)
                model = result.scalars().first()

                if model is None:
                    return Success(False)

                # Delete the entity
                await session.delete(model)
                await session.commit()

                return Success(True)
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error deleting entity: {str(e)}",
                )
            )

    async def count(
        self, filters: dict[str, Any] | None = None
    ) -> int | FrameworkError:
        """
        Count entities with optional filtering.

        Args:
            filters: Optional filters to apply

        Returns:
            Result containing the count
        """
        try:
            from sqlalchemy import func

            stmt = select(func.count()).select_from(self.model_class)

            # Apply filters
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model_class, field):
                        stmt = stmt.where(getattr(self.model_class, field) == value)

            # Execute the query
            async with self.session_repository.get_session() as session:
                result = await session.execute(stmt)
                count = result.scalar_one()

                return Success(count)
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            return Failure(
                FrameworkError(
                    code="DATABASE_QUERY_ERROR",
                    message=f"Error counting entities: {str(e)}",
                )
            )


class InMemoryQueryStatisticsRepository:
    """In-memory implementation of the query statistics repository."""

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the repository.

        Args:
            max_entries: Maximum number of entries to store
        """
        self._statistics: dict[str, QueryStatistics] = {}
        self.max_entries = max_entries

    async def save_statistics(
        self, statistics: QueryStatistics
    ) -> Result[QueryStatistics, FrameworkError]:
        """
        Save query statistics.

        Args:
            statistics: Query statistics to save

        Returns:
            Result containing the saved statistics
        """
        # Enforce max entries limit
        if len(self._statistics) >= self.max_entries:
            # Remove oldest entry
            oldest_time = datetime.max.replace(tzinfo=UTC)
            oldest_key = None

            for key, stats in self._statistics.items():
                if stats.start_time < oldest_time:
                    oldest_time = stats.start_time
                    oldest_key = key

            if oldest_key:
                del self._statistics[oldest_key]

        # Save the statistics
        self._statistics[str(statistics.query_id)] = statistics
        return Success(statistics)

    async def get_statistics(
        self, query_id: QueryId
    ) -> QueryStatistics | None | FrameworkError:
        """
        Get query statistics by ID.

        Args:
            query_id: Query ID

        Returns:
            Result containing the statistics if found
        """
        stats = self._statistics.get(str(query_id))
        return Success(stats)

    async def list_statistics(
        self, limit: int = 100, offset: int = 0
    ) -> list[QueryStatistics] | FrameworkError:
        """
        List query statistics.

        Args:
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            Result containing a list of statistics
        """
        # Sort statistics by start time, most recent first
        sorted_stats = sorted(
            self._statistics.values(), key=lambda s: s.start_time, reverse=True
        )

        # Apply pagination
        paginated = sorted_stats[offset : offset + limit]
        return Success(paginated)

    async def get_slow_queries(
        self, threshold: float = 1.0, limit: int = 100  # seconds
    ) -> list[QueryStatistics] | FrameworkError:
        """
        Get slow queries.

        Args:
            threshold: Threshold in seconds for slow queries
            limit: Maximum number of results

        Returns:
            Result containing a list of slow query statistics
        """
        # Filter for slow queries
        slow_queries = [
            stats for stats in self._statistics.values() if stats.duration > threshold
        ]

        # Sort by execution time, slowest first
        sorted_queries = sorted(slow_queries, key=lambda s: s.duration, reverse=True)

        # Apply limit
        limited = sorted_queries[:limit]
        return Success(limited)


class InMemoryQueryPlanRepository:
    """In-memory implementation of the query plan repository."""

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the repository.

        Args:
            max_entries: Maximum number of entries to store
        """
        self._plans: dict[str, QueryPlan] = {}
        self.max_entries = max_entries

    async def save_plan(self, plan: QueryPlan) -> Result[QueryPlan, FrameworkError]:
        """
        Save a query plan.

        Args:
            plan: Query plan to save

        Returns:
            Result containing the saved plan
        """
        # Enforce max entries limit
        if len(self._plans) >= self.max_entries:
            # Remove oldest entry
            oldest_time = datetime.max.replace(tzinfo=UTC)
            oldest_key = None

            for key, p in self._plans.items():
                if p.analyze_time < oldest_time:
                    oldest_time = p.analyze_time
                    oldest_key = key

            if oldest_key:
                del self._plans[oldest_key]

        # Save the plan
        self._plans[str(plan.query_id)] = plan
        return Success(plan)

    async def get_plan(
        self, query_id: QueryId
    ) -> QueryPlan | None | FrameworkError:
        """
        Get a query plan by ID.

        Args:
            query_id: Query ID

        Returns:
            Result containing the plan if found
        """
        plan = self._plans.get(str(query_id))
        return Success(plan)


class InMemoryIndexRecommendationRepository:
    """In-memory implementation of the index recommendation repository."""

    def __init__(self):
        """Initialize the repository."""
        self._recommendations: list[IndexRecommendation] = []

    async def save_recommendation(
        self, recommendation: IndexRecommendation
    ) -> Result[IndexRecommendation, FrameworkError]:
        """
        Save an index recommendation.

        Args:
            recommendation: Index recommendation to save

        Returns:
            Result containing the saved recommendation
        """
        # Check for duplicate recommendation
        for existing in self._recommendations:
            if (
                existing.table_name == recommendation.table_name
                and existing.column_names == recommendation.column_names
                and existing.index_type == recommendation.index_type
            ):
                # Update existing recommendation
                existing.estimated_improvement = max(
                    existing.estimated_improvement, recommendation.estimated_improvement
                )
                return Success(existing)

        # Add new recommendation
        self._recommendations.append(recommendation)
        return Success(recommendation)

    async def list_recommendations(
        self, table_name: str | None = None, limit: int = 100
    ) -> list[IndexRecommendation] | FrameworkError:
        """
        List index recommendations.

        Args:
            table_name: Optional table name to filter by
            limit: Maximum number of results

        Returns:
            Result containing a list of recommendations
        """
        # Filter by table name if provided
        if table_name:
            filtered = [r for r in self._recommendations if r.table_name == table_name]
        else:
            filtered = self._recommendations

        # Sort by priority, then by estimated improvement
        sorted_recommendations = sorted(
            filtered, key=lambda r: (r.priority, r.estimated_improvement), reverse=True
        )

        # Apply limit
        limited = sorted_recommendations[:limit]
        return Success(limited)


class InMemoryQueryCacheRepository:
    """In-memory implementation of the query cache repository."""

    def __init__(self, max_size: int = 1000):
        """
        Initialize the repository.

        Args:
            max_size: Maximum cache size
        """
        self._cache: dict[str, CachedResult] = {}
        self.max_size = max_size

    async def get_cached_result(
        self, key: CacheKey
    ) -> CachedResult | None | FrameworkError:
        """
        Get a cached query result.

        Args:
            key: Cache key

        Returns:
            Result containing the cached result if found
        """
        cached = self._cache.get(key.combined_key)

        # Check if result has expired
        if cached and cached.is_expired:
            del self._cache[key.combined_key]
            return Success(None)

        if cached:
            # Increment hit count
            cached.increment_hit_count()

        return Success(cached)

    async def set_cached_result(
        self, result: CachedResult
    ) -> Result[CachedResult, FrameworkError]:
        """
        Set a cached query result.

        Args:
            result: Cached result to store

        Returns:
            Result containing the stored cached result
        """
        # Enforce max size limit
        if len(self._cache) >= self.max_size:
            # Remove least recently used entry
            lru_key = None
            lru_time = datetime.max.replace(tzinfo=UTC)

            for key, cached in self._cache.items():
                if cached.created_at < lru_time:
                    lru_time = cached.created_at
                    lru_key = key

            if lru_key:
                del self._cache[lru_key]

        # Store the result
        self._cache[result.key.combined_key] = result
        return Success(result)

    async def invalidate_cache(
        self, key: CacheKey | None = None
    ) -> int | FrameworkError:
        """
        Invalidate cache entries.

        Args:
            key: Optional cache key to invalidate (invalidates all if None)

        Returns:
            Result containing the number of invalidated entries
        """
        if key:
            # Invalidate specific entry
            if key.combined_key in self._cache:
                del self._cache[key.combined_key]
                return Success(1)
            return Success(0)
        else:
            # Invalidate all entries
            count = len(self._cache)
            self._cache.clear()
            return Success(count)

    async def get_cache_size(self) -> int | FrameworkError:
        """
        Get the current cache size.

        Returns:
            Result containing the cache size
        """
        return Success(len(self._cache))


class InMemoryPoolStatisticsRepository:
    """In-memory implementation of the connection pool statistics repository."""

    def __init__(self, max_entries: int = 1000):
        """
        Initialize the repository.

        Args:
            max_entries: Maximum number of entries to store
        """
        self._statistics: list[PoolStatistics] = []
        self.max_entries = max_entries

    async def save_statistics(
        self, statistics: PoolStatistics
    ) -> Result[PoolStatistics, FrameworkError]:
        """
        Save pool statistics.

        Args:
            statistics: Pool statistics to save

        Returns:
            Result containing the saved statistics
        """
        # Enforce max entries limit
        if len(self._statistics) >= self.max_entries:
            # Remove oldest entry
            self._statistics.pop(0)

        # Save the statistics
        self._statistics.append(statistics)
        return Success(statistics)

    async def get_recent_statistics(
        self, limit: int = 100
    ) -> list[PoolStatistics] | FrameworkError:
        """
        Get recent pool statistics.

        Args:
            limit: Maximum number of results

        Returns:
            Result containing a list of statistics
        """
        # Sort by timestamp, most recent first
        sorted_stats = sorted(self._statistics, key=lambda s: s.timestamp, reverse=True)

        # Apply limit
        limited = sorted_stats[:limit]
        return Success(limited)
