# Database Framework Overview

The Uno framework provides a powerful database abstraction layer that leverages PostgreSQL's advanced features while maintaining clean separation of concerns.

## Introduction

The database framework is designed to:

1. Maximize PostgreSQL capabilities (functions, triggers, row-level security)
2. Support both synchronous and asynchronous access patterns
3. Provide optimized connection pooling
4. Enable transaction management with the Unit of Work pattern
5. Support complex queries and data access patterns
6. Integrate with the domain entity framework

## Key Components

### UnoDB

`UnoDB` is the core database abstraction class that provides:

```python
from uno.infrastructure.database import UnoDB
from sqlalchemy.ext.asyncio import AsyncSession

# Create a database instance
db = UnoDB(connection_string="postgresql+asyncpg://user:pass@localhost/dbname")

# Get a session
async with db.session() as session:
    # Execute raw SQL
    result = await session.execute("SELECT * FROM users WHERE id = :id", {"id": 123})
    user = result.fetchone()
    
    # Use SQLAlchemy
    from myapp.domain.models import UserModel
    user = await session.get(UserModel, 123)
```

Key features:
- Session management
- Transaction handling
- Connection pooling
- Metrics and monitoring
- Both async and sync access

### Database Engine Configuration

The database framework supports multiple engine configurations:

```python
from uno.infrastructure.database.engine import create_async_engine, create_sync_engine

# Create an async engine with custom pool settings
async_engine = create_async_engine(
    connection_string="postgresql+asyncpg://user:pass@localhost/dbname",
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    echo=True
)

# Create a sync engine
sync_engine = create_sync_engine(
    connection_string="postgresql+psycopg2://user:pass@localhost/dbname"
)
```

### Session Management

The framework provides utilities for session management:

```python
from uno.infrastructure.database.session import get_session, get_async_session
from uno.core.di import configure_container

# Configure dependency injection
configure_container()

# Get a session from the container
async def get_users():
    async with get_async_session() as session:
        result = await session.execute("SELECT * FROM users")
        return result.fetchall()
```

### Transaction Management

The framework integrates with the Unit of Work pattern for transaction management:

```python
from uno.core.uow import SqlAlchemyUnitOfWork
from uno.infrastructure.database.transaction import transaction

# Using the transaction context manager
async with transaction() as session:
    # Operations are wrapped in a transaction
    await session.execute("INSERT INTO users (name) VALUES (:name)", {"name": "John"})
    await session.execute("UPDATE users SET name = :name WHERE id = :id", {"name": "Jane", "id": 1})
    # Transaction is committed if no exception occurs
```

### Query Optimization

The database framework includes query optimization features:

```python
from uno.infrastructure.database.query_optimizer import QueryOptimizer
from uno.infrastructure.database.pg_optimizer_strategies import IndexScanStrategy

# Create an optimizer with strategies
optimizer = QueryOptimizer([
    IndexScanStrategy(),
    JoinOptimizationStrategy()
])

# Optimize a query
original_query = "SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE users.name = 'John'"
optimized_query = optimizer.optimize(original_query)
```

### PostgreSQL Features

The framework leverages PostgreSQL's advanced features:

```python
from uno.infrastructure.database.postgresql import PostgresExtensions

# Check for and initialize extensions
async def init_extensions():
    extensions = PostgresExtensions(session)
    
    # Check if vector extension is available
    has_vector = await extensions.has_extension("vector")
    
    # Install extensions if needed
    if not has_vector:
        await extensions.create_extension("vector")
```

## Integration with Apache AGE

The framework supports Apache AGE for graph database capabilities:

```python
from uno.infrastructure.database.age import AgeManager

# Initialize AGE
age_manager = AgeManager(session)
await age_manager.initialize_graph("my_graph")

# Run a Cypher query
result = await age_manager.execute_cypher(
    "MATCH (u:User)-[:ORDERED]->(p:Product) WHERE u.name = $name RETURN p",
    {"name": "John"}
)
```

## SQL Emitter

The `SQLEmitter` class enables programmatic SQL generation:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate a function definition
function_sql = emitter.create_function(
    name="get_user_by_name",
    parameters=[("name_param", "TEXT")],
    return_type="TABLE(id INT, name TEXT, email TEXT)",
    body="""
    RETURN QUERY
    SELECT id, name, email FROM users WHERE name = name_param;
    """
)

# Execute the generated SQL
await session.execute(function_sql)
```

## Relationship Loading

The framework includes utilities for efficient relationship loading:

```python
from uno.infrastructure.database.relationship_loader import RelationshipLoader

# Create a loader for User-Order relationships
loader = RelationshipLoader(
    parent_model=UserModel,
    child_model=OrderModel,
    parent_key="id",
    child_key="user_id",
    relationship_name="orders"
)

# Efficiently load relationships
users = await session.execute(select(UserModel)).scalars().all()
await loader.load_relationships(users, session)

# Access loaded relationships
for user in users:
    for order in user.orders:
        print(f"User {user.name} ordered {order.product_name}")
```

## Connection Pool Management

The framework provides enhanced connection pool management:

```python
from uno.infrastructure.database.engine import PooledAsyncEngine

# Create a pooled engine with enhanced metrics
engine = PooledAsyncEngine(
    connection_string="postgresql+asyncpg://user:pass@localhost/dbname",
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    metrics_enabled=True
)

# Get connection pool stats
stats = await engine.get_pool_stats()
print(f"Pool size: {stats.size}, Idle: {stats.idle}, Used: {stats.used}")
```

## Schema Management

The framework includes utilities for schema management:

```python
from uno.infrastructure.database.schema_manager import SchemaManager

# Create a schema manager
schema_manager = SchemaManager(engine)

# Create a new schema
await schema_manager.create_schema("analytics")

# Create tables in specific schemas
await schema_manager.create_tables(models, schema="analytics")
```

## Distributed Queries

The framework supports distributed query execution:

```python
from uno.infrastructure.database.distributed_query import DistributedQuery

# Create a distributed query
query = DistributedQuery(
    query="SELECT * FROM users WHERE created_at > :date",
    parameters={"date": "2023-01-01"},
    shard_key="tenant_id",
    shard_values=[1, 2, 3, 4]
)

# Execute the query across shards
results = await query.execute(shard_manager)
```

## Best Practices

### Connection Management

```python
# DON'T: Create new connections for each operation
async def bad_example():
    db = UnoDB(connection_string)
    async with db.session() as session1:
        # Operation 1
        pass
    
    async with db.session() as session2:
        # Operation 2
        pass

# DO: Create a single UnoDB instance and reuse it
db = UnoDB(connection_string)

async def good_example():
    async with db.session() as session:
        # Operation 1
        # Operation 2
```

### Transaction Management

```python
# DON'T: Manage transactions manually
async def bad_example():
    async with db.session() as session:
        transaction = await session.begin()
        try:
            await session.execute("INSERT INTO users (name) VALUES (:name)", {"name": "John"})
            await session.execute("UPDATE users SET name = :name WHERE id = :id", {"name": "Jane", "id": 1})
            await transaction.commit()
        except Exception:
            await transaction.rollback()
            raise

# DO: Use the Unit of Work pattern
async def good_example():
    async with unit_of_work:
        user_repo = unit_of_work.get_repository(UserRepository)
        user = User.create("John")
        await user_repo.add(user)
        # Transaction is handled automatically
```

### Query Optimization

```python
# DON'T: Use expensive queries without optimization
async def bad_example():
    async with db.session() as session:
        result = await session.execute("""
            SELECT * FROM users 
            JOIN orders ON users.id = orders.user_id
            JOIN order_items ON orders.id = order_items.order_id
            WHERE users.name LIKE '%John%'
        """)

# DO: Use optimized queries and fetch only what you need
async def good_example():
    async with db.session() as session:
        result = await session.execute("""
            SELECT u.id, u.name, o.id, o.total
            FROM users u
            JOIN orders o ON u.id = o.user_id
            WHERE u.name LIKE 'John%'
            LIMIT 100
        """)
```

## Integration with Domain Entities

The database framework integrates with the domain entity framework:

```python
from uno.domain.entity import EntityRepository
from uno.infrastructure.database.repository import SQLAlchemyRepository

# Create a repository that connects the domain entity to the database
class UserRepository(SQLAlchemyRepository[User, UUID, UserModel]):
    """Repository for User entity."""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, user_mapper)
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email."""
        query = self._build_query().filter(UserModel.email == email)
        result = await self._execute_query(query)
        models = result.scalars().all()
        
        if not models:
            return None
            
        return self._mapper.to_entity(models[0])
```

## Further Reading

- [Database Engine](engine.md): Configuration and optimization
- [Transaction Management](transaction_management.md): Working with transactions
- [Connection Pooling](enhanced_connection_pool.md): Pool configuration and management
- [Query Optimization](query_optimizer.md): Strategies for optimizing queries
- [PostgreSQL Features](postgresql_features.md): Leveraging PostgreSQL capabilities