"""
Example of using PostgreSQL-native vector search in the Uno framework.

This module demonstrates how to use the vector search capabilities with
PostgreSQL triggers for automatic vector management. It shows how to:

1. Set up vector search for a table
2. Perform similarity searches
3. Execute combined graph and vector hybrid searches
4. Use RAG capabilities for LLM contexts
"""

import logging
import asyncio
from typing import List, Dict, Any, Optional

from uno.domain.core import Entity
from uno.core.base.respository import Repository
from uno.domain.vector_search import (
    VectorSearchService,
    RAGService,
    VectorQuery,
    HybridQuery,
)
from uno.sql.emitters.vector import (
    VectorSQLEmitter,
    VectorConfig,
    VectorIntegrationEmitter,
)


# Example entity class
class Document(Entity):
    """Example document entity for vector search."""

    title: str
    content: str
    tags: Optional[List[str]] = None
    author: Optional[str] = None


# Example repository for documents
class DocumentRepository(Repository[Document]):
    """Repository for document entities."""

    async def get(self, id: str) -> Optional[Document]:
        """Get a document by ID."""
        # This would normally query the database
        # For example purposes, we'll just return a dummy document
        if id == "doc1":
            return Document(
                id="doc1",
                title="Example Document",
                content="This is an example document for vector search.",
                tags=["example", "vector", "search"],
                author="Uno Framework",
            )
        return None

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = 0,
    ) -> List[Document]:
        """List documents matching filters."""
        # This would normally query the database
        # For example purposes, we'll just return a dummy list
        return [
            Document(
                id="doc1",
                title="Example Document",
                content="This is an example document for vector search.",
                tags=["example", "vector", "search"],
                author="Uno Framework",
            )
        ]


# Example usage of vector search
async def vector_search_example():
    """Demonstrate vector search capabilities."""
    logger = logging.getLogger("vector_example")

    # Set up repositories
    doc_repo = DocumentRepository()

    # Create vector search service
    vector_search = VectorSearchService(
        entity_type=Document,
        table_name="document",
        repository=doc_repo,
        logger=logger,
        # schema defaults to uno_settings.DB_SCHEMA
    )

    # Create RAG service
    rag_service = RAGService(vector_search=vector_search, logger=logger)

    # Perform a simple vector search
    query = VectorQuery(
        query_text="How do I use vector search?",
        limit=5,
        threshold=0.7,
        metric="cosine",
    )

    logger.info("Performing vector search...")
    results = await vector_search.search(query)

    logger.info(f"Found {len(results)} results")
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}: ID={result.id}, Similarity={result.similarity:.4f}")
        if result.entity:
            logger.info(f"  Title: {result.entity.title}")
            logger.info(f"  Content: {result.entity.content[:50]}...")

    # Perform a hybrid search
    hybrid_query = HybridQuery(
        query_text="How do I use vector search with graph databases?",
        limit=5,
        threshold=0.7,
        start_node_type="Document",
        start_filters={"tags": "vector"},
        path_pattern="(n:Document)-[:RELATED_TO]->(end_node:Document)",
    )

    logger.info("Performing hybrid search...")
    hybrid_results = await vector_search.hybrid_search(hybrid_query)

    logger.info(f"Found {len(hybrid_results)} hybrid results")
    for i, result in enumerate(hybrid_results):
        logger.info(f"Result {i+1}: ID={result.id}, Similarity={result.similarity:.4f}")
        if result.entity:
            logger.info(f"  Title: {result.entity.title}")
            logger.info(f"  Content: {result.entity.content[:50]}...")

    # Create a RAG prompt
    system_prompt = (
        "You are a helpful assistant that answers questions about vector search."
    )

    logger.info("Creating RAG prompt...")
    rag_prompt = await rag_service.create_rag_prompt(
        query="How do I implement vector search?",
        system_prompt=system_prompt,
        limit=3,
        threshold=0.7,
    )

    logger.info("RAG Prompt:")
    logger.info(f"System: {rag_prompt['system_prompt']}")
    logger.info(f"User: {rag_prompt['user_prompt']}")


# Example of setting up vector search for a table
def setup_vector_search_example():
    """
    Demonstrate how to set up vector search for a table using SQL emitters.

    This would typically be done during database initialization.
    """
    from sqlalchemy import MetaData, Table, Column, String, Text
    from sqlalchemy.orm import declarative_base

    # Create a sample table definition
    Base = declarative_base()
    metadata = MetaData()

    # Define the document table
    document_table = Table(
        "document",
        metadata,
        Column("id", String(26), primary_key=True),
        Column("title", String(255), nullable=False),
        Column("content", Text, nullable=False),
        Column("author", String(100)),
    )

    # Create vector config
    vector_config = VectorConfig(
        dimensions=1536,  # OpenAI embedding dimensions
        index_type="hnsw",  # Use HNSW index for better performance
        m=16,
        ef_construction=64,
        ef_search=40,
    )

    # Create vector SQL emitter
    vector_emitter = VectorSQLEmitter(
        table=document_table,
        vector_columns=["title", "content"],  # Which columns to use for vectorization
        exclude_columns=["id"],  # Which columns to exclude
        vector_config=vector_config,
    )

    # Generate SQL statements
    statements = vector_emitter.generate_sql()

    print(f"Generated {len(statements)} SQL statements for vector search setup")
    for stmt in statements:
        print(f"- {stmt.name}: {stmt.type}")

    # Create vector integration emitter to integrate with graph database
    integration_emitter = VectorIntegrationEmitter(
        table=document_table, vector_config=vector_config
    )

    # Generate integration SQL statements
    integration_statements = integration_emitter.generate_sql()

    print(
        f"Generated {len(integration_statements)} SQL statements for graph integration"
    )
    for stmt in integration_statements:
        print(f"- {stmt.name}: {stmt.type}")


# Custom RAG implementation example
class DocumentRAG(RAGService[Document]):
    """Custom RAG service for Document entities."""

    def format_context_for_prompt(self, entities: List[Document]) -> str:
        """
        Format document entities as context for an LLM prompt.

        Args:
            entities: The document entities

        Returns:
            Formatted context string
        """
        context_parts = []

        for i, doc in enumerate(entities):
            context_text = f"[Document {i+1}]\n"
            context_text += f"Title: {doc.title}\n"
            context_text += f"Content: {doc.content}\n"

            if doc.author:
                context_text += f"Author: {doc.author}\n"

            if doc.tags:
                context_text += f"Tags: {', '.join(doc.tags)}\n"

            context_parts.append(context_text)

        return "\n---\n".join(context_parts)


# Run the examples
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Show how to set up vector search
    setup_vector_search_example()

    # Run the async examples
    asyncio.run(vector_search_example())
