# Testing Database Components

This document provides guidance on testing database components in the NotORM framework, with specific focus on challenges and best practices for both synchronous and asynchronous database operations.

## Introduction

The database layer in NotORM provides a unified approach to database operations, supporting both synchronous and asynchronous access patterns. Testing this layer thoroughly presents several challenges:

### Synchronous Testing Challenges

1. **Connection Management**: Testing proper connection lifecycle
2. **Error Handling**: Verifying retry mechanisms and proper error propagation
3. **Resource Cleanup**: Ensuring connections and engines are properly disposed
4. **Pool Configuration**: Testing connection pool settings
5. **Driver Compatibility**: Testing with multiple database drivers

### Asynchronous Testing Challenges

1. **Coroutine Handling**: Working with async functions and awaitable objects
2. **Context Manager Testing**: Testing `async with` context managers
3. **Mock Setup**: Properly configuring async mocks for testing
4. **Test Runner Integration**: Using pytest-asyncio or other async test runners
5. **Resource Cleanup**: Ensuring proper cleanup of async resources

This document provides strategies and examples for addressing these challenges.

## Testing Database Component Architecture

### Core Components Under Test

The main database components include:

1. **Factory Components**:
   - `DatabaseFactory`: Top-level factory that integrates all specialized factories
   - `SyncEngineFactory`: Creates synchronous SQLAlchemy engines
   - `AsyncEngineFactory`: Creates asynchronous SQLAlchemy engines
   - `AsyncSessionFactory`: Creates asynchronous SQLAlchemy ORM sessions

2. **Context Managers**:
   - `sync_connection`: Context manager for synchronous database connections
   - `async_connection`: Context manager for asynchronous database connections
   - `async_session`: Context manager for asynchronous ORM sessions

3. **Configuration**:
   - `ConnectionConfig`: Immutable configuration model for database connections

4. **Other Components**:
   - Connection callbacks for customization
   - Retry mechanisms for handling transient errors
   - Connection pooling configuration

## Testing Synchronous Database Components

The synchronous database components are more straightforward to test than their asynchronous counterparts, as they don't require special test runners or coroutine handling. However, they require careful attention to error handling, connection lifecycles, and resource cleanup.

### Testing the SyncEngineFactory

```python
@patch('uno.database.engine.sync.create_engine')
def test_create_engine(self, mock_create_engine):
    """Test creating a synchronous engine."""
    # Setup mock
    mock_engine = MagicMock(spec=Engine)
    mock_create_engine.return_value = mock_engine
    
    # Create a ConnectionConfig
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_user_pw="test_password",
        db_driver="postgresql+psycopg2"
    )
    
    # Create factory and engine
    factory = SyncEngineFactory()
    engine = factory.create_engine(config)
    
    # Verify engine creation and URL formation
    mock_create_engine.assert_called_once()
    url_arg = mock_create_engine.call_args[0][0]
    assert url_arg.drivername == config.db_driver
    assert url_arg.username == config.db_role
    assert url_arg.database == config.db_name
```

### Testing Connection Pooling

```python
def test_engine_with_custom_pool_settings(self):
    """Test engine creation with custom connection pool settings."""
    # Create config with pool settings
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_driver="postgresql+psycopg2",
        pool_size=20,
        max_overflow=15,
        pool_timeout=45,
        pool_recycle=120
    )
    
    # Test with mocked create_engine
    with patch('uno.database.engine.sync.create_engine') as mock_create_engine:
        mock_engine = MagicMock(spec=Engine)
        mock_create_engine.return_value = mock_engine
        
        factory = SyncEngineFactory()
        factory.create_engine(config)
        
        # Verify pool settings were passed to create_engine
        _, kwargs = mock_create_engine.call_args
        assert kwargs["pool_size"] == 20
        assert kwargs["max_overflow"] == 15
        assert kwargs["pool_timeout"] == 45
        assert kwargs["pool_recycle"] == 120
```

### Testing Multiple Database Drivers

```python
@pytest.mark.parametrize("driver,expected_uri_start", [
    ("postgresql+psycopg2", "postgresql+psycopg2://"),
    ("mysql+pymysql", "mysql+pymysql://"),
    ("sqlite+pysqlite", "sqlite+pysqlite://")
])
def test_multiple_database_drivers(self, driver, expected_uri_start):
    """Test engine creation with different database drivers."""
    # Create config with specific driver
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_driver=driver
    )
    
    # Test URI generation
    with patch('urllib.parse.quote_plus', return_value="encoded_password"):
        uri = config.get_uri()
        assert uri.startswith(expected_uri_start)
```

### Testing Error Handling and Retries

```python
def test_sync_connection_specific_error_types(self):
    """Test handling of specific database error types."""
    # Test with generic SQLAlchemy error
    with patch('uno.database.engine.sync.SyncEngineFactory') as MockFactory:
        mock_factory = MagicMock()
        MockFactory.return_value = mock_factory
        
        mock_engine = MagicMock(spec=Engine)
        mock_factory.create_engine.return_value = mock_engine
        
        # Set up error
        error = SQLAlchemyError("Test error")
        mock_engine.connect.side_effect = error
        
        # Test that connection context handles error with retries
        with pytest.raises(SQLAlchemyError):
            with sync_connection(
                db_role="test_role",
                db_name="test_db",
                factory=mock_factory,
                max_retries=2
            ):
                pass
        
        # Verify multiple attempts were made
        assert mock_factory.create_engine.call_count == 2
        assert mock_engine.connect.call_count == 2
        assert mock_engine.dispose.call_count == 2
```

## Testing Asynchronous Database Components

Testing asynchronous database code requires special handling due to the coroutine-based nature of async/await code. This section covers techniques specific to testing the async database components.

### Setting Up Async Tests

Use the pytest-asyncio plugin for testing async code:

```python
import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncConnection

@pytest.mark.asyncio
async def test_async_function():
    # Test async code here
    result = await some_async_function()
    assert result is not None
```

### Mocking Async Components

Properly mocking async components requires special consideration:

```python
# Basic async mock
mock_async_function = AsyncMock()

# Mocking an async context manager
mock_context = AsyncMock()
mock_context.__aenter__.return_value = mock_context
mock_context.__aexit__.return_value = None  # or return_value = False

# Mocking a chain of async method calls
mock_obj = AsyncMock()
mock_result = AsyncMock()
mock_obj.some_method.return_value = mock_result
```

### Example: Testing AsyncEngineFactory

```python
@pytest.mark.asyncio
async def test_async_engine_factory():
    # Setup
    logger = MagicMock()
    factory = AsyncEngineFactory(logger=logger)
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_host="localhost",
        db_port=5432,
        db_driver="postgresql+asyncpg"
    )
    
    # Test with patch
    with patch('sqlalchemy.ext.asyncio.create_async_engine') as mock_create_engine:
        mock_engine = AsyncMock(spec=AsyncEngine)
        mock_create_engine.return_value = mock_engine
        
        # Act
        engine = factory.create_engine(config)
        
        # Assert
        assert engine == mock_engine
        mock_create_engine.assert_called_once()
        logger.debug.assert_called_once()
```

### Challenges with Testing Async Context Managers

Testing async context managers like `async_connection` presents significant challenges:

1. **Coroutine Mocking**: Properly mocking `await engine.dispose()` in finally blocks
2. **Context Chaining**: Handling chains of async context managers
3. **Exception Flow**: Testing error paths in async context managers

For example, testing the `async_connection` context manager is complex because:

```python
@contextlib.asynccontextmanager
async def async_connection(...):
    # ... setup code ...
    try:
        # Create engine
        engine = factory.create_engine(config)
        
        # Connect and yield
        async with engine.connect() as conn:
            yield conn
    
    finally:
        # Dispose engine
        if engine:
            await engine.dispose()  # This await is hard to mock
```

### Strategies for Testing Async Context Managers

1. **Test Surrounding Functions**: Test the functions called by the context manager
2. **Integration Testing**: Use real connections to test the full context manager
3. **Custom Mock Classes**: Create specialized AsyncMock subclasses
4. **Patch Inner Components**: Patch specific parts of the context manager

#### Example: Using Custom AsyncMock

```python
class CustomAsyncMock(AsyncMock):
    """Custom AsyncMock that better handles awaited methods."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Setup default returns for common async methods
        self.dispose = AsyncMock()
        self.__aenter__ = AsyncMock(return_value=self)
        self.__aexit__ = AsyncMock(return_value=None)
```

## Testing DatabaseFactory Integration

The `DatabaseFactory` serves as the top-level entry point for all database operations, integrating the various specialized factories. Testing this integration presents unique challenges and opportunities.

### Testing Factory Initialization

```python
def test_initialization(self):
    """Test factory initialization creates all specialized factories."""
    logger = MagicMock(spec=logging.Logger)
    factory = DatabaseFactory(logger=logger)
    
    # Verify all specialized factories were created
    assert isinstance(factory.sync_engine_factory, SyncEngineFactory)
    assert isinstance(factory.async_engine_factory, AsyncEngineFactory)
    assert isinstance(factory.async_session_factory, AsyncSessionFactory)
    
    # Verify logger is shared between all factories
    assert factory.sync_engine_factory.logger is logger
    assert factory.async_engine_factory.logger is logger
    assert factory.async_session_factory.logger is logger
```

### Testing Factory Getters

```python
def test_factory_accessors(self):
    """Test access to specialized factories."""
    factory = DatabaseFactory()
    
    # Test getter methods
    sync_factory = factory.get_sync_engine_factory()
    async_factory = factory.get_async_engine_factory()
    session_factory = factory.get_async_session_factory()
    
    # Verify correct factory types
    assert isinstance(sync_factory, SyncEngineFactory)
    assert isinstance(async_factory, AsyncEngineFactory)
    assert isinstance(session_factory, AsyncSessionFactory)
```

### Testing Callback Isolation

```python
def test_factory_callback_isolation(self):
    """Test callbacks registered on one factory don't affect others."""
    factory = DatabaseFactory()
    
    # Create callback mocks
    sync_callback = MagicMock()
    async_callback = MagicMock()
    
    # Register callbacks on different factories
    sync_factory = factory.get_sync_engine_factory()
    async_factory = factory.get_async_engine_factory()
    
    sync_factory.register_callback("sync_test", sync_callback)
    async_factory.register_callback("async_test", async_callback)
    
    # Verify callbacks are registered only on appropriate factory
    assert "sync_test" in sync_factory.connection_callbacks
    assert "sync_test" not in async_factory.connection_callbacks
    assert "async_test" in async_factory.connection_callbacks
    assert "async_test" not in sync_factory.connection_callbacks
```

### Testing Custom Factories

```python
def test_custom_factories(self):
    """Test using custom factory implementations."""
    # Create custom factory implementations
    custom_sync_factory = MagicMock(spec=SyncEngineFactory)
    custom_async_factory = MagicMock(spec=AsyncEngineFactory)
    custom_session_factory = MagicMock(spec=AsyncSessionFactory)
    
    # Create factory and replace default factories
    factory = DatabaseFactory()
    factory.sync_engine_factory = custom_sync_factory
    factory.async_engine_factory = custom_async_factory
    factory.async_session_factory = custom_session_factory
    
    # Verify getters return custom factories
    assert factory.get_sync_engine_factory() is custom_sync_factory
    assert factory.get_async_engine_factory() is custom_async_factory
    assert factory.get_async_session_factory() is custom_session_factory
```

## Async/Sync Dual Testing

For code that can operate in both synchronous and asynchronous modes, consider:

1. **Parameterized Tests**: Use pytest.mark.parametrize to test both modes
2. **Shared Test Logic**: Extract common assertions into helper functions
3. **Mode-Specific Fixtures**: Create fixtures for sync and async testing

```python
@pytest.mark.parametrize("is_async", [True, False])
def test_database_operation(is_async):
    if is_async:
        # Setup async testing
        pytest.importorskip("pytest_asyncio")
        pytest.mark.asyncio(run_async_test())
    else:
        # Run sync test
        run_sync_test()
```

## Testing ConnectionConfig Edge Cases

The `ConnectionConfig` model is used to configure database connections and provides features like immutability, validation, and URI generation. Testing edge cases is important to ensure robust behavior.

### Testing Special Characters in Passwords

```python
@patch('urllib.parse.quote_plus')
def test_connection_config_with_special_characters(self, mock_quote_plus):
    """Test ConnectionConfig handles special characters in passwords."""
    # Create config with special characters in password
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_user_pw="p@$$w0rd!+%^*",  # Password with special characters
        db_driver="postgresql+psycopg2"
    )
    
    # Setup mock for password encoding
    mock_quote_plus.return_value = "encoded_special_password"
    
    # Get URI with encoded password
    uri = config.get_uri()
    
    # Verify quote_plus was called with the special password
    mock_quote_plus.assert_called_once_with("p@$$w0rd!+%^*")
    
    # Verify URI contains the encoded password
    assert uri == "postgresql+psycopg2://test_role:encoded_special_password@localhost:5432/test_db"
```

### Testing Driver-Specific Connection Arguments

```python
def test_connection_config_driver_specific_args(self):
    """Test ConnectionConfig with driver-specific connect_args."""
    # Create config with connect_args
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_driver="postgresql+psycopg2",
        connect_args={
            "ssl": True,
            "application_name": "test_app",
            "keepalives": 1
        }
    )
    
    # Verify connect_args are stored correctly
    assert config.connect_args == {
        "ssl": True,
        "application_name": "test_app",
        "keepalives": 1
    }
    
    # Test that the args are used when creating an engine
    with patch('sqlalchemy.create_engine') as mock_create_engine:
        from uno.database.engine.sync import SyncEngineFactory
        factory = SyncEngineFactory()
        factory.create_engine(config)
        
        # Verify connect_args were passed to create_engine
        _, kwargs = mock_create_engine.call_args
        assert kwargs["connect_args"] == config.connect_args
```

### Testing Immutability

```python
def test_immutability(self):
    """Test that ConnectionConfig is immutable."""
    config = ConnectionConfig(
        db_role="test_role",
        db_name="test_db",
        db_driver="postgresql+psycopg2"
    )
    
    # Attempt to modify a field
    with pytest.raises(Exception) as exc_info:
        config.db_name = "new_db_name"
    
    # Verify error about immutability
    assert "frozen" in str(exc_info.value).lower() or "immutable" in str(exc_info.value).lower()
```

## Best Practices

1. **Test Edge Cases**: Verify behavior with special characters, empty values, and edge cases
2. **Skip When Necessary**: If testing async code is too complex, skip with clear reasoning
3. **Focus on Units**: Test smaller async functions rather than large context managers
4. **Test Real Components**: Use real, in-memory databases for integration testing
5. **Dependency Injection**: Design code to accept mocked factories and engines
6. **Detailed Skip Messages**: When skipping tests, document why and future plans
7. **Test Driver Compatibility**: Verify code works with multiple database drivers
8. **Verify Error Handling**: Test retry mechanisms and error propagation

## Conclusion

Testing database components, especially those with asynchronous functionality, presents unique challenges but is essential for a robust application. Effective testing strategies include:

1. **Comprehensive Component Coverage**: Test all aspects of the database layer:
   - Configuration validation and edge cases
   - Factory integration and specialization
   - Connection management and pooling
   - Error handling and recovery
   - Multi-driver compatibility

2. **Async-Specific Approaches**:
   - Use proper async mocking techniques
   - Leverage pytest-asyncio for running async tests
   - Handle coroutines and awaitable objects carefully
   - Skip complex async tests with detailed explanations

3. **Balanced Test Strategy**:
   - Unit test individual components thoroughly
   - Integration test component interactions
   - Focus on smaller, more focused functions
   - Document testing strategies and challenges

4. **Practical Considerations**:
   - Use real, in-memory databases for integration testing
   - Design code with testability in mind through dependency injection
   - Test different database drivers
   - Verify error handling and retry mechanisms

When in doubt, prioritize testing core business functionality over testing the infrastructure itself, as the latter can often be better verified through integration tests. But with the strategies outlined in this document, even complex database components with synchronous and asynchronous capabilities can be effectively tested.