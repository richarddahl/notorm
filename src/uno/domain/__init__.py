"""
Domain module for domain-driven design patterns.

This module implements a domain-driven design (DDD) approach for the Uno framework,
providing a clear separation of concerns and a rich domain model.

It contains implementations of domain-driven design patterns including entities,
value objects, aggregates, repositories, and specifications.
"""

import warnings

# Core domain models, protocols, and factories
from uno.domain.models import (
    UnoEvent,
    ValueObject,
    PrimitiveValueObject,
    Entity,
    AggregateRoot,
)
# Domain model components

from uno.domain.protocols import (
    DomainEventProtocol,
    ValueObjectProtocol,
    PrimitiveValueObjectProtocol,
    EntityProtocol,
    AggregateRootProtocol,
    SpecificationProtocol,
    EntityFactoryProtocol,
    CommandResultProtocol,
    DomainServiceProtocol,
)

from uno.domain.factories import (
    EntityFactory,
    AggregateFactory,
    ValueObjectFactory,
    FactoryRegistry,
    create_entity_factory,
    create_aggregate_factory,
    create_value_factory,
)

from uno.domain.specifications import (
    Specification,
    AndSpecification,
    OrSpecification,
    NotSpecification,
    AttributeSpecification,
    PredicateSpecification,
    DictionarySpecification,
    specification_factory,
    specification_from_predicate,
)

# Specification translators
from uno.domain.specification_translators import (
    SpecificationTranslator,
    PostgreSQLSpecificationTranslator,
    PostgreSQLRepository,
    AsyncPostgreSQLRepository,
)

# Repository pattern is now imported from infrastructure module
# See uno.infrastructure.repositories for the unified repository implementation

# Include compatibility imports for backward compatibility
# These will be removed in a future version
from uno.domain.core import DomainException

# Business logic
from uno.domain.service import DomainService

# Event sourcing and event store
try:
    from uno.core.events import (
        EventHandler,
        EventBus,
        EventStore,
        InMemoryEventStore,
        EventPublisher,
        get_event_bus,
        get_event_store,
        get_event_publisher,
    )

    from uno.domain.event_store import (
        EventStore as EventStoreBase,
        PostgresEventStore,
        EventSourcedRepository,
    )

    from uno.domain.event_store_manager import EventStoreManager

    from uno.domain.event_store_integration import (
        EventStoreIntegration,
        get_event_store_integration,
        get_event_sourced_repository,
    )

    has_event_store = True
except ImportError:
    has_event_store = False

# Query system
try:
    from uno.domain.query import (
        QuerySpecification,
        QueryResult,
        QueryExecutor,
        RepositoryQueryExecutor,
        FilterQueryExecutor,
        QueryService,
    )

    # Enhanced query system
    from uno.domain.enhanced_query import QueryMetadata, EnhancedQueryExecutor

    from uno.domain.query_optimizer import (
        QueryPerformanceTracker,
        QueryPerformanceMetric,
        QueryResultCache,
        GraphQueryOptimizer,
        MaterializedQueryView,
    )

    from uno.domain.selective_updater import (
        GraphChangeEvent,
        SelectiveGraphUpdater,
        GraphSynchronizer,
    )

    from uno.domain.graph_path_query import (
        PathQuerySpecification,
        GraphPathQuery,
        GraphPathQueryService,
    )

    event_store_components = []
    if has_event_store:
        event_store_components = [
            # Event sourcing
            "EventHandler",
            "EventBus",
            "EventStore",
            "InMemoryEventStore",
            "EventPublisher",
            "get_event_bus",
            "get_event_store",
            "get_event_publisher",
            # Event store
            "EventStoreBase",
            "PostgresEventStore",
            "EventSourcedRepository",
            "EventStoreManager",
            # Event store integration
            "EventStoreIntegration",
            "get_event_store_integration",
            "get_event_sourced_repository",
        ]

    # New domain model components
    domain_model_components = [
        # Core domain models
        "UnoEvent",
        "ValueObject",
        "PrimitiveValueObject",
        "Entity",
        "AggregateRoot",
        "Email",
        "Money",
        "Address",
        # Domain protocols
        "DomainEventProtocol",
        "ValueObjectProtocol",
        "PrimitiveValueObjectProtocol",
        "EntityProtocol",
        "AggregateRootProtocol",
        "SpecificationProtocol",
        "EntityFactoryProtocol",
        "DomainServiceProtocol",
        # Domain factories
        "EntityFactory",
        "AggregateFactory",
        "ValueObjectFactory",
        "FactoryRegistry",
        "create_entity_factory",
        "create_aggregate_factory",
        "create_value_factory",
        # Specifications
        "Specification",
        "AndSpecification",
        "OrSpecification",
        "NotSpecification",
        "AttributeSpecification",
        "PredicateSpecification",
        "DictionarySpecification",
        "specification_factory",
        "specification_from_predicate",
        "specification_from_predicate",
        # Specification translators
        "SpecificationTranslator",
        "PostgreSQLSpecificationTranslator",
        "PostgreSQLRepository",
        "AsyncPostgreSQLRepository",
        # Repository pattern now in infrastructure module
    ]

    # Legacy for backward compatibility (will be removed)
    legacy_components = [
        "DomainException",
    ]

    __all__ = (
        domain_model_components
        + legacy_components
        + [
            # Business logic
            "DomainService",
            # Query system
            "QuerySpecification",
            "QueryResult",
            "QueryExecutor",
            "RepositoryQueryExecutor",
            "FilterQueryExecutor",
            "QueryService",
            # Enhanced query system
            "QueryMetadata",
            "EnhancedQueryExecutor",
            "QueryPerformanceTracker",
            "QueryPerformanceMetric",
            "QueryResultCache",
            "GraphQueryOptimizer",
            "MaterializedQueryView",
            "GraphChangeEvent",
            "SelectiveGraphUpdater",
            "GraphSynchronizer",
            "PathQuerySpecification",
            "GraphPathQuery",
            "GraphPathQueryService",
        ]
        + event_store_components
    )

except ImportError:
    # In case some enhanced query components aren't available yet
    event_store_components = []
    if has_event_store:
        event_store_components = [
            # Event sourcing
            "EventHandler",
            "EventBus",
            "EventStore",
            "InMemoryEventStore",
            "EventPublisher",
            "get_event_bus",
            "get_event_store",
            "get_event_publisher",
            # Event store
            "EventStoreBase",
            "PostgresEventStore",
            "EventSourcedRepository",
            "EventStoreManager",
            # Event store integration
            "EventStoreIntegration",
            "get_event_store_integration",
            "get_event_sourced_repository",
        ]

    # New domain model components
    domain_model_components = [
        # Core domain models
        "UnoEvent",
        "ValueObject",
        "PrimitiveValueObject",
        "Entity",
        "AggregateRoot",
        "Email",
        "Money",
        "Address",
        # Domain protocols
        "DomainEventProtocol",
        "ValueObjectProtocol",
        "PrimitiveValueObjectProtocol",
        "EntityProtocol",
        "AggregateRootProtocol",
        "SpecificationProtocol",
        "EntityFactoryProtocol",
        "DomainServiceProtocol",
        # Domain factories
        "EntityFactory",
        "AggregateFactory",
        "ValueObjectFactory",
        "FactoryRegistry",
        "create_entity_factory",
        "create_aggregate_factory",
        "create_value_factory",
        # Specifications
        "Specification",
        "AndSpecification",
        "OrSpecification",
        "NotSpecification",
        "AttributeSpecification",
        "PredicateSpecification",
        "DictionarySpecification",
        "specification_factory",
        # Specification translators
        "SpecificationTranslator",
        "PostgreSQLSpecificationTranslator",
        "PostgreSQLRepository",
        "AsyncPostgreSQLRepository",
        # Repository pattern now in infrastructure module
    ]

    # Legacy for backward compatibility (will be removed)
    legacy_components = [
        "DomainException",
    ]

    __all__ = (
        domain_model_components
        + legacy_components
        + [
            # Business logic
            "DomainService",
        ]
        + event_store_components
    )

# Display a warning to encourage using the new imports directly
warnings.warn(
    "For improved code organization, import domain model components directly from:\n"
    "- uno.domain.models (Entity, ValueObject, etc.)\n"
    "- uno.domain.protocols (EntityProtocol, ValueObjectProtocol, etc.)\n"
    "- uno.domain.factories (EntityFactory, create_entity_factory, etc.)\n"
    "- uno.domain.specifications (Specification, AttributeSpecification, etc.)\n"
    "- uno.domain.specification_translators (PostgreSQLSpecificationTranslator, etc.)\n"
    "- For repository pattern, use uno.infrastructure.repositories",
    DeprecationWarning,
    stacklevel=2,
)
