# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the reports module.

This module defines error types, error codes, and error catalog entries
specific to the reports functionality.
"""

from typing import Any, Dict, List, Optional, Union
from uno.core.base.error import BaseError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Report error codes
class ReportErrorCode:
    """Report-specific error codes."""

    # Template errors
    REPORT_TEMPLATE_NOT_FOUND = "REPORT-0001"
    REPORT_TEMPLATE_ALREADY_EXISTS = "REPORT-0002"
    REPORT_TEMPLATE_INVALID = "REPORT-0003"
    REPORT_TEMPLATE_CREATION_FAILED = "REPORT-0004"

    # Field errors
    REPORT_FIELD_NOT_FOUND = "REPORT-0101"
    REPORT_FIELD_INVALID = "REPORT-0102"
    REPORT_FIELD_TYPE_MISMATCH = "REPORT-0103"

    # Execution errors
    REPORT_EXECUTION_FAILED = "REPORT-0201"
    REPORT_EXECUTION_NOT_FOUND = "REPORT-0202"
    REPORT_EXECUTION_TIMEOUT = "REPORT-0203"
    REPORT_EXECUTION_CANCELLED = "REPORT-0204"

    # Output errors
    REPORT_OUTPUT_FAILED = "REPORT-0301"
    REPORT_OUTPUT_FORMAT_INVALID = "REPORT-0302"
    REPORT_OUTPUT_DELIVERY_FAILED = "REPORT-0303"

    # Trigger errors
    REPORT_TRIGGER_INVALID = "REPORT-0401"
    REPORT_TRIGGER_NOT_FOUND = "REPORT-0402"
    REPORT_TRIGGER_EXECUTION_FAILED = "REPORT-0403"

    # General errors
    REPORT_OPERATION_FAILED = "REPORT-0901"
    REPORT_VALIDATION_ERROR = "REPORT-0902"
    REPORT_PERMISSION_DENIED = "REPORT-0903"


# Generic Report Error class
class ReportError(BaseError):
    """Generic error for report operations."""

    def __init__(self, message: str, error_code: str, **context: Any):
        """
        Initialize a Report Error.

        Args:
            message: The error message
            error_code: The specific error code
            **context: Additional context information
        """
        super().__init__(message=message, error_code=error_code, **context)


# Template errors
class ReportTemplateNotFoundError(BaseError):
    """Error raised when a report template is not found."""

    def __init__(self, template_id: str, message: Optional[str] = None, **context: Any):
        message = message or f"Report template with ID {template_id} not found"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_TEMPLATE_NOT_FOUND,
            template_id=template_id,
            **context,
        )


class ReportTemplateAlreadyExistsError(BaseError):
    """Error raised when attempting to create a duplicate report template."""

    def __init__(self, name: str, message: Optional[str] = None, **context: Any):
        message = message or f"Report template with name '{name}' already exists"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_TEMPLATE_ALREADY_EXISTS,
            name=name,
            **context,
        )


class ReportTemplateInvalidError(BaseError):
    """Error raised when a report template is invalid."""

    def __init__(
        self,
        reason: str,
        template_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if template_id:
            ctx["template_id"] = template_id

        message = message or f"Invalid report template: {reason}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_TEMPLATE_INVALID,
            reason=reason,
            **ctx,
        )


# Field errors
class ReportFieldNotFoundError(BaseError):
    """Error raised when a report field is not found."""

    def __init__(self, field_id: str, message: Optional[str] = None, **context: Any):
        message = message or f"Report field with ID {field_id} not found"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_FIELD_NOT_FOUND,
            field_id=field_id,
            **context,
        )


class ReportFieldInvalidError(BaseError):
    """Error raised when a report field configuration is invalid."""

    def __init__(
        self,
        reason: str,
        field_id: Optional[str] = None,
        field_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if field_id:
            ctx["field_id"] = field_id
        if field_type:
            ctx["field_type"] = field_type

        message = message or f"Invalid report field: {reason}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_FIELD_INVALID,
            reason=reason,
            **ctx,
        )


# Execution errors
class ReportExecutionFailedError(BaseError):
    """Error raised when report execution fails."""

    def __init__(
        self,
        reason: str,
        execution_id: Optional[str] = None,
        template_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if execution_id:
            ctx["execution_id"] = execution_id
        if template_id:
            ctx["template_id"] = template_id

        message = message or f"Report execution failed: {reason}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_EXECUTION_FAILED,
            reason=reason,
            **ctx,
        )


class ReportExecutionNotFoundError(BaseError):
    """Error raised when a report execution is not found."""

    def __init__(
        self, execution_id: str, message: Optional[str] = None, **context: Any
    ):
        message = message or f"Report execution with ID {execution_id} not found"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_EXECUTION_NOT_FOUND,
            execution_id=execution_id,
            **context,
        )


# Output errors
class ReportOutputFormatInvalidError(BaseError):
    """Error raised when an output format is invalid."""

    def __init__(
        self,
        format: str,
        supported_formats: Optional[List[str]] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if supported_formats:
            ctx["supported_formats"] = supported_formats

        message = message or f"Invalid report output format: {format}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_OUTPUT_FORMAT_INVALID,
            format=format,
            **ctx,
        )


class ReportOutputDeliveryFailedError(BaseError):
    """Error raised when report delivery fails."""

    def __init__(
        self,
        reason: str,
        output_id: Optional[str] = None,
        execution_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if output_id:
            ctx["output_id"] = output_id
        if execution_id:
            ctx["execution_id"] = execution_id

        message = message or f"Report delivery failed: {reason}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_OUTPUT_DELIVERY_FAILED,
            reason=reason,
            **ctx,
        )


# Trigger errors
class ReportTriggerNotFoundError(BaseError):
    """Error raised when a report trigger is not found."""

    def __init__(self, trigger_id: str, message: Optional[str] = None, **context: Any):
        message = message or f"Report trigger with ID {trigger_id} not found"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_TRIGGER_NOT_FOUND,
            trigger_id=trigger_id,
            **context,
        )


class ReportTriggerInvalidError(BaseError):
    """Error raised when a report trigger configuration is invalid."""

    def __init__(
        self,
        reason: str,
        trigger_id: Optional[str] = None,
        trigger_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any,
    ):
        ctx = context.copy()
        if trigger_id:
            ctx["trigger_id"] = trigger_id
        if trigger_type:
            ctx["trigger_type"] = trigger_type

        message = message or f"Invalid report trigger: {reason}"
        super().__init__(
            message=message,
            error_code=ReportErrorCode.REPORT_TRIGGER_INVALID,
            reason=reason,
            **ctx,
        )


# Register error codes in the catalog
def register_report_errors():
    """Register report-specific error codes in the error catalog."""

    # Template errors
    register_error(
        code=ReportErrorCode.REPORT_TEMPLATE_NOT_FOUND,
        message_template="Report template with ID {template_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested report template could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_TEMPLATE_ALREADY_EXISTS,
        message_template="Report template with name '{name}' already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A template with this name already exists",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_TEMPLATE_INVALID,
        message_template="Invalid report template: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The report template is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_TEMPLATE_CREATION_FAILED,
        message_template="Failed to create report template: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The report template could not be created",
        http_status_code=500,
        retry_allowed=True,
    )

    # Field errors
    register_error(
        code=ReportErrorCode.REPORT_FIELD_NOT_FOUND,
        message_template="Report field with ID {field_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested field could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_FIELD_INVALID,
        message_template="Invalid report field: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The field configuration is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_FIELD_TYPE_MISMATCH,
        message_template="Field type mismatch: expected {expected_type}, got {actual_type}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The field type does not match the expected type",
        http_status_code=400,
        retry_allowed=True,
    )

    # Execution errors
    register_error(
        code=ReportErrorCode.REPORT_EXECUTION_FAILED,
        message_template="Report execution failed: {reason}",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The report execution failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_EXECUTION_NOT_FOUND,
        message_template="Report execution with ID {execution_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested execution could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_EXECUTION_TIMEOUT,
        message_template="Report execution timed out after {timeout_seconds} seconds",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The report execution timed out",
        http_status_code=504,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_EXECUTION_CANCELLED,
        message_template="Report execution was cancelled",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.INFO,
        description="The report execution was cancelled",
        http_status_code=200,
        retry_allowed=True,
    )

    # Output errors
    register_error(
        code=ReportErrorCode.REPORT_OUTPUT_FAILED,
        message_template="Report output generation failed: {reason}",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The report output generation failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_OUTPUT_FORMAT_INVALID,
        message_template="Invalid report output format: {format}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The requested output format is not supported",
        http_status_code=400,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_OUTPUT_DELIVERY_FAILED,
        message_template="Report delivery failed: {reason}",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The report delivery failed",
        http_status_code=500,
        retry_allowed=True,
    )

    # Trigger errors
    register_error(
        code=ReportErrorCode.REPORT_TRIGGER_INVALID,
        message_template="Invalid report trigger: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The trigger configuration is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_TRIGGER_NOT_FOUND,
        message_template="Report trigger with ID {trigger_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested trigger could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=ReportErrorCode.REPORT_TRIGGER_EXECUTION_FAILED,
        message_template="Report trigger execution failed: {reason}",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The trigger execution failed",
        http_status_code=500,
        retry_allowed=True,
    )

    # General errors
    register_error(
        code=ReportErrorCode.REPORT_OPERATION_FAILED,
        message_template="Report operation failed: {reason}",
        category=ErrorCategory.EXECUTION,
        severity=ErrorSeverity.ERROR,
        description="The report operation failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_VALIDATION_ERROR,
        message_template="Report validation error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The report validation failed",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=ReportErrorCode.REPORT_PERMISSION_DENIED,
        message_template="Permission denied for report operation: {operation}",
        category=ErrorCategory.SECURITY,
        severity=ErrorSeverity.ERROR,
        description="The user does not have permission for this operation",
        http_status_code=403,
        retry_allowed=False,
    )
