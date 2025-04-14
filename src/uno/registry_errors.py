# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the registry module.

This module defines error types, error codes, and error catalog entries
specific to the registry functionality.
"""

from typing import Any, Dict, List, Optional, Union, Type
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Registry error codes
class RegistryErrorCode:
    """Registry-specific error codes."""
    
    # Registration errors
    REGISTRY_DUPLICATE = "REG-0001"
    REGISTRY_INVALID_CLASS = "REG-0002"
    REGISTRY_MISSING_CLASS = "REG-0003"
    
    # Lookup errors
    REGISTRY_CLASS_NOT_FOUND = "REG-0101"
    REGISTRY_SCHEMA_NOT_FOUND = "REG-0102"
    
    # Configuration errors
    REGISTRY_CONFIG_ERROR = "REG-0201"
    
    # General errors
    REGISTRY_ERROR = "REG-0901"


# Registration errors
class RegistryDuplicateError(UnoError):
    """Error raised when attempting to register a duplicate class."""
    
    def __init__(
        self,
        class_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Class '{class_name}' is already registered"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_DUPLICATE,
            class_name=class_name,
            **context
        )


class RegistryInvalidClassError(UnoError):
    """Error raised when attempting to register an invalid class."""
    
    def __init__(
        self,
        class_name: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Invalid class '{class_name}': {reason}"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_INVALID_CLASS,
            class_name=class_name,
            reason=reason,
            **context
        )


class RegistryMissingClassError(UnoError):
    """Error raised when a required class is missing from the registry."""
    
    def __init__(
        self,
        class_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Required class '{class_name}' is not registered"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_MISSING_CLASS,
            class_name=class_name,
            **context
        )


# Lookup errors
class RegistryClassNotFoundError(UnoError):
    """Error raised when a class is not found in the registry."""
    
    def __init__(
        self,
        class_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Class '{class_name}' not found in registry"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_CLASS_NOT_FOUND,
            class_name=class_name,
            **context
        )


class RegistrySchemaNotFoundError(UnoError):
    """Error raised when a schema is not found in the registry."""
    
    def __init__(
        self,
        schema_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Schema '{schema_name}' not found in registry"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_SCHEMA_NOT_FOUND,
            schema_name=schema_name,
            **context
        )


# General errors
class RegistryError(UnoError):
    """General error for registry operations."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Registry error: {reason}"
        super().__init__(
            message=message,
            error_code=RegistryErrorCode.REGISTRY_ERROR,
            reason=reason,
            **context
        )


# Register registry error codes in the catalog
def register_registry_errors():
    """Register registry-specific error codes in the error catalog."""
    
    # Registration errors
    register_error(
        code=RegistryErrorCode.REGISTRY_DUPLICATE,
        message_template="Class '{class_name}' is already registered",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="Attempted to register a class that is already registered",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=RegistryErrorCode.REGISTRY_INVALID_CLASS,
        message_template="Invalid class '{class_name}': {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The class being registered is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=RegistryErrorCode.REGISTRY_MISSING_CLASS,
        message_template="Required class '{class_name}' is not registered",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A required class is missing from the registry",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Lookup errors
    register_error(
        code=RegistryErrorCode.REGISTRY_CLASS_NOT_FOUND,
        message_template="Class '{class_name}' not found in registry",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested class was not found in the registry",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=RegistryErrorCode.REGISTRY_SCHEMA_NOT_FOUND,
        message_template="Schema '{schema_name}' not found in registry",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested schema was not found in the registry",
        http_status_code=404,
        retry_allowed=False
    )
    
    # Configuration errors
    register_error(
        code=RegistryErrorCode.REGISTRY_CONFIG_ERROR,
        message_template="Registry configuration error: {reason}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the registry configuration",
        http_status_code=500,
        retry_allowed=False
    )
    
    # General errors
    register_error(
        code=RegistryErrorCode.REGISTRY_ERROR,
        message_template="Registry error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="A general registry error occurred",
        http_status_code=500,
        retry_allowed=True
    )