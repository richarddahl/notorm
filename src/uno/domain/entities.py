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


@dataclass
class BaseValue(AggregateRoot[str]):
    """
    Base class for all value entities.

    This class contains common fields and validation for all value types.
    """

    name: str
    group_id: Optional[str] = None
    tenant_id: Optional[str] = None

    # SQLAlchemy model mapping
    __uno_model__: ClassVar[str] = ""

    def validate(self) -> Result[None, str]:
        """Validate the value."""
        if not self.name:
            return Failure[None, str]("Name cannot be empty")
        return Success[None, str](None)


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
            return Failure[None, str]("File path cannot be empty")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a boolean")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a datetime")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a date")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a decimal")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be an integer")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a string")
        return Success[None, str](None)


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
            return Failure[None, str]("Value must be a time")
        return Success[None, str](None)
