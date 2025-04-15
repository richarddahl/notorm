# Domain-Driven Design Guide

This guide introduces domain-driven design (DDD) concepts in the Uno framework and provides practical examples of implementing business logic using the DDD approach.

## Introduction to Domain-Driven Design

Domain-Driven Design is an approach to software development that focuses on understanding the problem domain and creating a software model that reflects it. It emphasizes:

- A rich domain model with behavior, not just data
- Ubiquitous language shared between developers and domain experts
- Bounded contexts that define clear boundaries
- Strategic and tactical design patterns

## Core Components

The Uno framework provides several core components for implementing DDD:

### Entities

Entities are objects defined by their identity, which persists across different states:

```python
from uno.domain.core import Entity

class User(Entity):```

username: str
email: str
is_active: bool = True
``````

```
```

def deactivate(self):```

self.is_active = False
```
```
```

### Value Objects

Value objects are immutable objects defined by their attributes, with no identity:

```python
from uno.domain.core import ValueObject

class Address(ValueObject):```

street: str
city: str
state: str
zip_code: str
```
```

### Aggregates

Aggregates are clusters of entities and value objects that are treated as a single unit:

```python
from uno.domain.core import AggregateRoot
from typing import List

class Order(AggregateRoot):```

customer_id: str
shipping_address: Address
order_items: List[OrderItem] = []
``````

```
```

def add_item(self, item: OrderItem):```

self.order_items.append(item)
self.register_child_entity(item)
```
```
```

### Domain Events

Domain events represent significant occurrences within the domain:

```python
from uno.domain.core import DomainEvent

class OrderPlacedEvent(DomainEvent):```

order_id: str
customer_id: str
total_amount: float
```
```

## Repositories and Services

### Domain Repositories

Repositories provide data access for domain entities:

```python
from uno.dependencies import get_domain_repository
from my_app.domain.models import User

# Get a repository for User entities
user_repository = get_domain_repository(User)

# Use the repository
user = await user_repository.get("user123")
users = await user_repository.list(filters={"is_active": True})
```

### Domain Services

Domain services implement business logic that operates on domain entities:

```python
from uno.dependencies import get_domain_service
from my_app.domain.models import User

# Get a service for User entities
user_service = get_domain_service(User)

# Use the service
user = await user_service.get_by_id("user123")
await user_service.save(user)
```

## Events and Communication

### Publishing Events

```python
from uno.dependencies import get_event_publisher
from my_app.domain.events import UserCreatedEvent

# Get the event publisher
publisher = get_event_publisher()

# Publish an event
event = UserCreatedEvent(user_id="user123", username="johndoe")
await publisher.publish(event)
```

### Subscribing to Events

```python
from uno.dependencies import get_event_bus
from my_app.domain.events import UserCreatedEvent

# Define an event handler
async def notify_user_creation(event: UserCreatedEvent):```

print(f"User created: {event.username}")
```

# Get the event bus
event_bus = get_event_bus()

# Subscribe to events
event_bus.subscribe(UserCreatedEvent, notify_user_creation)
```

## Integration with FastAPI

### Endpoint with Domain Services

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_domain_service
from my_app.domain.models import User

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(user_id: str):```

user_service = get_domain_service(User)
user = await user_service.get_by_id(user_id)
if not user:```

raise HTTPException(status_code=404, detail="User not found")
```
return user
```
```

## Best Practices

1. **Keep Domain Models Rich**: Include behavior in your domain models, not just data.

2. **Use Value Objects**: Use value objects for concepts that have no identity, like money, addresses, or date ranges.

3. **Define Clear Boundaries**: Use bounded contexts to define clear boundaries in your domain.

4. **Use Events for Communication**: Use domain events to communicate between different parts of your application.

5. **Follow SOLID Principles**: Apply SOLID principles to your domain models and services.

6. **Test Your Domain Logic**: Write unit tests for your domain logic, ensuring all business rules are properly enforced.

7. **Use Dependency Injection**: Use the dependency injection container to access repositories and services.

## Example Application

Check out the [example.py](example.py) file for a complete example of using domain-driven design with the Uno framework.