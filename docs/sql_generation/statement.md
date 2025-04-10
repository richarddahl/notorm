# SQL Statement

The `SQLStatement` class in uno represents a SQL statement with parameters. It provides a clean interface for executing SQL statements with proper parameter handling.

## Overview

The `SQLStatement` class encapsulates:

- SQL text
- Parameters
- Statement execution
- Result handling

## Basic Usage

```python
from uno.sql.statement import SQLStatement

# Create a SQL statement
statement = SQLStatement(
    text="SELECT * FROM customer WHERE id = :id",
    params={"id": "abc123"}
)

# Execute the statement
result = await statement.execute(connection)

# Process the result
for row in result:
    print(row)
```

## Creating Statements

### Simple Statements

```python
from uno.sql.statement import SQLStatement

# Select statement
select_statement = SQLStatement(
    text="SELECT id, name, email FROM customer WHERE status = :status",
    params={"status": "active"}
)

# Insert statement
insert_statement = SQLStatement(
    text="INSERT INTO customer (id, name, email) VALUES (:id, :name, :email)",
    params={"id": "abc123", "name": "John Doe", "email": "john@example.com"}
)

# Update statement
update_statement = SQLStatement(
    text="UPDATE customer SET name = :name WHERE id = :id",
    params={"id": "abc123", "name": "John Smith"}
)

# Delete statement
delete_statement = SQLStatement(
    text="DELETE FROM customer WHERE id = :id",
    params={"id": "abc123"}
)
```

### Complex Statements

```python
from uno.sql.statement import SQLStatement

# Join with parameters
join_statement = SQLStatement(
    text="""
    SELECT c.id, c.name, o.id as order_id, o.total
    FROM customer c
    JOIN order o ON c.id = o.customer_id
    WHERE c.status = :status
    AND o.created_at > :date
    ORDER BY o.created_at DESC
    LIMIT :limit
    OFFSET :offset
    """,
    params={
        "status": "active",
        "date": "2023-01-01",
        "limit": 10,
        "offset": 0
    }
)

# With subquery
subquery_statement = SQLStatement(
    text="""
    SELECT c.id, c.name, (
        SELECT COUNT(*)
        FROM order o
        WHERE o.customer_id = c.id
    ) as order_count
    FROM customer c
    WHERE c.status = :status
    """,
    params={"status": "active"}
)
```

## Executing Statements

### With Connection Object

```python
from uno.sql.statement import SQLStatement
from uno.database.engine import sync_connection, async_connection

# Synchronous execution
with sync_connection(db_role="app_user", db_name="my_database") as conn:
    statement = SQLStatement(
        text="SELECT * FROM customer WHERE id = :id",
        params={"id": "abc123"}
    )
    result = statement.execute_sync(conn)
    
    # Process the result
    for row in result:
        print(row)

# Asynchronous execution
async with async_connection(db_role="app_user", db_name="my_database") as conn:
    statement = SQLStatement(
        text="SELECT * FROM customer WHERE id = :id",
        params={"id": "abc123"}
    )
    result = await statement.execute(conn)
    
    # Process the result
    async for row in result:
        print(row)
```

### With Custom Executor

```python
from uno.sql.statement import SQLStatement

# Define a custom executor function
async def custom_executor(conn, sql_text, params):
    """Custom executor for specific result handling."""
    result = await conn.execute(sql_text, params)
    return await result.mappings().all()

# Create and execute the statement with the custom executor
statement = SQLStatement(
    text="SELECT * FROM customer WHERE status = :status",
    params={"status": "active"}
)

async with async_connection(db_role="app_user", db_name="my_database") as conn:
    result = await statement.execute(conn, executor=custom_executor)
```

## Batch Operations

You can execute multiple statements in a transaction:

```python
from uno.sql.statement import SQLStatement
from uno.database.engine import async_connection
from sqlalchemy.ext.asyncio import AsyncSession

async def create_customer_with_orders(customer_data, orders_data):
    """Create a customer and their orders in a transaction."""
    async with AsyncSession() as session:
        async with session.begin():
            # Create customer
            customer_statement = SQLStatement(
                text="INSERT INTO customer (id, name, email) VALUES (:id, :name, :email) RETURNING id",
                params=customer_data
            )
            result = await customer_statement.execute(session.connection())
            customer_id = result.scalar_one()
            
            # Create orders
            for order_data in orders_data:
                order_data["customer_id"] = customer_id
                order_statement = SQLStatement(
                    text="""
                    INSERT INTO order (id, customer_id, product_id, quantity, price)
                    VALUES (:id, :customer_id, :product_id, :quantity, :price)
                    """,
                    params=order_data
                )
                await order_statement.execute(session.connection())
            
            # The transaction will be committed if no exceptions are raised
            return customer_id
```

## Statement Composition

You can compose statements from parts:

```python
from uno.sql.statement import SQLStatement

def build_search_query(filters):
    """Build a search query dynamically."""
    base_sql = "SELECT id, name, email FROM customer WHERE 1=1"
    params = {}
    
    # Add filters dynamically
    if "name" in filters:
        base_sql += " AND name ILIKE :name"
        params["name"] = f"%{filters['name']}%"
    
    if "email" in filters:
        base_sql += " AND email ILIKE :email"
        params["email"] = f"%{filters['email']}%"
    
    if "status" in filters:
        base_sql += " AND status = :status"
        params["status"] = filters["status"]
    
    # Add pagination
    base_sql += " LIMIT :limit OFFSET :offset"
    params["limit"] = filters.get("limit", 10)
    params["offset"] = filters.get("offset", 0)
    
    # Create the statement
    return SQLStatement(text=base_sql, params=params)
```

## Best Practices

1. **Use Parameters**: Always use parameterized statements to prevent SQL injection.

2. **Handle Errors**: Implement proper error handling for SQL execution errors.

3. **Use Transactions**: Wrap related statements in transactions to ensure data consistency.

4. **Close Resources**: Ensure connections and other resources are properly closed.

5. **Validate Input**: Validate input data before creating SQL statements.

6. **Document SQL**: Add comments to explain complex SQL statements.

7. **Test Thoroughly**: Test SQL statements with various inputs, including edge cases.

8. **Optimize Queries**: Monitor query performance and optimize as needed.

9. **Use Type Annotations**: Provide proper type annotations for better IDE support.

10. **Separate Concerns**: Keep SQL generation separate from business logic.