# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the queries module.

This module defines error types, error codes, and error catalog entries
specific to the queries functionality.
"""

from typing import Any, Optional, Dict, List, Union
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Query error codes
class QueryErrorCode:
    """Query-specific error codes."""
    
    # Query errors
    QUERY_NOT_FOUND = "QUERY-0001"
    QUERY_ALREADY_EXISTS = "QUERY-0002"
    QUERY_INVALID_DATA = "QUERY-0003"
    QUERY_EXECUTION_FAILED = "QUERY-0004"
    QUERY_VALIDATION_FAILED = "QUERY-0005"
    
    # Query path errors
    QUERY_PATH_NOT_FOUND = "QUERY-0101"
    QUERY_PATH_INVALID = "QUERY-0102"
    QUERY_PATH_SYNTAX_ERROR = "QUERY-0103"
    
    # Query value errors
    QUERY_VALUE_INVALID = "QUERY-0201"
    QUERY_VALUE_TYPE_MISMATCH = "QUERY-0202"
    
    # Filter errors
    FILTER_INVALID = "QUERY-0301"
    FILTER_COMPILATION_FAILED = "QUERY-0302"
    
    # Manager errors
    QUERY_MANAGER_ERROR = "QUERY-0901"
    

# Query-specific error types
class QueryNotFoundError(UnoError):
    """Error raised when a query is not found."""
    
    def __init__(
        self,
        query_id: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Query with ID {query_id} not found"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.QUERY_NOT_FOUND,
            query_id=query_id,
            **context
        )


class QueryInvalidDataError(UnoError):
    """Error raised when query data is invalid."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Invalid query data: {reason}"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.QUERY_INVALID_DATA,
            reason=reason,
            **context
        )


class QueryExecutionError(UnoError):
    """Error raised when query execution fails."""
    
    def __init__(
        self,
        reason: str,
        query_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if query_id:
            ctx["query_id"] = query_id
            
        message = message or f"Query execution failed: {reason}"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.QUERY_EXECUTION_FAILED,
            reason=reason,
            **ctx
        )


class QueryPathError(UnoError):
    """Error raised when there is an issue with a query path."""
    
    def __init__(
        self,
        reason: str,
        path_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if path_id:
            ctx["path_id"] = path_id
            
        message = message or f"Query path error: {reason}"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.QUERY_PATH_INVALID,
            reason=reason,
            **ctx
        )


class QueryValueError(UnoError):
    """Error raised when there is an issue with a query value."""
    
    def __init__(
        self,
        reason: str,
        value_id: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if value_id:
            ctx["value_id"] = value_id
            
        message = message or f"Query value error: {reason}"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.QUERY_VALUE_INVALID,
            reason=reason,
            **ctx
        )


class FilterError(UnoError):
    """Error raised when there is an issue with a filter."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Filter error: {reason}"
        super().__init__(
            message=message,
            error_code=QueryErrorCode.FILTER_INVALID,
            reason=reason,
            **context
        )


# Register query error codes in the catalog
def register_query_errors():
    """Register query-specific error codes in the error catalog."""
    
    # Query errors
    register_error(
        code=QueryErrorCode.QUERY_NOT_FOUND,
        message_template="Query with ID {query_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested query could not be found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=QueryErrorCode.QUERY_ALREADY_EXISTS,
        message_template="Query already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A query with these properties already exists",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=QueryErrorCode.QUERY_INVALID_DATA,
        message_template="Invalid query data: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query data is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=QueryErrorCode.QUERY_EXECUTION_FAILED,
        message_template="Query execution failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The query execution failed",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=QueryErrorCode.QUERY_VALIDATION_FAILED,
        message_template="Query validation failed: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query validation failed",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Query path errors
    register_error(
        code=QueryErrorCode.QUERY_PATH_NOT_FOUND,
        message_template="Query path with ID {path_id} not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested query path could not be found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=QueryErrorCode.QUERY_PATH_INVALID,
        message_template="Invalid query path: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query path is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=QueryErrorCode.QUERY_PATH_SYNTAX_ERROR,
        message_template="Query path syntax error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query path has a syntax error",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Query value errors
    register_error(
        code=QueryErrorCode.QUERY_VALUE_INVALID,
        message_template="Invalid query value: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query value is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=QueryErrorCode.QUERY_VALUE_TYPE_MISMATCH,
        message_template="Query value type mismatch: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The query value type does not match the expected type",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Filter errors
    register_error(
        code=QueryErrorCode.FILTER_INVALID,
        message_template="Invalid filter: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The filter is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=QueryErrorCode.FILTER_COMPILATION_FAILED,
        message_template="Filter compilation failed: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The filter compilation failed",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Manager errors
    register_error(
        code=QueryErrorCode.QUERY_MANAGER_ERROR,
        message_template="Query manager error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="An error occurred in the query manager",
        http_status_code=500,
        retry_allowed=True
    )