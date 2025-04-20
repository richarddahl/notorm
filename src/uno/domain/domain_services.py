"""
Domain services for the Values module.

This module provides domain services that implement business logic for values entities,
coordinating entity validation and persistence through repositories.
"""

from typing import Any, TypeVar, Generic, cast

from uno.core.errors.result import Result
from uno.domain.service import UnoEntityService
from uno.values.entities import (
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
    BaseValue,
)

# Type variables
T = TypeVar("T", bound=BaseValue)


class ValueServiceError(Exception):
    """Base error class for value service errors."""

    pass


class ValueService(UnoEntityService[T], Generic[T]):
    """
    Base service for value entities.

    This class provides common methods for all value services,
    with appropriate type safety through generics.
    """

    async def find_by_name(self, name: str) -> Result[T | None, str]:
        """
        Find a value entity by name.

        Args:
            name: The name to search for

        Returns:
            Result containing the entity if found, None otherwise
        """
        try:
            repository = cast(Any, self.repository)  # Cast to access find_by_name
            result = await repository.find_by_name(name)
            return Result.success(result, convert=True)
        except Exception as e:
            self.logger.error(f"Error finding {self.entity_type.__name__} by name: {e}")
            return Result.failure(
                ValueServiceError(
                    f"Error finding {self.entity_type.__name__} by name: {str(e)}"
                ),
                convert=True,
            )

    async def find_by_value(self, value: Any) -> Result[T | None, str]:
        """
        Find a value entity by its value field.

        Args:
            value: The value to search for

        Returns:
            Result containing the entity if found, None otherwise
        """
        try:
            repository = cast(Any, self.repository)  # Cast to access find_by_value
            result = await repository.find_by_value(value)
            return Result.success(result, convert=True)
        except Exception as e:
            self.logger.error(
                f"Error finding {self.entity_type.__name__} by value: {e}"
            )
            return Result.failure(
                ValueServiceError(
                    f"Error finding {self.entity_type.__name__} by value: {str(e)}"
                ),
                convert=True,
            )

    async def search(self, search_term: str, limit: int = 20) -> Result[list[T], str]:
        """
        Search for value entities matching a term.

        Args:
            search_term: The search term
            limit: Maximum number of results to return

        Returns:
            Result containing matching entities
        """
        try:
            # Repository doesn't have search directly, so implement it here
            # For text-based values, search by name or value
            if hasattr(self.entity_type, "value") and isinstance(
                self.entity_type.value, str
            ):
                filters = {
                    "or": [
                        {"name": {"lookup": "ilike", "val": f"%{search_term}%"}},
                        {"value": {"lookup": "ilike", "val": f"%{search_term}%"}},
                    ]
                }
            else:
                # For other value types, search by name only
                filters = {"name": {"lookup": "ilike", "val": f"%{search_term}%"}}

            results = await self.repository.list(filters=filters, limit=limit)
            return Result.success(results, convert=True)
        except Exception as e:
            self.logger.error(f"Error searching {self.entity_type.__name__}: {e}")
            return Result.failure(
                ValueServiceError(
                    f"Error searching {self.entity_type.__name__}: {str(e)}"
                ),
                convert=True,
            )


# Concrete service implementations


class AttachmentService(ValueService[Attachment]):
    """Service for Attachment entities."""

    async def find_by_file_path(self, file_path: str) -> Result[Attachment | None, str]:
        """
        Find an attachment by file path.

        Args:
            file_path: The file path to search for

        Returns:
            Result containing the attachment if found, None otherwise
        """
        try:
            repository = cast(Any, self.repository)  # Cast to access find_by_file_path
            result = await repository.find_by_file_path(file_path)
            return Result.success(result, convert=True)
        except Exception as e:
            self.logger.error(f"Error finding Attachment by file path: {e}")
            return Result.failure(
                ValueServiceError(f"Error finding Attachment by file path: {str(e)}"),
                convert=True,
            )


class BooleanValueService(ValueService[BooleanValue]):
    """Service for BooleanValue entities."""

    pass


class DateTimeValueService(ValueService[DateTimeValue]):
    """Service for DateTimeValue entities."""

    pass


class DateValueService(ValueService[DateValue]):
    """Service for DateValue entities."""

    pass


class DecimalValueService(ValueService[DecimalValue]):
    """Service for DecimalValue entities."""

    pass


class IntegerValueService(ValueService[IntegerValue]):
    """Service for IntegerValue entities."""

    pass


class TextValueService(ValueService[TextValue]):
    """Service for TextValue entities."""

    pass


class TimeValueService(ValueService[TimeValue]):
    """Service for TimeValue entities."""

    pass
