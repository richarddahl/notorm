"""
Core module for the Uno framework.

This module provides core functionality for the Uno framework, including:
- Protocols for dependency injection
- Protocol validation utilities
- Domain-driven design building blocks
- Event-driven architecture
- CQRS pattern
- Unit of Work pattern
- Result pattern for error handling
- Configuration management
- Error handling framework
"""

# Import from protocols
from uno.core.protocols import (
    # Domain model protocols
    Entity,
    ValueObject,
    UnoEvent,
    AggregateRoot,
    # Repository and Unit of Work
    Repository,
    UnitOfWork,
    # Command and Query
    Command,
    Query,
    CommandHandler,
    QueryHandler,
    # Event system
    EventHandler,
    EventBus,
    # Dependency Injection
    ServiceProvider,
    ServiceScope,
    # Lifecycle
    Initializable,
    Disposable,
    AsyncDisposable,
    # Error handling
    Result,
    # Logging and monitoring
    Logger,
    Metric,
    MetricsProvider,
    # Common type definitions
    Pagination,
    Sorting,
    QueryOptions,
    # Type guards
    is_entity,
    is_value_object,
    is_aggregate_root,
    # Database protocols
    DatabaseSessionProtocol,
    DatabaseSessionContextProtocol,
    DatabaseSessionFactoryProtocol,
    DatabaseRepository,
)

# CQRS Pattern
from uno.core.cqrs import (
    # Command and Query base implementations
    BaseCommand,
    BaseQuery,
    # Command and Query handlers
    BaseCommandHandler,
    BaseQueryHandler,
    EventSourcingCommandHandler,
    # Command and Query buses
    CommandBus,
    QueryBus,
    HandlerRegistry,
    Mediator,
    # Handler registration
    command_handler,
    query_handler,
    # Mediator management
    initialize_mediator,
    reset_mediator,
    get_mediator,
    # API functions
    execute_command,
    execute_query,
)

# Error handling
from uno.core.errors.base import ErrorCategory, UnoError
from uno.core.errors.result import Success, Failure, Result
from uno.core.errors import (
    # Error context
    with_error_context,
    add_error_context,
    get_error_context,
    # Error catalog
    register_error,
    get_error_code_info,
    get_all_error_codes,
    # Validation
    ValidationError,
    ValidationContext,
    validate_fields,
    # Result pattern helpers
    of,
    failure,
    from_exception,
    from_awaitable,
    combine,
    combine_dict,
)

# Dependency Injection
from uno.core.di import (
    # Container management
    DIContainer,
    ServiceLifetime,
    ServiceRegistration,
    initialize_container,
    get_container,
    reset_container,
    # Service resolution
    get_service,
    create_scope,
    create_async_scope,
)

# FastAPI integration
from uno.core.di_fastapi import (
    # Dependency providers
    FromDI,
    ScopedDeps,
    create_request_scope,
    get_service as fastapi_get_service,
    # Application integration
    configure_di_middleware,
    register_app_shutdown,
)

# Testing utilities
from uno.core.di_testing import (
    # Test container
    TestContainer,
    test_container,
    # Mock injection
    inject_mock,
    create_test_scope,
)

__all__ = [
    # Domain model protocols
    "Entity",
    "ValueObject",
    "UnoEvent",
    "AggregateRoot",
    # Repository and Unit of Work
    "Repository",
    "UnitOfWork",
    # Command and Query protocols
    "Command",
    "Query",
    "CommandHandler",
    "QueryHandler",
    # CQRS implementations
    "BaseCommand",
    "BaseQuery",
    "BaseCommandHandler",
    "BaseQueryHandler",
    "EventSourcingCommandHandler",
    "CommandBus",
    "QueryBus",
    "HandlerRegistry",
    "Mediator",
    "command_handler",
    "query_handler",
    "initialize_mediator",
    "reset_mediator",
    "get_mediator",
    "execute_command",
    "execute_query",
    # Event system
    "EventHandler",
    "EventBus",
    # Dependency Injection protocols
    "ServiceProvider",
    "ServiceScope",
    # Lifecycle
    "Initializable",
    "Disposable",
    "AsyncDisposable",
    # Error handling
    "UnoError",
    "ErrorCategory",
    "Result",
    "Success",
    "Failure",
    # Error context
    "with_error_context",
    "add_error_context",
    "get_error_context",
    # Error catalog
    "register_error",
    "get_error_code_info",
    "get_all_error_codes",
    # Validation
    "ValidationError",
    "ValidationContext",
    "validate_fields",
    # Result pattern helpers
    "of",
    "failure",
    "from_exception",
    "from_awaitable",
    "combine",
    "combine_dict",
    # Logging and monitoring
    "Logger",
    "Metric",
    "MetricsProvider",
    # Common type definitions
    "Pagination",
    "Sorting",
    "QueryOptions",
    # Type guards
    "is_entity",
    "is_value_object",
    "is_aggregate_root",
    # Database protocols
    "DatabaseSessionProtocol",
    "DatabaseSessionContextProtocol",
    "DatabaseSessionFactoryProtocol",
    "DatabaseRepository",
    # DI Container
    "DIContainer",
    "ServiceLifetime",
    "ServiceRegistration",
    "initialize_container",
    "get_container",
    "reset_container",
    "get_service",
    "create_scope",
    "create_async_scope",
    # FastAPI integration
    "FromDI",
    "ScopedDeps",
    "create_request_scope",
    "fastapi_get_service",
    "configure_di_middleware",
    "register_app_shutdown",
    # Testing utilities
    "TestContainer",
    "test_container",
    "inject_mock",
    "create_test_scope",
]
