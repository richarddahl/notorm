# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Data Transfer Objects (DTOs) for the Values module.

This module contains Pydantic models that represent the API contract for value
entities. These DTOs are used for serialization/deserialization in API requests and responses.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import date, datetime, time
from decimal import Decimal


# Base value DTOs
class ValueBaseDto(BaseModel):
    """Base DTO for all value types."""

    name: str | None = Field(None, description="Name of the value")


class ValueResponseDto(BaseModel):
    """Base response DTO for values."""

    id: str = Field(..., description="Unique identifier for the value")
    name: str = Field(..., description="Name of the value")
    value_type: str = Field(..., description="Type of the value")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


# Create/Update DTOs
class CreateValueDto(BaseModel):
    """DTO for creating a value."""

    value_type: str = Field(
        ...,
        description="Type of the value (boolean, integer, text, decimal, date, datetime, time)",
    )
    value: Any = Field(..., description="The actual value")
    name: str | None = Field(
        None,
        description="Optional name for the value (defaults to string representation of value)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value_type": "text",
                "value": "Example value",
                "name": "Example Text",
            }
        }
    )


class UpdateValueDto(BaseModel):
    """DTO for updating a value."""

    name: str | None = Field(None, description="Name of the value")


# Value Type-Specific DTOs


class BooleanValueCreateDto(ValueBaseDto):
    """DTO for creating boolean values."""

    value: bool = Field(..., description="The boolean value")

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": True, "name": "Boolean Example"}}
    )


class BooleanValueViewDto(ValueResponseDto):
    """DTO for viewing boolean values."""

    value: bool = Field(..., description="The boolean value")
    value_type: str = Field("boolean", description="Type of the value")


class IntegerValueCreateDto(ValueBaseDto):
    """DTO for creating integer values."""

    value: int = Field(..., description="The integer value")

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": 42, "name": "Integer Example"}}
    )


class IntegerValueViewDto(ValueResponseDto):
    """DTO for viewing integer values."""

    value: int = Field(..., description="The integer value")
    value_type: str = Field("integer", description="Type of the value")


class TextValueCreateDto(ValueBaseDto):
    """DTO for creating text values."""

    value: str = Field(..., description="The text value")

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": "Example text", "name": "Text Example"}}
    )


class TextValueViewDto(ValueResponseDto):
    """DTO for viewing text values."""

    value: str = Field(..., description="The text value")
    value_type: str = Field("text", description="Type of the value")


class DecimalValueCreateDto(ValueBaseDto):
    """DTO for creating decimal values."""

    value: Union[Decimal, float, str] = Field(..., description="The decimal value")

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": 3.14159, "name": "Decimal Example"}}
    )

    @model_validator(mode="after")
    def validate_decimal(self):
        """Convert value to Decimal if it's not already."""
        if not isinstance(self.value, Decimal):
            try:
                self.value = Decimal(str(self.value))
            except (ValueError, decimal.InvalidOperation):
                raise ValueError(f"Invalid decimal value: {self.value}")
        return self


class DecimalValueViewDto(ValueResponseDto):
    """DTO for viewing decimal values."""

    value: float = Field(..., description="The decimal value")
    value_type: str = Field("decimal", description="Type of the value")


class DateValueCreateDto(ValueBaseDto):
    """DTO for creating date values."""

    value: Union[date, str] = Field(
        ..., description="The date value in ISO format (YYYY-MM-DD)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": "2023-01-15", "name": "Date Example"}}
    )

    @model_validator(mode="after")
    def validate_date(self):
        """Convert value to date if it's a string."""
        if isinstance(self.value, str):
            try:
                self.value = date.fromisoformat(self.value)
            except ValueError:
                raise ValueError(
                    f"Invalid date format: {self.value}. Must be in ISO format (YYYY-MM-DD)"
                )
        return self


class DateValueViewDto(ValueResponseDto):
    """DTO for viewing date values."""

    value: str = Field(..., description="The date value in ISO format (YYYY-MM-DD)")
    value_type: str = Field("date", description="Type of the value")


class DateTimeValueCreateDto(ValueBaseDto):
    """DTO for creating datetime values."""

    value: Union[datetime, str] = Field(
        ..., description="The datetime value in ISO format"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"value": "2023-01-15T14:30:15", "name": "DateTime Example"}
        }
    )

    @model_validator(mode="after")
    def validate_datetime(self):
        """Convert value to datetime if it's a string."""
        if isinstance(self.value, str):
            try:
                self.value = datetime.fromisoformat(self.value)
            except ValueError:
                raise ValueError(
                    f"Invalid datetime format: {self.value}. Must be in ISO format"
                )
        return self


class DateTimeValueViewDto(ValueResponseDto):
    """DTO for viewing datetime values."""

    value: str = Field(..., description="The datetime value in ISO format")
    value_type: str = Field("datetime", description="Type of the value")


class TimeValueCreateDto(ValueBaseDto):
    """DTO for creating time values."""

    value: Union[time, str] = Field(
        ..., description="The time value in ISO format (HH:MM:SS)"
    )

    model_config = ConfigDict(
        json_schema_extra={"example": {"value": "14:30:15", "name": "Time Example"}}
    )

    @model_validator(mode="after")
    def validate_time(self):
        """Convert value to time if it's a string."""
        if isinstance(self.value, str):
            try:
                self.value = time.fromisoformat(self.value)
            except ValueError:
                raise ValueError(
                    f"Invalid time format: {self.value}. Must be in ISO format (HH:MM:SS)"
                )
        return self


class TimeValueViewDto(ValueResponseDto):
    """DTO for viewing time values."""

    value: str = Field(..., description="The time value in ISO format (HH:MM:SS)")
    value_type: str = Field("time", description="Type of the value")


class AttachmentCreateDto(ValueBaseDto):
    """DTO for creating attachments."""

    file_path: str = Field(..., description="Path to the file")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {"file_path": "/path/to/file.pdf", "name": "Attachment Example"}
        }
    )


class AttachmentViewDto(ValueResponseDto):
    """DTO for viewing file attachments."""

    file_path: str = Field(..., description="Path to the file")
    value_type: str = Field("attachment", description="Type of the value")


# Filter parameter DTOs
class ValueFilterParams(BaseModel):
    """Filter parameters for values."""

    name: str | None = Field(None, description="Filter by name")
    value_type: str | None = Field(None, description="Filter by value type")
    created_after: Optional[datetime] = Field(
        None, description="Filter by creation date (after)"
    )
    created_before: Optional[datetime] = Field(
        None, description="Filter by creation date (before)"
    )
