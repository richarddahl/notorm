"""
Database integration for the modern dependency injection system.

This module provides utilities for integrating the database provider
with the modern DI system.
"""

from typing import (
    TypeVar,
    Type,
    Callable,
    Any,
    Optional,
    Dict,
    List,
    cast,
    AsyncIterator,
)
from contextlib import asynccontextmanager

from fastapi import Depends

from sqlalchemy.ext.asyncio import AsyncSession
import asyncpg
import psycopg

# Use the modern DI system exclusively
from uno.dependencies.scoped_container import get_service

from uno.dependencies.interfaces import (
    UnoDatabaseProviderProtocol,
    UnoDBManagerProtocol,
    SQLEmitterFactoryProtocol,
    SQLExecutionProtocol,
    SchemaManagerProtocol,
    EventBusProtocol,
    DomainRepositoryProtocol,
    DomainServiceProtocol,
)
from uno.database.repository import UnoBaseRepository


T = TypeVar("T")
ModelT = TypeVar("ModelT")


@asynccontextmanager
async def get_db_session() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency for database sessions.

    Yields a database session and handles cleanup.

    Yields:
        An AsyncSession instance
    """
    db_provider = get_service(UnoDatabaseProviderProtocol)
    async with db_provider.async_session() as session:
        yield session


@asynccontextmanager
async def get_raw_connection() -> AsyncIterator[asyncpg.Connection]:
    """
    FastAPI dependency for raw database connections.

    Yields a raw database connection and handles cleanup.

    Yields:
        An asyncpg Connection instance
    """
    db_provider = get_service(UnoDatabaseProviderProtocol)
    async with db_provider.async_connection() as conn:
        yield conn


def get_repository(
    repo_class: Type[UnoBaseRepository],
) -> Callable[[AsyncSession], UnoBaseRepository]:
    """
    Create a FastAPI dependency for a repository.

    Args:
        repo_class: The repository class to instantiate

    Returns:
        A callable that FastAPI can use as a dependency
    """

    def dependency(
        session: AsyncSession = Depends(get_db_session),
    ) -> UnoBaseRepository:
        # Instantiate the repository with the session
        return repo_class(session)

    dependency.__name__ = f"get_{repo_class.__name__}"
    return dependency


def get_db_manager() -> Any:
    """
    Get the database manager instance for executing DDL statements.

    This is used in FastAPI applications to access the database manager
    for schema operations and executing emitters directly.

    Returns:
        A DBManager instance
    """
    return get_service(UnoDBManagerProtocol)


def get_sql_emitter_factory() -> Any:
    """
    Get the SQL emitter factory service.

    This service creates SQL emitters with the appropriate configuration.

    Returns:
        The SQL emitter factory service
    """
    return get_service(SQLEmitterFactoryProtocol)


def get_sql_execution_service() -> Any:
    """
    Get the SQL execution service.

    This service provides a higher-level interface for executing SQL operations.

    Returns:
        The SQL execution service
    """
    return get_service(SQLExecutionProtocol)


def get_schema_manager() -> Any:
    """
    Get the schema manager service.

    This service handles the creation and management of schemas for domain entities
    and database models, providing data validation and transformation
    between different application layers.

    Returns:
        The schema manager service
    """
    from uno.dto import get_dto_manager
    return get_dto_manager()


def get_event_bus() -> Any:
    """
    Get the event bus service.

    The event bus enables loosely coupled communication between different parts
    of the application using an event-driven architecture.

    Returns:
        The event bus service
    """
    return get_service(EventBusProtocol)


def get_event_publisher() -> Any:
    """
    Get the event publisher service.

    The event publisher provides a convenient interface for publishing events
    to the event bus.

    Returns:
        The event publisher service
    """
    from uno.core.events import EventPublisher

    return get_service(EventPublisher)


def get_domain_registry() -> Any:
    """
    Get the domain registry service.

    The domain registry provides centralized access to domain entities,
    repositories, and services.

    Returns:
        The domain registry service
    """
    from uno.domain.factory import DomainRegistry

    return get_service(DomainRegistry)


def get_domain_repository(entity_type: Type[T]) -> DomainRepositoryProtocol[T]:
    """
    Get a domain repository for a specific entity type.

    Args:
        entity_type: The type of entity to get a repository for

    Returns:
        A repository for the specified entity type
    """
    registry = get_domain_registry()
    return registry.get_repository(entity_type)


def get_domain_service(entity_type: Type[T]) -> DomainServiceProtocol[T]:
    """
    Get a domain service for a specific entity type.

    Args:
        entity_type: The type of entity to get a service for

    Returns:
        A service for the specified entity type
    """
    registry = get_domain_registry()
    return registry.get_service(entity_type)
