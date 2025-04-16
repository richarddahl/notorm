"""
Domain provider for the Vector Search module.

This module configures dependency injection for the Vector Search module,
allowing consumers to access vector search services through a clean interface.
"""

import logging
import inject
from typing import Optional, Dict, Any, List, Callable, Type

from uno.database.provider import get_db_session
from uno.core.result import Result

from uno.vector_search.domain_repositories import (
    VectorIndexRepository,
    EmbeddingRepository,
    SearchRepository,
    VectorIndexRepositoryProtocol,
    EmbeddingRepositoryProtocol,
    SearchRepositoryProtocol
)
from uno.vector_search.domain_services import (
    VectorIndexService,
    EmbeddingService,
    SearchService,
    RAGService,
    VectorSearchService
)


def configure_vector_search_dependencies(binder: inject.Binder) -> None:
    """
    Configure dependencies for the Vector Search module.
    
    Args:
        binder: Dependency injection binder
    """
    # Create logger
    logger = logging.getLogger("uno.vector_search")
    
    # Bind repositories
    binder.bind(
        VectorIndexRepositoryProtocol,
        lambda: VectorIndexRepository(get_db_session())
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
        VectorIndexService,
        lambda: VectorIndexService(
            inject.instance(VectorIndexRepositoryProtocol),
            logger.getChild("index")
        )
    )
    binder.bind(
        EmbeddingService,
        lambda: EmbeddingService(
            inject.instance(EmbeddingRepositoryProtocol),
            inject.instance(SearchRepositoryProtocol),
            logger.getChild("embedding")
        )
    )
    binder.bind(
        SearchService,
        lambda: SearchService(
            inject.instance(SearchRepositoryProtocol),
            logger.getChild("search")
        )
    )
    binder.bind(
        RAGService,
        lambda: RAGService(
            inject.instance(SearchService),
            None,  # Entity loader will be provided via special accessor methods
            logger.getChild("rag")
        )
    )
    
    # Bind coordinating service
    binder.bind(
        VectorSearchService,
        lambda: VectorSearchService(
            inject.instance(VectorIndexService),
            inject.instance(EmbeddingService),
            inject.instance(SearchService),
            inject.instance(RAGService),
            logger
        )
    )


# Helper accessor functions
def get_index_service() -> VectorIndexService:
    """
    Get the vector index service.
    
    Returns:
        VectorIndexService instance
    """
    return inject.instance(VectorIndexService)


def get_embedding_service() -> EmbeddingService:
    """
    Get the embedding service.
    
    Returns:
        EmbeddingService instance
    """
    return inject.instance(EmbeddingService)


def get_search_service() -> SearchService:
    """
    Get the search service.
    
    Returns:
        SearchService instance
    """
    return inject.instance(SearchService)


def get_rag_service(entity_loader: Optional[Callable] = None) -> RAGService:
    """
    Get the RAG service.
    
    Args:
        entity_loader: Optional function to load entities by ID and type
    
    Returns:
        RAGService instance
    """
    rag_service = inject.instance(RAGService)
    if entity_loader:
        rag_service.entity_loader = entity_loader
    return rag_service


def get_vector_search_service() -> VectorSearchService:
    """
    Get the vector search service.
    
    Returns:
        VectorSearchService instance
    """
    return inject.instance(VectorSearchService)


# Special accessor functions with custom configurations
def get_document_search_service() -> SearchService:
    """
    Get a search service configured for document search.
    
    Returns:
        SearchService instance
    """
    search_service = get_search_service()
    # You could add specialized functionality here if needed
    return search_service


def get_document_rag_service(
    default_system_prompt: Optional[str] = None,
    entity_loader: Optional[Callable] = None
) -> RAGService:
    """
    Get a RAG service configured for document-based RAG.
    
    Args:
        default_system_prompt: Optional default system prompt
        entity_loader: Optional function to load document entities
        
    Returns:
        RAGService instance
    """
    rag_service = get_rag_service(entity_loader)
    # You could add specialized functionality or configuration here
    return rag_service