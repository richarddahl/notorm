# Repository Pattern Implementation

This directory contains a comprehensive implementation of the repository pattern for the Uno framework, providing a clean separation between domain logic and data access.

## Overview

The repository pattern implementation in Uno is designed to be:

- **Unified**: A single, cohesive mechanism used consistently throughout the application
- **Flexible**: Supporting different persistence mechanisms and capabilities
- **Domain-friendly**: Integrating well with DDD concepts like entities, aggregates, and specifications
- **Testable**: With in-memory implementations for testing without database dependencies
- **Type-safe**: Using Python's type hints for clear interfaces and type checking

## Architecture

The repository pattern implementation uses a layered architecture:

1. **Protocols**: Interface definitions using Python Protocol classes for structural typing
2. **Base Classes**: Abstract base classes providing shared functionality
3. **Concrete Implementations**: SQLAlchemy and in-memory implementations
4. **Unit of Work**: Transaction and repository coordination
5. **Factory**: Simplified creation of repositories
6. **DI Integration**: All repositories are integrated via the central DI system.

## Key Components

### Protocols (`protocols.py`)

Defines the interface contracts that repositories must follow:

- `RepositoryProtocol`: Base interface for repository operations
- `SpecificationRepositoryProtocol`: Support for the Specification pattern
- `BatchRepositoryProtocol`: Support for batch operations
- `StreamingRepositoryProtocol`: Support for streaming large result sets
- `EventCollectingRepositoryProtocol`: Support for collecting domain events
- `AggregateRootRepositoryProtocol`: Support for aggregate roots
- `UnitOfWorkProtocol`: Interface for the Unit of Work pattern

### Base Classes (`base.py`)

Abstract base classes implementing the protocols:

- `Repository`: Base repository implementation
- `SpecificationRepository`: Support for the Specification pattern
- `BatchRepository`: Support for batch operations
- `StreamingRepository`: Support for streaming large result sets
- `EventCollectingRepository`: Support for collecting domain events
- `AggregateRepository`: Support for aggregate roots
- `CompleteRepository`: Combines all repository capabilities

### SQLAlchemy Implementation (`sqlalchemy.py`)

Concrete implementations using SQLAlchemy:

- `SQLAlchemyRepository`: SQLAlchemy implementation of the repository pattern
- `SQLAlchemySpecificationRepository`: With specification support
- `SQLAlchemyBatchRepository`: With batch support
- `SQLAlchemyStreamingRepository`: With streaming support
- `SQLAlchemyEventCollectingRepository`: With event collection
- `SQLAlchemyAggregateRepository`: For aggregate roots
- `SQLAlchemyCompleteRepository`: With all capabilities

### In-Memory Implementation (`in_memory.py`)

Implementations using dictionaries for testing:

- `InMemoryRepository`: In-memory implementation of the repository pattern
- `InMemorySpecificationRepository`: With specification support
- `InMemoryBatchRepository`: With batch support
- `InMemoryStreamingRepository`: With streaming support
- `InMemoryEventCollectingRepository`: With event collection
- `InMemoryAggregateRepository`: For aggregate roots
- `InMemoryCompleteRepository`: With all capabilities

### Unit of Work (`unit_of_work.py`)

Implementation of the Unit of Work pattern:

- `UnitOfWork`: Base Unit of Work implementation
- `SQLAlchemyUnitOfWork`: SQLAlchemy implementation
- `InMemoryUnitOfWork`: In-memory implementation for testing

### Factory (`factory.py`)

Factory for creating repositories:

- `RepositoryFactory`: Factory for creating repositories
- `UnitOfWorkFactory`: Factory for creating units of work
- Helper functions for working with the factories

### Dependency Injection

All repositories and services are registered and resolved via the central DI system. No ad hoc or legacy patterns remain.

Integration with the DI system:

- `init_repository_system`: Initialize the repository system
- `get_repository`: Get a repository through DI
- `get_unit_of_work`: Get a unit of work through DI
- `register_specification_translator`: Register a specification translator

## Usage

### Basic Usage

```python
# Import the repository components
from uno.infrastructure.repositories import get_repository, Repository

# Get a repository for a specific entity type
product_repo = await get_repository(
    entity_type=ProductEntity,
    session=session,
    model_class=ProductModel
)

# Basic CRUD operations
product = await product_repo.get(product_id)
products = await product_repo.list(filters={"category": "Electronics"})
new_product = await product_repo.add(product)
updated_product = await product_repo.update(product)
await product_repo.delete(product)
```

### With Specifications

```python
# Import components
from uno.infrastructure.repositories import get_repository
from uno.domain.specifications import Specification

# Define specifications
class ProductByPriceRange(Specification[ProductEntity]):
    def __init__(self, min_price: float, max_price: float):
        self.min_price = min_price
        self.max_price = max_price
    
    def is_satisfied_by(self, product: ProductEntity) -> bool:
        return self.min_price <= product.price <= self.max_price

# Get a repository with specification support
product_repo = await get_repository(
    entity_type=ProductEntity,
    session=session,
    model_class=ProductModel,
    include_specification=True
)

# Use the specification
price_spec = ProductByPriceRange(50.0, 150.0)
matching_products = await product_repo.find(price_spec)
```

### With Batch Operations

```python
# Get a repository with batch support
product_repo = await get_repository(
    entity_type=ProductEntity,
    session=session,
    model_class=ProductModel,
    include_batch=True
)

# Perform batch operations
products_to_add = [Product(...), Product(...), Product(...)]
added_products = await product_repo.add_many(products_to_add)

products_to_update = [product1, product2, product3]
updated_products = await product_repo.update_many(products_to_update)

await product_repo.delete_many([product1, product2])
```

### With Streaming

```python
# Get a repository with streaming support
product_repo = await get_repository(
    entity_type=ProductEntity,
    session=session,
    model_class=ProductModel,
    include_streaming=True
)

# Stream large datasets
async for product in product_repo.stream(filters={"category": "Electronics"}):
    # Process each product individually without loading the entire dataset
    process_product(product)
```

### With Event Collection

```python
# Get a repository with event collection support
order_repo = await get_repository(
    entity_type=OrderEntity,
    session=session,
    model_class=OrderModel,
    include_events=True
)

# Add or update an aggregate that raises events
order = await order_repo.add(new_order)

# Collect the events
events = order_repo.collect_events()

# Process the events
for event in events:
    await event_bus.publish(event)
```

### With Unit of Work

```python
# Import the unit of work
from uno.infrastructure.repositories import get_unit_of_work

# Get a unit of work
uow = await get_unit_of_work(session=session)

# Use the unit of work for transactional operations
async with uow:
    # Get repositories within the transaction
    product_repo = await get_repository(
        entity_type=ProductEntity,
        session=session,
        model_class=ProductModel
    )
    
    order_repo = await get_repository(
        entity_type=OrderEntity,
        session=session,
        model_class=OrderModel
    )
    
    # Perform operations in a single transaction
    product = await product_repo.add(product)
    order = OrderEntity(...)
    order.add_item(OrderItemEntity(product_id=product.id, ...))
    await order_repo.add(order)
    
    # Commit the transaction at the end of the context
```

### Using Factories Directly

```python
# Import factory functions
from uno.infrastructure.repositories import create_repository, create_unit_of_work

# Create a repository explicitly
repository = create_repository(
    entity_type=ProductEntity,
    session_or_model=session,
    model_class=ProductModel,
    include_specification=True,
    include_batch=True
)

# Create a unit of work explicitly
uow = create_unit_of_work(session=session)
```

## Application Startup

Initialize the repository system during application startup:

```python
from uno.infrastructure.repositories import init_repository_system

def startup():
    # Initialize the repository system with a session factory and logger
    init_repository_system(
        session_factory=lambda: get_async_session(),
        logger=logging.getLogger("repositories")
    )
```

## Testing with In-Memory Repositories

The in-memory implementation is perfect for testing:

```python
from uno.infrastructure.repositories import get_repository

async def test_product_service():
    # Create an in-memory repository for testing
    product_repo = await get_repository(
        entity_type=ProductEntity,
        in_memory=True,  # Use in-memory implementation
        include_specification=True
    )
    
    # Test with the repository
    service = ProductService(product_repo)
    result = await service.create_product(...)
    
    # Assertions
    assert result.id is not None
    assert await product_repo.count() == 1
```

## FastAPI Integration

Example of using repositories with FastAPI:

```python
from fastapi import Depends, FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.database import get_async_session
from uno.infrastructure.repositories import get_repository, Repository

app = FastAPI()

# Define a dependency to get a repository
async def get_product_repository(
    session: AsyncSession = Depends(get_async_session)
) -> Repository[ProductEntity, int]:
    return await get_repository(
        entity_type=ProductEntity,
        session=session,
        model_class=ProductModel,
        include_specification=True
    )

# Use it in endpoints
@app.get("/products/{product_id}")
async def get_product(
    product_id: int,
    product_repo: Repository[ProductEntity, int] = Depends(get_product_repository)
):
    product = await product_repo.get(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```