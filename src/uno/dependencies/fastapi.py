"""
FastAPI integration for dependency injection.

This module provides utilities for integrating the DI container
with FastAPI's dependency injection system.
"""

from typing import AsyncIterator

from typing import TypeVar, Type, Callable, Any, Optional, Dict, List, cast
from fastapi import Depends

import inject
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.interfaces import (
    UnoRepositoryProtocol,
    UnoServiceProtocol,
    UnoConfigProtocol,
)
from uno.dependencies.container import get_instance


T = TypeVar("T")
ModelT = TypeVar("ModelT")


def inject_dependency(dep_class: Type[T]) -> Callable[[], T]:
    """
    Create a FastAPI dependency that resolves an instance from the DI container.

    Args:
        dep_class: The class to resolve

    Returns:
        A callable that FastAPI can use as a dependency
    """

    def dependency() -> T:
        return get_instance(dep_class)

    # Set a more descriptive name for FastAPI's OpenAPI docs
    dependency.__name__ = f"get_{dep_class.__name__}"
    return dependency


# Import the working db session function from database.py
from uno.dependencies.database import get_db_session


def get_repository(
    repo_class: Type[UnoRepositoryProtocol[ModelT]],
) -> Callable[[AsyncSession], UnoRepositoryProtocol[ModelT]]:
    """
    Create a FastAPI dependency for a repository.

    Args:
        repo_class: The repository class to instantiate

    Returns:
        A callable that FastAPI can use as a dependency
    """

    def dependency(
        session: AsyncSession = Depends(get_db_session),
    ) -> UnoRepositoryProtocol[ModelT]:
        # Instantiate the repository with the session
        return repo_class(session)

    dependency.__name__ = f"get_{repo_class.__name__}"
    return dependency


def get_config() -> UnoConfigProtocol:
    """
    FastAPI dependency for configuration.

    Returns:
        A configuration provider
    """
    return get_instance(UnoConfigProtocol)
