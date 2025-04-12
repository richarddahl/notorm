# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the SQL debugging module.

These tests verify the functionality of the SQL query tracking and analysis tools.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
import asyncio
import contextlib

from uno.devtools.debugging.sql_debug import (
    capture_sql_queries,
    analyze_query_patterns,
    detect_n_plus_1,
    SqlQueryInfo,
    get_sql_debug_hooks,
    format_query
)


class TestSqlDebugging:
    """Tests for the SQL debugging utilities."""
    
    def test_format_query(self):
        """Test formatting SQL queries with parameters."""
        # Test basic query formatting
        query = "SELECT * FROM users WHERE id = %s"
        params = (1,)
        formatted = format_query(query, params)
        assert formatted == "SELECT * FROM users WHERE id = 1"
        
        # Test with named parameters
        query = "SELECT * FROM users WHERE name = %(name)s AND age = %(age)s"
        params = {"name": "test", "age": 30}
        formatted = format_query(query, params)
        assert formatted == "SELECT * FROM users WHERE name = 'test' AND age = 30"
        
        # Test with different parameter types
        query = "INSERT INTO users (name, active, score) VALUES (%s, %s, %s)"
        params = ("John", True, 42.5)
        formatted = format_query(query, params)
        assert formatted == "INSERT INTO users (name, active, score) VALUES ('John', TRUE, 42.5)"
    
    @patch("uno.devtools.debugging.sql_debug.get_db_session")
    def test_capture_sql_queries_sync(self, mock_get_session):
        """Test capturing SQL queries in synchronous mode."""
        # Create mock session and connection
        mock_session = MagicMock()
        mock_connection = MagicMock()
        mock_session.connection.return_value = mock_connection
        mock_get_session.return_value = mock_session
        
        # Mock execute method to capture queries
        orig_execute = mock_connection.execute
        
        def mock_execute(query, params=None, **kwargs):
            # Record the query
            if not hasattr(mock_connection, "queries"):
                mock_connection.queries = []
            
            mock_connection.queries.append({
                "query": str(query),
                "params": params,
                "duration": 0.1
            })
            
            # Call original method
            return orig_execute(query, params, **kwargs)
        
        mock_connection.execute = mock_execute
        
        # Use the capture_sql_queries context manager
        with capture_sql_queries() as queries:
            # Execute some queries
            mock_session.execute("SELECT * FROM users", {"id": 1})
            mock_session.execute("SELECT * FROM posts")
        
        # Check that queries were captured
        assert len(queries) == 2
        assert queries[0]["query"] == "SELECT * FROM users"
        assert queries[0]["params"] == {"id": 1}
        assert queries[1]["query"] == "SELECT * FROM posts"
    
    @pytest.mark.asyncio
    @patch("uno.devtools.debugging.sql_debug.get_async_db_session")
    async def test_capture_sql_queries_async(self, mock_get_session):
        """Test capturing SQL queries in asynchronous mode."""
        # Create mock session and connection
        mock_session = AsyncMock()
        mock_connection = AsyncMock()
        mock_session.connection.return_value = mock_connection
        mock_get_session.return_value = mock_session
        
        # Mock execute method to capture queries
        orig_execute = mock_connection.execute
        
        async def mock_execute(query, params=None, **kwargs):
            # Record the query
            if not hasattr(mock_connection, "queries"):
                mock_connection.queries = []
            
            mock_connection.queries.append({
                "query": str(query),
                "params": params,
                "duration": 0.1
            })
            
            # Call original method
            return await orig_execute(query, params, **kwargs)
        
        mock_connection.execute = mock_execute
        
        # Use the capture_sql_queries context manager in async mode
        with capture_sql_queries(is_async=True) as queries:
            # Execute some queries
            await mock_session.execute("SELECT * FROM users", {"id": 1})
            await mock_session.execute("SELECT * FROM posts")
        
        # Check that queries were captured
        assert len(queries) == 2
        assert queries[0]["query"] == "SELECT * FROM users"
        assert queries[0]["params"] == {"id": 1}
        assert queries[1]["query"] == "SELECT * FROM posts"
    
    def test_analyze_query_patterns(self):
        """Test analyzing query patterns for inefficiencies."""
        # Create a list of queries, including some inefficient patterns
        queries = [
            SqlQueryInfo(
                query="SELECT * FROM users WHERE id = 1",
                params={},
                duration=0.1,
                source="test_function",
                timestamp=0
            ),
            SqlQueryInfo(
                query="SELECT * FROM posts WHERE user_id = 1",
                params={},
                duration=0.2,
                source="test_function",
                timestamp=0
            ),
            SqlQueryInfo(
                query="SELECT * FROM posts WHERE user_id = 2",
                params={},
                duration=0.2,
                source="test_function",
                timestamp=0
            ),
            SqlQueryInfo(
                query="SELECT * FROM posts WHERE user_id = 3",
                params={},
                duration=0.2,
                source="test_function",
                timestamp=0
            ),
            SqlQueryInfo(
                query="SELECT * FROM comments WHERE id = 1",
                params={},
                duration=1.5,  # Slow query
                source="test_function",
                timestamp=0
            )
        ]
        
        # Analyze the query patterns
        analysis = analyze_query_patterns(queries)
        
        # Check that slow queries were identified
        assert len(analysis["slow_queries"]) == 1
        assert analysis["slow_queries"][0].query == "SELECT * FROM comments WHERE id = 1"
        
        # Check that similar queries were identified
        assert len(analysis["similar_queries"]) > 0
        assert any(len(group) >= 3 for group in analysis["similar_queries"])
    
    def test_detect_n_plus_1(self):
        """Test detecting N+1 query patterns."""
        # Create queries with N+1 pattern: load one user, then load posts for that user
        queries = [
            SqlQueryInfo(
                query="SELECT * FROM users",
                params={},
                duration=0.1,
                source="get_users",
                timestamp=0
            )
        ]
        
        # Add N queries for individual posts
        for i in range(10):
            queries.append(
                SqlQueryInfo(
                    query=f"SELECT * FROM posts WHERE user_id = {i}",
                    params={},
                    duration=0.1,
                    source="get_user_posts",
                    timestamp=0
                )
            )
        
        # Detect N+1 patterns
        patterns = detect_n_plus_1(queries)
        
        # Check that the N+1 pattern was detected
        assert len(patterns) >= 1
        assert patterns[0]["parent_query"].query == "SELECT * FROM users"
        assert len(patterns[0]["child_queries"]) == 10
        
        # Check suggestion for fixing the pattern
        assert "JOIN" in patterns[0]["suggestion"] or "IN" in patterns[0]["suggestion"]
    
    @patch("uno.devtools.debugging.sql_debug.find_caller")
    def test_get_sql_debug_hooks(self, mock_find_caller):
        """Test getting SQL debugging hooks for database engines."""
        # Mock the find_caller function
        mock_find_caller.return_value = ("test_file.py", 42, "test_function")
        
        # Get the SQL debug hooks
        before_cursor_execute, after_cursor_execute = get_sql_debug_hooks()
        
        # Create mock connection and cursor
        conn = MagicMock()
        cursor = MagicMock()
        statement = "SELECT * FROM users"
        parameters = {"id": 1}
        context = {}
        
        # Test the before_cursor_execute hook
        before_cursor_execute(conn, cursor, statement, parameters, context, False)
        
        # Check that timing information was added to the context
        assert "query_start_time" in context
        
        # Test the after_cursor_execute hook
        after_cursor_execute(conn, cursor, statement, parameters, context, False)
        
        # Check that query duration was calculated
        assert "query_duration" in context