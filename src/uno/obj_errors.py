# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the UnoObj module.

This module defines error types, error codes, and error catalog entries
specific to the UnoObj component.
"""

from typing import Any, Dict, List, Optional, Union, Type
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# UnoObj error codes
class UnoObjErrorCode:
    """UnoObj-specific error codes."""
    
    # Object errors
    UNOOBJ_NOT_FOUND = "OBJ-0001"
    UNOOBJ_ALREADY_EXISTS = "OBJ-0002"
    UNOOBJ_INVALID = "OBJ-0003"
    UNOOBJ_CREATION_FAILED = "OBJ-0004"
    
    # Property errors
    UNOOBJ_PROPERTY_NOT_FOUND = "OBJ-0101"
    UNOOBJ_PROPERTY_INVALID = "OBJ-0102"
    UNOOBJ_PROPERTY_TYPE_MISMATCH = "OBJ-0103"
    
    # Schema errors
    UNOOBJ_SCHEMA_ERROR = "OBJ-0201"
    UNOOBJ_VALIDATION_FAILED = "OBJ-0202"
    
    # Conversion errors
    UNOOBJ_TO_MODEL_FAILED = "OBJ-0301"
    UNOOBJ_FROM_MODEL_FAILED = "OBJ-0302"
    
    # Operation errors
    UNOOBJ_OPERATION_FAILED = "OBJ-0401"
    UNOOBJ_PERSISTENCE_FAILED = "OBJ-0402"
    UNOOBJ_RELATIONSHIP_ERROR = "OBJ-0403"


# Object errors
class UnoObjNotFoundError(UnoError):
    """Error raised when a UnoObj is not found."""
    
    def __init__(
        self,
        obj_id: str,
        obj_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"{obj_type_str}Object with ID {obj_id} not found"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_NOT_FOUND,
            obj_id=obj_id,
            **ctx
        )


class UnoObjAlreadyExistsError(UnoError):
    """Error raised when a UnoObj already exists."""
    
    def __init__(
        self,
        obj_id: str,
        obj_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"{obj_type_str}Object with ID {obj_id} already exists"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_ALREADY_EXISTS,
            obj_id=obj_id,
            **ctx
        )


class UnoObjInvalidError(UnoError):
    """Error raised when a UnoObj is invalid."""
    
    def __init__(
        self,
        reason: str,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Invalid {obj_type_str}object: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_INVALID,
            reason=reason,
            **ctx
        )


# Property errors
class UnoObjPropertyNotFoundError(UnoError):
    """Error raised when a UnoObj property is not found."""
    
    def __init__(
        self,
        property_name: str,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Property '{property_name}' not found on {obj_type_str}object"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_PROPERTY_NOT_FOUND,
            property_name=property_name,
            **ctx
        )


class UnoObjPropertyInvalidError(UnoError):
    """Error raised when a UnoObj property is invalid."""
    
    def __init__(
        self,
        property_name: str,
        reason: str,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Invalid property '{property_name}' on {obj_type_str}object: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_PROPERTY_INVALID,
            property_name=property_name,
            reason=reason,
            **ctx
        )


# Schema errors
class UnoObjSchemaError(UnoError):
    """Error raised when there is an issue with a UnoObj schema."""
    
    def __init__(
        self,
        reason: str,
        obj_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Schema error for {obj_type_str}object: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_SCHEMA_ERROR,
            reason=reason,
            **ctx
        )


class UnoObjValidationError(UnoError):
    """Error raised when UnoObj validation fails."""
    
    def __init__(
        self,
        reason: str,
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
        if validation_errors:
            ctx["validation_errors"] = validation_errors
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Validation failed for {obj_type_str}object: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_VALIDATION_FAILED,
            reason=reason,
            **ctx
        )


# Conversion errors
class UnoObjToModelError(UnoError):
    """Error raised when converting a UnoObj to a model fails."""
    
    def __init__(
        self,
        reason: str,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Failed to convert {obj_type_str}object to model: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_TO_MODEL_FAILED,
            reason=reason,
            **ctx
        )


class UnoObjFromModelError(UnoError):
    """Error raised when creating a UnoObj from a model fails."""
    
    def __init__(
        self,
        reason: str,
        model_type: Optional[str] = None,
        model_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if model_type:
            ctx["model_type"] = model_type
        if model_id:
            ctx["model_id"] = model_id
            
        model_type_str = f"{model_type} " if model_type else ""
        message = message or f"Failed to create object from {model_type_str}model: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_FROM_MODEL_FAILED,
            reason=reason,
            **ctx
        )


# Operation errors
class UnoObjOperationError(UnoError):
    """Error raised when a UnoObj operation fails."""
    
    def __init__(
        self,
        operation: str,
        reason: str,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        message = message or f"Operation '{operation}' failed on {obj_type_str}object: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_OPERATION_FAILED,
            operation=operation,
            reason=reason,
            **ctx
        )


class UnoObjPersistenceError(UnoError):
    """Error raised when persisting a UnoObj fails."""
    
    def __init__(
        self,
        reason: str,
        operation: Optional[str] = None,
        obj_type: Optional[str] = None,
        obj_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation
        if obj_type:
            ctx["obj_type"] = obj_type
        if obj_id:
            ctx["obj_id"] = obj_id
            
        obj_type_str = f"{obj_type} " if obj_type else ""
        operation_str = f"during {operation}" if operation else ""
        message = message or f"Failed to persist {obj_type_str}object {operation_str}: {reason}"
        
        super().__init__(
            message=message,
            error_code=UnoObjErrorCode.UNOOBJ_PERSISTENCE_FAILED,
            reason=reason,
            **ctx
        )


# Register object error codes in the catalog
def register_unoobj_errors():
    """Register UnoObj-specific error codes in the error catalog."""
    
    # Object errors
    register_error(
        code=UnoObjErrorCode.UNOOBJ_NOT_FOUND,
        message_template="Object with ID {obj_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested UnoObj could not be found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_ALREADY_EXISTS,
        message_template="Object with ID {obj_id} already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A UnoObj with this ID already exists",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_INVALID,
        message_template="Invalid object: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The UnoObj is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_CREATION_FAILED,
        message_template="Failed to create object: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to create the UnoObj",
        http_status_code=500,
        retry_allowed=True
    )
    
    # Property errors
    register_error(
        code=UnoObjErrorCode.UNOOBJ_PROPERTY_NOT_FOUND,
        message_template="Property '{property_name}' not found on object",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The requested property was not found on the UnoObj",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_PROPERTY_INVALID,
        message_template="Invalid property '{property_name}' on object: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The property is invalid on the UnoObj",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_PROPERTY_TYPE_MISMATCH,
        message_template="Property '{property_name}' type mismatch: expected {expected_type}, got {actual_type}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The property type does not match the expected type",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Schema errors
    register_error(
        code=UnoObjErrorCode.UNOOBJ_SCHEMA_ERROR,
        message_template="Schema error for object: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the UnoObj schema",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_VALIDATION_FAILED,
        message_template="Validation failed for object: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The UnoObj validation failed",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Conversion errors
    register_error(
        code=UnoObjErrorCode.UNOOBJ_TO_MODEL_FAILED,
        message_template="Failed to convert object to model: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to convert a UnoObj to a model",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_FROM_MODEL_FAILED,
        message_template="Failed to create object from model: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to create a UnoObj from a model",
        http_status_code=500,
        retry_allowed=True
    )
    
    # Operation errors
    register_error(
        code=UnoObjErrorCode.UNOOBJ_OPERATION_FAILED,
        message_template="Operation '{operation}' failed on object: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="A UnoObj operation failed",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_PERSISTENCE_FAILED,
        message_template="Failed to persist object: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Failed to persist the UnoObj to the database",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=UnoObjErrorCode.UNOOBJ_RELATIONSHIP_ERROR,
        message_template="Relationship error on object: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with a UnoObj relationship",
        http_status_code=400,
        retry_allowed=False
    )