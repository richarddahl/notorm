# Read Model API

The Read Model module provides functionality for implementing the query side of the CQRS (Command Query Responsibility Segregation) pattern. It offers a rich set of tools for creating and managing read models, which are optimized data structures for specific query use cases.

## Overview

Read models are updated through projections that transform domain events from the command side. This module provides a complete infrastructure for:

- Creating and managing read models
- Defining projections to transform domain events
- Executing queries against read models
- Caching read models for improved performance
- Managing the event processing pipeline

## Key Components

### Core Entities

- **ReadModel**: Base entity for read models, optimized data structures for specific query use cases
- **Projection**: Defines how domain events are transformed into read models
- **Query**: Used to retrieve read models in a type-safe way
- **ProjectorConfiguration**: Configuration for a projector that manages multiple projections

### Repositories

The module provides repository interfaces with memory and database implementations:

- **ReadModelRepository**: For storing and retrieving read models
- **ProjectionRepository**: For managing projection definitions
- **QueryRepository**: For storing and retrieving queries
- **CacheRepository**: For caching read models
- **ProjectorConfigurationRepository**: For storing projector configurations

### Services

The business logic is encapsulated in these service interfaces:

- **ReadModelService**: Business logic for managing read models, with caching support
- **ProjectionService**: Business logic for managing projections and applying events
- **CacheService**: Service for caching read models and other data
- **QueryService**: Service for executing queries against read models
- **ProjectorService**: Service for managing the event processing pipeline

### Infrastructure

- **ReadModelProvider**: Configures dependency injection for the Read Model module
- **ReadModelEndpoints** & **ProjectionEndpoints**: Factory classes for creating FastAPI endpoints

## Usage Examples

### Creating a Read Model

```python
from datetime import datetime, UTC
from uno.read_model import ReadModel, ReadModelId

# Create a read model
product_read_model = ReadModel(
    id=ReadModelId(value="product-123"),
    version=1,
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
    data={
        "name": "Product 123",
        "description": "A sample product",
        "price": 99.99
    },
    metadata={
        "category": "sample"
    }
)

# Update the read model with new data
updated_model = product_read_model.update({
    "price": 89.99,
    "on_sale": True
})
```

### Defining a Projection

```python
from uno.read_model import Projection, ProjectionId, ProjectionType
from uno.domain.events import ProductCreatedEvent

# Define a projection for product events
product_projection = Projection(
    id=ProjectionId(value="product-projection"),
    name="Product Projection",
    event_type=ProductCreatedEvent.__name__,
    read_model_type="ProductReadModel",
    projection_type=ProjectionType.STANDARD,
    is_active=True,
    configuration={
        "include_inventory": True
    }
)
```

### Using the Read Model Service

```python
from uno.read_model import ReadModelService, InMemoryReadModelRepository
from uno.core.result import Success, Failure

# Create a repository and service
repository = InMemoryReadModelRepository(model_type=ProductReadModel)
service = ReadModelService(
    repository=repository,
    model_type=ProductReadModel
)

# Save a read model
result = await service.save(product_read_model)

if result.is_success():
    print(f"Saved product read model: {result.value.id.value}")
else:
    print(f"Error: {result.error.message}")

# Get a read model by ID
product_id = ReadModelId(value="product-123")
result = await service.get_by_id(product_id)

if result.is_success() and result.value:
    print(f"Found product: {result.value.data['name']}")
```

### Setting Up the Projector

```python
from uno.read_model import ProjectorService, ProjectionService
from uno.domain.events import EventBus, EventStore

# Create a projector service
projector_service = ProjectorService(
    event_bus=event_bus,
    event_store=event_store,
    projection_service=projection_service,
    projector_config_repository=config_repository,
    config_name="product-projector",
    async_processing=True
)

# Start the projector
await projector_service.start()

# Register a projection
await projector_service.register_projection(product_projection)
```

### Creating FastAPI Endpoints

```python
from fastapi import APIRouter, Depends
from uno.read_model import ReadModelEndpoints, ProjectionEndpoints

# Create a FastAPI router
app = APIRouter()

# Create endpoints for a specific read model type
product_router = ReadModelEndpoints.create_router(
    model_type=ProductReadModel,
    prefix="/api/products",
    read_model_service=product_service,
    query_service=product_query_service,
    tags=["Products"]
)

# Add the router to the application
app.include_router(product_router)
```

## Integration with Other Modules

The Read Model module integrates with:

- **Domain Events**: Receives events from the event bus to update read models
- **Database**: Stores read models and projections in the database
- **Caching**: Caches read models for improved performance
- **API**: Exposes read models through FastAPI endpoints

## Best Practices

1. **Design read models for specific use cases**: Each read model should be optimized for a specific query scenario.

2. **Use projections to transform events**: Define projections to update read models based on domain events.

3. **Enable caching for frequently accessed read models**: Use the caching infrastructure to improve performance.

4. **Process events asynchronously**: Use async projectors for improved scalability.

5. **Implement proper error handling**: Use the Result pattern for error handling in services and repositories.

6. **Use dependency injection**: Configure dependencies with the ReadModelProvider.

7. **Create typed interfaces**: Leverage generic types for type-safe read model operations.

## API Reference

See the [UnoObj API Documentation](../api/overview.md) for detailed information on the base classes and interfaces.

## Further Reading

- [CQRS Architecture](../architecture/cqrs.md)
- [Event-Driven Architecture](../architecture/event_driven_architecture.md)
- [Domain-Driven Design](../architecture/domain_driven_design.md)