# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Error definitions for the database module.

This module defines error types, error codes, and error catalog entries
specific to the database functionality.
"""

from typing import Any, Dict, List, Optional, Union, Type
from uno.core.errors.base import UnoError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import register_error


# Database error codes
class DatabaseErrorCode:
    """Database-specific error codes."""
    
    # Connection errors
    DATABASE_CONNECTION_ERROR = "DB-0001"
    DATABASE_CONNECTION_TIMEOUT = "DB-0002"
    DATABASE_CONNECTION_POOL_EXHAUSTED = "DB-0003"
    
    # Query errors
    DATABASE_QUERY_ERROR = "DB-0101"
    DATABASE_QUERY_TIMEOUT = "DB-0102"
    DATABASE_QUERY_SYNTAX_ERROR = "DB-0103"
    
    # Transaction errors
    DATABASE_TRANSACTION_ERROR = "DB-0201"
    DATABASE_TRANSACTION_ROLLBACK = "DB-0202"
    DATABASE_TRANSACTION_CONFLICT = "DB-0203"
    
    # Data errors
    DATABASE_INTEGRITY_ERROR = "DB-0301"
    DATABASE_UNIQUE_VIOLATION = "DB-0302"
    DATABASE_FOREIGN_KEY_VIOLATION = "DB-0303"
    DATABASE_CHECK_VIOLATION = "DB-0304"
    DATABASE_NOT_NULL_VIOLATION = "DB-0305"
    
    # Resource errors
    DATABASE_RESOURCE_NOT_FOUND = "DB-0401"
    DATABASE_RESOURCE_ALREADY_EXISTS = "DB-0402"
    DATABASE_TABLE_NOT_FOUND = "DB-0403"
    DATABASE_COLUMN_NOT_FOUND = "DB-0404"
    
    # Session errors
    DATABASE_SESSION_ERROR = "DB-0501"
    DATABASE_SESSION_EXPIRED = "DB-0502"
    DATABASE_SESSION_INVALID = "DB-0503"
    
    # Configuration errors
    DATABASE_CONFIG_ERROR = "DB-0601"
    DATABASE_CONFIG_INVALID = "DB-0602"
    
    # Operational errors
    DATABASE_OPERATIONAL_ERROR = "DB-0701"
    DATABASE_NOT_SUPPORTED = "DB-0702"
    DATABASE_FEATURE_NOT_AVAILABLE = "DB-0703"
    
    # General errors
    DATABASE_ERROR = "DB-0901"


# Connection errors
class DatabaseConnectionError(UnoError):
    """Error raised when there is a database connection issue."""
    
    def __init__(
        self,
        reason: str,
        database: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if database:
            ctx["database"] = database
            
        message = message or f"Database connection error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_CONNECTION_ERROR,
            reason=reason,
            **ctx
        )


class DatabaseConnectionTimeoutError(UnoError):
    """Error raised when a database connection times out."""
    
    def __init__(
        self,
        timeout_seconds: Union[int, float],
        database: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if database:
            ctx["database"] = database
            
        message = message or f"Database connection timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_CONNECTION_TIMEOUT,
            timeout_seconds=timeout_seconds,
            **ctx
        )


class DatabaseConnectionPoolExhaustedError(UnoError):
    """Error raised when a connection pool is exhausted."""
    
    def __init__(
        self,
        pool_size: int,
        wait_seconds: Optional[Union[int, float]] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if wait_seconds is not None:
            ctx["wait_seconds"] = wait_seconds
            
        message = message or f"Database connection pool exhausted (size: {pool_size})"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_CONNECTION_POOL_EXHAUSTED,
            pool_size=pool_size,
            **ctx
        )


# Query errors
class DatabaseQueryError(UnoError):
    """Error raised when there is a database query issue."""
    
    def __init__(
        self,
        reason: str,
        query: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if query:
            # Truncate long queries for better readability
            ctx["query"] = query[:1000] + "..." if len(query) > 1000 else query
            
        message = message or f"Database query error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_QUERY_ERROR,
            reason=reason,
            **ctx
        )


class DatabaseQueryTimeoutError(UnoError):
    """Error raised when a database query times out."""
    
    def __init__(
        self,
        timeout_seconds: Union[int, float],
        query: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if query:
            # Truncate long queries for better readability
            ctx["query"] = query[:1000] + "..." if len(query) > 1000 else query
            
        message = message or f"Database query timed out after {timeout_seconds} seconds"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_QUERY_TIMEOUT,
            timeout_seconds=timeout_seconds,
            **ctx
        )


class DatabaseQuerySyntaxError(UnoError):
    """Error raised when a database query has a syntax error."""
    
    def __init__(
        self,
        reason: str,
        query: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if query:
            # Truncate long queries for better readability
            ctx["query"] = query[:1000] + "..." if len(query) > 1000 else query
            
        message = message or f"Database query syntax error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_QUERY_SYNTAX_ERROR,
            reason=reason,
            **ctx
        )


# Transaction errors
class DatabaseTransactionError(UnoError):
    """Error raised when there is a database transaction issue."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database transaction error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_TRANSACTION_ERROR,
            reason=reason,
            **context
        )


class DatabaseTransactionRollbackError(UnoError):
    """Error raised when a database transaction is rolled back."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database transaction rolled back: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_TRANSACTION_ROLLBACK,
            reason=reason,
            **context
        )


class DatabaseTransactionConflictError(UnoError):
    """Error raised when there is a database transaction conflict."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database transaction conflict: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_TRANSACTION_CONFLICT,
            reason=reason,
            **context
        )


# Data errors
class DatabaseIntegrityError(UnoError):
    """Error raised when there is a database integrity issue."""
    
    def __init__(
        self,
        reason: str,
        table_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if table_name:
            ctx["table_name"] = table_name
            
        message = message or f"Database integrity error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_INTEGRITY_ERROR,
            reason=reason,
            **ctx
        )


class DatabaseUniqueViolationError(UnoError):
    """Error raised when a unique constraint is violated."""
    
    def __init__(
        self,
        constraint_name: str,
        table_name: Optional[str] = None,
        column_names: Optional[List[str]] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if table_name:
            ctx["table_name"] = table_name
        if column_names:
            ctx["column_names"] = column_names
            
        message = message or f"Unique constraint violation: {constraint_name}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_UNIQUE_VIOLATION,
            constraint_name=constraint_name,
            **ctx
        )


class DatabaseForeignKeyViolationError(UnoError):
    """Error raised when a foreign key constraint is violated."""
    
    def __init__(
        self,
        constraint_name: str,
        table_name: Optional[str] = None,
        referenced_table: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if table_name:
            ctx["table_name"] = table_name
        if referenced_table:
            ctx["referenced_table"] = referenced_table
            
        message = message or f"Foreign key constraint violation: {constraint_name}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_FOREIGN_KEY_VIOLATION,
            constraint_name=constraint_name,
            **ctx
        )


# Resource errors
class DatabaseResourceNotFoundError(UnoError):
    """Error raised when a database resource is not found."""
    
    def __init__(
        self,
        resource_type: str,
        resource_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database resource not found: {resource_type} '{resource_name}'"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_RESOURCE_NOT_FOUND,
            resource_type=resource_type,
            resource_name=resource_name,
            **context
        )


class DatabaseResourceAlreadyExistsError(UnoError):
    """Error raised when a database resource already exists."""
    
    def __init__(
        self,
        resource_type: str,
        resource_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database resource already exists: {resource_type} '{resource_name}'"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_RESOURCE_ALREADY_EXISTS,
            resource_type=resource_type,
            resource_name=resource_name,
            **context
        )


class DatabaseTableNotFoundError(UnoError):
    """Error raised when a database table is not found."""
    
    def __init__(
        self,
        table_name: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database table not found: '{table_name}'"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_TABLE_NOT_FOUND,
            table_name=table_name,
            **context
        )


class DatabaseColumnNotFoundError(UnoError):
    """Error raised when a database column is not found."""
    
    def __init__(
        self,
        column_name: str,
        table_name: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if table_name:
            ctx["table_name"] = table_name
            
        message = message or f"Database column not found: '{column_name}'"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_COLUMN_NOT_FOUND,
            column_name=column_name,
            **ctx
        )


# Session errors
class DatabaseSessionError(UnoError):
    """Error raised when there is a database session issue."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database session error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_SESSION_ERROR,
            reason=reason,
            **context
        )


class DatabaseSessionExpiredError(UnoError):
    """Error raised when a database session has expired."""
    
    def __init__(
        self,
        reason: Optional[str] = None,
        message: Optional[str] = None,
        **context: Any
    ):
        ctx = context.copy()
        if reason:
            ctx["reason"] = reason
            
        message = message or "Database session has expired"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_SESSION_EXPIRED,
            **ctx
        )


# Configuration errors
class DatabaseConfigError(UnoError):
    """Error raised when there is a database configuration issue."""
    
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
            
        message = message or f"Database configuration error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_CONFIG_ERROR,
            reason=reason,
            **ctx
        )


# Operational errors
class DatabaseOperationalError(UnoError):
    """Error raised when there is a database operational issue."""
    
    def __init__(
        self,
        reason: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database operational error: {reason}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_OPERATIONAL_ERROR,
            reason=reason,
            **context
        )


class DatabaseNotSupportedError(UnoError):
    """Error raised when a database feature is not supported."""
    
    def __init__(
        self,
        feature: str,
        message: Optional[str] = None,
        **context: Any
    ):
        message = message or f"Database feature not supported: {feature}"
        super().__init__(
            message=message,
            error_code=DatabaseErrorCode.DATABASE_NOT_SUPPORTED,
            feature=feature,
            **context
        )


# Register database error codes in the catalog
def register_database_errors():
    """Register database-specific error codes in the error catalog."""
    
    # Connection errors
    register_error(
        code=DatabaseErrorCode.DATABASE_CONNECTION_ERROR,
        message_template="Database connection error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Failed to connect to the database",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_CONNECTION_TIMEOUT,
        message_template="Database connection timed out after {timeout_seconds} seconds",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Database connection timed out",
        http_status_code=504,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_CONNECTION_POOL_EXHAUSTED,
        message_template="Database connection pool exhausted (size: {pool_size})",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="All connections in the database pool are in use",
        http_status_code=503,
        retry_allowed=True
    )
    
    # Query errors
    register_error(
        code=DatabaseErrorCode.DATABASE_QUERY_ERROR,
        message_template="Database query error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Failed to execute the database query",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_QUERY_TIMEOUT,
        message_template="Database query timed out after {timeout_seconds} seconds",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Database query timed out",
        http_status_code=504,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_QUERY_SYNTAX_ERROR,
        message_template="Database query syntax error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The database query has a syntax error",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Transaction errors
    register_error(
        code=DatabaseErrorCode.DATABASE_TRANSACTION_ERROR,
        message_template="Database transaction error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="Failed to complete the database transaction",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_TRANSACTION_ROLLBACK,
        message_template="Database transaction rolled back: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The database transaction was rolled back",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_TRANSACTION_CONFLICT,
        message_template="Database transaction conflict: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="A conflict occurred during the database transaction",
        http_status_code=409,
        retry_allowed=True
    )
    
    # Data errors
    register_error(
        code=DatabaseErrorCode.DATABASE_INTEGRITY_ERROR,
        message_template="Database integrity error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The operation would violate database integrity constraints",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_UNIQUE_VIOLATION,
        message_template="Unique constraint violation: {constraint_name}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The operation would violate a unique constraint",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_FOREIGN_KEY_VIOLATION,
        message_template="Foreign key constraint violation: {constraint_name}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The operation would violate a foreign key constraint",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_CHECK_VIOLATION,
        message_template="Check constraint violation: {constraint_name}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The operation would violate a check constraint",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_NOT_NULL_VIOLATION,
        message_template="Not null constraint violation: {column_name}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The operation would violate a not null constraint",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Resource errors
    register_error(
        code=DatabaseErrorCode.DATABASE_RESOURCE_NOT_FOUND,
        message_template="Database resource not found: {resource_type} '{resource_name}'",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested database resource does not exist",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_RESOURCE_ALREADY_EXISTS,
        message_template="Database resource already exists: {resource_type} '{resource_name}'",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A database resource with this name already exists",
        http_status_code=409,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_TABLE_NOT_FOUND,
        message_template="Database table not found: '{table_name}'",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested database table does not exist",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_COLUMN_NOT_FOUND,
        message_template="Database column not found: '{column_name}'",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested database column does not exist",
        http_status_code=404,
        retry_allowed=False
    )
    
    # Session errors
    register_error(
        code=DatabaseErrorCode.DATABASE_SESSION_ERROR,
        message_template="Database session error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the database session",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_SESSION_EXPIRED,
        message_template="Database session has expired",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The database session has expired",
        http_status_code=401,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_SESSION_INVALID,
        message_template="Invalid database session: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="The database session is invalid",
        http_status_code=400,
        retry_allowed=True
    )
    
    # Configuration errors
    register_error(
        code=DatabaseErrorCode.DATABASE_CONFIG_ERROR,
        message_template="Database configuration error: {reason}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="There is an issue with the database configuration",
        http_status_code=500,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_CONFIG_INVALID,
        message_template="Invalid database configuration: {reason}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="The database configuration is invalid",
        http_status_code=400,
        retry_allowed=False
    )
    
    # Operational errors
    register_error(
        code=DatabaseErrorCode.DATABASE_OPERATIONAL_ERROR,
        message_template="Database operational error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="There is a database operational issue",
        http_status_code=500,
        retry_allowed=True
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_NOT_SUPPORTED,
        message_template="Database feature not supported: {feature}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="The requested database feature is not supported",
        http_status_code=400,
        retry_allowed=False
    )
    
    register_error(
        code=DatabaseErrorCode.DATABASE_FEATURE_NOT_AVAILABLE,
        message_template="Database feature not available: {feature}",
        category=ErrorCategory.CONFIGURATION,
        severity=ErrorSeverity.ERROR,
        description="The requested database feature is not available",
        http_status_code=501,
        retry_allowed=False
    )
    
    # General errors
    register_error(
        code=DatabaseErrorCode.DATABASE_ERROR,
        message_template="Database error: {reason}",
        category=ErrorCategory.DATABASE,
        severity=ErrorSeverity.ERROR,
        description="A database error occurred",
        http_status_code=500,
        retry_allowed=True
    )