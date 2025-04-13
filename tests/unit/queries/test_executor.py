import pytest
import time
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock

import pytest

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from uno.queries.executor import QueryExecutor, QueryExecutionError
from uno.queries.objs import Query, QueryPath, QueryValue
from uno.core.errors.result import Ok, Err


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
        assert result.is_ok()
        assert result.unwrap() == []

    async def test_execute_query_cache(self, executor, mock_session, mock_query):
        """Test query result caching."""
        # Setup
        mock_query.query_values = []
        executor._result_cache[mock_query.id] = {
            'result': ['cached1', 'cached2'], 
            'expires': time.time() + 300
        }
        
        # Execute with cache enabled
        result1 = await executor.execute_query(mock_query, mock_session)
        
        # Execute with force refresh
        result2 = await executor.execute_query(mock_query, mock_session, force_refresh=True)
        
        # Assert
        assert result1.is_ok()
        assert result1.unwrap() == ['cached1', 'cached2']  # Should return cached result
        
        assert result2.is_ok()
        assert result2.unwrap() == []  # Should return fresh result

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

    async def test_check_record_matches_query_cached(self, executor, mock_session, mock_query):
        """Test checking if a record matches a query with cached result."""
        # Setup
        record_id = "test-record-1"
        cache_key = (mock_query.id, record_id)
        executor._record_match_cache[cache_key] = {
            'result': True, 
            'expires': time.time() + 300
        }
        
        # Execute
        result = await executor.check_record_matches_query(mock_query, record_id, mock_session)
        
        # Assert
        assert result.is_ok()
        assert result.unwrap() is True
        assert mock_session.execute.call_count == 0  # Should not query the database

    async def test_check_record_matches_query_optimized(self, executor, mock_session, mock_query, mock_query_value):
        """Test optimized record matching."""
        # Setup
        record_id = "test-record-1"
        mock_query.query_values = [mock_query_value]
        
        # Mock optimized check capability
        with patch.object(executor, '_can_use_optimized_check', return_value=True), \
             patch.object(executor, '_check_record_direct', return_value=Ok(True)):
            
            # Execute
            result = await executor.check_record_matches_query(mock_query, record_id, mock_session)
            
            # Assert
            assert result.is_ok()
            assert result.unwrap() is True

    async def test_count_query_matches_optimized(self, executor, mock_session, mock_query):
        """Test optimized query count."""
        # Setup
        # Mock optimized count capability
        with patch.object(executor, '_can_use_optimized_count', return_value=True), \
             patch.object(executor, '_count_direct', return_value=Ok(42)):
            
            # Execute
            result = await executor.count_query_matches(mock_query, mock_session)
            
            # Assert
            assert result.is_ok()
            assert result.unwrap() == 42

    async def test_count_query_matches_fallback(self, executor, mock_session, mock_query):
        """Test query count falling back to normal execution."""
        # Setup
        # Mock the query execution to return record IDs
        with patch.object(executor, '_can_use_optimized_count', return_value=True), \
             patch.object(executor, '_count_direct', side_effect=Exception("Test error")), \
             patch.object(executor, 'execute_query', return_value=Ok(['id1', 'id2', 'id3'])):
            
            # Execute
            result = await executor.count_query_matches(mock_query, mock_session)
            
            # Assert
            assert result.is_ok()
            assert result.unwrap() == 3  # Count of records returned by execute_query

    async def test_execute_query_error_handling(self, executor, mock_session, mock_query, mock_query_value):
        """Test error handling during query execution."""
        # Setup
        mock_query.query_values = [mock_query_value]
        mock_session.execute.side_effect = Exception("Test database error")
        
        # Execute
        result = await executor._execute_query(mock_query, mock_session)
        
        # Assert
        assert result.is_err()
        assert "Error executing query" in str(result.unwrap_err())

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