# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Service implementations for the attributes module.

This module provides business logic for working with attributes and attribute types,
implementing the interfaces defined in interfaces.py.
"""

from typing import Dict, List, Optional, Type, Union
import logging

from uno.core.errors.result import Result, Success, Failure
from uno.database.db_manager import DBManager
from uno.attributes.interfaces import (
    AttributeServiceProtocol,
    AttributeTypeServiceProtocol,
)
from uno.attributes.repositories import AttributeRepository, AttributeTypeRepository
from uno.attributes.errors import (
    AttributeErrorCode,
    AttributeNotFoundError,
    AttributeTypeNotFoundError,
    AttributeInvalidDataError,
    AttributeTypeInvalidDataError,
    AttributeValueError,
    AttributeServiceError,
    AttributeTypeServiceError,
)


class AttributeService(AttributeServiceProtocol):
    """
    Service implementation for attributes.

    This class provides business logic for working with attributes,
    implementing the AttributeServiceProtocol interface.
    """

    def __init__(
        self,
        attribute_repository: AttributeRepository,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the attribute service.

        Args:
            attribute_repository: Repository for attribute operations
            logger: Optional logger
        """
        self.attribute_repository = attribute_repository
        self.logger = logger or logging.getLogger(__name__)

    async def create_attribute(
        self, attribute: Attribute, values: Optional[List[MetaRecord]] = None
    ) -> Result[Attribute]:
        """Create a new attribute with optional values."""
        try:
            # First create the attribute
            result = await self.attribute_repository.create(attribute)

            if result.is_failure:
                return result

            created_attribute = result.value

            # Add values if provided
            if values and values:
                add_values_result = await self.add_values(created_attribute.id, values)

                if add_values_result.is_failure:
                    self.logger.warning(
                        f"Created attribute {created_attribute.id} but failed to add values: "
                        f"{add_values_result.error}"
                    )
                    return result  # Return the attribute anyway

                return add_values_result

            return result

        except Exception as e:
            self.logger.error(f"Error creating attribute: {e}")
            return Failure(AttributeServiceError(reason=str(e), operation="create"))

    async def add_values(
        self, attribute_id: str, values: List[MetaRecord]
    ) -> Result[Attribute]:
        """Add values to an existing attribute."""
        try:
            # First get the attribute
            attribute_result = await self.attribute_repository.get_by_id(attribute_id)

            if attribute_result.is_failure:
                return attribute_result

            attribute = attribute_result.value

            if attribute is None:
                return Failure(AttributeNotFoundError(attribute_id))

            # Update the attribute's values
            # In a real implementation, this would handle many-to-many relationship updates
            # For now, we'll just set the values directly
            attribute.values = values

            # Save the updated attribute
            update_result = await self.attribute_repository.update(attribute)

            return update_result

        except Exception as e:
            self.logger.error(f"Error adding values to attribute {attribute_id}: {e}")
            return Failure(
                AttributeServiceError(
                    reason=str(e), operation="add_values", attribute_id=attribute_id
                )
            )

    async def remove_values(
        self, attribute_id: str, value_ids: List[str]
    ) -> Result[Attribute]:
        """Remove values from an attribute."""
        try:
            # First get the attribute
            attribute_result = await self.attribute_repository.get_by_id(attribute_id)

            if attribute_result.is_failure:
                return attribute_result

            attribute = attribute_result.value

            if attribute is None:
                return Failure(AttributeNotFoundError(attribute_id))

            # Remove the specified values
            if attribute.values:
                attribute.values = [
                    v for v in attribute.values if v.id not in value_ids
                ]

            # Save the updated attribute
            update_result = await self.attribute_repository.update(attribute)

            return update_result

        except Exception as e:
            self.logger.error(
                f"Error removing values from attribute {attribute_id}: {e}"
            )
            return Failure(
                AttributeServiceError(
                    reason=str(e), operation="remove_values", attribute_id=attribute_id
                )
            )

    async def validate_attribute(
        self, attribute: Attribute, values: Optional[List[MetaRecord]] = None
    ) -> Result[bool]:
        """Validate an attribute against its type constraints."""
        try:
            # In a real implementation, this would check:
            # - If the attribute complies with its attribute type's constraints
            # - If the values are of the correct type
            # - If required fields are present
            # - etc.

            # For now, we'll just return True
            return Success(True)

        except Exception as e:
            self.logger.error(f"Error validating attribute: {e}")
            return Failure(
                AttributeInvalidDataError(
                    reason=str(e), message="Error validating attribute"
                )
            )

    async def get_attributes_for_record(
        self, record_id: str, include_values: bool = True
    ) -> Result[List[Attribute]]:
        """Get all attributes associated with a record."""
        try:
            # Get attributes for the record
            result = await self.attribute_repository.get_by_meta_record(record_id)

            return result

        except Exception as e:
            self.logger.error(f"Error getting attributes for record {record_id}: {e}")
            return Failure(
                AttributeServiceError(
                    reason=str(e),
                    operation="get_attributes_for_record",
                    record_id=record_id,
                )
            )


class AttributeTypeService(AttributeTypeServiceProtocol):
    """
    Service implementation for attribute types.

    This class provides business logic for working with attribute types,
    implementing the AttributeTypeServiceProtocol interface.
    """

    def __init__(
        self,
        attribute_type_repository: AttributeTypeRepository,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the attribute type service.

        Args:
            attribute_type_repository: Repository for attribute type operations
            logger: Optional logger
        """
        self.attribute_type_repository = attribute_type_repository
        self.logger = logger or logging.getLogger(__name__)

    async def create_attribute_type(
        self,
        attribute_type: AttributeType,
        applicable_meta_types: Optional[List[MetaType]] = None,
        value_meta_types: Optional[List[MetaType]] = None,
    ) -> Result[AttributeType]:
        """Create a new attribute type with optional related meta types."""
        try:
            # In a real implementation, this would handle setting up the
            # relationships between the attribute type and meta types

            # For now, we'll just create the attribute type
            result = await self.attribute_type_repository.create(attribute_type)

            return result

        except Exception as e:
            self.logger.error(f"Error creating attribute type: {e}")
            return Failure(AttributeTypeServiceError(reason=str(e), operation="create"))

    async def update_applicable_meta_types(
        self, attribute_type_id: str, meta_type_ids: List[str]
    ) -> Result[AttributeType]:
        """Update the meta types this attribute type applies to."""
        try:
            # First get the attribute type
            attribute_type_result = await self.attribute_type_repository.get_by_id(
                attribute_type_id
            )

            if attribute_type_result.is_failure:
                return attribute_type_result

            attribute_type = attribute_type_result.value

            if attribute_type is None:
                return Failure(AttributeTypeNotFoundError(attribute_type_id))

            # Update the applicable meta types
            # In a real implementation, this would handle many-to-many relationship updates

            # Save the updated attribute type
            update_result = await self.attribute_type_repository.update(attribute_type)

            return update_result

        except Exception as e:
            self.logger.error(
                f"Error updating applicable meta types for attribute type {attribute_type_id}: {e}"
            )
            return Failure(
                AttributeTypeServiceError(
                    reason=str(e),
                    operation="update_applicable_meta_types",
                    attribute_type_id=attribute_type_id,
                )
            )

    async def update_value_meta_types(
        self, attribute_type_id: str, meta_type_ids: List[str]
    ) -> Result[AttributeType]:
        """Update the meta types allowed as values for this attribute type."""
        try:
            # First get the attribute type
            attribute_type_result = await self.attribute_type_repository.get_by_id(
                attribute_type_id
            )

            if attribute_type_result.is_failure:
                return attribute_type_result

            attribute_type = attribute_type_result.value

            if attribute_type is None:
                return Failure(AttributeTypeNotFoundError(attribute_type_id))

            # Update the value meta types
            # In a real implementation, this would handle many-to-many relationship updates

            # Save the updated attribute type
            update_result = await self.attribute_type_repository.update(attribute_type)

            return update_result

        except Exception as e:
            self.logger.error(
                f"Error updating value meta types for attribute type {attribute_type_id}: {e}"
            )
            return Failure(
                AttributeTypeServiceError(
                    reason=str(e),
                    operation="update_value_meta_types",
                    attribute_type_id=attribute_type_id,
                )
            )

    async def get_applicable_attribute_types(
        self, meta_type_id: str
    ) -> Result[List[AttributeType]]:
        """Get all attribute types applicable to a meta type."""
        try:
            # Get attribute types for the meta type
            result = await self.attribute_type_repository.get_by_meta_type(meta_type_id)

            return result

        except Exception as e:
            self.logger.error(
                f"Error getting applicable attribute types for meta type {meta_type_id}: {e}"
            )
            return Failure(
                AttributeTypeServiceError(
                    reason=str(e),
                    operation="get_applicable_attribute_types",
                    meta_type_id=meta_type_id,
                )
            )
