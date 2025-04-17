"""
Domain repositories for the Values module.

This module contains domain repositories for value entities, providing data access
abstraction for the domain services layer following the domain-driven design pattern.
"""

from typing import List, Optional, Any, Dict, Generic, TypeVar, cast, Type
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result, Success, Failure
from uno.domain.repository import Repository, UnoDBRepository
from uno.database.db_manager import DBManager
from uno.values.entities import (
    BaseValue,
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)

T = TypeVar("T", bound=BaseValue)


class ValueRepositoryError(Exception):
    """Base error class for value repository errors."""

    pass


class ValueRepository(Repository[T]):
    """
    Base repository interface for value entities.

    This abstract class defines the contract for repositories handling value entities,
    with appropriate type safety through generics.
    """

    async def find_by_name(self, name: str) -> Optional[T]:
        """
        Find a value entity by name.

        Args:
            name: The name to search for

        Returns:
            The entity if found, None otherwise
        """
        pass

    async def find_by_value(self, value: Any) -> Optional[T]:
        """
        Find a value entity by its value field.

        Args:
            value: The value to search for

        Returns:
            The entity if found, None otherwise
        """
        pass

    async def search(self, search_term: str, limit: int = 20) -> List[T]:
        """
        Search for value entities matching a term.

        Args:
            search_term: The search term
            limit: Maximum number of results to return

        Returns:
            List of matching entities
        """
        pass


class UnoDBValueRepository(UnoDBRepository[T], ValueRepository[T]):
    """
    Repository implementation for value entities using UnoDBRepository.

    This implementation provides data access for value entities using the database layer,
    following the domain repository pattern.
    """

    def __init__(
        self,
        entity_type: Type[T],
        db_manager: DBManager,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the repository.

        Args:
            entity_type: The type of value entity this repository manages
            db_manager: Database manager instance
            logger: Optional logger
        """
        super().__init__(entity_type)
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def find_by_name(self, name: str) -> Optional[T]:
        """
        Find a value entity by name.

        Args:
            name: The name to search for

        Returns:
            The entity if found, None otherwise
        """
        try:
            results = await self.list(filters={"name": name}, limit=1)
            return results[0] if results else None
        except Exception as e:
            self.logger.error(f"Error finding {self.entity_type.__name__} by name: {e}")
            return None

    async def find_by_value(self, value: Any) -> Optional[T]:
        """
        Find a value entity by its value field.

        Args:
            value: The value to search for

        Returns:
            The entity if found, None otherwise
        """
        try:
            results = await self.list(filters={"value": value}, limit=1)
            return results[0] if results else None
        except Exception as e:
            self.logger.error(
                f"Error finding {self.entity_type.__name__} by value: {e}"
            )
            return None

    async def search(self, search_term: str, limit: int = 20) -> List[T]:
        """
        Search for value entities matching a term.

        Args:
            search_term: The search term
            limit: Maximum number of results to return

        Returns:
            List of matching entities
        """
        try:
            # For text-based values, search by name or value
            if self.entity_type == TextValue:
                filters = {
                    "or": [
                        {"name": {"lookup": "ilike", "val": f"%{search_term}%"}},
                        {"value": {"lookup": "ilike", "val": f"%{search_term}%"}},
                    ]
                }
            else:
                # For other value types, search by name only
                filters = {"name": {"lookup": "ilike", "val": f"%{search_term}%"}}

            return await self.list(filters=filters, limit=limit)
        except Exception as e:
            self.logger.error(f"Error searching {self.entity_type.__name__}: {e}")
            return []

    async def find_by_file_path(self, file_path: str) -> Optional[Attachment]:
        """
        Find an attachment by file path.

        This method is specific to the Attachment repository.

        Args:
            file_path: The file path to search for

        Returns:
            The attachment if found, None otherwise
        """
        if self.entity_type != Attachment:
            raise ValueError(
                "This method is only available for the Attachment repository"
            )

        try:
            results = await self.list(filters={"file_path": file_path}, limit=1)
            return cast(Optional[Attachment], results[0] if results else None)
        except Exception as e:
            self.logger.error(f"Error finding Attachment by file path: {e}")
            return None


# Concrete repository implementations


class AttachmentRepository(UnoDBValueRepository[Attachment]):
    """Repository for Attachment entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(Attachment, db_manager, logger)


class BooleanValueRepository(UnoDBValueRepository[BooleanValue]):
    """Repository for BooleanValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(BooleanValue, db_manager, logger)


class DateTimeValueRepository(UnoDBValueRepository[DateTimeValue]):
    """Repository for DateTimeValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DateTimeValue, db_manager, logger)


class DateValueRepository(UnoDBValueRepository[DateValue]):
    """Repository for DateValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DateValue, db_manager, logger)


class DecimalValueRepository(UnoDBValueRepository[DecimalValue]):
    """Repository for DecimalValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DecimalValue, db_manager, logger)


class IntegerValueRepository(UnoDBValueRepository[IntegerValue]):
    """Repository for IntegerValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(IntegerValue, db_manager, logger)


class TextValueRepository(UnoDBValueRepository[TextValue]):
    """Repository for TextValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(TextValue, db_manager, logger)


class TimeValueRepository(UnoDBValueRepository[TimeValue]):
    """Repository for TimeValue entities."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(TimeValue, db_manager, logger)
