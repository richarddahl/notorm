"""
AI capabilities for the Uno framework.

This package provides AI-enhanced features:
- Semantic search with vector embeddings
- Content generation and summarization
- Recommendation engines
- Anomaly detection
"""

from uno.ai.domain_endpoints import ai_router
from uno.ai.domain_provider import (
    configure_ai_dependencies,
    get_embedding_model_service,
    get_embedding_service,
    get_semantic_search_service,
    get_rag_service,
    create_embedding_service
)

__version__ = "0.2.0"

__all__ = [
    "ai_router",
    "configure_ai_dependencies",
    "get_embedding_model_service",
    "get_embedding_service",
    "get_semantic_search_service",
    "get_rag_service",
    "create_embedding_service"
]