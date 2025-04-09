# UnoDB

The `UnoDB` class is a factory-generated class that provides database operations for `UnoObj` models. It handles CRUD operations, filtering, and other database interactions.

## Overview

`UnoDB` is created by the `UnoDBFactory` and provides:

- Create, read, update, and delete (CRUD) operations
- Filtering and querying
- Transaction management
- Error handling
- Connection pooling

## Basic Usage

### Creating a UnoDB Instance

The `UnoDB` class is typically created automatically by the `UnoObj` class:

```python
from uno.obj import UnoObj
from uno.model import UnoModel

class CustomerModel(UnoModel):
    # Model definition...
    pass

class Customer(UnoObj[CustomerModel]):
    model = CustomerModel
    # The UnoObj.__init__ method will create a UnoDB instance
    # self.db = UnoDBFactory(obj=self.__class__)
```

However, you can also create it manually:

```python
from uno.db.db import UnoDBFactory

# Create a UnoDB for the Customer class
customer_db = UnoDBFactory(obj=Customer)
```

### Creating Records

```python
from uno.schema import UnoSchemaConfig

# Define a schema
schema_config = UnoSchemaConfig()
schema = schema_config.create_schema("create_schema", Customer)

# Create a new customer instance
new_customer = schema(
    name="John Doe",
    email="john@example.com"
)

# Save to database
customer, created = await customer_db.create(schema=new_customer)
```

### Retrieving Records

```python
# Get by ID
customer = await customer_db.get(id="abc123")

# Get by natural key
customer = await customer_db.get(email="john@example.com")
```

### Updating Records

```python
# Get the customer to update
customer = await customer_db.get(id="abc123")

# Update fields
customer.name = "John Smith"

# Save changes
updated_customer = await customer_db.update(to_db_model=customer)
```

### Deleting Records

```python
# Get the customer to delete
customer = await customer_db.get(id="abc123")

# Delete
await customer_db.delete(customer)
```

### Filtering Records

```python
from uno.db.db import FilterParam

# Create filter parameters
filter_params = FilterParam(
    limit=10,
    offset=0,
    name__contains="John"
)

# Get filtered customers
customers = await customer_db.filter(filters=filter_params)
```

### Merging Records

The merge operation performs an upsert (insert or update) based on the primary key:

```python
# Create a customer that may already exist
customer_data = {
    "id": "abc123",  # May or may not exist
    "name": "John Smith",
    "email": "john@example.com"
}

# Merge will update if ID exists, or create if it doesn't
result = await customer_db.merge(customer_data)
action = result[0].pop("_action")  # "insert" or "update"
merged_customer = result[0]
```

## Advanced Usage

### Table Keys

You can get information about a table's keys:

```python
# Get primary keys and unique constraints
pk_fields, unique_constraints = customer_db.table_keys()

print(f"Primary key fields: {pk_fields}")
print(f"Unique constraints: {unique_constraints}")
```

### Custom SQL Execution

You can execute custom SQL:

```python
# Define a custom executor function
async def custom_executor(conn, sql_text):
    result = await conn.execute(sql_text)
    return result.fetchall()

# Execute custom SQL
result = await customer_db.execute_sql(
    "SELECT * FROM customer WHERE name LIKE :name",
    params={"name": "%John%"},
    executor=custom_executor
)
```

### Transaction Management

You can manage transactions explicitly:

```python
from sqlalchemy.ext.asyncio import AsyncSession

async def transfer_funds(from_account_id: str, to_account_id: str, amount: float):
    async with AsyncSession() as session:
        # Start a transaction
        async with session.begin():
            # Get accounts
            from_account = await account_db.get(id=from_account_id, session=session)
            to_account = await account_db.get(id=to_account_id, session=session)
            
            # Check balance
            if from_account.balance < amount:
                raise ValueError("Insufficient funds")
                
            # Update balances
            from_account.balance -= amount
            to_account.balance += amount
            
            # Save changes
            await account_db.update(to_db_model=from_account, session=session)
            await account_db.update(to_db_model=to_account, session=session)
            
            # The transaction will be committed if no exceptions are raised
            # or rolled back if an exception occurs
```

### Error Handling

The `UnoDB` class provides specific exceptions for different error scenarios:

```python
from uno.db.db import IntegrityConflictException, NotFoundException

try:
    # Try to get a record
    customer = await customer_db.get(id="nonexistent")
except NotFoundException as e:
    # Handle not found
    print(f"Customer not found: {e}")
except IntegrityConflictException as e:
    # Handle integrity conflict (e.g., duplicate keys)
    print(f"Integrity conflict: {e}")
except Exception as e:
    # Handle other errors
    print(f"Unknown error: {e}")
```

## Common Patterns

### Batch Operations

Perform batch operations for better performance:

```python
async def batch_create_customers(customers: list):
    """Create multiple customers in a single transaction."""
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with AsyncSession() as session:
        async with session.begin():
            # Add all customers to the session
            for customer_data in customers:
                customer = CustomerModel(**customer_data)
                session.add(customer)
            
            # Commit the transaction
            await session.commit()
            
            return len(customers)
```

### Pagination

Implement pagination for large result sets:

```python
async def get_paginated_customers(page: int = 1, page_size: int = 10):
    """Get paginated customers."""
    # Calculate offset
    offset = (page - 1) * page_size
    
    # Create filter parameters
    filter_params = FilterParam(
        limit=page_size,
        offset=offset,
        order_by="name"  # Sort by name
    )
    
    # Get filtered customers
    customers = await customer_db.filter(filters=filter_params)
    
    # Count total (would need a separate query)
    total_count = await count_customers()
    
    # Calculate total pages
    total_pages = (total_count + page_size - 1) // page_size
    
    return {
        "data": customers,
        "page": page,
        "page_size": page_size,
        "total_items": total_count,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }

async def count_customers():
    """Count total customers."""
    # This would need a custom query
    # This is a simplified example
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with AsyncSession() as session:
        result = await session.execute(
            select(func.count()).select_from(CustomerModel)
        )
        return result.scalar_one()
```

### Soft Delete

Implement soft delete functionality:

```python
async def soft_delete_customer(customer_id: str):
    """Soft delete a customer."""
    # Get the customer
    customer = await customer_db.get(id=customer_id)
    
    # Mark as deleted
    customer.is_deleted = True
    customer.deleted_at = datetime.datetime.now()
    
    # Update in database
    await customer_db.update(to_db_model=customer)
    
    return customer

async def get_active_customers():
    """Get only active customers."""
    # Create filter parameters
    filter_params = FilterParam(
        is_deleted=False,
        is_active=True
    )
    
    # Get filtered customers
    return await customer_db.filter(filters=filter_params)
```

## Testing

When testing database operations, use transactions or mocking:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_create_customer():
    """Test creating a customer."""
    # Mock the database
    with patch("uno.db.db.async_session") as mock_session:
        # Setup the mock
        mock_session_instance = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_session_instance
        
        # Create a customer
        customer_data = {
            "name": "Test Customer",
            "email": "test@example.com"
        }
        
        # Convert to a model instance
        customer = CustomerModel(**customer_data)
        
        # Call the create method
        result, created = await customer_db.create(schema=customer)
        
        # Verify
        assert created is True
        assert mock_session_instance.add.called
        assert mock_session_instance.commit.called
```

For integration tests with a real database, use a separate test database:

```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Create a test engine and session factory
test_engine = create_async_engine("postgresql+asyncpg://test_user:test_pass@localhost/test_db")
TestAsyncSession = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture
async def setup_test_db():
    """Setup and teardown the test database."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(UnoModel.metadata.create_all)
    
    # Run the test
    yield
    
    # Drop tables
    async with test_engine.begin() as conn:
        await conn.run_sync(UnoModel.metadata.drop_all)

@pytest.mark.asyncio
async def test_crud_operations(setup_test_db):
    """Test CRUD operations with a real database."""
    # Patch the session to use our test session
    with patch("uno.db.db.async_session", TestAsyncSession):
        # Create a customer
        customer_data = {
            "name": "Test Customer",
            "email": "test@example.com"
        }
        
        customer = CustomerModel(**customer_data)
        result, created = await customer_db.create(schema=customer)
        
        # Get the customer
        retrieved = await customer_db.get(id=result.id)
        assert retrieved.name == customer_data["name"]
        
        # Update the customer
        retrieved.name = "Updated Name"
        updated = await customer_db.update(to_db_model=retrieved)
        assert updated.name == "Updated Name"
        
        # Delete the customer
        await customer_db.delete(updated)
        
        # Verify it's gone
        with pytest.raises(NotFoundException):
            await customer_db.get(id=result.id)
```

## Best Practices

1. **Use Transactions**: Wrap related operations in transactions to ensure data consistency.

2. **Handle Exceptions**: Catch and handle specific exceptions for better error reporting.

3. **Use Pagination**: Always paginate large result sets to avoid performance issues.

4. **Validate Input**: Validate input data before sending it to the database.

5. **Secure Queries**: Use parameterized queries and avoid string concatenation to prevent SQL injection.

6. **Optimize Performance**: Monitor query performance and optimize as needed.

7. **Implement Soft Delete**: Use soft delete instead of hard delete for important data.

8. **Test Thoroughly**: Test all database operations, including edge cases and error conditions.

9. **Use Dependency Injection**: Inject the database factory for better testability.

10. **Follow SQLAlchemy Best Practices**: Leverage SQLAlchemy's features and follow its recommended patterns.
