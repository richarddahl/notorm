# Repository Pattern

The Repository Pattern is a fundamental design pattern in domain-driven design (DDD) that provides a clean separation between the domain model and data access logic. The Uno framework implements a comprehensive repository pattern that is flexible, composable, and well-integrated with the dependency injection system.

## Core Concepts

The repository pattern acts as a collection-like interface for accessing domain objects. It provides several key benefits:

1. **Separation of Concerns**: Domain logic remains separate from data access concerns
2. **Testability**: Services can be tested with mock repositories
3. **Flexibility**: The underlying persistence mechanism can be changed without affecting domain code
4. **Encapsulation**: Query complexity is hidden behind a simple interface

## Uno's Repository Implementation

Uno's repository implementation is located in `uno.infrastructure.repositories` and follows a layered architecture:

### 1. Protocols Layer

The foundation is a set of Protocol classes that define the interfaces for repositories:

- `RepositoryProtocol`: Core CRUD operations (get, list, add, update, delete)
- `SpecificationRepositoryProtocol`: Support for the Specification pattern
- `BatchRepositoryProtocol`: Batch operations for efficiency
- `StreamingRepositoryProtocol`: Streaming for large datasets
- `EventCollectingRepositoryProtocol`: Collecting domain events
- `AggregateRootRepositoryProtocol`: Special handling for aggregate roots

### 2. Abstract Base Layer

Abstract base classes provide shared functionality:

- `Repository`: Base implementation with utility methods
- `SpecificationRepository`: Implementation of specification support
- `BatchRepository`: Implementation of batch operations
- `StreamingRepository`: Implementation of streaming
- `EventCollectingRepository`: Implementation of event collection
- `AggregateRepository`: Implementation for aggregate roots
- `CompleteRepository`: Combines all features

### 3. Concrete Implementations

Two concrete implementations are provided:

- **SQLAlchemy**: For working with relational databases through SQLAlchemy ORM
- **InMemory**: For testing with in-memory storage

### 4. Unit of Work Pattern

The Unit of Work pattern coordinates operations across repositories:

- Manages transactions (begin, commit, rollback)
- Collects domain events from multiple repositories
- Ensures atomic operations across multiple repositories

### 5. Factory Pattern

Factories simplify repository creation:

- `RepositoryFactory`: Creates repositories based on entity type
- `UnitOfWorkFactory`: Creates units of work
- Helper functions like `create_repository()` and `create_unit_of_work()`

### 6. Dependency Injection

Integration with the DI system:

- `get_repository()`: Get a repository through DI
- `get_unit_of_work()`: Get a unit of work through DI
- `init_repository_system()`: Initialize during application startup

## Using Repositories

### Basic Usage

```python
from uno.infrastructure.repositories import get_repository

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

The Specification pattern encapsulates query criteria in separate objects:

```python
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

### With Unit of Work

The Unit of Work pattern coordinates operations across repositories:

```python
from uno.infrastructure.repositories import get_unit_of_work, get_repository

# Get a unit of work
uow = await get_unit_of_work(session=session)

# Use the unit of work
async with uow:
    # Get repositories
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
    
    # Collect events
    events = uow.collect_events()
    
    # Transaction is committed at the end of the context
```

## Repositories and Domain Events

Repositories that support event collection can collect domain events from entities:

```python
# Get a repository with event collection
order_repo = await get_repository(
    entity_type=OrderEntity,
    session=session,
    model_class=OrderModel,
    include_events=True
)

# Save an aggregate that raises events
order = await order_repo.add(new_order)

# Collect the events
events = order_repo.collect_events()

# Process the events
for event in events:
    await event_bus.publish(event)
```

## Testing with In-Memory Repositories

In-memory repositories are perfect for testing:

```python
# Use in-memory repository for testing
product_repo = await get_repository(
    entity_type=ProductEntity,
    in_memory=True,
    include_specification=True
)

# Test with the repository
service = ProductService(product_repo)
result = await service.create_product(...)

# Assertions
assert result.id is not None
assert await product_repo.count() == 1
```

## Best Practices

1. **Use dependency injection**: Get repositories through the DI system
2. **Use the Unit of Work pattern**: For coordinating operations across repositories
3. **Use specifications**: For encapsulating query criteria
4. **Use event collection**: For collecting domain events
5. **Use in-memory repositories**: For testing

## Configuration

Configure the repository system during application startup:

```python
from uno.infrastructure.repositories import init_repository_system

def startup():
    # Initialize repository system
    init_repository_system(
        session_factory=lambda: get_async_session(),
        logger=logging.getLogger("repositories")
    )
```

## Conclusion

The Uno repository pattern implementation provides a clean, flexible, and powerful abstraction for data access. It supports a wide range of capabilities including CRUD operations, specifications, batch operations, streaming, event collection, and more, all with a consistent interface.