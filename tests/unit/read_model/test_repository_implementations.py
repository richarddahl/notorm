"""
Unit tests for the read model repository implementations.

This module tests the repository implementations for the read model module,
verifying that they correctly store and retrieve read model data.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta, UTC
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic

import asyncpg
from uno.read_model.entities import (
    ReadModel, ReadModelId, Projection, ProjectionId, 
    Query, QueryId, CacheLevel, ProjectionType, QueryType
)
from uno.read_model.repository_implementations import (
    PostgresReadModelRepository, PostgresProjectionRepository,
    PostgresQueryRepository, PostgresProjectorConfigurationRepository,
    HybridReadModelRepository
)
from uno.database.provider import DatabaseProvider
from uno.caching.distributed.redis import RedisCache

# Define test models
class TestReadModel(ReadModel):
    """Test read model for testing the repositories."""
    pass

class TestProjection(Projection):
    """Test projection for testing the repositories."""
    pass

class TestQuery(Query):
    """Test query for testing the repositories."""
    pass

@pytest.fixture
async def db_provider(request):
    """Create a database provider for testing."""
    from uno.database.config import ConnectionConfig
    
    # Use test-specific connection details
    config = ConnectionConfig(
        db_host="localhost",
        db_port=5432,
        db_name="testdb",
        db_role="testuser",
        db_user_pw="testpass",
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=300
    )
    
    # For tests, we'll mock the provider
    class MockDatabaseProvider:
        def __init__(self):
            self.connection = None
            
        async def async_connection(self):
            class MockAsyncContextManager:
                async def __aenter__(self_cm):
                    class MockAsyncConnection:
                        async def execute(self_conn, query, *args):
                            return "DELETE 1"  # Simulate 1 row deleted
                            
                        async def fetchval(self_conn, query, *args):
                            return None  # Simulate no results
                            
                        async def fetch(self_conn, query, *args):
                            return []  # Simulate empty result set
                            
                        async def fetchrow(self_conn, query, *args):
                            if "WHERE id = " in query or "WHERE name = " in query:
                                return None  # Simulate no single result
                            return None
                            
                        async def transaction(self_conn):
                            class MockTransaction:
                                async def __aenter__(self_tx):
                                    return self_tx
                                    
                                async def __aexit__(self_tx, exc_type, exc_val, exc_tb):
                                    return False
                            return MockTransaction()
                    
                    return MockAsyncConnection()
                    
                async def __aexit__(self_cm, exc_type, exc_val, exc_tb):
                    return False
            
            return MockAsyncContextManager()
    
    provider = MockDatabaseProvider()
    yield provider

@pytest.fixture
def redis_cache():
    """Create a Redis cache for testing."""
    # Mock Redis cache implementation
    class MockRedisCache:
        def __init__(self):
            self.cache = {}
            
        async def get_async(self, key):
            return self.cache.get(key)
            
        async def set_async(self, key, value, ttl=None):
            self.cache[key] = value
            return True
            
        async def delete_async(self, key):
            if key in self.cache:
                del self.cache[key]
                return True
            return False
            
        async def invalidate_pattern_async(self, pattern):
            keys_to_delete = []
            prefix = pattern.replace("*", "")
            for key in self.cache:
                if key.startswith(prefix):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                del self.cache[key]
                
            return len(keys_to_delete)
            
        async def multi_set_async(self, mapping, ttl=None):
            for key, value in mapping.items():
                self.cache[key] = value
            return True
    
    return MockRedisCache()

@pytest.mark.asyncio
async def test_postgres_read_model_repository_create_table(db_provider):
    """Test creating the read model table."""
    repo = PostgresReadModelRepository(
        model_type=TestReadModel,
        db_provider=db_provider,
        table_name="test_read_models"
    )
    
    result = await repo.create_table_if_not_exists()
    assert result.is_success()
    assert result.value is True

@pytest.mark.asyncio
async def test_postgres_read_model_repository_get_by_id(db_provider, monkeypatch):
    """Test getting a read model by ID."""
    repo = PostgresReadModelRepository(
        model_type=TestReadModel,
        db_provider=db_provider,
        table_name="test_read_models"
    )
    
    # Create a test model
    test_id = ReadModelId(value="test123")
    test_model = TestReadModel(
        id=test_id,
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        data={"name": "Test Model", "value": 42},
        metadata={"source": "test"}
    )
    
    # Mock the database response
    async def mock_fetchrow(query, *args):
        return {
            "id": test_model.id.value,
            "version": test_model.version,
            "created_at": test_model.created_at,
            "updated_at": test_model.updated_at,
            "data": json.dumps(test_model.data),
            "metadata": json.dumps(test_model.metadata)
        }
    
    # Apply the monkeypatch to the mock connection's fetchrow method
    monkeypatch.setattr(AsyncContextManagerMockProtocol, "fetchrow", mock_fetchrow)
    
    # Test get_by_id
    result = await repo.get_by_id(test_id)
    assert result.is_success()
    assert result.value is not None
    assert result.value.id.value == test_model.id.value
    assert result.value.data == test_model.data

@pytest.mark.asyncio
async def test_postgres_projection_repository_create_table(db_provider):
    """Test creating the projections table."""
    repo = PostgresProjectionRepository(
        model_type=TestProjection,
        db_provider=db_provider
    )
    
    result = await repo.create_table_if_not_exists()
    assert result.is_success()
    assert result.value is True

@pytest.mark.asyncio
async def test_postgres_query_repository_create_table(db_provider):
    """Test creating the queries table."""
    repo = PostgresQueryRepository(
        model_type=TestQuery,
        db_provider=db_provider
    )
    
    result = await repo.create_table_if_not_exists()
    assert result.is_success()
    assert result.value is True

@pytest.mark.asyncio
async def test_hybrid_read_model_repository(db_provider, redis_cache, monkeypatch):
    """Test the hybrid read model repository."""
    repo = HybridReadModelRepository(
        model_type=TestReadModel,
        db_provider=db_provider,
        redis_cache=redis_cache,
        table_name="test_read_models"
    )
    
    # Create a test model
    test_id = ReadModelId(value="test456")
    test_model = TestReadModel(
        id=test_id,
        version=1,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        data={"name": "Cached Model", "value": 99},
        metadata={"source": "test_cache"}
    )
    
    # Mock the database response
    async def mock_fetchrow(query, *args):
        return {
            "id": test_model.id.value,
            "version": test_model.version,
            "created_at": test_model.created_at,
            "updated_at": test_model.updated_at,
            "data": json.dumps(test_model.data),
            "metadata": json.dumps(test_model.metadata)
        }
    
    # Mock Success result for database operations
    class MockSuccess:
        def __init__(self, value):
            self.value = value
        
        def is_error(self):
            return False
            
        def is_success(self):
            return True
    
    # Mock the get_by_id method to return our test model
    async def mock_get_by_id(id):
        return MockSuccess(test_model)
    
    # Mock the save method to return success
    async def mock_save(model):
        return MockSuccess(model)
    
    # Apply the monkeypatch
    monkeypatch.setattr(repo.db_repo, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(repo.db_repo, "save", mock_save)
    
    # Test the cache flow
    
    # First, the data should not be in cache
    result = await repo.get_by_id(test_id)
    assert result.is_success()
    assert result.value is not None
    assert result.value.id.value == test_model.id.value
    
    # Now save the model to ensure it gets cached
    result = await repo.save(test_model)
    assert result.is_success()
    
    # Should be in cache now, let's check
    cache_key = f"{repo.cache_prefix}{test_model.model_type}:{test_id.value}"
    assert await redis_cache.get_async(cache_key) is not None
    
    # Test cache invalidation
    result = await repo.invalidate_cache(test_id)
    assert result.is_success()
    assert await redis_cache.get_async(cache_key) is None
    
    # Test deleting the model
    result = await repo.delete(test_id)
    assert result.is_success()

# Mock class to help with monkeypatching
class AsyncContextManagerMockProtocol:
    async def fetchrow(self, query, *args):
        pass