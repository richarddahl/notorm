"""
Integration tests for error handling.

These tests verify the error handling system works properly across components,
including error propagation, error context, and the Result pattern.
"""

import pytest
import asyncio
import logging
from typing import Any, Dict, List, Optional, Tuple, Union, cast
import uuid
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text
from sqlalchemy.exc import IntegrityError, NoResultFound

from uno.database.session import async_session
from uno.database.errors import (
    DatabaseErrorCode,
    DatabaseQueryError,
    DatabaseIntegrityError,
    DatabaseTransactionError,
    DatabaseResourceNotFoundError,
    DatabaseUniqueViolationError
)
from uno.core.errors.base import (
    UnoError,
    ErrorCategory,
    ErrorSeverity,
    ErrorCode,
    with_error_context,
    with_async_error_context,
    add_error_context
)
from uno.core.errors.catalog import register_error, get_error_code_info
from uno.core.errors.result import (
    Result,
    Success,
    Failure,
    from_exception,
    from_awaitable,
    combine,
    combine_dict
)
from uno.core.errors.core_errors import (
    ResourceNotFoundError,
    ValidationError,
    AuthorizationError,
    ConfigurationError
)
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
async def setup_test_tables():
    """Create test tables for error handling testing."""
    async with async_session() as session:
        # Create a test_errors table
        await session.execute(text("""
        CREATE TABLE IF NOT EXISTS test_errors (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            value INTEGER NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """))
        
        # Create a test_error_logs table for testing error logging
        await session.execute(text("""
        CREATE TABLE IF NOT EXISTS test_error_logs (
            id SERIAL PRIMARY KEY,
            error_code TEXT NOT NULL,
            message TEXT NOT NULL,
            context JSONB,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
        """))
        
        # Commit the schema changes
        await session.commit()


@pytest.fixture(scope="function")
async def clean_test_tables():
    """Clean test tables before each test."""
    async with async_session() as session:
        await session.execute(text("DELETE FROM test_error_logs"))
        await session.execute(text("DELETE FROM test_errors"))
        await session.commit()


@pytest.fixture(scope="module")
def test_error_code():
    """Register a test error code for testing."""
    TEST_ERROR_CODE = "TEST-1001"
    
    # Register the error code
    register_error(
        code=TEST_ERROR_CODE,
        message_template="Test error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="Error for testing",
        http_status_code=400,
        retry_allowed=False
    )
    
    return TEST_ERROR_CODE


@pytest.fixture(scope="module")
def test_api_app():
    """Create a FastAPI app for testing error handling in API endpoints."""
    app = FastAPI()
    
    # Error types to test
    class TestAppError(UnoError):
        """Test application error."""
        
        def __init__(self, message: str, reason: str, **context: Any):
            context_dict = context.copy()
            context_dict["reason"] = reason
            super().__init__(
                message=message,
                error_code="TEST-2001",
                **context_dict
            )
    
    # Register API-specific error
    register_error(
        code="TEST-2001",
        message_template="API Test error: {reason}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="API Error for testing",
        http_status_code=400,
        retry_allowed=False
    )
    
    # API exception handler
    @app.exception_handler(UnoError)
    async def uno_exception_handler(request, exc: UnoError):
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=exc.http_status_code,
            content=exc.to_dict()
        )
    
    # Test API routes
    @app.get("/api/test_error")
    async def test_error():
        raise TestAppError(
            message="Test API error",
            reason="This is a test error",
            user_id="test_user"
        )
    
    @app.get("/api/test_not_found")
    async def test_not_found():
        raise ResourceNotFoundError(
            resource_type="TestResource",
            resource_id="test123"
        )
    
    @app.get("/api/test_validation")
    async def test_validation():
        raise ValidationError(
            message="Validation failed",
            field="test_field",
            value="invalid_value"
        )
    
    @app.get("/api/test_result_success")
    async def test_result_success():
        result: Result[Dict[str, Any]] = Success({"status": "success", "data": "test"})
        if result.is_success and result.value:
            return result.value
        else:
            # Should never reach here in this test
            raise HTTPException(status_code=500, detail="Unexpected error")
    
    @app.get("/api/test_result_failure")
    async def test_result_failure():
        error = ValidationError(
            message="Validation failed in result",
            field="test_field",
            value="invalid_value"
        )
        result: Result[Dict[str, Any]] = Failure(error)
        if result.is_success and result.value:
            return result.value
        else:
            # Convert failure to UnoError and raise it
            if isinstance(result.error, UnoError):
                raise result.error
            else:
                raise HTTPException(
                    status_code=500, 
                    detail=f"Error: {str(result.error)}"
                )
    
    return app


@pytest.fixture(scope="module")
def test_client(test_api_app):
    """Create a test client for the FastAPI app."""
    return TestClient(test_api_app)


@pytest.mark.integration
class TestErrorHandling:
    """Integration tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_database_error_propagation(self, setup_test_tables, clean_test_tables):
        """Test that database errors are properly propagated and contain correct information."""
        # Test that unique constraint violations are properly handled
        async with async_session() as session:
            # Insert a record
            await session.execute(
                text("INSERT INTO test_errors (name, value) VALUES (:name, :value)"),
                {"name": "test1", "value": 100}
            )
            await session.commit()
            
            # Try to insert a duplicate record
            try:
                await session.execute(
                    text("INSERT INTO test_errors (name, value) VALUES (:name, :value)"),
                    {"name": "test1", "value": 200}
                )
                await session.commit()
                assert False, "Should have raised an exception"
            except Exception as e:
                # Verify we get the correct error type
                assert isinstance(e, IntegrityError), "Should be an IntegrityError"
                
                # Now let's see how our error system handles this
                try:
                    # Attempt to convert to our error framework
                    raise DatabaseUniqueViolationError(
                        constraint_name="test_errors_name_key",
                        table_name="test_errors",
                        column_names=["name"]
                    ) from e
                except DatabaseUniqueViolationError as ue:
                    # Verify error properties
                    assert ue.error_code == DatabaseErrorCode.DATABASE_UNIQUE_VIOLATION
                    assert "constraint_name" in ue.context
                    assert ue.context["constraint_name"] == "test_errors_name_key"
                    assert ue.http_status_code == 409
    
    @pytest.mark.asyncio
    async def test_error_context_propagation(self, test_error_code):
        """Test that error context is properly propagated through the call stack."""
        # Function with explicit error context
        @with_error_context
        def function_with_context(user_id: str, action: str):
            # This will automatically add user_id and action to the error context
            raise UnoError(
                message="Test error with context",
                error_code=test_error_code
            )
        
        # Function with manual error context
        def function_with_manual_context():
            add_error_context(source="manual_context")
            raise UnoError(
                message="Test error with manual context",
                error_code=test_error_code
            )
        
        # Nested function calls with context
        @with_error_context
        def outer_function(user_id: str):
            return inner_function(user_id)
        
        @with_error_context
        def inner_function(user_id: str):
            raise UnoError(
                message="Nested error with context",
                error_code=test_error_code
            )
        
        # Test explicit context parameters
        try:
            function_with_context(user_id="test123", action="create")
            assert False, "Should have raised an exception"
        except UnoError as e:
            assert e.context.get("user_id") == "test123"
            assert e.context.get("action") == "create"
        
        # Test manual context
        try:
            function_with_manual_context()
            assert False, "Should have raised an exception"
        except UnoError as e:
            assert e.context.get("source") == "manual_context"
        
        # Test nested context
        try:
            outer_function(user_id="nested123")
            assert False, "Should have raised an exception"
        except UnoError as e:
            assert e.context.get("user_id") == "nested123"
    
    @pytest.mark.asyncio
    async def test_async_error_context(self):
        """Test that error context works with async functions."""
        # Async function with error context
        @with_async_error_context
        async def async_function_with_context(user_id: str):
            await asyncio.sleep(0.1)  # Simulate async operation
            raise UnoError(
                message="Async error with context",
                error_code=ErrorCode.INTERNAL_ERROR
            )
        
        # Test async context manager
        async def test_async_context_manager():
            async with with_async_error_context(operation="test_operation"):
                await asyncio.sleep(0.1)  # Simulate async operation
                raise UnoError(
                    message="Async context manager error",
                    error_code=ErrorCode.INTERNAL_ERROR
                )
        
        # Test async function decorator
        try:
            await async_function_with_context(user_id="async123")
            assert False, "Should have raised an exception"
        except UnoError as e:
            assert e.context.get("user_id") == "async123"
        
        # Test async context manager
        try:
            await test_async_context_manager()
            assert False, "Should have raised an exception"
        except UnoError as e:
            assert e.context.get("operation") == "test_operation"
    
    @pytest.mark.asyncio
    async def test_result_pattern(self):
        """Test the Result pattern for functional error handling."""
        # Function that returns a Success
        @from_exception
        def get_success_result():
            return "success"
        
        # Function that returns a Failure
        @from_exception
        def get_failure_result():
            raise ValueError("Test failure")
        
        # Async function with Result
        async def async_result_success():
            return await from_awaitable(asyncio.sleep(0.1, result="async success"))
        
        async def async_result_failure():
            await asyncio.sleep(0.1)
            raise ValueError("Async failure")
        
        # Test success result
        result1 = get_success_result()
        assert result1.is_success
        assert not result1.is_failure
        assert result1.value == "success"
        
        # Test failure result
        result2 = get_failure_result()
        assert not result2.is_success
        assert result2.is_failure
        assert isinstance(result2.error, ValueError)
        assert str(result2.error) == "Test failure"
        
        # Test async success
        result3 = await async_result_success()
        assert result3.is_success
        assert result3.value == "async success"
        
        # Test async failure
        result4 = await from_awaitable(async_result_failure())
        assert result4.is_failure
        assert isinstance(result4.error, ValueError)
        assert str(result4.error) == "Async failure"
        
        # Test result mapping
        result5 = result1.map(lambda x: x.upper())
        assert result5.is_success
        assert result5.value == "SUCCESS"
        
        # Test chain of operations
        result6 = (
            result1
            .map(lambda x: x.upper())
            .flat_map(lambda x: Success(f"{x}!"))
        )
        assert result6.is_success
        assert result6.value == "SUCCESS!"
        
        # Test failure short-circuits
        result7 = (
            result2
            .map(lambda x: x.upper())  # Should not be called
            .flat_map(lambda x: Success(f"{x}!"))  # Should not be called
        )
        assert result7.is_failure
        assert isinstance(result7.error, ValueError)
    
    @pytest.mark.asyncio
    async def test_result_combination(self):
        """Test combining multiple results."""
        # Create several results
        result1: Result[int] = Success(1)
        result2: Result[int] = Success(2)
        result3: Result[int] = Success(3)
        result4: Result[int] = Failure(ValueError("Test failure"))
        
        # Combine successful results
        combined1 = combine([result1, result2, result3])
        assert combined1.is_success
        assert combined1.value == [1, 2, 3]
        
        # Combine with a failure
        combined2 = combine([result1, result4, result3])
        assert combined2.is_failure
        assert isinstance(combined2.error, ValueError)
        
        # Combine dictionaries
        result_dict1: Dict[str, Result[int]] = {
            "a": Success(1),
            "b": Success(2),
            "c": Success(3)
        }
        combined_dict1 = combine_dict(result_dict1)
        assert combined_dict1.is_success
        assert combined_dict1.value == {"a": 1, "b": 2, "c": 3}
        
        # Combine dictionaries with a failure
        result_dict2: Dict[str, Result[int]] = {
            "a": Success(1),
            "b": Failure(ValueError("Dict failure")),
            "c": Success(3)
        }
        combined_dict2 = combine_dict(result_dict2)
        assert combined_dict2.is_failure
        assert isinstance(combined_dict2.error, ValueError)
        assert str(combined_dict2.error) == "Dict failure"
    
    @pytest.mark.asyncio
    async def test_result_with_database(self, setup_test_tables, clean_test_tables):
        """Test using the Result pattern with database operations."""
        # Function that performs a database operation and returns a Result
        async def create_record(name: str, value: int) -> Result[int]:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        text("INSERT INTO test_errors (name, value) VALUES (:name, :value) RETURNING id"),
                        {"name": name, "value": value}
                    )
                    record_id = (await result.fetchone())[0]
                    await session.commit()
                    return Success(record_id)
            except IntegrityError as e:
                return Failure(DatabaseUniqueViolationError(
                    constraint_name="test_errors_name_key",
                    table_name="test_errors",
                    column_names=["name"]
                ))
            except Exception as e:
                return Failure(e)
        
        # Function that retrieves a record
        async def get_record(record_id: int) -> Result[Dict[str, Any]]:
            try:
                async with async_session() as session:
                    result = await session.execute(
                        text("SELECT id, name, value FROM test_errors WHERE id = :id"),
                        {"id": record_id}
                    )
                    row = await result.fetchone()
                    if row is None:
                        return Failure(DatabaseResourceNotFoundError(
                            resource_type="record",
                            resource_name=str(record_id)
                        ))
                    return Success({
                        "id": row[0],
                        "name": row[1],
                        "value": row[2]
                    })
            except Exception as e:
                return Failure(e)
        
        # Test successful creation
        result1 = await create_record("test_result_1", 100)
        assert result1.is_success
        assert isinstance(result1.value, int)
        
        # Test retrieving the record
        result2 = await get_record(result1.value)
        assert result2.is_success
        assert result2.value["name"] == "test_result_1"
        assert result2.value["value"] == 100
        
        # Test unique constraint violation
        result3 = await create_record("test_result_1", 200)  # Same name, should fail
        assert result3.is_failure
        assert isinstance(result3.error, DatabaseUniqueViolationError)
        
        # Test not found
        result4 = await get_record(9999)  # Non-existent ID
        assert result4.is_failure
        assert isinstance(result4.error, DatabaseResourceNotFoundError)
        
        # Test chaining database operations
        async def create_and_get(name: str, value: int) -> Result[Dict[str, Any]]:
            result = await create_record(name, value)
            if result.is_failure:
                return result
            return await get_record(result.value)
        
        result5 = await create_and_get("test_result_2", 300)
        assert result5.is_success
        assert result5.value["name"] == "test_result_2"
        assert result5.value["value"] == 300
    
    def test_api_error_handling(self, test_client):
        """Test error handling in API endpoints."""
        # Test basic error
        response = test_client.get("/api/test_error")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "TEST-2001"
        assert "user_id" in data["context"]
        assert data["context"]["user_id"] == "test_user"
        
        # Test not found error
        response = test_client.get("/api/test_not_found")
        assert response.status_code == 404
        data = response.json()
        assert data["error_code"] == ErrorCode.RESOURCE_NOT_FOUND
        assert data["context"]["resource_type"] == "TestResource"
        
        # Test validation error
        response = test_client.get("/api/test_validation")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == ErrorCode.VALIDATION_ERROR
        assert data["context"]["field"] == "test_field"
        
        # Test Result success
        response = test_client.get("/api/test_result_success")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        
        # Test Result failure
        response = test_client.get("/api/test_result_failure")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == ErrorCode.VALIDATION_ERROR
        assert data["context"]["field"] == "test_field"


class TestErrorLogging:
    """Tests for error logging functionality."""
    
    @pytest.mark.asyncio
    async def test_error_logging_to_database(self, setup_test_tables, clean_test_tables):
        """Test logging errors to the database."""
        # Create an error logger
        class DatabaseErrorLogger:
            """Error logger that stores errors in the database."""
            
            async def log_error(self, error: UnoError):
                """Log an error to the database."""
                async with async_session() as session:
                    # Convert context to JSON
                    context_json = json.dumps(error.context)
                    
                    # Insert the error log
                    await session.execute(
                        text("""
                        INSERT INTO test_error_logs (error_code, message, context)
                        VALUES (:error_code, :message, :context)
                        """),
                        {
                            "error_code": error.error_code,
                            "message": error.message,
                            "context": context_json
                        }
                    )
                    await session.commit()
        
        # Create the logger
        error_logger = DatabaseErrorLogger()
        
        # Create and log some errors
        error1 = ValidationError(
            message="Test validation error",
            field="test_field",
            value="invalid_value"
        )
        await error_logger.log_error(error1)
        
        error2 = ResourceNotFoundError(
            resource_type="TestResource",
            resource_id="test123"
        )
        await error_logger.log_error(error2)
        
        # Verify the errors were logged
        async with async_session() as session:
            result = await session.execute(
                text("SELECT error_code, message FROM test_error_logs ORDER BY id")
            )
            rows = await result.fetchall()
            
            assert len(rows) == 2
            assert rows[0][0] == ErrorCode.VALIDATION_ERROR
            assert "Test validation error" in rows[0][1]
            assert rows[1][0] == ErrorCode.RESOURCE_NOT_FOUND
            assert "TestResource" in rows[1][1]
            
            # Check context was properly stored
            result = await session.execute(
                text("SELECT context FROM test_error_logs WHERE error_code = :code"),
                {"code": ErrorCode.VALIDATION_ERROR}
            )
            context_json = (await result.fetchone())[0]
            context = json.loads(context_json)
            
            assert context["field"] == "test_field"
            assert context["value"] == "invalid_value"


if __name__ == "__main__":
    # For manual running of tests
    pytest.main(["-xvs", __file__])