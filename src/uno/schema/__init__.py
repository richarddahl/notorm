# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema module for Uno framework.

This module provides utilities for creating, validating, and converting between
different schema formats, supporting the data layer of the application.

The Schema module has been redesigned to follow domain-driven design principles,
with clear separation of concerns into entities, repositories, services, and endpoints.
"""

# Domain-driven design implementation
from uno.schema.entities import (
    SchemaId, SchemaDefinition, SchemaType, FieldDefinition,
    SchemaConfiguration, PaginatedResult, PaginationMetadata,
    SchemaCreationRequest, SchemaUpdateRequest, SchemaValidationRequest,
    ApiSchemaCreationRequest
)

from uno.schema.domain_repositories import (
    SchemaDefinitionRepositoryProtocol,
    SchemaConfigurationRepositoryProtocol,
    InMemorySchemaDefinitionRepository,
    InMemorySchemaConfigurationRepository,
    FileSchemaDefinitionRepository, 
    FileSchemaConfigurationRepository
)

from uno.schema.domain_services import (
    SchemaManagerServiceProtocol,
    SchemaValidationServiceProtocol,
    SchemaTransformationServiceProtocol,
    SchemaManagerService,
    SchemaValidationService,
    SchemaTransformationService
)

from uno.schema.domain_provider import (
    SchemaProvider,
    TestingSchemaProvider
)

from uno.schema.domain_endpoints import router as schema_router

# Legacy implementation
from uno.schema.schema import (
    UnoSchema,
    UnoSchemaConfig,
    PaginatedList,
    WithMetadata,
)

from uno.schema.schema_manager import (
    UnoSchemaManager,
    get_schema_manager,
)

from uno.schema.services import (
    SchemaManagerService as LegacySchemaManagerService,
)

from uno.schema.errors import (
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

# Register schema errors
register_schema_errors()

__all__ = [
    # Domain-driven design exports
    "SchemaId", "SchemaDefinition", "SchemaType", "FieldDefinition",
    "SchemaConfiguration", "PaginatedResult", "PaginationMetadata",
    "SchemaCreationRequest", "SchemaUpdateRequest", "SchemaValidationRequest",
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
    
    # Legacy exports
    "UnoSchema",
    "UnoSchemaConfig",
    "PaginatedList",
    "WithMetadata",
    
    "UnoSchemaManager",
    "get_schema_manager",
    "LegacySchemaManagerService",
    
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