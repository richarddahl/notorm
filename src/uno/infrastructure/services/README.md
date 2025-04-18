# Uno Framework Service Pattern

This package provides a comprehensive implementation of the service pattern for the Uno framework, designed to work seamlessly with the repository pattern, dependency injection system, and event system.

## Overview

The service pattern is a layer in the application that encapsulates business logic and domain operations, mediating between controllers/endpoints and repositories. It provides a clean separation of concerns and helps maintain a well-structured codebase.

## Features

- **Basic Service Functionality**: Common operations with error handling
- **CRUD Services**: Create, Read, Update, Delete operations for entities
- **Aggregate Services**: Operations for domain aggregate roots with proper version handling
- **Query Services**: Read-only operations optimized for querying
- **Application Services**: Complex operations that coordinate multiple services
- **Transactional Services**: Operations that require transaction management
- **Event Collection**: Integration with domain events system

## Architecture

The service pattern implementation consists of the following components:

- **Protocols**: Interface definitions in `protocols.py`
- **Base Implementations**: Base service classes in `base.py`
- **Factory**: Service creation utilities in `factory.py`
- **DI Integration**: Dependency injection setup in `di.py`
- **Initialization**: System setup utilities in `initialization.py`
- **Examples**: Example implementations in `examples.py`

## Usage

### Basic Service

```python
from uno.infrastructure.services import Service
from uno.core.errors.result import Result

class HealthCheckService(Service):
    async def check_health(self) -> Result[dict]:
        # Perform health check
        return Result.success({"status": "healthy"})
```

### CRUD Service

```python
from uno.infrastructure.services import CrudService
from uno.domain.models import Entity
from uno.core.errors.result import Result

class Product(Entity):
    name: str
    price: float

class ProductService(CrudService[Product]):
    async def get_products_by_price_range(self, min_price: float, max_price: float) -> Result[list[Product]]:
        all_products = await self.get_all()
        if all_products.is_failure:
            return all_products
        
        filtered_products = [p for p in all_products.value if min_price <= p.price <= max_price]
        return Result.success(filtered_products)
```

### Application Service

```python
from uno.infrastructure.services import ApplicationService
from uno.core.di import inject
from uno.core.errors.result import Result

class OrderProcessingService(ApplicationService):
    @inject
    def __init__(self, order_service, product_service, payment_service):
        super().__init__()
        self.order_service = order_service
        self.product_service = product_service
        self.payment_service = payment_service
    
    async def process_order(self, order_id: str) -> Result:
        # Get the order
        order = await self.order_service.get_by_id(order_id)
        if order.is_failure:
            return order
        
        # Process payment
        payment_result = await self.payment_service.process_payment(order.value)
        if payment_result.is_failure:
            return payment_result
        
        # Update inventory
        for item in order.value.items:
            await self.product_service.update_inventory(item.product_id, item.quantity)
        
        # Complete the order
        return await self.order_service.complete_order(order_id)
```

### Using Factory Functions

```python
from uno.infrastructure.services import create_crud_service, create_application_service
from uno.domain.models import Product, Order

# Create a product service
product_service = create_crud_service(Product)

# Create an order service
order_service = create_crud_service(Order)

# Create an application service
order_processor = create_application_service(OrderProcessingService)
```

### Dependency Injection

```python
from uno.infrastructure.services import (
    register_crud_service,
    register_application_service,
    get_crud_service,
    get_application_service
)

# Register services
register_crud_service(Product, ProductService)
register_application_service(OrderProcessingService, OrderProcessingServiceImpl)

# Get services
product_service = get_crud_service(Product)
order_processor = get_application_service(OrderProcessingService)
```

## Initialization

To initialize the service system for your application:

```python
from uno.infrastructure.services import initialize_unified_services

async def startup():
    # Initialize the unified service pattern
    await initialize_unified_services()
```

## Architecture Diagram

```
Unified Service Pattern Architecture
===================================

┌──────────────────────────────────────────────────────────────────┐
│                         Service Protocols                         │
│                                                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│  │ServiceProtocol│  │CrudService    │  │ApplicationService   │   │
│  │              │  │Protocol       │  │Protocol             │   │
│  └──────────────┘  └───────────────┘  └─────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                               ▲                                    
                               │                                    
                               │                                    
┌──────────────────────────────────────────────────────────────────┐
│                       Service Implementations                     │
│                                                                  │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│  │Service       │  │CrudService    │  │ApplicationService   │   │
│  │              │  │               │  │                     │   │
│  └──────────────┘  └───────────────┘  └─────────────────────┘   │
│         ▲                  ▲                   ▲                 │
│         │                  │                   │                 │
│  ┌──────────────┐  ┌───────────────┐  ┌─────────────────────┐   │
│  │Transactional │  │AggregateRoot  │  │EventCollecting      │   │
│  │Service       │  │Service        │  │Service              │   │
│  └──────────────┘  └───────────────┘  └─────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
            ▲                    ▲                    ▲              
            │                    │                    │              
            │                    │                    │              
┌───────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│ Service Factory   │  │     DI System    │  │Repository System │
│                   │  │                  │  │                  │
│ ┌─────────────┐  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
│ │ServiceFactory│  │  │ │ServiceResolver│ │  │ │Repository    │ │
│ │             │  │  │ │              │ │  │ │Protocol      │ │
│ └─────────────┘  │  │ └──────────────┘ │  │ └──────────────┘ │
│                   │  │                  │  │                  │
│ ┌─────────────┐  │  │ ┌──────────────┐ │  │ ┌──────────────┐ │
│ │create_service│  │  │ │get_service   │ │  │ │UnitOfWork    │ │
│ │             │  │  │ │              │ │  │ │Protocol      │ │
│ └─────────────┘  │  │ └──────────────┘ │  │ └──────────────┘ │
│                   │  │                  │  │                  │
└───────────────────┘  └──────────────────┘  └──────────────────┘
```