# Uno Framework Service Pattern

The service pattern in the Uno framework provides a unified approach to implementing business logic and domain operations. It integrates with the repository pattern, dependency injection system, and event system to provide a cohesive architecture.

## Overview

Services in the Uno framework encapsulate business logic and domain operations, providing a layer between controllers/endpoints and repositories. This pattern helps maintain clean separation of concerns and supports domain-driven design principles.

## Service Types

The Uno framework provides several types of services for different use cases:

### Basic Service

The base `Service` class provides common functionality for all services, including error handling, logging, and result pattern integration.

```python
from uno.infrastructure.services import Service
from uno.core.errors.result import Result

class HealthCheckService(Service):
    async def check_health(self) -> Result[dict]:
        # Perform health check
        return Result.success({"status": "healthy"})
```

### CRUD Service

The `CrudService` class provides Create, Read, Update, Delete operations for entities.

```python
from uno.infrastructure.services import CrudService
from uno.domain.models import Product
from uno.core.errors.result import Result

class ProductService(CrudService[Product]):
    async def get_by_name(self, name: str) -> Result[Product]:
        products = await self.get_all()
        if products.is_failure:
            return products
        
        for product in products.value:
            if product.name == name:
                return Result.success(product)
        
        return Result.failure(
            error="Product not found", 
            code="PRODUCT_NOT_FOUND"
        )
```

### Aggregate Root Service

The `AggregateCrudService` class provides operations for domain aggregate roots with proper version handling.

```python
from uno.infrastructure.services import AggregateCrudService
from uno.domain.models import Order
from uno.core.errors.result import Result

class OrderService(AggregateCrudService[Order]):
    async def finalize_order(self, order_id: str) -> Result[Order]:
        # Get the order
        order_result = await self.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Update the order status
        order.status = "finalized"
        
        # Update the order (with version checking)
        return await self.update(order)
```

### Query Service

The `QueryService` class provides read-only operations optimized for querying.

```python
from uno.infrastructure.services import QueryService
from uno.domain.models import Product
from uno.core.errors.result import Result

class ProductQueryService(QueryService[Product]):
    async def get_by_price_range(
        self, 
        min_price: float, 
        max_price: float
    ) -> Result[list[Product]]:
        products = await self.get_all()
        if products.is_failure:
            return products
        
        filtered_products = [
            p for p in products.value 
            if min_price <= p.price <= max_price
        ]
        
        return Result.success(filtered_products)
```

### Application Service

The `ApplicationService` class provides coordination of multiple services for complex operations.

```python
from uno.infrastructure.services import ApplicationService
from uno.core.di import inject
from uno.core.errors.result import Result

class OrderProcessingService(ApplicationService):
    @inject
    def __init__(
        self, 
        order_service, 
        product_service, 
        payment_service,
        logger=None
    ):
        super().__init__(logger=logger)
        self.order_service = order_service
        self.product_service = product_service
        self.payment_service = payment_service
    
    async def process_order(self, order_id: str) -> Result:
        # Get the order
        order_result = await self.order_service.get_by_id(order_id)
        if order_result.is_failure:
            return order_result
        
        order = order_result.value
        
        # Check inventory
        for item in order.items:
            product_result = await self.product_service.get_by_id(item.product_id)
            if product_result.is_failure:
                return product_result
            
            product = product_result.value
            if product.stock < item.quantity:
                return Result.failure(
                    error=f"Insufficient stock for product {product.name}",
                    code="INSUFFICIENT_STOCK"
                )
        
        # Process payment
        payment_result = await self.payment_service.process_payment(
            order_id, 
            order.total
        )
        if payment_result.is_failure:
            return payment_result
        
        # Update inventory
        for item in order.items:
            await self.product_service.reduce_stock(
                item.product_id, 
                item.quantity
            )
        
        # Complete the order
        return await self.order_service.complete_order(order_id)
```

## Factory Functions

The Uno framework provides factory functions for creating services:

```python
from uno.infrastructure.services import (
    create_service,
    create_crud_service,
    create_aggregate_service,
    create_query_service
)
from uno.domain.models import Product, Order

# Create a basic service
health_check = create_service(HealthCheckService)

# Create a CRUD service
product_service = create_crud_service(Product)

# Create an aggregate root service
order_service = create_aggregate_service(Order)

# Create a query service
product_query = create_query_service(Product)
```

## Dependency Injection

The Uno framework integrates services with the dependency injection system:

```python
from uno.infrastructure.services import (
    register_service,
    register_crud_service,
    get_service_by_type,
    get_crud_service
)

# Register services
register_service(HealthCheckService, HealthCheckServiceImpl)
register_crud_service(Product, ProductService)

# Get services
health_check = get_service_by_type(HealthCheckService)
product_service = get_crud_service(Product)
```

## Event Integration

Services in the Uno framework integrate with the domain event system:

```python
from uno.infrastructure.services import CrudService
from uno.domain.models import Product
from uno.core.errors.result import Result

class ProductService(CrudService[Product]):
    async def create_product(self, data: dict) -> Result[Product]:
        # Create the product
        product = Product(**data)
        
        # Add an event (will be published after successful creation)
        product.add_event(ProductCreatedEvent(
            product_id=str(product.id),
            name=product.name,
            price=product.price
        ))
        
        # Create the product (events are automatically collected and published)
        return await self.create(product)
```

## Result Pattern

Services in the Uno framework use the Result pattern for error handling:

```python
from uno.infrastructure.services import Service
from uno.core.errors.result import Result, Success, Failure

class ValidationService(Service):
    async def validate_email(self, email: str) -> Result[str]:
        if not '@' in email:
            return Failure(
                error="Invalid email format",
                code="INVALID_EMAIL"
            )
        
        return Success(email)
```

## Initialization

Initialize the service system for your application:

```python
from uno.infrastructure.services import initialize_unified_services

async def startup():
    # Initialize the unified service pattern
    await initialize_unified_services()
```

## Service System Architecture

The service system architecture consists of the following components:

1. **Protocols**: Interface definitions for services
2. **Base Implementations**: Base service classes
3. **Factory**: Service creation utilities
4. **DI Integration**: Dependency injection setup
5. **Initialization**: System setup utilities

## Integration with Repository Pattern

Services in the Uno framework integrate with the repository pattern:

```python
from uno.infrastructure.services import CrudService
from uno.infrastructure.repositories import RepositoryProtocol
from uno.domain.models import Product
from uno.core.di import inject

class ProductService(CrudService[Product]):
    @inject
    def __init__(
        self, 
        repository: RepositoryProtocol[Product],
        logger=None
    ):
        super().__init__(
            entity_type=Product,
            repository=repository,
            logger=logger
        )
```

## Examples

For more examples of using the service pattern in the Uno framework, refer to the provided examples in the `examples.py` file.