# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
DTO (Data Transfer Object) module for the Uno framework.

IMPORTANT: The primary DTO components have been moved to these standardized locations:
- Base DTO classes: uno.core.base.dto (BaseDTO, PaginatedListDTO, etc.)
- DTO Manager: uno.application.dto.manager (DTOManager)

This module is maintained for backward compatibility and schema-specific functionality.
For new code, please use the standardized imports above.

The DTO module has been redesigned to follow domain-driven design principles,
with clear separation of concerns into entities, repositories, services, and endpoints.
"""

# Import from core module for fundamental components
from uno.core.base.dto import (
    BaseDTO,
    DTOConfig,
    PaginatedListDTO,
    WithMetadataDTO,
)

# Import from application module for manager implementation
from uno.application.dto.manager import (
    DTOManager,
    get_dto_manager,
)

# Domain-driven design implementation
from uno.dto.entities import (
    SchemaId,
    SchemaDefinition,
    SchemaType,
    FieldDefinition,
    SchemaConfiguration,
    PaginatedResult,
    PaginationMetadata,
    SchemaCreationRequest,
    SchemaUpdateRequest,
    SchemaValidationRequest,
    ApiSchemaCreationRequest,
)

from uno.dto.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol,
    InMemorySchemaDefinitionRepository,
    InMemorySchemaConfigurationRepository,
    FileSchemaDefinitionRepository,
    FileSchemaConfigurationRepository,
)

from uno.dto.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol,
    SchemaManagerService,
    SchemaValidationService,
    SchemaTransformationService,
)

from uno.dto.domain_provider import SchemaProvider, TestingSchemaProvider
from uno.dto.domain_endpoints import router as schema_router

# Import error types for error handling
from uno.dto.errors import (
    SchemaErrorCode,
    SchemaNotFoundError,
    SchemaAlreadyExistsError,
    SchemaInvalidError,
    SchemaValidationError,
    SchemaFieldMissingError,
    SchemaFieldTypeMismatchError,
    SchemaConversionError,
    SchemaSerializationError,
    SchemaDeserializationError,
    register_schema_errors,
)

# No backward compatibility needed

# Register schema errors
register_schema_errors()

__all__ = [
    # Core DTO classes
    "BaseDTO",
    "DTOConfig",
    "PaginatedListDTO",
    "WithMetadataDTO",
    "DTOManager",
    "get_dto_manager",
    
    # Domain-driven design exports
    "SchemaId",
    "SchemaDefinition",
    "SchemaType",
    "FieldDefinition",
    "SchemaConfiguration",
    "PaginatedResult",
    "PaginationMetadata",
    "SchemaCreationRequest",
    "SchemaUpdateRequest",
    "SchemaValidationRequest",
    "ApiSchemaCreationRequest",
    "SchemaDefinitionRepositoryProtocol",
    "SchemaConfigurationRepositoryProtocol",
    "InMemorySchemaDefinitionRepository",
    "InMemorySchemaConfigurationRepository",
    "FileSchemaDefinitionRepository",
    "FileSchemaConfigurationRepository",
    "SchemaManagerServiceProtocol",
    "SchemaValidationServiceProtocol",
    "SchemaTransformationServiceProtocol",
    "SchemaManagerService",
    "SchemaValidationService",
    "SchemaTransformationService",
    "SchemaProvider",
    "TestingSchemaProvider",
    "schema_router",
    
    # Error types
    "SchemaErrorCode",
    "SchemaNotFoundError",
    "SchemaAlreadyExistsError",
    "SchemaInvalidError",
    "SchemaValidationError",
    "SchemaFieldMissingError",
    "SchemaFieldTypeMismatchError",
    "SchemaConversionError",
    "SchemaSerializationError",
    "SchemaDeserializationError",
]