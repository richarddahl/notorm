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

# Protocols
from uno.core.protocols import (
    # Domain model protocols
    Entity, ValueObject, DomainEvent, AggregateRoot,
    
    # Repository and Unit of Work
    Repository, UnitOfWork,
    
    # Command and Query
    Command, Query, CommandHandler, QueryHandler,
    
    # Event system
    EventHandler, EventBus,
    
    # Dependency Injection
    ServiceProvider, ServiceScope,
    
    # Lifecycle
    Initializable, Disposable, AsyncDisposable,
    
    # Error handling
    Result,
    
    # Logging and monitoring
    Logger, Metric, MetricsProvider,
    
    # Common type definitions
    Pagination, Sorting, QueryOptions,
    
    # Type guards
    is_entity, is_value_object, is_aggregate_root
)

# Error handling
from uno.core.errors import (
    # Error categories
    ErrorCategory,
    
    # Error classes
    DomainError, ValidationError, NotFoundError,
    BusinessRuleError, ConflictError, AuthorizationError,
    
    # Type guards
    is_validation_error, is_not_found_error, is_business_rule_error,
    is_conflict_error, is_authorization_error, is_domain_error,
    
    # Result pattern
    Success, Failure, Result, success, failure,
    
    # Error context
    error_context_manager, with_error_context, with_async_error_context,
    
    # Helper functions
    from_awaitable, from_callable, from_async_callable
)

# Dependency Injection
from uno.core.di import (
    # Container management
    DIContainer, ServiceLifetime, ServiceRegistration,
    initialize_container, get_container, reset_container,
    
    # Service resolution
    get_service, create_scope, create_async_scope
)

# FastAPI integration
from uno.core.di_fastapi import (
    # Dependency providers
    FromDI, ScopedDeps, create_request_scope, get_service as fastapi_get_service,
    
    # Application integration
    configure_di_middleware, register_app_shutdown
)

# Testing utilities
from uno.core.di_testing import (
    # Test container
    TestContainer, test_container,
    
    # Mock injection
    inject_mock, create_test_scope
)

__all__ = [
    # Domain model protocols
    'Entity', 'ValueObject', 'DomainEvent', 'AggregateRoot',
    
    # Repository and Unit of Work
    'Repository', 'UnitOfWork',
    
    # Command and Query
    'Command', 'Query', 'CommandHandler', 'QueryHandler',
    
    # Event system
    'EventHandler', 'EventBus',
    
    # Dependency Injection protocols
    'ServiceProvider', 'ServiceScope',
    
    # Lifecycle
    'Initializable', 'Disposable', 'AsyncDisposable',
    
    # Error handling protocols
    'Result',
    
    # Logging and monitoring
    'Logger', 'Metric', 'MetricsProvider',
    
    # Common type definitions
    'Pagination', 'Sorting', 'QueryOptions',
    
    # Type guards
    'is_entity', 'is_value_object', 'is_aggregate_root',
    
    # Error categories
    'ErrorCategory',
    
    # Error classes
    'DomainError', 'ValidationError', 'NotFoundError',
    'BusinessRuleError', 'ConflictError', 'AuthorizationError',
    
    # Error type guards
    'is_validation_error', 'is_not_found_error', 'is_business_rule_error',
    'is_conflict_error', 'is_authorization_error', 'is_domain_error',
    
    # Result pattern
    'Success', 'Failure', 'Result', 'success', 'failure',
    
    # Error context
    'error_context_manager', 'with_error_context', 'with_async_error_context',
    
    # Helper functions
    'from_awaitable', 'from_callable', 'from_async_callable',
    
    # DI Container
    'DIContainer', 'ServiceLifetime', 'ServiceRegistration',
    'initialize_container', 'get_container', 'reset_container',
    'get_service', 'create_scope', 'create_async_scope',
    
    # FastAPI integration
    'FromDI', 'ScopedDeps', 'create_request_scope', 'fastapi_get_service',
    'configure_di_middleware', 'register_app_shutdown',
    
    # Testing utilities
    'TestContainer', 'test_container', 'inject_mock', 'create_test_scope'
]