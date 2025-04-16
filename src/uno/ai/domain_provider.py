"""
Domain provider for the AI module.

This module configures dependency injection for the AI module,
providing access to AI services like embedding, semantic search,
recommendations, content generation, and anomaly detection.
"""

import logging
from typing import Optional, Dict, Any, List

import inject
from uno.database.provider import get_db_session

from uno.ai.domain_repositories import (
    EmbeddingModelRepository,
    EmbeddingRepository,
    SearchRepository,
    EmbeddingModelRepositoryProtocol,
    EmbeddingRepositoryProtocol,
    SearchRepositoryProtocol
)
from uno.ai.domain_services import (
    EmbeddingModelService,
    EmbeddingService,
    SemanticSearchService,
    RAGService
)


def configure_ai_dependencies(binder: inject.Binder) -> None:
    """
    Configure dependencies for the AI module.
    
    Args:
        binder: Dependency injection binder
    """
    # Create logger
    logger = logging.getLogger("uno.ai")
    
    # Bind repositories
    binder.bind(
        EmbeddingModelRepositoryProtocol,
        lambda: EmbeddingModelRepository(get_db_session())
    )
    binder.bind(
        EmbeddingRepositoryProtocol,
        lambda: EmbeddingRepository(get_db_session())
    )
    binder.bind(
        SearchRepositoryProtocol,
        lambda: SearchRepository(get_db_session())
    )
    
    # Bind services
    binder.bind(
        EmbeddingModelService,
        lambda: EmbeddingModelService(
            inject.instance(EmbeddingModelRepositoryProtocol),
            logger.getChild("embedding_model")
        )
    )
    binder.bind(
        EmbeddingService,
        lambda: EmbeddingService(
            inject.instance(EmbeddingRepositoryProtocol),
            inject.instance(EmbeddingModelService),
            logger.getChild("embedding")
        )
    )
    binder.bind(
        SemanticSearchService,
        lambda: SemanticSearchService(
            inject.instance(SearchRepositoryProtocol),
            inject.instance(EmbeddingService),
            logger.getChild("semantic_search")
        )
    )
    binder.bind(
        RAGService,
        lambda: RAGService(
            inject.instance(SemanticSearchService),
            None,  # Context repository would be provided if available
            logger.getChild("rag")
        )
    )


# Helper functions to access services
def get_embedding_model_service() -> EmbeddingModelService:
    """
    Get the embedding model service.
    
    Returns:
        EmbeddingModelService instance
    """
    return inject.instance(EmbeddingModelService)


def get_embedding_service() -> EmbeddingService:
    """
    Get the embedding service.
    
    Returns:
        EmbeddingService instance
    """
    return inject.instance(EmbeddingService)


def get_semantic_search_service() -> SemanticSearchService:
    """
    Get the semantic search service.
    
    Returns:
        SemanticSearchService instance
    """
    return inject.instance(SemanticSearchService)


def get_rag_service() -> RAGService:
    """
    Get the RAG service.
    
    Returns:
        RAGService instance
    """
    return inject.instance(RAGService)


# Factory functions for customized instances
def create_embedding_service(
    model_name: str,
    dimensions: int,
    normalize_vectors: bool = True,
    api_key: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> EmbeddingService:
    """
    Create a customized embedding service with a specific model.
    
    Args:
        model_name: Name of the embedding model
        dimensions: Embedding dimensions
        normalize_vectors: Whether to normalize vectors
        api_key: Optional API key for the model
        metadata: Optional metadata for the model
    
    Returns:
        EmbeddingService instance
    """
    from uno.ai.entities import EmbeddingModelType, ModelId
    import uuid
    
    # Get standard services
    model_service = get_embedding_model_service()
    embedding_service = get_embedding_service()
    
    # Create model if it doesn't exist
    model_result = model_service.get_model_by_name(model_name)
    if model_result.is_failure():
        # Determine model type
        if "openai" in model_name.lower():
            model_type = EmbeddingModelType.OPENAI
        elif any(name in model_name.lower() for name in ["bert", "roberta", "t5"]):
            model_type = EmbeddingModelType.HUGGINGFACE
        else:
            model_type = EmbeddingModelType.SENTENCE_TRANSFORMER
            
        # Create the model
        model_service.create_model(
            name=model_name,
            model_type=model_type,
            dimensions=dimensions,
            api_key=api_key,
            normalize_vectors=normalize_vectors,
            metadata=metadata
        )
    
    return embedding_service