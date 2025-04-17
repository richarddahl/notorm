"""
Repository result classes.

This module provides result classes for repository operations.
"""

from typing import Generic, TypeVar, Optional, List, Any

T = TypeVar("T")


class RepositoryResult(Generic[T]):
    """Result of a repository operation."""

    def __init__(
        self,
        is_success: bool,
        entity: Optional[T] = None,
        error: Optional[Exception] = None,
        message: Optional[str] = None,
    ):
        """
        Initialize the repository result.

        Args:
            is_success: Whether the operation was successful
            entity: The entity involved in the operation
            error: Any error that occurred
            message: A message describing the result
        """
        self.is_success = is_success
        self.entity = entity
        self.error = error
        self.message = message or (str(error) if error else None)

    @property
    def is_failure(self) -> bool:
        """
        Check if the operation failed.

        Returns:
            True if the operation failed, False otherwise
        """
        return not self.is_success

    @classmethod
    def success(cls, entity: T, message: Optional[str] = None) -> "RepositoryResult[T]":
        """
        Create a successful repository result.

        Args:
            entity: The entity involved in the operation
            message: A message describing the result

        Returns:
            A successful repository result
        """
        return cls(is_success=True, entity=entity, message=message)

    @classmethod
    def failure(
        cls, error: Exception, message: Optional[str] = None
    ) -> "RepositoryResult[T]":
        """
        Create a failed repository result.

        Args:
            error: The error that caused the failure
            message: A message describing the result

        Returns:
            A failed repository result
        """
        return cls(is_success=False, error=error, message=message or str(error))


class GetResult(Generic[T]):
    """Result of a repository get operation."""

    def __init__(
        self,
        is_success: bool,
        value: Optional[T] = None,
        error: Optional[Exception] = None,
        message: Optional[str] = None,
    ):
        """
        Initialize the get result.

        Args:
            is_success: Whether the operation was successful
            value: The value retrieved
            error: Any error that occurred
            message: A message describing the result
        """
        self.is_success = is_success
        self.value = value
        self.error = error
        self.message = message or (str(error) if error else None)

    @property
    def is_failure(self) -> bool:
        """
        Check if the operation failed.

        Returns:
            True if the operation failed, False otherwise
        """
        return not self.is_success

    @classmethod
    def success(cls, value: T, message: Optional[str] = None) -> "GetResult[T]":
        """
        Create a successful get result.

        Args:
            value: The value retrieved
            message: A message describing the result

        Returns:
            A successful get result
        """
        return cls(is_success=True, value=value, message=message)

    @classmethod
    def failure(cls, error: Exception, message: Optional[str] = None) -> "GetResult[T]":
        """
        Create a failed get result.

        Args:
            error: The error that caused the failure
            message: A message describing the result

        Returns:
            A failed get result
        """
        return cls(is_success=False, error=error, message=message or str(error))

    @classmethod
    def not_found(cls, message: str = "Entity not found") -> "GetResult[T]":
        """
        Create a not found result.

        Args:
            message: A message describing the result

        Returns:
            A not found result
        """
        return cls(is_success=False, error=Exception(message), message=message)
