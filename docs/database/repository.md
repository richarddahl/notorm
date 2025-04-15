# Repository Pattern

The Uno framework implements the repository pattern for database access, providing a clean separation between data access logic and business logic.

## Overview

The repository pattern abstracts the details of data access, making your code more maintainable, testable, and decoupled from the database implementation.

In Uno, the `UnoBaseRepository` class provides a foundation for all repositories, with methods for common CRUD operations and query functionality.

The repository pattern is a key component of the new database architecture, designed to facilitate dependency injection and improve testability. Repositories encapsulate data access logic, making it easier to mock database operations during testing and providing a more structured approach to data access compared to direct use of database APIs.

## Key Features

- **Generic Implementation**: Works with any SQLAlchemy model
- **Comprehensive CRUD Operations**: Full set of create, read, update, delete methods
- **Filtering & Pagination**: Support for filtering, ordering, and pagination
- **Type Safety**: Full type hints for better IDE support and error checking
- **UnoObj Integration**: Works with both UnoObj and standalone approaches

## Basic Usage

### Creating a Repository

```python
from uno.database.repository import UnoBaseRepository
from myapp.models import UserModel

class UserRepository(UnoBaseRepository[UserModel]):```

def __init__(self, session):```

super().__init__(session, UserModel)
```
    
# Add custom methods as needed
async def find_by_email(self, email: str):```

stmt = select(self.model_class).where(self.model_class.email == email)
result = await self.session.execute(stmt)
return result.scalars().first()
```
```
```

### Using a Repository with FastAPI

```python
from fastapi import APIRouter, Depends
from uno.dependencies import get_db_session, get_repository
from myapp.repositories import UserRepository

router = APIRouter()

@router.get("/users/{user_id}")
async def get_user(```

user_id: str,
repo: UserRepository = Depends(get_repository(UserRepository))
```
):```

user = await repo.get(user_id)
if not user:```

raise HTTPException(status_code=404, detail="User not found")
```
return user
```
```

## Standard Repository Methods

### Retrieval Methods

- **get(id: str)**: Get a single entity by ID
- **list(filters, order_by, limit, offset)**: Get a filtered, ordered, paginated list of entities
- **count(filters)**: Count entities matching the given filters

### Mutation Methods

- **create(data)**: Create a new entity
- **update(id, data)**: Update an existing entity
- **delete(id)**: Delete an entity
- **save(obj)**: Save an entity (create or update based on presence of ID)

### Query Methods

- **execute_query(query, params)**: Execute a raw SQL query

## Advanced Usage

### Custom Query Methods

Repositories can implement custom query methods for domain-specific operations:

```python
class ProductRepository(UnoBaseRepository[ProductModel]):```

async def find_by_category(self, category_id: str, in_stock_only: bool = False):```

stmt = select(self.model_class).where(
    self.model_class.category_id == category_id
)
``````

```
```

if in_stock_only:
    stmt = stmt.where(self.model_class.stock_count > 0)
    
result = await self.session.execute(stmt)
return list(result.scalars().all())
```
```
```

### Integration with UnoObj

The repository can work with UnoObj instances:

```python
from myapp.objs import UserObj

class UserRepository(UnoBaseRepository[UserModel]):```

async def create_from_obj(self, user_obj: UserObj):```

"""Create a user from a UnoObj instance."""
return await self.save(user_obj)
```
```

# Usage
user_obj = UserObj(name="John Doe", email="john@example.com")
user_model = await user_repo.create_from_obj(user_obj)
```

### Transactions

Repositories automatically work with SQLAlchemy's transaction management:

```python
async with db_provider.async_session() as session:```

async with session.begin():```

user_repo = UserRepository(session)
order_repo = OrderRepository(session)
``````

```
```

# Both operations will be in the same transaction
user = await user_repo.get(user_id)
await order_repo.create({
    "user_id": user.id,
    "amount": 100.00
})
# Transaction is committed if no exceptions are raised
```
```
```

## Best Practices

### Repository Organization

- One repository per domain entity
- Group related repositories in modules
- Keep repositories focused on data access operations
- Move business logic to services

### Repository Testing

Repositories are easy to test with the testing utilities:

```python
import pytest
from myapp.repositories import UserRepository
from uno.dependencies.testing import MockRepository, TestSession

@pytest.fixture
def user_repo():```

session = TestSession.create()
return UserRepository(session)
```

def test_find_by_email(user_repo):```

# Configure the mock session
user_repo.session.execute.return_value.scalars.return_value.first.return_value = {```

"id": "123",
"email": "test@example.com"
```
}
``````

```
```

# Test the repository method
user = await user_repo.find_by_email("test@example.com")
assert user.id == "123"
``````

```
```

# Verify the query was correct
user_repo.session.execute.assert_called_once()
```
```

### When to Use Raw SQL

While the repository pattern encourages using SQLAlchemy's ORM, sometimes raw SQL is more appropriate:

```python
class ReportRepository(UnoBaseRepository[ReportModel]):```

async def get_sales_summary(self, start_date, end_date):```

"""Get sales summary using raw SQL for better performance."""
query = """
    SELECT 
        DATE_TRUNC('day', created_at) as date,
        SUM(amount) as total,
        COUNT(*) as count
    FROM orders
    WHERE created_at BETWEEN :start_date AND :end_date
    GROUP BY DATE_TRUNC('day', created_at)
    ORDER BY date
"""
result = await self.execute_query(
    query, 
    {"start_date": start_date, "end_date": end_date}
)
return [dict(row) for row in result]
```
```
```