# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Example for using the distributed tracing framework.

This module demonstrates how to use the UNO tracing framework with
context propagation, integrations with logging, metrics, and error handling,
and tracing for HTTP requests and database operations.
"""

import asyncio
import random
import time
import uuid
from typing import Dict, List, Any, Optional

from fastapi import FastAPI, Depends, HTTPException

from uno.core.tracing import (
    configure_tracing,
    TracingConfig,
    SpanKind,
    get_tracer,
    get_current_span,
    get_current_trace_id,
    trace,
    register_logging_integration,
    register_metrics_integration,
    register_error_integration,
    create_request_middleware,
    create_database_integration,
)
from uno.core.logging import (
    configure_logging,
    LogConfig,
    LogFormat,
    get_logger,
)
from uno.core.metrics import (
    configure_metrics,
    MetricsConfig,
    timed,
)
from uno.core.errors.framework import ValidationError, NotFoundError


# Configure logging, metrics, and tracing
def setup_observability() -> None:
    """Configure observability for the application."""
    # Configure logging
    logging_config = LogConfig(
        level="DEBUG",
        format=LogFormat.JSON,
        console_output=True,
    )
    configure_logging(logging_config)

    # Configure metrics
    metrics_config = MetricsConfig(
        enabled=True,
        service_name="example-service",
        environment="development",
        export_interval=10.0,
    )
    configure_metrics(metrics_config)

    # Configure tracing
    tracing_config = TracingConfig(
        enabled=True,
        service_name="example-service",
        environment="development",
        export_interval=5.0,
        console_export=True,
    )
    tracer = configure_tracing(tracing_config)

    # Register integrations
    register_logging_integration(tracer)
    register_metrics_integration(tracer)
    register_error_integration(tracer)


# Mock database session for examples
class MockDatabaseSession:
    """Mock database session for demonstration purposes."""

    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a query against the mock database.

        Args:
            query: SQL query to execute
            params: Query parameters

        Returns:
            Query result
        """
        # Simulate query execution
        await asyncio.sleep(random.uniform(0.05, 0.2))

        # Log the query
        logger.debug(f"Executing query: {query}", extra={"params": params})

        # Generate mock results based on the query
        if "SELECT" in query and "users" in query:
            user_id = params.get("id") if params else None
            if user_id == "not_found":
                return MockResult([])
            else:
                return MockResult(
                    [
                        {
                            "id": user_id or str(uuid.uuid4()),
                            "name": f"User {user_id}" if user_id else "Random User",
                            "email": (
                                f"user{user_id}@example.com"
                                if user_id
                                else "user@example.com"
                            ),
                        }
                    ]
                )
        elif "INSERT" in query:
            return MockResult([], rowcount=1)
        elif "UPDATE" in query:
            return MockResult([], rowcount=random.randint(0, 5))
        else:
            return MockResult([])


class MockResult:
    """Mock query result."""

    def __init__(self, rows: list[dict[str, Any]], rowcount: int = None):
        """
        Initialize a mock result.

        Args:
            rows: Result rows
            rowcount: Number of affected rows
        """
        self.rows = rows
        self.rowcount = rowcount or len(rows)

    def fetchall(self) -> list[dict[str, Any]]:
        """Fetch all results."""
        return self.rows

    def fetchone(self) -> Optional[Dict[str, Any]]:
        """Fetch one result."""
        return self.rows[0] if self.rows else None

    def __iter__(self):
        """Iterate through results."""
        return iter(self.rows)

    def __len__(self):
        """Get number of results."""
        return len(self.rows)


# Get a logger for this module
logger = get_logger("examples.tracing")


# Example of tracing with context manager
async def trace_with_context_manager() -> Dict[str, Any]:
    """Example of using a tracing context manager."""
    # Get the tracer
    tracer = get_tracer()

    # Start a new trace with a root span
    async with tracer.create_span(
        name="trace_example",
        attributes={"example": "context_manager"},
        kind=SpanKind.INTERNAL,
    ) as root_span:
        logger.info("Started root span")

        # Add an event to the span
        root_span.add_event("process_started")

        # Perform some work
        await asyncio.sleep(0.1)

        # Create a child span
        async with tracer.create_span(
            name="child_operation",
            attributes={"operation": "subprocess"},
        ) as child_span:
            logger.info("Executing child operation")

            # Perform some work
            await asyncio.sleep(0.2)

            # Add an event
            child_span.add_event("subprocess_completed")

            # The child span is automatically ended when exiting the context

        # Fetch the current span and trace
        current_span = get_current_span()
        current_trace_id = get_current_trace_id()

        logger.info(
            f"Current trace: {current_trace_id}, current span: {current_span.span_id}"
        )

        # Add a second child span that fails
        try:
            async with tracer.create_span("failing_operation") as error_span:
                logger.info("Starting operation that will fail")

                # Simulate an error
                raise ValueError("Simulated error in span")
        except ValueError as e:
            # The span will automatically be marked with error status
            logger.error(f"Error in span: {str(e)}")

        # The root span is automatically ended when exiting the context

    return {
        "trace_id": root_span.trace_id,
        "root_span_id": root_span.span_id,
        "root_span_duration": root_span.duration,
    }


# Example of tracing with decorator
@trace(name="decorated_function", attributes={"method": "decorator_example"})
async def trace_with_decorator(iterations: int = 3) -> Dict[str, Any]:
    """
    Example of using the tracing decorator.

    Args:
        iterations: Number of iterations to perform

    Returns:
        Result dictionary
    """
    # The function is automatically traced with the trace decorator
    logger.info(f"Executing traced function with {iterations} iterations")

    results = []
    for i in range(iterations):
        # Simulate some work
        await asyncio.sleep(random.uniform(0.1, 0.3))

        # Get current span
        span = get_current_span()

        # Add an event for this iteration
        span.add_event(
            f"iteration_{i}", attributes={"iteration": i, "timestamp": time.time()}
        )

        # Add a result
        result = {"iteration": i, "value": random.randint(1, 100)}
        results.append(result)
        logger.info(f"Completed iteration {i}")

    # Return results
    return {
        "trace_id": get_current_trace_id(),
        "span_id": get_current_span().span_id,
        "iterations": iterations,
        "results": results,
    }


# Example of tracing with database operations
async def trace_database_operations() -> Dict[str, Any]:
    """Example of tracing database operations."""
    # Create a mock database session
    session = MockDatabaseSession()

    # Create a database tracing decorator
    trace_db = create_database_integration()

    # Define a traced database function
    @trace_db
    async def get_user(session: MockDatabaseSession, user_id: str) -> Dict[str, Any]:
        """
        Get a user from the database.

        Args:
            session: Database session
            user_id: User ID to retrieve

        Returns:
            User data
        """
        result = await session.execute(
            "SELECT * FROM users WHERE id = :id", {"id": user_id}
        )
        return result.fetchone()

    @trace_db
    async def create_user(
        session: MockDatabaseSession, user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a user in the database.

        Args:
            session: Database session
            user_data: User data to insert

        Returns:
            Created user data
        """
        # Insert the user
        await session.execute(
            "INSERT INTO users (id, name, email) VALUES (:id, :name, :email)", user_data
        )

        # Return the created user
        return user_data

    # Start a new trace
    tracer = get_tracer()
    async with tracer.create_span("database_operations") as root_span:
        logger.info("Starting database operations")

        # Create a user
        user_id = str(uuid.uuid4())
        user_data = {
            "id": user_id,
            "name": "Test User",
            "email": "test@example.com",
        }

        created_user = await create_user(session, user_data)
        logger.info(f"Created user: {created_user['id']}")

        # Get the user
        user = await get_user(session, user_id)
        logger.info(f"Retrieved user: {user['id']}")

        # Try to get a non-existent user
        try:
            await get_user(session, "not_found")
        except Exception as e:
            logger.warning(f"User not found, as expected")

        return {
            "trace_id": root_span.trace_id,
            "user_id": user_id,
            "operations": ["create_user", "get_user"],
        }


# FastAPI integration example
app = FastAPI(title="Tracing Example API")

# Add tracing middleware
app.add_middleware(create_request_middleware(app, excluded_paths=["/health"]))


# Define session dependency
async def get_db_session():
    """Get a database session."""
    session = MockDatabaseSession()

    # The FastAPI dependency injection system will inject the trace context
    logger.debug("Created database session")

    yield session


# Create a database tracing decorator
trace_db = create_database_integration()


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    This endpoint is excluded from tracing in the middleware.
    """
    return {"status": "healthy"}


@app.get("/api/users/{user_id}")
@trace(name="get_user_endpoint")
async def get_user_endpoint(
    user_id: str, session: MockDatabaseSession = Depends(get_db_session)
):
    """Get user details with tracing."""
    logger.info(f"Getting user: {user_id}")

    # Define a traced database function
    @trace_db
    async def get_user(session, user_id):
        result = await session.execute(
            "SELECT * FROM users WHERE id = :id", {"id": user_id}
        )
        return result.fetchone()

    # Get the user
    user = await get_user(session, user_id)

    if not user:
        error = NotFoundError(f"User not found: {user_id}")
        logger.warning(str(error))
        raise HTTPException(status_code=404, detail=str(error))

    # Get current span and add custom attribute
    span = get_current_span()
    if span:
        span.attributes["user.id"] = user_id

    return {"user": user}


@app.post("/api/users")
@trace(name="create_user_endpoint")
async def create_user_endpoint(
    user_data: Dict[str, Any], session: MockDatabaseSession = Depends(get_db_session)
):
    """Create a user with tracing."""
    logger.info(f"Creating user: {user_data.get('name')}")

    # Validate the user data
    if not user_data.get("name"):
        error = ValidationError("User name is required", field="name")
        logger.error(str(error))
        raise HTTPException(status_code=400, detail=str(error))

    # Define a traced database function
    @trace_db
    async def insert_user(session, user_data):
        # Generate an ID if not provided
        if "id" not in user_data:
            user_data["id"] = str(uuid.uuid4())

        # Insert the user
        await session.execute(
            "INSERT INTO users (id, name, email) VALUES (:id, :name, :email)", user_data
        )

        return user_data

    # Create the user
    created_user = await insert_user(session, user_data)

    # Get current span and add custom attribute
    span = get_current_span()
    if span:
        span.attributes["user.id"] = created_user["id"]
        span.add_event("user_created", attributes={"user_id": created_user["id"]})

    return {"user": created_user}


@app.get("/api/traces/examples")
async def run_trace_examples():
    """Run all tracing examples and return results."""
    logger.info("Running tracing examples")

    # Run the context manager example
    context_manager_result = await trace_with_context_manager()

    # Run the decorator example
    decorator_result = await trace_with_decorator(iterations=3)

    # Run the database example
    database_result = await trace_database_operations()

    return {
        "context_manager_example": context_manager_result,
        "decorator_example": decorator_result,
        "database_example": database_result,
    }


# Example of running all tracing examples
async def run_examples():
    """Run all tracing examples."""
    # Configure observability
    setup_observability()

    logger.info("Starting tracing examples")

    # Run examples
    try:
        # Example with context manager
        context_result = await trace_with_context_manager()
        logger.info(
            "Completed context manager example", extra={"result": context_result}
        )

        # Example with decorator
        decorator_result = await trace_with_decorator(iterations=3)
        logger.info("Completed decorator example", extra={"result": decorator_result})

        # Example with database operations
        db_result = await trace_database_operations()
        logger.info(
            "Completed database operations example", extra={"result": db_result}
        )

        logger.info("All examples completed successfully")

    except Exception as e:
        logger.exception(f"Error in examples: {str(e)}")

    # Let spans export
    await asyncio.sleep(1)

    # Shutdown tracing
    tracer = get_tracer()
    await tracer.shutdown()


if __name__ == "__main__":
    # Run the examples as a standalone script
    asyncio.run(run_examples())

    # To start the FastAPI app, uncomment:
    # import uvicorn
    # setup_observability()
    # uvicorn.run(app, host="0.0.0.0", port=8000)
