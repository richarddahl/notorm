# Migrating to the Unified Domain-Driven Design Approach

This guide explains how to migrate existing code to the unified domain-driven design (DDD) approach implemented in the Uno framework.

## Overview

The Uno framework now provides a standardized, consistent implementation of domain-driven design patterns. This includes:

1. **Unified Domain Events**: A standardized event system in `uno.core.unified_events`
2. **Unified Domain Services**: A standardized service pattern in `uno.domain.unified_services`
3. **Standardized Domain Model**: Consistent entity, aggregate, and value object patterns in `uno.domain.core`
4. **Standardized Repository Pattern**: DDD-compliant repository implementation in `uno.domain.repository`
5. **API Integration**: Standardized approach for integrating domain services with API endpoints

To support a smooth migration, we've provided adapter classes that allow integrating legacy code with the new patterns while you gradually migrate your codebase.

## Migration Strategy

We recommend a gradual migration strategy:

1. Start by migrating domain events to the unified implementation
2. Then migrate repositories to the standardized pattern
3. Next, migrate domain services to the unified approach
4. Finally, update API endpoints to use the service endpoint factory

This approach allows you to migrate one component at a time, without needing to change everything at once.

## Migrating Domain Events

### Before
```python
# Old approach with multiple event implementations
from uno.domain.models import UnoDomainEvent

class OrderCreatedEvent(UnoDomainEvent):
    order_id: str
    customer_id: str
```

### After
```python
# New approach using the unified event system
from uno.core.unified_events import UnoDomainEvent

class OrderCreatedEvent(UnoDomainEvent):
    order_id: str
    customer_id: str
```

### Using Event Adapter for Legacy Code

If you have legacy code that depends on the old event interfaces, use the adapter pattern to maintain compatibility while migrating:

```python
from uno.core.unified_events import UnoDomainEvent as CanonicalEvent

# Temporary compatibility layer
class LegacyUnoDomainEvent(CanonicalEvent):
    # Add any methods or properties needed for backward compatibility
    pass
```

## Migrating Repositories

### Before
```python
# Old approach with multiple repository implementations
from uno.dependencies.repository import UnoRepository

class ProductRepository(UnoRepository):
    def __init__(self):
        super().__init__(ProductModel)
    
    async def find_by_category(self, category_id: str):
        # Custom implementation
        pass
```

### After
```python
# New approach using the standardized repository pattern
from uno.domain.repository import SQLAlchemyRepository

class ProductRepository(SQLAlchemyRepository[Product, ProductModel]):
    def __init__(self, session):
        super().__init__(Product, session, ProductModel)
    
    async def find_by_category(self, category_id: str):
        # Implementation using standardized patterns
        pass
```

### Using Repository Adapter for Legacy Code

If you have legacy code that depends on the old repository interfaces, use the repository adapter:

```python
from uno.domain.repository_adapter import StandardRepositoryAdapter

# Wrap the standardized repository
legacy_compatible_repo = StandardRepositoryAdapter(standard_repository)

# Use it with legacy code
await legacy_compatible_repo.get_by_id(product_id)
```

## Migrating Domain Services

### Before
```python
# Old approach with multiple service implementations
from uno.domain.service import UnoEntityService

class ProductService(UnoEntityService):
    def __init__(self, repository):
        self.repository = repository
    
    async def update_price(self, id: str, new_price: float):
        product = await self.repository.get(id)
        product.price = new_price
        return await self.repository.update(product)
```

### After
```python
# New approach using the unified service pattern
from uno.domain.unified_services import DomainService
from uno.core.errors.result import Success, Failure

class UpdateProductPriceInput(BaseModel):
    id: str
    price: float

class ProductPriceService(DomainService[UpdateProductPriceInput, Product, UnitOfWork]):
    async def _execute_internal(self, input_data: UpdateProductPriceInput) -> Result[Product]:
        # Get product from repository
        product = await self.uow.products.get(input_data.id)
        if not product:
            return Failure(f"Product with ID {input_data.id} not found")
        
        # Update price
        product.price = input_data.price
        product.update()
        
        # Update in repository
        updated_product = await self.uow.products.update(product)
        
        return Success(updated_product)
```

### Using Service Adapter for Legacy Code

If you have legacy code that depends on the old service interfaces, use the service adapter:

```python
from uno.domain.service_adapter import StandardServiceAdapter

# Wrap the standardized service
legacy_compatible_service = StandardServiceAdapter(standard_service)

# Use it with legacy code
product = await legacy_compatible_service.update_price(id="123", new_price=29.99)
```

## Migrating API Endpoints

### Before
```python
# Old approach with direct service calls
@router.post("/products/{id}/price")
async def update_product_price(
    id: str, 
    price_data: dict,
    service: ProductService = Depends(get_product_service)
):
    product = await service.update_price(id, price_data["price"])
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
```

### After
```python
# New approach using service endpoint factory
from uno.api.service_endpoint_factory import get_domain_service_endpoint_factory

factory = get_domain_service_endpoint_factory()

# Create endpoint from domain service
factory.create_domain_service_endpoint(
    router=router,
    service_class=ProductPriceService,
    path="/products/{id}/price",
    method="POST",
    summary="Update Product Price",
    response_model=ProductOutput
)
```

## Using Module Registry for Migration

To facilitate migration, we've provided registries for repositories and services. Register your implementations to make them discoverable by other modules:

```python
# In your module's __init__.py
from uno.domain.repository_adapter import register_repository_implementation
from uno.domain.service_adapter import register_service_implementation

# Register implementations
register_repository_implementation("products", ProductRepository)
register_service_implementation("products", "price_service", ProductPriceService)
```

## Code Cleanup and Deprecation

The following implementations are now deprecated and will be removed in a future version:

1. `uno.core.domain.UnoDomainEvent` - Use `uno.core.unified_events.UnoDomainEvent` instead
2. `uno.core.protocols.UnoDomainEvent` - Use `uno.core.unified_events.DomainEventProtocol` instead
3. `uno.domain.core.UnoDomainEvent` - Use `uno.core.unified_events.UnoDomainEvent` instead
4. `uno.domain.models.UnoDomainEvent` - Use `uno.core.unified_events.UnoDomainEvent` instead
5. `uno.domain.service` - Use `uno.domain.unified_services` instead
6. `uno.domain.services` - Use `uno.domain.unified_services` instead
7. `uno.dependencies.repository.UnoRepository` - Use `uno.domain.repository` classes instead
8. `uno.infrastructure.database.repository` - Use `uno.domain.repository` classes instead

These modules now include deprecation warnings to alert you when you're using deprecated implementations.

## Migration Help and Troubleshooting

If you encounter issues during migration, check the following:

1. **Dependency Injection**: Make sure your services and repositories are properly registered in the DI container
2. **Type Hints**: Ensure you're using proper type hints with the new generic implementations
3. **Result Pattern**: The new patterns use the Result pattern for error handling
4. **Event Bus**: Ensure the event bus is properly initialized before use

For more help, refer to the detailed documentation in the `docs/domain` directory or file an issue in the project issue tracker.

## Best Practices for New Code

For new code, we recommend:

1. **Always use the canonical implementations**:
   - `uno.core.unified_events` for domain events
   - `uno.domain.unified_services` for domain services
   - `uno.domain.repository` for repositories
   - `uno.api.service_endpoint_factory` for API endpoints

2. **Follow the Domain-Driven Design principles**:
   - Clearly separate entities, value objects, and aggregates
   - Use repositories for data access
   - Use domain services for complex operations
   - Use domain events for communication between bounded contexts

3. **Use the Result pattern for error handling**:
   - Return `Success` or `Failure` instead of throwing exceptions
   - Include meaningful error messages and codes

4. **Use proper dependency injection**:
   - Register your repositories and services in the DI container
   - Use constructor injection for dependencies

By following these practices, you'll create maintainable, testable code that aligns with the unified domain-driven design approach in the Uno framework.