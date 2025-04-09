
# DatabaseFactory Integration Examples

## Exports

```python
# Main entry point
from uno.db import DatabaseFactory

# Sync connection management
from uno.db.engine import sync_connection, SyncEngineFactory

# Async connection management
from uno.db.engine import async_connection, AsyncEngineFactory

# Async session management
from uno.db.session import async_session, AsyncSessionFactory

# Configuration
from uno.db.engine import ConnectionConfig
```

## Synchronous Table Creation

```python
from uno.db.engine import sync_connection
from sqlalchemy import MetaData, Table, Column, String

metadata = MetaData()

users = Table(
    'users',
    metadata,
    Column('id', String(36), primary_key=True),
    Column('email', String(255), nullable=False),
    Column('name', String(255), nullable=False),
    schema='auth'
)

def create_tables():
    with sync_connection(
        role="admin_role",
        database="mydb",
        driver="postgresql"
    ) as conn:
        metadata.create_all(conn)
```

## Asynchronous Raw Queries

```python
from uno.db.engine import async_connection
from sqlalchemy import text

async def count_users():
    async with async_connection(
        role="reader_role",
        database="mydb",
        driver="postgresql+asyncpg"
    ) as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM auth.users"))
        return await result.scalar()
```

## ORM Operations with Async Sessions

```python
from uno.db.engine import async_session
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    
    id: Mapped[str] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(unique=True)
    name: Mapped[str]

async def get_user_by_email(email: str):
    async with async_session(
        role="reader_role",
        database="mydb",
        driver="postgresql+asyncpg"
    ) as session:
        stmt = select(User).where(User.email == email)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

async def create_user(email: str, name: str):
    async with async_session(
        role="writer_role",
        database="mydb",
        driver="postgresql+asyncpg"
    ) as session:
        user = User(email=email, name=name)
        session.add(user)
        await session.commit()
        return user
```

## Connection Configuration via Environment

```python
from functools import partial
from uno.db.engine import sync_connection, async_connection, async_session
from uno.settingsimport uno_settings

# Create partially configured context managers for your application
db_sync_connection = partial(
    sync_connection,
    host=uno_settings.DB_HOST,
    database=uno_settings.DB_NAME,
    driver="postgresql",
    pool_size=uno_settings.DB_POOL_SIZE
)

db_async_connection = partial(
    async_connection,
    host=uno_settings.DB_HOST,
    database=uno_settings.DB_NAME,
    driver="postgresql+asyncpg",
    pool_size=uno_settings.DB_POOL_SIZE
)

db_async_session = partial(
    async_session,
    host=uno_settings.DB_HOST,
    database=uno_settings.DB_NAME,
    driver="postgresql+asyncpg"
)

# Then use these throughout your application
async def example_usage():
    # For raw queries
    async with db_async_connection(role="reader_role") as conn:
        # Use connection
        
    # For ORM operations
    async with db_async_session(role="writer_role") as session:
        # Use session
```

## Custom Connection Callbacks

```python
from uno.db.engine import AsyncEngineFactory, async_connection

async def configure_database():
    # Get an engine factory
    factory = AsyncEngineFactory()
    
    # Register connection callbacks
    factory.register_callback(
        "set_application_name", 
        lambda conn: conn.execute(text("SET application_name = 'my_app'"))
    )
    
    factory.register_callback(
        "set_user_context",
        lambda conn: conn.execute(text("SET LOCAL app.current_user = 'system'"))
    )
    
    # Use the configured factory
    async with async_connection(
        role="app_role",
        database="mydb",
        driver="postgresql+asyncpg",
        factory=factory
    ) as conn:
        # Connection has had callbacks applied
        result = await conn.execute(text("SELECT current_setting('application_name')"))
        app_name = await result.scalar()
        assert app_name == 'my_app'
```

## FastApi Integration

### Create session factory

```python
session_factory = AsyncSessionFactory()
```

### Create a standard configuration

```python
connection_config = ConnectionConfig(
    role="app_user",
    database=uno_settings.DB_NAME,
    host=uno_settings.DB_HOST,
    password=uno_settings.DB_PASSWORD,
    driver="postgresql+asyncpg"
)
```

### Dependency to get a scoped session

```python
async def get_db() -> AsyncSession:
    session = session_factory.get_scoped_session(connection_config)
    try:
        yield session
    finally:
        # The session remains open, will be cleaned up by middleware
        pass
```

### Middleware to clean up sessions

```python
@app.middleware("http")
async def db_session_middleware(request, call_next):
    response = await call_next(request)
    await session_factory.cleanup_all_scoped_sessions()
    return response
```

### Example route using the session

```python
@app.get("/users/{user_id}")
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    # Use the session for database operations
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```