# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Core error definitions for the Uno framework.

This module defines error types, error codes, and error catalog entries
for core framework functionality that doesn't fit in other specific modules.
"""

from typing import Any, Dict, List, Optional, Union, Type
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Core error codes
class CoreErrorCode:
    """Core framework error codes."""
    
    # Configuration errors
    CONFIG_NOT_FOUND = "CORE-0001"
    CONFIG_INVALID = "CORE-0002"
    CONFIG_TYPE_MISMATCH = "CORE-0003"
    
    # Initialization errors
    INIT_FAILED = "CORE-0101"
    COMPONENT_INIT_FAILED = "CORE-0102"
    
    # Dependency errors
    DEPENDENCY_NOT_FOUND = "CORE-0201"
    DEPENDENCY_RESOLUTION_FAILED = "CORE-0202"
    DEPENDENCY_CYCLE = "CORE-0203"
    
    # Object errors
    OBJECT_NOT_FOUND = "CORE-0301"
    OBJECT_INVALID = "CORE-0302"
    OBJECT_PROPERTY_ERROR = "CORE-0303"
    
    # Serialization errors
    SERIALIZATION_ERROR = "CORE-0401"
    DESERIALIZATION_ERROR = "CORE-0402"
    
    # Protocol errors
    PROTOCOL_VALIDATION_FAILED = "CORE-0501"
    INTERFACE_METHOD_MISSING = "CORE-0502"
    
    # General errors
    OPERATION_FAILED = "CORE-0901"
    NOT_IMPLEMENTED = "CORE-0902"
    INTERNAL_ERROR = "CORE-0903"


# Configuration errors
class ConfigNotFoundError(UnoError):
    """Error raised when a configuration setting is not found."""
    
    def __init__(
        self,
        config_key: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Configuration setting '{config_key}' not found"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.CONFIG_NOT_FOUND,
            config_key=config_key,
            **context
        )


class ConfigInvalidError(UnoError):
    """Error raised when a configuration setting is invalid."""
    
    def __init__(
        self,
        config_key: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Invalid configuration setting '{config_key}': {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.CONFIG_INVALID,
            config_key=config_key,
            reason=reason,
            **context
        )


class ConfigTypeMismatchError(UnoError):
    """Error raised when a configuration setting has the wrong type."""
    
    def __init__(
        self,
        config_key: str,
        expected_type: Union[str, Type],
        actual_type: Union[str, Type],
        message: Optional[str] = None,
        **context: Any
    ):
        expected_type_str = expected_type.__name__ if isinstance(expected_type, type) else str(expected_type)
        actual_type_str = actual_type.__name__ if isinstance(actual_type, type) else str(actual_type)
        
        message = message or f"Configuration type mismatch for '{config_key}': expected {expected_type_str}, got {actual_type_str}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.CONFIG_TYPE_MISMATCH,
            config_key=config_key,
            expected_type=expected_type_str,
            actual_type=actual_type_str,
            **context
        )


# Initialization errors
class InitializationError(UnoError):
    """Error raised when framework initialization fails."""
    
    def __init__(
        self,
        reason: str,
        component: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if component:
            ctx["component"] = component
            
        message = message or f"Initialization failed: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.INIT_FAILED,
            reason=reason,
            **ctx
        )


class ComponentInitializationError(UnoError):
    """Error raised when a specific component fails to initialize."""
    
    def __init__(
        self,
        component: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Component '{component}' initialization failed: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.COMPONENT_INIT_FAILED,
            component=component,
            reason=reason,
            **context
        )


# Dependency errors
class DependencyNotFoundError(UnoError):
    """Error raised when a required dependency is not found."""
    
    def __init__(
        self,
        dependency_name: str,
        component: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if component:
            ctx["component"] = component
            
        message = message or f"Dependency '{dependency_name}' not found"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.DEPENDENCY_NOT_FOUND,
            dependency_name=dependency_name,
            **ctx
        )


class DependencyResolutionError(UnoError):
    """Error raised when dependency resolution fails."""
    
    def __init__(
        self,
        dependency_name: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Failed to resolve dependency '{dependency_name}': {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.DEPENDENCY_RESOLUTION_FAILED,
            dependency_name=dependency_name,
            reason=reason,
            **context
        )


class DependencyCycleError(UnoError):
    """Error raised when a dependency cycle is detected."""
    
    def __init__(
        self,
        cycle_components: List[str],
        message: Optional[str] = None,
        **context: Any
    ):
        cycle_str = " -> ".join(cycle_components)
        message = message or f"Dependency cycle detected: {cycle_str}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.DEPENDENCY_CYCLE,
            cycle_components=cycle_components,
            **context
        )


# Object errors
class ObjectNotFoundError(UnoError):
    """Error raised when an object is not found."""
    
    def __init__(
        self,
        object_type: str,
        object_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if object_id:
            ctx["object_id"] = object_id
            
        message = message or f"{object_type} not found"
        if object_id:
            message = f"{object_type} with ID '{object_id}' not found"
            
        super().__init__(
            message=message,
            error_code=CoreErrorCode.OBJECT_NOT_FOUND,
            object_type=object_type,
            **ctx
        )


class ObjectInvalidError(UnoError):
    """Error raised when an object is invalid."""
    
    def __init__(
        self,
        object_type: str,
        reason: str,
        object_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if object_id:
            ctx["object_id"] = object_id
            
        message = message or f"Invalid {object_type}: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.OBJECT_INVALID,
            object_type=object_type,
            reason=reason,
            **ctx
        )


class ObjectPropertyError(UnoError):
    """Error raised when there is an issue with an object property."""
    
    def __init__(
        self,
        object_type: str,
        property_name: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Error with {object_type} property '{property_name}': {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.OBJECT_PROPERTY_ERROR,
            object_type=object_type,
            property_name=property_name,
            reason=reason,
            **context
        )


# Serialization errors
class SerializationError(UnoError):
    """Error raised when object serialization fails."""
    
    def __init__(
        self,
        object_type: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Failed to serialize {object_type}: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.SERIALIZATION_ERROR,
            object_type=object_type,
            reason=reason,
            **context
        )


class DeserializationError(UnoError):
    """Error raised when object deserialization fails."""
    
    def __init__(
        self,
        object_type: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Failed to deserialize {object_type}: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.DESERIALIZATION_ERROR,
            object_type=object_type,
            reason=reason,
            **context
        )


# Protocol errors
class ProtocolValidationError(UnoError):
    """Error raised when protocol validation fails."""
    
    def __init__(
        self,
        protocol_name: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Protocol validation failed for '{protocol_name}': {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.PROTOCOL_VALIDATION_FAILED,
            protocol_name=protocol_name,
            reason=reason,
            **context
        )


class InterfaceMethodError(UnoError):
    """Error raised when a required interface method is missing."""
    
    def __init__(
        self,
        interface_name: str,
        method_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Required method '{method_name}' missing in interface '{interface_name}'"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.INTERFACE_METHOD_MISSING,
            interface_name=interface_name,
            method_name=method_name,
            **context
        )


# General errors
class OperationFailedError(UnoError):
    """Error raised when an operation fails."""
    
    def __init__(
        self,
        operation: str,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Operation '{operation}' failed: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.OPERATION_FAILED,
            operation=operation,
            reason=reason,
            **context
        )


class NotImplementedError(UnoError):
    """Error raised when a feature is not implemented."""
    
    def __init__(
        self,
        feature: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Feature '{feature}' is not implemented"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.NOT_IMPLEMENTED,
            feature=feature,
            **context
        )


class InternalError(UnoError):
    """Error raised when an internal error occurs."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Internal error: {reason}"
        super().__init__(
            message=message,
            error_code=CoreErrorCode.INTERNAL_ERROR,
            reason=reason,
            **context
        )


# Register core error codes in the catalog
def register_core_errors():
    """Register core-specific error codes in the error catalog."""
    
    # Configuration errors
    register_error(
        code=CoreErrorCode.CONFIG_NOT_FOUND,
        message_template="Configuration setting '{config_key}' not found",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="The requested configuration setting does not exist",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.CONFIG_INVALID,
        message_template="Invalid configuration setting '{config_key}': {reason}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="The configuration setting is invalid",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.CONFIG_TYPE_MISMATCH,
        message_template="Configuration type mismatch for '{config_key}': expected {expected_type}, got {actual_type}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="The configuration setting has the wrong type",
        http_status_code=500,
        retry_allowed=False
    )
    
    # Initialization errors
    register_error(
        code=CoreErrorCode.INIT_FAILED,
        message_template="Initialization failed: {reason}",
        category=ErrorCategory.INITIALIZATION,
        severity=ErrorSeverity.ERROR,
        description="The framework initialization failed",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=CoreErrorCode.COMPONENT_INIT_FAILED,
        message_template="Component '{component}' initialization failed: {reason}",
        category=ErrorCategory.INITIALIZATION,
        severity=ErrorSeverity.ERROR,
        description="A component failed to initialize",
        http_status_code=500,
        retry_allowed=True
    )
    
    # Dependency errors
    register_error(
        code=CoreErrorCode.DEPENDENCY_NOT_FOUND,
        message_template="Dependency '{dependency_name}' not found",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        description="A required dependency was not found",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.DEPENDENCY_RESOLUTION_FAILED,
        message_template="Failed to resolve dependency '{dependency_name}': {reason}",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        description="Failed to resolve a dependency",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.DEPENDENCY_CYCLE,
        message_template="Dependency cycle detected: {cycle_components}",
        category=ErrorCategory.DEPENDENCY,
        severity=ErrorSeverity.ERROR,
        description="A circular dependency was detected",
        http_status_code=500,
        retry_allowed=False
    )
    
    # Object errors
    register_error(
        code=CoreErrorCode.OBJECT_NOT_FOUND,
        message_template="{object_type} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested object was not found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.OBJECT_INVALID,
        message_template="Invalid {object_type}: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The object is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.OBJECT_PROPERTY_ERROR,
        message_template="Error with {object_type} property '{property_name}': {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with an object property",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Serialization errors
    register_error(
        code=CoreErrorCode.SERIALIZATION_ERROR,
        message_template="Failed to serialize {object_type}: {reason}",
        category=ErrorCategory.SERIALIZATION,
        severity=ErrorSeverity.ERROR,
        description="Failed to serialize an object",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=CoreErrorCode.DESERIALIZATION_ERROR,
        message_template="Failed to deserialize {object_type}: {reason}",
        category=ErrorCategory.SERIALIZATION,
        severity=ErrorSeverity.ERROR,
        description="Failed to deserialize an object",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Protocol errors
    register_error(
        code=CoreErrorCode.PROTOCOL_VALIDATION_FAILED,
        message_template="Protocol validation failed for '{protocol_name}': {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A protocol validation check failed",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.INTERFACE_METHOD_MISSING,
        message_template="Required method '{method_name}' missing in interface '{interface_name}'",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A required interface method is missing",
        http_status_code=500,
        retry_allowed=False
    )
    
    # General errors
    register_error(
        code=CoreErrorCode.OPERATION_FAILED,
        message_template="Operation '{operation}' failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An operation failed",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=CoreErrorCode.NOT_IMPLEMENTED,
        message_template="Feature '{feature}' is not implemented",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="A requested feature is not implemented",
        http_status_code=501,
        retry_allowed=False
    )
    
    register_error(
        code=CoreErrorCode.INTERNAL_ERROR,
        message_template="Internal error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An internal error occurred",
        http_status_code=500,
        retry_allowed=True
    )