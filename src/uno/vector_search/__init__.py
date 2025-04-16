"""Vector search module for Uno framework.

This module provides vector search capabilities using PostgreSQL's pgvector extension,
including similarity search, RAG (Retrieval-Augmented Generation), and hybrid search
combining vector similarity with graph traversal.
"""

from uno.vector_search.domain_endpoints import vector_search_router as router
from uno.vector_search.domain_provider import (
    configure_vector_search_dependencies,
    get_index_service,
    get_embedding_service,
    get_search_service,
    get_rag_service,
    get_vector_search_service
)
import uno.domain.vector_search
import uno.sql.emitters.vector
import uno.dependencies.vector_interfaces 
import uno.dependencies.vector_provider

__all__ = [
    "router",
    "configure_vector_search_dependencies",
    "get_index_service",
    "get_embedding_service",
    "get_search_service",
    "get_rag_service",
    "get_vector_search_service"
]