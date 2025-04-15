# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example usage of the Uno error handling system.

This module provides examples of using the error handling system in various scenarios.
It demonstrates how to use UnoError, context, and the Result pattern.
"""

from typing import Dict, List, Any, Optional
import random
from fastapi import APIRouter, Depends, Query, Path

from uno.core.errors.base import (
    UnoError, ErrorCode, with_error_context, with_async_error_context,
    ValidationError, EntityNotFoundError, AuthorizationError
)
from uno.core.result import Success, Failure, from_exception

# Create a FastAPI router for example error handling endpoints
router = APIRouter(prefix="/examples/errors", tags=["Error Examples"])


# Basic example endpoint that demonstrates UnoError usage
@router.get("/basic/{error_type}")
async def basic_error_example(
    error_type: str = Path(..., description="Type of error to demonstrate"),
    message: Optional[str] = Query(None, description="Custom error message")
):
    """
    Demonstrate basic error handling with UnoError.
    
    Available error types:
    - validation
    - authorization
    - not_found
    - internal
    - custom
    """
    default_message = "This is a demonstration error"
    error_message = message or default_message
    
    if error_type == "validation":
        raise ValidationError(
            message=error_message,
            field="example_field",
            value="invalid_value"
        )
    elif error_type == "authorization":
        raise AuthorizationError(
            message=error_message,
            permission="EXAMPLE_PERMISSION",
            resource_type="ExampleResource"
        )
    elif error_type == "not_found":
        raise EntityNotFoundError(
            entity_type="ExampleEntity",
            entity_id="example-123"
        )
    elif error_type == "internal":
        raise UnoError(
            message=error_message,
            error_code=ErrorCode.INTERNAL_ERROR
        )
    elif error_type == "custom":
        raise UnoError(
            message=error_message,
            error_code="EXAMPLE-001",
            custom_data="Additional context"
        )
    
    return {"message": "No error was raised"}


# Example of using error context
@router.get("/context/{user_id}")
@with_error_context
async def context_example(
    user_id: str = Path(..., description="User ID to use in the context"),
    operation: Optional[str] = Query("view", description="Operation being performed")
):
    """
    Demonstrate error context with UnoError.
    
    This endpoint uses the with_error_context decorator to automatically
    add function parameters to the error context.
    """
    # The user_id and operation are automatically added to error context
    # because of the @with_error_context decorator
    
    # Simulate an error
    if user_id == "error":
        raise UnoError(
            message="Error with context example",
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            # Additional context can be added here
            detail="This error includes the user_id and operation in its context"
        )
    
    return {
        "message": "Success, but try with user_id=error to see context in action",
        "context_example": {
            "user_id": user_id,
            "operation": operation
        }
    }


# Example of using error context with context manager
@router.get("/context-manager/{resource_id}")
async def context_manager_example(
    resource_id: str = Path(..., description="Resource ID to use in the context")
):
    """
    Demonstrate error context with context manager.
    
    This endpoint uses the with_error_context as a context manager to
    add context to errors raised within its block.
    """
    try:
        # Add context using the context manager
        with with_error_context(
            resource_id=resource_id,
            operation="context_manager_example",
            timestamp="2024-04-15T12:00:00Z"
        ):
            # Simulate an error
            if resource_id == "error":
                raise UnoError(
                    message="Error with context manager example",
                    error_code=ErrorCode.RESOURCE_NOT_FOUND
                )
            
            return {
                "message": "Success, but try with resource_id=error to see context in action",
                "resource_id": resource_id
            }
    except UnoError as e:
        # This would normally be handled by the FastAPI error handlers,
        # but we're re-raising to demonstrate how the context is preserved
        raise


# Example of using the Result pattern
@router.get("/result/{value}")
async def result_pattern_example(
    value: str = Path(..., description="Value to use for the example")
):
    """
    Demonstrate using the Result pattern for error handling.
    
    This endpoint uses the Result pattern to handle success and failure
    cases in a functional style.
    """
    # Use a function that returns a Result
    result = process_value(value)
    
    if result.is_success:
        # Handle success case
        return {
            "success": True,
            "message": "Value processed successfully",
            "result": result.value
        }
    else:
        # Handle failure case (this will be captured by the error handlers)
        # In a real application, you might want to convert this to a proper error
        # instead of letting it propagate as an exception
        raise result.error


# Example function that returns a Result
def process_value(value: str) -> Success[Dict[str, Any]] | Failure:
    """Process a value and return a Result."""
    try:
        # Simulate validation
        if not value or len(value) < 3:
            return Failure(ValidationError(
                message="Value must be at least 3 characters long",
                field="value",
                value=value
            ))
        
        # Simulate processing
        processed = {
            "original": value,
            "uppercase": value.upper(),
            "length": len(value),
            "reversed": value[::-1]
        }
        
        # Simulate random error
        if value == "error":
            return Failure(UnoError(
                message="Simulated error during processing",
                error_code=ErrorCode.INTERNAL_ERROR
            ))
        
        # Return success with processed value
        return Success(processed)
    except Exception as e:
        # Catch any unexpected exceptions
        return Failure(UnoError(
            message=f"Unexpected error: {str(e)}",
            error_code=ErrorCode.INTERNAL_ERROR,
            original_error=str(e)
        ))


# Example of using from_exception decorator
@from_exception
def divide(a: int, b: int) -> int:
    """
    Divide two numbers and return the result.
    
    This function is decorated with from_exception, so it will return a Result.
    """
    return a // b


@router.get("/from-exception")
async def from_exception_example(
    a: int = Query(10, description="Numerator"),
    b: int = Query(2, description="Denominator")
):
    """
    Demonstrate using the from_exception decorator for error handling.
    
    This endpoint uses a function decorated with from_exception to handle
    exceptions in a functional style.
    """
    # Use a function decorated with from_exception
    result = divide(a, b)
    
    if result.is_success:
        return {
            "success": True,
            "message": f"{a} / {b} = {result.value}",
            "result": result.value
        }
    else:
        # Convert the Result.error to a UnoError
        error = result.error
        if isinstance(error, ZeroDivisionError):
            # Convert specific errors to UnoError
            raise UnoError(
                message="Cannot divide by zero",
                error_code=ErrorCode.VALIDATION_ERROR,
                numerator=a,
                denominator=b
            )
        else:
            # Re-raise other errors
            raise UnoError(
                message=f"Error during division: {str(error)}",
                error_code=ErrorCode.INTERNAL_ERROR,
                original_error=str(error)
            )