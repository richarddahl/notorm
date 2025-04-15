"""
Tests for the GraphNavigator class.

This module contains tests for the GraphNavigator class which provides
advanced graph traversal algorithms for knowledge graphs.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from uno.ai.graph_integration.graph_navigator import (
    GraphNavigator,
    GraphNavigatorConfig,
    TraversalMode,
    NavigationAlgorithm,
    NavigationStrategy,
    RelationshipType,
    NodeFilter,
    PathConstraint,
    PathResult,
    SubgraphResult,
    create_graph_navigator
)


class TestGraphNavigator:
    """Tests for the GraphNavigator class."""
    
    @pytest.fixture
    def mock_pool(self):
        """Create a mock connection pool."""
        mock = MagicMock()
        mock.acquire = AsyncMock()
        mock.close = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_conn(self):
        """Create a mock database connection."""
        mock = MagicMock()
        mock.execute = AsyncMock()
        mock.fetchval = AsyncMock()
        mock.fetch = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_asyncpg(self):
        """Mock asyncpg module."""
        with patch("uno.ai.graph_integration.graph_navigator.asyncpg") as mock:
            mock.create_pool = AsyncMock()
            yield mock
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        return GraphNavigatorConfig(
            age_schema="ag_catalog",
            graph_name="test_graph",
            default_traversal_mode=TraversalMode.BREADTH_FIRST,
            default_algorithm=NavigationAlgorithm.SHORTEST_PATH,
            default_strategy=NavigationStrategy.DEFAULT,
            default_max_depth=3,
            default_max_results=10,
            relationship_types=[
                RelationshipType(name="KNOWS", direction="OUTGOING", weight=1.0),
                RelationshipType(name="WORKS_WITH", direction="BOTH", weight=1.5)
            ],
            default_node_filter=NodeFilter(),
            default_path_constraint=PathConstraint(),
            cache_results=True,
            cache_ttl=60,
            timeout=10
        )
    
    @pytest.fixture
    async def navigator(self, mock_asyncpg, mock_pool, mock_conn, config):
        """Create a test navigator with mocked dependencies."""
        mock_asyncpg.create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = True
        
        navigator = GraphNavigator(
            connection_string="postgresql://test:test@localhost:5432/testdb",
            config=config
        )
        await navigator.initialize()
        return navigator
    
    @pytest.mark.asyncio
    async def test_initialize(self, navigator, mock_asyncpg, mock_conn):
        """Test initialization of the graph navigator."""
        # Check that the pool was created
        mock_asyncpg.create_pool.assert_called_once_with(
            "postgresql://test:test@localhost:5432/testdb"
        )
        
        # Check that AGE extension was checked
        mock_conn.fetchval.assert_called_once()
        assert "extname = 'age'" in mock_conn.fetchval.call_args[0][0]
        
        # Check that initialization is complete
        assert navigator.initialized is True
    
    @pytest.mark.asyncio
    async def test_close(self, navigator, mock_pool):
        """Test closing the navigator."""
        await navigator.close()
        
        # Check that the pool was closed
        mock_pool.close.assert_called_once()
        
        # Check that initialized is set to False
        assert navigator.initialized is False
    
    @pytest.mark.asyncio
    async def test_find_shortest_path(self, navigator, mock_conn):
        """Test finding the shortest path between nodes."""
        # Mock the database response
        mock_conn.fetchval.return_value = json.dumps({
            "vertices": [
                {"id": "node1", "labels": ["Person"], "properties": {"name": "Alice"}},
                {"id": "node2", "labels": ["Person"], "properties": {"name": "Bob"}}
            ],
            "edges": [
                {"id": "edge1", "label": "KNOWS", "start_id": "node1", "end_id": "node2"}
            ]
        })
        
        # Call the method
        result = await navigator.find_shortest_path(
            start_node_id="node1",
            end_node_id="node2",
            traversal_mode=TraversalMode.BREADTH_FIRST,
            relationship_types=["KNOWS"],
            max_depth=3
        )
        
        # Check the result
        assert result is not None
        assert result.start_node["id"] == "node1"
        assert result.end_node["id"] == "node2"
        assert len(result.nodes) == 2
        assert len(result.relationships) == 1
        assert result.length == 1
        
        # Check that the correct query was executed
        executed_query = mock_conn.fetchval.call_args_list[1][0][0]
        assert "cypher('test_graph'" in executed_query
        
        # Ensure Cypher params were used
        params = mock_conn.fetchval.call_args_list[1][0][1]
        assert "MATCH path = shortestPath" in params
        assert "WHERE id(a) = 'node1' AND id(b) = 'node2'" in params
    
    @pytest.mark.asyncio
    async def test_find_all_paths(self, navigator, mock_conn):
        """Test finding all paths between nodes."""
        # Mock the database response
        mock_conn.fetch.return_value = [
            MagicMock(path=json.dumps({
                "vertices": [
                    {"id": "node1", "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": "node3", "labels": ["Person"], "properties": {"name": "Charlie"}},
                    {"id": "node2", "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "edges": [
                    {"id": "edge1", "label": "KNOWS", "start_id": "node1", "end_id": "node3"},
                    {"id": "edge2", "label": "KNOWS", "start_id": "node3", "end_id": "node2"}
                ]
            })),
            MagicMock(path=json.dumps({
                "vertices": [
                    {"id": "node1", "labels": ["Person"], "properties": {"name": "Alice"}},
                    {"id": "node4", "labels": ["Person"], "properties": {"name": "David"}},
                    {"id": "node2", "labels": ["Person"], "properties": {"name": "Bob"}}
                ],
                "edges": [
                    {"id": "edge3", "label": "WORKS_WITH", "start_id": "node1", "end_id": "node4"},
                    {"id": "edge4", "label": "WORKS_WITH", "start_id": "node4", "end_id": "node2"}
                ]
            }))
        ]
        
        # Call the method
        results = await navigator.find_all_paths(
            start_node_id="node1",
            end_node_id="node2",
            max_paths=2,
            traversal_mode=TraversalMode.BREADTH_FIRST,
            relationship_types=["KNOWS", "WORKS_WITH"],
            max_depth=3
        )
        
        # Check the results
        assert len(results) == 2
        assert results[0].start_node["id"] == "node1"
        assert results[0].end_node["id"] == "node2"
        assert len(results[0].nodes) == 3
        assert len(results[0].relationships) == 2
        assert results[0].length == 2
        
        # Check that the correct query was executed
        executed_query = mock_conn.fetch.call_args[0][0]
        assert "cypher('test_graph'" in executed_query
        
        # Ensure Cypher params were used
        params = mock_conn.fetch.call_args[0][1]
        assert "MATCH path = (a)-[r:KNOWS|WORKS_WITH*1..3]->(b)" in params
        assert "WHERE id(a) = 'node1' AND id(b) = 'node2'" in params
        assert "LIMIT 2" in params
    
    @pytest.mark.asyncio
    async def test_extract_subgraph(self, navigator, mock_conn):
        """Test extracting a subgraph centered on a node."""
        # Mock the database response
        mock_conn.fetchval.return_value = json.dumps({
            "nodes": [
                {"id": "node1", "labels": ["Person"], "properties": {"name": "Alice"}},
                {"id": "node2", "labels": ["Person"], "properties": {"name": "Bob"}},
                {"id": "node3", "labels": ["Person"], "properties": {"name": "Charlie"}}
            ],
            "relationships": [
                {"id": "edge1", "label": "KNOWS", "start_id": "node1", "end_id": "node2"},
                {"id": "edge2", "label": "KNOWS", "start_id": "node1", "end_id": "node3"}
            ]
        })
        
        # Call the method
        result = await navigator.extract_subgraph(
            center_node_id="node1",
            max_depth=2,
            relationship_types=["KNOWS"],
            traversal_mode=TraversalMode.BREADTH_FIRST,
            node_filter=NodeFilter(labels=["Person"]),
            max_nodes=10
        )
        
        # Check the result
        assert result is not None
        assert result.center_node["id"] == "node1"
        assert len(result.nodes) == 3
        assert len(result.relationships) == 2
        assert result.node_count == 3
        assert result.relationship_count == 2
        
        # Check that the correct query was executed
        executed_query = mock_conn.fetchval.call_args_list[1][0][0]
        assert "cypher('test_graph'" in executed_query
        
        # Ensure Cypher params were used
        params = mock_conn.fetchval.call_args_list[1][0][1]
        assert "MATCH path = (a)-[r:KNOWS*1..2]-(b)" in params
        assert "WHERE id(a) = 'node1'" in params
        assert "ANY(label IN LABELS(b) WHERE label IN ['Person'])" in params
    
    @pytest.mark.asyncio
    async def test_find_similar_nodes(self, navigator, mock_conn):
        """Test finding nodes similar to a given node."""
        # Mock the database response
        mock_conn.fetch.return_value = [
            MagicMock(node=json.dumps({
                "id": "node2", 
                "labels": ["Person"], 
                "properties": {"name": "Bob"}
            }), 
            similarity=json.dumps(0.8)),
            MagicMock(node=json.dumps({
                "id": "node3", 
                "labels": ["Person"], 
                "properties": {"name": "Charlie"}
            }), 
            similarity=json.dumps(0.6))
        ]
        
        # Call the method
        results = await navigator.find_similar_nodes(
            node_id="node1",
            similarity_metric="common_neighbors",
            top_k=3,
            min_similarity=0.5,
            relationship_types=["KNOWS"],
            node_filter=NodeFilter(labels=["Person"])
        )
        
        # Check the results
        assert len(results) == 2
        assert results[0][0]["id"] == "node2"
        assert results[0][1] == 0.8
        assert results[1][0]["id"] == "node3"
        assert results[1][1] == 0.6
        
        # Check that the correct query was executed
        executed_query = mock_conn.fetch.call_args[0][0]
        assert "cypher('test_graph'" in executed_query
        
        # Ensure Cypher params were used
        params = mock_conn.fetch.call_args[0][1]
        assert "MATCH (a)-[r1:KNOWS]-(common)-[r2:KNOWS]-(b)" in params
        assert "WHERE id(a) = 'node1'" in params
        assert "ANY(label IN LABELS(b) WHERE label IN ['Person'])" in params
        assert "ORDER BY commonNeighbors DESC" in params
        assert "LIMIT 3" in params
    
    @pytest.mark.asyncio
    async def test_find_path_with_reasoning(self, navigator, mock_conn):
        """Test finding a path with reasoning capabilities."""
        # Mock the database response
        mock_conn.fetchval.return_value = json.dumps({
            "vertices": [
                {"id": "concept1", "labels": ["Concept"], "properties": {"name": "Climate Change"}},
                {"id": "concept2", "labels": ["Concept"], "properties": {"name": "Extreme Weather"}},
                {"id": "concept3", "labels": ["Concept"], "properties": {"name": "Flooding"}}
            ],
            "edges": [
                {"id": "edge1", "label": "CAUSES", "start_id": "concept1", "end_id": "concept2"},
                {"id": "edge2", "label": "CAUSES", "start_id": "concept2", "end_id": "concept3"}
            ]
        })
        
        # Call the method
        result = await navigator.find_path_with_reasoning(
            start_node_id="concept1",
            end_node_id="concept3",
            reasoning_type="causal",
            max_depth=5,
            relationship_types=["CAUSES", "LEADS_TO"]
        )
        
        # Check the result
        assert result is not None
        assert result.start_node["id"] == "concept1"
        assert result.end_node["id"] == "concept3"
        assert len(result.nodes) == 3
        assert len(result.relationships) == 2
        assert result.length == 2
        assert "explanation" in result.metadata
        assert "causal chain" in result.metadata["explanation"]
        
        # Check that the correct query was executed
        executed_query = mock_conn.fetchval.call_args_list[1][0][0]
        assert "cypher('test_graph'" in executed_query
        
        # Ensure Cypher params were used
        params = mock_conn.fetchval.call_args_list[1][0][1]
        assert "MATCH path = (a)-[r:CAUSES|LEADS_TO*1..5]->(b)" in params
        assert "WHERE id(a) = 'concept1' AND id(b) = 'concept3'" in params
    
    @pytest.mark.asyncio
    async def test_find_context_for_rag(self, navigator, mock_conn):
        """Test finding context for RAG applications."""
        # Mock the database responses
        mock_conn.fetchval.return_value = json.dumps({
            "nodes": [
                {"id": "node1", "labels": ["Document"], "properties": {"name": "Climate Report", "content": "Climate change is causing extreme weather events."}},
                {"id": "node2", "labels": ["Concept"], "properties": {"name": "Climate Change"}}
            ],
            "relationships": [
                {"id": "edge1", "label": "MENTIONS", "start_id": "node1", "end_id": "node2"}
            ]
        })
        
        # Call the method
        context_items = await navigator.find_context_for_rag(
            query="What are the impacts of climate change?",
            relevant_nodes=["node1", "node2"],
            max_results=3,
            strategy="hybrid"
        )
        
        # Check the results
        assert len(context_items) > 0
        assert "text" in context_items[0]
        assert "type" in context_items[0]
        assert "relevance" in context_items[0]
        
        # Context should contain mentioned entities
        assert "Climate Change" in context_items[0]["text"] or "Climate Report" in context_items[0]["text"]
    
    @pytest.mark.asyncio
    async def test_create_graph_navigator(self, mock_asyncpg, mock_pool, mock_conn):
        """Test the factory function to create a graph navigator."""
        # Mock the database connection
        mock_asyncpg.create_pool.return_value = mock_pool
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchval.return_value = True
        
        # Call the factory function
        navigator = await create_graph_navigator(
            connection_string="postgresql://test:test@localhost:5432/testdb",
            graph_name="test_graph"
        )
        
        # Check the navigator
        assert navigator is not None
        assert navigator.initialized is True
        assert navigator.config.graph_name == "test_graph"
        assert navigator.connection_string == "postgresql://test:test@localhost:5432/testdb"