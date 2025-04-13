# Enhanced Connection Pool

The Enhanced Connection Pool module provides a high-performance, feature-rich database connection pooling system for the Uno framework.

## Features

- **Dynamic pool sizing**: Automatically scales the connection pool based on actual load
- **Intelligent connection allocation**: Optimizes connection reuse and distribution
- **Comprehensive health checking**: Monitors connection health and circuit breaking
- **Detailed metrics collection**: Tracks performance, utilization, and health statistics
- **Multiple pool strategies**: Different connection strategies for different workloads
- **Seamless integration** with SQLAlchemy AsyncEngine and AsyncSession

## Architecture

The Enhanced Connection Pool system consists of the following main components:

1. **EnhancedConnectionPool**: The core connection pool implementation
2. **EnhancedAsyncEnginePool**: A specialized pool for SQLAlchemy AsyncEngine instances
3. **EnhancedAsyncConnectionManager**: A manager for multiple connection pools
4. **EnhancedPooledSessionFactory**: A factory for creating database sessions using the enhanced pool
5. **EnhancedPooledSessionContext**: A context manager for database sessions

## Usage Examples

### Basic Connection Usage

Using the enhanced connection pool with default settings:

```python
from uno.database.enhanced_connection_pool import enhanced_async_connection

async def example_function():
    # Get a connection from the enhanced pool
    async with enhanced_async_connection() as connection:
        # Use the connection
        result = await connection.execute("SELECT * FROM users")
        users = await result.fetchall()
    
    # Connection is automatically returned to the pool when context exits
```

### Connection Pool Configuration

Configuring the connection pool for specific needs:

```python
from uno.database.enhanced_connection_pool import (
    ConnectionPoolConfig, 
    ConnectionPoolStrategy,
    get_connection_manager,
)

async def configure_pool_example():
    # Get the connection manager
    manager = get_connection_manager()
    
    # Create a custom configuration
    config = ConnectionPoolConfig(
        # Pool sizing
        initial_size=10,
        min_size=5,
        max_size=50,
        
        # Connection lifecycle
        idle_timeout=300.0,  # 5 minutes
        max_lifetime=1800.0,  # 30 minutes
        
        # Strategy
        strategy=ConnectionPoolStrategy.HIGH_THROUGHPUT,
        
        # Dynamic scaling
        dynamic_scaling_enabled=True,
        scale_up_threshold=0.7,  # Scale up when 70% utilized
        scale_down_threshold=0.3,  # Scale down when below 30% utilized
    )
    
    # Apply configuration to specific database role
    manager.configure_pool(role="analytics_role", config=config)
    
    # Apply configuration as default for all roles
    manager.configure_pool(config=config)
```

### Enhanced Session Usage

Using the enhanced session system with the connection pool:

```python
from uno.database.enhanced_pool_session import enhanced_pool_session

async def session_example():
    # Get a session using the enhanced pool
    async with enhanced_pool_session() as session:
        # Use the session for database operations
        result = await session.execute("SELECT * FROM users")
        users = await result.fetchall()
        
        # Perform ORM operations
        user = User(name="John", email="john@example.com")
        session.add(user)
        await session.commit()
```

### Session Pool Configuration

Configuring the session pool for specific needs:

```python
from uno.database.enhanced_pool_session import (
    SessionPoolConfig,
    enhanced_pool_session,
)

async def configure_session_pool_example():
    # Create session pool configuration
    session_config = SessionPoolConfig(
        # Session pool sizing
        min_sessions=10,
        max_sessions=100,
        
        # Session lifecycle
        idle_timeout=120.0,  # 2 minutes
        max_lifetime=1800.0,  # 30 minutes
    )
    
    # Use the configuration with a session
    async with enhanced_pool_session(
        session_pool_config=session_config,
        db_role="analytics_role",
        db_name="analytics",
    ) as session:
        # Use the session
        # ...
```

### Session Operation Group

Coordinating multiple database operations:

```python
from uno.database.enhanced_pool_session import EnhancedPooledSessionOperationGroup

async def operation_group_example():
    # Create an operation group
    async with EnhancedPooledSessionOperationGroup(name="user_operations") as group:
        # Create a session
        session = await group.create_session(db_role="user_role", db_name="users")
        
        # Run operations in parallel
        results = await group.run_parallel_operations(session, [
            lambda s: s.execute("SELECT * FROM users WHERE role = 'admin'"),
            lambda s: s.execute("SELECT * FROM users WHERE role = 'user'"),
            lambda s: s.execute("SELECT COUNT(*) FROM users"),
        ])
        
        # Run operations in a transaction
        await group.run_in_transaction(session, [
            lambda s: s.execute("INSERT INTO users (name, email) VALUES ('John', 'john@example.com')"),
            lambda s: s.execute("INSERT INTO user_roles (user_id, role) VALUES (?, 'admin')", [user_id]),
        ])
```

## Performance Metrics

The Enhanced Connection Pool provides comprehensive metrics for monitoring and optimization:

```python
from uno.database.enhanced_connection_pool import get_connection_manager

async def get_metrics_example():
    # Get the connection manager
    manager = get_connection_manager()
    
    # Get basic metrics for all pools
    metrics = manager.get_metrics()
    
    for pool_name, pool_metrics in metrics.items():
        print(f"Pool: {pool_name}")
        print(f"  Size: {pool_metrics['size']['current']}")
        print(f"  Active: {pool_metrics['size']['active']}")
        print(f"  Idle: {pool_metrics['size']['idle']}")
        print(f"  Current load: {pool_metrics['performance']['current_load']:.2f}")
        print(f"  Avg wait time: {pool_metrics['performance']['avg_wait_time']:.4f}s")
        
    # Get detailed metrics for a specific pool
    pool = await manager.get_engine_pool(config)
    detailed_metrics = pool.pool.get_detailed_metrics()
    
    # Access connection-specific metrics
    for conn_id, conn_metrics in detailed_metrics['connections'].items():
        print(f"Connection {conn_id}:")
        print(f"  Age: {conn_metrics['age']:.2f}s")
        print(f"  Idle time: {conn_metrics['idle_time']:.2f}s")
        print(f"  Usage count: {conn_metrics['usage_count']}")
        print(f"  Query count: {conn_metrics['query_count']}")
        print(f"  Avg query time: {conn_metrics['avg_query_time']:.4f}s")
```

## Integration with SQLAlchemy

The Enhanced Connection Pool system seamlessly integrates with SQLAlchemy's asynchronous ORM:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uno.database.enhanced_pool_session import enhanced_pool_session
from uno.models import User

async def sqlalchemy_example():
    async with enhanced_pool_session() as session:
        # Use SQLAlchemy ORM queries
        query = select(User).where(User.active == True)
        result = await session.execute(query)
        active_users = result.scalars().all()
        
        # Perform ORM operations
        new_user = User(name="Jane", email="jane@example.com")
        session.add(new_user)
        await session.commit()
```

## Best Practices

1. **Use context managers**: Always use the connection and session context managers to ensure proper resource cleanup
2. **Configure pool sizing**: Adjust pool size based on your workload characteristics
3. **Choose appropriate strategies**: Use different pool strategies for different workloads
4. **Monitor metrics**: Regularly check pool metrics to identify performance issues
5. **Use operation groups**: Coordinate related operations with the session operation group
6. **Set appropriate timeouts**: Configure timeouts based on expected operation durations

## Advanced Configuration

The Enhanced Connection Pool system offers extensive configuration options for advanced use cases. See the `ConnectionPoolConfig` and `SessionPoolConfig` classes for all available options.

## FAQ

### When should I use the enhanced pool vs. standard SQLAlchemy pooling?

The enhanced connection pool provides more features and better performance than SQLAlchemy's built-in pooling, especially for high-traffic applications. Use it when you need:

- Dynamic pool sizing based on load
- Detailed performance metrics
- Health checking and circuit breaking
- Different pool strategies for different workloads

### How does dynamic scaling work?

Dynamic scaling adjusts the pool size based on current load:

1. If load exceeds the `scale_up_threshold`, the pool adds new connections
2. If load falls below the `scale_down_threshold`, the pool removes idle connections
3. The scaling has a cool-down period to prevent rapid fluctuations

### How do connection strategies work?

Different strategies optimize for different workloads:

- **BALANCED**: Default balanced approach suitable for most applications
- **HIGH_THROUGHPUT**: Optimized for maximum query throughput, maintains more connections
- **LOW_LATENCY**: Optimized for minimal latency, resets connections more frequently
- **DYNAMIC**: Automatically adjusts based on workload patterns

### How can I monitor pool performance?

The pool provides detailed metrics through:
- `get_metrics()`: Basic metrics for all pools
- `get_detailed_metrics()`: Detailed metrics including per-connection statistics

Consider exporting these metrics to your monitoring system for observability.

### How does health checking work?

The pool periodically checks connection health by:
1. Creating a test connection
2. Validating it with a simple query
3. If validation fails, triggering the circuit breaker to temporarily disable connections
4. Automatically recovering when the system is healthy again