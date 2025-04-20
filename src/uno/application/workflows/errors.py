# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the workflow module.

This module defines error types, error codes, and error catalog entries
specific to the workflow functionality.
"""

from uno.core.base.error import BaseError
from uno.core.errors.framework import ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Workflow error codes
class WorkflowErrorCode:
    """Workflow-specific error codes."""

    # Workflow definition errors
    WORKFLOW_NOT_FOUND = "WORKFLOW-0001"
    WORKFLOW_ALREADY_EXISTS = "WORKFLOW-0002"
    WORKFLOW_INVALID_DEFINITION = "WORKFLOW-0003"
    WORKFLOW_VERSION_CONFLICT = "WORKFLOW-0004"

    # Workflow execution errors
    WORKFLOW_EXECUTION_FAILED = "WORKFLOW-0101"
    WORKFLOW_CONDITION_FAILED = "WORKFLOW-0102"
    WORKFLOW_ACTION_FAILED = "WORKFLOW-0103"
    WORKFLOW_RECIPIENT_ERROR = "WORKFLOW-0104"
    WORKFLOW_RECIPIENT_INVALID = "WORKFLOW-0105"
    WORKFLOW_TRIGGER_INVALID = "WORKFLOW-0106"

    # Event integration errors
    WORKFLOW_EVENT_PROCESSING_FAILED = "WORKFLOW-0201"
    WORKFLOW_EVENT_LISTENER_FAILED = "WORKFLOW-0202"
    WORKFLOW_EVENT_INVALID = "WORKFLOW-0203"

    # Query integration errors
    WORKFLOW_QUERY_INTEGRATION_FAILED = "WORKFLOW-0301"
    WORKFLOW_QUERY_EXECUTION_FAILED = "WORKFLOW-0302"
    WORKFLOW_QUERY_INVALID = "WORKFLOW-0303"


# Workflow-specific error types
class WorkflowNotFoundError(BaseError):
    """Error raised when a workflow is not found."""

    def __init__(self, workflow_id: str, message: str | None = None, **context: Any):
        message = message or f"Workflow with ID {workflow_id} not found"
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_NOT_FOUND,
            workflow_id=workflow_id,
            **context,
        )


class WorkflowInvalidDefinitionError(BaseError):
    """Error raised when a workflow definition is invalid."""

    def __init__(
        self,
        reason: str,
        workflow_id: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        context_dict = context.copy()
        if workflow_id:
            context_dict["workflow_id"] = workflow_id

        message = message or f"Invalid workflow definition: {reason}"
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_INVALID_DEFINITION,
            reason=reason,
            **context_dict,
        )


class WorkflowExecutionError(BaseError):
    """Error raised when workflow execution fails."""

    def __init__(
        self,
        workflow_id: str,
        execution_id: str | None = None,
        reason: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        context_dict = context.copy()
        if execution_id:
            context_dict["execution_id"] = execution_id

        message = (
            message
            or f"Workflow execution failed: {reason if reason else 'unknown error'}"
        )
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_EXECUTION_FAILED,
            workflow_id=workflow_id,
            **context_dict,
        )


class WorkflowActionError(BaseError):
    """Error raised when a workflow action fails."""

    def __init__(
        self,
        action_id: str,
        workflow_id: str,
        execution_id: str | None = None,
        reason: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        context_dict = context.copy()
        if execution_id:
            context_dict["execution_id"] = execution_id

        message = (
            message
            or f"Workflow action failed: {reason if reason else 'unknown error'}"
        )
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_ACTION_FAILED,
            workflow_id=workflow_id,
            action_id=action_id,
            **context_dict,
        )


class WorkflowConditionError(BaseError):
    """Error raised when a workflow condition evaluation fails."""

    def __init__(
        self,
        condition_id: str | None = None,
        workflow_id: str | None = None,
        condition_type: str | None = None,
        reason: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        context_dict = context.copy()
        if condition_id:
            context_dict["condition_id"] = condition_id
        if workflow_id:
            context_dict["workflow_id"] = workflow_id
        if condition_type:
            context_dict["condition_type"] = condition_type

        message = (
            message
            or f"Workflow condition failed: {reason if reason else 'unknown error'}"
        )
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_CONDITION_FAILED,
            **context_dict,
        )


class WorkflowEventError(BaseError):
    """Error raised when workflow event processing fails."""

    def __init__(
        self,
        event_type: str,
        reason: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        message = (
            message
            or f"Workflow event processing failed: {reason if reason else 'unknown error'}"
        )
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_EVENT_PROCESSING_FAILED,
            event_type=event_type,
            **context,
        )


class WorkflowQueryError(BaseError):
    """Error raised when workflow query integration fails."""

    def __init__(
        self,
        query_id: str | None = None,
        reason: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        context_dict = context.copy()
        if query_id:
            context_dict["query_id"] = query_id

        message = (
            message
            or f"Workflow query integration failed: {reason if reason else 'unknown error'}"
        )
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_QUERY_INTEGRATION_FAILED,
            **context_dict,
        )


class WorkflowRecipientError(BaseError):
    """Error raised when there is an issue with workflow recipients."""

    def __init__(
        self,
        reason: str,
        recipient_type: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        message: str | None = None,
        **context: Any,
    ):
        ctx = context.copy()
        if recipient_type:
            ctx["recipient_type"] = recipient_type
        if workflow_id:
            ctx["workflow_id"] = workflow_id
        if execution_id:
            ctx["execution_id"] = execution_id

        message = message or f"Workflow recipient error: {reason}"
        super().__init__(
            message=message,
            error_code=WorkflowErrorCode.WORKFLOW_RECIPIENT_ERROR,
            reason=reason,
            **ctx,
        )


# Register workflow error codes in the catalog
def register_workflow_errors():
    """Register workflow-specific error codes in the error catalog."""

    # Workflow definition errors
    register_error(
        code=WorkflowErrorCode.WORKFLOW_NOT_FOUND,
        message_template="Workflow with ID {workflow_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested workflow could not be found",
        http_status_code=404,
        retry_allowed=False,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_ALREADY_EXISTS,
        message_template="Workflow with name '{name}' already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A workflow with this name already exists",
        http_status_code=409,
        retry_allowed=False,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_INVALID_DEFINITION,
        message_template="Invalid workflow definition: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow definition is invalid",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_VERSION_CONFLICT,
        message_template="Workflow version conflict: {message}",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The workflow version conflicts with the current state",
        http_status_code=409,
        retry_allowed=True,
    )

    # Workflow execution errors
    register_error(
        code=WorkflowErrorCode.WORKFLOW_EXECUTION_FAILED,
        message_template="Workflow execution failed: {message}",
        category=ErrorCategory.BUSINESS_RULE,
        severity=ErrorSeverity.ERROR,
        description="The workflow execution failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_CONDITION_FAILED,
        message_template="Workflow condition evaluation failed: {message}",
        category=ErrorCategory.BUSINESS_RULE,
        severity=ErrorSeverity.ERROR,
        description="The workflow condition evaluation failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_ACTION_FAILED,
        message_template="Workflow action failed: {message}",
        category=ErrorCategory.BUSINESS_RULE,
        severity=ErrorSeverity.ERROR,
        description="The workflow action execution failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_RECIPIENT_ERROR,
        message_template="Workflow recipient error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="There was an issue with workflow recipients",
        http_status_code=400,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_RECIPIENT_INVALID,
        message_template="Invalid workflow recipient: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow recipient is invalid",
        http_status_code=400,
        retry_allowed=False,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_TRIGGER_INVALID,
        message_template="Invalid workflow trigger: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow trigger is invalid",
        http_status_code=400,
        retry_allowed=False,
    )

    # Event integration errors
    register_error(
        code=WorkflowErrorCode.WORKFLOW_EVENT_PROCESSING_FAILED,
        message_template="Workflow event processing failed: {message}",
        category=ErrorCategory.INTEGRATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow event processing failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_EVENT_LISTENER_FAILED,
        message_template="Workflow event listener failed: {message}",
        category=ErrorCategory.INTEGRATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow event listener failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_EVENT_INVALID,
        message_template="Invalid workflow event: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow event is invalid",
        http_status_code=400,
        retry_allowed=False,
    )

    # Query integration errors
    register_error(
        code=WorkflowErrorCode.WORKFLOW_QUERY_INTEGRATION_FAILED,
        message_template="Workflow query integration failed: {message}",
        category=ErrorCategory.INTEGRATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow query integration failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_QUERY_EXECUTION_FAILED,
        message_template="Workflow query execution failed: {message}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The workflow query execution failed",
        http_status_code=500,
        retry_allowed=True,
    )

    register_error(
        code=WorkflowErrorCode.WORKFLOW_QUERY_INVALID,
        message_template="Invalid workflow query: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The workflow query is invalid",
        http_status_code=400,
        retry_allowed=False,
    )
