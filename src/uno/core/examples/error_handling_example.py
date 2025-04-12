# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example demonstrating the comprehensive error handling framework.

This module shows how to use the various error handling components
including structured errors, error codes, contextual information,
validation, and logging.
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from uno.core.errors import (
    UnoError, ErrorCode, ErrorCategory, ErrorSeverity,
    ValidationError, ValidationContext,
    Result, Success, Failure, of, failure, from_exception, from_awaitable,
    ErrorCatalog, register_error,
    configure_logging, get_logger, LogConfig,
    with_error_context, add_error_context, get_error_context,
    with_logging_context, add_logging_context
)


# Step 1: Initialize error catalog with application-specific error codes
def init_error_catalog():
    """Initialize the error catalog with application-specific error codes."""
    # Register a custom error code for user operations
    register_error(
        code="USER-0001",
        message_template="User validation error: {message}",
        category=ErrorCategory.VALIDATION,
        severity=ErrorSeverity.ERROR,
        description="Error validating user data",
        http_status_code=400,
        retry_allowed=True
    )
    
    register_error(
        code="USER-0002",
        message_template="User not found: {user_id}",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="The requested user could not be found",
        http_status_code=404,
        retry_allowed=False
    )
    
    register_error(
        code="USER-0003",
        message_template="Duplicate username: {username}",
        category=ErrorCategory.RESOURCE,
        severity=ErrorSeverity.ERROR,
        description="A user with this username already exists",
        http_status_code=409,
        retry_allowed=False
    )


# Step 2: Define domain models
@dataclass
class User:
    """User model for the example."""
    id: Optional[str] = None
    username: str = ""
    email: str = ""
    age: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert user to dictionary."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "age": self.age
        }


# Step 3: Implement validation with ValidationContext
def validate_user(user: User) -> None:
    """
    Validate a user object.
    
    Args:
        user: The user to validate
        
    Raises:
        ValidationError: If validation fails
    """
    context = ValidationContext("User")
    
    # Validate username
    if not user.username:
        context.add_error(
            field="username",
            message="Username is required",
            error_code="FIELD_REQUIRED"
        )
    elif len(user.username) < 3:
        context.add_error(
            field="username",
            message="Username must be at least 3 characters",
            error_code="FIELD_INVALID",
            value=user.username
        )
    
    # Validate email using a nested context
    email_context = context.nested("email")
    if not user.email:
        email_context.add_error(
            field="",  # Empty because it's added to the path already
            message="Email is required",
            error_code="FIELD_REQUIRED"
        )
    elif "@" not in user.email:
        email_context.add_error(
            field="format",  # Will become email.format in the full path
            message="Invalid email format",
            error_code="FIELD_INVALID",
            value=user.email
        )
    
    # Validate age
    if user.age < 18:
        context.add_error(
            field="age",
            message="User must be 18 or older",
            error_code="FIELD_INVALID",
            value=user.age
        )
    
    # Raise if there are any errors
    context.raise_if_errors()


# Step 4: Implement service with Result pattern for error handling
class UserService:
    """
    User service implementing business logic with Result pattern for error handling.
    """
    
    def __init__(self):
        """Initialize the user service with an in-memory database."""
        self.users: Dict[str, User] = {}
        self.logger = get_logger(__name__)
    
    @with_error_context
    @with_logging_context
    def create_user(self, user_data: Dict[str, Any]) -> Result[User]:
        """
        Create a new user.
        
        Args:
            user_data: The user data
            
        Returns:
            Result containing the created user or an error
        """
        # Add context for logging and error handling
        add_error_context(operation="create_user")
        add_logging_context(operation="create_user", user_data=user_data)
        
        self.logger.info("Creating new user")
        
        try:
            # Create user object
            user = User(
                id=f"user_{len(self.users) + 1}",
                username=user_data.get("username", ""),
                email=user_data.get("email", ""),
                age=user_data.get("age", 0)
            )
            
            # Check for duplicate username
            for existing_user in self.users.values():
                if existing_user.username == user.username:
                    return failure(UnoError(
                        f"Username '{user.username}' already exists",
                        "USER-0003",
                        username=user.username
                    ))
            
            # Validate user
            try:
                validate_user(user)
            except ValidationError as e:
                return failure(e)
            
            # Store user
            self.users[user.id] = user
            self.logger.info(f"User created with ID: {user.id}")
            
            return of(user)
            
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            return failure(UnoError(
                f"Failed to create user: {str(e)}",
                ErrorCode.INTERNAL_ERROR
            ))
    
    @from_exception
    def get_user(self, user_id: str) -> User:
        """
        Get a user by ID using exception-based error handling.
        
        This method demonstrates using the @from_exception decorator
        to convert exception-based code to Result-based code.
        
        Args:
            user_id: The user ID
            
        Returns:
            The user
            
        Raises:
            UnoError: If the user is not found
        """
        if user_id not in self.users:
            raise UnoError(
                f"User with ID '{user_id}' not found",
                "USER-0002",
                user_id=user_id
            )
        
        return self.users[user_id]
    
    async def get_user_async(self, user_id: str) -> Result[User]:
        """
        Get a user by ID asynchronously.
        
        This method demonstrates converting an async operation
        to a Result using from_awaitable.
        
        Args:
            user_id: The user ID
            
        Returns:
            Result containing the user or an error
        """
        # Simulate async database query
        async def async_get_user() -> User:
            await asyncio.sleep(0.1)  # Simulate network delay
            
            if user_id not in self.users:
                raise UnoError(
                    f"User with ID '{user_id}' not found",
                    "USER-0002",
                    user_id=user_id
                )
            
            return self.users[user_id]
        
        # Convert awaitable to Result
        return await from_awaitable(async_get_user())
    
    def list_users(self) -> Result[List[User]]:
        """
        List all users.
        
        Returns:
            Result containing list of users
        """
        try:
            users = list(self.users.values())
            return of(users)
        except Exception as e:
            return failure(UnoError(
                f"Failed to list users: {str(e)}",
                ErrorCode.INTERNAL_ERROR
            ))


# Example usage
async def main():
    """Run the example."""
    # Step 1: Initialize error catalog and configure logging
    init_error_catalog()
    configure_logging(LogConfig(level="INFO", json_format=True))
    
    logger = get_logger("example")
    logger.info("Starting error handling example")
    
    # Step 2: Create user service
    user_service = UserService()
    
    # Step 3: Create a valid user
    valid_user_result = user_service.create_user({
        "username": "johndoe",
        "email": "john@example.com",
        "age": 30
    })
    
    if valid_user_result.is_success:
        user = valid_user_result.value
        logger.info(f"Successfully created user: {user.username}")
    else:
        logger.error(f"Failed to create user: {valid_user_result.error}")
    
    # Step 4: Create an invalid user
    invalid_user_result = user_service.create_user({
        "username": "al",
        "email": "invalid-email",
        "age": 17
    })
    
    if invalid_user_result.is_success:
        user = invalid_user_result.value
        logger.info(f"Successfully created user: {user.username}")
    else:
        # Handle validation errors
        error = invalid_user_result.error
        logger.error(f"Failed to create user: {error}")
        
        if isinstance(error, ValidationError):
            logger.error("Validation errors:")
            for field_error in error.validation_errors:
                logger.error(f"  - {field_error['field']}: {field_error['message']}")
    
    # Step 5: Get a user
    get_user_result = user_service.get_user("user_1")
    
    if get_user_result.is_success:
        user = get_user_result.value
        logger.info(f"Found user: {user.username}")
    else:
        logger.error(f"Failed to get user: {get_user_result.error}")
    
    # Step 6: Get a non-existent user
    get_user_result = user_service.get_user("user_999")
    
    if get_user_result.is_success:
        user = get_user_result.value
        logger.info(f"Found user: {user.username}")
    else:
        logger.error(f"Failed to get user: {get_user_result.error}")
    
    # Step 7: Async operations
    get_user_async_result = await user_service.get_user_async("user_1")
    
    if get_user_async_result.is_success:
        user = get_user_async_result.value
        logger.info(f"Found user async: {user.username}")
    else:
        logger.error(f"Failed to get user async: {get_user_async_result.error}")
    
    # Step 8: Convert Result to HTTP response (example)
    def result_to_http_response(result: Result[Any]) -> Dict[str, Any]:
        """Convert a Result to an HTTP response."""
        if result.is_success:
            return {
                "status_code": 200,
                "body": result.to_dict()
            }
        else:
            error = result.error
            status_code = 500
            
            if isinstance(error, UnoError):
                status_code = error.http_status_code
            
            return {
                "status_code": status_code,
                "body": result.to_dict()
            }
    
    # Convert the get user result to an HTTP response
    response = result_to_http_response(get_user_result)
    logger.info(f"HTTP Response: {response}")
    
    logger.info("Error handling example completed")


if __name__ == "__main__":
    asyncio.run(main())