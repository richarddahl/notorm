# Command Query Responsibility Segregation (CQRS)

This guide explains the Command Query Responsibility Segregation (CQRS) pattern in the Uno framework.

## What is CQRS?

CQRS is an architectural pattern that separates read operations (Queries) from write operations (Commands):

- **Commands**: Change the state of the system but don't return data
- **Queries**: Return data but don't change the system state

This separation enables:
- Optimization of read and write operations independently
- Scaling query and command sides separately
- Different data models for reading and writing
- Advanced security and validation for commands
- Simplified query modeling for complex reporting

## Basic CQRS Concepts

### Commands

Commands represent intent to change the system:

```python
from pydantic import BaseModel
from uuid import UUID
from typing import List

class CreateOrderCommand(BaseModel):
    """Command to create a new order."""
    
    customer_id: UUID
    items: List[dict]  # Each item has product_id, quantity, and price
    shipping_address: dict

class UpdateOrderStatusCommand(BaseModel):
    """Command to update an order's status."""
    
    order_id: UUID
    new_status: str
    reason: str = None
```

Commands:
- Are imperative (CreateOrder, UpdateStatus)
- Contain all data needed for the operation
- Are validated before processing
- May be rejected if business rules are violated
- Can be audited and logged
- May raise domain events when processed

### Queries

Queries represent requests for information:

```python
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class GetOrderByIdQuery(BaseModel):
    """Query to get an order by ID."""
    
    order_id: UUID

class FindOrdersQuery(BaseModel):
    """Query to find orders matching criteria."""
    
    customer_id: Optional[UUID] = None
    status: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
```

Queries:
- Are interrogative (GetOrder, FindOrders)
- Specify filtering, sorting, and pagination parameters
- Return data transfer objects (DTOs) for display
- Can be optimized for read performance
- May use denormalized data structures

### Command Handlers

Command handlers process commands and update the system:

```python
from uno.core.errors.result import Result, Success, Failure
from uno.core.di import inject

class OrderCommandHandler:
    """Handler for order-related commands."""
    
    @inject
    def __init__(self, order_repository, event_publisher, unit_of_work):
        self.order_repository = order_repository
        self.event_publisher = event_publisher
        self.unit_of_work = unit_of_work
    
    async def handle_create_order(self, command: CreateOrderCommand) -> Result[UUID, str]:
        """Handle the CreateOrderCommand."""
        async with self.unit_of_work:
            # Create the order
            order = Order.create(command.customer_id)
            
            # Add items
            for item in command.items:
                order.add_item(
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
            
            # Set shipping address
            order.set_shipping_address(command.shipping_address)
            
            # Save the order
            await self.order_repository.add(order)
            
            # Return the order ID
            return Success(order.id)
    
    async def handle_update_order_status(self, command: UpdateOrderStatusCommand) -> Result[None, str]:
        """Handle the UpdateOrderStatusCommand."""
        async with self.unit_of_work:
            # Get the order
            order = await self.order_repository.get_by_id(command.order_id)
            if not order:
                return Failure(f"Order with ID {command.order_id} not found")
            
            # Update status
            try:
                order.update_status(command.new_status, command.reason)
            except ValueError as e:
                return Failure(str(e))
            
            # Save the order
            await self.order_repository.update(order)
            
            return Success(None)
```

Command handlers:
- Validate commands before processing
- Coordinate operations on domain entities
- Use the Unit of Work pattern for transactions
- Return success or failure results
- Don't return domain data

### Query Handlers

Query handlers process queries and return data:

```python
from typing import List, Optional

class OrderQueryHandler:
    """Handler for order-related queries."""
    
    @inject
    def __init__(self, order_read_repository):
        self.order_read_repository = order_read_repository
    
    async def handle_get_order_by_id(self, query: GetOrderByIdQuery) -> Optional[OrderDTO]:
        """Handle the GetOrderByIdQuery."""
        # Get the order from the read model
        order = await self.order_read_repository.get_by_id(query.order_id)
        
        # Return null if not found
        if not order:
            return None
        
        # Map to DTO and return
        return OrderDTO.from_read_model(order)
    
    async def handle_find_orders(self, query: FindOrdersQuery) -> PaginatedResult[OrderDTO]:
        """Handle the FindOrdersQuery."""
        # Build filter criteria
        criteria = {}
        if query.customer_id:
            criteria["customer_id"] = query.customer_id
        if query.status:
            criteria["status"] = query.status
        if query.min_amount:
            criteria.setdefault("total_amount", {})["$gte"] = query.min_amount
        if query.max_amount:
            criteria.setdefault("total_amount", {})["$lte"] = query.max_amount
        if query.from_date:
            criteria.setdefault("created_at", {})["$gte"] = query.from_date
        if query.to_date:
            criteria.setdefault("created_at", {})["$lte"] = query.to_date
        
        # Query the read model
        orders, total = await self.order_read_repository.find_with_count(
            criteria,
            skip=(query.page - 1) * query.page_size,
            limit=query.page_size,
            sort=[("created_at", "desc")]
        )
        
        # Map to DTOs
        order_dtos = [OrderDTO.from_read_model(order) for order in orders]
        
        # Return paginated result
        return PaginatedResult(
            items=order_dtos,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
```

Query handlers:
- Translate query parameters into database queries
- Return DTOs rather than domain entities
- May use specialized read models
- Can implement caching strategies
- Don't modify system state

## Implementing CQRS with Uno

Uno provides several components to implement CQRS:

### Command and Query DTOs

```python
# application/commands/order_commands.py
from pydantic import BaseModel
from uuid import UUID
from typing import List

class CreateOrderCommand(BaseModel):
    """Command to create a new order."""
    
    customer_id: UUID
    items: List[dict]
    shipping_address: dict

# application/queries/order_queries.py
from pydantic import BaseModel
from uuid import UUID
from typing import Optional

class GetOrderQuery(BaseModel):
    """Query to get an order by ID."""
    
    order_id: UUID

# application/dtos/order_dtos.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import List

class OrderItemDTO(BaseModel):
    """DTO for an order item."""
    
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: float
    total_price: float

class OrderDTO(BaseModel):
    """DTO for an order."""
    
    id: UUID
    customer_id: UUID
    status: str
    items: List[OrderItemDTO]
    total_amount: float
    created_at: datetime
    updated_at: datetime
```

### Command Dispatcher

```python
# application/cqrs/command_dispatcher.py
from typing import Dict, Type, Callable, Any
from pydantic import BaseModel

class CommandDispatcher:
    """Dispatches commands to their handlers."""
    
    def __init__(self):
        self._handlers: Dict[Type[BaseModel], Callable] = {}
    
    def register(self, command_type: Type[BaseModel], handler: Callable) -> None:
        """Register a handler for a command type."""
        if command_type in self._handlers:
            raise ValueError(f"Handler already registered for {command_type.__name__}")
        
        self._handlers[command_type] = handler
    
    async def dispatch(self, command: BaseModel) -> Any:
        """Dispatch a command to its handler."""
        command_type = type(command)
        handler = self._handlers.get(command_type)
        
        if not handler:
            raise ValueError(f"No handler registered for {command_type.__name__}")
        
        return await handler(command)
```

### Query Dispatcher

```python
# application/cqrs/query_dispatcher.py
from typing import Dict, Type, Callable, Any
from pydantic import BaseModel

class QueryDispatcher:
    """Dispatches queries to their handlers."""
    
    def __init__(self):
        self._handlers: Dict[Type[BaseModel], Callable] = {}
    
    def register(self, query_type: Type[BaseModel], handler: Callable) -> None:
        """Register a handler for a query type."""
        if query_type in self._handlers:
            raise ValueError(f"Handler already registered for {query_type.__name__}")
        
        self._handlers[query_type] = handler
    
    async def dispatch(self, query: BaseModel) -> Any:
        """Dispatch a query to its handler."""
        query_type = type(query)
        handler = self._handlers.get(query_type)
        
        if not handler:
            raise ValueError(f"No handler registered for {query_type.__name__}")
        
        return await handler(query)
```

### Service Layer Integration

```python
# application/services/order_service.py
from uno.core.di import inject
from uno.application.cqrs import CommandDispatcher, QueryDispatcher
from typing import List, Optional

class OrderService:
    """Application service for orders using CQRS."""
    
    @inject
    def __init__(
        self,
        command_dispatcher: CommandDispatcher,
        query_dispatcher: QueryDispatcher
    ):
        self.command_dispatcher = command_dispatcher
        self.query_dispatcher = query_dispatcher
    
    async def create_order(
        self,
        customer_id: UUID,
        items: List[dict],
        shipping_address: dict
    ) -> Result[UUID, str]:
        """Create a new order."""
        command = CreateOrderCommand(
            customer_id=customer_id,
            items=items,
            shipping_address=shipping_address
        )
        
        return await self.command_dispatcher.dispatch(command)
    
    async def get_order(self, order_id: UUID) -> Optional[OrderDTO]:
        """Get an order by ID."""
        query = GetOrderQuery(order_id=order_id)
        
        return await self.query_dispatcher.dispatch(query)
```

### API Layer Integration

```python
# api/endpoints/order_endpoints.py
from fastapi import APIRouter, Depends, HTTPException
from uno.api.endpoint import BaseEndpoint
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency
from typing import List

router = APIRouter()
orders_endpoint = BaseEndpoint(router=router, tags=["Orders"])

@orders_endpoint.router.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    order_service: OrderService = Depends(get_dependency(OrderService))
) -> DataResponse[UUID]:
    """Create a new order."""
    result = await order_service.create_order(
        customer_id=request.customer_id,
        items=request.items,
        shipping_address=request.shipping_address
    )
    
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return DataResponse(data=result.value)

@orders_endpoint.router.get("/orders/{order_id}")
async def get_order(
    order_id: UUID,
    order_service: OrderService = Depends(get_dependency(OrderService))
) -> DataResponse[OrderDTO]:
    """Get an order by ID."""
    order = await order_service.get_order(order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return DataResponse(data=order)
```

## CQRS with Event Sourcing

CQRS works well with Event Sourcing for a robust architecture:

```python
# domain/entities/order.py
from uno.domain.entity import AggregateRoot
from uno.core.events import Event
from typing import List

class Order(AggregateRoot[UUID]):
    """Order aggregate root with event sourcing."""
    
    # Properties
    customer_id: UUID
    items: List[OrderItem] = []
    status: str = "created"
    
    @classmethod
    def create(cls, customer_id: UUID) -> "Order":
        """Create a new order."""
        order = cls(id=uuid4())
        
        # Apply event
        order.apply_event(OrderCreated(
            order_id=order.id,
            customer_id=customer_id,
            created_at=datetime.now(datetime.UTC)
        ))
        
        return order
    
    def add_item(self, product_id: UUID, quantity: int, price: float) -> None:
        """Add an item to the order."""
        if self.status != "created":
            raise ValueError("Cannot add items to a non-draft order")
        
        # Apply event
        self.apply_event(OrderItemAdded(
            order_id=self.id,
            product_id=product_id,
            quantity=quantity,
            price=price
        ))
    
    def apply_event(self, event: Event) -> None:
        """Apply an event to this aggregate."""
        # Update state based on event
        if isinstance(event, OrderCreated):
            self.customer_id = event.customer_id
            self.status = "created"
        elif isinstance(event, OrderItemAdded):
            item = OrderItem(
                product_id=event.product_id,
                quantity=event.quantity,
                price=event.price
            )
            self.items.append(item)
        elif isinstance(event, OrderStatusChanged):
            self.status = event.new_status
        
        # Record the event
        self.record_event(event)

# application/event_handlers/order_event_handlers.py
from uno.core.events import SubscriptionManager

# Create subscription manager
subscription_manager = SubscriptionManager(event_bus)

@subscription_manager.subscribe("order_created")
async def create_order_read_model(event: OrderCreated):
    """Create read model when an order is created."""
    # Create order summary in read DB
    await read_db.orders.insert_one({
        "_id": str(event.order_id),
        "customer_id": str(event.customer_id),
        "status": "created",
        "items": [],
        "total_amount": 0,
        "created_at": event.created_at,
        "updated_at": event.created_at
    })

@subscription_manager.subscribe("order_item_added")
async def update_order_items_read_model(event: OrderItemAdded):
    """Update read model when an item is added."""
    # Get product details
    product = await product_repository.get_by_id(event.product_id)
    
    # Update order in read DB
    await read_db.orders.update_one(
        {"_id": str(event.order_id)},
        {
            "$push": {
                "items": {
                    "product_id": str(event.product_id),
                    "product_name": product.name,
                    "quantity": event.quantity,
                    "unit_price": event.price,
                    "total_price": event.price * event.quantity
                }
            },
            "$inc": {"total_amount": event.price * event.quantity},
            "$set": {"updated_at": datetime.now(datetime.UTC)}
        }
    )
```

## Advanced CQRS Patterns

### Distributed CQRS

For larger applications, distribute CQRS components:

```python
# Command service (write side)
from fastapi import FastAPI, HTTPException
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency

app = FastAPI(title="Order Command Service")

@app.post("/orders")
async def create_order(
    request: CreateOrderRequest,
    command_handler: OrderCommandHandler = Depends(get_dependency(OrderCommandHandler))
) -> DataResponse[UUID]:
    """Create a new order."""
    result = await command_handler.handle_create_order(CreateOrderCommand(
        customer_id=request.customer_id,
        items=request.items,
        shipping_address=request.shipping_address
    ))
    
    if not result.is_success:
        raise HTTPException(status_code=400, detail=result.error)
    
    return DataResponse(data=result.value)

# Query service (read side)
from fastapi import FastAPI, HTTPException
from uno.api.endpoint.response import DataResponse
from uno.core.di import get_dependency

app = FastAPI(title="Order Query Service")

@app.get("/orders/{order_id}")
async def get_order(
    order_id: UUID,
    query_handler: OrderQueryHandler = Depends(get_dependency(OrderQueryHandler))
) -> DataResponse[OrderDTO]:
    """Get an order by ID."""
    order = await query_handler.handle_get_order_by_id(GetOrderByIdQuery(
        order_id=order_id
    ))
    
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    return DataResponse(data=order)
```

### Dedicated Read Models

Create specialized read models for different query needs:

```python
# Various read models for different query needs
from pydantic import BaseModel
from typing import List

class OrderSummaryReadModel(BaseModel):
    """Simplified order summary for listings."""
    
    id: UUID
    customer_id: UUID
    status: str
    total_amount: float
    item_count: int
    created_at: datetime

class OrderDetailReadModel(BaseModel):
    """Detailed order information."""
    
    id: UUID
    customer_id: UUID
    status: str
    items: List[OrderItemReadModel]
    total_amount: float
    shipping_address: dict
    created_at: datetime
    updated_at: datetime

class CustomerOrdersReadModel(BaseModel):
    """Customer-centric view of orders."""
    
    customer_id: UUID
    orders: List[OrderSummaryReadModel]
    total_spent: float
    average_order_value: float
    first_order_date: datetime
    last_order_date: datetime

# Event handler updating multiple read models
@subscription_manager.subscribe("order_placed")
async def update_read_models_for_order_placed(event: OrderPlaced):
    """Update multiple read models when an order is placed."""
    # Update order summary
    await read_db.order_summaries.update_one(
        {"_id": str(event.order_id)},
        {"$set": {"status": "placed"}}
    )
    
    # Update customer orders
    await read_db.customer_orders.update_one(
        {"_id": str(event.customer_id)},
        {
            "$push": {"order_ids": str(event.order_id)},
            "$inc": {"total_spent": event.total_amount},
            "$set": {"last_order_date": datetime.now(datetime.UTC)}
        },
        upsert=True
    )
    
    # Update sales analytics
    await read_db.sales_analytics.insert_one({
        "date": datetime.now(datetime.UTC),
        "order_id": str(event.order_id),
        "customer_id": str(event.customer_id),
        "amount": event.total_amount
    })
```

### Materialized Views

Use materialized views for complex queries:

```python
class MaterializedViewManager:
    """Manager for materialized views."""
    
    def __init__(self, read_db):
        self.read_db = read_db
    
    async def rebuild_customer_order_stats_view(self):
        """Rebuild the customer order statistics view."""
        # Drop existing view
        await self.read_db.customer_order_stats.drop()
        
        # Create new view with aggregated data
        result = await self.read_db.orders.aggregate([
            # Group by customer
            {"$group": {
                "_id": "$customer_id",
                "total_spent": {"$sum": "$total_amount"},
                "order_count": {"$sum": 1},
                "average_order_value": {"$avg": "$total_amount"},
                "first_order_date": {"$min": "$created_at"},
                "last_order_date": {"$max": "$created_at"}
            }},
            # Project the results
            {"$project": {
                "customer_id": "$_id",
                "total_spent": 1,
                "order_count": 1,
                "average_order_value": 1,
                "first_order_date": 1,
                "last_order_date": 1,
                "_id": 0
            }},
            # Write to new collection
            {"$out": "customer_order_stats"}
        ]).to_list()
        
        return result
```

## Best Practices

1. **Keep Command and Query Models Separate**: Use different models for reads and writes
2. **Use Domain-Driven Design**: Base commands on domain operations
3. **Design for Eventual Consistency**: Accept that read models may be temporarily out of sync
4. **Validate Commands Thoroughly**: Check all business rules before processing commands
5. **Optimize Query Models for Reading**: Denormalize data for efficient reading
6. **Use Events for Integration**: Use events to update read models
7. **Implement Idempotency**: Ensure commands can be safely retried
8. **Document Commands and Queries**: Clearly document all commands and queries
9. **Test Commands and Queries Separately**: Write focused tests for each side
10. **Monitor Performance**: Track metrics for both read and write operations

## When to Use CQRS

CQRS provides significant benefits but adds complexity. Consider CQRS when:

1. **Read and Write Loads Differ**: Different scaling needs for reads and writes
2. **Complex Reporting**: Need to optimize for complex reporting queries
3. **Microservices Architecture**: Fits well with bounded contexts
4. **Event Sourcing**: Planning to use event sourcing for persistence
5. **Complex Business Rules**: Many validation rules for commands

## Conclusion

CQRS in Uno provides a powerful approach to separating read and write operations. By using distinct models for commands and queries, you can optimize each side independently, improve scalability, and create cleaner, more maintainable code.

For more detailed guidance on related patterns:

- [Event-Driven Architecture](event_driven_architecture.md): Combining CQRS with events
- [Domain-Driven Design](domain_driven_design.md): Using DDD with CQRS
- [API Endpoint Framework](../api/endpoint/overview.md): Implementing CQRS in endpoints