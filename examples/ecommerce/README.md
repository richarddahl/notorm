# E-commerce Domain Example

This example demonstrates a complete domain-driven design (DDD) implementation for an e-commerce application using the Uno framework. It showcases:

1. **Rich Domain Model** - Value objects, entities, and aggregates
2. **Persistence** - PostgreSQL repository pattern implementation
3. **Event-Driven Architecture** - Domain events, event store, and event handlers
4. **Clean Layered Architecture** - Separation of domain, persistence, and application layers

## Components

- **Domain Layer**
  - Value Objects: Money, Address, EmailAddress, etc.
  - Entities: Product, User, Order, etc.
  - Aggregates: Order (containing OrderItems)
  - Domain Events: ProductCreatedEvent, OrderStatusChangedEvent, etc.

- **Persistence Layer**
  - Repository Implementations: ProductRepository, OrderRepository, UserRepository
  - Event Store: PostgreSQL-based event storage
  
- **Infrastructure**
  - Event Dispatcher: Asynchronous event processing
  - Event Subscribers: Handling domain events

## Getting Started

### Prerequisites

- PostgreSQL 16+
- Python 3.12+
- Uno framework

### Setup

1. **Initialize the database**

   First, make sure the Uno framework database is set up:

   ```bash
   python src/scripts/createdb.py
   ```

2. **Set up the event store schema**

   Next, set up the event store schema for domain events:

   ```bash
   python src/scripts/eventstore.py create
   ```

3. **Run the example setup**

   Initialize the example:

   ```bash
   cd examples/ecommerce
   python setup.py
   ```

4. **Run the integration demo**

   Run the demo to see everything in action:

   ```bash
   python integration_demo.py
   ```

## Key Concepts

### Entity and Aggregate Roots

The example showcases proper entity modeling with identity, business rules, and aggregate boundaries. For example, `Order` is an aggregate root that contains `OrderItem` entities.

### Value Objects

Value objects like `Money`, `Address`, and `EmailAddress` encapsulate domain concepts that are defined by their attributes rather than identity.

### Domain Events

Events like `ProductCreatedEvent` and `OrderStatusChangedEvent` represent important domain occurrences and facilitate loose coupling between components.

### Repository Pattern

The repositories provide a collection-like interface to the domain model while hiding the complexity of data access:

```python
# Example repository usage
product_repo = ProductRepository()
product = await product_repo.get(product_id)

# Update the product
product.update_price(Money(amount=99.99, currency="USD"))
await product_repo.update(product)
```

### Event Sourcing

The example shows how to implement both traditional persistence and event sourcing, allowing for tracking the full history of an aggregate.

## Architecture Diagram

```
┌───────────────────────┐      ┌───────────────────────┐
│   Application Layer   │◄─────┤       API Layer       │
│  (Services, Commands) │      │  (FastAPI Endpoints)  │
└───────────┬───────────┘      └───────────────────────┘
            │
┌───────────▼───────────┐
│     Domain Layer      │      ┌───────────────────────┐
│(Entities, Aggregates, │◄─────┤   Infrastructure      │
│ Value Objects, Events)│      │  (Event Dispatchers)  │
└───────────┬───────────┘      └───────────┬───────────┘
            │                               │
┌───────────▼───────────────────────────────▼───────────┐
│               Persistence Layer                        │
│    (Repositories, Event Store, Database Access)        │
└───────────────────────────────────────────────────────┘
```