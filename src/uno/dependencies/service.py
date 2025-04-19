"""
Base service implementation for dependency injection in the Uno framework.

This module provides service implementations that integrate with the
dependency injection system, while following the standardized service pattern.
"""

from typing import Dict, List, Optional, TypeVar, Generic, Any, Type, cast
import logging

from uno.domain.base.model import ModelBase
from uno.core.base.service import BaseService as CoreBaseService, ServiceProtocol
from uno.core.base.error import BaseError
from uno.core.errors.result import Result, Success, Failure
from uno.dependencies.interfaces import UnoRepositoryProtocol

# Type variables
ModelT = TypeVar("ModelT", bound=BaseModel)
T = TypeVar("T")
InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class BaseService(CoreBaseService[Dict[str, Any], T], Generic[ModelT, T]):
    """
    DI-compatible service implementation that extends the core BaseService.

    This service follows the standardized service pattern while providing
    compatibility with the dependency injection system.
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
        super().__init__(logger)
        self.repository = repository

    # Note: The execute method is inherited from CoreBaseService
    # and automatically provides error handling

    async def _execute_internal(self, input_data: Dict[str, Any]) -> Result[T]:
        """
        Internal implementation of the service operation.

        This method must be overridden by subclasses to provide specific
        service operation logic.

        Args:
            input_data: Dictionary of parameters for the operation

        Returns:
            Result containing the operation output
        """
        raise NotImplementedError("Subclasses must implement _execute_internal()")


class CrudService(Generic[ModelT]):
    """
    Generic CRUD service implementation that uses the Result pattern.

    Provides standardized CRUD operations using a repository.
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

    async def get(self, id: str) -> Result[Optional[ModelT]]:
        """
        Get a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            Result containing the model instance if found, None otherwise
        """
        try:
            result = await self.repository.get(id)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error getting entity: {str(e)}")
            return Failure(str(e))

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[List[ModelT]]:
        """
        List models with optional filtering and pagination.

        Args:
            filters: Dictionary of field name to value pairs for filtering
            limit: Maximum number of results to return
            offset: Number of results to skip

        Returns:
            Result containing list of model instances
        """
        try:
            result = await self.repository.list(filters, limit, offset)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error listing entities: {str(e)}")
            return Failure(str(e))

    async def create(self, data: Dict[str, Any]) -> Result[ModelT]:
        """
        Create a new model instance.

        Args:
            data: Dictionary of field name to value pairs

        Returns:
            Result containing the created model instance
        """
        try:
            result = await self.repository.create(data)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error creating entity: {str(e)}")
            return Failure(str(e))

    async def update(self, id: str, data: Dict[str, Any]) -> Result[Optional[ModelT]]:
        """
        Update an existing model by ID.

        Args:
            id: The unique identifier of the model
            data: Dictionary of field name to value pairs to update

        Returns:
            Result containing the updated model instance if found, None otherwise
        """
        try:
            result = await self.repository.update(id, data)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error updating entity: {str(e)}")
            return Failure(str(e))

    async def delete(self, id: str) -> Result[bool]:
        """
        Delete a model by ID.

        Args:
            id: The unique identifier of the model

        Returns:
            Result containing True if the model was deleted, False otherwise
        """
        try:
            result = await self.repository.delete(id)
            return Success(result)
        except BaseError as e:
            return Failure(str(e), error_code=getattr(e, "error_code", None))
        except Exception as e:
            self.logger.error(f"Error deleting entity: {str(e)}")
            return Failure(str(e))
