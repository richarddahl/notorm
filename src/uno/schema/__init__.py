# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Schema module for Uno framework.

This module provides utilities for creating, validating, and converting between
different schema formats, supporting the data layer of the application.
"""

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
    SchemaManagerService,
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
    # Schema classes
    "UnoSchema",
    "UnoSchemaConfig",
    "PaginatedList",
    "WithMetadata",
    
    # Schema management
    "UnoSchemaManager",
    "get_schema_manager",
    "SchemaManagerService",
    
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