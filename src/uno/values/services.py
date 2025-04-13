# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Service implementations for the values module.

This module provides business logic for working with different value types,
implementing the interfaces defined in interfaces.py.
"""

import datetime
import decimal
from typing import Any, Dict, List, Optional, Type, Union, cast
import logging

from uno.core.errors.result import Result, Ok, Err
from uno.database.db_manager import DBManager
from uno.values.interfaces import ValueServiceProtocol, ValueObj, ValueType
from uno.values.repositories import (
    BooleanValueRepository,
    TextValueRepository,
    IntegerValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
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


class ValueServiceError(Exception):
    """Base error class for value service errors."""
    pass


class ValueService(ValueServiceProtocol):
    """Service for value operations."""

    def __init__(
        self,
        boolean_repository: BooleanValueRepository,
        text_repository: TextValueRepository,
        integer_repository: IntegerValueRepository,
        decimal_repository: DecimalValueRepository,
        date_repository: DateValueRepository,
        datetime_repository: DateTimeValueRepository,
        time_repository: TimeValueRepository,
        attachment_repository: AttachmentRepository,
        db_manager: DBManager,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the value service.
        
        Args:
            boolean_repository: Repository for boolean values
            text_repository: Repository for text values
            integer_repository: Repository for integer values
            decimal_repository: Repository for decimal values
            date_repository: Repository for date values
            datetime_repository: Repository for datetime values
            time_repository: Repository for time values
            attachment_repository: Repository for attachments
            db_manager: Database manager instance
            logger: Optional logger
        """
        self.repositories = {
            BooleanValue: boolean_repository,
            TextValue: text_repository,
            IntegerValue: integer_repository,
            DecimalValue: decimal_repository,
            DateValue: date_repository,
            DateTimeValue: datetime_repository,
            TimeValue: time_repository,
            Attachment: attachment_repository,
        }
        self.db_manager = db_manager
        self.logger = logger or logging.getLogger(__name__)

    async def create_value(
        self,
        value_type: Type[ValueObj],
        value: ValueType,
        name: Optional[str] = None
    ) -> Result[ValueObj, ValueServiceError]:
        """
        Create a new value of the specified type.
        
        Args:
            value_type: The type of value to create
            value: The actual value
            name: Optional name for the value
            
        Returns:
            Result containing the created value object or an error
        """
        try:
            # Get the appropriate repository
            repository = self._get_repository(value_type)
            
            if not repository:
                return Err(ValueServiceError(f"No repository found for value type {value_type.__name__}"))
            
            # Validate value
            validation_result = await self.validate_value(value_type, value)
            
            if validation_result.is_err():
                return Err(ValueServiceError(f"Validation failed: {validation_result.unwrap_err()}"))
            
            # Create value object
            value_obj = value_type(
                value=value,
                name=name or str(value)
            )
            
            # Create value
            create_result = await repository.create(value_obj)
            
            if create_result.is_err():
                return Err(ValueServiceError(f"Failed to create value: {create_result.unwrap_err()}"))
            
            return Ok(create_result.unwrap())
        
        except Exception as e:
            self.logger.error(f"Error creating {value_type.__name__}: {e}")
            return Err(ValueServiceError(f"Error creating {value_type.__name__}: {str(e)}"))

    async def get_or_create_value(
        self,
        value_type: Type[ValueObj],
        value: ValueType,
        name: Optional[str] = None
    ) -> Result[ValueObj, ValueServiceError]:
        """
        Get a value by its actual value, or create it if it doesn't exist.
        
        Args:
            value_type: The type of value to get or create
            value: The actual value
            name: Optional name for the value if it needs to be created
            
        Returns:
            Result containing the value object or an error
        """
        try:
            # Get the appropriate repository
            repository = self._get_repository(value_type)
            
            if not repository:
                return Err(ValueServiceError(f"No repository found for value type {value_type.__name__}"))
            
            # Try to get existing value
            get_result = await repository.get_by_value(value)
            
            if get_result.is_err():
                return Err(ValueServiceError(f"Failed to get value: {get_result.unwrap_err()}"))
            
            existing_value = get_result.unwrap()
            
            # Return existing value if found
            if existing_value:
                return Ok(existing_value)
            
            # Create new value if not found
            return await self.create_value(value_type, value, name)
        
        except Exception as e:
            self.logger.error(f"Error getting or creating {value_type.__name__}: {e}")
            return Err(ValueServiceError(f"Error getting or creating {value_type.__name__}: {str(e)}"))

    async def get_value_by_id(
        self,
        value_type: Type[ValueObj],
        value_id: str
    ) -> Result[Optional[ValueObj], ValueServiceError]:
        """
        Get a value by its ID.
        
        Args:
            value_type: The type of value to get
            value_id: The ID of the value
            
        Returns:
            Result containing the value object or an error
        """
        try:
            # Get the appropriate repository
            repository = self._get_repository(value_type)
            
            if not repository:
                return Err(ValueServiceError(f"No repository found for value type {value_type.__name__}"))
            
            # Get value
            get_result = await repository.get_by_id(value_id)
            
            if get_result.is_err():
                return Err(ValueServiceError(f"Failed to get value: {get_result.unwrap_err()}"))
            
            return Ok(get_result.unwrap())
        
        except Exception as e:
            self.logger.error(f"Error getting {value_type.__name__} by ID {value_id}: {e}")
            return Err(ValueServiceError(f"Error getting {value_type.__name__}: {str(e)}"))

    async def create_attachment(
        self,
        file_path: str,
        name: str
    ) -> Result[Attachment, ValueServiceError]:
        """
        Create a new file attachment.
        
        Args:
            file_path: Path to the file
            name: Name of the attachment
            
        Returns:
            Result containing the created attachment or an error
        """
        try:
            # Get the attachment repository
            repository = self._get_repository(Attachment)
            
            if not repository:
                return Err(ValueServiceError("Attachment repository not found"))
            
            # Create attachment object
            attachment = Attachment(
                file_path=file_path,
                name=name
            )
            
            # Create attachment
            create_result = await repository.create(attachment)
            
            if create_result.is_err():
                return Err(ValueServiceError(f"Failed to create attachment: {create_result.unwrap_err()}"))
            
            return Ok(create_result.unwrap())
        
        except Exception as e:
            self.logger.error(f"Error creating attachment: {e}")
            return Err(ValueServiceError(f"Error creating attachment: {str(e)}"))

    async def validate_value(
        self,
        value_type: Type[ValueObj],
        value: ValueType
    ) -> Result[bool, ValueServiceError]:
        """
        Validate a value against its type constraints.
        
        Args:
            value_type: The type of value to validate
            value: The actual value to validate
            
        Returns:
            Result containing True if valid, or an error
        """
        try:
            # Validate correct type
            valid_type = False
            
            if value_type == BooleanValue and isinstance(value, bool):
                valid_type = True
            elif value_type == IntegerValue and isinstance(value, int) and not isinstance(value, bool):
                valid_type = True
            elif value_type == TextValue and isinstance(value, str):
                valid_type = True
            elif value_type == DecimalValue and (isinstance(value, decimal.Decimal) or isinstance(value, float)):
                valid_type = True
            elif value_type == DateValue and isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
                valid_type = True
            elif value_type == DateTimeValue and isinstance(value, datetime.datetime):
                valid_type = True
            elif value_type == TimeValue and isinstance(value, datetime.time):
                valid_type = True
            
            if not valid_type:
                expected_type = {
                    BooleanValue: "bool",
                    IntegerValue: "int",
                    TextValue: "str",
                    DecimalValue: "decimal.Decimal or float",
                    DateValue: "datetime.date",
                    DateTimeValue: "datetime.datetime",
                    TimeValue: "datetime.time",
                }.get(value_type, "unknown")
                
                return Err(ValueServiceError(
                    f"Invalid value type: expected {expected_type}, got {type(value).__name__}"
                ))
            
            return Ok(True)
        
        except Exception as e:
            self.logger.error(f"Error validating value: {e}")
            return Err(ValueServiceError(f"Error validating value: {str(e)}"))

    async def convert_value(
        self,
        value: Any,
        target_type: Type[ValueObj]
    ) -> Result[ValueType, ValueServiceError]:
        """
        Convert a value to the appropriate type for a value object.
        
        Args:
            value: The value to convert
            target_type: The target value type
            
        Returns:
            Result containing the converted value or an error
        """
        try:
            # Already correct type
            if await self.validate_value(target_type, value).is_ok():
                return Ok(value)
            
            # Conversion logic based on target type
            converted_value = None
            
            if target_type == BooleanValue:
                # String conversion
                if isinstance(value, str):
                    lower_value = value.lower()
                    if lower_value in ("true", "yes", "1", "y", "t"):
                        converted_value = True
                    elif lower_value in ("false", "no", "0", "n", "f"):
                        converted_value = False
                # Numeric conversion
                elif isinstance(value, (int, float)):
                    converted_value = bool(value)
            
            elif target_type == IntegerValue:
                # String conversion
                if isinstance(value, str):
                    try:
                        converted_value = int(value)
                    except ValueError:
                        pass
                # Float conversion
                elif isinstance(value, float):
                    converted_value = int(value)
                # Boolean conversion
                elif isinstance(value, bool):
                    converted_value = 1 if value else 0
            
            elif target_type == TextValue:
                # Convert any value to string
                converted_value = str(value)
            
            elif target_type == DecimalValue:
                # String conversion
                if isinstance(value, str):
                    try:
                        converted_value = decimal.Decimal(value)
                    except decimal.InvalidOperation:
                        pass
                # Numeric conversion
                elif isinstance(value, (int, float)):
                    converted_value = decimal.Decimal(str(value))
                # Boolean conversion
                elif isinstance(value, bool):
                    converted_value = decimal.Decimal("1" if value else "0")
            
            elif target_type == DateValue:
                # String conversion (ISO format)
                if isinstance(value, str):
                    try:
                        converted_value = datetime.date.fromisoformat(value)
                    except ValueError:
                        pass
                # DateTime conversion
                elif isinstance(value, datetime.datetime):
                    converted_value = value.date()
            
            elif target_type == DateTimeValue:
                # String conversion (ISO format)
                if isinstance(value, str):
                    try:
                        converted_value = datetime.datetime.fromisoformat(value)
                    except ValueError:
                        pass
                # Date conversion
                elif isinstance(value, datetime.date):
                    converted_value = datetime.datetime.combine(value, datetime.time())
            
            elif target_type == TimeValue:
                # String conversion (ISO format)
                if isinstance(value, str):
                    try:
                        converted_value = datetime.time.fromisoformat(value)
                    except ValueError:
                        pass
                # DateTime conversion
                elif isinstance(value, datetime.datetime):
                    converted_value = value.time()
            
            if converted_value is None:
                return Err(ValueServiceError(
                    f"Cannot convert {type(value).__name__} to {target_type.__name__}"
                ))
            
            # Validate converted value
            validation_result = await self.validate_value(target_type, converted_value)
            
            if validation_result.is_err():
                return Err(ValueServiceError(f"Conversion validation failed: {validation_result.unwrap_err()}"))
            
            return Ok(converted_value)
        
        except Exception as e:
            self.logger.error(f"Error converting value: {e}")
            return Err(ValueServiceError(f"Error converting value: {str(e)}"))

    def _get_repository(self, value_type: Type[ValueObj]):
        """Get the appropriate repository for a value type."""
        return self.repositories.get(value_type)