# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the attributes module.

This module defines the interfaces for the attributes repositories and services,
following the project's dependency injection pattern.
"""

from typing import List, Optional, Protocol, TypeVar, runtime_checkable, Type
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result
from uno.attributes.models import AttributeModel, AttributeTypeModel
from uno.attributes.errors import (
    AttributeErrorCode,
    AttributeNotFoundError,
    AttributeValidationError,
    AttributeGraphError,
)


T = TypeVar("T")


@runtime_checkable
class AttributeRepositoryProtocol(Protocol):
    """Protocol for attribute repositories."""

    async def get_by_id(
        self, attribute_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[Attribute]]:
        """Get an attribute by ID."""
        ...

    async def get_by_type(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """Get attributes by attribute type ID."""
        ...

    async def get_by_meta_record(
        self, meta_record_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """Get attributes associated with a meta record."""
        ...

    async def create(
        self, attribute: Attribute, session: Optional[AsyncSession] = None
    ) -> Result[Attribute]:
        """Create a new attribute."""
        ...

    async def update(
        self, attribute: Attribute, session: Optional[AsyncSession] = None
    ) -> Result[Attribute]:
        """Update an existing attribute."""
        ...

    async def delete(
        self, attribute_id: str, session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """Delete an attribute by ID."""
        ...

    async def bulk_create(
        self, attributes: List[Attribute], session: Optional[AsyncSession] = None
    ) -> Result[List[Attribute]]:
        """Create multiple attributes in a single operation."""
        ...


@runtime_checkable
class AttributeTypeRepositoryProtocol(Protocol):
    """Protocol for attribute type repositories."""

    async def get_by_id(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[AttributeType]]:
        """Get an attribute type by ID."""
        ...

    async def get_by_name(
        self, name: str, session: Optional[AsyncSession] = None
    ) -> Result[Optional[AttributeType]]:
        """Get an attribute type by name."""
        ...

    async def get_by_meta_type(
        self, meta_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[List[AttributeType]]:
        """Get attribute types applicable to a meta type."""
        ...

    async def create(
        self, attribute_type: AttributeType, session: Optional[AsyncSession] = None
    ) -> Result[AttributeType]:
        """Create a new attribute type."""
        ...

    async def update(
        self, attribute_type: AttributeType, session: Optional[AsyncSession] = None
    ) -> Result[AttributeType]:
        """Update an existing attribute type."""
        ...

    async def delete(
        self, attribute_type_id: str, session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """Delete an attribute type by ID."""
        ...


@runtime_checkable
class AttributeServiceProtocol(Protocol):
    """Protocol for attribute services."""

    async def create_attribute(
        self, attribute: Attribute, values: Optional[List[MetaRecord]] = None
    ) -> Result[Attribute]:
        """
        Create a new attribute with optional values.

        Args:
            attribute: The attribute to create
            values: Optional list of values to associate with the attribute

        Returns:
            Result containing the created attribute or an error
        """
        ...

    async def add_values(
        self, attribute_id: str, values: List[MetaRecord]
    ) -> Result[Attribute]:
        """
        Add values to an existing attribute.

        Args:
            attribute_id: The ID of the attribute
            values: List of values to add to the attribute

        Returns:
            Result containing the updated attribute or an error
        """
        ...

    async def remove_values(
        self, attribute_id: str, value_ids: List[str]
    ) -> Result[Attribute]:
        """
        Remove values from an attribute.

        Args:
            attribute_id: The ID of the attribute
            value_ids: List of value IDs to remove from the attribute

        Returns:
            Result containing the updated attribute or an error
        """
        ...

    async def validate_attribute(
        self, attribute: Attribute, values: Optional[List[MetaRecord]] = None
    ) -> Result[bool]:
        """
        Validate an attribute against its type constraints.

        Args:
            attribute: The attribute to validate
            values: Optional list of values to validate

        Returns:
            Result containing True if valid, or an error
        """
        ...

    async def get_attributes_for_record(
        self, record_id: str, include_values: bool = True
    ) -> Result[List[Attribute]]:
        """
        Get all attributes associated with a record.

        Args:
            record_id: The ID of the record
            include_values: Whether to include attribute values

        Returns:
            Result containing a list of attributes or an error
        """
        ...


@runtime_checkable
class AttributeTypeServiceProtocol(Protocol):
    """Protocol for attribute type services."""

    async def create_attribute_type(
        self,
        attribute_type: AttributeType,
        applicable_meta_types: Optional[List[MetaType]] = None,
        value_meta_types: Optional[List[MetaType]] = None,
    ) -> Result[AttributeType]:
        """
        Create a new attribute type with optional related meta types.

        Args:
            attribute_type: The attribute type to create
            applicable_meta_types: Optional list of meta types this attribute type applies to
            value_meta_types: Optional list of meta types allowed as values

        Returns:
            Result containing the created attribute type or an error
        """
        ...

    async def update_applicable_meta_types(
        self, attribute_type_id: str, meta_type_ids: List[str]
    ) -> Result[AttributeType]:
        """
        Update the meta types this attribute type applies to.

        Args:
            attribute_type_id: The ID of the attribute type
            meta_type_ids: List of meta type IDs

        Returns:
            Result containing the updated attribute type or an error
        """
        ...

    async def update_value_meta_types(
        self, attribute_type_id: str, meta_type_ids: List[str]
    ) -> Result[AttributeType]:
        """
        Update the meta types allowed as values for this attribute type.

        Args:
            attribute_type_id: The ID of the attribute type
            meta_type_ids: List of meta type IDs

        Returns:
            Result containing the updated attribute type or an error
        """
        ...

    async def get_applicable_attribute_types(
        self, meta_type_id: str
    ) -> Result[List[AttributeType]]:
        """
        Get all attribute types applicable to a meta type.

        Args:
            meta_type_id: The ID of the meta type

        Returns:
            Result containing a list of attribute types or an error
        """
        ...
