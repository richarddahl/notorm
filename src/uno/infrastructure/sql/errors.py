# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the SQL module.

This module defines error types, error codes, and error catalog entries
specific to the SQL functionality.
"""

from typing import Any, Dict, List, Optional, Union
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# SQL error codes
class SQLErrorCode:
    """SQL-specific error codes."""
    
    # SQL statement errors
    SQL_STATEMENT_INVALID = "SQL-0001"
    SQL_STATEMENT_EXECUTION_FAILED = "SQL-0002"
    SQL_STATEMENT_SYNTAX_ERROR = "SQL-0003"
    
    # SQL emitter errors
    SQL_EMITTER_ERROR = "SQL-0101"
    SQL_EMITTER_INVALID_CONFIG = "SQL-0102"
    SQL_EMITTER_ALREADY_APPLIED = "SQL-0103"
    
    # SQL registry errors
    SQL_REGISTRY_CLASS_NOT_FOUND = "SQL-0201"
    SQL_REGISTRY_CLASS_ALREADY_EXISTS = "SQL-0202"
    SQL_REGISTRY_INITIALIZATION_FAILED = "SQL-0203"
    
    # SQL configuration errors
    SQL_CONFIG_ERROR = "SQL-0301"
    SQL_CONFIG_INVALID = "SQL-0302"
    SQL_CONFIG_EXTENSION_MISSING = "SQL-0303"
    
    # SQL connection errors
    SQL_CONNECTION_ERROR = "SQL-0401"
    SQL_CONNECTION_TIMEOUT = "SQL-0402"
    SQL_CONNECTION_FAILED = "SQL-0403"
    
    # General errors
    SQL_OPERATION_FAILED = "SQL-0901"


# SQL statement errors
class SQLStatementError(UnoError):
    """Error raised when there is an issue with a SQL statement."""
    
    def __init__(
        self,
        reason: str,
        statement: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if statement:
            ctx["statement"] = statement
            
        message = message or f"SQL statement error: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_STATEMENT_INVALID,
            reason=reason,
            **ctx
        )


class SQLExecutionError(UnoError):
    """Error raised when SQL execution fails."""
    
    def __init__(
        self,
        reason: str,
        statement_type: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if statement_type:
            ctx["statement_type"] = statement_type
            
        message = message or f"SQL execution failed: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_STATEMENT_EXECUTION_FAILED,
            reason=reason,
            **ctx
        )


class SQLSyntaxError(UnoError):
    """Error raised when a SQL statement has a syntax error."""
    
    def __init__(
        self,
        reason: str,
        statement: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if statement:
            ctx["statement"] = statement
            
        message = message or f"SQL syntax error: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_STATEMENT_SYNTAX_ERROR,
            reason=reason,
            **ctx
        )


# SQL emitter errors
class SQLEmitterError(UnoError):
    """Error raised when there is an issue with a SQL emitter."""
    
    def __init__(
        self,
        reason: str,
        emitter: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if emitter:
            ctx["emitter"] = emitter
            
        message = message or f"SQL emitter error: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_EMITTER_ERROR,
            reason=reason,
            **ctx
        )


class SQLEmitterInvalidConfigError(UnoError):
    """Error raised when a SQL emitter has an invalid configuration."""
    
    def __init__(
        self,
        reason: str,
        emitter: Optional[str] = None,
        config_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if emitter:
            ctx["emitter"] = emitter
        if config_name:
            ctx["config_name"] = config_name
            
        message = message or f"Invalid SQL emitter configuration: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_EMITTER_INVALID_CONFIG,
            reason=reason,
            **ctx
        )


# SQL registry errors
class SQLRegistryClassNotFoundError(UnoError):
    """Error raised when a SQL registry class is not found."""
    
    def __init__(
        self,
        class_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"SQL registry class '{class_name}' not found"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_REGISTRY_CLASS_NOT_FOUND,
            class_name=class_name,
            **context
        )


class SQLRegistryClassAlreadyExistsError(UnoError):
    """Error raised when a SQL registry class already exists."""
    
    def __init__(
        self,
        class_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"SQL registry class '{class_name}' already exists"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_REGISTRY_CLASS_ALREADY_EXISTS,
            class_name=class_name,
            **context
        )


# SQL configuration errors
class SQLConfigError(UnoError):
    """Error raised when there is an issue with SQL configuration."""
    
    def __init__(
        self,
        reason: str,
        config_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if config_name:
            ctx["config_name"] = config_name
            
        message = message or f"SQL configuration error: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_CONFIG_ERROR,
            reason=reason,
            **ctx
        )


class SQLConfigInvalidError(UnoError):
    """Error raised when SQL configuration is invalid."""
    
    def __init__(
        self,
        reason: str,
        config_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if config_name:
            ctx["config_name"] = config_name
            
        message = message or f"Invalid SQL configuration: {reason}"
        super().__init__(
            message=message,
            error_code=SQLErrorCode.SQL_CONFIG_INVALID,
            reason=reason,
            **ctx
        )


# Register SQL error codes in the catalog
def register_sql_errors():
    """Register SQL-specific error codes in the error catalog."""
    
    # SQL statement errors
    register_error(
        code=SQLErrorCode.SQL_STATEMENT_INVALID,
        message_template="SQL statement error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the SQL statement",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_STATEMENT_EXECUTION_FAILED,
        message_template="SQL execution failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The SQL statement execution failed",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_STATEMENT_SYNTAX_ERROR,
        message_template="SQL syntax error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The SQL statement has a syntax error",
        http_status_code=400,
        retry_allowed=False
    )
    
    # SQL emitter errors
    register_error(
        code=SQLErrorCode.SQL_EMITTER_ERROR,
        message_template="SQL emitter error: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the SQL emitter",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_EMITTER_INVALID_CONFIG,
        message_template="Invalid SQL emitter configuration: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The SQL emitter configuration is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=SQLErrorCode.SQL_EMITTER_ALREADY_APPLIED,
        message_template="SQL emitter already applied: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.WARNING,
        description="The SQL emitter has already been applied",
        http_status_code=409,
        retry_allowed=False
    )
    
    # SQL registry errors
    register_error(
        code=SQLErrorCode.SQL_REGISTRY_CLASS_NOT_FOUND,
        message_template="SQL registry class '{class_name}' not found",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested SQL registry class does not exist",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=SQLErrorCode.SQL_REGISTRY_CLASS_ALREADY_EXISTS,
        message_template="SQL registry class '{class_name}' already exists",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A SQL registry class with this name already exists",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=SQLErrorCode.SQL_REGISTRY_INITIALIZATION_FAILED,
        message_template="SQL registry initialization failed: {reason}",
        category=ErrorCategory.INTERNAL,
        severity=ErrorSeverity.ERROR,
        description="Failed to initialize the SQL registry",
        http_status_code=500,
        retry_allowed=True
    )
    
    # SQL configuration errors
    register_error(
        code=SQLErrorCode.SQL_CONFIG_ERROR,
        message_template="SQL configuration error: {reason}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the SQL configuration",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_CONFIG_INVALID,
        message_template="Invalid SQL configuration: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The SQL configuration is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=SQLErrorCode.SQL_CONFIG_EXTENSION_MISSING,
        message_template="SQL extension missing: {extension}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="A required SQL extension is missing",
        http_status_code=500,
        retry_allowed=False
    )
    
    # SQL connection errors
    register_error(
        code=SQLErrorCode.SQL_CONNECTION_ERROR,
        message_template="SQL connection error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the SQL connection",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_CONNECTION_TIMEOUT,
        message_template="SQL connection timeout: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The SQL connection timed out",
        http_status_code=504,
        retry_allowed=True
    )
    
    register_error(
        code=SQLErrorCode.SQL_CONNECTION_FAILED,
        message_template="SQL connection failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Failed to establish a SQL connection",
        http_status_code=500,
        retry_allowed=True
    )
    
    # General errors
    register_error(
        code=SQLErrorCode.SQL_OPERATION_FAILED,
        message_template="SQL operation failed: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="A SQL operation failed",
        http_status_code=500,
        retry_allowed=True
    )