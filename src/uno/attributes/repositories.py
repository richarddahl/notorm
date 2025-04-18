# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Repository implementations for the attributes module.

This module provides database access and query functionality for attributes
and attribute types, implementing the interfaces defined in interfaces.py.
"""

from typing import List, Optional, Type, cast
import logging
from sqlalchemy import select, and_, or_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from uno.core.errors.result import Result, Success, Failure
from uno.database.repository import UnoBaseRepository as BaseRepository
from uno.database.db_manager import DBManager
from uno.attributes.models import AttributeModel, AttributeTypeModel
from uno.attributes.interfaces import (
    AttributeRepositoryProtocol,
    AttributeTypeRepositoryProtocol,
)


class AttributeRepositoryError(Exception):
    """Base error class for attribute repository errors."""

    pass


class AttributeRepository(BaseRepository, AttributeRepositoryProtocol):
    """
    Repository implementation for attributes.

    This class provides database access methods for AttributeModel entities,
    implementing the AttributeRepositoryProtocol interface.
    """

    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the attribute repository.

        Args:
            db_manager: Optional database manager. If not provided, a new instance is created.
            logger: Optional logger. If not provided, a new logger is created.
        """
        super().__init__(model_class=AttributeModel, db_manager=db_manager)
        self.logger = logger or logging.getLogger(__name__)

    async def get_by_id(
        self, attribute_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[Attribute]]:
        """
        Get an attribute by ID.

        Args:
            attribute_id: The ID of the attribute to get
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the attribute, None if not found, or an error
        """
        try:
            query = (
                select(AttributeModel)
                .where(AttributeModel.id == attribute_id)
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            result = await self._execute_query(query, session)

            if not result:
                return Success(None)

            return Success(Attribute(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error getting attribute by ID {attribute_id}: {e}")
            return Failure(
                AttributeRepositoryError(f"Error getting attribute by ID: {str(e)}")
            )

    async def get_by_type(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """
        Get attributes by attribute type ID.

        Args:
            attribute_type_id: The ID of the attribute type
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing a list of attributes or an error
        """
        try:
            query = (
                select(AttributeModel)
                .where(AttributeModel.attribute_type_id == attribute_type_id)
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            results = await self._execute_query_many(query, session)

            attributes = [Attribute(**result.dict()) for result in results]

            return Success(attributes)

        except Exception as e:
            self.logger.error(
                f"Error getting attributes by type {attribute_type_id}: {e}"
            )
            return Failure(
                AttributeRepositoryError(f"Error getting attributes by type: {str(e)}")
            )

    async def get_by_meta_record(
        self, meta_record_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """
        Get attributes associated with a meta record.

        Args:
            meta_record_id: The ID of the meta record
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing a list of attributes or an error
        """
        try:
            # We need a more complex query to get attributes by meta record
            # since we're dealing with a many-to-many relationship
            query = (
                select(AttributeModel)
                .join(AttributeModel.meta_records)
                .where(AttributeModel.meta_records.any(id=meta_record_id))
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            results = await self._execute_query_many(query, session)

            attributes = [Attribute(**result.dict()) for result in results]

            return Success(attributes)

        except Exception as e:
            self.logger.error(
                f"Error getting attributes by meta record {meta_record_id}: {e}"
            )
            return Failure(
                AttributeRepositoryError(
                    f"Error getting attributes by meta record: {str(e)}"
                )
            )

    async def create(
        self, attribute: Attribute, session: Optional[AsyncSession] = None
    ) -> Result[Attribute]:
        """
        Create a new attribute.

        Args:
            attribute: The attribute to create
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the created attribute or an error
        """
        try:
            # Convert to model
            model = AttributeModel(
                **attribute.model_dump(
                    exclude={"attribute_type", "values", "meta_records"}
                )
            )

            # Save to database
            result = await self._save(model, session)

            # Reload to get all relationships
            query = (
                select(AttributeModel)
                .where(AttributeModel.id == result.id)
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            result = await self._execute_query(query, session)

            return Success(Attribute(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error creating attribute: {e}")
            return Failure(
                AttributeRepositoryError(f"Error creating attribute: {str(e)}")
            )

    async def update(
        self, attribute: Attribute, session: Optional[AsyncSession] = None
    ) -> Result[Attribute]:
        """
        Update an existing attribute.

        Args:
            attribute: The attribute to update
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the updated attribute or an error
        """
        try:
            # Check if the attribute exists
            existing_result = await self.get_by_id(attribute.id, session)

            if existing_result.is_failure:
                return existing_result

            if existing_result.value is None:
                return Failure(
                    AttributeRepositoryError(
                        f"Attribute with ID {attribute.id} not found"
                    )
                )

            # Convert to model
            model = AttributeModel(
                **attribute.model_dump(
                    exclude={"attribute_type", "values", "meta_records"}
                )
            )

            # Save to database
            result = await self._save(model, session)

            # Reload to get all relationships
            query = (
                select(AttributeModel)
                .where(AttributeModel.id == result.id)
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            result = await self._execute_query(query, session)

            return Success(Attribute(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error updating attribute: {e}")
            return Failure(
                AttributeRepositoryError(f"Error updating attribute: {str(e)}")
            )

    async def delete(
        self, attribute_id: str, session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """
        Delete an attribute by ID.

        Args:
            attribute_id: The ID of the attribute to delete
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing True if successful, or an error
        """
        try:
            # Check if the attribute exists
            existing_result = await self.get_by_id(attribute_id, session)

            if existing_result.is_failure:
                return existing_result

            if existing_result.value is None:
                return Failure(
                    AttributeRepositoryError(
                        f"Attribute with ID {attribute_id} not found"
                    )
                )

            # Delete from database
            result = await self._delete(attribute_id, session)

            return Success(result)

        except Exception as e:
            self.logger.error(f"Error deleting attribute: {e}")
            return Failure(
                AttributeRepositoryError(f"Error deleting attribute: {str(e)}")
            )

    async def bulk_create(
        self, attributes: List[Attribute], session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """
        Create multiple attributes in a single operation.

        Args:
            attributes: The attributes to create
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the created attributes or an error
        """
        try:
            # Convert to models
            models = [
                AttributeModel(
                    **attr.model_dump(
                        exclude={"attribute_type", "values", "meta_records"}
                    )
                )
                for attr in attributes
            ]

            # Save to database
            results = await self._bulk_save(models, session)

            # Reload to get all relationships
            ids = [result.id for result in results]

            query = (
                select(AttributeModel)
                .where(AttributeModel.id.in_(ids))
                .options(
                    joinedload(AttributeModel.attribute_type),
                    selectinload(AttributeModel.values),
                    selectinload(AttributeModel.meta_records),
                )
            )

            results = await self._execute_query_many(query, session)

            created_attributes = [Attribute(**result.dict()) for result in results]

            return Success(created_attributes)

        except Exception as e:
            self.logger.error(f"Error bulk creating attributes: {e}")
            return Failure(
                AttributeRepositoryError(f"Error bulk creating attributes: {str(e)}")
            )


class AttributeTypeRepository(BaseRepository, AttributeTypeRepositoryProtocol):
    """
    Repository implementation for attribute types.

    This class provides database access methods for AttributeTypeModel entities,
    implementing the AttributeTypeRepositoryProtocol interface.
    """

    def __init__(
        self,
        db_manager: Optional[DBManager] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the attribute type repository.

        Args:
            db_manager: Optional database manager. If not provided, a new instance is created.
            logger: Optional logger. If not provided, a new logger is created.
        """
        super().__init__(model_class=AttributeTypeModel, db_manager=db_manager)
        self.logger = logger or logging.getLogger(__name__)

    async def get_by_id(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[AttributeType]]:
        """
        Get an attribute type by ID.

        Args:
            attribute_type_id: The ID of the attribute type to get
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the attribute type, None if not found, or an error
        """
        try:
            query = (
                select(AttributeTypeModel)
                .where(AttributeTypeModel.id == attribute_type_id)
                .options(
                    selectinload(AttributeTypeModel.applicable_meta_types),
                    selectinload(AttributeTypeModel.value_meta_types),
                )
            )

            result = await self._execute_query(query, session)

            if not result:
                return Success(None)

            return Success(AttributeType(**result.dict()))

        except Exception as e:
            self.logger.error(
                f"Error getting attribute type by ID {attribute_type_id}: {e}"
            )
            return Failure(
                AttributeRepositoryError(
                    f"Error getting attribute type by ID: {str(e)}"
                )
            )

    async def get_by_name(
        self, name: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[AttributeType]]:
        """
        Get an attribute type by name.

        Args:
            name: The name of the attribute type to get
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the attribute type, None if not found, or an error
        """
        try:
            query = (
                select(AttributeTypeModel)
                .where(AttributeTypeModel.name == name)
                .options(
                    selectinload(AttributeTypeModel.applicable_meta_types),
                    selectinload(AttributeTypeModel.value_meta_types),
                )
            )

            result = await self._execute_query(query, session)

            if not result:
                return Success(None)

            return Success(AttributeType(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error getting attribute type by name {name}: {e}")
            return Failure(
                AttributeRepositoryError(
                    f"Error getting attribute type by name: {str(e)}"
                )
            )

    async def get_by_meta_type(
        self, meta_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[AttributeType]]:
        """
        Get attribute types applicable to a meta type.

        Args:
            meta_type_id: The ID of the meta type
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing a list of attribute types or an error
        """
        try:
            # We need a more complex query to get attribute types by meta type
            # since we're dealing with a many-to-many relationship
            query = (
                select(AttributeTypeModel)
                .join(AttributeTypeModel.applicable_meta_types)
                .where(AttributeTypeModel.applicable_meta_types.any(id=meta_type_id))
                .options(
                    selectinload(AttributeTypeModel.applicable_meta_types),
                    selectinload(AttributeTypeModel.value_meta_types),
                )
            )

            results = await self._execute_query_many(query, session)

            attribute_types = [AttributeType(**result.dict()) for result in results]

            return Success(attribute_types)

        except Exception as e:
            self.logger.error(
                f"Error getting attribute types by meta type {meta_type_id}: {e}"
            )
            return Failure(
                AttributeRepositoryError(
                    f"Error getting attribute types by meta type: {str(e)}"
                )
            )

    async def create(
        self, attribute_type: AttributeType, session: Optional[AsyncSession] = None
    ) -> Result[AttributeType]:
        """
        Create a new attribute type.

        Args:
            attribute_type: The attribute type to create
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the created attribute type or an error
        """
        try:
            # Convert to model
            model = AttributeTypeModel(
                **attribute_type.model_dump(
                    exclude={"applicable_meta_types", "value_meta_types"}
                )
            )

            # Save to database
            result = await self._save(model, session)

            # Reload to get all relationships
            query = (
                select(AttributeTypeModel)
                .where(AttributeTypeModel.id == result.id)
                .options(
                    selectinload(AttributeTypeModel.applicable_meta_types),
                    selectinload(AttributeTypeModel.value_meta_types),
                )
            )

            result = await self._execute_query(query, session)

            return Success(AttributeType(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error creating attribute type: {e}")
            return Failure(
                AttributeRepositoryError(f"Error creating attribute type: {str(e)}")
            )

    async def update(
        self, attribute_type: AttributeType, session: Optional[AsyncSession] = None
    ) -> Result[AttributeType]:
        """
        Update an existing attribute type.

        Args:
            attribute_type: The attribute type to update
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing the updated attribute type or an error
        """
        try:
            # Check if the attribute type exists
            existing_result = await self.get_by_id(attribute_type.id, session)

            if existing_result.is_failure:
                return existing_result

            if existing_result.value is None:
                return Failure(
                    AttributeRepositoryError(
                        f"Attribute type with ID {attribute_type.id} not found"
                    )
                )

            # Convert to model
            model = AttributeTypeModel(
                **attribute_type.model_dump(
                    exclude={"applicable_meta_types", "value_meta_types"}
                )
            )

            # Save to database
            result = await self._save(model, session)

            # Reload to get all relationships
            query = (
                select(AttributeTypeModel)
                .where(AttributeTypeModel.id == result.id)
                .options(
                    selectinload(AttributeTypeModel.applicable_meta_types),
                    selectinload(AttributeTypeModel.value_meta_types),
                )
            )

            result = await self._execute_query(query, session)

            return Success(AttributeType(**result.dict()))

        except Exception as e:
            self.logger.error(f"Error updating attribute type: {e}")
            return Failure(
                AttributeRepositoryError(f"Error updating attribute type: {str(e)}")
            )

    async def delete(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """
        Delete an attribute type by ID.

        Args:
            attribute_type_id: The ID of the attribute type to delete
            session: Optional async session. If not provided, a new session is created.

        Returns:
            Result containing True if successful, or an error
        """
        try:
            # Check if the attribute type exists
            existing_result = await self.get_by_id(attribute_type_id, session)

            if existing_result.is_failure:
                return existing_result

            if existing_result.value is None:
                return Failure(
                    AttributeRepositoryError(
                        f"Attribute type with ID {attribute_type_id} not found"
                    )
                )

            # Delete from database
            result = await self._delete(attribute_type_id, session)

            return Success(result)

        except Exception as e:
            self.logger.error(f"Error deleting attribute type: {e}")
            return Failure(
                AttributeRepositoryError(f"Error deleting attribute type: {str(e)}")
            )
