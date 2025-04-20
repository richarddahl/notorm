"""
Domain entities for the Values module.

This module contains domain entities for various value types used in the application.
"""

import datetime
import decimal
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any

from uno.domain.core import Entity, AggregateRoot
from uno.core.base.error import ValidationError
from uno.core.errors.result import Result


@dataclass
class BaseValue(AggregateRoot[str]):
    """
    Base class for all value entities.

    This class contains common fields and validation for all value types.
    """

    name: str
    group_id: str | None = None
    tenant_id: str | None = None

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = ""

    def validate(self) -> Result[None, str]:
        """Validate the value."""
        if not self.name:
            return Result.failure("Name cannot be empty")
        return Result.success(None)


@dataclass
class Attachment(BaseValue):
    """Domain entity for file attachments."""

    file_path: str
    __uno_model__: ClassVar[str] = "AttachmentModel"

    def validate(self) -> Result[None, str]:
        """Validate the attachment."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not self.file_path:
            return Result.failure("File path cannot be empty")
        return Result.success(None)


@dataclass
class BooleanValue(BaseValue):
    """Domain entity for boolean values."""

    value: bool
    __uno_model__: ClassVar[str] = "BooleanValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the boolean value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, bool):
            return Result.failure("Value must be a boolean")
        return Result.success(None)


@dataclass
class DateTimeValue(BaseValue):
    """Domain entity for datetime values."""

    value: datetime.datetime
    __uno_model__: ClassVar[str] = "DateTimeValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the datetime value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, datetime.datetime):
            return Result.failure("Value must be a datetime")
        return Result.success(None)


@dataclass
class DateValue(BaseValue):
    """Domain entity for date values."""

    value: datetime.date
    __uno_model__: ClassVar[str] = "DateValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the date value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, datetime.date):
            return Result.failure("Value must be a date")
        return Result.success(None)


@dataclass
class DecimalValue(BaseValue):
    """Domain entity for decimal values."""

    value: decimal.Decimal
    __uno_model__: ClassVar[str] = "DecimalValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the decimal value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, decimal.Decimal):
            return Result.failure("Value must be a decimal")
        return Result.success(None)


@dataclass
class IntegerValue(BaseValue):
    """Domain entity for integer values."""

    value: int
    __uno_model__: ClassVar[str] = "IntegerValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the integer value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, int):
            return Result.failure("Value must be an integer")
        return Result.success(None)


@dataclass
class TextValue(BaseValue):
    """Domain entity for text values."""

    value: str
    __uno_model__: ClassVar[str] = "TextValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the text value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, str):
            return Result.failure("Value must be a string")
        return Result.success(None)


@dataclass
class TimeValue(BaseValue):
    """Domain entity for time values."""

    value: datetime.time
    __uno_model__: ClassVar[str] = "TimeValueModel"

    def validate(self) -> Result[None, str]:
        """Validate the time value."""
        base_result = super().validate()
        if base_result.is_failure():
            return base_result
        if not isinstance(self.value, datetime.time):
            return Result.failure("Value must be a time")
        return Result.success(None)
