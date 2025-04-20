# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the values module.

This module defines error types, error codes, and error catalog entries
specific to the values functionality.
"""

from typing import Any, Optional, Dict, List, Union
from uno.core.base.error import BaseError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Value error codes
class ValueErrorCode:
    """Value-specific error codes."""

    # Value errors
    VALUE_NOT_FOUND = "VALUE-0001"
    VALUE_ALREADY_EXISTS = "VALUE-0002"
    VALUE_INVALID_DATA = "VALUE-0003"
    VALUE_TYPE_MISMATCH = "VALUE-0004"
    VALUE_UPDATE_FAILED = "VALUE-0005"

    # Validation errors
    VALUE_VALIDATION_FAILED = "VALUE-0101"
    VALUE_REQUIRED = "VALUE-0102"
    VALUE_OUT_OF_RANGE = "VALUE-0103"
    VALUE_FORMAT_INVALID = "VALUE-0104"

    # Query errors
    VALUE_QUERY_FAILED = "VALUE-0201"

    # General errors
    VALUE_SERVICE_ERROR = "VALUE-0901"
    VALUE_REPOSITORY_ERROR = "VALUE-0902"


# Value-specific error types
class ValueNotFoundError(BaseError):
    """Error raised when a value is not found."""

    def __init__(
        self,
        value_id: str,
        value_type: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if value_type:
            ctx["value_type"] = value_type

        message = message or f"Value with ID {value_id} not found"
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_NOT_FOUND,
            value_id=value_id,
            **ctx,
        )


class ValueInvalidDataError(BaseError):
    """Error raised when value data is invalid."""

    def __init__(
        self,
        reason: str,
        value_type: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if value_type:
            ctx["value_type"] = value_type

        message = message or f"Invalid value data: {reason}"
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_INVALID_DATA,
            reason=reason,
            **ctx,
        )


class ValueTypeMismatchError(BaseError):
    """Error raised when value type doesn't match expected type."""

    def __init__(
        self,
        expected_type: str,
        actual_type: str,
        message: str | None = None,
        **context: Any,
    ):
        message = (
            message
            or f"Value type mismatch: expected {expected_type}, got {actual_type}"
        )
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_TYPE_MISMATCH,
            expected_type=expected_type,
            actual_type=actual_type,
            **context,
        )


class ValueValidationError(BaseError):
    """Error raised when value validation fails."""

    def __init__(
        self,
        reason: str,
        value: Any = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if value is not None:
            ctx["value"] = str(value)

        message = message or f"Value validation failed: {reason}"
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_VALIDATION_FAILED,
            reason=reason,
            **ctx,
        )


class ValueServiceError(BaseError):
    """Error raised when a value service operation fails."""

    def __init__(
        self,
        reason: str,
        operation: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation

        message = message or f"Value service error: {reason}"
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_SERVICE_ERROR,
            reason=reason,
            **ctx,
        )


class ValueRepositoryError(BaseError):
    """Error raised when a value repository operation fails."""

    def __init__(
        self,
        reason: str,
        operation: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if operation:
            ctx["operation"] = operation

        message = message or f"Value repository error: {reason}"
        super().__init__(
            message=message,
            error_code=ValueErrorCode.VALUE_REPOSITORY_ERROR,
            reason=reason,
            **ctx,
        )


# Register value error codes in the catalog
def register_value_errors():
    """Register value-specific error codes in the error catalog."""

    # Value errors
    register_error(
        code=ValueErrorCode.VALUE_NOT_FOUND,
        message_template="Value with ID {value_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested value could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=ValueErrorCode.VALUE_ALREADY_EXISTS,
        message_template="Value already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A value with these properties already exists",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=ValueErrorCode.VALUE_INVALID_DATA,
        message_template="Invalid value data: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value data is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ValueErrorCode.VALUE_TYPE_MISMATCH,
        message_template="Value type mismatch: expected {expected_type}, got {actual_type}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value type does not match the expected type",
        http_status_code=400,
        retry_allowed=False,
    )

    register_error(
        code=ValueErrorCode.VALUE_UPDATE_FAILED,
        message_template="Failed to update value: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to update the value",
        http_status_code=500,
        retry_allowed=True,
    )

    # Validation errors
    register_error(
        code=ValueErrorCode.VALUE_VALIDATION_FAILED,
        message_template="Value validation failed: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value failed validation",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ValueErrorCode.VALUE_REQUIRED,
        message_template="Value is required",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="A value is required but none was provided",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ValueErrorCode.VALUE_OUT_OF_RANGE,
        message_template="Value is out of range",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value is outside of the allowed range",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ValueErrorCode.VALUE_FORMAT_INVALID,
        message_template="Value format is invalid: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The value format is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    # Query errors
    register_error(
        code=ValueErrorCode.VALUE_QUERY_FAILED,
        message_template="Value query failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The value query failed",
        http_status_code=500,
        retry_allowed=True,
    )

    # General errors
    register_error(
        code=ValueErrorCode.VALUE_SERVICE_ERROR,
        message_template="Value service error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An error occurred in the value service",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=ValueErrorCode.VALUE_REPOSITORY_ERROR,
        message_template="Value repository error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An error occurred in the value repository",
        http_status_code=500,
        retry_allowed=True,
    )
