"""
Cross-feature integration for Uno AI components.

This module provides integration between different AI features including
semantic search, recommendations, content generation, and anomaly detection,
enabling more powerful combined capabilities.
"""

from uno.ai.integration.context import (
    ContextBatch,
    ContextItem,
    ContextQuery,
    ContextSource, 
    ContextType,
    ContextValidityPeriod,
    Relevance,
    UnifiedContextManager,
)
from uno.ai.integration.embeddings import (
    EmbeddingModelConfig,
    EmbeddingType,
    EnhancedRAGService,
    SharedEmbeddingService,
)

# Note: These imports will be available when those modules are implemented
try:
    from uno.ai.integration.recommendations import IntelligentRecommendationService
except ImportError:
    pass

__all__ = [
    # Context management
    "ContextBatch",
    "ContextItem",
    "ContextQuery", 
    "ContextSource",
    "ContextType",
    "ContextValidityPeriod",
    "Relevance",
    "UnifiedContextManager",
    
    # Embedding and RAG
    "EmbeddingModelConfig",
    "EmbeddingType",
    "EnhancedRAGService",
    "SharedEmbeddingService",
    
    # Intelligent recommendations (when available)
    "IntelligentRecommendationService",
]