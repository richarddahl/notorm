"""
Domain services for the Vector Search module.

This module defines the core domain services for the Vector Search module,
providing high-level operations for vector search, embeddings, and RAG.
"""

import logging
import uuid
from typing import Dict, List, Optional, Any, Union, TypeVar, Type, Generic, Tuple
from datetime import datetime, UTC

from uno.core.result import Result, Success, Failure
from uno.domain.service import DomainService

from uno.vector_search.entities import (
    VectorId,
    IndexId,
    EmbeddingId,
    SearchQueryId,
    VectorIndex,
    Embedding,
    SearchQuery,
    SearchResult,
    HybridSearchQuery,
    IndexType,
    DistanceMetric,
    EmbeddingModel,
    TypedSearchResult,
    RAGContext
)
from uno.vector_search.domain_repositories import (
    VectorIndexRepositoryProtocol,
    EmbeddingRepositoryProtocol,
    SearchRepositoryProtocol
)

T = TypeVar('T')


class VectorIndexService(DomainService):
    """Service for managing vector indices."""
    
    def __init__(
        self,
        index_repository: VectorIndexRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the vector index service.
        
        Args:
            index_repository: Repository for vector indices
            logger: Optional logger
        """
        self.index_repository = index_repository
        self.logger = logger or logging.getLogger("uno.vector_search.index")
    
    async def create_index(
        self,
        name: str,
        dimension: int,
        index_type: IndexType = IndexType.HNSW,
        distance_metric: DistanceMetric = DistanceMetric.COSINE,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[VectorIndex]:
        """
        Create a new vector index.
        
        Args:
            name: Index name
            dimension: Vector dimension
            index_type: Type of index
            distance_metric: Distance metric
            metadata: Optional metadata
            
        Returns:
            Result containing the created index or an error
        """
        try:
            # Check if index already exists
            existing_result = await self.index_repository.get_by_name(name)
            if isinstance(existing_result, Success):
                return Result.failure(f"Index '{name}' already exists")
            
            # Create index entity
            index = VectorIndex(
                id=IndexId(str(uuid.uuid4())),
                name=name,
                dimension=dimension,
                index_type=index_type,
                distance_metric=distance_metric,
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.index_repository.create(index)
        except Exception as e:
            self.logger.error(f"Failed to create index: {str(e)}")
            return Result.failure(f"Failed to create index: {str(e)}")
    
    async def get_index(self, index_id: Union[str, IndexId]) -> Result[VectorIndex]:
        """
        Get a vector index by ID.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing the index or an error if not found
        """
        try:
            if isinstance(index_id, str):
                index_id = IndexId(index_id)
            
            return await self.index_repository.get(index_id)
        except Exception as e:
            self.logger.error(f"Failed to get index: {str(e)}")
            return Result.failure(f"Failed to get index: {str(e)}")
    
    async def get_index_by_name(self, name: str) -> Result[VectorIndex]:
        """
        Get a vector index by name.
        
        Args:
            name: Index name
            
        Returns:
            Result containing the index or an error if not found
        """
        try:
            return await self.index_repository.get_by_name(name)
        except Exception as e:
            self.logger.error(f"Failed to get index by name: {str(e)}")
            return Result.failure(f"Failed to get index by name: {str(e)}")
    
    async def update_index(
        self,
        index_id: Union[str, IndexId],
        name: Optional[str] = None,
        distance_metric: Optional[DistanceMetric] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[VectorIndex]:
        """
        Update a vector index.
        
        Args:
            index_id: Index ID
            name: New name (optional)
            distance_metric: New distance metric (optional)
            metadata: New metadata (optional)
            
        Returns:
            Result containing the updated index or an error
        """
        try:
            if isinstance(index_id, str):
                index_id = IndexId(index_id)
            
            # Get existing index
            index_result = await self.index_repository.get(index_id)
            if isinstance(index_result, Failure):
                return index_result
            
            index = index_result.value
            
            # Update fields
            index.update(name, distance_metric, metadata)
            
            # Save to repository
            return await self.index_repository.update(index)
        except Exception as e:
            self.logger.error(f"Failed to update index: {str(e)}")
            return Result.failure(f"Failed to update index: {str(e)}")
    
    async def delete_index(self, index_id: Union[str, IndexId]) -> Result[bool]:
        """
        Delete a vector index.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            if isinstance(index_id, str):
                index_id = IndexId(index_id)
            
            return await self.index_repository.delete(index_id)
        except Exception as e:
            self.logger.error(f"Failed to delete index: {str(e)}")
            return Result.failure(f"Failed to delete index: {str(e)}")
    
    async def list_indexes(self) -> Result[List[VectorIndex]]:
        """
        List all vector indexes.
        
        Returns:
            Result containing a list of vector indexes or an error
        """
        try:
            return await self.index_repository.list()
        except Exception as e:
            self.logger.error(f"Failed to list indexes: {str(e)}")
            return Result.failure(f"Failed to list indexes: {str(e)}")


class EmbeddingService(DomainService):
    """Service for managing embeddings."""
    
    def __init__(
        self,
        embedding_repository: EmbeddingRepositoryProtocol,
        search_repository: SearchRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the embedding service.
        
        Args:
            embedding_repository: Repository for embeddings
            search_repository: Repository for search operations (used for generating embeddings)
            logger: Optional logger
        """
        self.embedding_repository = embedding_repository
        self.search_repository = search_repository
        self.logger = logger or logging.getLogger("uno.vector_search.embedding")
    
    async def create_embedding(
        self,
        source_id: str,
        source_type: str,
        content: str,
        model: EmbeddingModel = EmbeddingModel.DEFAULT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[Embedding]:
        """
        Create a new embedding from content.
        
        Args:
            source_id: Source ID
            source_type: Source type
            content: Text content to embed
            model: Embedding model
            metadata: Optional metadata
            
        Returns:
            Result containing the created embedding or an error
        """
        try:
            # Generate embedding vector
            vector_result = await self.search_repository.generate_embedding(content)
            if isinstance(vector_result, Failure):
                return Result.failure(f"Failed to generate embedding: {vector_result.error}")
            
            vector = vector_result.value
            
            # Create embedding entity
            embedding = Embedding(
                id=EmbeddingId(str(uuid.uuid4())),
                vector=vector,
                source_id=source_id,
                source_type=source_type,
                model=model,
                dimension=len(vector),
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.embedding_repository.create(embedding)
        except Exception as e:
            self.logger.error(f"Failed to create embedding: {str(e)}")
            return Result.failure(f"Failed to create embedding: {str(e)}")
    
    async def create_embedding_with_vector(
        self,
        source_id: str,
        source_type: str,
        vector: List[float],
        model: EmbeddingModel = EmbeddingModel.DEFAULT,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[Embedding]:
        """
        Create a new embedding with a pre-generated vector.
        
        Args:
            source_id: Source ID
            source_type: Source type
            vector: Pre-generated embedding vector
            model: Embedding model
            metadata: Optional metadata
            
        Returns:
            Result containing the created embedding or an error
        """
        try:
            # Create embedding entity
            embedding = Embedding(
                id=EmbeddingId(str(uuid.uuid4())),
                vector=vector,
                source_id=source_id,
                source_type=source_type,
                model=model,
                dimension=len(vector),
                metadata=metadata or {}
            )
            
            # Save to repository
            return await self.embedding_repository.create(embedding)
        except Exception as e:
            self.logger.error(f"Failed to create embedding with vector: {str(e)}")
            return Result.failure(f"Failed to create embedding with vector: {str(e)}")
    
    async def get_embedding(self, embedding_id: Union[str, EmbeddingId]) -> Result[Embedding]:
        """
        Get an embedding by ID.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            if isinstance(embedding_id, str):
                embedding_id = EmbeddingId(embedding_id)
            
            return await self.embedding_repository.get(embedding_id)
        except Exception as e:
            self.logger.error(f"Failed to get embedding: {str(e)}")
            return Result.failure(f"Failed to get embedding: {str(e)}")
    
    async def get_embedding_by_source(self, source_id: str, source_type: str) -> Result[Embedding]:
        """
        Get an embedding by source.
        
        Args:
            source_id: Source ID
            source_type: Source type
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            return await self.embedding_repository.get_by_source(source_id, source_type)
        except Exception as e:
            self.logger.error(f"Failed to get embedding by source: {str(e)}")
            return Result.failure(f"Failed to get embedding by source: {str(e)}")
    
    async def update_embedding(
        self,
        embedding_id: Union[str, EmbeddingId],
        content: Optional[str] = None,
        vector: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[Embedding]:
        """
        Update an embedding.
        
        Args:
            embedding_id: Embedding ID
            content: New content to embed (optional)
            vector: New vector (optional, used if content not provided)
            metadata: New metadata (optional)
            
        Returns:
            Result containing the updated embedding or an error
        """
        try:
            if isinstance(embedding_id, str):
                embedding_id = EmbeddingId(embedding_id)
            
            # Get existing embedding
            embedding_result = await self.embedding_repository.get(embedding_id)
            if isinstance(embedding_result, Failure):
                return embedding_result
            
            embedding = embedding_result.value
            
            # Update vector if content or vector provided
            if content is not None:
                # Generate new embedding vector
                vector_result = await self.search_repository.generate_embedding(content)
                if isinstance(vector_result, Failure):
                    return Result.failure(f"Failed to generate embedding: {vector_result.error}")
                
                new_vector = vector_result.value
                embedding.update_vector(new_vector)
            elif vector is not None:
                embedding.update_vector(vector)
            
            # Update metadata if provided
            if metadata:
                embedding.metadata.update(metadata)
            
            # Save to repository
            return await self.embedding_repository.update(embedding)
        except Exception as e:
            self.logger.error(f"Failed to update embedding: {str(e)}")
            return Result.failure(f"Failed to update embedding: {str(e)}")
    
    async def delete_embedding(self, embedding_id: Union[str, EmbeddingId]) -> Result[bool]:
        """
        Delete an embedding.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            if isinstance(embedding_id, str):
                embedding_id = EmbeddingId(embedding_id)
            
            return await self.embedding_repository.delete(embedding_id)
        except Exception as e:
            self.logger.error(f"Failed to delete embedding: {str(e)}")
            return Result.failure(f"Failed to delete embedding: {str(e)}")
    
    async def bulk_create_embeddings(
        self,
        items: List[Dict[str, Any]]
    ) -> Result[List[Embedding]]:
        """
        Bulk create embeddings.
        
        Args:
            items: List of items to create embeddings for, each with:
                  - source_id: Source ID
                  - source_type: Source type
                  - content: Text content to embed
                  - model: (optional) Embedding model
                  - metadata: (optional) Metadata
            
        Returns:
            Result containing a list of created embeddings or an error
        """
        try:
            embeddings = []
            
            # Process each item
            for item in items:
                # Generate embedding vector
                content = item.get("content")
                if not content:
                    return Result.failure("Content is required for embedding generation")
                
                vector_result = await self.search_repository.generate_embedding(content)
                if isinstance(vector_result, Failure):
                    return Result.failure(f"Failed to generate embedding: {vector_result.error}")
                
                vector = vector_result.value
                
                # Create embedding entity
                embedding = Embedding(
                    id=EmbeddingId(str(uuid.uuid4())),
                    vector=vector,
                    source_id=item.get("source_id"),
                    source_type=item.get("source_type"),
                    model=item.get("model", EmbeddingModel.DEFAULT),
                    dimension=len(vector),
                    metadata=item.get("metadata", {})
                )
                
                embeddings.append(embedding)
            
            # Bulk save to repository
            return await self.embedding_repository.bulk_create(embeddings)
        except Exception as e:
            self.logger.error(f"Failed to bulk create embeddings: {str(e)}")
            return Result.failure(f"Failed to bulk create embeddings: {str(e)}")


class SearchService(DomainService):
    """Service for performing vector searches."""
    
    def __init__(
        self,
        search_repository: SearchRepositoryProtocol,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the search service.
        
        Args:
            search_repository: Repository for search operations
            logger: Optional logger
        """
        self.search_repository = search_repository
        self.logger = logger or logging.getLogger("uno.vector_search.search")
    
    async def search_by_text(
        self,
        query_text: str,
        limit: int = 10,
        threshold: float = 0.7,
        metric: str = "cosine",
        index_id: Optional[Union[str, IndexId]] = None,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[List[SearchResult]]:
        """
        Search by text.
        
        Args:
            query_text: Text query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            metric: Distance metric
            index_id: Optional index ID
            filters: Optional filters
            metadata: Optional metadata
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            # Create query entity
            query = SearchQuery(
                id=SearchQueryId(str(uuid.uuid4())),
                query_text=query_text,
                limit=limit,
                threshold=threshold,
                metric=metric,
                index_id=IndexId(index_id) if isinstance(index_id, str) and index_id else None,
                filters=filters or {},
                metadata=metadata or {}
            )
            
            # Execute search
            return await self.search_repository.search(query)
        except Exception as e:
            self.logger.error(f"Failed to search by text: {str(e)}")
            return Result.failure(f"Failed to search by text: {str(e)}")
    
    async def search_by_vector(
        self,
        vector: List[float],
        limit: int = 10,
        threshold: float = 0.7,
        metric: str = "cosine",
        index_id: Optional[Union[str, IndexId]] = None,
        filters: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[List[SearchResult]]:
        """
        Search by vector.
        
        Args:
            vector: Vector query
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            metric: Distance metric
            index_id: Optional index ID
            filters: Optional filters
            metadata: Optional metadata
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            # Create query entity
            query = SearchQuery(
                id=SearchQueryId(str(uuid.uuid4())),
                query_vector=vector,
                limit=limit,
                threshold=threshold,
                metric=metric,
                index_id=IndexId(index_id) if isinstance(index_id, str) and index_id else None,
                filters=filters or {},
                metadata=metadata or {}
            )
            
            # Execute search
            return await self.search_repository.search(query)
        except Exception as e:
            self.logger.error(f"Failed to search by vector: {str(e)}")
            return Result.failure(f"Failed to search by vector: {str(e)}")
    
    async def hybrid_search(
        self,
        query_text: str,
        start_node_type: str,
        path_pattern: str,
        limit: int = 10,
        threshold: float = 0.7,
        metric: str = "cosine",
        start_filters: Optional[Dict[str, Any]] = None,
        combine_method: str = "intersect",
        graph_weight: float = 0.5,
        vector_weight: float = 0.5,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[List[SearchResult]]:
        """
        Perform a hybrid search combining graph and vector search.
        
        Args:
            query_text: Text query
            start_node_type: Type of node to start graph traversal from
            path_pattern: Cypher path pattern for traversal
            limit: Maximum number of results
            threshold: Minimum similarity threshold
            metric: Distance metric
            start_filters: Filters to apply to the start node
            combine_method: How to combine graph and vector results
            graph_weight: Weight to give graph results (0-1)
            vector_weight: Weight to give vector results (0-1)
            metadata: Optional metadata
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            # Create hybrid query entity
            query = HybridSearchQuery(
                id=SearchQueryId(str(uuid.uuid4())),
                query_text=query_text,
                start_node_type=start_node_type,
                path_pattern=path_pattern,
                limit=limit,
                threshold=threshold,
                metric=metric,
                start_filters=start_filters or {},
                combine_method=combine_method,
                graph_weight=graph_weight,
                vector_weight=vector_weight,
                metadata=metadata or {}
            )
            
            # Execute hybrid search
            return await self.search_repository.hybrid_search(query)
        except Exception as e:
            self.logger.error(f"Failed to perform hybrid search: {str(e)}")
            return Result.failure(f"Failed to perform hybrid search: {str(e)}")
    
    async def generate_embedding(self, text: str) -> Result[List[float]]:
        """
        Generate an embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Result containing the embedding vector or an error
        """
        try:
            return await self.search_repository.generate_embedding(text)
        except Exception as e:
            self.logger.error(f"Failed to generate embedding: {str(e)}")
            return Result.failure(f"Failed to generate embedding: {str(e)}")


class RAGService(DomainService):
    """Service for Retrieval-Augmented Generation (RAG)."""
    
    def __init__(
        self,
        search_service: SearchService,
        entity_loader: Optional[callable] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the RAG service.
        
        Args:
            search_service: Service for performing searches
            entity_loader: Optional function to load entities by ID and type
            logger: Optional logger
        """
        self.search_service = search_service
        self.entity_loader = entity_loader
        self.logger = logger or logging.getLogger("uno.vector_search.rag")
    
    async def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[List[SearchResult]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query text
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold
            filters: Optional filters
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            # Perform vector search
            return await self.search_service.search_by_text(
                query_text=query,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve context: {str(e)}")
            return Result.failure(f"Failed to retrieve context: {str(e)}")
    
    def format_context(self, results: List[SearchResult]) -> str:
        """
        Format search results as context for an LLM prompt.
        
        Args:
            results: The search results
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, result in enumerate(results):
            # Format as a numbered context item
            context_text = f"[{i+1}] "
            
            # Add metadata
            if result.metadata and "raw_data" in result.metadata:
                raw_data = result.metadata["raw_data"]
                
                # Add title if available
                if "title" in raw_data:
                    context_text += f"Title: {raw_data['title']}\n"
                
                # Add content if available
                if "content" in raw_data:
                    content = raw_data["content"]
                    # Limit very long content
                    if len(content) > 2000:
                        content = content[:2000] + "..."
                    context_text += f"Content: {content}\n"
                
                # Add other metadata
                for key, value in raw_data.items():
                    if key not in ["title", "content"] and isinstance(value, (str, int, float, bool)):
                        context_text += f"{key}: {value}\n"
            
            context_parts.append(context_text)
        
        # Join all context items with separators
        return "\n---\n".join(context_parts)
    
    async def create_rag_prompt(
        self,
        query: str,
        system_prompt: str,
        limit: int = 5,
        threshold: float = 0.7,
        filters: Optional[Dict[str, Any]] = None
    ) -> Result[Dict[str, str]]:
        """
        Create a RAG prompt with retrieved context.
        
        Args:
            query: The user's query
            system_prompt: The system prompt 
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold
            filters: Optional filters
            
        Returns:
            Result containing a dict with system_prompt and user_prompt keys
        """
        try:
            # Retrieve context
            results_result = await self.retrieve_context(
                query=query,
                limit=limit,
                threshold=threshold,
                filters=filters
            )
            
            if isinstance(results_result, Failure):
                return results_result
            
            results = results_result.value
            
            # Create RAG context
            rag_context = RAGContext(
                query=query,
                system_prompt=system_prompt,
                results=results
            )
            
            # Format context and create prompt
            formatted_context = self.format_context(results)
            rag_context.formatted_context = formatted_context
            
            prompt = rag_context.create_prompt()
            
            return Result.success(prompt)
        except Exception as e:
            self.logger.error(f"Failed to create RAG prompt: {str(e)}")
            return Result.failure(f"Failed to create RAG prompt: {str(e)}")


class VectorSearchService(DomainService):
    """Coordinating service for vector search operations."""
    
    def __init__(
        self,
        index_service: VectorIndexService,
        embedding_service: EmbeddingService,
        search_service: SearchService,
        rag_service: RAGService,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the vector search service.
        
        Args:
            index_service: Service for managing indices
            embedding_service: Service for managing embeddings
            search_service: Service for performing searches
            rag_service: Service for RAG operations
            logger: Optional logger
        """
        self.index_service = index_service
        self.embedding_service = embedding_service
        self.search_service = search_service
        self.rag_service = rag_service
        self.logger = logger or logging.getLogger("uno.vector_search")
    
    async def index_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Result[Embedding]:
        """
        Index a document for vector search.
        
        Args:
            document_id: Document ID
            content: Document content to embed
            metadata: Optional metadata
            
        Returns:
            Result containing the created embedding or an error
        """
        return await self.embedding_service.create_embedding(
            source_id=document_id,
            source_type="document",
            content=content,
            metadata=metadata
        )
    
    async def search_documents(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """
        Search documents using vector similarity.
        
        Args:
            query: The search query text
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of search results or an error
        """
        return await self.search_service.search_by_text(
            query_text=query,
            limit=limit,
            threshold=threshold,
            filters={"source_type": "document"}
        )
    
    async def generate_rag_prompt(
        self,
        query: str,
        system_prompt: str,
        limit: int = 3,
        threshold: float = 0.7
    ) -> Result[Dict[str, str]]:
        """
        Generate a RAG prompt with retrieved context.
        
        Args:
            query: The user's query
            system_prompt: System prompt for the LLM
            limit: Maximum number of documents to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Result containing a dict with system_prompt and user_prompt keys
        """
        return await self.rag_service.create_rag_prompt(
            query=query,
            system_prompt=system_prompt,
            limit=limit,
            threshold=threshold,
            filters={"source_type": "document"}
        )