"""
Semantic search module for Uno framework.

This module provides semantic search capabilities using vector embeddings,
allowing for meaning-based searching beyond simple keyword matching.
"""

from uno.ai.semantic_search.engine import SemanticSearchEngine
from uno.ai.semantic_search.api import create_search_router

__all__ = ["SemanticSearchEngine", "create_search_router"]