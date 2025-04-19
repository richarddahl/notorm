# Repository Pattern in UNO

This document explains the Repository pattern implementation in the UNO framework's domain entity package. It covers the different repository types, their capabilities, and how to use them effectively in your applications.

## Overview

The Repository pattern in the UNO framework is implemented in the `uno.domain.entity.repository` module and includes the following components:

- **EntityRepository**: Base abstract class defining the repository interface
- **InMemoryRepository**: In-memory implementation for testing and prototyping
- **SQLAlchemyRepository**: SQLAlchemy-based implementation for database access
- **EntityMapper**: Utility for mapping between domain entities and database models

The repository pattern abstracts data access logic, allowing domain entities to remain focused on business logic without concerns about data persistence.

## Core Concepts

### EntityRepository

The `EntityRepository` class defines the standard repository interface for working with domain entities:

```python
from uno.domain.entity.repository import EntityRepository
from uno.domain.entity.base import EntityBase
from uuid import UUID

class User(EntityBase[UUID]):
    name: str
    email: str

class UserRepository(EntityRepository[User, UUID]):
    async def get(self, id: UUID) -> Optional[User]:
        # Implementation details
        ...
    
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[User]:
        # Implementation details
        ...
    
    # Other required methods
```

### Repository Operations

All repositories support the following operations:

- **get(id)**: Get an entity by ID
- **get_or_fail(id)**: Get an entity by ID or return a Failure
- **list(filters, order_by, limit, offset)**: List entities with filtering and pagination
- **add(entity)**: Add a new entity
- **update(entity)**: Update an existing entity 
- **delete(entity)**: Delete an entity
- **exists(id)**: Check if an entity with the given ID exists
- **delete_by_id(id)**: Delete an entity by ID
- **save(entity)**: Save an entity (create or update based on existence)

### Specification Support

Repositories include methods for working with the Specification pattern:

- **find(specification)**: Find entities matching a specification
- **find_one(specification)**: Find a single entity matching a specification
- **count(specification)**: Count entities matching a specification

### Batch Operations

For efficiency, repositories include methods for batch operations:

- **add_many(entities)**: Add multiple entities
- **update_many(entities)**: Update multiple entities
- **delete_many(entities)**: Delete multiple entities
- **delete_by_ids(ids)**: Delete entities by their IDs

### Streaming Support

For working with large datasets, repositories include streaming support:

- **stream(specification, order_by, batch_size)**: Stream entities matching a specification

## Implementations

### InMemoryRepository

The `InMemoryRepository` class provides an in-memory implementation useful for testing and prototyping:

```python
from uno.domain.entity.repository_memory import InMemoryRepository
from uuid import UUID

# Create an in-memory repository
repository = InMemoryRepository[User, UUID](User)

# Use the repository
user = User(id=UUID('...'), name="John", email="john@example.com")
await repository.add(user)
users = await repository.list()
```

### SQLAlchemyRepository

The `SQLAlchemyRepository` class provides a SQLAlchemy-based implementation for database access:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper

# Define SQLAlchemy model
Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)

# Define mapping functions
def model_to_entity(model: UserModel) -> User:
    return User(
        id=UUID(model.id),
        name=model.name,
        email=model.email
    )

def entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=str(entity.id),
        name=entity.name,
        email=entity.email
    )

# Create entity mapper
mapper = EntityMapper(
    entity_type=User,
    model_type=UserModel,
    to_entity=model_to_entity,
    to_model=entity_to_model
)

# Create SQLAlchemy repository
session = AsyncSession(...)  # Your SQLAlchemy session
repository = SQLAlchemyRepository[User, UUID, UserModel](session, mapper)
```

## Working with Specifications

The repository implementations provide powerful specification-based querying:

```python
from uno.domain.entity.specification import Specification, AttributeSpecification

# Using custom specifications
class ActiveUserSpecification(Specification[User]):
    def is_satisfied_by(self, candidate: User) -> bool:
        return candidate.is_active

# Using built-in specifications
email_spec = AttributeSpecification("email", "john@example.com")
role_spec = AttributeSpecification("role", "admin")

# Combining specifications
active_admin_spec = ActiveUserSpecification().and_(role_spec)

# Using specifications with repositories
active_admins = await repository.find(active_admin_spec)
john = await repository.find_one(email_spec)
admin_count = await repository.count(role_spec)
```

## Integration with SQLAlchemy

The `SQLAlchemyRepository` integrates with SQLAlchemy to translate specifications into SQL queries:

```python
# The SQLAlchemyRepository automatically translates specifications to SQL
# For example, this query:
users = await repository.find(
    AttributeSpecification("name", "John").and_(
        AttributeSpecification("role", "admin")
    )
)

# Gets translated to something like:
# SELECT * FROM users WHERE name = 'John' AND role = 'admin'
```

The repository implementation includes an automatic specification translator that handles conversions between domain specifications and SQL expressions.

## Transactions and Unit of Work

Repositories are designed to work with the Unit of Work pattern for transaction management:

```python
from uno.core.uow import AbstractUnitOfWork, SqlAlchemyUnitOfWork

# Create a unit of work
uow = SqlAlchemyUnitOfWork(session_factory)

# Register repositories
uow.register_repository(User, user_repository)
uow.register_repository(Order, order_repository)

# Use the unit of work
async with uow:
    # Get repositories from the unit of work
    user_repo = uow.get_repository(User)
    order_repo = uow.get_repository(Order)
    
    # Perform operations
    user = await user_repo.get(user_id)
    order = await order_repo.get(order_id)
    
    # Update entities
    user.name = "New Name"
    order.status = "completed"
    
    await user_repo.update(user)
    await order_repo.update(order)
    
    # Commit or rollback happens automatically
```

## Advanced Features

### Custom Repository Methods

You can extend the repository interface with custom domain-specific methods:

```python
class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    async def find_by_email(self, email: str) -> Optional[User]:
        email_spec = AttributeSpecification("email", email)
        return await self.find_one(email_spec)
    
    async def find_active_users(self) -> List[User]:
        active_spec = AttributeSpecification("is_active", True)
        return await self.find(active_spec)
    
    async def count_by_role(self, role: str) -> int:
        role_spec = AttributeSpecification("role", role)
        return await self.count(role_spec)
```

### Optimizing Queries

The SQLAlchemy repository allows for query optimization:

```python
class ProductRepository(SQLAlchemyRepository[Product, UUID, ProductModel]):
    def _specification_to_where_clause(self, specification: Specification[Product]) -> Optional[Any]:
        # Custom specification translation logic for optimized queries
        if isinstance(specification, ProductCategorySpecification):
            # Optimize category queries
            return self.mapper.model_type.category_id == specification.category_id
        
        # Fall back to default translation
        return super()._specification_to_where_clause(specification)
```

### In-Memory Filtering

If a specification can't be translated to SQL, the repository automatically falls back to in-memory filtering:

```python
class CustomSpecification(Specification[User]):
    def is_satisfied_by(self, candidate: User) -> bool:
        # Complex logic that can't be translated to SQL
        return some_complex_calculation(candidate)

# This will work, but will load all users and filter in memory
users = await repository.find(CustomSpecification())
```

## Best Practices

### Repository Design

1. Define a repository interface for each aggregate root
2. Keep repositories focused on data access (no business logic)
3. Use specifications for query criteria instead of ad-hoc filters
4. Implement optimized query methods for common operations
5. Consider batching for bulk operations

### Entity Mapping

1. Keep mapping logic simple and focused on conversion
2. Separate mapping concerns from repository implementation
3. Use type annotations to ensure type safety
4. Handle null values and optional fields correctly
5. Consider using library mapping tools for complex mappings

### Transaction Management

1. Use the Unit of Work pattern for coordinating multiple repositories
2. Register repositories with the unit of work explicitly
3. Start transactions at the service level, not in repositories
4. Let the Unit of Work manage transaction boundaries
5. Use explicit transaction names for debugging and logging

### Testing

1. Use `InMemoryRepository` for unit testing services
2. Create test fixtures for common repository operations
3. Test specification translations and compositions
4. Consider using SQLite for integration testing
5. Test transaction rollback scenarios

## Migration from Legacy Repositories

If you're migrating from legacy repository implementations in UNO, follow these steps:

1. Replace `BaseRepository` implementations with `EntityRepository`
2. Replace custom query methods with specification-based queries
3. Replace manual SQL queries with repository operations
4. Add deprecation warnings to legacy repository implementations
5. Update repository consumers to use the new pattern

## Example: Complete Implementation

Here's a complete example showing how to implement and use a repository:

```python
# Define domain entity
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List, Dict, Any
from uno.domain.entity import EntityBase

class User(EntityBase[UUID]):
    name: str
    email: str
    is_active: bool = True
    role: str = "user"
    last_login: Optional[datetime] = None

# Define SQLAlchemy model
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

# Define mapping functions
def model_to_entity(model: UserModel) -> User:
    return User(
        id=UUID(model.id),
        name=model.name,
        email=model.email,
        is_active=model.is_active,
        role=model.role,
        last_login=model.last_login,
        created_at=model.created_at,
        updated_at=model.updated_at
    )

def entity_to_model(entity: User) -> UserModel:
    return UserModel(
        id=str(entity.id),
        name=entity.name,
        email=entity.email,
        is_active=entity.is_active,
        role=entity.role,
        last_login=entity.last_login,
        created_at=entity.created_at,
        updated_at=entity.updated_at
    )

# Define repository
from sqlalchemy.ext.asyncio import AsyncSession
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper
from uno.domain.entity.specification import AttributeSpecification, Specification

class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    def __init__(self, session: AsyncSession):
        mapper = EntityMapper(
            entity_type=User,
            model_type=UserModel,
            to_entity=model_to_entity,
            to_model=entity_to_model
        )
        super().__init__(session, mapper)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email address."""
        email_spec = AttributeSpecification("email", email)
        return await self.find_one(email_spec)
    
    async def find_active_by_role(self, role: str) -> List[User]:
        """Find all active users with a specific role."""
        role_spec = AttributeSpecification("role", role)
        active_spec = AttributeSpecification("is_active", True)
        
        return await self.find(role_spec.and_(active_spec))

# Custom specification
class RecentLoginSpecification(Specification[User]):
    def __init__(self, days: int = 30):
        self.days = days
    
    def is_satisfied_by(self, candidate: User) -> bool:
        if not candidate.last_login:
            return False
        
        cutoff = datetime.now() - timedelta(days=self.days)
        return candidate.last_login >= cutoff

# Usage example
async def main():
    # Create session
    session = AsyncSession(engine)
    
    # Create repository
    repository = UserRepository(session)
    
    # Create a user
    user = User(
        id=uuid4(),
        name="John Doe",
        email="john@example.com",
        role="admin"
    )
    
    # Add user
    await repository.add(user)
    
    # Find user by ID
    found_user = await repository.get(user.id)
    print(f"Found user: {found_user.name}")
    
    # Find user by email
    email_user = await repository.find_by_email("john@example.com")
    print(f"Email lookup: {email_user.name}")
    
    # Find users by role
    admin_users = await repository.find_active_by_role("admin")
    print(f"Found {len(admin_users)} active admins")
    
    # Use custom specification
    recent_users = await repository.find(RecentLoginSpecification(7))
    print(f"Found {len(recent_users)} users who logged in within the last week")
    
    # Update user
    if found_user:
        found_user.role = "super_admin"
        await repository.update(found_user)
    
    # Delete user
    await repository.delete_by_id(user.id)
```

## Further Reading

- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Specification Pattern](docs/domain/specification_pattern.md)
- [Unit of Work Pattern](https://martinfowler.com/eaaCatalog/unitOfWork.html)
- [Domain-Driven Design](https://domaindrivendesign.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)