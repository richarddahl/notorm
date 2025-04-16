"""
Domain entities for the Values module.

This module contains domain entities for various value types used in the application.
"""

import datetime
import decimal
from dataclasses import dataclass, field
from typing import ClassVar, List, Optional, Dict, Any

from uno.domain.core import Entity, AggregateRoot
from uno.core.errors.base import ValidationError


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

    def validate(self) -> None:
        """Validate the value."""
        if not self.name:
            raise ValidationError("Name cannot be empty")


@dataclass
class Attachment(BaseValue):
    """Domain entity for file attachments."""

    file_path: str
    __uno_model__: ClassVar[str] = "AttachmentModel"

    def validate(self) -> None:
        """Validate the attachment."""
        super().validate()
        if not self.file_path:
            raise ValidationError("File path cannot be empty")


@dataclass
class BooleanValue(BaseValue):
    """Domain entity for boolean values."""

    value: bool
    __uno_model__: ClassVar[str] = "BooleanValueModel"

    def validate(self) -> None:
        """Validate the boolean value."""
        super().validate()
        if not isinstance(self.value, bool):
            raise ValidationError("Value must be a boolean")


@dataclass
class DateTimeValue(BaseValue):
    """Domain entity for datetime values."""

    value: datetime.datetime
    __uno_model__: ClassVar[str] = "DateTimeValueModel"

    def validate(self) -> None:
        """Validate the datetime value."""
        super().validate()
        if not isinstance(self.value, datetime.datetime):
            raise ValidationError("Value must be a datetime")


@dataclass
class DateValue(BaseValue):
    """Domain entity for date values."""

    value: datetime.date
    __uno_model__: ClassVar[str] = "DateValueModel"

    def validate(self) -> None:
        """Validate the date value."""
        super().validate()
        if not isinstance(self.value, datetime.date):
            raise ValidationError("Value must be a date")


@dataclass
class DecimalValue(BaseValue):
    """Domain entity for decimal values."""

    value: decimal.Decimal
    __uno_model__: ClassVar[str] = "DecimalValueModel"

    def validate(self) -> None:
        """Validate the decimal value."""
        super().validate()
        if not isinstance(self.value, decimal.Decimal):
            raise ValidationError("Value must be a decimal")


@dataclass
class IntegerValue(BaseValue):
    """Domain entity for integer values."""

    value: int
    __uno_model__: ClassVar[str] = "IntegerValueModel"

    def validate(self) -> None:
        """Validate the integer value."""
        super().validate()
        if not isinstance(self.value, int):
            raise ValidationError("Value must be an integer")


@dataclass
class TextValue(BaseValue):
    """Domain entity for text values."""

    value: str
    __uno_model__: ClassVar[str] = "TextValueModel"

    def validate(self) -> None:
        """Validate the text value."""
        super().validate()
        if not isinstance(self.value, str):
            raise ValidationError("Value must be a string")


@dataclass
class TimeValue(BaseValue):
    """Domain entity for time values."""

    value: datetime.time
    __uno_model__: ClassVar[str] = "TimeValueModel"

    def validate(self) -> None:
        """Validate the time value."""
        super().validate()
        if not isinstance(self.value, datetime.time):
            raise ValidationError("Value must be a time")
