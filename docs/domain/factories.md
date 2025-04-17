# Domain Model Factories

This document explains the factory pattern implementation for domain models in the `uno` framework.

## Overview

Factories in Domain-Driven Design (DDD) encapsulate the creation logic for domain objects. They provide a way to construct domain entities and value objects with proper validation, event registration, and dependency wiring. The `uno` framework provides a comprehensive factory implementation for domain entities, aggregate roots, and value objects.

## Key Components

### EntityFactory

The `EntityFactory` is a generic base class for creating domain entities. It provides methods for:

- Creating new entities with generated IDs
- Creating entities with registered domain events
- Reconstituting entities from data (e.g., from a database)

```python
# Example: Creating a user entity
user = UserFactory.create(
    username="johndoe",
    email="john@example.com"
)

# Example: Creating with events
user_created_event = UserCreatedEvent(username="johndoe")
user = UserFactory.create_with_events(
    [user_created_event],
    username="johndoe",
    email="john@example.com"
)
```

### AggregateFactory

The `AggregateFactory` extends the `EntityFactory` with aggregate-specific functionality, such as handling child entities and checking invariants:

```python
# Example: Creating an order aggregate with line items
order = OrderFactory.create_with_children(
    [
        LineItemFactory.create(product_id="prod-1", quantity=2),
        LineItemFactory.create(product_id="prod-2", quantity=1)
    ],
    customer_id="cust-123",
    status="pending"
)
```

### ValueObjectFactory

The `ValueObjectFactory` provides methods for creating value objects with proper validation:

```python
# Example: Creating an email value object
email = EmailFactory.create(value="john@example.com")

# Example: Creating from dictionary
address = AddressFactory.create_from_dict({
    "street": "123 Main St",
    "city": "Anytown",
    "state": "CA",
    "postal_code": "12345",
    "country": "US"
})
```

### FactoryRegistry

The `FactoryRegistry` provides a central place to register and access factories for domain objects:

```python
# Example: Setting up a factory registry
registry = FactoryRegistry()
registry.register_entity_factory(User, UserFactory)
registry.register_entity_factory(Order, OrderFactory)
registry.register_value_factory(Email, EmailFactory)

# Example: Getting factories from the registry
user_factory = registry.get_entity_factory(User)
email_factory = registry.get_value_factory(Email)
```

### Factory Creation Helpers

Helper functions for creating factory classes for specific entity, aggregate, and value object types:

```python
# Example: Creating a factory for a custom entity
class Product(Entity):
    name: str
    price: float

ProductFactory = create_entity_factory(Product)

# Example: Using the created factory
product = ProductFactory.create(name="Widget", price=9.99)
```

## Integration with Dependency Injection

Factories integrate naturally with the dependency injection system:

```python
# Example: Registering factories in the DI container
container.register(EntityFactoryProtocol[User], UserFactory)
container.register(ValueObjectFactory[Email], EmailFactory)

# Example: Injecting factories into services
@inject
class UserService:
    def __init__(self, user_factory: EntityFactoryProtocol[User]):
        self.user_factory = user_factory
    
    def create_user(self, username: str, email: str) -> User:
        return self.user_factory.create(
            username=username,
            email=email
        )
```

## Best Practices

1. **Use Factory Methods**: Always use factory methods to create domain objects, rather than direct instantiation.

2. **Encapsulate Creation Logic**: Complex creation logic should be encapsulated in factory methods, not exposed to clients.

3. **Factory Per Aggregate**: Create dedicated factories for each aggregate root.

4. **Validate in Factories**: Ensure all business rules are enforced during object creation.

5. **Events in Creation**: Register domain events during entity creation when appropriate.

6. **Use Registry**: Use the factory registry for centralized factory management in larger applications.

## Implementation Notes

- All factories are stateless and use class methods for entity creation.
- Factories include proper type hints for better tooling support.
- Factory methods take keyword arguments for flexibility and readability.
- Custom validation is enforced during object creation.