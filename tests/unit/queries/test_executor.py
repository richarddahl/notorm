import pytest
import time
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from uno.core.caching import QueryCache
from uno.queries.executor import QueryExecutor, QueryExecutionError, cache_query_result
from uno.queries.objs import Query, QueryPath, QueryValue
from uno.core.errors.result import Success, Failure


class TestQueryExecutor:
    """Tests for the QueryExecutor class."""

    @pytest.fixture
    def mock_session(self):
        """Mock SQLAlchemy AsyncSession."""
        session = MagicMock(spec=AsyncSession)
        
        # Mock execute method
        execute_result = MagicMock()
        execute_result.fetchall.return_value = [('record1',), ('record2',)]
        execute_result.fetchone.return_value = {'matched': True}
        execute_result.scalar.return_value = 2
        
        session.execute.return_value = execute_result
        
        return session

    @pytest.fixture
    def mock_query(self):
        """Mock Query object."""
        query = Mock(spec=Query)
        query.id = "test-query-id"
        query.query_meta_type_id = "test_entity"
        query.query_values = []
        query.sub_queries = []
        query.include_values = "include"
        query.match_values = "and"
        query.include_queries = "include"
        query.match_queries = "and"
        
        return query

    @pytest.fixture
    def mock_query_value(self):
        """Mock QueryValue object."""
        query_value = Mock(spec=QueryValue)
        query_value.query_path_id = "test-path-id"
        query_value.include = "include"
        query_value.match = "and"
        query_value.lookup = "equal"
        query_value.values = [Mock(id="value1"), Mock(id="value2")]
        
        return query_value

    @pytest.fixture
    def mock_path(self):
        """Mock QueryPath object."""
        path = Mock(spec=QueryPath)
        path.id = "test-path-id"
        path.source_meta_type_id = "test_entity"
        path.target_meta_type_id = "test_target"
        path.cypher_path = "(s:Entity)-[:RELATION]->(t:Target)"
        
        return path

    @pytest.fixture
    def executor(self):
        """Create a QueryExecutor instance."""
        return QueryExecutor(logger=Mock())

    async def test_execute_query_empty(self, executor, mock_session, mock_query):
        """Test executing a query with no values or sub-queries."""
        # Setup
        mock_query.query_values = []
        mock_query.sub_queries = []
        
        # Execute
        result = await executor._execute_query(mock_query, mock_session)
        
        # Assert
        assert result.is_success
        assert result.value == []

    async def test_execute_query_legacy_cache(self, executor, mock_session, mock_query):
        """Test query result caching with legacy cache."""
        # Setup
        mock_query.query_values = []
        executor._legacy_result_cache[mock_query.id] = {
            'result': ['cached1', 'cached2'], 
            'expires': time.time() + 300
        }
        
        # Execute with cache enabled
        with patch.object(executor, 'get_query_cache', side_effect=Exception("Test error")):
            result1 = await executor.execute_query(mock_query, mock_session)
            
            # Execute with force refresh
            result2 = await executor.execute_query(mock_query, mock_session, force_refresh=True)
        
        # Assert
        assert result1.is_success
        assert result1.value == ['cached1', 'cached2']  # Should return cached result
        
        assert result2.is_success
        assert result2.value == []  # Should return fresh result
        
    async def test_execute_query_modern_cache(self, executor, mock_session, mock_query):
        """Test query result caching with modern cache system."""
        # Setup
        mock_query.query_values = []
        mock_cache = MagicMock(spec=QueryCache)
        mock_cache.get.return_value = ['cached1', 'cached2']
        
        # Mock the cache getter
        with patch.object(executor, 'get_query_cache', return_value=mock_cache):
            # Execute with cache enabled
            result1 = await executor.execute_query(mock_query, mock_session)
            
            # Execute with force refresh
            result2 = await executor.execute_query(mock_query, mock_session, force_refresh=True)
        
        # Assert
        assert result1.is_success
        assert result1.value == ['cached1', 'cached2']  # Should return cached result
        
        assert result2.is_success
        assert result2.value == []  # Should return fresh result
        
        # Verify cache was accessed
        mock_cache.get.assert_called_once()
        # Verify cache was not accessed for force refresh
        assert mock_cache.get.call_count == 1

    async def test_execute_query_values(self, executor, mock_session, mock_query, mock_query_value, mock_path):
        """Test executing query values."""
        # Setup
        mock_query.query_values = [mock_query_value]
        
        # Mock session execution
        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: mock_path)),  # For path lookup
            MagicMock(fetchall=lambda: [('record1',), ('record2',)]),       # For cypher query
        ]
        
        # Execute
        result = await executor._execute_query_values(
            mock_query.id, 
            [mock_query_value], 
            mock_query.include_values, 
            mock_query.match_values, 
            mock_session
        )
        
        # Assert
        assert result == ['record1', 'record2']
        assert mock_session.execute.call_count == 2

    async def test_check_record_matches_query_legacy_cached(self, executor, mock_session, mock_query):
        """Test checking if a record matches a query with legacy cached result."""
        # Setup
        record_id = "test-record-1"
        cache_key = (mock_query.id, record_id)
        executor._legacy_record_match_cache[cache_key] = {
            'result': True, 
            'expires': time.time() + 300
        }
        
        # Execute with mock cache exception to fall back to legacy
        with patch.object(executor, 'get_record_cache', side_effect=Exception("Test error")):
            result = await executor.check_record_matches_query(mock_query, record_id, mock_session)
        
        # Assert
        assert result.is_success
        assert result.value is True
        assert mock_session.execute.call_count == 0  # Should not query the database
        
    async def test_check_record_matches_query_modern_cached(self, executor, mock_session, mock_query):
        """Test checking if a record matches a query with modern cached result."""
        # Setup
        record_id = "test-record-1"
        mock_cache = MagicMock(spec=QueryCache)
        mock_cache.get.return_value = True
        
        # Execute
        with patch.object(executor, 'get_record_cache', return_value=mock_cache):
            result = await executor.check_record_matches_query(mock_query, record_id, mock_session)
        
        # Assert
        assert result.is_success
        assert result.value is True
        assert mock_session.execute.call_count == 0  # Should not query the database
        
        # Verify cache was accessed
        mock_cache.get.assert_called_once()

    async def test_check_record_matches_query_optimized(self, executor, mock_session, mock_query, mock_query_value):
        """Test optimized record matching."""
        # Setup
        record_id = "test-record-1"
        mock_query.query_values = [mock_query_value]
        
        # Mock optimized check capability
        with patch.object(executor, '_can_use_optimized_check', return_value=True), \
             patch.object(executor, '_check_record_direct', return_value=Success(True)):
            
            # Execute
            result = await executor.check_record_matches_query(mock_query, record_id, mock_session)
            
            # Assert
            assert result.is_success
            assert result.value is True

    async def test_count_query_matches_optimized(self, executor, mock_session, mock_query):
        """Test optimized query count."""
        # Setup
        # Mock optimized count capability
        with patch.object(executor, '_can_use_optimized_count', return_value=True), \
             patch.object(executor, '_count_direct', return_value=Success(42)):
            
            # Execute
            result = await executor.count_query_matches(mock_query, mock_session)
            
            # Assert
            assert result.is_success
            assert result.value == 42

    async def test_count_query_matches_fallback(self, executor, mock_session, mock_query):
        """Test query count falling back to normal execution."""
        # Setup
        # Mock the query execution to return record IDs
        with patch.object(executor, '_can_use_optimized_count', return_value=True), \
             patch.object(executor, '_count_direct', side_effect=Exception("Test error")), \
             patch.object(executor, 'execute_query', return_value=Success(['id1', 'id2', 'id3'])):
            
            # Execute
            result = await executor.count_query_matches(mock_query, mock_session)
            
            # Assert
            assert result.is_success
            assert result.value == 3  # Count of records returned by execute_query

    async def test_execute_query_error_handling(self, executor, mock_session, mock_query, mock_query_value):
        """Test error handling during query execution."""
        # Setup
        mock_query.query_values = [mock_query_value]
        mock_session.execute.side_effect = Exception("Test database error")
        
        # Execute
        result = await executor._execute_query(mock_query, mock_session)
        
        # Assert
        assert result.is_failure
        assert "Error executing query" in str(result.error)

    async def test_count_query_matches_cached(self, executor, mock_session, mock_query):
        """Test count query matches with cache."""
        # Setup
        mock_cache = MagicMock(spec=QueryCache)
        mock_cache.get.return_value = 42
        
        # Execute with cache
        with patch.object(executor, 'get_query_cache', return_value=mock_cache):
            result = await executor.count_query_matches(mock_query, mock_session)
        
        # Assert
        assert result.is_success
        assert result.value == 42
        # Verify cache was accessed
        mock_cache.get.assert_called_once()
        
    async def test_cache_invalidation(self, executor, mock_query):
        """Test cache invalidation methods."""
        # Setup mock caches
        mock_query_cache = MagicMock(spec=QueryCache)
        mock_query_cache.invalidate.return_value = 5
        mock_record_cache = MagicMock(spec=QueryCache)
        mock_record_cache.invalidate.return_value = 3
        
        # Test query invalidation
        with patch.object(executor, 'get_query_cache', return_value=mock_query_cache), \
             patch.object(executor, 'get_record_cache', return_value=mock_record_cache):
            count = await executor.invalidate_cache_for_query(mock_query.id)
            
        # Assert
        assert count == 8  # 5 + 3
        mock_query_cache.invalidate.assert_called()
        mock_record_cache.invalidate.assert_called()
        
    async def test_cache_decorator(self):
        """Test the cache_query_result decorator."""
        mock_cache = MagicMock(spec=QueryCache)
        mock_cache.get.side_effect = [None, "cached_result"]  # First None (miss), then hit
        mock_cache.set.return_value = None
        
        executor = QueryExecutor()
        
        # Define a function with the decorator
        @cache_query_result(ttl=60)
        async def test_func(arg1, arg2=None):
            return f"result-{arg1}-{arg2}"
        
        # Test cache miss
        with patch.object(executor, 'get_query_cache', return_value=mock_cache), \
             patch('uno.queries.executor.get_query_executor', return_value=executor):
            result1 = await test_func("a", arg2="b")
            result2 = await test_func("a", arg2="b")  # Should be cached now
            
        # Assert
        assert result1 == "result-a-b"
        assert result2 == "cached_result"
        assert mock_cache.get.call_count == 2
        mock_cache.set.assert_called_once()
        
    async def test_complex_lookup_conditions(self, executor, mock_session, mock_query, mock_query_value, mock_path):
        """Test different lookup conditions."""
        # Setup
        lookups_to_test = [
            "contains", "startswith", "endswith", "pattern", 
            "gt", "gte", "lt", "lte", "range", "null", "not_null",
            "in_values", "not_in_values", "has_property", "property_values"
        ]
        
        for lookup in lookups_to_test:
            # Configure mock objects
            mock_query_value.lookup = lookup
            mock_query.query_values = [mock_query_value]
            
            # Mock session execution
            mock_session.execute.side_effect = [
                MagicMock(scalars=lambda: MagicMock(first=lambda: mock_path)),  # For path lookup
                MagicMock(fetchall=lambda: [('record1',)]),                     # For cypher query
            ]
            
            # Execute
            result = await executor._execute_query_values(
                mock_query.id, 
                [mock_query_value], 
                mock_query.include_values, 
                mock_query.match_values, 
                mock_session
            )
            
            # Reset mocks for next iteration
            mock_session.reset_mock()
            
            # Assert something was returned for each lookup type
            assert isinstance(result, list)