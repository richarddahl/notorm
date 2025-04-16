# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema managers for the Values module.

This module provides schema managers for converting between domain entities and DTOs
for various value types. It serves as a bridge between the repository/domain layer and the API layer.
"""

from typing import Dict, Type, Any, Optional, Union, List
from pydantic import BaseModel
from datetime import date, datetime, time
from decimal import Decimal

from uno.values.entities import (
    BaseValue,
    BooleanValue,
    IntegerValue,
    TextValue,
    DecimalValue,
    DateValue,
    DateTimeValue,
    TimeValue,
    Attachment,
)
from uno.values.dtos import (
    # Base DTOs
    ValueBaseDto,
    ValueResponseDto,
    CreateValueDto,
    UpdateValueDto,
    ValueFilterParams,
    
    # Value type-specific DTOs
    BooleanValueCreateDto,
    BooleanValueViewDto,
    IntegerValueCreateDto,
    IntegerValueViewDto,
    TextValueCreateDto,
    TextValueViewDto,
    DecimalValueCreateDto,
    DecimalValueViewDto,
    DateValueCreateDto,
    DateValueViewDto,
    DateTimeValueCreateDto,
    DateTimeValueViewDto,
    TimeValueCreateDto,
    TimeValueViewDto,
    AttachmentCreateDto,
    AttachmentViewDto,
)


class BaseValueSchemaManager:
    """Base schema manager for value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        self.schemas = {
            "view_schema": ValueResponseDto,
            "create_schema": CreateValueDto,
            "update_schema": UpdateValueDto,
            "filter_schema": ValueFilterParams,
        }
    
    def get_schema(self, schema_name: str) -> Optional[Type[BaseModel]]:
        """Get a schema by name."""
        return self.schemas.get(schema_name)
    
    def entity_to_dto(self, entity: BaseValue) -> ValueResponseDto:
        """Convert a base entity to a DTO."""
        return ValueResponseDto(
            id=entity.id,
            name=entity.name,
            value_type=self._get_value_type(entity),
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: BaseModel) -> BaseValue:
        """Convert a DTO to an entity."""
        data = dto.model_dump(exclude_unset=True)
        return BaseValue(**data)
    
    def _get_value_type(self, entity: BaseValue) -> str:
        """Get the value type string from an entity."""
        if isinstance(entity, BooleanValue):
            return "boolean"
        elif isinstance(entity, IntegerValue):
            return "integer"
        elif isinstance(entity, TextValue):
            return "text"
        elif isinstance(entity, DecimalValue):
            return "decimal"
        elif isinstance(entity, DateValue):
            return "date"
        elif isinstance(entity, DateTimeValue):
            return "datetime"
        elif isinstance(entity, TimeValue):
            return "time"
        elif isinstance(entity, Attachment):
            return "attachment"
        return "unknown"


class BooleanValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for boolean value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": BooleanValueViewDto,
            "create_schema": BooleanValueCreateDto,
        })
    
    def entity_to_dto(self, entity: BooleanValue) -> BooleanValueViewDto:
        """Convert a boolean value entity to a DTO."""
        return BooleanValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            value_type="boolean",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: BooleanValueCreateDto) -> BooleanValue:
        """Convert a DTO to a boolean value entity."""
        data = dto.model_dump(exclude_unset=True)
        return BooleanValue(**data)


class IntegerValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for integer value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": IntegerValueViewDto,
            "create_schema": IntegerValueCreateDto,
        })
    
    def entity_to_dto(self, entity: IntegerValue) -> IntegerValueViewDto:
        """Convert an integer value entity to a DTO."""
        return IntegerValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            value_type="integer",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: IntegerValueCreateDto) -> IntegerValue:
        """Convert a DTO to an integer value entity."""
        data = dto.model_dump(exclude_unset=True)
        return IntegerValue(**data)


class TextValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for text value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": TextValueViewDto,
            "create_schema": TextValueCreateDto,
        })
    
    def entity_to_dto(self, entity: TextValue) -> TextValueViewDto:
        """Convert a text value entity to a DTO."""
        return TextValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value,
            value_type="text",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: TextValueCreateDto) -> TextValue:
        """Convert a DTO to a text value entity."""
        data = dto.model_dump(exclude_unset=True)
        return TextValue(**data)


class DecimalValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for decimal value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": DecimalValueViewDto,
            "create_schema": DecimalValueCreateDto,
        })
    
    def entity_to_dto(self, entity: DecimalValue) -> DecimalValueViewDto:
        """Convert a decimal value entity to a DTO."""
        return DecimalValueViewDto(
            id=entity.id,
            name=entity.name,
            value=float(entity.value),  # Convert Decimal to float for JSON serialization
            value_type="decimal",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: DecimalValueCreateDto) -> DecimalValue:
        """Convert a DTO to a decimal value entity."""
        data = dto.model_dump(exclude_unset=True)
        # Ensure value is a Decimal
        if not isinstance(data.get("value"), Decimal):
            data["value"] = Decimal(str(data["value"]))
        return DecimalValue(**data)


class DateValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for date value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": DateValueViewDto,
            "create_schema": DateValueCreateDto,
        })
    
    def entity_to_dto(self, entity: DateValue) -> DateValueViewDto:
        """Convert a date value entity to a DTO."""
        return DateValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value.isoformat(),
            value_type="date",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: DateValueCreateDto) -> DateValue:
        """Convert a DTO to a date value entity."""
        data = dto.model_dump(exclude_unset=True)
        # Ensure value is a date
        if isinstance(data.get("value"), str):
            data["value"] = date.fromisoformat(data["value"])
        return DateValue(**data)


class DateTimeValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for datetime value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": DateTimeValueViewDto,
            "create_schema": DateTimeValueCreateDto,
        })
    
    def entity_to_dto(self, entity: DateTimeValue) -> DateTimeValueViewDto:
        """Convert a datetime value entity to a DTO."""
        return DateTimeValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value.isoformat(),
            value_type="datetime",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: DateTimeValueCreateDto) -> DateTimeValue:
        """Convert a DTO to a datetime value entity."""
        data = dto.model_dump(exclude_unset=True)
        # Ensure value is a datetime
        if isinstance(data.get("value"), str):
            data["value"] = datetime.fromisoformat(data["value"])
        return DateTimeValue(**data)


class TimeValueSchemaManager(BaseValueSchemaManager):
    """Schema manager for time value entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": TimeValueViewDto,
            "create_schema": TimeValueCreateDto,
        })
    
    def entity_to_dto(self, entity: TimeValue) -> TimeValueViewDto:
        """Convert a time value entity to a DTO."""
        return TimeValueViewDto(
            id=entity.id,
            name=entity.name,
            value=entity.value.isoformat(),
            value_type="time",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: TimeValueCreateDto) -> TimeValue:
        """Convert a DTO to a time value entity."""
        data = dto.model_dump(exclude_unset=True)
        # Ensure value is a time
        if isinstance(data.get("value"), str):
            data["value"] = time.fromisoformat(data["value"])
        return TimeValue(**data)


class AttachmentSchemaManager(BaseValueSchemaManager):
    """Schema manager for attachment entities."""
    
    def __init__(self):
        """Initialize the schema manager."""
        super().__init__()
        self.schemas.update({
            "view_schema": AttachmentViewDto,
            "create_schema": AttachmentCreateDto,
        })
    
    def entity_to_dto(self, entity: Attachment) -> AttachmentViewDto:
        """Convert an attachment entity to a DTO."""
        return AttachmentViewDto(
            id=entity.id,
            name=entity.name,
            file_path=entity.file_path,
            value_type="attachment",
            created_at=entity.created_at.isoformat() if entity.created_at else None,
            updated_at=entity.updated_at.isoformat() if entity.updated_at else None,
        )
    
    def dto_to_entity(self, dto: AttachmentCreateDto) -> Attachment:
        """Convert a DTO to an attachment entity."""
        data = dto.model_dump(exclude_unset=True)
        return Attachment(**data)


class ValueSchemaManagerFactory:
    """Factory for creating value schema managers based on value type."""
    
    @staticmethod
    def create_schema_manager(value_type: str) -> BaseValueSchemaManager:
        """Create a schema manager for the given value type."""
        schema_managers = {
            "boolean": BooleanValueSchemaManager(),
            "integer": IntegerValueSchemaManager(),
            "text": TextValueSchemaManager(),
            "decimal": DecimalValueSchemaManager(),
            "date": DateValueSchemaManager(),
            "datetime": DateTimeValueSchemaManager(),
            "time": TimeValueSchemaManager(),
            "attachment": AttachmentSchemaManager(),
        }
        
        manager = schema_managers.get(value_type.lower())
        if not manager:
            raise ValueError(f"Invalid value type: {value_type}")
        
        return manager