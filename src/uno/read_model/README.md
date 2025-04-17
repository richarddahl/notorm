# Read Model Module

The Read Model module for the Uno framework implements the query side of the CQRS (Command Query Responsibility Segregation) pattern. It provides a robust framework for creating, managing, and querying read models optimized for specific query use cases.

## Overview

Read models are data structures optimized for specific query scenarios. Unlike domain models, which enforce business rules and maintain data consistency, read models are denormalized, flat structures designed for efficient queries. They are created and updated by projections applied to domain events.

The Read Model module consists of:

1. **Core entities**: ReadModel, Projection, Query, etc.
2. **Repository interfaces**: Type-safe protocols for data access
3. **Repository implementations**: Concrete implementations for different storage backends
4. **Services**: Business logic for working with read models
5. **Provider**: Dependency injection support
6. **Endpoints**: API endpoints for read model operations

## Repository Implementations

### In-Memory Repositories

Suitable for testing and simple applications:

- `InMemoryReadModelRepository`
- `InMemoryProjectionRepository`
- `InMemoryQueryRepository`
- `InMemoryCacheRepository`
- `InMemoryProjectorConfigurationRepository`

### PostgreSQL Repositories

Robust, production-ready implementations using PostgreSQL:

- `PostgresReadModelRepository`
- `PostgresProjectionRepository`
- `PostgresQueryRepository`
- `PostgresProjectorConfigurationRepository`

### Redis Cache Repository

Redis-based caching implementation:

- `RedisCacheRepository`

### Hybrid Implementation

Combines PostgreSQL persistence with Redis caching for optimal performance:

- `HybridReadModelRepository`

## Usage Examples

### Creating a Read Model

```python
from uno.read_model import ReadModel, ReadModelId
from datetime import datetime, UTC

class CustomerReadModel(ReadModel):
    """Customer read model for query optimization."""
    pass

# Create a new read model
customer = CustomerReadModel(
    id=ReadModelId(value="customer-123"),
    version=1,
    created_at=datetime.now(UTC),
    updated_at=datetime.now(UTC),
    data={
        "name": "John Doe",
        "email": "john.doe@example.com",
        "segment": "premium",
        "last_purchase_date": "2023-06-15"
    },
    metadata={
        "source": "customer_created_event"
    }
)
```

### Setting Up Repositories

```python
from uno.read_model import (
    PostgresReadModelRepository,
    PostgresProjectionRepository,
    HybridReadModelRepository
)

# Create a PostgreSQL repository
postgres_repo = PostgresReadModelRepository(
    model_type=CustomerReadModel,
    db_provider=db_provider,
    table_name="customer_read_models"
)

# Create the table if it doesn't exist
await postgres_repo.create_table_if_not_exists()

# Create a hybrid repository with caching
hybrid_repo = HybridReadModelRepository(
    model_type=CustomerReadModel,
    db_provider=db_provider,
    redis_cache=redis_cache,
    cache_ttl=3600,  # 1 hour
    cache_prefix="customer:"
)
```

### Working with Read Models

```python
# Save a read model
await repo.save(customer)

# Retrieve by ID
customer = await repo.get_by_id(ReadModelId("customer-123"))

# Find with criteria
premium_customers = await repo.find({"data.segment": "premium"})

# Save multiple read models in a batch
await repo.batch_save([customer1, customer2, customer3])

# Find with pagination
customers, total = await repo.find_with_pagination(
    criteria={"data.segment": "premium"},
    page=1,
    page_size=20,
    sort_by="updated_at",
    sort_direction="DESC"
)
```

### Working with Projections

```python
from uno.read_model import Projection, ProjectionId, ProjectionType

# Create a projection
customer_projection = Projection(
    id=ProjectionId(value="customer-created-projection"),
    name="CustomerCreatedProjection",
    event_type="CustomerCreated",
    read_model_type="CustomerReadModel",
    projection_type=ProjectionType.STANDARD,
    is_active=True,
    configuration={
        "fields_mapping": {
            "customer_id": "id",
            "customer_name": "name",
            "customer_email": "email"
        }
    }
)

# Save the projection
projection_repo = PostgresProjectionRepository(
    model_type=Projection,
    db_provider=db_provider
)
await projection_repo.save(customer_projection)

# Get projections for an event type
projections = await projection_repo.get_by_event_type("CustomerCreated")
```

### Cache Management with Hybrid Repository

```python
# The hybrid repository automatically manages the cache
customer = await hybrid_repo.get_by_id(ReadModelId("customer-123"))

# Update the customer (automatically updates cache)
customer = customer.update({"loyalty_points": 150})
await hybrid_repo.save(customer)

# Manually invalidate cache if needed
await hybrid_repo.invalidate_cache(ReadModelId("customer-123"))

# Invalidate all cache entries for this read model type
await hybrid_repo.invalidate_all_cache()
```

## Integration with CQRS

The Read Model module integrates with the CQRS pattern:

1. **Events** from the command side trigger **Projections**
2. **Projections** update **Read Models**
3. **Queries** retrieve data from **Read Models**

Example integration:

```python
# Query handler that uses a read model repository
class GetCustomerQueryHandler(QueryHandler[GetCustomerQuery, CustomerDTO]):
    def __init__(self, repository: ReadModelRepositoryProtocol[CustomerReadModel]):
        self.repository = repository
    
    async def handle(self, query: GetCustomerQuery) -> CustomerDTO:
        read_model = await self.repository.get_by_id(
            ReadModelId(query.customer_id)
        )
        
        if not read_model:
            raise EntityNotFoundError(f"Customer {query.customer_id} not found")
        
        # Map the read model to a DTO
        return CustomerDTO(
            id=read_model.id.value,
            name=read_model.data.get("name"),
            email=read_model.data.get("email"),
            segment=read_model.data.get("segment")
        )
```

## Best Practices

1. **Keep read models denormalized** and optimized for specific query scenarios
2. **Use the hybrid repository** for production workloads to benefit from caching
3. **Create separate read models** for different query needs rather than trying to make one model fit all scenarios
4. **Use batch operations** when working with multiple read models to improve performance
5. **Consider pagination** for queries that may return large result sets
6. **Version your projections** to handle schema evolution
7. **Use the appropriate repository implementation** for your environment (in-memory for tests, PostgreSQL for production, etc.)