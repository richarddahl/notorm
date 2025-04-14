# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
The values module provides type-safe storage for different kinds of values
used throughout the UNO framework, particularly as attribute values.

This module implements specialized storage for various data types, ensuring
type safety, proper validation, and efficient querying. Each value type
has appropriate lookup operations defined for filtering.

Key components:
- BooleanValue: True/False values
- TextValue: String text values
- IntegerValue: Integer numerical values
- DecimalValue: Decimal numerical values
- DateValue: Date values
- DateTimeValue: Date and time values
- TimeValue: Time values
- Attachment: File attachments
- API Integration: FastAPI endpoints for value operations
"""

from uno.values.models import (
    AttachmentModel,
    BooleanValueModel,
    DateTimeValueModel,
    DateValueModel,
    DecimalValueModel,
    IntegerValueModel,
    TextValueModel,
    TimeValueModel,
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
from uno.values.interfaces import ValueRepositoryProtocol, ValueServiceProtocol
from uno.values.repositories import (
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository,
)
from uno.values.services import ValueService
from uno.values.api_integration import register_value_endpoints
from uno.values.errors import (
    ValueErrorCode,
    ValueNotFoundError,
    ValueInvalidDataError,
    ValueTypeMismatchError,
    ValueValidationError,
    ValueServiceError,
    ValueRepositoryError,
    register_value_errors,
)

# Register value error codes in the catalog
try:
    register_value_errors()
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to register value error codes: {e}")

__all__ = [
    # Models
    "Attachment",
    "AttachmentModel",
    "BooleanValue",
    "BooleanValueModel",
    "DateTimeValue",
    "DateTimeValueModel",
    "DateValue",
    "DateValueModel",
    "DecimalValue",
    "DecimalValueModel",
    "IntegerValue",
    "IntegerValueModel",
    "TextValue",
    "TextValueModel",
    "TimeValue",
    "TimeValueModel",
    
    # Interfaces
    "ValueRepositoryProtocol",
    "ValueServiceProtocol",
    
    # Repositories
    "AttachmentRepository",
    "BooleanValueRepository",
    "DateTimeValueRepository",
    "DateValueRepository",
    "DecimalValueRepository",
    "IntegerValueRepository",
    "TextValueRepository",
    "TimeValueRepository",
    
    # Services
    "ValueService",
    
    # API integration
    "register_value_endpoints",
    
    # Error types
    "ValueErrorCode",
    "ValueNotFoundError",
    "ValueInvalidDataError",
    "ValueTypeMismatchError",
    "ValueValidationError",
    "ValueServiceError",
    "ValueRepositoryError",
]