# PostgreSQL Features in UNO

The UNO framework is designed to leverage PostgreSQL's powerful features to deliver high performance, security, and flexibility. This guide explains how UNO integrates with PostgreSQL and how to take advantage of advanced database features.

## Overview

PostgreSQL is a powerful, open-source object-relational database system with over 30 years of active development. UNO is built to harness PostgreSQL's unique capabilities, including:

1. **Custom Functions and Procedures**: Moving business logic to the database for better performance
2. **Triggers**: Automatically maintaining data integrity and consistency
3. **Row-Level Security (RLS)**: Implementing fine-grained access control
4. **JSON and JSONB**: Native support for JSON data
5. **Full-Text Search**: Built-in text search capabilities
6. **Extensions**: Expanding functionality with extensions like pgvector and Apache AGE
7. **Materialized Views**: Caching complex query results
8. **Partitioning**: Efficiently managing large tables

## SQL Emitter

UNO provides the `SQLEmitter` utility for programmatically creating PostgreSQL objects:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate a function definition
function_sql = emitter.create_function(
    name="get_filtered_users",
    parameters=[("min_age", "INT"), ("status", "TEXT")],
    return_type="TABLE(id UUID, name TEXT, email TEXT, age INT)",
    body="""
    RETURN QUERY
    SELECT id, name, email, age
    FROM users
    WHERE age >= min_age AND status = status;
    """
)

# Execute the generated SQL to create the function
async with db.session() as session:
    await session.execute(function_sql)
```

The SQL Emitter can generate:
- Functions and procedures
- Custom types
- Triggers and trigger functions
- Indices
- Views and materialized views

## Custom Functions

UNO makes it easy to create and use custom PostgreSQL functions:

```python
from uno.infrastructure.sql import SQLEmitter
from uno.infrastructure.database import UnoDB

# Create a database instance
db = UnoDB(connection_string="postgresql+asyncpg://user:pass@localhost/dbname")

# Create SQL emitter
emitter = SQLEmitter()

# Generate a function for soft-delete
soft_delete_function = emitter.create_function(
    name="soft_delete_record",
    parameters=[
        ("table_name", "TEXT"),
        ("record_id", "UUID"),
        ("deleted_by", "UUID")
    ],
    return_type="BOOLEAN",
    language="plpgsql",
    body="""
    DECLARE
        query TEXT;
    BEGIN
        query := format('UPDATE %I SET deleted_at = NOW(), 
                         deleted_by = %L, is_active = FALSE 
                         WHERE id = %L RETURNING id', 
                         table_name, deleted_by, record_id);
        
        EXECUTE query;
        RETURN FOUND;
    END;
    """
)

# Create the function in the database
async def create_soft_delete_function():
    async with db.session() as session:
        await session.execute(soft_delete_function)

# Use the function
async def soft_delete_user(user_id: UUID, deleted_by: UUID):
    async with db.session() as session:
        result = await session.execute(
            "SELECT soft_delete_record('users', :user_id, :deleted_by)",
            {"user_id": user_id, "deleted_by": deleted_by}
        )
        return result.scalar()
```

### Function Helpers

UNO provides helpers for common types of functions:

```python
# Create a validation function
validation_function = emitter.create_validation_function(
    name="validate_email",
    parameters=[("email", "TEXT")],
    body="""
    BEGIN
        IF email !~ '^[A-Za-z0-9._%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$' THEN
            RETURN FALSE;
        END IF;
        RETURN TRUE;
    END;
    """
)

# Create a computed column function
computed_column_function = emitter.create_computed_column_function(
    name="calculate_order_total",
    table_name="orders",
    parameters=[("order_row", "orders")],
    return_type="NUMERIC",
    body="""
    SELECT SUM(price * quantity)
    FROM order_items
    WHERE order_id = order_row.id;
    """
)
```

## Triggers

UNO makes it easy to create triggers that automatically respond to database changes:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an audit trigger function
audit_trigger_function = emitter.create_function(
    name="audit_trigger_func",
    parameters=[],
    return_type="TRIGGER",
    language="plpgsql",
    body="""
    DECLARE
        audit_row jsonb;
    BEGIN
        IF (TG_OP = 'DELETE') THEN
            audit_row = to_jsonb(OLD);
        ELSE
            audit_row = to_jsonb(NEW);
        END IF;
        
        INSERT INTO audit_logs(
            table_name, 
            action, 
            row_data, 
            changed_by, 
            changed_at
        ) VALUES (
            TG_TABLE_NAME,
            TG_OP,
            audit_row,
            current_setting('app.current_user_id', TRUE),
            now()
        );
        
        RETURN NULL;
    END;
    """
)

# Create the trigger
audit_trigger = emitter.create_trigger(
    name="users_audit_trigger",
    table_name="users",
    timing="AFTER",
    events=["INSERT", "UPDATE", "DELETE"],
    function_name="audit_trigger_func"
)

# Apply both to the database
async def setup_audit_trigger():
    async with db.session() as session:
        await session.execute(audit_trigger_function)
        await session.execute(audit_trigger)
```

### Common Trigger Patterns

UNO provides templates for common trigger patterns:

```python
# Create a timestamp trigger (updated_at)
timestamp_trigger = emitter.create_timestamp_trigger(
    table_name="users",
    column_name="updated_at"
)

# Create a versioning trigger
versioning_trigger = emitter.create_versioning_trigger(
    table_name="documents",
    version_column="version"
)

# Create a search vector update trigger
search_trigger = emitter.create_search_vector_trigger(
    table_name="articles",
    search_vector_column="search_vector",
    columns=["title", "body", "tags"]
)
```

## Row-Level Security (RLS)

UNO makes it easy to implement row-level security policies:

```python
from uno.infrastructure.sql import SQLEmitter
from uno.infrastructure.database.postgresql import RLSPolicy

# Create an emitter
emitter = SQLEmitter()

# Enable RLS on a table
enable_rls = emitter.enable_row_level_security("users")

# Create RLS policies
user_policy = RLSPolicy(
    name="users_isolation_policy",
    table_name="users",
    using_expr="(id = current_setting('app.current_user_id')::uuid OR "
               "current_setting('app.is_admin')::boolean)",
    check_expr=None,
    command="ALL",
    roles=None
)

admin_policy = RLSPolicy(
    name="users_admin_policy",
    table_name="users",
    using_expr="current_setting('app.is_admin')::boolean",
    check_expr=None,
    command="ALL",
    roles=["admin_role"]
)

# Generate and execute SQL
async def setup_rls():
    async with db.session() as session:
        # Enable RLS
        await session.execute(enable_rls)
        
        # Create policies
        await session.execute(emitter.create_policy(user_policy))
        await session.execute(emitter.create_policy(admin_policy))
```

### Setting RLS Context Variables

UNO provides utilities for setting PostgreSQL session variables needed for RLS:

```python
from uno.infrastructure.database.postgresql import SessionContext

async def set_user_context(session, user_id, is_admin=False):
    context = SessionContext(session)
    await context.set_variable("app.current_user_id", str(user_id))
    await context.set_variable("app.is_admin", str(is_admin).lower())

# Use in request handlers
async def handle_request(request, session):
    user = get_current_user(request)
    await set_user_context(session, user.id, user.is_admin)
    
    # Now RLS will filter query results based on the user's context
    result = await session.execute("SELECT * FROM users")
    users = result.fetchall()
    
    # Users will only see records they're allowed to see based on RLS policies
```

## JSON and JSONB Support

UNO provides utilities for working with PostgreSQL's JSON and JSONB data types:

```python
from uno.infrastructure.database.postgresql import JSONField, JSONBField
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    name = Column(String)
    preferences = Column(JSONBField)  # JSONB type
    profile = Column(JSONField)       # JSON type

# Query JSON/JSONB data
async def find_users_by_preference(key, value):
    async with db.session() as session:
        result = await session.execute(
            "SELECT * FROM users WHERE preferences->:key = :value::jsonb",
            {"key": key, "value": json.dumps(value)}
        )
        return result.fetchall()

# Use JSON operators
async def get_users_with_location():
    async with db.session() as session:
        result = await session.execute(
            "SELECT id, name, profile->'location' as location FROM users WHERE profile ? 'location'"
        )
        return result.fetchall()
```

### JSON/JSONB Index Creation

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate indexes for JSONB fields
jsonb_index = emitter.create_index(
    name="users_preferences_gin_idx",
    table_name="users",
    columns=["preferences"],
    method="GIN"  # GIN index for JSONB
)

jsonb_path_index = emitter.create_index(
    name="users_preferences_city_idx",
    table_name="users",
    expression="(preferences->>'city')"
)

# Create the indexes
async def create_jsonb_indexes():
    async with db.session() as session:
        await session.execute(jsonb_index)
        await session.execute(jsonb_path_index)
```

## Full-Text Search

UNO integrates with PostgreSQL's powerful full-text search capabilities:

```python
from uno.infrastructure.sql import SQLEmitter
from uno.infrastructure.database.postgresql import TSVectorField

# Create a model with full-text search
class Article(Base):
    __tablename__ = "articles"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    body = Column(String)
    search_vector = Column(TSVectorField)  # tsvector type

# Create a search index and trigger
async def setup_full_text_search():
    emitter = SQLEmitter()
    
    # Create search vector function
    search_function = emitter.create_function(
        name="articles_search_vector_update",
        parameters=[],
        return_type="TRIGGER",
        language="plpgsql",
        body="""
        BEGIN
            NEW.search_vector = setweight(to_tsvector('english', coalesce(NEW.title, '')), 'A') || 
                               setweight(to_tsvector('english', coalesce(NEW.body, '')), 'B');
            RETURN NEW;
        END;
        """
    )
    
    # Create trigger
    search_trigger = emitter.create_trigger(
        name="articles_search_vector_trigger",
        table_name="articles",
        timing="BEFORE",
        events=["INSERT", "UPDATE"],
        function_name="articles_search_vector_update"
    )
    
    # Create GIN index
    search_index = emitter.create_index(
        name="articles_search_vector_idx",
        table_name="articles",
        columns=["search_vector"],
        method="GIN"
    )
    
    # Apply to database
    async with db.session() as session:
        await session.execute(search_function)
        await session.execute(search_trigger)
        await session.execute(search_index)

# Perform full-text search
async def search_articles(query):
    async with db.session() as session:
        result = await session.execute(
            """
            SELECT id, title, ts_headline('english', body, query) as excerpt, 
                   ts_rank(search_vector, query) as rank
            FROM articles, to_tsquery('english', :query) query
            WHERE search_vector @@ query
            ORDER BY rank DESC
            LIMIT 10
            """,
            {"query": " & ".join(query.split())}  # Convert "word word" to "word & word"
        )
        return result.fetchall()
```

## Extensions Management

UNO includes utilities for managing PostgreSQL extensions:

```python
from uno.infrastructure.database.postgresql import PostgresExtensions

async def setup_extensions(session):
    extensions = PostgresExtensions(session)
    
    # Check if extensions exist
    has_vector = await extensions.has_extension("vector")
    has_age = await extensions.has_extension("age")
    
    # Create extensions if needed
    if not has_vector:
        await extensions.create_extension("vector")
    
    if not has_age:
        await extensions.create_extension("age")
    
    # List all available extensions
    available_extensions = await extensions.list_available_extensions()
    print(f"Available extensions: {available_extensions}")
    
    # List installed extensions
    installed_extensions = await extensions.list_installed_extensions()
    print(f"Installed extensions: {installed_extensions}")
```

### pgvector Integration

UNO provides specialized support for pgvector:

```python
from uno.infrastructure.database.postgresql import VectorField
from uno.ai.vector_storage import PgVectorStorage
from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# Model with vector field
class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True)
    content = Column(String)
    embedding = Column(VectorField(dimensions=1536))  # OpenAI embedding size

# Setup pgvector
async def setup_pgvector(session):
    # Check for vector extension
    extensions = PostgresExtensions(session)
    if not await extensions.has_extension("vector"):
        await extensions.create_extension("vector")
    
    # Create tables with vector columns
    await Base.metadata.create_all(db.engine)
    
    # Create vector index
    await session.execute("""
        CREATE INDEX IF NOT EXISTS documents_embedding_idx 
        ON documents USING ivfflat (embedding vector_cosine_ops) 
        WITH (lists = 100)
    """)

# Use pgvector for semantic search
async def semantic_search(query_embedding, limit=10):
    async with db.session() as session:
        # Convert embedding to PostgreSQL array format
        pg_vector = ",".join(map(str, query_embedding))
        
        result = await session.execute(
            f"""
            SELECT id, content, 1 - (embedding <=> '{{{pg_vector}}}') as similarity
            FROM documents
            ORDER BY embedding <=> '{{{pg_vector}}}'
            LIMIT :limit
            """,
            {"limit": limit}
        )
        return result.fetchall()
```

## Apache AGE Integration

UNO integrates with Apache AGE for graph database capabilities:

```python
from uno.infrastructure.database.postgresql import AgeGraph

# Initialize Apache AGE
async def setup_age_graph(session):
    # Create a graph
    graph = AgeGraph(session, "knowledge_graph")
    
    # Initialize the graph (create if not exists)
    await graph.initialize()
    
    # Create vertex labels
    await graph.execute_cypher("""
        CREATE VLABEL IF NOT EXISTS Person
    """)
    
    await graph.execute_cypher("""
        CREATE VLABEL IF NOT EXISTS Product
    """)
    
    # Create edge labels
    await graph.execute_cypher("""
        CREATE ELABEL IF NOT EXISTS PURCHASED
    """)

# Create vertices and edges
async def add_person_and_purchases(session, person_data, purchases):
    graph = AgeGraph(session, "knowledge_graph")
    
    # Create person vertex
    person_id = person_data.pop("id")
    cypher = f"""
        CREATE (p:Person {{id: '{person_id}'}})
        SET p += $properties
        RETURN p
    """
    result = await graph.execute_cypher(cypher, {"properties": person_data})
    
    # Create purchase relationships
    for product_id in purchases:
        cypher = f"""
            MATCH (p:Person {{id: '{person_id}'}}), (pr:Product {{id: '{product_id}'}})
            CREATE (p)-[r:PURCHASED {{date: datetime()}}]->(pr)
            RETURN r
        """
        await graph.execute_cypher(cypher)

# Query the graph
async def find_related_products(session, product_id):
    graph = AgeGraph(session, "knowledge_graph")
    
    # Find people who purchased this product
    cypher = f"""
        MATCH (p:Person)-[:PURCHASED]->(pr:Product {{id: '{product_id}'}})
        MATCH (p)-[:PURCHASED]->(other:Product)
        WHERE other.id <> '{product_id}'
        RETURN other.id, other.name, count(*) as frequency
        ORDER BY frequency DESC
        LIMIT 5
    """
    
    result = await graph.execute_cypher(cypher)
    return result
```

## Materialized Views

UNO supports PostgreSQL materialized views for caching complex query results:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate a materialized view
materialized_view = emitter.create_materialized_view(
    name="product_sales_summary",
    query="""
    SELECT 
        p.id as product_id,
        p.name as product_name,
        p.category,
        COUNT(o.id) as orders_count,
        SUM(oi.quantity) as total_units_sold,
        SUM(oi.quantity * oi.unit_price) as total_revenue
    FROM products p
    JOIN order_items oi ON p.id = oi.product_id
    JOIN orders o ON oi.order_id = o.id
    WHERE o.status = 'completed'
    GROUP BY p.id, p.name, p.category
    """
)

# Create an index on the materialized view
view_index = emitter.create_index(
    name="product_sales_category_idx",
    table_name="product_sales_summary",
    columns=["category"]
)

# Apply to database
async def create_sales_summary_view():
    async with db.session() as session:
        await session.execute(materialized_view)
        await session.execute(view_index)

# Refresh the materialized view
async def refresh_sales_summary():
    async with db.session() as session:
        await session.execute("REFRESH MATERIALIZED VIEW product_sales_summary")

# Query the materialized view
async def get_category_sales(category):
    async with db.session() as session:
        result = await session.execute(
            "SELECT * FROM product_sales_summary WHERE category = :category",
            {"category": category}
        )
        return result.fetchall()
```

## Table Partitioning

UNO supports PostgreSQL table partitioning for managing large tables:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate a partitioned table
partitioned_table = emitter.create_partitioned_table(
    name="user_activity_logs",
    columns=[
        ("id", "UUID", "PRIMARY KEY"),
        ("user_id", "UUID", "NOT NULL"),
        ("activity_type", "TEXT", "NOT NULL"),
        ("created_at", "TIMESTAMP WITH TIME ZONE", "NOT NULL")
    ],
    partition_key="RANGE (created_at)"
)

# Create partitions
partitions = [
    emitter.create_partition(
        parent_table="user_activity_logs",
        name="user_activity_logs_y2023m01",
        bounds=("'2023-01-01'", "'2023-02-01'")
    ),
    emitter.create_partition(
        parent_table="user_activity_logs",
        name="user_activity_logs_y2023m02",
        bounds=("'2023-02-01'", "'2023-03-01'")
    ),
    emitter.create_partition(
        parent_table="user_activity_logs",
        name="user_activity_logs_y2023m03",
        bounds=("'2023-03-01'", "'2023-04-01'")
    )
]

# Apply to database
async def setup_partitioned_table():
    async with db.session() as session:
        await session.execute(partitioned_table)
        for partition in partitions:
            await session.execute(partition)

# Create a function to automatically create new partitions
partition_function = emitter.create_function(
    name="create_activity_log_partition",
    parameters=[],
    return_type="TRIGGER",
    language="plpgsql",
    body="""
    DECLARE
        partition_date TEXT;
        partition_name TEXT;
        start_date DATE;
        end_date DATE;
    BEGIN
        start_date := date_trunc('month', NEW.created_at);
        end_date := start_date + interval '1 month';
        partition_date := to_char(start_date, 'y"y"YYYY"m"MM');
        partition_name := 'user_activity_logs_' || partition_date;
        
        -- Check if partition exists
        IF NOT EXISTS (
            SELECT 1 FROM pg_tables WHERE tablename = partition_name
        ) THEN
            EXECUTE format(
                'CREATE TABLE IF NOT EXISTS %I PARTITION OF user_activity_logs
                FOR VALUES FROM (%L) TO (%L)',
                partition_name, start_date, end_date
            );
            
            EXECUTE format(
                'CREATE INDEX IF NOT EXISTS %I ON %I (user_id, created_at)',
                partition_name || '_user_created_idx', partition_name
            );
        END IF;
        
        RETURN NEW;
    END;
    """
)

# Create trigger for automatic partition creation
partition_trigger = emitter.create_trigger(
    name="activity_logs_partition_trigger",
    table_name="user_activity_logs",
    timing="BEFORE",
    events=["INSERT"],
    function_name="create_activity_log_partition"
)

# Apply partition function and trigger
async def setup_dynamic_partitioning():
    async with db.session() as session:
        await session.execute(partition_function)
        await session.execute(partition_trigger)
```

## Best Practices

### Moving Logic to the Database

```python
# DON'T: Perform complex calculations in application code
async def calculate_order_total(order_id):
    async with db.session() as session:
        # Get order items
        result = await session.execute(
            "SELECT quantity, unit_price FROM order_items WHERE order_id = :order_id",
            {"order_id": order_id}
        )
        items = result.fetchall()
        
        # Calculate total in application code (inefficient)
        total = sum(item.quantity * item.unit_price for item in items)
        
        # Update order
        await session.execute(
            "UPDATE orders SET total = :total WHERE id = :order_id",
            {"total": total, "order_id": order_id}
        )

# DO: Use database functions for complex calculations
async def setup_order_total_function():
    emitter = SQLEmitter()
    
    # Create a function to calculate order total
    function_sql = emitter.create_function(
        name="calculate_order_total",
        parameters=[("order_id_param", "UUID")],
        return_type="NUMERIC",
        language="plpgsql",
        body="""
        DECLARE
            total NUMERIC;
        BEGIN
            SELECT SUM(quantity * unit_price)
            INTO total
            FROM order_items
            WHERE order_id = order_id_param;
            
            UPDATE orders SET total = total WHERE id = order_id_param;
            
            RETURN total;
        END;
        """
    )
    
    async with db.session() as session:
        await session.execute(function_sql)

# Use the function
async def update_order_total(order_id):
    async with db.session() as session:
        result = await session.execute(
            "SELECT calculate_order_total(:order_id)",
            {"order_id": order_id}
        )
        return result.scalar()
```

### Optimizing Large Datasets

```python
# DON'T: Fetch large datasets to process in application code
async def get_all_active_users():
    async with db.session() as session:
        result = await session.execute(
            "SELECT * FROM users WHERE is_active = TRUE"
        )
        users = result.fetchall()
        
        # Process in application (memory intensive)
        return [process_user(user) for user in users]

# DO: Process data in the database where possible
async def get_processed_active_users():
    async with db.session() as session:
        result = await session.execute("""
            SELECT 
                id, 
                name, 
                email,
                CASE 
                    WHEN last_login > NOW() - INTERVAL '7 days' THEN 'recent'
                    WHEN last_login > NOW() - INTERVAL '30 days' THEN 'active'
                    ELSE 'inactive'
                END AS activity_level,
                (SELECT COUNT(*) FROM orders WHERE user_id = users.id) AS orders_count
            FROM users
            WHERE is_active = TRUE
            ORDER BY last_login DESC
            LIMIT 1000
        """)
        return result.fetchall()
```

### Securing Data with RLS

```python
# DON'T: Filter data in application code
async def get_user_orders(user_id, is_admin):
    async with db.session() as session:
        if is_admin:
            # Admin can see all orders
            result = await session.execute("SELECT * FROM orders")
        else:
            # Regular users can only see their own orders
            result = await session.execute(
                "SELECT * FROM orders WHERE user_id = :user_id",
                {"user_id": user_id}
            )
        return result.fetchall()

# DO: Use Row-Level Security in the database
async def setup_orders_rls():
    emitter = SQLEmitter()
    
    # Enable RLS
    enable_rls = emitter.enable_row_level_security("orders")
    
    # Create policies
    user_policy = RLSPolicy(
        name="orders_user_policy",
        table_name="orders",
        using_expr="user_id = current_setting('app.current_user_id')::uuid",
        command="ALL"
    )
    
    admin_policy = RLSPolicy(
        name="orders_admin_policy",
        table_name="orders",
        using_expr="current_setting('app.is_admin')::boolean",
        command="ALL"
    )
    
    async with db.session() as session:
        await session.execute(enable_rls)
        await session.execute(emitter.create_policy(user_policy))
        await session.execute(emitter.create_policy(admin_policy))

# With RLS enabled, the query is simple
async def get_orders():
    # Set context variables first
    await set_user_context(session, user_id, is_admin)
    
    # Same query for everyone, RLS handles the filtering
    result = await session.execute("SELECT * FROM orders")
    return result.fetchall()
```

## PostgreSQL Monitoring

UNO provides tools for monitoring PostgreSQL performance:

```python
from uno.infrastructure.database.postgresql import PostgresMonitor

# Create a monitoring instance
monitor = PostgresMonitor(db.engine)

# Get database statistics
async def get_db_stats():
    stats = {}
    
    # Get table statistics
    stats["tables"] = await monitor.get_table_stats()
    
    # Get index statistics
    stats["indexes"] = await monitor.get_index_stats()
    
    # Get active connections
    stats["connections"] = await monitor.get_active_connections()
    
    # Get long-running queries
    stats["long_queries"] = await monitor.get_long_running_queries(min_duration_seconds=5)
    
    # Get lock information
    stats["locks"] = await monitor.get_locks()
    
    # Get database size
    stats["size"] = await monitor.get_database_size()
    
    return stats

# Monitor query performance
async def monitor_query_performance():
    # Enable query logging
    await monitor.enable_query_logging()
    
    # Run queries...
    
    # Get slow queries
    slow_queries = await monitor.get_slow_queries(min_duration_ms=100)
    print(f"Slow queries: {slow_queries}")
    
    # Disable query logging
    await monitor.disable_query_logging()
```

## Advanced Feature: Custom Types

UNO supports creating custom PostgreSQL types:

```python
from uno.infrastructure.sql import SQLEmitter

# Create an emitter
emitter = SQLEmitter()

# Generate an ENUM type
status_enum = emitter.create_enum_type(
    name="order_status",
    values=["draft", "pending", "processing", "shipped", "delivered", "cancelled"]
)

# Generate a composite type
address_type = emitter.create_composite_type(
    name="address_type",
    attributes=[
        ("street", "TEXT"),
        ("city", "TEXT"),
        ("state", "TEXT"),
        ("postal_code", "TEXT"),
        ("country", "TEXT")
    ]
)

# Apply to database
async def create_custom_types():
    async with db.session() as session:
        await session.execute(status_enum)
        await session.execute(address_type)

# Use custom types
async def create_orders_table():
    await session.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id UUID PRIMARY KEY,
            user_id UUID NOT NULL,
            status order_status NOT NULL DEFAULT 'draft',
            shipping_address address_type,
            billing_address address_type,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
    """)
```

## Conclusion

PostgreSQL's advanced features, combined with UNO's integration utilities, provide a powerful foundation for building high-performance, secure, and scalable applications. By leveraging features like custom functions, triggers, RLS, JSON support, and extensions, you can build applications that efficiently utilize the database's capabilities.

For more information on related topics, see:

- [Database Overview](overview.md): General database framework information
- [Connection Management](connections.md): Managing database connections
- [Transaction Management](transactions.md): Working with transactions
- [Query Optimization](query_optimization.md): Optimizing database queries
- [Apache AGE Integration](apache_age.md): Working with graph databases
- [Vector Search](../vector_search/overview.md): Using pgvector for vector search