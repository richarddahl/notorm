# Domain Protocols

This document explains the protocol-based interfaces for domain models in the `uno` framework.

## Overview

The `uno` framework uses Python's Protocol system to define clear interfaces for domain model components. These protocols provide a common contract for implementations and enable better type checking and code completion.

## Key Protocols

### DomainEventProtocol

Defines the interface for domain events:

```python
from uno.domain.protocols import DomainEventProtocol

# Example class implementing the protocol
class UserCreatedEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    aggregate_id: Optional[str]
    aggregate_type: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert event to dictionary
        return {...}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserCreatedEvent':
        # Create event from dictionary
        return cls(...)
```

### ValueObjectProtocol

Defines the interface for value objects:

```python
from uno.domain.protocols import ValueObjectProtocol

# Example class implementing the protocol
class Address:
    def equals(self, other: Any) -> bool:
        # Check equality based on attributes
        return ...
    
    def validate(self) -> None:
        # Validate the value object
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary
        return {...}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Address':
        # Create from dictionary
        return cls(...)
```

### PrimitiveValueObjectProtocol

Defines the interface for primitive value objects that wrap single values:

```python
from uno.domain.protocols import PrimitiveValueObjectProtocol

# Example class implementing the protocol
class Email:
    value: str
    
    # Inherits methods from ValueObjectProtocol
    
    @classmethod
    def create(cls, value: str) -> 'Email':
        # Create and validate a new email
        return cls(value=value)
```

### EntityProtocol

Defines the interface for domain entities:

```python
from uno.domain.protocols import EntityProtocol, DomainEventProtocol

# Example class implementing the protocol
class User:
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    def register_event(self, event: DomainEventProtocol) -> None:
        # Register a domain event
        ...
    
    def clear_events(self) -> List[DomainEventProtocol]:
        # Clear and return all registered events
        return [...]
    
    def update(self) -> None:
        # Update the entity
        ...
    
    def to_dict(self) -> Dict[str, Any]:
        # Convert to dictionary
        return {...}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        # Create from dictionary
        return cls(...)
```

### AggregateRootProtocol

Defines the interface for aggregate roots:

```python
from uno.domain.protocols import AggregateRootProtocol, EntityProtocol

# Example class implementing the protocol
class Order:
    # Inherits properties and methods from EntityProtocol
    id: str
    created_at: datetime
    updated_at: Optional[datetime]
    version: int
    
    def check_invariants(self) -> None:
        # Check that all aggregate invariants are satisfied
        ...
    
    def apply_changes(self) -> None:
        # Apply changes and ensure consistency
        ...
    
    def add_child_entity(self, entity: EntityProtocol) -> None:
        # Add a child entity
        ...
    
    def get_child_entities(self) -> Set[EntityProtocol]:
        # Get all child entities
        return {...}
```

### SpecificationProtocol

Defines the interface for specifications:

```python
from uno.domain.protocols import SpecificationProtocol, EntityProtocol

# Example class implementing the protocol
class ActiveUserSpecification:
    def is_satisfied_by(self, entity: User) -> bool:
        # Check if the entity satisfies this specification
        return entity.is_active
    
    def and_(self, other: SpecificationProtocol[User]) -> SpecificationProtocol[User]:
        # Combine with another specification using AND
        return AndSpecification(self, other)
    
    def or_(self, other: SpecificationProtocol[User]) -> SpecificationProtocol[User]:
        # Combine with another specification using OR
        return OrSpecification(self, other)
    
    def not_(self) -> SpecificationProtocol[User]:
        # Negate this specification
        return NotSpecification(self)
```

### EntityFactoryProtocol

Defines the interface for entity factories:

```python
from uno.domain.protocols import EntityFactoryProtocol

# Example class implementing the protocol
class UserFactory:
    @classmethod
    def create(cls, **kwargs: Any) -> User:
        # Create a new entity
        return User(**kwargs)
    
    @classmethod
    def create_from_dict(cls, data: Dict[str, Any]) -> User:
        # Create an entity from a dictionary
        return User.from_dict(data)
```

### CommandResultProtocol

Defines the interface for command results:

```python
from uno.domain.protocols import CommandResultProtocol, DomainEventProtocol

# Example class implementing the protocol
class CommandResult:
    is_success: bool
    events: List[DomainEventProtocol]
    
    @property
    def is_failure(self) -> bool:
        # Check if the command result is a failure
        return not self.is_success
    
    @classmethod
    def success(cls, events: Optional[List[DomainEventProtocol]] = None) -> 'CommandResult':
        # Create a successful command result
        return cls(is_success=True, events=events or [])
    
    @classmethod
    def failure(cls, error: Exception) -> 'CommandResult':
        # Create a failed command result
        return cls(is_success=False, events=[])
```

### DomainServiceProtocol

Defines the interface for domain services:

```python
from uno.domain.protocols import DomainServiceProtocol, CommandResultProtocol

# Example class implementing the protocol
class UserService:
    def execute(self, **kwargs: Any) -> CommandResultProtocol:
        # Execute domain logic
        try:
            # Do something with kwargs
            return CommandResult.success([...])
        except Exception as e:
            return CommandResult.failure(e)
```

## Using Protocols

### Type Checking

Protocols enable static type checking with tools like mypy:

```python
from uno.domain.protocols import EntityProtocol, DomainEventProtocol

def publish_events(entity: EntityProtocol) -> None:
    events = entity.clear_events()
    for event in events:
        publish_event(event)

def publish_event(event: DomainEventProtocol) -> None:
    # Publish event to message bus
    event_data = event.to_dict()
    # ...
```

### Runtime Type Checking

You can use protocol types for runtime type checking:

```python
from uno.domain.protocols import EntityProtocol

def is_entity(obj: Any) -> bool:
    return isinstance(obj, EntityProtocol)

# Usage
user = User(id="user-1", username="john")
if is_entity(user):
    print("User is an entity")
```

### Generic Containers

Protocols work well with generic containers:

```python
from typing import List, Dict, Type
from uno.domain.protocols import EntityProtocol, EntityFactoryProtocol

class Registry:
    def __init__(self):
        self.factories: Dict[Type[EntityProtocol], EntityFactoryProtocol] = {}
    
    def register(self, entity_type: Type[EntityProtocol], factory: EntityFactoryProtocol) -> None:
        self.factories[entity_type] = factory
    
    def create(self, entity_type: Type[EntityProtocol], **kwargs: Any) -> EntityProtocol:
        if entity_type not in self.factories:
            raise KeyError(f"No factory registered for {entity_type.__name__}")
        return self.factories[entity_type].create(**kwargs)
```

## Best Practices

1. **Use `@runtime_checkable`**: All domain protocols are runtime checkable, allowing `isinstance()` checks.

2. **Use Generic Protocols**: When a protocol should work with specific types, use generic protocols.

3. **Protocol vs. Implementation**: Keep protocols focused on interface, not implementation details.

4. **Simple Method Signatures**: Keep protocol method signatures simple and focused on the contract.

5. **Document Contracts**: Document what each protocol method is expected to do.

## Implementation Notes

- All protocols are defined with `@runtime_checkable` for runtime type checking.
- Protocols use Python 3.12+ features including Self type.
- Generic type variables are used extensively for type safety.
- Protocols define the minimum interface required, not the full implementation.