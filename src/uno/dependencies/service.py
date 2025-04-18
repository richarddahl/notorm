"""
Base service implementation for Uno framework.

This module provides base service implementations that can be
injected via the DI container. Services encapsulate business logic
and use repositories for data access.
"""

from typing import Dict, List, Optional, TypeVar, Generic, Any, Type
import logging

from uno.domain.base.model import BaseModel
from uno.dependencies.interfaces import UnoRepositoryProtocol, UnoServiceProtocol
from uno.dependencies.repository import UnoRepository


ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T")


class UnoService(UnoServiceProtocol[T], Generic[ModelT, T]):
    """
    Base service implementation for Uno framework.

    Services encapsulate business logic and use repositories for data access.
    """

    def __init__(
        self,
        repository: UnoRepositoryProtocol[ModelT],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the service.

        Args:
            repository: Repository for data access
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

    async def execute(self, *args, **kwargs) -> T:
        """
        Execute the service operation.

        This is a template method that should be overridden by subclasses.

        Args:
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            The result of the service operation
        """
        raise NotImplementedError("Subclasses must implement execute()")


class CrudService(Generic[ModelT]):
    """
    Generic CRUD service implementation.

    Provides standard CRUD operations using a repository.
    """

    def __init__(
        self,
        repository: UnoRepositoryProtocol[ModelT],
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the CRUD service.

        Args:
            repository: Repository for data access
            logger: Optional logger instance
        """
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)

    async def get(self, id: str) -> Optional[ModelT]:
        """
        Get a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            The model instance if found, None otherwise
        """
        return await self.repository.get(id)

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
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
        return await self.repository.list(filters, limit, offset)

    async def create(self, data: Dict[str, Any]) -> ModelT:
        """
        Create a new model instance.

        Args:
            data: Dictionary of field name to value pairs

        Returns:
            The created model instance
        """
        return await self.repository.create(data)

    async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelT]:
        """
        Update an existing model by ID.

        Args:
            id: The unique identifier of the model
            data: Dictionary of field name to value pairs to update

        Returns:
            The updated model instance if found, None otherwise
        """
        return await self.repository.update(id, data)

    async def delete(self, id: str) -> bool:
        """
        Delete a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            True if the model was deleted, False if it wasn't found
        """
        return await self.repository.delete(id)
