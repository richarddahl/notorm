"""
Tests for the graph path query component.

This module contains tests for the GraphPathQuery and related classes,
focusing on path-based query functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any, Optional

from uno.domain.graph_path_query import (
    PathQuerySpecification,
    GraphPathQuery,
    GraphPathQueryService
)
from uno.domain.enhanced_query import QueryMetadata
from uno.domain.core import Entity


class Product(Entity):
    """Test product entity."""
    id: str
    name: str
    price: float
    

class TestPathQuerySpecification:
    """Tests for PathQuerySpecification class."""
    
    def test_init_with_string_path(self):
        """Test initialization with a string path."""
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"},
            limit=10,
            offset=5
        )
        
        assert query.path_expression == "(s:Product)-[:CATEGORY]->(t:Category)"
        assert query.params == {"t.name": "Electronics"}
        assert query.limit == 10
        assert query.offset == 5
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"},
            limit=10,
            offset=5,
            order_by="s.price",
            order_direction="desc"
        )
        
        result = query.to_dict()
        
        assert result["path_expression"] == "(s:Product)-[:CATEGORY]->(t:Category)"
        assert result["params"] == {"t.name": "Electronics"}
        assert result["limit"] == 10
        assert result["offset"] == 5
        assert result["order_by"] == "s.price"
        assert result["order_direction"] == "desc"


class TestGraphPathQuery:
    """Tests for GraphPathQuery class."""
    
    @pytest.fixture
    def mock_session(self):
        """Create a mock session for testing."""
        mock = MagicMock()
        mock.execute = AsyncMock()
        return mock
    
    @pytest.fixture
    def path_query(self):
        """Create a GraphPathQuery instance for testing."""
        return GraphPathQuery(
            track_performance=False,
            use_cache=False
        )
    
    def test_build_path_query(self, path_query):
        """Test building a Cypher query from a path specification."""
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics", "s.price": 100},
            limit=10,
            offset=5,
            order_by="s.price",
            order_direction="desc"
        )
        
        result = path_query._build_path_query(query)
        
        # Check that the result contains expected Cypher components
        assert "MATCH (s:Product)-[:CATEGORY]->(t:Category)" in result
        assert "WHERE" in result
        assert "t.name = 'Electronics'" in result
        assert "s.price = 100" in result
        assert "RETURN s.id AS id" in result
        assert "ORDER BY s.price DESC" in result
        assert "SKIP 5" in result
        assert "LIMIT 10" in result
    
    def test_format_parameter_value(self, path_query):
        """Test formatting of parameter values for Cypher queries."""
        # String value
        assert path_query._format_parameter_value("test") == "'test'"
        
        # Numeric value
        assert path_query._format_parameter_value(100) == "100"
        
        # Boolean value
        assert path_query._format_parameter_value(True) == "true"
        
        # None value
        assert path_query._format_parameter_value(None) == "NULL"
        
        # List value
        assert path_query._format_parameter_value([1, 2, "test"]) == "[1, 2, 'test']"
        
        # Dictionary with lookup
        assert path_query._format_parameter_value({"lookup": "gt", "val": 100}) == "> 100"
    
    @pytest.mark.asyncio
    async def test_execute(self, path_query, mock_session):
        """Test execution of a path query."""
        # Create a test query
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"}
        )
        
        # Mock the response from the database
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            MagicMock(id="product1"),
            MagicMock(id="product2")
        ]
        mock_session.execute.return_value = mock_result
        
        # Patch the async_session to return our mock
        with patch("uno.domain.graph_path_query.async_session", return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock())):
            # Execute the query
            result, metadata = await path_query.execute(query)
            
            # Check the result
            assert result == ["product1", "product2"]
            assert isinstance(metadata, QueryMetadata)
            assert metadata.query_path == "(s:Product)-[:CATEGORY]->(t:Category)"
            
            # Verify that the session was used correctly
            mock_session.execute.assert_called_once()
            assert "cypher('graph'" in mock_session.execute.call_args[0][0].text


class TestGraphPathQueryService:
    """Tests for GraphPathQueryService class."""
    
    @pytest.fixture
    def mock_path_query(self):
        """Create a mock GraphPathQuery for testing."""
        mock = MagicMock()
        mock.execute = AsyncMock(return_value=(["product1", "product2"], QueryMetadata(query_path="test")))
        return mock
    
    @pytest.fixture
    def mock_repository(self):
        """Create a mock repository for testing."""
        mock = MagicMock()
        mock.get = AsyncMock(side_effect=lambda id: Product(id=id, name=f"Product {id}", price=100.0) if id in ["product1", "product2"] else None)
        return mock
    
    @pytest.fixture
    def query_service(self, mock_path_query):
        """Create a GraphPathQueryService instance for testing."""
        return GraphPathQueryService(
            path_query=mock_path_query
        )
    
    @pytest.mark.asyncio
    async def test_query_entities(self, query_service, mock_repository):
        """Test querying entities using the service."""
        # Create a test query
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"}
        )
        
        # Execute the query through the service
        products, metadata = await query_service.query_entities(
            query=query,
            repository=mock_repository,
            entity_type=Product
        )
        
        # Verify results
        assert len(products) == 2
        assert all(isinstance(p, Product) for p in products)
        assert [p.id for p in products] == ["product1", "product2"]
    
    @pytest.mark.asyncio
    async def test_count_query_results(self, query_service):
        """Test counting query results without retrieving entities."""
        # Create a test query
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"},
            limit=10
        )
        
        # Execute the count query
        count = await query_service.count_query_results(query)
        
        # Verify result
        assert count == 2
        
        # Verify that the query was executed with pagination removed
        call_args = query_service.path_query.execute.call_args[0][0]
        assert call_args.path_expression == "(s:Product)-[:CATEGORY]->(t:Category)"
        assert call_args.params == {"t.name": "Electronics"}
        assert call_args.limit is None  # Should be removed for counting
    
    @pytest.mark.asyncio
    async def test_query_exists(self, query_service):
        """Test checking if a query would return results."""
        # Create a test query
        query = PathQuerySpecification(
            path="(s:Product)-[:CATEGORY]->(t:Category)",
            params={"t.name": "Electronics"}
        )
        
        # Execute the exists query
        exists = await query_service.query_exists(query)
        
        # Verify result
        assert exists is True
        
        # Verify that the query was executed with limit=1
        call_args = query_service.path_query.execute.call_args[0][0]
        assert call_args.path_expression == "(s:Product)-[:CATEGORY]->(t:Category)"
        assert call_args.params == {"t.name": "Electronics"}
        assert call_args.limit == 1  # Should be set to 1 for exists check