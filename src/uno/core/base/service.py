"""
Base service protocols and classes for the Uno framework.

This module defines the core service interfaces and base implementation classes
that form the foundation of the service pattern in the Uno framework.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast

from uno.core.errors.result import Result, Success, Failure
from uno.core.base.error import BaseError

# Type variables
T = TypeVar("T")  # Entity type
ID = TypeVar("ID")  # ID type
InputT = TypeVar("InputT")  # Input type
OutputT = TypeVar("OutputT")  # Output type
ParamsT = TypeVar("ParamsT")  # Parameters type


class ServiceProtocol(Generic[InputT, OutputT]):
    """
    Protocol defining the standard service interface.

    This protocol defines the basic operations that all services must support.
    """

    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.

        Args:
            input_data: The input data for the operation

        Returns:
            A Result containing either the operation result or error information
        """
        ...


class CrudServiceProtocol(Generic[T, ID]):
    """
    Protocol for CRUD services.

    This protocol defines the standard CRUD operations that CRUD services must support.
    """

    async def get(self, id: ID) -> Result[Optional[T]]:
        """
        Get an entity by ID.

        Args:
            id: The entity ID

        Returns:
            Result containing the entity or None if not found
        """
        ...

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Result[List[T]]:
        """
        List entities with optional filtering, ordering, and pagination.

        Args:
            filters: Optional filters to apply
            order_by: Optional ordering
            limit: Maximum number of entities to return
            offset: Number of entities to skip

        Returns:
            Result containing the list of matching entities
        """
        ...

    async def create(self, data: Dict[str, Any]) -> Result[T]:
        """
        Create a new entity.

        Args:
            data: Entity data

        Returns:
            Result containing the created entity
        """
        ...

    async def update(self, id: ID, data: Dict[str, Any]) -> Result[T]:
        """
        Update an existing entity.

        Args:
            id: Entity ID
            data: Updated entity data

        Returns:
            Result containing the updated entity
        """
        ...

    async def delete(self, id: ID) -> Result[bool]:
        """
        Delete an entity.

        Args:
            id: Entity ID

        Returns:
            Result indicating success or failure
        """
        ...


class QueryServiceProtocol(Generic[ParamsT, OutputT]):
    """
    Protocol for query services.

    This protocol defines the operations that query services must support.
    """

    async def execute_query(self, params: ParamsT) -> Result[OutputT]:
        """
        Execute a query operation.

        Args:
            params: Query parameters

        Returns:
            Result containing the query results
        """
        ...

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count entities matching filters.

        Args:
            filters: Optional filters to apply

        Returns:
            Result containing the count
        """
        ...


class BaseService(Generic[InputT, OutputT], ServiceProtocol[InputT, OutputT], ABC):
    """
    Abstract base class for services.

    This class implements the ServiceProtocol and provides a foundation
    for all service implementations.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the service.

        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the service operation.

        This method provides error handling and validation for the service
        operation, delegating to _execute_internal for the actual implementation.

        Args:
            input_data: The input data for the operation

        Returns:
            A Result containing either the operation result or error information
        """
        try:
            # Validate input data
            validation_result = await self.validate(input_data)
            if validation_result is not None:
                return validation_result

            # Execute the operation
            return await self._execute_internal(input_data)

        except BaseError as e:
            # Domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))

        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(
                f"Unexpected error in {self.__class__.__name__}: {str(e)}",
                exc_info=True,
            )
            return Failure(str(e))

    async def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate the input data before execution.

        This method can be overridden by derived classes to implement
        input validation logic. Return None if validation passes,
        or a Failure result if validation fails.

        Args:
            input_data: Input data to validate

        Returns:
            None if validation passes, or a Failure result if validation fails
        """
        return None

    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the service operation.

        This method should be implemented by derived classes to provide
        the specific service operation logic.

        Args:
            input_data: The input data for the operation

        Returns:
            A Result containing either the operation result or error information
        """
        pass


class BaseQueryService(
    Generic[ParamsT, OutputT], QueryServiceProtocol[ParamsT, OutputT], ABC
):
    """
    Base implementation for query services.

    Query services handle read-only operations, retrieving and transforming data
    without modifying domain state.
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the query service.

        Args:
            logger: Optional logger for diagnostic information
        """
        self.logger = logger or logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    async def execute_query(self, params: ParamsT) -> Result[OutputT]:
        """
        Execute a query operation.

        Args:
            params: Query parameters

        Returns:
            Result containing the query results
        """
        try:
            # Execute the query
            return await self._execute_query_internal(params)
        except Exception as e:
            self.logger.error(f"Error executing query: {str(e)}")
            return Failure(str(e))

    @abstractmethod
    async def _execute_query_internal(self, params: ParamsT) -> Result[OutputT]:
        """
        Internal implementation of the query operation.

        This method should be implemented by derived classes to provide
        the specific query logic.

        Args:
            params: Query parameters

        Returns:
            Result containing the query results
        """
        pass

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count entities matching filters.

        Args:
            filters: Optional filters to apply

        Returns:
            Result containing the count
        """
        try:
            # Execute the count query
            return await self._count_internal(filters)
        except Exception as e:
            self.logger.error(f"Error counting entities: {str(e)}")
            return Failure(str(e))

    @abstractmethod
    async def _count_internal(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> Result[int]:
        """
        Internal implementation of the count operation.

        This method should be implemented by derived classes to provide
        the specific count logic.

        Args:
            filters: Optional filters to apply

        Returns:
            Result containing the count
        """
        pass
