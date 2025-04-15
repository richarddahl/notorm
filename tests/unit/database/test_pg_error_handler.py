# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""Tests for PostgreSQL error handling."""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock

from uno.database.pg_error_handler import (
    extract_pg_error_details,
    extract_pg_error_code,
    map_pg_exception_to_uno_error,
    handle_pg_error,
    with_pg_error_handling,
    is_deadlock_error,
    is_serialization_error,
    is_constraint_violation,
    is_connection_error,
    is_transient_error,
    get_retry_delay_for_error,
    PostgresErrorCode,
)
from uno.database.errors import (
    DatabaseErrorCode,
    DatabaseConnectionError,
    DatabaseTransactionConflictError,
    DatabaseUniqueViolationError,
    DatabaseForeignKeyViolationError,
    DatabaseTableNotFoundError,
    DatabaseColumnNotFoundError,
    DatabaseQueryError,
)
from uno.core.errors.base import UnoError


class MockPgException(Exception):
    """Mock PostgreSQL exception for testing."""
    
    def __init__(self, message: str, pgcode: str = None):
        self.pgcode = pgcode
        super().__init__(message)


def test_extract_pg_error_details():
    """Test extraction of details from PostgreSQL error messages."""
    # Test constraint name extraction
    error_message = 'duplicate key value violates unique constraint "users_email_key"'
    details = extract_pg_error_details(error_message)
    assert details["constraint_name"] == "users_email_key"
    
    # Test relation/table name extraction
    error_message = 'relation "users" does not exist'
    details = extract_pg_error_details(error_message)
    assert details["table_name"] == "users"
    
    # Test column name extraction
    error_message = 'column "emails" does not exist'
    details = extract_pg_error_details(error_message)
    assert details["column_name"] == "emails"
    
    # Test detail extraction
    error_message = 'ERROR: duplicate key value violates unique constraint\nDETAIL: Key (email)=(user@example.com) already exists.'
    details = extract_pg_error_details(error_message)
    assert details["detail"] == "Key (email)=(user@example.com) already exists."
    
    # Test multi-pattern extraction
    error_message = 'relation "users" does not exist, column "email" in table "users"'
    details = extract_pg_error_details(error_message)
    assert details["table_name"] == "users"
    assert details["column_name"] == "email"


def test_extract_pg_error_code():
    """Test extraction of PostgreSQL error code from exceptions."""
    # Test direct pgcode attribute
    ex = MockPgException("connection failed", pgcode=PostgresErrorCode.CONNECTION_FAILURE)
    assert extract_pg_error_code(ex) == PostgresErrorCode.CONNECTION_FAILURE
    
    # Test nested exception
    inner_ex = MockPgException("inner error", pgcode=PostgresErrorCode.UNIQUE_VIOLATION)
    ex = Exception("outer error")
    ex.__cause__ = inner_ex
    assert extract_pg_error_code(ex) == PostgresErrorCode.UNIQUE_VIOLATION
    
    # Test fallback extraction from message
    ex = Exception("ERROR: sqlstate: 40P01: deadlock detected")
    assert extract_pg_error_code(ex) == "40P01"
    
    # Test no error code
    ex = Exception("some other error")
    assert extract_pg_error_code(ex) is None


def test_map_pg_exception_to_uno_error():
    """Test mapping PostgreSQL exceptions to Uno error types."""
    # Test unique violation mapping
    ex = MockPgException(
        'duplicate key value violates unique constraint "users_email_key"',
        pgcode=PostgresErrorCode.UNIQUE_VIOLATION
    )
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseUniqueViolationError)
    assert error.context.get("constraint_name") == "users_email_key"
    
    # Test foreign key violation mapping
    ex = MockPgException(
        'insert or update on table "orders" violates foreign key constraint "orders_user_id_fkey"',
        pgcode=PostgresErrorCode.FOREIGN_KEY_VIOLATION
    )
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseForeignKeyViolationError)
    assert error.context.get("constraint_name") == "orders_user_id_fkey"
    assert error.context.get("table_name") == "orders"
    
    # Test table not found mapping
    ex = MockPgException(
        'relation "non_existent_table" does not exist',
        pgcode=PostgresErrorCode.UNDEFINED_TABLE
    )
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseTableNotFoundError)
    assert error.context.get("table_name") == "non_existent_table"
    
    # Test column not found mapping
    ex = MockPgException(
        'column "non_existent_column" of relation "users" does not exist',
        pgcode=PostgresErrorCode.UNDEFINED_COLUMN
    )
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseColumnNotFoundError)
    assert error.context.get("column_name") == "non_existent_column"
    assert error.context.get("table_name") == "users"
    
    # Test deadlock detection
    ex = MockPgException(
        'deadlock detected',
        pgcode=PostgresErrorCode.DEADLOCK_DETECTED
    )
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseTransactionConflictError)
    assert "Deadlock detected" in error.message
    
    # Test additional context
    ex = MockPgException(
        'connection failed',
        pgcode=PostgresErrorCode.CONNECTION_FAILURE
    )
    error = map_pg_exception_to_uno_error(ex, database="test_db")
    assert isinstance(error, DatabaseConnectionError)
    assert error.context.get("database") == "test_db"
    
    # Test default case
    ex = Exception("some unknown error")
    error = map_pg_exception_to_uno_error(ex)
    assert isinstance(error, DatabaseQueryError)


@pytest.mark.asyncio
async def test_handle_pg_error():
    """Test async error handling for PostgreSQL errors."""
    # Test successful case
    async def success_func():
        return "success"
    
    result = await handle_pg_error(success_func)
    assert result == "success"
    
    # Test UnoError passthrough
    async def uno_error_func():
        raise DatabaseQueryError(reason="Test UnoError")
    
    with pytest.raises(DatabaseQueryError) as excinfo:
        await handle_pg_error(uno_error_func)
    assert "Test UnoError" in str(excinfo.value)
    
    # Test PostgreSQL error mapping
    async def pg_error_func():
        raise MockPgException(
            'duplicate key value violates unique constraint "users_email_key"',
            pgcode=PostgresErrorCode.UNIQUE_VIOLATION
        )
    
    with pytest.raises(DatabaseUniqueViolationError) as excinfo:
        await handle_pg_error(pg_error_func)
    assert "users_email_key" in str(excinfo.value)
    
    # Test custom error message
    async def generic_error_func():
        raise Exception("Some database error")
    
    with pytest.raises(DatabaseQueryError) as excinfo:
        await handle_pg_error(generic_error_func, error_message="Custom error message")
    assert "Custom error message" in str(excinfo.value)


@pytest.mark.asyncio
async def test_with_pg_error_handling_decorator():
    """Test the decorator for PostgreSQL error handling."""
    # Define a function with the decorator
    @with_pg_error_handling(error_message="Operation failed")
    async def decorated_function(value):
        if value == "error":
            raise MockPgException(
                'deadlock detected',
                pgcode=PostgresErrorCode.DEADLOCK_DETECTED
            )
        return f"Success: {value}"
    
    # Test successful case
    result = await decorated_function("test")
    assert result == "Success: test"
    
    # Test error case
    with pytest.raises(DatabaseTransactionConflictError) as excinfo:
        await decorated_function("error")
    assert "Operation failed" in str(excinfo.value)


def test_error_type_check_functions():
    """Test functions that check error types."""
    # Test deadlock error check
    ex = MockPgException("deadlock detected", pgcode=PostgresErrorCode.DEADLOCK_DETECTED)
    assert is_deadlock_error(ex) is True
    
    # Test serialization error check
    ex = MockPgException("serialization failure", pgcode=PostgresErrorCode.SERIALIZATION_FAILURE)
    assert is_serialization_error(ex) is True
    
    # Test constraint violation check
    ex = MockPgException("unique violation", pgcode=PostgresErrorCode.UNIQUE_VIOLATION)
    assert is_constraint_violation(ex) is True
    
    ex = MockPgException("foreign key violation", pgcode=PostgresErrorCode.FOREIGN_KEY_VIOLATION)
    assert is_constraint_violation(ex) is True
    
    # Test connection error check
    ex = MockPgException("connection failure", pgcode=PostgresErrorCode.CONNECTION_FAILURE)
    assert is_connection_error(ex) is True
    
    # Test transient error check
    ex = MockPgException("deadlock detected", pgcode=PostgresErrorCode.DEADLOCK_DETECTED)
    assert is_transient_error(ex) is True
    
    ex = MockPgException("connection failure", pgcode=PostgresErrorCode.CONNECTION_FAILURE)
    assert is_transient_error(ex) is True
    
    ex = MockPgException("syntax error", pgcode=PostgresErrorCode.SYNTAX_ERROR)
    assert is_transient_error(ex) is False


def test_get_retry_delay_for_error():
    """Test getting appropriate retry delays for different error types."""
    # Test deadlock error
    ex = MockPgException("deadlock detected", pgcode=PostgresErrorCode.DEADLOCK_DETECTED)
    assert get_retry_delay_for_error(ex) == 0.1
    
    # Test serialization error
    ex = MockPgException("serialization failure", pgcode=PostgresErrorCode.SERIALIZATION_FAILURE)
    assert get_retry_delay_for_error(ex) == 0.2
    
    # Test connection error
    ex = MockPgException("connection failure", pgcode=PostgresErrorCode.CONNECTION_FAILURE)
    assert get_retry_delay_for_error(ex) == 1.0
    
    # Test other error
    ex = MockPgException("syntax error", pgcode=PostgresErrorCode.SYNTAX_ERROR)
    assert get_retry_delay_for_error(ex) == 0.5