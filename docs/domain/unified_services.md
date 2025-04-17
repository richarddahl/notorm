# Unified Domain Services

This document describes the standardized domain service pattern in the uno framework, designed to provide a consistent approach to implementing domain services that work with the domain model and the unified event system.

## Overview

Domain services encapsulate operations and business logic that don't naturally belong to entities or value objects. They provide a clear boundary for complex operations that may involve multiple domain objects or external resources.

The unified domain service pattern implements the following key concepts:

- **Transactional Boundaries** - Services manage transaction boundaries with appropriate error handling
- **Domain Events** - Services collect and publish domain events using the unified event system
- **Validation** - Services validate input data before processing
- **Result Pattern** - Services return results instead of throwing exceptions
- **Factory** - Services are created using a factory that provides appropriate dependencies

## Service Types

The unified domain service pattern includes the following service types:

### DomainService

The `DomainService` class is the base class for domain services that require transactions. It provides:

- Transaction management through a Unit of Work
- Input validation
- Error handling with Result objects
- Domain event collection and publishing

```python
class CreateOrderService(DomainService[CreateOrderInput, OrderOutput, UnitOfWork]):
    def __init__(self, uow: UnitOfWork, order_repository: OrderRepository):
        super().__init__(uow)
        self.order_repository = order_repository
    
    async def _execute_internal(self, input_data: CreateOrderInput) -> Result[OrderOutput]:
        # Create order
        order = Order(
            id=uuid.uuid4(),
            customer_id=input_data.customer_id,
            items=input_data.items
        )
        
        # Add order to repository
        saved_order = await self.order_repository.add(order)
        
        # Return success
        return Success(OrderOutput.from_entity(saved_order))
```

### ReadOnlyDomainService

The `ReadOnlyDomainService` class is for read-only operations that don't modify domain state. It provides:

- Input validation
- Error handling with Result objects
- No transaction boundaries (for performance)

```python
class GetOrderService(ReadOnlyDomainService[str, OrderOutput, UnitOfWork]):
    def __init__(self, uow: UnitOfWork, order_repository: OrderRepository):
        super().__init__(uow)
        self.order_repository = order_repository
    
    async def _execute_internal(self, input_data: str) -> Result[OrderOutput]:
        # Get order by ID
        order = await self.order_repository.get(input_data)
        
        # Check if order exists
        if order is None:
            return Failure(f"Order with ID {input_data} not found")
        
        # Return success
        return Success(OrderOutput.from_entity(order))
```

### EntityService

The `EntityService` class provides standard CRUD operations for domain entities. It includes:

- Get, find, list, create, update, delete operations
- Event publishing for domain events
- Error handling with Result objects

```python
# Create an entity service
product_service = EntityService(
    entity_type=Product,
    repository=product_repository
)

# Use the service
result = await product_service.create({
    "name": "New Product",
    "price": 29.99,
    "description": "A brand new product"
})
```

### AggregateService

The `AggregateService` class provides operations for working with aggregate roots, with additional features:

- Optimistic concurrency control using version numbers
- Child entity management
- Transaction management with Unit of Work
- Event publishing for domain events

```python
# Create an aggregate service
order_service = AggregateService(
    aggregate_type=Order,
    repository=order_repository,
    unit_of_work=uow
)

# Use the service
result = await order_service.update(
    id="order-123",
    version=1,  # Current version for concurrency control
    data={"status": "shipped"}
)
```

## Domain Service Factory

The `DomainServiceFactory` creates domain services with proper dependencies:

```python
# Initialize the factory
initialize_service_factory(unit_of_work_factory)

# Register entity types with repositories
service_factory = get_service_factory()
service_factory.register_entity_type(Order, order_repository)
service_factory.register_entity_type(Product, product_repository)

# Create services
order_service = service_factory.create_domain_service(
    CreateOrderService,
    order_repository=order_repository
)

product_service = service_factory.create_entity_service(Product)
```

## Working with Results

All domain services use the Result pattern for error handling:

```python
# Execute a domain service
result = await create_order_service.execute(input_data)

# Check the result
if result.is_success:
    # Handle success case
    order = result.value
    return {"id": str(order.id), "message": "Order created successfully"}
else:
    # Handle failure case
    return {"error": result.error}
```

## Integration with Event System

Domain services integrate with the unified event system:

1. **Collecting Events** - Domain services collect events from domain entities
2. **Publishing Events** - Events are published after successful transactions
3. **Event Handlers** - Events can be handled by subscribers registered with the event bus

```python
# Define an event handler
@event_handler(OrderCreatedEvent)
async def notify_customer(event: OrderCreatedEvent):
    # Send notification to customer
    await notification_service.send(
        to=event.customer_email,
        subject="Order Confirmation",
        message=f"Your order {event.order_id} has been created."
    )

# Register the handler
subscribe_handler(OrderCreatedEvent, notify_customer)
```

## Best Practices

1. **Separation of Concerns**
   - Use domain services for complex operations involving multiple entities
   - Keep entity methods focused on their own state and behavior

2. **Transaction Management**
   - Use `DomainService` for operations that modify state
   - Use `ReadOnlyDomainService` for queries and reporting

3. **Event Handling**
   - Let entities publish domain events when their state changes
   - Use domain services to collect and persist events
   - Register event handlers for cross-domain integration

4. **Error Handling**
   - Always use the Result pattern to return success or failure
   - Provide meaningful error messages in failure cases
   - Handle expected errors gracefully using the Result pattern

5. **Testing**
   - Test domain services with mock repositories and unit of work
   - Test event handling separately from domain logic
   - Use in-memory implementations for integration testing