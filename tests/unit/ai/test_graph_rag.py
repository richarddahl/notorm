"""
Tests for Graph-Enhanced RAG functionality.

This module contains tests for the GraphRAGService class that
integrates knowledge graphs with vector search for enhanced
retrieval-augmented generation.
"""

import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any, Optional

from uno.ai.graph_integration.graph_rag import (
    GraphRAGService,
    GraphContext,
    create_graph_rag_service
)
from uno.domain.core import Entity
from uno.domain.vector_search import VectorSearchService, VectorSearchResult, RAGService
from uno.ai.graph_integration.graph_navigator import (
    GraphNavigator,
    PathResult,
    SubgraphResult
)
from uno.ai.graph_integration.knowledge_constructor import KnowledgeConstructor


class TestEntity(Entity):
    """Test entity for testing."""
    id: str
    name: str
    description: str


class TestGraphRAGService:
    """Tests for the GraphRAGService class."""
    
    @pytest.fixture
    def mock_vector_search(self):
        """Create a mock vector search service."""
        mock = MagicMock()
        mock.search = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_graph_navigator(self):
        """Create a mock graph navigator."""
        mock = MagicMock()
        mock.find_context_for_rag = AsyncMock()
        mock.find_shortest_path = AsyncMock()
        mock.find_path_with_reasoning = AsyncMock()
        mock.extract_subgraph = AsyncMock()
        return mock
    
    @pytest.fixture
    def mock_knowledge_constructor(self):
        """Create a mock knowledge constructor."""
        mock = MagicMock()
        mock.query_graph = AsyncMock()
        return mock
    
    @pytest.fixture
    def graph_rag_service(self, mock_vector_search, mock_graph_navigator, mock_knowledge_constructor):
        """Create a GraphRAGService instance for testing."""
        return GraphRAGService(
            vector_search=mock_vector_search,
            graph_navigator=mock_graph_navigator,
            knowledge_constructor=mock_knowledge_constructor
        )
    
    @pytest.fixture
    def mock_base_rag(self):
        """Mock the base RAG service."""
        with patch("uno.domain.vector_search.RAGService") as mock:
            instance = MagicMock()
            instance.retrieve_context = AsyncMock()
            instance.format_context_for_prompt = MagicMock()
            instance.create_rag_prompt = AsyncMock()
            mock.return_value = instance
            yield instance
    
    @pytest.mark.asyncio
    async def test_extract_relevant_nodes(self, graph_rag_service, mock_vector_search):
        """Test extracting relevant nodes based on vector search."""
        # Set up mock return value
        mock_vector_search.search.return_value = [
            VectorSearchResult(id="node1", similarity=0.9),
            VectorSearchResult(id="node2", similarity=0.8),
            VectorSearchResult(id="node3", similarity=0.7)
        ]
        
        # Call the method
        result = await graph_rag_service.extract_relevant_nodes(
            query="test query",
            limit=3,
            threshold=0.7
        )
        
        # Verify the result
        assert result == ["node1", "node2", "node3"]
        
        # Check that vector search was called correctly
        mock_vector_search.search.assert_called_once()
        args = mock_vector_search.search.call_args[0][0]
        assert args.query_text == "test query"
        assert args.limit == 3
        assert args.threshold == 0.7
    
    @pytest.mark.asyncio
    async def test_retrieve_graph_context(self, graph_rag_service, mock_vector_search, mock_graph_navigator):
        """Test retrieving graph context for a query."""
        # Set up mock returns
        mock_vector_search.search.return_value = [
            VectorSearchResult(id="node1", similarity=0.9),
            VectorSearchResult(id="node2", similarity=0.8)
        ]
        
        mock_graph_navigator.find_context_for_rag.return_value = [
            {
                "type": "path",
                "text": "Path from A to B",
                "relevance": 0.9,
                "source": "graph_path",
                "path_data": {"nodes": [{"id": "A"}, {"id": "B"}]}
            },
            {
                "type": "subgraph",
                "text": "Subgraph around A",
                "relevance": 0.8,
                "source": "graph_subgraph",
                "subgraph_data": {"center_node": {"id": "A"}}
            }
        ]
        
        # Call the method
        result = await graph_rag_service.retrieve_graph_context(
            query="test query",
            limit=5,
            threshold=0.7,
            max_depth=3,
            strategy="hybrid"
        )
        
        # Verify the result
        assert len(result) == 2
        assert isinstance(result[0], GraphContext)
        assert result[0].context_type == "path"
        assert result[0].text == "Path from A to B"
        assert result[0].relevance == 0.9
        assert result[0].source == "graph_path"
        
        # Check that the methods were called correctly
        mock_vector_search.search.assert_called_once()
        mock_graph_navigator.find_context_for_rag.assert_called_once_with(
            query="test query",
            relevant_nodes=["node1", "node2"],
            max_results=5,
            strategy="hybrid"
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_path_context(self, graph_rag_service, mock_graph_navigator):
        """Test retrieving context from a path between nodes."""
        # Create a mock path result
        mock_path = MagicMock(spec=PathResult)
        mock_path.nodes = [
            {"id": "node1", "properties": {"name": "Node A"}},
            {"id": "node2", "properties": {"name": "Node B"}}
        ]
        mock_path.relationships = [
            {"id": "rel1", "label": "CONNECTED_TO", "start_id": "node1", "end_id": "node2"}
        ]
        mock_path.start_node = mock_path.nodes[0]
        mock_path.end_node = mock_path.nodes[1]
        mock_path.length = 1
        mock_path.metadata = {}
        mock_path.dict = MagicMock(return_value={"nodes": mock_path.nodes, "relationships": mock_path.relationships})
        
        # Set up mock return values
        mock_graph_navigator.find_shortest_path.return_value = mock_path
        
        # Call the method
        result = await graph_rag_service.retrieve_path_context(
            start_node_id="node1",
            end_node_id="node2",
            max_depth=3,
            relationship_types=["CONNECTED_TO"]
        )
        
        # Verify the result
        assert isinstance(result, GraphContext)
        assert result.context_type == "path"
        assert "Path from Node A to Node B" in result.text
        assert result.relevance == 1.0
        assert result.source == "graph_path"
        
        # Check that the correct method was called
        mock_graph_navigator.find_shortest_path.assert_called_once_with(
            start_node_id="node1",
            end_node_id="node2",
            max_depth=3,
            relationship_types=["CONNECTED_TO"]
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_path_context_with_reasoning(self, graph_rag_service, mock_graph_navigator):
        """Test retrieving context from a path with reasoning."""
        # Create a mock path result with explanation
        mock_path = MagicMock(spec=PathResult)
        mock_path.nodes = [
            {"id": "node1", "properties": {"name": "Climate Change"}},
            {"id": "node2", "properties": {"name": "Extreme Weather"}},
            {"id": "node3", "properties": {"name": "Flooding"}}
        ]
        mock_path.relationships = [
            {"id": "rel1", "label": "CAUSES", "start_id": "node1", "end_id": "node2"},
            {"id": "rel2", "label": "CAUSES", "start_id": "node2", "end_id": "node3"}
        ]
        mock_path.start_node = mock_path.nodes[0]
        mock_path.end_node = mock_path.nodes[2]
        mock_path.length = 2
        mock_path.metadata = {
            "explanation": "This path represents a causal chain of events."
        }
        mock_path.dict = MagicMock(return_value={"nodes": mock_path.nodes, "relationships": mock_path.relationships})
        
        # Set up mock return values
        mock_graph_navigator.find_path_with_reasoning.return_value = mock_path
        
        # Call the method
        result = await graph_rag_service.retrieve_path_context(
            start_node_id="node1",
            end_node_id="node3",
            max_depth=3,
            relationship_types=["CAUSES"],
            reasoning_type="causal"
        )
        
        # Verify the result
        assert isinstance(result, GraphContext)
        assert result.context_type == "path"
        assert "Path from Climate Change to Flooding" in result.text
        assert "Explanation" in result.text
        assert result.relevance == 1.0
        assert result.source == "graph_path"
        
        # Check that the correct method was called
        mock_graph_navigator.find_path_with_reasoning.assert_called_once_with(
            start_node_id="node1",
            end_node_id="node3",
            reasoning_type="causal",
            max_depth=3,
            relationship_types=["CAUSES"]
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_subgraph_context(self, graph_rag_service, mock_graph_navigator):
        """Test retrieving context from a subgraph."""
        # Create a mock subgraph result
        mock_subgraph = MagicMock(spec=SubgraphResult)
        mock_subgraph.center_node = {"id": "node1", "properties": {"name": "Center Node"}}
        mock_subgraph.nodes = [
            mock_subgraph.center_node,
            {"id": "node2", "properties": {"name": "Related Node A"}},
            {"id": "node3", "properties": {"name": "Related Node B"}}
        ]
        mock_subgraph.relationships = [
            {"id": "rel1", "label": "CONNECTED_TO", "start_id": "node1", "end_id": "node2"},
            {"id": "rel2", "label": "CONNECTED_TO", "start_id": "node1", "end_id": "node3"}
        ]
        mock_subgraph.node_count = 3
        mock_subgraph.relationship_count = 2
        mock_subgraph.dict = MagicMock(return_value={
            "center_node": mock_subgraph.center_node,
            "nodes": mock_subgraph.nodes,
            "relationships": mock_subgraph.relationships
        })
        
        # Set up mock return values
        mock_graph_navigator.extract_subgraph.return_value = mock_subgraph
        
        # Call the method
        result = await graph_rag_service.retrieve_subgraph_context(
            center_node_id="node1",
            max_depth=2,
            max_nodes=10,
            relationship_types=["CONNECTED_TO"]
        )
        
        # Verify the result
        assert isinstance(result, GraphContext)
        assert result.context_type == "subgraph"
        assert "Knowledge graph centered on Center Node" in result.text
        assert result.relevance == 0.9
        assert result.source == "graph_subgraph"
        
        # Check that the correct method was called
        mock_graph_navigator.extract_subgraph.assert_called_once_with(
            center_node_id="node1",
            max_depth=2,
            max_nodes=10,
            relationship_types=["CONNECTED_TO"]
        )
    
    @pytest.mark.asyncio
    async def test_retrieve_knowledge_context(self, graph_rag_service, mock_knowledge_constructor):
        """Test retrieving context from knowledge graph."""
        # Set up mock return values
        mock_knowledge_constructor.query_graph.return_value = [
            {
                "id": "node1",
                "labels": ["Organization"],
                "properties": {"name": "Acme Corp", "industry": "Technology"}
            },
            {
                "id": "node2",
                "labels": ["Person"],
                "properties": {"name": "John Smith", "title": "CEO"}
            }
        ]
        
        # Call the method
        result = await graph_rag_service.retrieve_knowledge_context(
            query="Acme Corp CEO",
            limit=5
        )
        
        # Verify the result
        assert len(result) == 2
        assert all(isinstance(item, GraphContext) for item in result)
        assert result[0].context_type == "knowledge"
        assert "Organization: Acme Corp" in result[0].text
        assert result[0].relevance == 0.8
        assert result[0].source == "knowledge_graph"
        
        # Check that the correct method was called
        mock_knowledge_constructor.query_graph.assert_called_once()
        args = mock_knowledge_constructor.query_graph.call_args[0][0]
        assert "Acme Corp CEO" in args
        assert "LIMIT 5" in args
    
    def test_format_context_for_prompt(self, graph_rag_service):
        """Test formatting graph contexts for a prompt."""
        # Create test contexts
        contexts = [
            GraphContext(
                context_type="path",
                text="Path from A to B:\n- A CAUSES B",
                relevance=0.9,
                source="graph_path"
            ),
            GraphContext(
                context_type="subgraph",
                text="Knowledge graph centered on A:\nFocus Entity: A\n- property: value",
                relevance=0.8,
                source="graph_subgraph"
            ),
            GraphContext(
                context_type="knowledge",
                text="Organization: Acme Corp\n- industry: Technology",
                relevance=0.7,
                source="knowledge_graph"
            )
        ]
        
        # Format contexts
        result = graph_rag_service.format_context_for_prompt(contexts)
        
        # Verify result
        assert "[1]" in result  # First context
        assert "[2]" in result  # Second context
        assert "[3]" in result  # Third context
        assert "Path from A to B" in result
        assert "Knowledge graph centered on A" in result
        assert "Organization: Acme Corp" in result
        
        # Contexts should be ordered by relevance
        first_pos = result.find("[1]")
        second_pos = result.find("[2]")
        third_pos = result.find("[3]")
        
        assert first_pos < second_pos < third_pos
        assert "Path from A to B" in result[first_pos:second_pos]  # Highest relevance
    
    @pytest.mark.asyncio
    async def test_create_graph_enhanced_prompt(self, graph_rag_service, mock_vector_search, mock_graph_navigator):
        """Test creating a RAG prompt with graph-enhanced context."""
        # Set up mocks for retrieving graph context
        mock_vector_search.search.return_value = [
            VectorSearchResult(id="node1", similarity=0.9),
            VectorSearchResult(id="node2", similarity=0.8)
        ]
        
        mock_graph_navigator.find_context_for_rag.return_value = [
            {
                "type": "path",
                "text": "Path from A to B:\n- A CAUSES B",
                "relevance": 0.9,
                "source": "graph_path"
            },
            {
                "type": "subgraph",
                "text": "Knowledge graph centered on A:\nFocus Entity: A\n- property: value",
                "relevance": 0.8,
                "source": "graph_subgraph"
            }
        ]
        
        # Call the method
        result = await graph_rag_service.create_graph_enhanced_prompt(
            query="test query",
            system_prompt="You are a helpful assistant",
            limit=5,
            threshold=0.7,
            max_depth=3
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert "system_prompt" in result
        assert "user_prompt" in result
        assert result["system_prompt"] == "You are a helpful assistant"
        assert "following context from a knowledge graph" in result["user_prompt"]
        assert "Path from A to B" in result["user_prompt"]
        assert "Knowledge graph centered on A" in result["user_prompt"]
        assert "My question is: test query" in result["user_prompt"]
    
    @pytest.mark.asyncio
    async def test_create_graph_enhanced_prompt_fallback(self, graph_rag_service, mock_vector_search, mock_graph_navigator, mock_base_rag):
        """Test fallback to standard RAG when no graph contexts are found."""
        # Set up mocks for empty graph context
        mock_vector_search.search.return_value = [
            VectorSearchResult(id="node1", similarity=0.9),
            VectorSearchResult(id="node2", similarity=0.8)
        ]
        
        mock_graph_navigator.find_context_for_rag.return_value = []
        
        # Set up mock for base RAG
        mock_base_rag.create_rag_prompt.return_value = {
            "system_prompt": "You are a helpful assistant",
            "user_prompt": "Standard RAG prompt"
        }
        
        # Replace the base_rag with our mock
        graph_rag_service.base_rag = mock_base_rag
        
        # Call the method
        result = await graph_rag_service.create_graph_enhanced_prompt(
            query="test query",
            system_prompt="You are a helpful assistant",
            limit=5,
            threshold=0.7,
            max_depth=3
        )
        
        # Verify the result falls back to standard RAG
        assert result["system_prompt"] == "You are a helpful assistant"
        assert result["user_prompt"] == "Standard RAG prompt"
        
        # Check that base RAG was called
        mock_base_rag.create_rag_prompt.assert_called_once_with(
            query="test query",
            system_prompt="You are a helpful assistant",
            limit=5,
            threshold=0.7
        )
    
    @pytest.mark.asyncio
    async def test_create_hybrid_rag_prompt(self, graph_rag_service, mock_vector_search, mock_graph_navigator, mock_base_rag):
        """Test creating a hybrid RAG prompt with both vector and graph context."""
        # Set up mocks for vector context
        vector_entity = TestEntity(id="node1", name="Test Entity", description="A test entity")
        mock_base_rag.retrieve_context.return_value = ([vector_entity], [])
        mock_base_rag.format_context_for_prompt.return_value = "Vector context for Test Entity"
        
        # Set up mocks for graph context
        mock_vector_search.search.return_value = [
            VectorSearchResult(id="node1", similarity=0.9),
            VectorSearchResult(id="node2", similarity=0.8)
        ]
        
        mock_graph_navigator.find_context_for_rag.return_value = [
            {
                "type": "path",
                "text": "Path from A to B",
                "relevance": 0.9,
                "source": "graph_path"
            }
        ]
        
        # Replace the base_rag with our mock
        graph_rag_service.base_rag = mock_base_rag
        
        # Call the method
        result = await graph_rag_service.create_hybrid_rag_prompt(
            query="test query",
            system_prompt="You are a helpful assistant",
            vector_limit=3,
            graph_limit=3,
            threshold=0.7,
            max_depth=3
        )
        
        # Verify the result
        assert isinstance(result, dict)
        assert "system_prompt" in result
        assert "user_prompt" in result
        assert result["system_prompt"] == "You are a helpful assistant"
        assert "VECTOR SEARCH RESULTS" in result["user_prompt"]
        assert "KNOWLEDGE GRAPH CONTEXT" in result["user_prompt"]
        assert "Vector context for Test Entity" in result["user_prompt"]
        assert "Path from A to B" in result["user_prompt"]
        assert "My question is: test query" in result["user_prompt"]
        
        # Check that methods were called correctly
        mock_base_rag.retrieve_context.assert_called_once_with("test query", 3, 0.7)
        mock_base_rag.format_context_for_prompt.assert_called_once_with([vector_entity])
    
    @pytest.mark.asyncio
    async def test_create_graph_rag_service(self):
        """Test the factory function for creating a GraphRAGService."""
        # Mock the required components
        with patch("uno.domain.vector_search.VectorSearchService") as mock_vector_search:
            with patch("uno.ai.graph_integration.graph_navigator.create_graph_navigator") as mock_create_navigator:
                with patch("uno.ai.graph_integration.knowledge_constructor.create_knowledge_constructor") as mock_create_constructor:
                    # Set up return values
                    mock_vector_search.return_value = MagicMock()
                    mock_create_navigator.return_value = MagicMock()
                    mock_create_constructor.return_value = MagicMock()
                    
                    # Call the factory function
                    service = await create_graph_rag_service(
                        connection_string="postgresql://test:test@localhost:5432/testdb",
                        entity_type=TestEntity,
                        table_name="test_table",
                        graph_name="test_graph"
                    )
                    
                    # Verify that the right components were created
                    assert isinstance(service, GraphRAGService)
                    
                    # Check that the vector search service was created correctly
                    mock_vector_search.assert_called_once_with(
                        entity_type=TestEntity,
                        table_name="test_table",
                        logger=None
                    )
                    
                    # Check that the graph navigator was created correctly
                    mock_create_navigator.assert_called_once_with(
                        connection_string="postgresql://test:test@localhost:5432/testdb",
                        graph_name="test_graph",
                        logger=None
                    )
                    
                    # Check that the knowledge constructor was created correctly
                    mock_create_constructor.assert_called_once_with(
                        connection_string="postgresql://test:test@localhost:5432/testdb",
                        graph_name="test_graph",
                        logger=None
                    )