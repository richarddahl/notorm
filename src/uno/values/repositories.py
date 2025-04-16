# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Repository implementations for the values module.

This module provides database access and query functionality for different
value types, implementing the interfaces defined in interfaces.py.
"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union, cast
import logging
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result, Success, Failure
from uno.database.repository import UnoBaseRepository
from uno.database.db_manager import DBManager
from uno.values.models import (
    AttachmentModel,
    BooleanValueModel,
    DateTimeValueModel,
    DateValueModel,
    DecimalValueModel,
    IntegerValueModel,
    TextValueModel,
    TimeValueModel,
)
from uno.values.interfaces import ValueRepositoryProtocol


T = TypeVar("T")
M = TypeVar("M")


class ValueRepositoryError(Exception):
    """Base error class for value repository errors."""

    pass


class ValueRepository(UnoBaseRepository, Generic[T, M], ValueRepositoryProtocol[T]):
    """Generic repository for value operations."""

    def __init__(
        self,
        value_class: Type[T],
        model_class: Type[M],
        db_manager: DBManager,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the value repository.

        Args:
            value_class: The value object class
            model_class: The value model class
            db_manager: Database manager instance
            logger: Optional logger
        """
        super().__init__(value_class, db_manager)
        self.value_class = value_class
        self.model_class = model_class
        self.logger = logger or logging.getLogger(__name__)

    async def get_by_id(
        self, value_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[T]]:
        """
        Get a value by ID.

        Args:
            value_id: The ID of the value to get
            session: Optional database session

        Returns:
            Result containing the value or None if not found
        """
        try:
            query = select(self.model_class).where(self.model_class.id == value_id)

            result = await self._execute_query(query, session)

            if not result:
                return Success(None)

            return Success(self.value_class(**result.dict()))

        except Exception as e:
            self.logger.error(
                f"Error getting {self.value_class.__name__} by ID {value_id}: {e}"
            )
            return Failure(
                ValueRepositoryError(
                    f"Error getting {self.value_class.__name__}: {str(e)}"
                )
            )

    async def get_by_value(
        self, value: Any, session: Optional[AsyncSession] = None
    ) -> Result[Optional[T]]:
        """
        Get a value object by its actual value.

        Args:
            value: The actual value to look up
            session: Optional database session

        Returns:
            Result containing the value object or None if not found
        """
        try:
            query = select(self.model_class).where(self.model_class.value == value)

            result = await self._execute_query(query, session)

            if not result:
                return Success(None)

            return Success(self.value_class(**result.dict()))

        except Exception as e:
            self.logger.error(
                f"Error getting {self.value_class.__name__} by value {value}: {e}"
            )
            return Failure(
                ValueRepositoryError(
                    f"Error getting {self.value_class.__name__}: {str(e)}"
                )
            )

    async def create(
        self, value_obj: T, session: Optional[AsyncSession] = None
    ) -> Result[T]:
        """
        Create a new value.

        Args:
            value_obj: The value object to create
            session: Optional database session

        Returns:
            Result containing the created value
        """
        try:
            # Create model instance from value object
            model = self.model_class(**value_obj.dict(exclude_unset=True))

            if session is None:
                async with self.db_manager.get_enhanced_session() as session:
                    session.add(model)
                    await session.commit()
            else:
                session.add(model)
                await session.flush()

            # Return the value object with generated ID
            value_obj_dict = value_obj.dict()
            value_obj_dict["id"] = model.id

            return Success(self.value_class(**value_obj_dict))

        except Exception as e:
            self.logger.error(f"Error creating {self.value_class.__name__}: {e}")
            return Failure(
                ValueRepositoryError(
                    f"Error creating {self.value_class.__name__}: {str(e)}"
                )
            )

    async def update(
        self, value_obj: T, session: Optional[AsyncSession] = None
    ) -> Result[T]:
        """
        Update an existing value.

        Args:
            value_obj: The value object to update
            session: Optional database session

        Returns:
            Result containing the updated value
        """
        try:
            # Ensure value exists
            value_id = getattr(value_obj, "id")

            if not value_id:
                return Failure(
                    ValueRepositoryError(
                        f"Cannot update {self.value_class.__name__} without ID"
                    )
                )

            # Check if value exists
            existing_result = await self.get_by_id(value_id, session)

            if existing_result.is_failure:
                return Failure(
                    ValueRepositoryError(
                        f"Error updating {self.value_class.__name__}: {existing_result.error}"
                    )
                )

            existing = existing_result.value

            if not existing:
                return Failure(
                    ValueRepositoryError(
                        f"{self.value_class.__name__} with ID {value_id} not found"
                    )
                )

            # Update value fields
            update_data = value_obj.dict(
                exclude={"id"}, exclude_unset=True, exclude_none=True
            )

            if session is None:
                async with self.db_manager.get_enhanced_session() as session:
                    result = await session.execute(
                        select(self.model_class).where(self.model_class.id == value_id)
                    )
                    model = result.scalars().first()

                    if not model:
                        return Failure(
                            ValueRepositoryError(
                                f"{self.value_class.__name__} with ID {value_id} not found"
                            )
                        )

                    # Update model fields
                    for field, value in update_data.items():
                        setattr(model, field, value)

                    await session.commit()
            else:
                result = await session.execute(
                    select(self.model_class).where(self.model_class.id == value_id)
                )
                model = result.scalars().first()

                if not model:
                    return Failure(
                        ValueRepositoryError(
                            f"{self.value_class.__name__} with ID {value_id} not found"
                        )
                    )

                # Update model fields
                for field, value in update_data.items():
                    setattr(model, field, value)

                await session.flush()

            # Return updated value
            return await self.get_by_id(value_id, session)

        except Exception as e:
            self.logger.error(
                f"Error updating {self.value_class.__name__} {getattr(value_obj, 'id', 'unknown')}: {e}"
            )
            return Failure(
                ValueRepositoryError(
                    f"Error updating {self.value_class.__name__}: {str(e)}"
                )
            )

    async def delete(
        self, value_id: str, session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """
        Delete a value by ID.

        Args:
            value_id: The ID of the value to delete
            session: Optional database session

        Returns:
            Result containing True if successful
        """
        try:
            if session is None:
                async with self.db_manager.get_enhanced_session() as session:
                    result = await session.execute(
                        select(self.model_class).where(self.model_class.id == value_id)
                    )
                    model = result.scalars().first()

                    if not model:
                        return Success(False)

                    await session.delete(model)
                    await session.commit()
            else:
                result = await session.execute(
                    select(self.model_class).where(self.model_class.id == value_id)
                )
                model = result.scalars().first()

                if not model:
                    return Success(False)

                await session.delete(model)
                await session.flush()

            return Success(True)

        except Exception as e:
            self.logger.error(
                f"Error deleting {self.value_class.__name__} {value_id}: {e}"
            )
            return Failure(
                ValueRepositoryError(
                    f"Error deleting {self.value_class.__name__}: {str(e)}"
                )
            )

    async def bulk_create(
        self, value_objs: List[T], session: Optional[AsyncSession] = None
    ) -> Result[List[T]]:
        """
        Create multiple values in a single operation.

        Args:
            value_objs: List of value objects to create
            session: Optional database session

        Returns:
            Result containing the created values
        """
        try:
            # Create model instances from value objects
            models = [
                self.model_class(**obj.dict(exclude_unset=True)) for obj in value_objs
            ]

            if session is None:
                async with self.db_manager.get_enhanced_session() as session:
                    session.add_all(models)
                    await session.commit()
            else:
                session.add_all(models)
                await session.flush()

            # Return value objects with generated IDs
            created_values = []
            for i, model in enumerate(models):
                value_obj_dict = value_objs[i].dict()
                value_obj_dict["id"] = model.id
                created_values.append(self.value_class(**value_obj_dict))

            return Success(created_values)

        except Exception as e:
            self.logger.error(f"Error bulk creating {self.value_class.__name__}s: {e}")
            return Failure(
                ValueRepositoryError(
                    f"Error bulk creating {self.value_class.__name__}s: {str(e)}"
                )
            )

    async def search(
        self, search_term: str, limit: int = 20, session: Optional[AsyncSession] = None
    ) -> Result[List[T]]:
        """
        Search for values matching a term.

        Args:
            search_term: The search term
            limit: Maximum number of results to return
            session: Optional database session

        Returns:
            Result containing matching values
        """
        try:
            # Implement type-specific search logic
            if hasattr(self.model_class, "value") and hasattr(self.model_class, "name"):
                # For string-based values, search in value and name
                if self.model_class == TextValueModel:
                    query = (
                        select(self.model_class)
                        .where(
                            or_(
                                self.model_class.value.ilike(f"%{search_term}%"),
                                self.model_class.name.ilike(f"%{search_term}%"),
                            )
                        )
                        .limit(limit)
                    )
                elif self.model_class == AttachmentModel:
                    query = (
                        select(self.model_class)
                        .where(self.model_class.name.ilike(f"%{search_term}%"))
                        .limit(limit)
                    )
                else:
                    # For other value types, search by name only
                    query = (
                        select(self.model_class)
                        .where(self.model_class.name.ilike(f"%{search_term}%"))
                        .limit(limit)
                    )
            else:
                # Fallback to basic ID search if no searchable fields
                query = (
                    select(self.model_class)
                    .where(self.model_class.id.ilike(f"%{search_term}%"))
                    .limit(limit)
                )

            results = await self._execute_query_many(query, session)

            return Success([self.value_class(**result.dict()) for result in results])

        except Exception as e:
            self.logger.error(f"Error searching {self.value_class.__name__}s: {e}")
            return Failure(
                ValueRepositoryError(
                    f"Error searching {self.value_class.__name__}s: {str(e)}"
                )
            )


# Specialized repository implementations for each value type


class BooleanValueRepository(ValueRepository[BooleanValue, BooleanValueModel]):
    """Repository for boolean values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(BooleanValue, BooleanValueModel, db_manager, logger)


class TextValueRepository(ValueRepository[TextValue, TextValueModel]):
    """Repository for text values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(TextValue, TextValueModel, db_manager, logger)


class IntegerValueRepository(ValueRepository[IntegerValue, IntegerValueModel]):
    """Repository for integer values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(IntegerValue, IntegerValueModel, db_manager, logger)


class DecimalValueRepository(ValueRepository[DecimalValue, DecimalValueModel]):
    """Repository for decimal values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DecimalValue, DecimalValueModel, db_manager, logger)


class DateValueRepository(ValueRepository[DateValue, DateValueModel]):
    """Repository for date values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DateValue, DateValueModel, db_manager, logger)


class DateTimeValueRepository(ValueRepository[DateTimeValue, DateTimeValueModel]):
    """Repository for datetime values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(DateTimeValue, DateTimeValueModel, db_manager, logger)


class TimeValueRepository(ValueRepository[TimeValue, TimeValueModel]):
    """Repository for time values."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(TimeValue, TimeValueModel, db_manager, logger)


class AttachmentRepository(ValueRepository[Attachment, AttachmentModel]):
    """Repository for file attachments."""

    def __init__(self, db_manager: DBManager, logger: Optional[logging.Logger] = None):
        super().__init__(Attachment, AttachmentModel, db_manager, logger)
