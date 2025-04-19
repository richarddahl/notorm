# Domain Entity Framework

The Domain Entity Framework provides a comprehensive set of classes and utilities for implementing Domain-Driven Design (DDD) patterns in the UNO framework. This document explains the components of the framework and how to use them effectively.

## Overview

The domain entity framework is located in the `uno.domain.entity` package and consists of several key components:

- **EntityBase**: Base class for all domain entities
- **Identity**: Type-safe entity identifier implementation
- **ValueObject**: Base class for immutable value objects
- **AggregateRoot**: Base class for aggregate roots with event collection
- **Repository**: Pattern for data access with specification support
- **Specification**: Pattern for encapsulating query criteria
- **Service**: Pattern for domain and application services

## Entity Classes

### EntityBase

The `EntityBase` class serves as the foundation for all domain entities. It provides:

- Identity management
- Equality based on identity
- Created/updated timestamps
- Serialization and deserialization through Pydantic

```python
from uuid import UUID, uuid4
from uno.domain.entity import EntityBase

class User(EntityBase[UUID]):
    name: str
    email: str
    
    @classmethod
    def create(cls, name: str, email: str) -> "User":
        return cls(
            id=uuid4(),
            name=name,
            email=email
        )
```

### Identity

The `Identity` and `IdentityGenerator` classes provide type-safe entity identification:

```python
from uno.domain.entity import Identity, IdentityGenerator

# Creating a typed ID class
UserID = Identity["User", UUID]

# Using the ID generator
user_id = IdentityGenerator.next_id(UserID)
```

### ValueObject

Value objects are immutable objects defined by their attributes rather than identity:

```python
from uno.domain.entity import ValueObject

class Address(ValueObject):
    street: str
    city: str
    state: str
    zip_code: str
    
    def formatted(self) -> str:
        return f"{self.street}, {self.city}, {self.state} {self.zip_code}"
```

### AggregateRoot

An aggregate root is an entity that encapsulates a cluster of objects and ensures their consistency:

```python
from uno.domain.entity import AggregateRoot, EntityBase

class Order(AggregateRoot[UUID]):
    customer_id: UUID
    items: List[OrderItem] = []
    total: float = 0.0
    
    def add_item(self, item: OrderItem) -> None:
        self.items.append(item)
        self.total += item.price * item.quantity
        self.record_event(OrderItemAdded(
            order_id=self.id,
            item_id=item.id
        ))
        
    def get_uncommitted_events(self) -> List[Event]:
        return self._events
        
    def clear_events(self) -> None:
        self._events.clear()
```

## Repository Pattern

### EntityRepository

The `EntityRepository` class provides a standardized interface for working with domain entities:

```python
from uno.domain.entity import EntityRepository, SQLAlchemyRepository, EntityMapper

# Define your repository by extending EntityRepository
class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    def __init__(self, session: AsyncSession):
        mapper = EntityMapper(
            entity_type=User,
            model_type=UserModel,
            to_entity=model_to_entity,
            to_model=entity_to_model
        )
        super().__init__(session, mapper)
```

### Repository Usage

Basic repository operations:

```python
# Create a new entity
user = User.create("John Doe", "john@example.com")
await repository.add(user)

# Get by ID
user = await repository.get(user_id)

# Update
user.email = "new_email@example.com"
await repository.update(user)

# Delete
await repository.delete(user)
```

## Specification Pattern

### Creating Specifications

Specifications allow you to encapsulate query criteria in reusable objects:

```python
from uno.domain.entity.specification import Specification

class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.is_active

# Using built-in specifications
from uno.domain.entity import AttributeSpecification

email_spec = AttributeSpecification("email", "john@example.com")
```

### Combining Specifications

Specifications can be combined using logical operators:

```python
# AND combination
active_premium_spec = ActiveUserSpecification().and_(PremiumUserSpecification())

# OR combination
email_or_name_spec = email_spec.or_(AttributeSpecification("name", "John"))

# NOT operation
inactive_spec = ActiveUserSpecification().not_()
```

### Using Specifications with Repositories

Repositories support querying with specifications:

```python
# Find all matching entities
active_users = await repository.find(ActiveUserSpecification())

# Find a single entity
admin_user = await repository.find_one(
    AttributeSpecification("role", "admin")
)

# Count entities
premium_count = await repository.count(PremiumUserSpecification())
```

## Service Pattern

### DomainService

Domain services encapsulate business logic that doesn't naturally belong to entities:

```python
from uno.domain.entity import DomainService
from uno.core.errors.result import Result, Success, Failure

class UserService(DomainService[User, UUID]):
    async def authenticate(self, email: str, password: str) -> Result[User, str]:
        # Find user by email
        user = await self.repository.find_one(
            AttributeSpecification("email", email)
        )
        
        if user is None:
            return Failure("User not found")
            
        if not self._verify_password(user, password):
            return Failure("Invalid password")
            
        return Success(user)
        
    def _verify_password(self, user: User, password: str) -> bool:
        # Password verification logic
        pass
```

### Application Service

Application services coordinate operations across multiple domain services:

```python
from uno.domain.entity import ApplicationService

class OrderingService(ApplicationService[Dict, str]):
    def __init__(
        self,
        user_service: UserService,
        product_service: ProductService,
        order_service: OrderService
    ):
        super().__init__()
        self.user_service = user_service
        self.product_service = product_service
        self.order_service = order_service
        
    async def place_order(
        self, user_id: UUID, product_ids: List[UUID]
    ) -> Result[Order, str]:
        # Validation
        user_result = await self.user_service.get_by_id(user_id)
        if not user_result.is_success():
            return user_result
            
        # Product validation
        products_result = await self.product_service.get_products(product_ids)
        if not products_result.is_success():
            return products_result
            
        # Create order
        return await self.order_service.create_order(
            user_result.value, products_result.value
        )
```

### Service With Unit of Work

For managing transactions across repositories:

```python
from uno.domain.entity import DomainServiceWithUnitOfWork

class OrderService(DomainServiceWithUnitOfWork[Order, UUID]):
    async def create_order(self, user: User, products: List[Product]) -> Result[Order, str]:
        async with self.with_uow("create_order"):
            # This code runs in a transaction
            await self._ensure_repository()
            
            # Create order
            order = Order(
                id=uuid4(),
                user_id=user.id,
                total=sum(p.price for p in products)
            )
            
            # Add products to order
            for product in products:
                # Update inventory
                product_repo = self.unit_of_work.get_repository(Product)
                product.inventory_count -= 1
                await product_repo.update(product)
                
                # Add to order
                order.add_item(OrderItem(
                    id=uuid4(),
                    product_id=product.id,
                    price=product.price,
                    quantity=1
                ))
                
            # Save order
            order = await self.repository.add(order)
            return Success(order)
```

## Factory Pattern

The `ServiceFactory` simplifies the creation of services:

```python
from uno.domain.entity import ServiceFactory

# Create a factory for the User entity
factory = ServiceFactory(
    User,
    repository_factory=create_user_repository,
    unit_of_work_factory=create_unit_of_work
)

# Create domain service
user_service = factory.create_domain_service()

# Create domain service with UoW
user_service_with_uow = factory.create_domain_service_with_uow()

# Create CRUD service
user_crud_service = factory.create_crud_service()
```

## Best Practices

### Entity Design

1. Keep entities focused on their core domain responsibilities
2. Use value objects for immutable values
3. Implement business rules in domain services
4. Use AggregateRoot for entities that need to maintain consistency across multiple objects
5. Use entities' domain events to trigger side effects

### Repository Design

1. Define repository interfaces for each entity type
2. Use specifications for query criteria
3. Implement optimized repository adapters for different data sources
4. Use the Unit of Work pattern for transactions
5. Keep repository methods focused on data access (no business logic)

### Service Design

1. Use domain services for business logic that doesn't fit on entities
2. Use application services to coordinate multiple domain services
3. Return Result objects to handle errors elegantly
4. Use the service factory to simplify service creation
5. Document service methods clearly

## Migration from Legacy Patterns

If you're migrating from legacy patterns, follow these steps:

1. Replace `UnoEntityService` with `DomainService`
2. Replace `BaseRepository` with `EntityRepository`
3. Replace old specifications with the new specification pattern
4. Use `DomainServiceWithUnitOfWork` instead of manual transaction management
5. Replace service factory methods with `ServiceFactory`

## Examples

Comprehensive examples are available in the `uno.domain.entity.examples` package:

- `repository_example.py`: Demonstrates repository usage with specifications
- `specification_querying.py`: Shows real-world specification usage
- `service_example.py`: Illustrates domain and application services

## Further Reading

- [Domain-Driven Design](https://domaindrivendesign.org/)
- [Specification Pattern](https://martinfowler.com/apsupp/spec.pdf)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [UNO Framework Architecture](architecture.md)