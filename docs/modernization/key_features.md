# Uno Framework Modernization: Key Features

This document outlines the key features and improvements made to the Uno framework to make it more modular, loosely coupled, and aligned with modern Python best practices.

## Core Architectural Improvements

### 1. Protocol-Based Design

The framework now uses Python's Protocol class extensively to define interfaces, enabling better dependency injection and loose coupling.

```python
from typing import Protocol, TypeVar, Generic

T = TypeVar('T')
KeyT = TypeVar('KeyT')

class Repository(Protocol, Generic[T, KeyT]):```

"""Protocol for repositories."""
``````

```
```

async def get(self, id: KeyT) -> Optional[T]:```

"""Get an entity by its ID."""
...
```
``````

```
```

async def save(self, entity: T) -> None:```

"""Save an entity."""
...
```
``````

```
```

async def delete(self, id: KeyT) -> bool:```

"""Delete an entity by its ID."""
...
```
```
```

### 2. Domain-Driven Design Architecture

The framework now provides building blocks for implementing Domain-Driven Design (DDD) principles.

```python
from uno.core import AggregateEntity, BaseDomainEvent

# Define a domain event
class OrderPlacedEvent(BaseDomainEvent):```

order_id: str
customer_id: str
total_amount: float
``````

```
```

@property
def aggregate_id(self) -> str:```

return self.order_id
```
```

# Define an aggregate root
class Order(AggregateEntity[str]):```

def __init__(self, id: str, customer_id: str):```

super().__init__(id=id)
self.customer_id = customer_id
self.items = []
self.total_amount = 0.0
self.status = "pending"
```
``````

```
```

def add_item(self, product_id: str, quantity: int, price: float):```

item = {"product_id": product_id, "quantity": quantity, "price": price}
self.items.append(item)
self.total_amount += quantity * price
```
``````

```
```

def place(self):```

if not self.items:
    raise ValueError("Cannot place an empty order")
``````

```
```

self.status = "placed"
``````

```
```

# Register a domain event
self.register_event(OrderPlacedEvent(
    order_id=self.id,
    customer_id=self.customer_id,
    total_amount=self.total_amount
))
```
```
```

### 3. Event-Driven Architecture

The framework now supports event-driven architecture with both synchronous and asynchronous event handling.

```python
from uno.core import event_handler, DomainEventProcessor, EventBus

# Event handler using decorator pattern
class OrderEventProcessor(DomainEventProcessor):```

def __init__(self, event_bus: EventBus, email_service):```

super().__init__(event_bus)
self.email_service = email_service
```
``````

```
```

@event_handler(OrderPlacedEvent)
async def handle_order_placed(self, event: OrderPlacedEvent):```

# Send confirmation email
await self.email_service.send_confirmation(
    event.customer_id,
    f"Order {event.order_id} placed successfully",
    f"Your order for ${event.total_amount} has been placed."
)
``````

```
```

# Update inventory (in a real app, this might be a separate handler)
# ...
```
```
```

### 4. CQRS Pattern Implementation

The framework now separates command (write) operations from query (read) operations for better performance and scalability.

```python
from uno.core import (```

BaseCommand, BaseQuery, BaseCommandHandler, BaseQueryHandler,
command_handler, query_handler, Success, Failure
```
)

# Command for creating an order
class CreateOrderCommand(BaseCommand):```

customer_id: str
items: List[Dict[str, Any]]
```

# Command handler
@singleton
@command_handler(CreateOrderCommand)
class CreateOrderCommandHandler(BaseCommandHandler[CreateOrderCommand, Order]):```

def __init__(self, unit_of_work: AbstractUnitOfWork):```

self.unit_of_work = unit_of_work
```
``````

```
```

async def handle(self, command: CreateOrderCommand):```

try:
    # Create order entity
    order_id = generate_id()
    order = Order(id=order_id, customer_id=command.customer_id)
    
    # Add items
    for item in command.items:
        order.add_item(
            product_id=item["product_id"],
            quantity=item["quantity"],
            price=item["price"]
        )
    
    order.place()
    
    # Use unit of work to manage transaction
    async with self.unit_of_work:
        order_repo = self.unit_of_work.get_repository(OrderRepository)
        await order_repo.save(order)
    
    return Success(order)
except Exception as e:
    return Failure(e)
```
```

# Query for getting an order
class GetOrderQuery(BaseQuery):```

order_id: str
```

# Query handler
@singleton
@query_handler(GetOrderQuery)
class GetOrderQueryHandler(BaseQueryHandler[GetOrderQuery, Order]):```

def __init__(self, order_repository: OrderRepository):```

self.order_repository = order_repository
```
``````

```
```

async def handle(self, query: GetOrderQuery):```

try:
    order = await self.order_repository.get(query.order_id)
    if not order:
        return Failure(ValueError(f"Order not found: {query.order_id}"))
    return Success(order)
except Exception as e:
    return Failure(e)
```
```
```

### 5. Enhanced Dependency Injection

The framework now provides a modern dependency injection system with proper scoping and lifecycle management.

```python
from uno.dependencies import singleton, scoped, transient, inject_params

# Define a service with singleton scope
@singleton
class OrderService:```

def __init__(self, command_bus, query_bus):```

self.command_bus = command_bus
self.query_bus = query_bus
```
``````

```
```

async def create_order(self, customer_id: str, items: List[Dict[str, Any]]):```

command = CreateOrderCommand(customer_id=customer_id, items=items)
return await self.command_bus.dispatch(command)
```
``````

```
```

async def get_order(self, order_id: str):```

query = GetOrderQuery(order_id=order_id)
return await self.query_bus.dispatch(query)
```
```

# Use in a FastAPI endpoint with auto-injection
@app.post("/orders")
@inject_params()
async def create_order(```

data: Dict[str, Any],
order_service: OrderService  # Injected automatically
```
):```

result = await order_service.create_order(```

customer_id=data["customer_id"],
items=data["items"]
```
)
``````

```
```

if result.is_success:```

return {"id": result.value.id, "status": "success"}
```
else:```

return {"error": str(result.error)}, 400
```
```
```

### 6. Functional Error Handling

The framework now uses the Result pattern (also known as Either pattern) for handling errors without exceptions.

```python
from uno.core import Success, Failure, Result

def divide(a: float, b: float) -> Result[float]:```

if b == 0:```

return Failure(ValueError("Division by zero"))
```
return Success(a / b)
```

# Usage
result = divide(10, 2)
if result.is_success:```

print(f"Result: {result.value}")
```
else:```

print(f"Error: {result.error}")
```

# Chaining results using monadic operations
def calculate(a: float, b: float) -> Result[float]:```

return divide(a, b).map(lambda x: x * 2)
```

# Using with pattern matching (Python 3.10+)
match calculate(10, 2):```

case Success(value):```

print(f"Result: {value}")
```
case Failure(error):```

print(f"Error: {error}")
```
```
```

### 7. Unit of Work Pattern

The framework now provides a Unit of Work pattern for managing transaction boundaries.

```python
from uno.core import AbstractUnitOfWork, transaction

# Using unit of work explicitly
async def create_and_place_order(customer_id: str, items: List[Dict[str, Any]], uow: AbstractUnitOfWork):```

async with uow:```

# Get repositories
order_repo = uow.get_repository(OrderRepository)
customer_repo = uow.get_repository(CustomerRepository)
``````

```
```

# Check customer exists
customer = await customer_repo.get(customer_id)
if not customer:
    return Failure(ValueError(f"Customer not found: {customer_id}"))
``````

```
```

# Create order
order = Order(id=generate_id(), customer_id=customer_id)
for item in items:
    order.add_item(
        product_id=item["product_id"],
        quantity=item["quantity"],
        price=item["price"]
    )
``````

```
```

# Place order
order.place()
``````

```
```

# Save order
await order_repo.save(order)
``````

```
```

# Transaction is committed at the end of the with block
# Events are published after successful commit
```
``````

```
```

return Success(order)
```

# Using unit of work with decorator
@transaction(lambda: get_service_provider().get_service(AbstractUnitOfWork))
async def create_and_place_order(customer_id: str, items: List[Dict[str, Any]], uow: AbstractUnitOfWork = None):```

# Implementation...
```
```

### 8. Enhanced Configuration Management

The framework now provides a flexible and extensible configuration system.

```python
from uno.core import ConfigurationService, ConfigurationOptions, FileConfigSource, EnvironmentConfigSource

# Define configuration options
class DatabaseConfig(ConfigurationOptions):```

host: str = "localhost"
port: int = 5432
database: str = "uno"
username: str = "postgres"
password: str = ""
pool_size: int = 10
timeout: int = 30
```

# Create configuration service
config_service = ConfigurationService()
config_service.add_source(EnvironmentConfigSource(prefix="UNO"), priority=10)
config_service.add_source(FileConfigSource("config.yaml", auto_reload=True), priority=5)

# Get typed configuration
db_config = DatabaseConfig.from_config(config_service, section="database")

# Use configuration
print(f"Connecting to {db_config.host}:{db_config.port}/{db_config.database}")

# Validate configuration with Pydantic
from pydantic import BaseModel, Field

class DatabaseSettings(BaseModel):```

host: str = Field(..., description="Database host")
port: int = Field(5432, description="Database port")
database: str = Field(..., description="Database name")
username: str = Field(..., description="Database username")
password: str = Field(..., description="Database password")
pool_size: int = Field(10, description="Connection pool size", ge=1, le=100)
timeout: int = Field(30, description="Connection timeout in seconds", ge=1)
```

# Validate configuration
db_settings = config_service.validate(DatabaseSettings, section="database")
```

## API Usage Examples

### REST API with FastAPI and Automatic Dependency Injection

```python
from fastapi import APIRouter, Path, Query, Body
from uno.dependencies.fastapi_integration import DIAPIRouter
from uno.core import Result, Success, Failure

# Create router with automatic dependency injection
router = DIAPIRouter(prefix="/orders", tags=["orders"])

@router.post("/")
@inject_params()
async def create_order(```

data: Dict[str, Any] = Body(...),
order_service: OrderService = None  # Injected automatically
```
):```

result = await order_service.create_order(```

customer_id=data["customer_id"],
items=data["items"]
```
)
``````

```
```

if result.is_success:```

return {"id": result.value.id, "status": "success"}
```
else:```

return {"error": str(result.error)}, 400
```
```

@router.get("/{order_id}")
@inject_params()
async def get_order(```

order_id: str
``` = Path(..., description="The order ID"),```

order_service: OrderService = None  # Injected automatically
```
):```

result = await order_service.get_order(order_id)
``````

```
```

if result.is_success:```

order = result.value
return {
    "id": order.id,
    "customer_id": order.customer_id,
    "items": order.items,
    "total_amount": order.total_amount,
    "status": order.status
}
```
else:```

return {"error": str(result.error)}, 400
```
```
```

### Combining Vector Search with Domain-Driven Design

```python
from uno.core import BaseQuery, query_handler, Success, Failure
from uno.dependencies import singleton, inject_params

# Define a query
class ProductSearchQuery(BaseQuery):```

query_text: str
limit: int = 10
threshold: float = 0.7
categories: Optional[List[str]] = None
```

# Define a query handler
@singleton
@query_handler(ProductSearchQuery)
class ProductSearchQueryHandler:```

def __init__(self, vector_search_factory, product_repository):```

self.vector_search_factory = vector_search_factory
self.product_repository = product_repository
```
``````

```
```

async def handle(self, query: ProductSearchQuery):```

try:
    # Get vector search service
    product_search = self.vector_search_factory.create_search_service(
        entity_type="product",
        table_name="products"
    )
    
    # Build search criteria
    search_query = {
        "query_text": query.query_text,
        "limit": query.limit,
        "threshold": query.threshold
    }
    
    # Add filter by categories if specified
    if query.categories:
        search_query["filters"] = [
            {"field": "category", "operator": "in", "value": query.categories}
        ]
    
    # Perform vector search
    results = await product_search.search(search_query)
    
    # Enhance results with domain information
    enhanced_results = []
    for result in results:
        product = await self.product_repository.get(result.id)
        if product:
            # Add business logic
            is_in_stock = product.stock_quantity > 0
            is_on_sale = product.discount_percentage > 0
            
            enhanced_results.append({
                "id": result.id,
                "similarity": result.similarity,
                "name": product.name,
                "price": product.price,
                "is_in_stock": is_in_stock,
                "is_on_sale": is_on_sale,
                "thumbnail_url": product.thumbnail_url
            })
    
    return Success(enhanced_results)
except Exception as e:
    return Failure(e)
```
```

# Use in an API endpoint
@router.get("/search")
@inject_params()
async def search_products(```

query_text: str,
limit: int = Query(10, ge=1, le=100),
threshold: float = Query(0.7, ge=0, le=1),
categories: Optional[List[str]] = Query(None),
query_bus = None  # Injected automatically
```
):```

query = ProductSearchQuery(```

query_text=query_text,
limit=limit,
threshold=threshold,
categories=categories
```
)
``````

```
```

result = await query_bus.dispatch(query)
``````

```
```

if result.is_success:```

return result.value
```
else:```

return {"error": str(result.error)}, 400
```
```
```

## Integration Examples

### Integrating with External Services

```python
from uno.core import ServiceLifecycle, Result, Success, Failure
from uno.dependencies import singleton

@singleton
class EmailService(ServiceLifecycle):```

"""Email service with lifecycle management."""
``````

```
```

def __init__(self, config, logger):```

self.config = config
self.logger = logger
self.client = None
```
``````

```
```

async def initialize(self):```

"""Initialize the email service client."""
self.logger.info("Initializing email service")
self.client = EmailClient(
    host=self.config.get("email.host"),
    port=self.config.get("email.port"),
    username=self.config.get("email.username"),
    password=self.config.get("email.password")
)
await self.client.connect()
self.logger.info("Email service initialized")
```
``````

```
```

async def dispose(self):```

"""Clean up resources."""
self.logger.info("Disposing email service")
if self.client:
    await self.client.disconnect()
self.logger.info("Email service disposed")
```
``````

```
```

async def send_email(self, to: str, subject: str, body: str) -> Result[bool]:```

"""Send an email."""
try:
    if not self.client:
        return Failure(ValueError("Email service not initialized"))
    
    await self.client.send_email(to, subject, body)
    self.logger.info(f"Email sent to {to}: {subject}")
    return Success(True)
except Exception as e:
    self.logger.error(f"Error sending email: {e}")
    return Failure(e)
```
```
```

### Implementing a Repository with Unit of Work

```python
from uno.core import Repository
from uno.dependencies import scoped

@scoped
class PostgresOrderRepository(Repository[Order, str]):```

"""Order repository implementation using PostgreSQL."""
``````

```
```

def __init__(self, db_session):```

self.db_session = db_session
self._events = []
```
``````

```
```

async def get(self, id: str) -> Optional[Order]:```

"""Get an order by ID."""
query = """
SELECT id, customer_id, status, total_amount, items
FROM orders
WHERE id = $1
"""
row = await self.db_session.fetchrow(query, id)
if not row:
    return None
``````

```
```

# Map database row to domain entity
order = Order(
    id=row["id"],
    customer_id=row["customer_id"]
)
order.status = row["status"]
order.total_amount = row["total_amount"]
order.items = row["items"]
``````

```
```

return order
```
``````

```
```

async def save(self, order: Order) -> None:```

"""Save an order."""
# Collect events from the aggregate
self._events.extend(order.clear_events())
``````

```
```

# Check if order exists
exists = await self.exists(order.id)
``````

```
```

if exists:
    # Update existing order
    query = """
    UPDATE orders
    SET customer_id = $1, status = $2, total_amount = $3, items = $4
    WHERE id = $5
    """
    await self.db_session.execute(
        query,
        order.customer_id,
        order.status,
        order.total_amount,
        order.items,
        order.id
    )
else:
    # Insert new order
    query = """
    INSERT INTO orders (id, customer_id, status, total_amount, items)
    VALUES ($1, $2, $3, $4, $5)
    """
    await self.db_session.execute(
        query,
        order.id,
        order.customer_id,
        order.status,
        order.total_amount,
        order.items
    )
```
``````

```
```

async def delete(self, id: str) -> bool:```

"""Delete an order by ID."""
query = "DELETE FROM orders WHERE id = $1"
result = await self.db_session.execute(query, id)
return result == "DELETE 1"
```
``````

```
```

async def exists(self, id: str) -> bool:```

"""Check if an order exists."""
query = "SELECT EXISTS(SELECT 1 FROM orders WHERE id = $1)"
return await self.db_session.fetchval(query, id)
```
``````

```
```

def collect_events(self) -> List[DomainEvent]:```

"""Collect events from saved aggregates."""
events = self._events.copy()
self._events.clear()
return events
```
```
```

## Key Takeaways

1. **Protocol-Based Design**: Use Protocols for interfaces to achieve loose coupling and better testability.

2. **Domain-Driven Design**: Focus on modeling the domain accurately with entities, value objects, and aggregates.

3. **Event-Driven Architecture**: Use events to decouple components and enable extensibility.

4. **CQRS Pattern**: Separate read and write operations for better performance and scalability.

5. **Result Pattern**: Use Result objects instead of exceptions for more predictable error handling.

6. **Unit of Work**: Manage transaction boundaries consistently and ensure all-or-nothing operations.

7. **Dependency Injection**: Use the DI system with appropriate scopes to manage component lifecycle.

8. **Async-First**: Embrace asynchronous programming for better resource utilization.

These architectural improvements make the Uno framework more modular, loosely coupled, and aligned with modern Python best practices.