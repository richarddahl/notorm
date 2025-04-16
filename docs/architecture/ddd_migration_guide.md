# Migration Guide: Legacy to Domain-Driven Design

This guide provides a comprehensive roadmap for migrating existing code from legacy patterns to domain-driven design in the Uno framework.

## Overview

The Uno framework has fully adopted domain-driven design (DDD) for all modules. This architectural approach provides several benefits:

- **Clear Separation of Concerns**: Distinct boundaries between entities, repositories, services, and APIs
- **Improved Testability**: Each component can be tested in isolation
- **Enhanced Maintainability**: Consistent patterns make the code easier to understand
- **Better Reusability**: Well-defined interfaces and components
- **Stronger Type Safety**: Explicit typing throughout the system

This guide will help you migrate your code to follow the DDD approach, whether you're working on an existing Uno module or creating a new one.

## Core Concepts

Before migrating, it's important to understand the key components of the DDD architecture:

### Domain Entities

Domain entities represent the core business objects in your domain model. They are defined in `entities.py` files:

```python
from dataclasses import dataclass, field
from typing import List, Optional
from uno.domain.core import AggregateRoot

@dataclass
class Order(AggregateRoot[str]):
    """Domain entity for orders."""
    
    id: str
    customer_id: str
    status: str = "pending"
    items: List["OrderItem"] = field(default_factory=list)
    shipping_address: Optional[str] = None
    
    def add_item(self, item: "OrderItem") -> None:
        """Add an item to the order."""
        self.items.append(item)
        
    def calculate_total(self) -> float:
        """Calculate the total amount for the order."""
        return sum(item.quantity * item.price for item in self.items)
```

### Domain Repositories

Repositories handle data access and persistence for domain entities. They are defined in `domain_repositories.py` files:

```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uno.domain.repository import Repository
from .entities import Order

class OrderRepository(Repository[Order, str]):
    """Repository for managing Order entities."""
    
    entity_class = Order
    
    async def find_by_customer(self, customer_id: str, session: Optional[AsyncSession] = None) -> List[Order]:
        """Find orders for a specific customer."""
        query = {"customer_id": customer_id}
        return await self.filter(query, session=session)
```

### Domain Services

Services encapsulate business logic for working with domain entities. They are defined in `domain_services.py` files:

```python
from typing import List
from uno.domain.service import DomainService
from uno.core.result import Result, Success, Failure
from .entities import Order
from .domain_repositories import OrderRepository

class OrderService(DomainService[Order, str]):
    """Service for managing Order entities."""
    
    def __init__(self, repository: OrderRepository):
        super().__init__(repository)
    
    async def place_order(self, order: Order) -> Result[Order]:
        """Place a new order and save it."""
        try:
            # Business validation
            if not order.items:
                return Failure("Order must have at least one item")
                
            # Save the order
            saved_order = await self.repository.save(order)
            return Success(saved_order)
        except Exception as e:
            return Failure(f"Failed to place order: {str(e)}")
```

### Domain Providers

Providers configure dependency injection for domain components. They are defined in `domain_provider.py` files:

```python
from uno.dependencies.service import register_service
from .domain_repositories import OrderRepository
from .domain_services import OrderService

def register_order_services():
    """Register order services in the dependency container."""
    register_service(OrderRepository)
    register_service(OrderService, depends=[OrderRepository])
```

### Domain Endpoints

Endpoints expose domain functionality through APIs. They are defined in `domain_endpoints.py` files:

```python
from fastapi import APIRouter, Depends, HTTPException
from uno.domain.api_integration import create_domain_router, domain_endpoint
from uno.dependencies.scoped_container import get_service
from .entities import Order
from .domain_services import OrderService

def create_orders_router() -> APIRouter:
    """Create router for Order endpoints."""
    router = create_domain_router(
        entity_type=Order,
        service_type=OrderService,
        prefix="/orders",
        tags=["Orders"]
    )
    
    # Add custom endpoints
    @router.post("/place")
    @domain_endpoint(entity_type=Order, service_type=OrderService)
    async def place_order(order_data: dict, service: OrderService = Depends(lambda: get_service(OrderService))):
        """Place a new order."""
        order = Order(**order_data)
        result = await service.place_order(order)
        
        if result.is_failure:
            raise HTTPException(status_code=400, detail=str(result.error))
            
        return result.value
    
    return router
```

## Step-by-Step Migration Process

### Step 1: Identify Your Domain Objects

1. Analyze your current code to identify core business entities
2. Determine entity relationships and boundaries
3. Identify value objects that don't have identity
4. Map out entity hierarchies and aggregates

### Step 2: Create Domain Entities

1. Create `entities.py` file or update existing one
2. Define your entities using `@dataclass` and inheritance from `AggregateRoot` or `Entity`
3. Move domain logic methods from existing classes to entity methods
4. Use proper typing for all fields and methods

Example of a migrated entity:

```python
# Before: Legacy UnoObj approach
class Product(UnoObj):
    id: str
    name: str
    price: float
    
    @classmethod
    async def find_by_name(cls, name: str):
        return await cls.filter(cls.name == name)
    
    def apply_discount(self, percentage: float):
        self.price = self.price * (1 - percentage/100)
        self.save()

# After: Domain-driven approach
@dataclass
class Product(AggregateRoot[str]):
    id: str
    name: str
    price: float
    
    def apply_discount(self, percentage: float) -> None:
        self.price = self.price * (1 - percentage/100)
```

### Step 3: Implement Domain Repositories

1. Create `domain_repositories.py` file 
2. Define repository classes for each entity
3. Move data access methods from legacy classes to repository methods
4. Implement the generic Repository interface

Example of a migrated repository:

```python
# Before: Data access mixed with entity definition
class Product(UnoObj):
    @classmethod
    async def find_by_name(cls, name: str):
        return await cls.filter(cls.name == name)

# After: Separated repository
class ProductRepository(Repository[Product, str]):
    entity_class = Product
    
    async def find_by_name(self, name: str, session: Optional[AsyncSession] = None) -> List[Product]:
        query = {"name": name}
        return await self.filter(query, session=session)
```

### Step 4: Create Domain Services

1. Create `domain_services.py` file
2. Define service classes for business operations
3. Move business logic from legacy classes to service methods
4. Use Result type for consistent error handling

Example of a migrated service:

```python
# Before: Business logic mixed with entity
class Product(UnoObj):
    def process_sale(self, quantity: int):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        # Business logic...

# After: Service-based approach
class ProductService(DomainService[Product, str]):
    async def process_sale(self, product_id: str, quantity: int) -> Result[Product]:
        if quantity <= 0:
            return Failure("Quantity must be positive")
            
        product = await self.get_by_id(product_id)
        if product.is_failure:
            return product
            
        # Business logic...
        return Success(product.value)
```

### Step 5: Configure Domain Providers

1. Create `domain_provider.py` file
2. Register repositories and services with dependency injection container
3. Set up service dependencies

Example of a provider configuration:

```python
def register_product_services():
    register_service(ProductRepository)
    register_service(ProductService, depends=[ProductRepository])
```

### Step 6: Implement Domain Endpoints

1. Create `domain_endpoints.py` file
2. Use `create_domain_router` to generate standard CRUD endpoints
3. Add custom endpoints with `domain_endpoint` decorator
4. Update imports and references

Example of migrated endpoints:

```python
# Before: Legacy direct API implementation
@app.post("/products")
async def create_product(data: dict):
    product = await Product.create(**data)
    return product.to_dict()

# After: Domain-driven approach
def create_products_router() -> APIRouter:
    router = create_domain_router(
        entity_type=Product,
        service_type=ProductService,
        prefix="/products",
        tags=["Products"]
    )
    return router
```

### Step 7: Update Module Imports

1. Update `__init__.py` to expose domain entities and services
2. Import from domain-specific files instead of legacy files
3. Remove legacy imports

Example of updated imports:

```python
# Before: Legacy imports
from .entities import Product
from .services import product_service

# After: Domain-driven imports
from .entities import Product
from .domain_services import ProductService
from .domain_repositories import ProductRepository
from .domain_endpoints import create_products_router
```

## Using the DDD Generator Tool

To make the migration process easier, you can use the DDD generator tool included with Uno:

```bash
# Generate a complete module with all components
python src/scripts/ddd_generator.py module src/uno/products products "Product:name:str,price:float,description:Optional[str]"

# Generate just an entity
python src/scripts/ddd_generator.py entity src/uno/products products Product --fields "name:str,price:float,description:Optional[str]"

# Generate just a repository
python src/scripts/ddd_generator.py repository src/uno/products products Product

# Generate just a service
python src/scripts/ddd_generator.py service src/uno/products products Product

# Generate endpoints for multiple entities
python src/scripts/ddd_generator.py endpoints src/uno/products products Product Category
```

## Troubleshooting Common Migration Issues

### Entity Field Type Issues

If you encounter issues with entity field types:

```python
# Problem: Missing type annotations
class Product(Entity):
    name = ""  # Missing type annotation
    
# Solution: Add proper type annotations
@dataclass
class Product(Entity):
    name: str = ""
```

### Circular Import Issues

If you encounter circular imports:

```python
# Problem: Circular imports between entities
# In order.py
from .product import Product

# In product.py
from .order import Order

# Solution: Use string references for forward declarations
@dataclass
class Order(AggregateRoot[str]):
    items: List["OrderItem"] = field(default_factory=list)
```

### Repository Query Issues

If you encounter issues with repository queries:

```python
# Problem: Legacy filter syntax
products = await repository.filter(Product.price > 100)

# Solution: Use dictionary-based filters
products = await repository.filter({"price__gt": 100})
```

## Best Practices

### Entity Design

1. Use `AggregateRoot` for root entities with identity
2. Use `Entity` for entities that belong within an aggregate
3. Use `ValueObject` for immutable value types
4. Keep entities focused on domain behavior, not data access
5. Implement validation in entity constructors or dedicated methods

### Repository Design

1. Keep repositories focused on data access only
2. Use generic `filter`, `get_by_id`, and `save` methods when possible
3. Add custom query methods only when needed
4. Return `Result` types for operations that can fail
5. Handle transactions at the service level, not in repositories

### Service Design

1. Use constructor injection for dependencies
2. Return `Result` types for all operations that can fail
3. Keep services focused on orchestrating domain logic
4. Don't expose database details in service interfaces
5. Validate inputs before performing operations

### Endpoint Design

1. Use `create_domain_router` for standard CRUD endpoints
2. Use `domain_endpoint` decorator for custom endpoints
3. Handle errors consistently with HTTPException
4. Use Pydantic models for request and response schemas
5. Keep endpoint handlers thin, delegate logic to services

## Conclusion

Migrating to domain-driven design may seem like a significant effort, but the benefits in terms of code quality, maintainability, and testability are substantial. By following this guide and using the provided tools, you can modernize your codebase and align with Uno's architecture.

Remember that DDD is not just about file structure but about modeling your domain accurately. Take time to identify the right entities, aggregates, and boundaries to create a clean and cohesive domain model.