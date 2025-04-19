"""
Dependency injection integration for repositories.

This module provides utilities for integrating repositories with the DI container.

NOTE: The UnitOfWork functionality in this module is deprecated. Use the 
AbstractUnitOfWork, DatabaseUnitOfWork, and related classes from uno.core.uow instead.
"""

import logging
from typing import Any, Callable, Optional, Type, TypeVar, Dict, cast

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.di import inject_dependency
from uno.dependencies.database import get_async_session
from uno.dependencies.modern_provider import register_provider
from uno.domain.core import Entity, AggregateRoot
from uno.core.base.repository import BaseRepository
from uno.infrastructure.repositories.factory import (
    initialize_factories,
    create_repository,
    create_unit_of_work,
    get_repository_factory,
)
from uno.infrastructure.repositories.protocols import (
    UnitOfWorkProtocol,
    RepositoryProtocol
)
from uno.infrastructure.repositories.unit_of_work import UnitOfWork


# Type variables
T = TypeVar("T")  # Entity type
E = TypeVar("E", bound=Entity)  # Entity constrained to Entity
A = TypeVar("A", bound=AggregateRoot)  # Entity constrained to AggregateRoot
ID = TypeVar("ID")  # ID type


# Repository cache to avoid creating multiple repositories for the same entity type
_REPOSITORY_CACHE: Dict[Type, BaseRepository] = {}


def init_repository_system(
    session_factory: Optional[Callable[[], AsyncSession]] = None,
    logger: Optional[logging.Logger] = None
) -> None:
    """
    Initialize the repository system.
    
    This should be called during application startup to configure the repository
    factories with the appropriate session factory and logger.
    
    Args:
        session_factory: Factory for creating SQLAlchemy sessions
        logger: Logger for repositories
    """
    initialize_factories(session_factory=session_factory, logger=logger)
    
    # Register providers with the DI container
    register_provider("get_repository", get_repository)
    register_provider("get_unit_of_work", get_unit_of_work)


async def get_repository(
    entity_type: Type[T],
    session: Optional[AsyncSession] = None,
    model_class: Optional[Type[Any]] = None,
    include_specification: bool = False,
    include_batch: bool = False,
    include_streaming: bool = False,
    include_events: bool = False,
    use_cache: bool = True,
) -> BaseRepository[T, Any]:
    """
    Get a repository for the specified entity type.
    
    This is the main entry point for obtaining repositories through the DI system.
    
    Args:
        entity_type: The entity type for the repository
        session: SQLAlchemy session (injected if not provided)
        model_class: SQLAlchemy model class
        include_specification: Whether to include specification support
        include_batch: Whether to include batch operation support
        include_streaming: Whether to include streaming support
        include_events: Whether to include event collection
        use_cache: Whether to use the repository cache
        
    Returns:
        A repository for the entity type
    """
    # Check cache first if enabled
    cache_key = (
        entity_type,
        include_specification,
        include_batch,
        include_streaming,
        include_events
    )
    
    if use_cache and cache_key in _REPOSITORY_CACHE:
        return cast(BaseRepository[T, Any], _REPOSITORY_CACHE[cache_key])
    
    # Get session if not provided
    if session is None:
        session = await inject_dependency(get_async_session)
    
    # Create repository
    repo = create_repository(
        entity_type=entity_type,
        session_or_model=session,
        model_class=model_class,
        include_specification=include_specification,
        include_batch=include_batch,
        include_streaming=include_streaming,
        include_events=include_events,
    )
    
    # Cache if enabled
    if use_cache:
        _REPOSITORY_CACHE[cache_key] = repo
    
    return repo


async def get_unit_of_work(
    session: Optional[AsyncSession] = None,
    in_memory: bool = False,
) -> UnitOfWork:
    """
    Get a unit of work instance.
    
    DEPRECATED: Use the UnitOfWork implementations from uno.core.uow instead.
    
    Args:
        session: SQLAlchemy session (injected if not provided)
        in_memory: Whether to create an in-memory unit of work
        
    Returns:
        A unit of work instance
    """
    import warnings
    warnings.warn(
        "get_unit_of_work is deprecated. Use the UnitOfWork implementations from "
        "uno.core.uow instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Get session if not provided and not using in-memory
    if session is None and not in_memory:
        session = await inject_dependency(get_async_session)
    
    # Create unit of work
    return create_unit_of_work(in_memory=in_memory, session=session)


async def register_specification_translator(
    entity_type: Type[T],
    translator: Any
) -> None:
    """
    Register a specification translator for an entity type.
    
    Args:
        entity_type: The entity type
        translator: The specification translator
    """
    factory = get_repository_factory()
    factory.register_specification_translator(entity_type, translator)
    
    # Clear cache to ensure new translators are used
    _REPOSITORY_CACHE.clear()


def clear_repository_cache() -> None:
    """Clear the repository cache."""
    _REPOSITORY_CACHE.clear()