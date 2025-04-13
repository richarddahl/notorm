# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Protocol definitions for the values module.

This module defines the interfaces for the values repositories and services,
following the project's dependency injection pattern.
"""

from typing import Any, Dict, Generic, List, Optional, Protocol, Type, TypeVar, Union, runtime_checkable
from datetime import date, datetime, time
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.errors.result import Result
from uno.values.objs import (
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)

T = TypeVar('T')
V = TypeVar('V')
ValueType = Union[bool, int, str, Decimal, datetime, date, time]
ValueObj = Union[
    BooleanValue,
    IntegerValue,
    TextValue,
    DecimalValue, 
    DateTimeValue,
    DateValue,
    TimeValue,
    Attachment
]

# Define a concrete error class for values
class ValueError(Exception):
    """Error class for value-related errors."""
    def __init__(self, message: str, code: str = "VALUE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


@runtime_checkable
class ValueRepositoryProtocol(Protocol, Generic[T]):
    """Protocol for value repositories."""

    async def get_by_id(
        self, 
        value_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[T]]:
        """Get a value by ID."""
        ...

    async def get_by_value(
        self, 
        value: Any, 
        session: Optional[AsyncSession] = None
    ) -> Result[Optional[T]]:
        """Get a value object by its actual value."""
        ...

    async def create(
        self, 
        value_obj: T, 
        session: Optional[AsyncSession] = None
    ) -> Result[T]:
        """Create a new value."""
        ...

    async def update(
        self, 
        value_obj: T, 
        session: Optional[AsyncSession] = None
    ) -> Result[T]:
        """Update an existing value."""
        ...

    async def delete(
        self, 
        value_id: str, 
        session: Optional[AsyncSession] = None
    ) -> Result[bool]:
        """Delete a value by ID."""
        ...

    async def bulk_create(
        self, 
        value_objs: List[T], 
        session: Optional[AsyncSession] = None
    ) -> Result[List[T]]:
        """Create multiple values in a single operation."""
        ...

    async def search(
        self, 
        search_term: str, 
        limit: int = 20, 
        session: Optional[AsyncSession] = None
    ) -> Result[List[T]]:
        """Search for values matching a term."""
        ...


@runtime_checkable
class ValueServiceProtocol(Protocol):
    """Protocol for value services."""

    async def create_value(
        self, 
        value_type: Type[ValueObj], 
        value: ValueType, 
        name: Optional[str] = None
    ) -> Result[ValueObj]:
        """
        Create a new value of the specified type.
        
        Args:
            value_type: The type of value to create
            value: The actual value
            name: Optional name for the value
            
        Returns:
            Result containing the created value object or an error
        """
        ...

    async def get_or_create_value(
        self, 
        value_type: Type[ValueObj], 
        value: ValueType, 
        name: Optional[str] = None
    ) -> Result[ValueObj]:
        """
        Get a value by its actual value, or create it if it doesn't exist.
        
        Args:
            value_type: The type of value to get or create
            value: The actual value
            name: Optional name for the value if it needs to be created
            
        Returns:
            Result containing the value object or an error
        """
        ...

    async def get_value_by_id(
        self, 
        value_type: Type[ValueObj], 
        value_id: str
    ) -> Result[Optional[ValueObj]]:
        """
        Get a value by its ID.
        
        Args:
            value_type: The type of value to get
            value_id: The ID of the value
            
        Returns:
            Result containing the value object or an error
        """
        ...

    async def create_attachment(
        self, 
        file_path: str, 
        name: str
    ) -> Result[Attachment]:
        """
        Create a new file attachment.
        
        Args:
            file_path: Path to the file
            name: Name of the attachment
            
        Returns:
            Result containing the created attachment or an error
        """
        ...

    async def validate_value(
        self, 
        value_type: Type[ValueObj], 
        value: ValueType
    ) -> Result[bool]:
        """
        Validate a value against its type constraints.
        
        Args:
            value_type: The type of value to validate
            value: The actual value to validate
            
        Returns:
            Result containing True if valid, or an error
        """
        ...

    async def convert_value(
        self, 
        value: Any, 
        target_type: Type[ValueObj]
    ) -> Result[ValueType]:
        """
        Convert a value to the appropriate type for a value object.
        
        Args:
            value: The value to convert
            target_type: The target value type
            
        Returns:
            Result containing the converted value or an error
        """
        ...