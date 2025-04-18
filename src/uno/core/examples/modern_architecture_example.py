"""
Demonstrating the modern architecture of the Uno framework.

This example shows the integration of:
1. Modern error handling with BaseError, Result pattern, and error catalog
2. Dependency Injection with container and service lifetimes
3. Event-driven architecture with events and handlers
4. Repository pattern for data access
5. Unit of Work pattern for transaction management

Note: This is a simplified version for demonstration purposes. The full implementation
would showcase a complete user management system with CRUD operations and event handling.
"""

import asyncio
import logging
from typing import Optional

from uno.core.base.error import BaseError, ErrorCategory, ErrorSeverity
from uno.core.errors.catalog import (
    register_error,
    get_all_error_codes,
    get_error_code_info,
    ErrorCatalog,
)
from uno.core.errors.result import Result, Success, Failure


# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize error catalog
try:
    ErrorCatalog.initialize()
except ValueError:
    # Error catalog already initialized, which is fine
    pass

# Register domain-specific error codes
register_error(
    "USER_ALREADY_EXISTS",
    "A user with the same username already exists",
    category=ErrorCategory.CONFLICT,
    severity=ErrorSeverity.ERROR,
    description="A user with the given username already exists in the system",
    http_status_code=409,
)

register_error(
    "INVALID_USER_DATA",
    "The user data provided is invalid",
    category=ErrorCategory.VALIDATION,
    severity=ErrorSeverity.WARNING,
    description="The user input data failed validation requirements",
    http_status_code=400,
)

register_error(
    "USER_NOT_FOUND",
    "The requested user could not be found",
    category=ErrorCategory.NOT_FOUND,
    severity=ErrorSeverity.WARNING,
    description="The user with the specified ID does not exist in the system",
    http_status_code=404,
)


async def simple_demonstration():
    """Demonstrate the core architectural components."""
    print("\n=== Modern Architecture Example ===\n")

    # Demonstrate error catalog
    print("1. Error Catalog Demonstration")
    print("------------------------------")
    all_errors = get_all_error_codes()
    print(f"Total registered errors: {len(all_errors)}")

    # Group errors by category
    errors_by_category = {}
    for error in all_errors:
        category = error.category.name
        if category not in errors_by_category:
            errors_by_category[category] = []
        errors_by_category[category].append(error)

    # Show a few sample categories
    for category in ["VALIDATION", "CONFLICT", "NOT_FOUND", "RESOURCE"]:
        if category in errors_by_category:
            print(
                f"\nCategory: {category} ({len(errors_by_category[category])} errors)"
            )
            for error in errors_by_category[category][:3]:  # Show up to 3 examples
                print(
                    f"  - {error.code}: {error.message_template} (HTTP {error.http_status_code})"
                )

    # Demonstrate looking up specific errors
    print("\n2. Error Lookup Demonstration")
    print("------------------------------")
    user_not_found = get_error_code_info("USER_NOT_FOUND")
    if user_not_found:
        print(f"Error code: {user_not_found.code}")
        print(f"Message template: {user_not_found.message_template}")
        print(f"Category: {user_not_found.category.name}")
        print(f"Severity: {user_not_found.severity.name}")
        print(f"HTTP Status: {user_not_found.http_status_code}")

    # Demonstrate Result pattern
    print("\n3. Result Pattern Demonstration")
    print("------------------------------")

    def validate_username(username: str) -> Result[str]:
        """Validate a username using the Result pattern."""
        if not username:
            return Failure(
                BaseError(
                    message="Username cannot be empty", error_code="INVALID_USER_DATA"
                )
            )

        if len(username) < 3:
            return Failure(
                BaseError(
                    message="Username must be at least 3 characters",
                    error_code="INVALID_USER_DATA",
                )
            )

        if len(username) > 50:
            return Failure(
                BaseError(
                    message="Username cannot exceed 50 characters",
                    error_code="INVALID_USER_DATA",
                )
            )

        return Success(username)

    # Test with valid and invalid values
    test_usernames = ["", "a", "valid_username", "x" * 60]

    for username in test_usernames:
        result = validate_username(username)
        if result.is_success:
            print(f"'{username}' is valid")
        else:
            error = result.error
            error_code = getattr(error, "error_code", "UNKNOWN")
            print(f"'{username}' is invalid: {error} (Code: {error_code})")

    # Future demonstrations would include:
    # 4. Dependency Injection
    # 5. Event-Driven Architecture
    # 6. Repository Pattern
    # 7. Unit of Work Pattern

    print("\nThis example demonstrates the foundation of the modern architecture.")
    print(
        "The source code contains full implementations of all these patterns working together."
    )


if __name__ == "__main__":
    asyncio.run(simple_demonstration())
