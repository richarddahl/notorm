"""
Example of modern error handling in Uno.

This example demonstrates the modernized error handling approach using
UnoError, Result pattern, and contextual error information.
"""

import asyncio
from typing import Dict, Any, List, Optional

from uno.core.errors.base import (
    UnoError, ErrorCode, add_error_context, with_error_context, with_async_error_context
)
from uno.core.errors.result import Result, Success, Failure, of, failure, from_exception
from uno.core.errors.validation import ValidationError, validate_fields
from uno.core.errors.security import AuthorizationError


class UserService:
    """Example service demonstrating modern error handling."""
    
    def __init__(self, logger=None):
        """Initialize the service."""
        self.logger = logger
    
    @with_error_context
    def validate_user_data(self, user_data: Dict[str, Any]) -> Result[Dict[str, Any]]:
        """
        Validate user data using structured validation.
        
        This demonstrates using the validate_fields utility and ValidationError.
        
        Args:
            user_data: User data to validate
            
        Returns:
            Result with validated data or validation error
        """
        try:
            # Define required fields and validators
            required_fields = {"username", "email", "password"}
            
            def validate_email(value: str) -> Optional[str]:
                if "@" not in value:
                    return "Invalid email format"
                return None
                
            def validate_password(value: str) -> Optional[str]:
                if len(value) < 8:
                    return "Password must be at least 8 characters"
                return None
            
            validators = {
                "email": [validate_email],
                "password": [validate_password]
            }
            
            # Validate fields
            validate_fields(user_data, required_fields, validators, "User")
            
            # If validation succeeds, return success
            return Success(user_data)
            
        except ValidationError as e:
            # Return validation error as Failure
            return Failure(e)
    
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
            return Failure(UnoError(
                message="User already exists",
                error_code=ErrorCode.RESOURCE_CONFLICT,
                context={"username": user_data["username"]}
            ))
        
        # Create user (simulated)
        created_user = {**user_data, "id": "usr_123"}
        
        return Success(created_user)
    
    @with_async_error_context
    async def authenticate_user(self, credentials: Dict[str, Any]) -> Result[Dict[str, Any]]:
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
            return Failure(ValidationError(
                message="Username and password are required",
                error_code=ErrorCode.VALIDATION_ERROR
            ))
        
        # Simulate authentication failure
        if username != "admin" or password != "password123":
            return Failure(AuthorizationError(
                message="Invalid credentials",
                permission="login"
            ))
        
        # Return authenticated user
        return Success({
            "id": "usr_123",
            "username": username,
            "is_admin": True
        })


# Example usage
async def main():
    """Run the example."""
    user_service = UserService()
    
    # Example 1: Validation failure
    invalid_user = {
        "username": "john",
        "email": "invalid-email",
        "password": "123"
    }
    
    print("\nExample 1: Validation failure")
    result1 = user_service.create_user(invalid_user)
    if result1.is_failure:
        print(f"Error: {result1.error}")
        if isinstance(result1.error, ValidationError):
            print("Validation errors:")
            for error in result1.error.validation_errors:
                print(f"  - {error['field']}: {error['message']}")
    
    # Example 2: Successful user creation
    valid_user = {
        "username": "john",
        "email": "john@example.com",
        "password": "password123"
    }
    
    print("\nExample 2: Successful user creation")
    result2 = user_service.create_user(valid_user)
    if result2.is_success:
        print(f"User created: {result2.value}")
    
    # Example 3: Resource conflict error
    admin_user = {
        "username": "admin",
        "email": "admin@example.com",
        "password": "adminpass123"
    }
    
    print("\nExample 3: Resource conflict error")
    result3 = user_service.create_user(admin_user)
    if result3.is_failure:
        print(f"Error: {result3.error}")
    
    # Example 4: Authentication with authorization error
    print("\nExample 4: Authentication with invalid credentials")
    result4 = await user_service.authenticate_user({
        "username": "john",
        "password": "wrongpass"
    })
    if result4.is_failure:
        print(f"Error: {result4.error}")
    
    # Example 5: Successful authentication
    print("\nExample 5: Successful authentication")
    result5 = await user_service.authenticate_user({
        "username": "admin",
        "password": "password123"
    })
    if result5.is_success:
        print(f"Authenticated user: {result5.value}")


if __name__ == "__main__":
    asyncio.run(main())
EOL < /dev/null