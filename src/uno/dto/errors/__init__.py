# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error handling for the DTO module.

This module provides error types and utilities for the DTO module.
"""

from typing import Dict, List, Any, Optional

from uno.core.base.error import BaseError
from uno.core.errors.catalog import ErrorCatalog


class SchemaErrorCode:
    """Error codes for schema-related errors."""
    SCHEMA_NOT_FOUND = "SCHEMA-0001"
    SCHEMA_ALREADY_EXISTS = "SCHEMA-0002"
    SCHEMA_INVALID = "SCHEMA-0003"
    SCHEMA_VALIDATION_ERROR = "SCHEMA-0004"
    SCHEMA_FIELD_MISSING = "SCHEMA-0005"
    SCHEMA_FIELD_TYPE_MISMATCH = "SCHEMA-0006"
    SCHEMA_CONVERSION_ERROR = "SCHEMA-0007"
    SCHEMA_SERIALIZATION_ERROR = "SCHEMA-0008"
    SCHEMA_DESERIALIZATION_ERROR = "SCHEMA-0009"


class SchemaNotFoundError(BaseError):
    """Error raised when a schema is not found."""
    def __init__(
        self, 
        schema_identifier: Any, 
        identifier_type: str = "id",
        **context: Any
    ):
        """
        Initialize a SchemaNotFoundError.
        
        Args:
            schema_identifier: The schema identifier
            identifier_type: The type of identifier (id, name, etc.)
            **context: Additional context information
        """
        message = f"Schema with {identifier_type} {schema_identifier} not found"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_NOT_FOUND,
            schema_identifier=schema_identifier,
            identifier_type=identifier_type,
            **context
        )


class SchemaAlreadyExistsError(BaseError):
    """Error raised when a schema already exists."""
    def __init__(
        self, 
        schema_name: str, 
        schema_version: str,
        **context: Any
    ):
        """
        Initialize a SchemaAlreadyExistsError.
        
        Args:
            schema_name: The schema name
            schema_version: The schema version
            **context: Additional context information
        """
        message = f"Schema with name {schema_name} and version {schema_version} already exists"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_ALREADY_EXISTS,
            schema_name=schema_name,
            schema_version=schema_version,
            **context
        )


class SchemaInvalidError(BaseError):
    """Error raised when a schema is invalid."""
    def __init__(
        self, 
        message: str,
        **context: Any
    ):
        """
        Initialize a SchemaInvalidError.
        
        Args:
            message: The error message
            **context: Additional context information
        """
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_INVALID,
            **context
        )


class SchemaValidationError(BaseError):
    """Error raised when data validation against a schema fails."""
    def __init__(
        self, 
        message: str,
        validation_errors: Optional[Dict[str, List[str]]] = None,
        **context: Any
    ):
        """
        Initialize a SchemaValidationError.
        
        Args:
            message: The error message
            validation_errors: Dictionary of validation errors by field name
            **context: Additional context information
        """
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_VALIDATION_ERROR,
            validation_errors=validation_errors or {},
            **context
        )


class SchemaFieldMissingError(BaseError):
    """Error raised when a required field is missing."""
    def __init__(
        self, 
        field_name: str,
        schema_id: Any = None,
        **context: Any
    ):
        """
        Initialize a SchemaFieldMissingError.
        
        Args:
            field_name: The name of the missing field
            schema_id: The schema ID
            **context: Additional context information
        """
        message = f"Required field {field_name} is missing"
        if schema_id:
            message = f"{message} in schema {schema_id}"
            
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_FIELD_MISSING,
            field_name=field_name,
            schema_id=schema_id,
            **context
        )


class SchemaFieldTypeMismatchError(BaseError):
    """Error raised when a field type doesn't match the expected type."""
    def __init__(
        self, 
        field_name: str,
        expected_type: str,
        actual_type: str,
        **context: Any
    ):
        """
        Initialize a SchemaFieldTypeMismatchError.
        
        Args:
            field_name: The name of the field
            expected_type: The expected field type
            actual_type: The actual field type
            **context: Additional context information
        """
        message = f"Field {field_name} has type {actual_type}, expected {expected_type}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_FIELD_TYPE_MISMATCH,
            field_name=field_name,
            expected_type=expected_type,
            actual_type=actual_type,
            **context
        )


class SchemaConversionError(BaseError):
    """Error raised when schema conversion fails."""
    def __init__(
        self, 
        message: str,
        source_format: Optional[str] = None,
        target_format: Optional[str] = None,
        **context: Any
    ):
        """
        Initialize a SchemaConversionError.
        
        Args:
            message: The error message
            source_format: The source schema format
            target_format: The target schema format
            **context: Additional context information
        """
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_CONVERSION_ERROR,
            source_format=source_format,
            target_format=target_format,
            **context
        )


class SchemaSerializationError(BaseError):
    """Error raised when schema serialization fails."""
    def __init__(
        self, 
        message: str,
        schema_id: Any = None,
        **context: Any
    ):
        """
        Initialize a SchemaSerializationError.
        
        Args:
            message: The error message
            schema_id: The schema ID
            **context: Additional context information
        """
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_SERIALIZATION_ERROR,
            schema_id=schema_id,
            **context
        )


class SchemaDeserializationError(BaseError):
    """Error raised when schema deserialization fails."""
    def __init__(
        self, 
        message: str,
        **context: Any
    ):
        """
        Initialize a SchemaDeserializationError.
        
        Args:
            message: The error message
            **context: Additional context information
        """
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_DESERIALIZATION_ERROR,
            **context
        )


def register_schema_errors() -> None:
    """Register schema errors with the error catalog."""
    from uno.core.errors.base import ErrorCategory, ErrorSeverity, ErrorInfo
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_NOT_FOUND,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_NOT_FOUND,
            message_template="Schema not found: {schema_identifier}",
            category=ErrorCategory.NOT_FOUND,
            severity=ErrorSeverity.ERROR,
            description="Error raised when a schema is not found",
            http_status_code=404,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_ALREADY_EXISTS,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_ALREADY_EXISTS,
            message_template="Schema already exists: {schema_name} {schema_version}",
            category=ErrorCategory.CONFLICT,
            severity=ErrorSeverity.ERROR,
            description="Error raised when a schema already exists",
            http_status_code=409,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_INVALID,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_INVALID,
            message_template="Invalid schema: {message}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when a schema is invalid",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_VALIDATION_ERROR,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_VALIDATION_ERROR,
            message_template="Schema validation error: {message}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when data validation against a schema fails",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_FIELD_MISSING,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_FIELD_MISSING,
            message_template="Field {field_name} is missing",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when a required field is missing",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_FIELD_TYPE_MISMATCH,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_FIELD_TYPE_MISMATCH,
            message_template="Field {field_name} has type {actual_type}, expected {expected_type}",
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when a field type doesn't match the expected type",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_CONVERSION_ERROR,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_CONVERSION_ERROR,
            message_template="Schema conversion error: {message}",
            category=ErrorCategory.SERIALIZATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when schema conversion fails",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_SERIALIZATION_ERROR,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_SERIALIZATION_ERROR,
            message_template="Schema serialization error: {message}",
            category=ErrorCategory.SERIALIZATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when schema serialization fails",
            http_status_code=400,
            retry_allowed=False
        )
    )
    
    ErrorCatalog.register(
        SchemaErrorCode.SCHEMA_DESERIALIZATION_ERROR,
        ErrorInfo(
            code=SchemaErrorCode.SCHEMA_DESERIALIZATION_ERROR,
            message_template="Schema deserialization error: {message}",
            category=ErrorCategory.SERIALIZATION,
            severity=ErrorSeverity.ERROR,
            description="Error raised when schema deserialization fails",
            http_status_code=400,
            retry_allowed=False
        )
    )