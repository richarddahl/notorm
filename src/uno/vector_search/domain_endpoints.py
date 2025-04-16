"""
Domain endpoints for the Vector Search module.

This module defines FastAPI endpoints for the Vector Search module,
providing a RESTful API for vector search operations.
"""

from typing import Dict, List, Optional, Any, Union, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from pydantic import BaseModel, Field, ConfigDict

from uno.core.result import Success, Failure
from uno.vector_search.domain_services import (
    VectorIndexService,
    EmbeddingService,
    SearchService,
    RAGService,
    VectorSearchService
)
from uno.vector_search.domain_provider import (
    get_index_service,
    get_embedding_service,
    get_search_service,
    get_rag_service,
    get_vector_search_service,
    get_document_search_service,
    get_document_rag_service
)
from uno.vector_search.entities import (
    IndexType,
    DistanceMetric,
    EmbeddingModel
)


# DTOs
class VectorIndexDTO(BaseModel):
    """DTO for vector indices."""
    
    id: str = Field(..., description="Index ID")
    name: str = Field(..., description="Index name")
    dimension: int = Field(..., description="Vector dimension")
    index_type: str = Field(..., description="Index type")
    distance_metric: str = Field(..., description="Distance metric")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Index metadata")


class CreateIndexDTO(BaseModel):
    """DTO for creating indices."""
    
    name: str = Field(..., description="Index name")
    dimension: int = Field(..., description="Vector dimension")
    index_type: str = Field("hnsw", description="Index type")
    distance_metric: str = Field("cosine", description="Distance metric")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Index metadata")


class UpdateIndexDTO(BaseModel):
    """DTO for updating indices."""
    
    name: Optional[str] = Field(None, description="Index name")
    distance_metric: Optional[str] = Field(None, description="Distance metric")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Index metadata")


class EmbeddingDTO(BaseModel):
    """DTO for embeddings."""
    
    id: str = Field(..., description="Embedding ID")
    vector: List[float] = Field(..., description="Embedding vector")
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    model: str = Field(..., description="Embedding model")
    dimension: int = Field(..., description="Vector dimension")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Embedding metadata")


class CreateEmbeddingDTO(BaseModel):
    """DTO for creating embeddings."""
    
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    content: str = Field(..., description="Content to embed")
    model: Optional[str] = Field("default", description="Embedding model")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Embedding metadata")


class CreateEmbeddingWithVectorDTO(BaseModel):
    """DTO for creating embeddings with pre-generated vectors."""
    
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    vector: List[float] = Field(..., description="Pre-generated embedding vector")
    model: Optional[str] = Field("default", description="Embedding model")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Embedding metadata")


class UpdateEmbeddingDTO(BaseModel):
    """DTO for updating embeddings."""
    
    content: Optional[str] = Field(None, description="New content to embed")
    vector: Optional[List[float]] = Field(None, description="New vector")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Embedding metadata")


class SearchResultDTO(BaseModel):
    """DTO for search results."""
    
    id: str = Field(..., description="Result ID")
    similarity: float = Field(..., description="Similarity score")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    rank: int = Field(..., description="Result rank")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class TextSearchDTO(BaseModel):
    """DTO for text searches."""
    
    query: str = Field(..., description="Query text")
    limit: int = Field(10, description="Maximum number of results")
    threshold: float = Field(0.7, description="Minimum similarity threshold")
    metric: str = Field("cosine", description="Distance metric")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Search metadata")


class VectorSearchDTO(BaseModel):
    """DTO for vector searches."""
    
    vector: List[float] = Field(..., description="Query vector")
    limit: int = Field(10, description="Maximum number of results")
    threshold: float = Field(0.7, description="Minimum similarity threshold")
    metric: str = Field("cosine", description="Distance metric")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Search metadata")


class HybridSearchDTO(BaseModel):
    """DTO for hybrid searches."""
    
    query: str = Field(..., description="Query text")
    start_node_type: str = Field(..., description="Start node type")
    path_pattern: str = Field(..., description="Path pattern")
    limit: int = Field(10, description="Maximum number of results")
    threshold: float = Field(0.7, description="Minimum similarity threshold")
    metric: str = Field("cosine", description="Distance metric")
    start_filters: Optional[Dict[str, Any]] = Field(None, description="Start filters")
    combine_method: str = Field("intersect", description="Combine method")
    graph_weight: float = Field(0.5, description="Graph weight")
    vector_weight: float = Field(0.5, description="Vector weight")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Search metadata")


class GenerateEmbeddingDTO(BaseModel):
    """DTO for generating embeddings."""
    
    text: str = Field(..., description="Text to embed")


class RAGPromptDTO(BaseModel):
    """DTO for RAG prompts."""
    
    query: str = Field(..., description="User query")
    system_prompt: str = Field(..., description="System prompt")
    limit: int = Field(3, description="Maximum number of results")
    threshold: float = Field(0.7, description="Minimum similarity threshold")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters")


class RAGPromptResponseDTO(BaseModel):
    """DTO for RAG prompt responses."""
    
    system_prompt: str = Field(..., description="System prompt")
    user_prompt: str = Field(..., description="User prompt with context")


class DocumentDTO(BaseModel):
    """DTO for documents."""
    
    id: str = Field(..., description="Document ID")
    title: Optional[str] = Field(None, description="Document title")
    content: str = Field(..., description="Document content")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    
    model_config = ConfigDict(extra="allow")


class BulkIndexDocumentsDTO(BaseModel):
    """DTO for bulk indexing documents."""
    
    documents: List[DocumentDTO] = Field(..., description="Documents to index")


# Router factory
def create_vector_search_router() -> APIRouter:
    """
    Create FastAPI router for vector search endpoints.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(
        prefix="/api/vector-search",
        tags=["vector-search"],
        responses={401: {"description": "Unauthorized"}},
    )
    
    # Index endpoints
    @router.post(
        "/indexes",
        response_model=VectorIndexDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create index",
        description="Create a new vector index"
    )
    async def create_index(
        request: CreateIndexDTO,
        index_service: VectorIndexService = Depends(get_index_service)
    ) -> VectorIndexDTO:
        """Create a new vector index."""
        try:
            # Convert types
            index_type = IndexType(request.index_type)
            distance_metric = DistanceMetric(request.distance_metric)
            
            # Create index
            result = await index_service.create_index(
                request.name,
                request.dimension,
                index_type,
                distance_metric,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            
            index = result.value
            
            # Convert to DTO
            return VectorIndexDTO(
                id=index.id.value,
                name=index.name,
                dimension=index.dimension,
                index_type=index.index_type.value,
                distance_metric=index.distance_metric.value,
                created_at=index.created_at,
                updated_at=index.updated_at,
                metadata=index.metadata
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create index: {str(e)}"
            )
    
    @router.get(
        "/indexes/{index_id}",
        response_model=VectorIndexDTO,
        summary="Get index",
        description="Get a vector index by ID"
    )
    async def get_index(
        index_id: str,
        index_service: VectorIndexService = Depends(get_index_service)
    ) -> VectorIndexDTO:
        """Get a vector index by ID."""
        try:
            # Get index
            result = await index_service.get_index(index_id)
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            index = result.value
            
            # Convert to DTO
            return VectorIndexDTO(
                id=index.id.value,
                name=index.name,
                dimension=index.dimension,
                index_type=index.index_type.value,
                distance_metric=index.distance_metric.value,
                created_at=index.created_at,
                updated_at=index.updated_at,
                metadata=index.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get index: {str(e)}"
            )
    
    @router.get(
        "/indexes",
        response_model=List[VectorIndexDTO],
        summary="List indexes",
        description="List all vector indexes"
    )
    async def list_indexes(
        index_service: VectorIndexService = Depends(get_index_service)
    ) -> List[VectorIndexDTO]:
        """List all vector indexes."""
        try:
            # List indexes
            result = await index_service.list_indexes()
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            indexes = result.value
            
            # Convert to DTOs
            return [
                VectorIndexDTO(
                    id=index.id.value,
                    name=index.name,
                    dimension=index.dimension,
                    index_type=index.index_type.value,
                    distance_metric=index.distance_metric.value,
                    created_at=index.created_at,
                    updated_at=index.updated_at,
                    metadata=index.metadata
                )
                for index in indexes
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list indexes: {str(e)}"
            )
    
    @router.put(
        "/indexes/{index_id}",
        response_model=VectorIndexDTO,
        summary="Update index",
        description="Update a vector index"
    )
    async def update_index(
        index_id: str,
        request: UpdateIndexDTO,
        index_service: VectorIndexService = Depends(get_index_service)
    ) -> VectorIndexDTO:
        """Update a vector index."""
        try:
            # Convert types
            distance_metric = DistanceMetric(request.distance_metric) if request.distance_metric else None
            
            # Update index
            result = await index_service.update_index(
                index_id,
                request.name,
                distance_metric,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            index = result.value
            
            # Convert to DTO
            return VectorIndexDTO(
                id=index.id.value,
                name=index.name,
                dimension=index.dimension,
                index_type=index.index_type.value,
                distance_metric=index.distance_metric.value,
                created_at=index.created_at,
                updated_at=index.updated_at,
                metadata=index.metadata
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update index: {str(e)}"
            )
    
    @router.delete(
        "/indexes/{index_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete index",
        description="Delete a vector index"
    )
    async def delete_index(
        index_id: str,
        index_service: VectorIndexService = Depends(get_index_service)
    ) -> None:
        """Delete a vector index."""
        try:
            # Delete index
            result = await index_service.delete_index(index_id)
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete index: {str(e)}"
            )
    
    # Embedding endpoints
    @router.post(
        "/embeddings",
        response_model=EmbeddingDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create embedding",
        description="Create a new embedding from content"
    )
    async def create_embedding(
        request: CreateEmbeddingDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> EmbeddingDTO:
        """Create a new embedding from content."""
        try:
            # Convert types
            model = EmbeddingModel(request.model) if request.model else EmbeddingModel.DEFAULT
            
            # Create embedding
            result = await embedding_service.create_embedding(
                request.source_id,
                request.source_type,
                request.content,
                model,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            
            embedding = result.value
            
            # Convert to DTO
            return EmbeddingDTO(
                id=embedding.id.value,
                vector=embedding.vector,
                source_id=embedding.source_id,
                source_type=embedding.source_type,
                model=embedding.model.value,
                dimension=embedding.dimension,
                created_at=embedding.created_at,
                metadata=embedding.metadata
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create embedding: {str(e)}"
            )
    
    @router.post(
        "/embeddings/with-vector",
        response_model=EmbeddingDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create embedding with vector",
        description="Create a new embedding using a pre-generated vector"
    )
    async def create_embedding_with_vector(
        request: CreateEmbeddingWithVectorDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> EmbeddingDTO:
        """Create a new embedding using a pre-generated vector."""
        try:
            # Convert types
            model = EmbeddingModel(request.model) if request.model else EmbeddingModel.DEFAULT
            
            # Create embedding
            result = await embedding_service.create_embedding_with_vector(
                request.source_id,
                request.source_type,
                request.vector,
                model,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            
            embedding = result.value
            
            # Convert to DTO
            return EmbeddingDTO(
                id=embedding.id.value,
                vector=embedding.vector,
                source_id=embedding.source_id,
                source_type=embedding.source_type,
                model=embedding.model.value,
                dimension=embedding.dimension,
                created_at=embedding.created_at,
                metadata=embedding.metadata
            )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create embedding with vector: {str(e)}"
            )
    
    @router.get(
        "/embeddings/{embedding_id}",
        response_model=EmbeddingDTO,
        summary="Get embedding",
        description="Get an embedding by ID"
    )
    async def get_embedding(
        embedding_id: str,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> EmbeddingDTO:
        """Get an embedding by ID."""
        try:
            # Get embedding
            result = await embedding_service.get_embedding(embedding_id)
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            embedding = result.value
            
            # Convert to DTO
            return EmbeddingDTO(
                id=embedding.id.value,
                vector=embedding.vector,
                source_id=embedding.source_id,
                source_type=embedding.source_type,
                model=embedding.model.value,
                dimension=embedding.dimension,
                created_at=embedding.created_at,
                metadata=embedding.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get embedding: {str(e)}"
            )
    
    @router.put(
        "/embeddings/{embedding_id}",
        response_model=EmbeddingDTO,
        summary="Update embedding",
        description="Update an embedding"
    )
    async def update_embedding(
        embedding_id: str,
        request: UpdateEmbeddingDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> EmbeddingDTO:
        """Update an embedding."""
        try:
            # Update embedding
            result = await embedding_service.update_embedding(
                embedding_id,
                request.content,
                request.vector,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            embedding = result.value
            
            # Convert to DTO
            return EmbeddingDTO(
                id=embedding.id.value,
                vector=embedding.vector,
                source_id=embedding.source_id,
                source_type=embedding.source_type,
                model=embedding.model.value,
                dimension=embedding.dimension,
                created_at=embedding.created_at,
                metadata=embedding.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update embedding: {str(e)}"
            )
    
    @router.delete(
        "/embeddings/{embedding_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete embedding",
        description="Delete an embedding"
    )
    async def delete_embedding(
        embedding_id: str,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> None:
        """Delete an embedding."""
        try:
            # Delete embedding
            result = await embedding_service.delete_embedding(embedding_id)
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete embedding: {str(e)}"
            )
    
    # Search endpoints
    @router.post(
        "/search/text",
        response_model=List[SearchResultDTO],
        summary="Text search",
        description="Search using text"
    )
    async def search_by_text(
        request: TextSearchDTO,
        search_service: SearchService = Depends(get_search_service)
    ) -> List[SearchResultDTO]:
        """Search using text."""
        try:
            # Perform search
            result = await search_service.search_by_text(
                request.query,
                request.limit,
                request.threshold,
                request.metric,
                None,
                request.filters,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            search_results = result.value
            
            # Convert to DTOs
            return [
                SearchResultDTO(
                    id=sr.id,
                    similarity=sr.similarity,
                    entity_id=sr.entity_id,
                    entity_type=sr.entity_type,
                    rank=sr.rank,
                    metadata=sr.metadata
                )
                for sr in search_results
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search by text: {str(e)}"
            )
    
    @router.post(
        "/search/vector",
        response_model=List[SearchResultDTO],
        summary="Vector search",
        description="Search using a vector"
    )
    async def search_by_vector(
        request: VectorSearchDTO,
        search_service: SearchService = Depends(get_search_service)
    ) -> List[SearchResultDTO]:
        """Search using a vector."""
        try:
            # Perform search
            result = await search_service.search_by_vector(
                request.vector,
                request.limit,
                request.threshold,
                request.metric,
                None,
                request.filters,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            search_results = result.value
            
            # Convert to DTOs
            return [
                SearchResultDTO(
                    id=sr.id,
                    similarity=sr.similarity,
                    entity_id=sr.entity_id,
                    entity_type=sr.entity_type,
                    rank=sr.rank,
                    metadata=sr.metadata
                )
                for sr in search_results
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search by vector: {str(e)}"
            )
    
    @router.post(
        "/search/hybrid",
        response_model=List[SearchResultDTO],
        summary="Hybrid search",
        description="Search using hybrid of vector and graph"
    )
    async def hybrid_search(
        request: HybridSearchDTO,
        search_service: SearchService = Depends(get_search_service)
    ) -> List[SearchResultDTO]:
        """Search using hybrid of vector and graph."""
        try:
            # Perform hybrid search
            result = await search_service.hybrid_search(
                request.query,
                request.start_node_type,
                request.path_pattern,
                request.limit,
                request.threshold,
                request.metric,
                request.start_filters,
                request.combine_method,
                request.graph_weight,
                request.vector_weight,
                request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            search_results = result.value
            
            # Convert to DTOs
            return [
                SearchResultDTO(
                    id=sr.id,
                    similarity=sr.similarity,
                    entity_id=sr.entity_id,
                    entity_type=sr.entity_type,
                    rank=sr.rank,
                    metadata=sr.metadata
                )
                for sr in search_results
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to perform hybrid search: {str(e)}"
            )
    
    @router.post(
        "/generate-embedding",
        summary="Generate embedding",
        description="Generate an embedding vector for text"
    )
    async def generate_embedding(
        request: GenerateEmbeddingDTO,
        search_service: SearchService = Depends(get_search_service)
    ) -> Dict[str, Any]:
        """Generate an embedding vector for text."""
        try:
            # Generate embedding
            result = await search_service.generate_embedding(request.text)
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            vector = result.value
            
            # Return embedding info
            return {
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "dimensions": len(vector),
                "embedding": vector
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate embedding: {str(e)}"
            )
    
    # RAG endpoints
    @router.post(
        "/rag/prompt",
        response_model=RAGPromptResponseDTO,
        summary="Create RAG prompt",
        description="Create a RAG prompt with retrieved context"
    )
    async def create_rag_prompt(
        request: RAGPromptDTO,
        rag_service: RAGService = Depends(get_rag_service)
    ) -> RAGPromptResponseDTO:
        """Create a RAG prompt with retrieved context."""
        try:
            # Create RAG prompt
            result = await rag_service.create_rag_prompt(
                request.query,
                request.system_prompt,
                request.limit,
                request.threshold,
                request.filters
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            prompt = result.value
            
            # Return prompt
            return RAGPromptResponseDTO(
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create RAG prompt: {str(e)}"
            )
    
    # Document endpoints
    @router.post(
        "/documents",
        status_code=status.HTTP_201_CREATED,
        summary="Index document",
        description="Index a document for vector search"
    )
    async def index_document(
        document: DocumentDTO,
        vector_search_service: VectorSearchService = Depends(get_vector_search_service)
    ) -> Dict[str, Any]:
        """Index a document for vector search."""
        try:
            # Extract content
            content = document.content
            if document.title:
                content = f"{document.title}\n\n{content}"
            
            # Create metadata
            metadata = document.metadata or {}
            if document.title:
                metadata["title"] = document.title
            
            # Index document
            result = await vector_search_service.index_document(
                document.id,
                content,
                metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result.error
                )
            
            embedding = result.value
            
            # Return success
            return {
                "id": document.id,
                "embedding_id": embedding.id.value,
                "dimensions": embedding.dimension,
                "status": "indexed"
            }
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to index document: {str(e)}"
            )
    
    @router.post(
        "/documents/search",
        response_model=List[SearchResultDTO],
        summary="Search documents",
        description="Search documents using vector similarity"
    )
    async def search_documents(
        query: Annotated[str, Body(..., description="Query text")],
        limit: Annotated[int, Body(10, description="Maximum number of results")],
        threshold: Annotated[float, Body(0.7, description="Minimum similarity threshold")],
        vector_search_service: VectorSearchService = Depends(get_vector_search_service)
    ) -> List[SearchResultDTO]:
        """Search documents using vector similarity."""
        try:
            # Search documents
            result = await vector_search_service.search_documents(
                query,
                limit,
                threshold
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            search_results = result.value
            
            # Convert to DTOs
            return [
                SearchResultDTO(
                    id=sr.id,
                    similarity=sr.similarity,
                    entity_id=sr.entity_id,
                    entity_type=sr.entity_type,
                    rank=sr.rank,
                    metadata=sr.metadata
                )
                for sr in search_results
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to search documents: {str(e)}"
            )
    
    @router.post(
        "/documents/rag",
        response_model=RAGPromptResponseDTO,
        summary="Generate document RAG prompt",
        description="Generate a RAG prompt using document search"
    )
    async def generate_document_rag_prompt(
        query: Annotated[str, Body(..., description="Query text")],
        system_prompt: Annotated[str, Body(..., description="System prompt")],
        limit: Annotated[int, Body(3, description="Maximum number of results")],
        threshold: Annotated[float, Body(0.7, description="Minimum similarity threshold")],
        vector_search_service: VectorSearchService = Depends(get_vector_search_service)
    ) -> RAGPromptResponseDTO:
        """Generate a RAG prompt using document search."""
        try:
            # Generate RAG prompt
            result = await vector_search_service.generate_rag_prompt(
                query,
                system_prompt,
                limit,
                threshold
            )
            
            if isinstance(result, Failure):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            prompt = result.value
            
            # Return prompt
            return RAGPromptResponseDTO(
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"]
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to generate document RAG prompt: {str(e)}"
            )
    
    return router


# Create router for direct use
vector_search_router = create_vector_search_router()