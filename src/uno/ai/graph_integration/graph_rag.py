"""
Graph-enhanced Retrieval-Augmented Generation (RAG) for Uno framework.

This module integrates Knowledge Graph capabilities with vector search for
enhanced RAG, providing richer context through relationship awareness and
graph traversal.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, TypeVar, Type, Generic, Tuple, Union

from pydantic import BaseModel

from uno.domain.core import Entity
from uno.domain.vector_search import RAGService, VectorSearchService, VectorQuery
from uno.ai.graph_integration.graph_navigator import (
    GraphNavigator,
    PathResult,
    SubgraphResult,
)
from uno.ai.graph_integration.knowledge_constructor import KnowledgeConstructor

T = TypeVar("T", bound=Entity)


class GraphContext(BaseModel):
    """
    Graph-derived context for RAG.

    Attributes:
        context_type: Type of graph context (path, subgraph, etc.)
        text: Formatted text representation of the context
        relevance: Calculated relevance score (0-1)
        source: Source of the context (node, path, subgraph)
        metadata: Additional metadata about the context
    """

    context_type: str
    text: str
    relevance: float
    source: str
    metadata: Dict[str, Any] = {}


class GraphRAGService(Generic[T]):
    """
    Graph-enhanced Retrieval-Augmented Generation service.

    This service combines vector search with graph traversal for enhanced context
    retrieval, providing richer information for LLM interactions by leveraging
    relationships between entities.
    """

    def __init__(
        self,
        vector_search: VectorSearchService[T],
        graph_navigator: GraphNavigator,
        knowledge_constructor: Optional[KnowledgeConstructor] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize Graph RAG service.

        Args:
            vector_search: Vector search service for semantic retrieval
            graph_navigator: Graph navigator for relationship traversal
            knowledge_constructor: Optional knowledge constructor for text processing
            logger: Optional logger for diagnostics
        """
        self.vector_search = vector_search
        self.graph_navigator = graph_navigator
        self.knowledge_constructor = knowledge_constructor
        self.logger = logger or logging.getLogger(__name__)

        # Create standard RAG service as base implementation
        self.base_rag = RAGService(vector_search)

    async def extract_relevant_nodes(
        self, query: str, limit: int = 5, threshold: float = 0.7
    ) -> List[str]:
        """
        Extract relevant node IDs based on semantic similarity to query.

        Args:
            query: The query text
            limit: Maximum number of nodes to extract
            threshold: Minimum similarity threshold

        Returns:
            List of relevant node IDs
        """
        # Use vector search to find semantically relevant nodes
        search_query = VectorQuery(query_text=query, limit=limit, threshold=threshold)

        search_results = await self.vector_search.search(search_query)

        # Extract entity IDs from results
        node_ids = [result.id for result in search_results]

        return node_ids

    async def retrieve_graph_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        strategy: str = "hybrid",
    ) -> List[GraphContext]:
        """
        Retrieve graph-based context for a query.

        This method combines vector search with graph traversal to find
        context that includes relationship information.

        Args:
            query: The query text
            limit: Maximum number of context items to retrieve
            threshold: Minimum similarity threshold for vector search
            max_depth: Maximum graph traversal depth
            relationship_types: Types of relationships to traverse
            strategy: Context retrieval strategy (hybrid, path, subgraph)

        Returns:
            List of graph context items
        """
        # Extract relevant nodes using vector search
        relevant_nodes = await self.extract_relevant_nodes(query, limit, threshold)

        if not relevant_nodes:
            self.logger.warning(f"No relevant nodes found for query: {query}")
            return []

        # Retrieve context from graph database
        context_items = await self.graph_navigator.find_context_for_rag(
            query=query,
            relevant_nodes=relevant_nodes,
            max_results=limit,
            strategy=strategy,
        )

        # Convert to GraphContext objects
        graph_contexts = []

        for item in context_items:
            graph_context = GraphContext(
                context_type=item["type"],
                text=item["text"],
                relevance=item["relevance"],
                source=item["source"],
                metadata={
                    key: value
                    for key, value in item.items()
                    if key not in ["type", "text", "relevance", "source"]
                },
            )
            graph_contexts.append(graph_context)

        return graph_contexts

    async def retrieve_path_context(
        self,
        start_node_id: str,
        end_node_id: str,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        reasoning_type: Optional[str] = None,
    ) -> Optional[GraphContext]:
        """
        Retrieve context from a path between two nodes.

        Args:
            start_node_id: ID of the start node
            end_node_id: ID of the end node
            max_depth: Maximum path depth
            relationship_types: Types of relationships to traverse
            reasoning_type: Optional type of reasoning for the path

        Returns:
            Graph context from the path if found, None otherwise
        """
        # Find path between nodes
        if reasoning_type:
            path = await self.graph_navigator.find_path_with_reasoning(
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                reasoning_type=reasoning_type,
                max_depth=max_depth,
                relationship_types=relationship_types,
            )
        else:
            path = await self.graph_navigator.find_shortest_path(
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                max_depth=max_depth,
                relationship_types=relationship_types,
            )

        if not path:
            return None

        # Format path as context
        text = self._format_path_for_context(path)

        return GraphContext(
            context_type="path",
            text=text,
            relevance=1.0,
            source="graph_path",
            metadata={"path": path.dict(), "reasoning_type": reasoning_type},
        )

    async def retrieve_subgraph_context(
        self,
        center_node_id: str,
        max_depth: int = 2,
        max_nodes: int = 10,
        relationship_types: Optional[List[str]] = None,
    ) -> Optional[GraphContext]:
        """
        Retrieve context from a subgraph centered on a node.

        Args:
            center_node_id: ID of the center node
            max_depth: Maximum traversal depth
            max_nodes: Maximum number of nodes to include
            relationship_types: Types of relationships to traverse

        Returns:
            Graph context from the subgraph if found, None otherwise
        """
        # Extract subgraph
        subgraph = await self.graph_navigator.extract_subgraph(
            center_node_id=center_node_id,
            max_depth=max_depth,
            max_nodes=max_nodes,
            relationship_types=relationship_types,
        )

        if not subgraph:
            return None

        # Format subgraph as context
        text = self._format_subgraph_for_context(subgraph)

        return GraphContext(
            context_type="subgraph",
            text=text,
            relevance=0.9,
            source="graph_subgraph",
            metadata={"subgraph": subgraph.dict()},
        )

    async def retrieve_knowledge_context(
        self, query: str, limit: int = 5
    ) -> List[GraphContext]:
        """
        Retrieve context from knowledge graph based on query.

        Args:
            query: The query text
            limit: Maximum number of results to return

        Returns:
            List of graph context items from knowledge graph
        """
        if not self.knowledge_constructor:
            self.logger.warning("Knowledge constructor not available")
            return []

        # Execute a Cypher query to find related knowledge
        cypher_query = f"""
        MATCH (n)
        WHERE n.properties->>'text' CONTAINS '{query}'
        RETURN n
        LIMIT {limit}
        """

        results = await self.knowledge_constructor.query_graph(cypher_query)

        context_items = []

        for i, result in enumerate(results):
            # Format node as context
            text = self._format_knowledge_node_for_context(result)

            context = GraphContext(
                context_type="knowledge",
                text=text,
                relevance=0.8 - (i * 0.05),  # Higher relevance for earlier results
                source="knowledge_graph",
                metadata={"node": result},
            )

            context_items.append(context)

        return context_items

    def _format_path_for_context(self, path: PathResult) -> str:
        """Format a path as context text."""
        nodes = path.nodes
        relationships = path.relationships

        if not nodes or len(nodes) < 2:
            return "No valid path found."

        start_name = (
            nodes[0].get("properties", {}).get("name", nodes[0].get("id", "Unknown"))
        )
        end_name = (
            nodes[-1].get("properties", {}).get("name", nodes[-1].get("id", "Unknown"))
        )

        text = f"Path from {start_name} to {end_name}:\n\n"

        # Add detailed path steps
        for i, rel in enumerate(relationships):
            start_node = nodes[i]
            end_node = nodes[i + 1]

            start_name = start_node.get("properties", {}).get(
                "name", start_node.get("id", "Unknown")
            )
            end_name = end_node.get("properties", {}).get(
                "name", end_node.get("id", "Unknown")
            )
            rel_type = rel.get("label", "related to")

            text += f"- {start_name} {rel_type} {end_name}\n"

        # Add explanation if available
        if path.metadata and "explanation" in path.metadata:
            text += f"\nExplanation:\n{path.metadata['explanation']}\n"

        return text

    def _format_subgraph_for_context(self, subgraph: SubgraphResult) -> str:
        """Format a subgraph as context text."""
        center_node = subgraph.center_node
        nodes = subgraph.nodes
        relationships = subgraph.relationships

        center_name = center_node.get("properties", {}).get(
            "name", center_node.get("id", "Unknown")
        )

        text = f"Knowledge graph centered on {center_name}:\n\n"

        # Add center node details
        text += f"Focus Entity: {center_name}\n"
        for prop, value in center_node.get("properties", {}).items():
            if prop not in ["embedding", "id", "created_at"]:
                text += f"- {prop}: {value}\n"

        text += "\nRelated Information:\n"

        # Create a map of node IDs to nodes
        node_map = {node.get("id"): node for node in nodes}

        # Add relationship information
        for rel in relationships:
            if rel.get("start_id") == center_node.get("id"):
                # Outgoing relationship
                end_node = node_map.get(rel.get("end_id"))
                if end_node:
                    end_name = end_node.get("properties", {}).get(
                        "name", end_node.get("id", "Unknown")
                    )
                    rel_type = rel.get("label", "related to")
                    text += f"- {center_name} {rel_type} {end_name}\n"

            elif rel.get("end_id") == center_node.get("id"):
                # Incoming relationship
                start_node = node_map.get(rel.get("start_id"))
                if start_node:
                    start_name = start_node.get("properties", {}).get(
                        "name", start_node.get("id", "Unknown")
                    )
                    rel_type = rel.get("label", "related to")
                    text += f"- {start_name} {rel_type} {center_name}\n"

        return text

    def _format_knowledge_node_for_context(self, node: Dict[str, Any]) -> str:
        """Format a knowledge graph node as context text."""
        node_type = node.get("labels", ["Unknown"])[0] if "labels" in node else "Entity"
        props = node.get("properties", {})

        text = f"{node_type}: "

        # Add name or ID
        if "name" in props:
            text += f"{props['name']}\n"
        elif "text" in props:
            text += f"{props['text']}\n"
        else:
            text += f"ID: {node.get('id', 'Unknown')}\n"

        # Add properties
        for prop, value in props.items():
            if prop not in ["id", "name", "text", "embedding", "created_at"]:
                text += f"- {prop}: {value}\n"

        return text

    def format_context_for_prompt(self, contexts: List[GraphContext]) -> str:
        """
        Format graph contexts as context for an LLM prompt.

        Args:
            contexts: List of graph contexts

        Returns:
            Formatted context string
        """
        if not contexts:
            return "No relevant context found."

        # Sort contexts by relevance (descending)
        sorted_contexts = sorted(contexts, key=lambda c: c.relevance, reverse=True)

        # Format each context
        context_parts = []

        for i, context in enumerate(sorted_contexts):
            # Format as a numbered context item
            context_text = f"[{i+1}] {context.text}"
            context_parts.append(context_text)

        # Join all context items with separators
        return "\n---\n".join(context_parts)

    async def create_graph_enhanced_prompt(
        self,
        query: str,
        system_prompt: str,
        limit: int = 5,
        threshold: float = 0.7,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
        strategy: str = "hybrid",
    ) -> Dict[str, str]:
        """
        Create a RAG prompt with graph-enhanced context.

        Args:
            query: The user's query
            system_prompt: The system prompt
            limit: Maximum number of context items to retrieve
            threshold: Minimum similarity threshold
            max_depth: Maximum graph traversal depth
            relationship_types: Types of relationships to traverse
            strategy: Context retrieval strategy (hybrid, path, subgraph)

        Returns:
            Dictionary with system_prompt and user_prompt keys
        """
        # Retrieve graph-based context
        graph_contexts = await self.retrieve_graph_context(
            query=query,
            limit=limit,
            threshold=threshold,
            max_depth=max_depth,
            relationship_types=relationship_types,
            strategy=strategy,
        )

        # If no graph contexts found, fall back to standard RAG
        if not graph_contexts:
            self.logger.info("No graph contexts found, falling back to standard RAG")
            return await self.base_rag.create_rag_prompt(
                query=query,
                system_prompt=system_prompt,
                limit=limit,
                threshold=threshold,
            )

        # Format context
        context = self.format_context_for_prompt(graph_contexts)

        # Create user prompt with context and query
        user_prompt = f"""I need information based on the following context from a knowledge graph:

{context}

My question is: {query}"""

        return {"system_prompt": system_prompt, "user_prompt": user_prompt}

    async def create_hybrid_rag_prompt(
        self,
        query: str,
        system_prompt: str,
        vector_limit: int = 3,
        graph_limit: int = 3,
        threshold: float = 0.7,
        max_depth: int = 3,
        relationship_types: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Create a RAG prompt combining vector search and graph-based context.

        This method retrieves context from both vector search and graph traversal,
        combining them for a more comprehensive prompt.

        Args:
            query: The user's query
            system_prompt: The system prompt
            vector_limit: Maximum number of vector results to include
            graph_limit: Maximum number of graph results to include
            threshold: Minimum similarity threshold
            max_depth: Maximum graph traversal depth
            relationship_types: Types of relationships to traverse

        Returns:
            Dictionary with system_prompt and user_prompt keys
        """
        # Retrieve context from both sources concurrently
        vector_task = asyncio.create_task(
            self.base_rag.retrieve_context(query, vector_limit, threshold)
        )

        graph_task = asyncio.create_task(
            self.retrieve_graph_context(
                query=query,
                limit=graph_limit,
                threshold=threshold,
                max_depth=max_depth,
                relationship_types=relationship_types,
            )
        )

        # Wait for both to complete
        vector_results, _ = await vector_task
        graph_contexts = await graph_task

        # Format vector context
        vector_context = self.base_rag.format_context_for_prompt(vector_results)

        # Format graph context
        graph_context = self.format_context_for_prompt(graph_contexts)

        # Create user prompt with both contexts
        user_prompt = f"""I need information based on the following contextual data:

VECTOR SEARCH RESULTS:
{vector_context}

KNOWLEDGE GRAPH CONTEXT:
{graph_context}

My question is: {query}"""

        return {"system_prompt": system_prompt, "user_prompt": user_prompt}


async def create_graph_rag_service(
    connection_string: str,
    entity_type: Type[T],
    table_name: str,
    graph_name: str = "graph",
    logger: Optional[logging.Logger] = None,
) -> GraphRAGService[T]:
    """
    Create a graph RAG service with initialized components.

    Args:
        connection_string: Database connection string
        entity_type: Entity type for vector search
        table_name: Table name for vector embeddings
        graph_name: Name of the graph in Apache AGE
        logger: Optional logger instance

    Returns:
        Initialized GraphRAGService
    """
    from uno.core.base.respository import Repository
    from uno.domain.vector_search import VectorSearchService
    from uno.ai.graph_integration.graph_navigator import create_graph_navigator
    from uno.ai.graph_integration.knowledge_constructor import (
        create_knowledge_constructor,
    )

    # Create vector search service
    vector_search = VectorSearchService(
        entity_type=entity_type, table_name=table_name, logger=logger
    )

    # Create graph navigator
    graph_navigator = await create_graph_navigator(
        connection_string=connection_string, graph_name=graph_name, logger=logger
    )

    # Create knowledge constructor
    knowledge_constructor = await create_knowledge_constructor(
        connection_string=connection_string, graph_name=graph_name, logger=logger
    )

    # Create and return the graph RAG service
    return GraphRAGService(
        vector_search=vector_search,
        graph_navigator=graph_navigator,
        knowledge_constructor=knowledge_constructor,
        logger=logger,
    )
