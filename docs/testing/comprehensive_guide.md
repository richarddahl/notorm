# Comprehensive Testing Guide

This guide provides detailed information about uno's testing architecture, methodologies, and best practices for implementing effective tests.

## Testing Architecture

The uno framework employs a layered testing approach to ensure comprehensive coverage:

```
testing_architecture
├── Unit Tests          # Testing isolated components
├── Integration Tests   # Testing component interactions
├── System Tests        # Testing end-to-end workflows
└── Performance Tests   # Testing scalability and performance
```

### Test Organization

Tests are organized according to the component structure of the framework:

```
tests/
├── unit/               # Unit tests for isolated components
│   ├── test_core/      # Tests for core functionality
│   ├── database/       # Tests for database components
│   ├── api/            # Tests for API components
│   ├── sql/            # Tests for SQL generation
│   └── ...
├── integration/        # Integration tests for component interactions
│   ├── database/       # Database integration tests
│   ├── reports/        # Reports integration tests
│   └── ...
├── benchmarks/         # Performance benchmarks
│   ├── test_api_performance.py
│   ├── test_database_performance.py
│   └── ...
└── snapshots/          # Snapshot data for comparison testing
```

## Test Types and Methodologies

### 1. Unit Tests

Unit tests verify the behavior of individual components in isolation from their dependencies.

#### Example: Testing a Model Class

```python
def test_model_attributes():
    """Test that model attributes are correctly defined."""
    # Arrange
    class TestModel(UnoModel):
        __tablename__ = "test_model"
        id = Column(Integer, primary_key=True)
        name = Column(String(255), nullable=False)
        description = Column(Text)
    
    # Act
    mapper = inspect(TestModel)
    columns = mapper.columns
    
    # Assert
    assert "id" in columns
    assert "name" in columns
    assert "description" in columns
    assert not columns["name"].nullable
    assert columns["description"].nullable
```

#### Mocking Dependencies

Use `unittest.mock` to isolate components from their dependencies:

```python
from unittest.mock import patch, MagicMock, AsyncMock

def test_database_service_with_mocked_connection():
    """Test database service with a mocked connection."""
    # Arrange
    mock_conn = MagicMock()
    mock_conn.execute.return_value = MagicMock(
        fetchall=MagicMock(return_value=[{"id": 1, "name": "Test"}])
    )
    
    service = DatabaseService()
    
    # Act
    with patch("uno.database.db.get_connection", return_value=mock_conn):
        result = service.get_records()
    
    # Assert
    assert len(result) == 1
    assert result[0]["name"] == "Test"
    mock_conn.execute.assert_called_once()
```

#### Async Testing

For testing async functions, use the `pytest-asyncio` plugin:

```python
import pytest

@pytest.mark.asyncio
async def test_async_database_service():
    """Test async database operations."""
    # Arrange
    mock_conn = AsyncMock()
    mock_conn.execute.return_value = AsyncMock(
        fetchall=AsyncMock(return_value=[{"id": 1, "name": "Test"}])
    )
    
    service = AsyncDatabaseService()
    
    # Act
    with patch("uno.database.db.get_async_connection", return_value=mock_conn):
        result = await service.get_records_async()
    
    # Assert
    assert len(result) == 1
    assert result[0]["name"] == "Test"
    mock_conn.execute.assert_called_once()
```

### 2. Integration Tests

Integration tests verify the interaction between multiple components, often involving real databases or API calls.

#### Database Integration Tests

```python
import pytest
from uno.database.config import ConnectionConfig
from uno.database.db import async_connection

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integration():
    """Test integration with the actual database."""
    # Arrange - establish real connection to test database
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_user_pw="test_password",
        db_driver="postgresql+asyncpg"
    )
    
    # Act - execute real query
    async with async_connection(config) as conn:
        result = await conn.execute("SELECT 1 as test")
        row = await result.fetchone()
    
    # Assert
    assert row is not None
    assert row["test"] == 1
```

#### API Integration Tests

```python
from fastapi.testclient import TestClient
from uno.api.app import app

@pytest.mark.integration
def test_api_integration():
    """Test integration with FastAPI endpoints."""
    # Arrange
    client = TestClient(app)
    
    # Act
    response = client.get("/api/items")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
```

### 3. System Tests

System tests verify end-to-end workflows across multiple components.

```python
import pytest
from fastapi.testclient import TestClient
from uno.api.app import app
from uno.database.db import get_connection
from sqlalchemy import text

@pytest.mark.system
def test_complete_item_workflow():
    """Test complete item creation, retrieval, and deletion workflow."""
    # Arrange
    client = TestClient(app)
    
    # Setup test data
    with get_connection() as conn:
        conn.execute(text("DELETE FROM items WHERE name LIKE 'Test Item%'"))
        conn.commit()
    
    # Act - Create item
    create_response = client.post(
        "/api/items",
        json={"name": "Test Item", "description": "Created by test"}
    )
    
    # Assert creation
    assert create_response.status_code == 201
    item_data = create_response.json()
    item_id = item_data["id"]
    
    # Act - Retrieve item
    get_response = client.get(f"/api/items/{item_id}")
    
    # Assert retrieval
    assert get_response.status_code == 200
    retrieved_item = get_response.json()
    assert retrieved_item["name"] == "Test Item"
    
    # Act - Delete item
    delete_response = client.delete(f"/api/items/{item_id}")
    
    # Assert deletion
    assert delete_response.status_code == 204
    
    # Verify item no longer exists
    get_deleted_response = client.get(f"/api/items/{item_id}")
    assert get_deleted_response.status_code == 404
```

### 4. Performance Tests

Performance tests verify the system's ability to handle load and measure performance characteristics.

```python
import pytest
import time
from uno.database.db import get_connection
from uno.queries.batch_operations import BatchOperations

@pytest.mark.performance
def test_batch_operation_performance():
    """Test performance of batch operations."""
    # Arrange
    batch_sizes = [10, 100, 1000]
    results = {}
    
    # Act - measure performance for each batch size
    for size in batch_sizes:
        # Create test data
        items = [{"id": f"item_{i}", "value": f"value_{i}"} for i in range(size)]
        
        # Measure execution time
        start_time = time.time()
        
        with get_connection() as conn:
            batch_op = BatchOperations(conn)
            batch_op.insert_many("test_items", items)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Record result
        results[size] = execution_time
        
        # Clean up
        with get_connection() as conn:
            conn.execute("DELETE FROM test_items")
            conn.commit()
    
    # Assert - execution time should scale sub-linearly
    # This means that execution_time(1000) < 10 * execution_time(100)
    assert results[1000] < 10 * results[100]
    
    # Log performance results
    for size, duration in results.items():
        print(f"Batch size {size}: {duration:.4f} seconds")
```

## Test Fixtures and Common Patterns

### 1. Database Fixtures

Reusable database fixtures provide consistent test environments:

```python
import pytest
from uno.database.config import ConnectionConfig
from uno.database.db import get_connection
from sqlalchemy import text

@pytest.fixture(scope="session")
def db_config():
    """Fixture to provide database configuration."""
    return ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_user_pw="test_password",
        db_driver="postgresql+psycopg2"
    )

@pytest.fixture(scope="function")
def db_connection(db_config):
    """Fixture to provide database connection."""
    with get_connection(db_config) as conn:
        yield conn

@pytest.fixture(scope="function")
def clean_db(db_connection):
    """Fixture to provide clean database state."""
    # Setup - clean tables before test
    tables = ["users", "items", "orders"]
    for table in tables:
        db_connection.execute(text(f"DELETE FROM {table}"))
    db_connection.commit()
    
    # Provide the connection for the test
    yield db_connection
    
    # Teardown - clean again after test
    for table in tables:
        db_connection.execute(text(f"DELETE FROM {table}"))
    db_connection.commit()
```

### 2. Factory Fixtures

Use factory fixtures to generate test data:

```python
import pytest
import uuid
from datetime import datetime

@pytest.fixture
def user_factory():
    """Factory fixture to create user test data."""
    def _create_user(**kwargs):
        """Create a user with default values that can be overridden."""
        default_user = {
            "id": str(uuid.uuid4()),
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "created_at": datetime.now(datetime.UTC).isoformat(),
            "is_active": True
        }
        return {**default_user, **kwargs}
    
    return _create_user

@pytest.fixture
def item_factory():
    """Factory fixture to create item test data."""
    def _create_item(**kwargs):
        """Create an item with default values that can be overridden."""
        default_item = {
            "id": str(uuid.uuid4()),
            "name": f"Item {uuid.uuid4().hex[:8]}",
            "description": "Test item description",
            "price": 10.99,
            "created_at": datetime.now(datetime.UTC).isoformat()
        }
        return {**default_item, **kwargs}
    
    return _create_item

# Usage in test
def test_user_creation(user_factory, db_connection):
    """Test user creation with factory-generated data."""
    # Create a user with custom email
    user = user_factory(email="custom@example.com")
    
    # Use in test
    db_connection.execute(
        text("INSERT INTO users (id, username, email, created_at, is_active) VALUES (:id, :username, :email, :created_at, :is_active)"),
        user
    )
    db_connection.commit()
    
    # Verify
    result = db_connection.execute(
        text("SELECT * FROM users WHERE id = :id"),
        {"id": user["id"]}
    ).fetchone()
    
    assert result is not None
    assert result["email"] == "custom@example.com"
```

### 3. Mock Service Fixtures

Create fixtures for common mocked services:

```python
import pytest
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_logger():
    """Fixture to provide a mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.error = MagicMock()
    logger.warning = MagicMock()
    logger.debug = MagicMock()
    return logger

@pytest.fixture
def mock_config():
    """Fixture to provide a mock configuration service."""
    config = MagicMock()
    
    # Set up default config values
    config_values = {
        "DB_HOST": "localhost",
        "DB_PORT": 5432,
        "API_VERSION": "1.0",
        "DEBUG": True
    }
    
    # Setup the get_value method to return from config_values
    config.get_value.side_effect = lambda key, default=None: config_values.get(key, default)
    
    return config

@pytest.fixture
def mock_db_session():
    """Fixture to provide a mock database session."""
    session = MagicMock()
    session.query = MagicMock(return_value=session)
    session.filter = MagicMock(return_value=session)
    session.filter_by = MagicMock(return_value=session)
    session.all = MagicMock(return_value=[])
    session.first = MagicMock(return_value=None)
    session.execute = MagicMock()
    session.commit = MagicMock()
    session.rollback = MagicMock()
    return session

@pytest.fixture
def mock_async_db_session():
    """Fixture to provide a mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session
```

### 4. Application Fixtures

Fixtures for application components:

```python
import pytest
from fastapi.testclient import TestClient
from uno.api.app import app, get_settings
from uno.database.db import get_db

@pytest.fixture
def override_settings():
    """Fixture to override application settings during tests."""
    original_settings = get_settings()
    
    # Create test settings
    test_settings = MagicMock()
    test_settings.DATABASE_URL = "sqlite:///./test.db"
    test_settings.API_PREFIX = "/api/v1"
    test_settings.DEBUG = True
    
    # Override the dependency
    app.dependency_overrides[get_settings] = lambda: test_settings
    
    yield test_settings
    
    # Restore original settings
    app.dependency_overrides[get_settings] = lambda: original_settings

@pytest.fixture
def override_db(mock_db_session):
    """Fixture to override database session during tests."""
    # Store the original get_db dependency
    original_get_db = get_db
    
    # Override with mock session
    app.dependency_overrides[get_db] = lambda: mock_db_session
    
    yield mock_db_session
    
    # Restore original
    app.dependency_overrides[get_db] = original_get_db

@pytest.fixture
def test_client(override_settings, override_db):
    """Fixture to provide a FastAPI test client with overridden dependencies."""
    with TestClient(app) as client:
        yield client
```

## Advanced Testing Techniques

### 1. Parametrized Tests

Use pytest's parametrize feature to run the same test with different inputs:

```python
import pytest
from uno.model import UnoModel, PostgresTypes
from sqlalchemy import Column, String, Integer

@pytest.mark.parametrize(
    "model_class,expected_columns,expected_primary_key",
    [
        (
            type(
                "UserModel", 
                (UnoModel,), 
                {
                    "__tablename__": "users",
                    "id": Column(Integer, primary_key=True),
                    "name": Column(String(255), nullable=False)
                }
            ),
            ["id", "name"],
            "id"
        ),
        (
            type(
                "ProductModel", 
                (UnoModel,), 
                {
                    "__tablename__": "products",
                    "product_id": Column(Integer, primary_key=True),
                    "title": Column(String(255), nullable=False),
                    "description": Column(PostgresTypes.Text)
                }
            ),
            ["product_id", "title", "description"],
            "product_id"
        )
    ]
)
def test_model_inspection(model_class, expected_columns, expected_primary_key):
    """Test model inspection with parametrized inputs."""
    # Inspect the model
    mapper = inspect(model_class)
    
    # Verify columns
    columns = mapper.columns
    column_names = [c.name for c in columns]
    for expected_column in expected_columns:
        assert expected_column in column_names
    
    # Verify primary key
    assert mapper.primary_key[0].name == expected_primary_key
```

### 2. Property-Based Testing

Use `hypothesis` for property-based testing:

```python
import pytest
from hypothesis import given, strategies as st
from uno.utilities import merge_dicts

@given(
    dict1=st.dictionaries(st.text(), st.integers()),
    dict2=st.dictionaries(st.text(), st.integers())
)
def test_merge_dicts_properties(dict1, dict2):
    """Test merge_dicts function using property-based testing."""
    # Merge dictionaries
    result = merge_dicts(dict1, dict2)
    
    # Properties that should always be true
    
    # 1. Result contains all keys from both dictionaries
    assert set(result.keys()) == set(dict1.keys()) | set(dict2.keys())
    
    # 2. Values from dict1 are preserved for unique keys
    for key, value in dict1.items():
        if key not in dict2:
            assert result[key] == value
    
    # 3. Values from dict2 are preserved for unique keys
    for key, value in dict2.items():
        if key not in dict1:
            assert result[key] == value
    
    # 4. In case of key collision, dict2 values override dict1 values
    for key in set(dict1.keys()) & set(dict2.keys()):
        assert result[key] == dict2[key]
```

### 3. Snapshot Testing

Implement snapshot testing for complex outputs:

```python
import pytest
import json
import os
from uno.sql.emitter import TableEmitter
from uno.model import UnoModel
from sqlalchemy import Column, Integer, String, ForeignKey

def test_table_emitter_snapshot(snapshot_dir):
    """Test that table emitter generates expected SQL using snapshot comparison."""
    # Create a model to test
    class TestModel(UnoModel):
        __tablename__ = "test_snapshot"
        id = Column(Integer, primary_key=True)
        name = Column(String(255), nullable=False)
        parent_id = Column(Integer, ForeignKey("parent.id"))
    
    # Generate SQL
    emitter = TableEmitter(TestModel)
    sql = emitter.emit()
    
    # Get snapshot file path
    snapshot_file = os.path.join(snapshot_dir, "test_snapshot_table.sql")
    
    # If snapshot doesn't exist, create it
    if not os.path.exists(snapshot_file):
        with open(snapshot_file, 'w') as f:
            f.write(sql)
        pytest.skip(f"Created new snapshot at {snapshot_file}")
    
    # Compare with existing snapshot
    with open(snapshot_file, 'r') as f:
        expected_sql = f.read()
    
    # Use normalized comparison that ignores whitespace differences
    assert normalize_sql(sql) == normalize_sql(expected_sql)

def normalize_sql(sql):
    """Normalize SQL by removing extra whitespace and standardizing newlines."""
    return ' '.join(sql.replace('\n', ' ').split())
```

### 4. Test Doubles (Beyond Simple Mocks)

Implement more sophisticated test doubles:

```python
class FakeRepository:
    """
    A fake repository implementation for testing.
    
    This is more sophisticated than a simple mock, as it implements
    actual in-memory behavior for testing.
    """
    
    def __init__(self):
        self.data = {}
        self.id_counter = 1
    
    def add(self, entity):
        """Add an entity to the repository."""
        if not hasattr(entity, 'id') or entity.id is None:
            entity.id = self.id_counter
            self.id_counter += 1
        
        self.data[entity.id] = entity
        return entity
    
    def get(self, entity_id):
        """Get an entity by ID."""
        return self.data.get(entity_id)
    
    def list(self, **filters):
        """List entities, optionally filtered."""
        result = list(self.data.values())
        
        # Apply filters
        for attr, value in filters.items():
            result = [e for e in result if getattr(e, attr, None) == value]
        
        return result
    
    def update(self, entity):
        """Update an entity."""
        if entity.id not in self.data:
            return None
        
        self.data[entity.id] = entity
        return entity
    
    def delete(self, entity_id):
        """Delete an entity by ID."""
        if entity_id in self.data:
            del self.data[entity_id]
            return True
        return False

# Test using the fake repository
def test_service_with_fake_repository():
    """Test service using a fake repository."""
    # Arrange
    fake_repo = FakeRepository()
    service = UserService(repository=fake_repo)
    
    # Act - create a user
    user = service.create_user("test_user", "test@example.com")
    
    # Assert
    assert user.id is not None
    assert user.name == "test_user"
    
    # Act - retrieve the user
    retrieved_user = service.get_user(user.id)
    
    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.name == "test_user"
```

## Testing Database Components

### Testing Connection Pooling

```python
import pytest
from contextlib import ExitStack
from uno.database.enhanced_connection_pool import EnhancedConnectionPool
from uno.database.config import ConnectionConfig

@pytest.mark.asyncio
async def test_connection_pool():
    """Test enhanced connection pool behavior."""
    # Arrange
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_user_pw="test_password",
        db_driver="postgresql+asyncpg"
    )
    
    pool = EnhancedConnectionPool(
        config,
        min_size=2,
        max_size=5,
        max_idle=10,
        timeout=3.0
    )
    
    try:
        # Act - initialize pool
        await pool.initialize()
        
        # Assert initial state
        assert pool.size == 2  # Min connections created
        assert pool.idle_count == 2  # All connections idle
        
        # Act - get connections
        async with ExitStack() as stack:
            # Get 3 connections (exceeds min_size but within max_size)
            conn1 = await stack.enter_async_context(pool.acquire())
            conn2 = await stack.enter_async_context(pool.acquire())
            conn3 = await stack.enter_async_context(pool.acquire())
            
            # Assert pool expanded
            assert pool.size == 3
            assert pool.idle_count == 0
            
            # Test connections work
            result1 = await conn1.execute("SELECT 1 as test")
            row1 = await result1.fetchone()
            assert row1["test"] == 1
            
            # Try a 4th connection
            conn4 = await stack.enter_async_context(pool.acquire())
            
            # Assert pool expanded again
            assert pool.size == 4
            assert pool.idle_count == 0
        
        # After exiting context, connections should be returned to pool
        assert pool.size == 4
        assert pool.idle_count == 4
        
    finally:
        # Cleanup
        await pool.close()
```

### Testing Transaction Management

```python
import pytest
from uno.database.db import async_connection
from unittest.mock import patch

@pytest.mark.asyncio
async def test_transaction_commit():
    """Test transaction commit behavior."""
    # Arrange - create mock connection and transaction objects
    mock_conn = AsyncMock()
    mock_transaction = AsyncMock()
    mock_conn.begin.return_value = mock_transaction
    
    # Act - use transaction context manager with commit
    with patch("uno.database.db.async_connection", return_value=mock_conn):
        async with async_connection() as conn:
            async with conn.begin():
                await conn.execute("INSERT INTO test VALUES ('test')")
    
    # Assert
    mock_conn.begin.assert_called_once()
    mock_transaction.__aenter__.assert_called_once()
    mock_transaction.__aexit__.assert_called_once()
    mock_conn.execute.assert_called_once_with("INSERT INTO test VALUES ('test')")
    # Transaction should be committed by not raising an exception

@pytest.mark.asyncio
async def test_transaction_rollback():
    """Test transaction rollback behavior when exception occurs."""
    # Arrange - create mock connection and transaction objects
    mock_conn = AsyncMock()
    mock_transaction = AsyncMock()
    mock_conn.begin.return_value = mock_transaction
    mock_conn.execute.side_effect = Exception("Test error")
    
    # Act - use transaction context manager with rollback due to exception
    with pytest.raises(Exception, match="Test error"):
        with patch("uno.database.db.async_connection", return_value=mock_conn):
            async with async_connection() as conn:
                async with conn.begin():
                    await conn.execute("INSERT INTO test VALUES ('test')")
    
    # Assert
    mock_conn.begin.assert_called_once()
    mock_transaction.__aenter__.assert_called_once()
    mock_transaction.__aexit__.assert_called_once()
    mock_conn.execute.assert_called_once_with("INSERT INTO test VALUES ('test')")
    # Transaction should be rolled back by passing the exception to __aexit__
```

## Testing FastAPI Endpoints

### Testing Route Registration

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from uno.api.endpoint_factory import UnoEndpointFactory

def test_endpoint_factory_route_registration():
    """Test that endpoint factory correctly registers routes."""
    # Arrange
    app = FastAPI()
    factory = UnoEndpointFactory()
    
    # Create a simple model for testing
    class TestModel:
        __tablename__ = "test_model"
        _pk_field = "id"
        
        @classmethod
        def get_schema(cls):
            return {"properties": {"id": {"type": "integer"}, "name": {"type": "string"}}}
        
        @classmethod
        def get_filter_fields(cls):
            return ["name"]
    
    # Act - register endpoints
    factory.create_endpoints(
        app=app,
        model_obj=TestModel,
        endpoints=["List", "Get", "Create", "Update", "Delete"],
        prefix="/api/test"
    )
    
    # Create test client
    client = TestClient(app)
    
    # Assert - routes are registered correctly
    # 1. List endpoint
    list_response = client.get("/api/test")
    assert list_response.status_code == 200  # Route exists
    
    # 2. Get by ID endpoint
    get_response = client.get("/api/test/1")
    assert get_response.status_code in [404, 422]  # Route exists but no item found
    
    # 3. Create endpoint
    create_response = client.post("/api/test", json={"name": "Test Item"})
    assert create_response.status_code in [201, 422]  # Route exists
    
    # 4. Update endpoint
    update_response = client.put("/api/test/1", json={"name": "Updated Item"})
    assert update_response.status_code in [200, 404, 422]  # Route exists
    
    # 5. Delete endpoint
    delete_response = client.delete("/api/test/1")
    assert delete_response.status_code in [204, 404]  # Route exists
```

### Testing Request Validation

```python
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field
from typing import Optional

# Define API models
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    description: Optional[str] = Field(None, max_length=200)
    price: float = Field(..., gt=0)

# Define API endpoints
app = FastAPI()

@app.post("/api/items", status_code=201)
async def create_item(item: ItemCreate):
    return {"id": "123", **item.dict()}

# Create test client
client = TestClient(app)

@pytest.mark.parametrize(
    "payload,expected_status,expected_error",
    [
        # Valid payload
        (
            {"name": "Test Item", "price": 10.99},
            201,
            None
        ),
        # Invalid: name too short
        (
            {"name": "Te", "price": 10.99},
            422,
            "String should have at least 3 characters"
        ),
        # Invalid: name too long
        (
            {"name": "T" * 51, "price": 10.99},
            422,
            "String should have at most 50 characters"
        ),
        # Invalid: missing required field
        (
            {"name": "Test Item"},
            422,
            "Field required"
        ),
        # Invalid: price <= 0
        (
            {"name": "Test Item", "price": 0},
            422,
            "Input should be greater than 0"
        ),
        # Invalid: description too long
        (
            {"name": "Test Item", "price": 10.99, "description": "X" * 201},
            422,
            "String should have at most 200 characters"
        )
    ]
)
def test_create_item_validation(payload, expected_status, expected_error):
    """Test validation for create item endpoint."""
    # Act
    response = client.post("/api/items", json=payload)
    
    # Assert
    assert response.status_code == expected_status
    
    if expected_error:
        error_detail = response.json().get("detail", [])
        error_messages = [err.get("msg") for err in error_detail]
        assert any(expected_error in msg for msg in error_messages)
```

## Testing SQL Generation

### Testing Table Creation

```python
import pytest
from uno.sql.emitter import TableEmitter
from uno.model import UnoModel
from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean

def test_table_emitter():
    """Test table emitter generates correct SQL."""
    # Arrange - create model
    class TestModel(UnoModel):
        __tablename__ = "test_emitter"
        id = Column(Integer, primary_key=True)
        name = Column(String(255), nullable=False)
        description = Column(Text)
        is_active = Column(Boolean, default=True)
        parent_id = Column(Integer, ForeignKey("parent.id"))
    
    # Act - generate SQL
    emitter = TableEmitter(TestModel)
    sql = emitter.emit()
    
    # Assert - SQL contains correct statements
    assert "CREATE TABLE IF NOT EXISTS" in sql
    assert "test_emitter" in sql
    assert "id INTEGER NOT NULL" in sql.replace(" ", "")
    assert "name VARCHAR(255) NOT NULL" in sql.replace(" ", "")
    assert "description TEXT" in sql.replace(" ", "")
    assert "is_active BOOLEAN DEFAULT true" in sql.replace(" ", "")
    assert "parent_id INTEGER REFERENCES parent(id)" in sql.replace(" ", "")
    assert "PRIMARY KEY (id)" in sql.replace(" ", "")
```

### Testing Function Generation

```python
import pytest
from uno.sql.builders.function import FunctionBuilder

def test_function_builder():
    """Test function builder generates correct SQL."""
    # Arrange - create function builder
    builder = FunctionBuilder("calculate_total")
    
    # Configure function
    builder.add_parameter("price", "DECIMAL")
    builder.add_parameter("quantity", "INTEGER")
    builder.set_return_type("DECIMAL")
    builder.set_language("plpgsql")
    builder.set_body("""
    DECLARE
        total DECIMAL;
    BEGIN
        total := price * quantity;
        RETURN total;
    END;
    """)
    
    # Act - build SQL
    sql = builder.build()
    
    # Assert
    assert "CREATE OR REPLACE FUNCTION calculate_total" in sql
    assert "price DECIMAL, quantity INTEGER" in sql.replace(" ", "")
    assert "RETURNS DECIMAL" in sql
    assert "LANGUAGE plpgsql" in sql
    assert "total := price * quantity" in sql
```

## Benchmarking and Performance Testing

### Database Benchmarks

```python
import pytest
import time
import statistics
from uno.database.db import get_connection
from uno.queries.batch_operations import BatchOperations

@pytest.mark.benchmark
def test_batch_insert_performance():
    """Benchmark batch insert performance."""
    # Arrange
    batch_sizes = [10, 100, 1000]
    iterations = 10
    results = {}
    
    with get_connection() as conn:
        # Create test table
        conn.execute("""
        CREATE TABLE IF NOT EXISTS benchmark_test (
            id TEXT PRIMARY KEY,
            value TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """)
        conn.commit()
        
        try:
            for size in batch_sizes:
                # Initialize results
                results[size] = []
                
                # Create batch operation handler
                batch_op = BatchOperations(conn)
                
                for i in range(iterations):
                    # Create test items
                    items = [
                        {"id": f"item_{size}_{i}_{j}", "value": f"value_{j}"}
                        for j in range(size)
                    ]
                    
                    # Measure performance
                    start_time = time.time()
                    batch_op.insert_many("benchmark_test", items)
                    end_time = time.time()
                    
                    # Record time
                    results[size].append(end_time - start_time)
                    
                    # Clean up inserted items
                    conn.execute(f"DELETE FROM benchmark_test WHERE id LIKE 'item_{size}_{i}_%'")
                    conn.commit()
                
                # Calculate statistics
                mean = statistics.mean(results[size])
                median = statistics.median(results[size])
                stdev = statistics.stdev(results[size]) if len(results[size]) > 1 else 0
                
                print(f"Batch size {size}: mean={mean:.4f}s, median={median:.4f}s, stdev={stdev:.4f}s")
                
                # Performance assertions
                if size > 10:
                    # Batch operations should be more efficient as size increases
                    # Time per item should decrease with larger batches
                    small_batch_time_per_item = statistics.mean(results[size//10]) / (size//10)
                    large_batch_time_per_item = mean / size
                    
                    assert large_batch_time_per_item < small_batch_time_per_item
        
        finally:
            # Clean up test table
            conn.execute("DROP TABLE IF EXISTS benchmark_test")
            conn.commit()
```

### API Benchmarks

```python
import pytest
import time
import statistics
import asyncio
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager

# Create test API
app = FastAPI()

@app.get("/api/benchmark/simple")
async def simple_endpoint():
    return {"status": "ok"}

@app.get("/api/benchmark/db-query")
async def db_query_endpoint():
    # Simulate database query
    await asyncio.sleep(0.01)
    return {"status": "ok", "results": [{"id": 1, "name": "Test"}]}

@app.get("/api/benchmark/complex")
async def complex_endpoint():
    # Simulate complex processing
    await asyncio.sleep(0.05)
    result = {
        "status": "ok",
        "items": [
            {"id": i, "name": f"Item {i}", "value": i * 10}
            for i in range(100)
        ]
    }
    return result

@pytest.mark.benchmark
def test_api_endpoint_performance():
    """Benchmark API endpoint performance."""
    # Arrange
    endpoints = [
        "/api/benchmark/simple",
        "/api/benchmark/db-query",
        "/api/benchmark/complex"
    ]
    iterations = 50
    results = {}
    
    # Create test client
    client = TestClient(app)
    
    for endpoint in endpoints:
        # Initialize results
        results[endpoint] = []
        
        for _ in range(iterations):
            # Measure performance
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            # Verify response
            assert response.status_code == 200
            
            # Record time
            results[endpoint].append(end_time - start_time)
        
        # Calculate statistics
        mean = statistics.mean(results[endpoint])
        median = statistics.median(results[endpoint])
        stdev = statistics.stdev(results[endpoint])
        
        print(f"Endpoint {endpoint}: mean={mean:.4f}s, median={median:.4f}s, stdev={stdev:.4f}s")
        
        # Performance assertions based on endpoint type
        if endpoint == "/api/benchmark/simple":
            assert mean < 0.01, "Simple endpoint should be very fast"
        elif endpoint == "/api/benchmark/db-query":
            assert mean < 0.03, "DB query endpoint should be relatively fast"
        elif endpoint == "/api/benchmark/complex":
            assert mean < 0.1, "Complex endpoint should complete in reasonable time"
```

## Test Coverage and Reporting

### Configure Test Coverage

```python
# In pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_classes = ["Test*"]
python_functions = ["test_*"]
python_files = ["test_*.py"]

[tool.coverage.run]
source = ["src/uno"]
omit = ["*/__init__.py", "*/migrations/*", "*/tests/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "pass"
]
```

### Create Coverage Report

```bash
# Run tests with coverage
pytest --cov=src/uno --cov-report=xml --cov-report=html tests/

# Generate console report
coverage report -m

# Generate HTML report
coverage html
```

### Visualize Test Results

```bash
# Generate JUnit XML report
pytest --junitxml=test-results.xml

# Use a reporting tool like pytest-html
pytest --html=report.html --self-contained-html
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_PASSWORD: postgreSQLR0ck%
          POSTGRES_DB: uno_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install hatch
        hatch env create
    
    - name: Run tests
      run: |
        hatch run test:all
    
    - name: Run lint
      run: |
        hatch run lint:check
    
    - name: Generate coverage report
      run: |
        hatch run test:coverage
    
    - name: Upload coverage reports
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
```

## Best Practices for Testing in uno

### 1. Test Organization

- **Name tests descriptively**: Use clear, descriptive names that explain what's being tested
- **Group related tests**: Use classes to group related tests
- **Follow naming conventions**: Use `test_` prefix for test functions and `Test` prefix for test classes
- **Use pytest marks**: Use `@pytest.mark.unit`, `@pytest.mark.integration`, etc. to categorize tests

### 2. Test Structure

- **Follow Arrange-Act-Assert**: Organize tests into setup, execution, and verification phases
- **Use docstrings**: Add clear docstrings explaining the purpose of each test
- **Keep tests focused**: Each test should verify one specific behavior
- **Isolate tests**: Tests should not depend on each other or specific execution order

### 3. Mocking and Fixtures

- **Prefer fixture factories**: Create fixtures that can generate test data with customizable parameters
- **Use context managers**: For resource cleanup in fixtures
- **Scope fixtures appropriately**: Use the right scope (`function`, `class`, `module`, `session`)
- **Mock external dependencies**: Use mocking to isolate components from external dependencies

### 4. Test Coverage

- **Aim for high coverage**: Target >80% code coverage for critical components
- **Cover edge cases**: Test boundary conditions and error scenarios
- **Test both success and failure paths**: Verify correct behavior for both valid and invalid inputs
- **Focus on functionality**: Don't chase 100% coverage at the expense of meaningful tests

### 5. Performance

- **Keep tests fast**: Fast tests encourage regular testing
- **Use test parallelization**: Run tests in parallel with `pytest-xdist`
- **Separate slow tests**: Use markers to separate slow tests
- **Optimize test fixtures**: Use session-scoped fixtures for expensive setup operations

### 6. Database Testing

- **Use test databases**: Never test against production databases
- **Clean up after tests**: Ensure tests leave the database in a clean state
- **Use transactions**: Wrap tests in transactions that can be rolled back
- **Consider in-memory databases**: For faster unit tests

### 7. API Testing

- **Test HTTP methods**: Verify correct behavior for all supported HTTP methods
- **Test status codes**: Verify appropriate status codes are returned
- **Test validation**: Verify request validation works correctly
- **Test response format**: Verify response structure matches expected format

### 8. Documentation

- **Document test requirements**: Document any special setup required for tests
- **Document test data**: Explain the purpose and structure of test fixtures
- **Document test categories**: Explain the different types of tests and when to use each

## Future Directions

### Test Automation

- **CI/CD Integration**: Expand integration with CI/CD pipelines
- **Test Monitoring**: Monitor test metrics over time (duration, flakiness, coverage)
- **Automated Regression Testing**: Implement automated regression testing for critical paths

### Test Quality

- **Mutation Testing**: Implement mutation testing to verify test quality
- **Property-Based Testing**: Expand property-based testing for complex components
- **Contract Testing**: Implement contract testing for API boundaries

### Performance Testing

- **Load Testing**: Implement load testing for high-traffic endpoints
- **Stress Testing**: Implement stress testing to identify breaking points
- **Endurance Testing**: Test system behavior under sustained load

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Property-Based Testing with Hypothesis](https://hypothesis.readthedocs.io/en/latest/)
- [Docker Compose Testing](https://docs.docker.com/compose/gettingstarted/)