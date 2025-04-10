# Database Module Tests

This directory contains tests for the database-related modules in the NotORM framework.

## Test Files

### `test_db.py`

Tests for the `UnoDBFactory` class and related database operations:
- Connection management (sync and async)
- CRUD operations
- Transaction handling
- Error handling and recovery
- Connection pooling

Note that some tests in this module require an actual PostgreSQL database for integration testing. These tests are skipped when running in environments without database access.

## Testing Approach

The database tests use a combination of:

1. **Mocked database connections** for pure unit tests
2. **In-memory SQLite** for lightweight tests that require a real database
3. **PostgreSQL database** for full integration tests

Many of the async tests require `pytest-asyncio` to run properly. Make sure it's installed when running these tests.

## Common Test Patterns

1. **Connection mocking**: 
   ```python
   with patch('uno.database.db.async_connection') as mock_conn:
       # Test code here
   ```

2. **Transaction testing**:
   ```python
   # Setup
   mock_conn = AsyncMockContextManager()
   mock_conn.__aenter__.return_value = mock_conn
   
   # Test transaction
   await db.transaction(mock_conn, ...)
   ```

3. **Result validation**:
   ```python
   mock_cursor.fetchall.return_value = [{'id': 1, 'name': 'test'}]
   result = await db.execute_query(...)
   assert result[0]['id'] == 1
   ```

## Running the Tests

To run just the database module tests:

```bash
ENV=test pytest tests/unit/database/
```

To run a specific test file:

```bash
ENV=test pytest tests/unit/database/test_db.py
```

## Known Issues

- Some async tests may be skipped if pytest-asyncio is not installed
- Integration tests will be skipped without a configured test database
- Transaction tests can be sensitive to mocking implementation details