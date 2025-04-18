# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the attributes module.

This module defines error types, error codes, and error catalog entries
specific to the attributes functionality.
"""

from typing import Any, Optional, Dict, List
from uno.core.base.error import BaseError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Attribute error codes
class AttributeErrorCode:
    """Attribute-specific error codes."""

    # Attribute errors
    ATTRIBUTE_NOT_FOUND = "ATTRIBUTE-0001"
    ATTRIBUTE_ALREADY_EXISTS = "ATTRIBUTE-0002"
    ATTRIBUTE_INVALID_DATA = "ATTRIBUTE-0003"
    ATTRIBUTE_TYPE_MISMATCH = "ATTRIBUTE-0004"
    ATTRIBUTE_UPDATE_FAILED = "ATTRIBUTE-0005"

    # Attribute type errors
    ATTRIBUTE_TYPE_NOT_FOUND = "ATTRIBUTE-0101"
    ATTRIBUTE_TYPE_ALREADY_EXISTS = "ATTRIBUTE-0102"
    ATTRIBUTE_TYPE_INVALID_DATA = "ATTRIBUTE-0103"
    ATTRIBUTE_TYPE_IN_USE = "ATTRIBUTE-0104"
    ATTRIBUTE_TYPE_UPDATE_FAILED = "ATTRIBUTE-0105"

    # Value errors
    ATTRIBUTE_VALUE_INVALID = "ATTRIBUTE-0201"
    ATTRIBUTE_VALUE_REQUIRED = "ATTRIBUTE-0202"
    ATTRIBUTE_VALUE_NOT_ALLOWED = "ATTRIBUTE-0203"

    # Relationship errors
    ATTRIBUTE_RELATIONSHIP_INVALID = "ATTRIBUTE-0301"
    ATTRIBUTE_QUERY_FAILED = "ATTRIBUTE-0302"

    # General errors
    ATTRIBUTE_SERVICE_ERROR = "ATTRIBUTE-0901"
    ATTRIBUTE_TYPE_SERVICE_ERROR = "ATTRIBUTE-0902"


# Attribute-specific error types
class AttributeNotFoundError(BaseError):
    """Error raised when an attribute is not found."""

    def __init__(
        self, attribute_id: str, message: Optional[str] = None, **context: Any
    ):
        message = message or f"Attribute with ID {attribute_id} not found"
        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_NOT_FOUND,
            attribute_id=attribute_id,
            **context,
        )


class AttributeTypeNotFoundError(BaseError):
    """Error raised when an attribute type is not found."""

    def __init__(
        self, attribute_type_id: str, message: Optional[str] = None, **context: Any
    ):
        message = message or f"Attribute type with ID {attribute_type_id} not found"
        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_TYPE_NOT_FOUND,
            attribute_type_id=attribute_type_id,
            **context,
        )


class AttributeInvalidDataError(BaseError):
    """Error raised when attribute data is invalid."""

    def __init__(self, reason: str, message: Optional[str] = None, **context: Any):
        message = message or f"Invalid attribute data: {reason}"
        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_INVALID_DATA,
            reason=reason,
            **context,
        )


class AttributeTypeInvalidDataError(BaseError):
    """Error raised when attribute type data is invalid."""

    def __init__(self, reason: str, message: Optional[str] = None, **context: Any):
        message = message or f"Invalid attribute type data: {reason}"
        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_TYPE_INVALID_DATA,
            reason=reason,
            **context,
        )


class AttributeValueError(BaseError):
    """Error raised when attribute values are invalid."""

    def __init__(
        self,
        reason: str,
        attribute_id: Optional[str] = None,
        attribute_type_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        message = message or f"Invalid attribute value: {reason}"
        ctx = context.copy()
        if attribute_id:
            ctx["attribute_id"] = attribute_id
        if attribute_type_id:
            ctx["attribute_type_id"] = attribute_type_id

        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_VALUE_INVALID,
            reason=reason,
            **ctx,
        )


class AttributeServiceError(BaseError):
    """Error raised when an attribute service operation fails."""

    def __init__(
        self,
        reason: str,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        message = message or f"Attribute service error: {reason}"
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation

        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_SERVICE_ERROR,
            reason=reason,
            **ctx,
        )


class AttributeTypeServiceError(BaseError):
    """Error raised when an attribute type service operation fails."""

    def __init__(
        self,
        reason: str,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        message = message or f"Attribute type service error: {reason}"
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation

        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_TYPE_SERVICE_ERROR,
            reason=reason,
            **ctx,
        )


class AttributeValidationError(BaseError):
    """Error raised when attribute validation fails."""

    def __init__(
        self,
        reason: str,
        attribute_id: Optional[str] = None,
        attribute_type_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        message = message or f"Attribute validation failed: {reason}"
        ctx = context.copy()
        if attribute_id:
            ctx["attribute_id"] = attribute_id
        if attribute_type_id:
            ctx["attribute_type_id"] = attribute_type_id

        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_INVALID_DATA,
            reason=reason,
            **ctx,
        )


class AttributeGraphError(BaseError):
    """Error raised when an attribute graph operation fails."""

    def __init__(
        self,
        reason: str,
        operation: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        message = message or f"Attribute graph error: {reason}"
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation

        super().__init__(
            message=message,
            error_code=AttributeErrorCode.ATTRIBUTE_QUERY_FAILED,
            reason=reason,
            **ctx,
        )


# Register attribute error codes in the catalog
def register_attribute_errors():
    """Register attribute-specific error codes in the error catalog."""

    # Attribute errors
    register_error(
        code=AttributeErrorCode.ATTRIBUTE_NOT_FOUND,
        message_template="Attribute with ID {attribute_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested attribute could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_ALREADY_EXISTS,
        message_template="Attribute already exists for the given record and type",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="An attribute already exists for the given record and type",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_INVALID_DATA,
        message_template="Invalid attribute data: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The attribute data is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_MISMATCH,
        message_template="Attribute type mismatch: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The attribute type does not match the expected type",
        http_status_code=400,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_UPDATE_FAILED,
        message_template="Failed to update attribute: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to update the attribute",
        http_status_code=500,
        retry_allowed=True,
    )

    # Attribute type errors
    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_NOT_FOUND,
        message_template="Attribute type with ID {attribute_type_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested attribute type could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_ALREADY_EXISTS,
        message_template="Attribute type with name '{name}' already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="An attribute type with this name already exists",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_INVALID_DATA,
        message_template="Invalid attribute type data: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The attribute type data is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_IN_USE,
        message_template="Attribute type is in use and cannot be modified or deleted",
        category=ErrorCategory.BUSINESS_RULE,
        severity=ErrorSeverity.ERROR,
        description="The attribute type is in use and cannot be modified or deleted",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_UPDATE_FAILED,
        message_template="Failed to update attribute type: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to update the attribute type",
        http_status_code=500,
        retry_allowed=True,
    )

    # Value errors
    register_error(
        code=AttributeErrorCode.ATTRIBUTE_VALUE_INVALID,
        message_template="Invalid attribute value: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The attribute value is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_VALUE_REQUIRED,
        message_template="Attribute value is required",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A value is required for this attribute",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_VALUE_NOT_ALLOWED,
        message_template="Value type is not allowed for this attribute type",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value type is not allowed for this attribute type",
        http_status_code=400,
        retry_allowed=False,
    )

    # Relationship errors
    register_error(
        code=AttributeErrorCode.ATTRIBUTE_RELATIONSHIP_INVALID,
        message_template="Invalid attribute relationship: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The attribute relationship is invalid",
        http_status_code=400,
        retry_allowed=False,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_QUERY_FAILED,
        message_template="Attribute query failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The attribute query failed",
        http_status_code=500,
        retry_allowed=True,
    )

    # General errors
    register_error(
        code=AttributeErrorCode.ATTRIBUTE_SERVICE_ERROR,
        message_template="Attribute service error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An error occurred in the attribute service",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=AttributeErrorCode.ATTRIBUTE_TYPE_SERVICE_ERROR,
        message_template="Attribute type service error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An error occurred in the attribute type service",
        http_status_code=500,
        retry_allowed=True,
    )
