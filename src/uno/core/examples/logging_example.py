# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example for using the structured logging framework.

This module demonstrates how to use the UNO structured logging framework
with context propagation, error integration, and HTTP middleware.
"""

import asyncio
import uuid
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException

from uno.core.logging import (
    configure_logging,
    get_logger,
    LogConfig,
    LogLevel,
    LogFormat,
    with_logging_context,
    add_context,
    clear_context,
    log_error,
    LoggingMiddleware,
)
from uno.core.errors.framework import ValidationError, NotFoundError, DatabaseError


# Configure the logger
def setup_logging() -> None:
    """Configure logging for the application."""
    config = LogConfig(
        level=LogLevel.DEBUG,
        format=LogFormat.JSON,
        console_output=True,
        service_name="example-service",
        environment="development",
    )
    configure_logging(config)


# Get a logger for this module
logger = get_logger("uno.examples.logging")


# Example of function with context decorator
@with_logging_context
def process_user(user_id: str, action: str) -> dict[str, Any]:
    """
    Process a user action.

    Args:
        user_id: User identifier
        action: Action to perform

    Returns:
        Result of the action
    """
    # The user_id and action are automatically added to the logging context
    logger.info(f"Processing user action: {action}")

    # Example of logging with additional context
    logger.debug(
        "Processing details",
        extra={"extras": {"detail_level": "high", "priority": "normal"}},
    )

    # Simulate an error for demonstration
    if action == "fail":
        error = ValidationError("Invalid action specified", field="action")
        log_error(error)
        raise error

    return {"user_id": user_id, "action": action, "status": "completed"}


# Example of a function with static context
@with_logging_context(component="user_service", module="authentication")
def authenticate_user(username: str, password: str) -> dict[str, Any]:
    """
    Authenticate a user.

    Args:
        username: Username
        password: Password

    Returns:
        Authentication result
    """
    # 'component' and 'module' are added to all logs in this function
    logger.info(f"Authenticating user: {username}")

    # Bind additional context for all subsequent logs
    auth_logger = logger.bind(auth_method="password", security_level="standard")

    # Simulate validation
    if len(password) < 8:
        auth_logger.warning(f"Password too short for user: {username}")
        error = ValidationError(
            "Password must be at least 8 characters",
            code="AUTH_INVALID_PASSWORD",
            field="password",
        )
        log_error(error)
        raise error

    auth_logger.info(f"User authenticated: {username}")
    return {
        "username": username,
        "authenticated": True,
        "session_id": str(uuid.uuid4()),
    }


# Example of async function with logging
async def async_task_example() -> None:
    """Demonstrate async task with logging context."""
    # Add context for this task
    task_id = str(uuid.uuid4())
    add_context(task_id=task_id, task_type="background")

    logger.info("Starting async task")

    try:
        # Simulate work
        await asyncio.sleep(0.1)
        logger.info("Async task progress update")

        # Simulate more work
        await asyncio.sleep(0.1)
        logger.info("Async task completed")

    except Exception as e:
        # Log any exceptions
        logger.exception(f"Error in async task: {str(e)}")
        raise

    finally:
        # Important: clear context when done
        clear_context()


# FastAPI example with logging middleware
app = FastAPI(title="Logging Example API")


# Add logging middleware to the application
app.add_middleware(
    LoggingMiddleware,
    exclude_paths=["/health"],
    sensitive_headers=["authorization", "cookie", "x-api-key"],
)


# Define dependencies for request logging
async def get_request_logger():
    """Get a logger with request context."""
    # This would typically be set by middleware in a real application
    request_id = str(uuid.uuid4())
    add_context(request_id=request_id)

    try:
        yield logger.bind(endpoint="api")
    finally:
        clear_context()


# Example endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: str, logger=Depends(get_request_logger)):
    """Get user details."""
    logger.info(f"Getting user: {user_id}")

    try:
        # Simulate database lookup
        if user_id == "not_found":
            error = NotFoundError(f"User not found: {user_id}")
            log_error(error)
            raise HTTPException(status_code=404, detail=str(error))

        return {"user_id": user_id, "name": "Example User"}

    except Exception as e:
        logger.exception(f"Error getting user: {str(e)}")
        raise


@app.post("/users/{user_id}/actions")
async def user_action(
    user_id: str, action: dict[str, Any], logger=Depends(get_request_logger)
):
    """Perform a user action."""
    action_type = action.get("type", "unknown")
    logger.info(f"User action request: {action_type}")

    try:
        # Use our context-aware function
        result = process_user(user_id, action_type)
        return result

    except ValidationError as e:
        # This will be handled by the error framework
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Log unexpected errors
        error = DatabaseError(f"Unexpected error: {str(e)}")
        log_error(error)
        raise HTTPException(status_code=500, detail=str(error))


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # This is excluded from request logging by the middleware
    return {"status": "ok"}


# Example of running the application
def run_example():
    """Run the example application."""
    # Configure logging
    setup_logging()

    logger.info("Starting logging example application")

    try:
        # Example of using synchronous functions
        user_result = process_user("user123", "login")
        logger.info("Process user result", extra={"extras": {"result": user_result}})

        auth_result = authenticate_user("testuser", "password123")
        logger.info("Auth result", extra={"extras": {"result": auth_result}})

        # Example of using the error logging
        try:
            authenticate_user("baduser", "short")
        except ValidationError as e:
            logger.warning(f"Expected auth error: {str(e)}")

        # Example of running an async task
        asyncio.run(async_task_example())

        logger.info("Example application completed successfully")

    except Exception as e:
        logger.exception(f"Unexpected error in example: {str(e)}")


if __name__ == "__main__":
    run_example()
