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
- Domain Entities: Type-specific value objects following domain-driven design
  - BooleanValue: True/False values
  - TextValue: String text values
  - IntegerValue: Integer numerical values
  - DecimalValue: Decimal numerical values
  - DateValue: Date values
  - DateTimeValue: Date and time values
  - TimeValue: Time values
  - Attachment: File attachments
- Repository Pattern: Follows domain-driven design for data access
- Domain Services: Encapsulates business logic for values
- API Integration: FastAPI endpoints for value operations
"""

# Domain entities (DDD)
from uno.values.entities import (
    BaseValue,
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)

# Models (for ORM)
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

# Interfaces
from uno.values.interfaces import ValueRepositoryProtocol, ValueServiceProtocol

# Repositories
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

# Services
from uno.values.services import ValueService

# DTOs
from uno.values.dtos import (
    BooleanValueViewDto,
    IntegerValueViewDto,
    TextValueViewDto,
    DecimalValueViewDto,
    DateValueViewDto,
    DateTimeValueViewDto,
    TimeValueViewDto,
    AttachmentViewDto,
)

# Schema managers
from uno.values.schemas import (
    BooleanValueSchemaManager,
    IntegerValueSchemaManager,
    TextValueSchemaManager,
    DecimalValueSchemaManager,
    DateValueSchemaManager,
    DateTimeValueSchemaManager,
    TimeValueSchemaManager,
    AttachmentSchemaManager,
    ValueSchemaManagerFactory,
)

# Legacy API integration
from uno.values.api_integration import register_value_endpoints

# Domain-driven API integration
from uno.values.domain_api_integration import register_domain_value_endpoints_api

# Error types
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
    # Domain Entities (DDD)
    "BaseValue",
    "Attachment",
    "BooleanValue",
    "DateTimeValue",
    "DateValue",
    "DecimalValue",
    "IntegerValue",
    "TextValue",
    "TimeValue",
    
    # ORM Models
    "AttachmentModel",
    "BooleanValueModel",
    "DateTimeValueModel",
    "DateValueModel",
    "DecimalValueModel",
    "IntegerValueModel",
    "TextValueModel",
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
    
    # DTOs
    "BooleanValueViewDto",
    "IntegerValueViewDto",
    "TextValueViewDto",
    "DecimalValueViewDto",
    "DateValueViewDto",
    "DateTimeValueViewDto",
    "TimeValueViewDto",
    "AttachmentViewDto",
    
    # Schema Managers
    "BooleanValueSchemaManager",
    "IntegerValueSchemaManager", 
    "TextValueSchemaManager",
    "DecimalValueSchemaManager", 
    "DateValueSchemaManager",
    "DateTimeValueSchemaManager",
    "TimeValueSchemaManager",
    "AttachmentSchemaManager",
    "ValueSchemaManagerFactory",
    
    # API integration
    "register_value_endpoints",
    "register_domain_value_endpoints_api",
    
    # Error types
    "ValueErrorCode",
    "ValueNotFoundError",
    "ValueInvalidDataError",
    "ValueTypeMismatchError",
    "ValueValidationError",
    "ValueServiceError",
    "ValueRepositoryError",
]
