"""
Direct tests for the RelationshipCache class.

These tests are designed to run without database dependencies,
focusing solely on the relationship caching functionality.
"""

import asyncio
import pytest
import unittest.mock
from unittest.mock import MagicMock, AsyncMock

from uno.database.query_cache import QueryCache, CachedResult, Ok
from uno.database.relationship_loader import (
    RelationshipCache,
    RelationshipCacheConfig,
)


class TestRelationshipCacheDirect:
    """Direct tests for the RelationshipCache class without database dependencies."""
    
    @pytest.mark.asyncio
    async def test_cache_to_one_relationships(self):
        """Test caching of to-one relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True,
            default_ttl=60.0,
            cache_to_one=True
        )
        
        # Create a mock query cache
        mock_query_cache = MagicMock()
        mock_query_cache.get = AsyncMock(return_value=unittest.mock.MagicMock(is_success=False))
        mock_query_cache.set = AsyncMock()
        
        # Create the cache
        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)
        
        # Create mock entities
        parent = MagicMock()
        parent.__class__ = type('Parent', (), {})
        parent.id = "parent1"
        
        related_entity = MagicMock()
        related_entity.__class__ = type('Related', (), {'__tablename__': 'related'})
        related_entity.id = "related1"
        
        # Test storing a to-one relationship
        await cache.store_to_one(parent, "related", related_entity)
        
        # Verify the query cache was called to store the relationship
        assert mock_query_cache.set.call_count == 1
        
        # Setup cache hit for next call
        mock_query_cache.get = AsyncMock(return_value=Ok(related_entity))
        
        # Test retrieving the to-one relationship
        target_class = related_entity.__class__
        result = await cache.get_to_one(parent, "related", target_class, related_entity.id)
        
        # Verify we got the entity back and stats were updated
        assert result.is_success
        assert result.value == related_entity
        assert cache.hits == 1
    
    @pytest.mark.asyncio
    async def test_cache_to_many_relationships(self):
        """Test caching of to-many relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True,
            default_ttl=60.0,
            cache_to_many=True
        )
        
        # Create a mock query cache
        mock_query_cache = MagicMock()
        mock_query_cache.get = AsyncMock(return_value=unittest.mock.MagicMock(is_success=False))
        mock_query_cache.set = AsyncMock()
        
        # Create the cache
        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)
        
        # Create mock entities
        parent = MagicMock()
        parent.__class__ = type('Parent', (), {})
        parent.id = "parent1"
        
        related_entities = [
            MagicMock(),
            MagicMock(),
            MagicMock()
        ]
        
        for i, entity in enumerate(related_entities):
            entity.__class__ = type('Related', (), {'__tablename__': 'related'})
            entity.id = f"related{i+1}"
        
        # Test storing a to-many relationship
        await cache.store_to_many(parent, "related", related_entities)
        
        # Verify the query cache was called to store the relationship
        assert mock_query_cache.set.call_count == 1
        
        # Setup cache hit for next call
        mock_query_cache.get = AsyncMock(return_value=Ok(related_entities))
        
        # Test retrieving the to-many relationship
        target_class = related_entities[0].__class__
        result = await cache.get_to_many(parent, "related", target_class)
        
        # Verify we got the entities back and stats were updated
        assert result.is_success
        assert result.value == related_entities
        assert cache.hits == 1
    
    @pytest.mark.asyncio
    async def test_cache_disabled(self):
        """Test behavior when cache is disabled."""
        # Setup with cache disabled
        cache_config = RelationshipCacheConfig(
            enabled=False
        )
        
        # Create a mock query cache
        mock_query_cache = MagicMock()
        mock_query_cache.get = AsyncMock()
        mock_query_cache.set = AsyncMock()
        
        # Create the cache
        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)
        
        # Create mock entities
        parent = MagicMock()
        parent.__class__ = type('Parent', (), {})
        parent.id = "parent1"
        
        related_entity = MagicMock()
        related_entity.__class__ = type('Related', (), {'__tablename__': 'related'})
        related_entity.id = "related1"
        
        # Test storing with cache disabled
        await cache.store_to_one(parent, "related", related_entity)
        
        # Verify the query cache was not called
        assert mock_query_cache.set.call_count == 0
        
        # Test retrieving with cache disabled
        target_class = related_entity.__class__
        result = await cache.get_to_one(parent, "related", target_class, related_entity.id)
        
        # Verify we got a cache miss result
        assert result.is_failure
        assert mock_query_cache.get.call_count == 0
    
    @pytest.mark.asyncio
    async def test_invalidate_entity(self):
        """Test invalidation of cached relationships."""
        # Setup
        cache_config = RelationshipCacheConfig(
            enabled=True,
            default_ttl=60.0
        )
        
        # Create a mock query cache
        mock_query_cache = MagicMock()
        mock_query_cache.invalidate_by_table = AsyncMock()
        mock_query_cache.invalidate = AsyncMock()
        
        # Create the cache
        cache = RelationshipCache(config=cache_config, query_cache=mock_query_cache)
        
        # Create mock entity
        entity = MagicMock()
        entity.__class__ = type('TestEntity', (), {'__tablename__': 'test_table'})
        entity.id = "test1"
        
        # Test invalidation
        await cache.invalidate_entity(entity)
        
        # Verify that invalidation methods were called
        assert mock_query_cache.invalidate_by_table.call_count == 1
        assert mock_query_cache.invalidate.call_count == 1
        assert cache.invalidations == 1
    
    @pytest.mark.asyncio
    async def test_custom_ttl_config(self):
        """Test custom TTL configuration."""
        # Setup with custom TTLs
        cache_config = RelationshipCacheConfig(
            enabled=True,
            default_ttl=60.0,
            entity_ttls={"TestEntity": 120.0},
            relationship_ttls={"TestEntity.related": 180.0}
        )
        
        # Create the cache
        cache = RelationshipCache(config=cache_config)
        
        # Test TTL retrieval
        assert cache.config.get_ttl_for_entity("TestEntity") == 120.0
        assert cache.config.get_ttl_for_entity("UnknownEntity") == 60.0
        assert cache.config.get_ttl_for_relationship("TestEntity", "related") == 180.0
        assert cache.config.get_ttl_for_relationship("TestEntity", "unknown") == 120.0
        assert cache.config.get_ttl_for_relationship("UnknownEntity", "related") == 60.0