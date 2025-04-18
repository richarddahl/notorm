# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the schema module.

This module defines error types, error codes, and error catalog entries
specific to the schema functionality.
"""

from typing import Any, Dict, List, Optional, Union, Type, Set
from uno.core.base.error import BaseError
from uno.core.errors.base import ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Schema error codes
class SchemaErrorCode:
    """Schema-specific error codes."""
    
    # Schema errors
    SCHEMA_NOT_FOUND = "SCHEMA-0001"
    SCHEMA_ALREADY_EXISTS = "SCHEMA-0002"
    SCHEMA_INVALID = "SCHEMA-0003"
    SCHEMA_REGISTRATION_FAILED = "SCHEMA-0004"
    
    # Validation errors
    SCHEMA_VALIDATION_FAILED = "SCHEMA-0101"
    SCHEMA_FIELD_MISSING = "SCHEMA-0102"
    SCHEMA_FIELD_TYPE_MISMATCH = "SCHEMA-0103"
    
    # Conversion errors
    SCHEMA_CONVERSION_FAILED = "SCHEMA-0201"
    SCHEMA_SERIALIZATION_FAILED = "SCHEMA-0202"
    SCHEMA_DESERIALIZATION_FAILED = "SCHEMA-0203"
    
    # General errors
    SCHEMA_OPERATION_FAILED = "SCHEMA-0901"


# Schema errors
class SchemaNotFoundError(BaseError):
    """Error raised when a schema is not found."""
    
    def __init__(
        self,
        schema_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Schema '{schema_name}' not found"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_NOT_FOUND,
            schema_name=schema_name,
            **context
        )


class SchemaAlreadyExistsError(BaseError):
    """Error raised when attempting to create a duplicate schema."""
    
    def __init__(
        self,
        schema_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Schema '{schema_name}' already exists"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_ALREADY_EXISTS,
            schema_name=schema_name,
            **context
        )


class SchemaInvalidError(BaseError):
    """Error raised when a schema is invalid."""
    
    def __init__(
        self,
        reason: str,
        schema_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if schema_name:
            ctx["schema_name"] = schema_name
            
        message = message or f"Invalid schema: {reason}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_INVALID,
            reason=reason,
            **ctx
        )


# Validation errors
class SchemaValidationError(BaseError):
    """Error raised when schema validation fails."""
    
    def __init__(
        self,
        reason: str,
        field_name: Optional[str] = None,
        schema_name: Optional[str] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if field_name:
            ctx["field_name"] = field_name
        if schema_name:
            ctx["schema_name"] = schema_name
        if validation_errors:
            ctx["validation_errors"] = validation_errors
            
        message = message or f"Schema validation failed: {reason}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_VALIDATION_FAILED,
            reason=reason,
            **ctx
        )


class SchemaFieldMissingError(BaseError):
    """Error raised when a required field is missing."""
    
    def __init__(
        self,
        field_name: str,
        schema_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if schema_name:
            ctx["schema_name"] = schema_name
            
        message = message or f"Required field '{field_name}' is missing"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_FIELD_MISSING,
            field_name=field_name,
            **ctx
        )


class SchemaFieldTypeMismatchError(BaseError):
    """Error raised when a field type doesn't match the expected type."""
    
    def __init__(
        self,
        field_name: str,
        expected_type: Union[str, Type],
        actual_type: Union[str, Type],
        schema_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if schema_name:
            ctx["schema_name"] = schema_name
            
        expected_type_str = expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
        actual_type_str = actual_type.__name__ if isinstance(actual_type, type) else str(actual_type)
        
        message = message or f"Field '{field_name}' type mismatch: expected {expected_type_str}, got {actual_type_str}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_FIELD_TYPE_MISMATCH,
            field_name=field_name,
            expected_type=expected_type_str,
            actual_type=actual_type_str,
            **ctx
        )


# Conversion errors
class SchemaConversionError(BaseError):
    """Error raised when schema conversion fails."""
    
    def __init__(
        self,
        reason: str,
        source_type: Optional[str] = None,
        target_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if source_type:
            ctx["source_type"] = source_type
        if target_type:
            ctx["target_type"] = target_type
            
        message = message or f"Schema conversion failed: {reason}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_CONVERSION_FAILED,
            reason=reason,
            **ctx
        )


class SchemaSerializationError(BaseError):
    """Error raised when schema serialization fails."""
    
    def __init__(
        self,
        reason: str,
        schema_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if schema_name:
            ctx["schema_name"] = schema_name
            
        message = message or f"Schema serialization failed: {reason}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_SERIALIZATION_FAILED,
            reason=reason,
            **ctx
        )


class SchemaDeserializationError(BaseError):
    """Error raised when schema deserialization fails."""
    
    def __init__(
        self,
        reason: str,
        schema_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if schema_name:
            ctx["schema_name"] = schema_name
            
        message = message or f"Schema deserialization failed: {reason}"
        super().__init__(
            message=message,
            error_code=SchemaErrorCode.SCHEMA_DESERIALIZATION_FAILED,
            reason=reason,
            **ctx
        )


# Register schema error codes in the catalog
def register_schema_errors():
    """Register schema-specific error codes in the error catalog."""
    
    # Schema errors
    register_error(
        code=SchemaErrorCode.SCHEMA_NOT_FOUND,
        message_template="Schema '{schema_name}' not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested schema could not be found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_ALREADY_EXISTS,
        message_template="Schema '{schema_name}' already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A schema with this name already exists",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_INVALID,
        message_template="Invalid schema: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The schema is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_REGISTRATION_FAILED,
        message_template="Failed to register schema: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="The schema could not be registered",
        http_status_code=500,
        retry_allowed=True
    )
    
    # Validation errors
    register_error(
        code=SchemaErrorCode.SCHEMA_VALIDATION_FAILED,
        message_template="Schema validation failed: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The data failed schema validation",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_FIELD_MISSING,
        message_template="Required field '{field_name}' is missing",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A required field is missing from the data",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_FIELD_TYPE_MISMATCH,
        message_template="Field '{field_name}' type mismatch: expected {expected_type}, got {actual_type}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A field has the wrong type",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Conversion errors
    register_error(
        code=SchemaErrorCode.SCHEMA_CONVERSION_FAILED,
        message_template="Schema conversion failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to convert between schema types",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_SERIALIZATION_FAILED,
        message_template="Schema serialization failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to serialize schema data",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SchemaErrorCode.SCHEMA_DESERIALIZATION_FAILED,
        message_template="Schema deserialization failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to deserialize schema data",
        http_status_code=400,
        retry_allowed=True
    )
    
    # General errors
    register_error(
        code=SchemaErrorCode.SCHEMA_OPERATION_FAILED,
        message_template="Schema operation failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="A schema operation failed",
        http_status_code=500,
        retry_allowed=True
    )