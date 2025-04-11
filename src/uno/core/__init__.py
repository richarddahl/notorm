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
"""

# Protocols
from uno.core.protocols import (
    # DDD building blocks
    Entity, AggregateRoot, ValueObject,
    
    # Event-driven architecture
    DomainEvent, EventHandler, EventBus,
    
    # CQRS patterns
    Command, CommandHandler, Query, QueryHandler,
    
    # Repository pattern
    Repository, UnitOfWork,
    
    # Error handling
    Result,
    
    # Caching
    Cache,
    
    # Configuration
    ConfigProvider,
    
    # Resource management
    ResourceManager,
    
    # Messaging
    MessagePublisher, MessageConsumer,
    
    # Plugin architecture
    Plugin, PluginManager,
    
    # Health checks
    HealthCheck, HealthCheckRegistry
)

# Domain-driven design
from uno.core.domain import (
    BaseEntity, AggregateEntity, BaseValueObject,
    DomainService, Repository, DomainValidator
)

# Event-driven architecture
from uno.core.events import (
    BaseDomainEvent, BaseEventHandler, SimpleEventBus,
    TypedEventBus, AsyncEventBus, DomainEventPublisher,
    event_handler, DomainEventProcessor
)

# CQRS pattern
from uno.core.cqrs import (
    BaseCommand, BaseQuery, BaseCommandHandler, BaseQueryHandler,
    CommandBus, QueryBus, HandlerRegistry,
    command_handler, query_handler
)

# Unit of Work pattern
from uno.core.uow import (
    AbstractUnitOfWork, DatabaseUnitOfWork,
    ContextUnitOfWork, transaction
)

# Result pattern
from uno.core.result import (
    Success, Failure, of, failure, from_exception,
    from_awaitable, combine, combine_dict
)

# Configuration management
from uno.core.config import (
    ConfigurationError, ConfigSource, DictConfigSource,
    EnvironmentConfigSource, FileConfigSource,
    ConfigurationService, ConfigurationOptions
)

# Protocol validation
from uno.core.protocol_validator import (
    validate_protocol, validate_implementation, 
    find_protocol_implementations, implements,
    verify_all_implementations, ProtocolValidationError
)

__all__ = [
    # DDD building blocks
    'Entity', 'AggregateRoot', 'ValueObject',
    'BaseEntity', 'AggregateEntity', 'BaseValueObject',
    'DomainService', 'Repository', 'DomainValidator',
    
    # Event-driven architecture
    'DomainEvent', 'EventHandler', 'EventBus',
    'BaseDomainEvent', 'BaseEventHandler', 'SimpleEventBus',
    'TypedEventBus', 'AsyncEventBus', 'DomainEventPublisher',
    'event_handler', 'DomainEventProcessor',
    
    # CQRS patterns
    'Command', 'CommandHandler', 'Query', 'QueryHandler',
    'BaseCommand', 'BaseQuery', 'BaseCommandHandler', 'BaseQueryHandler',
    'CommandBus', 'QueryBus', 'HandlerRegistry',
    'command_handler', 'query_handler',
    
    # Unit of Work pattern
    'UnitOfWork', 'AbstractUnitOfWork', 'DatabaseUnitOfWork',
    'ContextUnitOfWork', 'transaction',
    
    # Result pattern
    'Result', 'Success', 'Failure', 'of', 'failure',
    'from_exception', 'from_awaitable', 'combine', 'combine_dict',
    
    # Configuration management
    'ConfigProvider', 'ConfigurationError', 'ConfigSource',
    'DictConfigSource', 'EnvironmentConfigSource', 'FileConfigSource',
    'ConfigurationService', 'ConfigurationOptions',
    
    # Resource management
    'ResourceManager',
    
    # Caching
    'Cache',
    
    # Messaging
    'MessagePublisher', 'MessageConsumer',
    
    # Plugin architecture
    'Plugin', 'PluginManager',
    
    # Health checks
    'HealthCheck', 'HealthCheckRegistry',
    
    # Protocol validation
    'validate_protocol', 'validate_implementation',
    'find_protocol_implementations', 'implements',
    'verify_all_implementations', 'ProtocolValidationError'
]