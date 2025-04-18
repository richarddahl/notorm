"""
Example of modern error handling in Uno.

This example demonstrates the modernized error handling approach using
the Result pattern, ValidationError, and the new validation framework.
"""

import asyncio
from typing import Dict, Any, List, Optional

from uno.core.base.error import (
    BaseError,
    ErrorCode,
    add_error_context,
    with_error_context,
    with_async_error_context,
)
from uno.core.errors.result import Result, ValidationResult, ValidationError, ErrorSeverity
from uno.core.validation import validate_schema, required, email, min_length
from uno.core.validation.schema import SchemaValidator
from uno.core.errors.security import AuthorizationError
from pydantic import BaseModel, Field


class UserService:
    """Example service demonstrating modern error handling."""

    def __init__(self, logger=None):
        """Initialize the service."""
        self.logger = logger

    # Define a Pydantic schema for user data
    class UserSchema(BaseModel):
        """Schema for user data validation."""
        username: str = Field(..., min_length=2)
        email: str = Field(..., pattern=r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
        password: str = Field(..., min_length=8)
    
    @with_error_context
    def validate_user_data(self, user_data: Dict[str, Any]) -> ValidationResult[Dict[str, Any]]:
        """
        Validate user data using the new validation framework.

        This demonstrates using the schema validator with Pydantic integration.

        Args:
            user_data: User data to validate

        Returns:
            ValidationResult with validated data or validation errors
        """
        # Create validator function for the schema
        validate = validate_schema(self.UserSchema)
        
        # Validate the data against the schema
        schema_result = validate(user_data)
        
        # If validation succeeds, return the original data for further processing
        if schema_result.is_success:
            return Result.success(user_data)
        
        # If validation fails, return the validation errors
        return schema_result.map(lambda _: user_data)

    @with_error_context
    def create_user(self, user_data: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """
        Create a user using the Result pattern for error handling.

        This demonstrates using Result for functional error handling.

        Args:
            user_data: User data for the new user

        Returns:
            Result with created user or error
        """
        # Add context information for better debugging
        add_error_context(operation="create_user")

        # Validate user data
        validation_result = self.validate_user_data(user_data)
        if validation_result.is_failure:
            return validation_result

        # Check if user exists (simulate database error)
        if user_data.get("username") == "admin":
            return Result.failure(
                BaseError(
                    message="User already exists",
                    error_code=ErrorCode.RESOURCE_CONFLICT,
                    context={"username": user_data["username"]},
                )
            )

        # Create user (simulated)
        created_user = {**user_data, "id": "usr_123"}

        return Result.success(created_user)

    @with_async_error_context
    async def authenticate_user(
        self, credentials: Dict[str, Any]
    ) -> Result[Dict[str, Any]]:
        """
        Authenticate a user with async error handling.

        This demonstrates using async error context and AuthorizationError.

        Args:
            credentials: User credentials

        Returns:
            Result with authenticated user or error
        """
        username = credentials.get("username")
        password = credentials.get("password")

        # Add context for better debugging
        add_error_context(username=username)

        # Simulate async operation
        await asyncio.sleep(0.1)

        # Check credentials
        if not username or not password:
            return Result.failure(
                ValidationError(
                    message="Username and password are required",
                    code="CREDENTIALS_REQUIRED",
                    severity=ErrorSeverity.ERROR
                )
            )

        # Simulate authentication failure
        if username != "admin" or password != "password123":
            return Result.failure(
                AuthorizationError(message="Invalid credentials", permission="login")
            )

        # Return authenticated user
        return Result.success({"id": "usr_123", "username": username, "is_admin": True})


# Example usage
async def main():
    """Run the example."""
    user_service = UserService()

    # Example 1: Validation failure
    invalid_user = {"username": "john", "email": "invalid-email", "password": "123"}

    print("\nExample 1: Validation failure")
    result1 = user_service.create_user(invalid_user)
    if result1.is_failure:
        print(f"Error: {result1.errors[0].message}")
        print("Validation errors:")
        for error in result1.errors:
            path = error.path or "unknown"
            print(f"  - {path}: {error.message}")

    # Example 2: Successful user creation
    valid_user = {
        "username": "john",
        "email": "john@example.com",
        "password": "password123",
    }

    print("\nExample 2: Successful user creation")
    result2 = user_service.create_user(valid_user)
    if result2.is_success:
        print(f"User created: {result2.value}")

    # Example 3: Resource conflict error
    admin_user = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass123",
    }

    print("\nExample 3: Resource conflict error")
    result3 = user_service.create_user(admin_user)
    if result3.is_failure:
        print(f"Error: {result3.error.message}")

    # Example 4: Authentication with authorization error
    print("\nExample 4: Authentication with invalid credentials")
    result4 = await user_service.authenticate_user(
        {"username": "john", "password": "wrongpass"}
    )
    if result4.is_failure:
        print(f"Error: {result4.error.message}")

    # Example 5: Successful authentication
    print("\nExample 5: Successful authentication")
    result5 = await user_service.authenticate_user(
        {"username": "admin", "password": "password123"}
    )
    if result5.is_success:
        print(f"Authenticated user: {result5.value}")
        
    # Example 6: Demonstrate metadata in Result
    print("\nExample 6: Using result metadata")
    result6 = Result.success("Success value")
    result6.add_metadata("execution_time", 0.5)
    result6.add_metadata("source", "example")
    
    print(f"Result metadata: {result6.metadata}")
    
    # Example 7: Demonstrate tap method
    print("\nExample 7: Using tap method")
    result7 = Result.success("Success value")
    result7.tap(lambda value: print(f"Processing: {value}"))
    
    # Example 8: Demonstrate value_or and value_or_raise
    print("\nExample 8: Using value_or and value_or_raise")
    success_result = Result.success(42)
    failure_result = Result.failure(ValidationError(message="Failed"))
    
    print(f"Success value_or: {success_result.value_or(0)}")
    print(f"Failure value_or: {failure_result.value_or(0)}")
    
    try:
        failure_result.value_or_raise()
    except Exception as e:
        print(f"Raised exception: {e}")


if __name__ == "__main__":
    asyncio.run(main())
