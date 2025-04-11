"""Vector search module for Uno framework.

This module provides vector search capabilities using PostgreSQL's pgvector extension,
including similarity search, RAG (Retrieval-Augmented Generation), and hybrid search
combining vector similarity with graph traversal.
"""

from uno.vector_search.endpoints import router
import uno.domain.vector_search
import uno.sql.emitters.vector
import uno.dependencies.vector_interfaces 
import uno.dependencies.vector_provider

__all__ = [
    "router",
    "vector_search",
    "vector_interfaces",
    "vector_provider"
]