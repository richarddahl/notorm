# Repository Pattern

The repository pattern is a fundamental design pattern in Domain-Driven Design (DDD) that mediates between the domain and data mapping layers, acting like an in-memory collection of domain objects.

## Overview

In the uno framework, the repository pattern is implemented to provide a standardized interface for accessing domain entities, regardless of the underlying data store. This abstraction allows the domain layer to focus on business logic without concerning itself with persistence details.

## Core Components

### Base Repository Interface

The repository pattern in uno provides a standard interface for data access operations:

```python
from uno.domain.core import Entity
from uno.domain.repository_standardized import Repository

class ProductRepository(Repository[Product]):
    """Repository for managing products."""
    # Implement abstract methods
```

### Specification Pattern Integration

Repositories integrate with the specification pattern, allowing for complex querying:

```python
# Find products using a specification
spec = ProductSpecification.in_stock().and_(
    ProductSpecification.price_between(10.0, 50.0)
)
in_stock_affordable_products = await product_repository.find(spec)
```

### Unit of Work Integration

Repositories work with the Unit of Work pattern to ensure transactional consistency:

```python
async with get_unit_of_work() as uow:
    # Get the product repository
    product_repo = uow.get_repository(Product)
    
    # Make changes
    product = await product_repo.get_by_id("123")
    product.update_price(29.99)
    await product_repo.update(product)
    
    # Commit the transaction (or it will be rolled back on exception)
    await uow.commit()
```

## Repository Implementations

### SQLAlchemy Repository

The `SQLAlchemyRepository` provides integration with SQLAlchemy, supporting both ORM and Core approaches:

```python
from uno.domain.repository_standardized import SQLAlchemyRepository
from sqlalchemy.ext.asyncio import AsyncSession

# Create a SQLAlchemy repository
repo = SQLAlchemyRepository(
    entity_type=Product,
    session=async_session,
    model_class=ProductModel
)
```

### In-Memory Repository

The `InMemoryRepository` provides an in-memory implementation, useful for testing:

```python
from uno.domain.repository_standardized import InMemoryRepository

# Create an in-memory repository
repo = InMemoryRepository(entity_type=Product)
```

### Aggregate Repository

For aggregates that need event collection and additional lifecycle management:

```python
from uno.domain.repository_standardized import SQLAlchemyAggregateRepository
from uno.domain.core import AggregateRoot

class Order(AggregateRoot):
    """Order aggregate."""
    # Implement aggregate logic

# Create an aggregate repository
repo = SQLAlchemyAggregateRepository(
    aggregate_type=Order,
    session=async_session,
    model_class=OrderModel
)
```

## Repository Factory

The `RepositoryFactory` simplifies the creation of repositories:

```python
from uno.domain.repository_factory import repository_factory

# Register models
repository_factory.register_model(Product, ProductModel)
repository_factory.register_model(Order, OrderModel)

# Set up the database connection
repository_factory.create_from_connection_string(
    "postgresql+asyncpg://user:password@localhost/dbname"
)

# Create repositories
product_repo = repository_factory.create_repository(Product)
order_repo = repository_factory.create_repository(Order)
```

## Key Concepts

### Repository Methods

All repositories provide these core methods:

- `get(id)`: Get an entity by ID
- `find(specification)`: Find entities matching a specification
- `find_one(specification)`: Find a single entity matching a specification
- `list(filters, order_by, limit, offset)`: List entities with filtering and pagination
- `add(entity)`: Add a new entity
- `update(entity)`: Update an existing entity
- `remove(entity)`: Remove an entity
- `exists(id)`: Check if an entity exists
- `count(specification)`: Count entities matching a specification

### Result Pattern Integration

Repositories integrate with the Result pattern for better error handling:

```python
result = await product_repo.get_by_id_result("123")
if result.is_success:
    product = result.value
    # Use the product
else:
    # Handle the error
    error_message = result.error
```

### Specification Translators

The `SpecificationTranslator` converts domain specifications to database queries:

```python
from uno.domain.specification_translators import create_translator

# Create a translator
translator = create_translator(
    model_class=ProductModel,
    entity_type=Product,
    enhanced=True,
    postgres_specific=True
)

# Use the translator
query = translator.translate(specification)
```

## Best Practices

### Use Unit of Work for Transactions

Always use a unit of work when making multiple changes that need to be transactional:

```python
async with get_unit_of_work() as uow:
    # Get repositories
    order_repo = uow.get_repository(Order)
    product_repo = uow.get_repository(Product)
    
    # Make changes
    order = await order_repo.get_by_id("123")
    product = await product_repo.get_by_id(order.product_id)
    
    order.complete()
    product.decrement_stock(order.quantity)
    
    await order_repo.update(order)
    await product_repo.update(product)
    
    # Commit all changes at once
    await uow.commit()
```

### Collect Domain Events

For aggregates, use the repository to collect and publish domain events:

```python
# Save the aggregate, which collects events
order = await order_repo.save(order)

# Collect events from the repository
events = order_repo.collect_events()

# Publish events
for event in events:
    await event_bus.publish(event)
```

### Extend for Custom Logic

Extend the base repositories for domain-specific query methods:

```python
class CustomProductRepository(SQLAlchemyRepository[Product]):
    """Custom product repository with specialized queries."""
    
    async def find_featured_products(self) -> List[Product]:
        """Find featured products for the homepage."""
        spec = ProductSpecification.is_featured().and_(
            ProductSpecification.in_stock()
        )
        return await self.find(spec)
```

## Migration Guide

If you're migrating from the old repository pattern:

1. Replace imports from `uno.domain.repository` with `uno.domain.repository_standardized`
2. Use `Repository[T]` as the base class for your repositories
3. Use `SQLAlchemyRepository[T, M]` for SQLAlchemy repositories
4. Use `AggregateRepository[A]` for aggregate repositories
5. Use `SQLAlchemyAggregateRepository[A, M]` for SQLAlchemy aggregate repositories
6. Use the `RepositoryFactory` for creating repositories
7. Use the `UnitOfWorkManager` for managing transactions

For compatibility with existing code, you can use the `AsyncPostgreSQLRepository` class which provides the same interface as the old implementation but uses the new standardized pattern internally.

## Implementation Details

The standardized repository pattern consists of the following components:

- `Repository[T]`: Abstract base class for all repositories
- `AggregateRepository[A]`: Repository for aggregate roots
- `SQLAlchemyRepository[T, M]`: SQLAlchemy implementation
- `SQLAlchemyAggregateRepository[A, M]`: SQLAlchemy implementation for aggregates
- `InMemoryRepository[T]`: In-memory implementation
- `InMemoryAggregateRepository[A]`: In-memory implementation for aggregates
- `UnitOfWork`: Abstract unit of work
- `SQLAlchemyUnitOfWork`: SQLAlchemy implementation of unit of work
- `InMemoryUnitOfWork`: In-memory implementation of unit of work
- `UnitOfWorkManager`: Manager for multiple units of work
- `RepositoryFactory`: Factory for creating repositories
- `SpecificationFactory[T]`: Factory for creating specifications
- `SpecificationTranslator[T]`: Translator for specifications
- `SQLAlchemySpecificationTranslator[T, M]`: SQLAlchemy implementation of translator
- `PostgreSQLSpecificationTranslator[T, M]`: PostgreSQL-specific implementation of translator
- `EnhancedSpecificationTranslator[T, M]`: Enhanced implementation of translator

These components work together to provide a comprehensive implementation of the repository pattern that integrates with the rest of the uno framework.