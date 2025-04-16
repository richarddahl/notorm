"""
Domain endpoints for the AI module.

This module defines FastAPI endpoints for the AI module,
providing a RESTful API for AI features like embeddings, semantic search,
recommendations, content generation, and anomaly detection.
"""

from typing import Dict, List, Optional, Any, Union, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Body, Query, Path
from pydantic import BaseModel, Field

from uno.core.result import Success, Failure
from uno.ai.domain_services import (
    EmbeddingModelService,
    EmbeddingService,
    SemanticSearchService,
    RAGService
)
from uno.ai.domain_provider import (
    get_embedding_model_service,
    get_embedding_service,
    get_semantic_search_service,
    get_rag_service
)
from uno.ai.entities import (
    EmbeddingModelType,
    ContentGenerationType,
    AnomalyDetectionMethod,
    RecommendationMethod,
    SimilarityMetric
)


# DTOs
class EmbeddingModelDTO(BaseModel):
    """DTO for embedding models."""
    
    id: str = Field(..., description="Model ID")
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type")
    dimensions: int = Field(..., description="Number of dimensions")
    normalize_vectors: bool = Field(..., description="Whether to normalize vectors")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Model metadata")


class CreateEmbeddingModelDTO(BaseModel):
    """DTO for creating embedding models."""
    
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type (sentence_transformer, huggingface, openai, custom)")
    dimensions: int = Field(..., description="Number of dimensions")
    api_key: Optional[str] = Field(None, description="API key for the model")
    normalize_vectors: bool = Field(True, description="Whether to normalize vectors")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Model metadata")


class UpdateEmbeddingModelDTO(BaseModel):
    """DTO for updating embedding models."""
    
    name: Optional[str] = Field(None, description="New model name")
    api_key: Optional[str] = Field(None, description="New API key")
    normalize_vectors: Optional[bool] = Field(None, description="New normalization setting")
    metadata: Optional[Dict[str, Any]] = Field(None, description="New metadata")


class EmbeddingDTO(BaseModel):
    """DTO for embeddings."""
    
    id: str = Field(..., description="Embedding ID")
    vector: List[float] = Field(..., description="Embedding vector")
    model_id: str = Field(..., description="Model ID")
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    dimensions: int = Field(..., description="Number of dimensions")
    created_at: datetime = Field(..., description="Creation timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Embedding metadata")


class GenerateEmbeddingDTO(BaseModel):
    """DTO for generating embeddings."""
    
    text: str = Field(..., description="Text to embed")
    model_name: Optional[str] = Field(None, description="Model name to use")


class CreateEmbeddingDTO(BaseModel):
    """DTO for creating embeddings."""
    
    text: str = Field(..., description="Text to embed")
    source_id: str = Field(..., description="Source ID")
    source_type: str = Field(..., description="Source type")
    model_name: Optional[str] = Field(None, description="Model name to use")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Embedding metadata")


class BatchCreateEmbeddingDTO(BaseModel):
    """DTO for batch creating embeddings."""
    
    texts: List[str] = Field(..., description="Texts to embed")
    source_ids: List[str] = Field(..., description="Source IDs")
    source_type: str = Field(..., description="Source type")
    model_name: Optional[str] = Field(None, description="Model name to use")
    metadata_list: Optional[List[Dict[str, Any]]] = Field(None, description="List of metadata dictionaries")


class ComputeSimilarityDTO(BaseModel):
    """DTO for computing similarity."""
    
    vector1: List[float] = Field(..., description="First embedding vector")
    vector2: List[float] = Field(..., description="Second embedding vector")
    metric: str = Field("cosine", description="Similarity metric (cosine, euclidean, dot_product)")


class DocumentIndexDTO(BaseModel):
    """DTO for document indices."""
    
    id: str = Field(..., description="Document ID")
    content: str = Field(..., description="Document content")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    embedding_id: Optional[str] = Field(None, description="Embedding ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")


class IndexDocumentDTO(BaseModel):
    """DTO for indexing documents."""
    
    content: str = Field(..., description="Document content")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")


class BatchIndexDocumentDTO(BaseModel):
    """DTO for batch indexing documents."""
    
    contents: List[str] = Field(..., description="Document contents")
    entity_ids: List[str] = Field(..., description="Entity IDs")
    entity_type: str = Field(..., description="Entity type")
    metadata_list: Optional[List[Dict[str, Any]]] = Field(None, description="List of metadata dictionaries")


class SearchQueryDTO(BaseModel):
    """DTO for search queries."""
    
    query_text: str = Field(..., description="Search query text")
    user_id: Optional[str] = Field(None, description="User ID")
    entity_type: Optional[str] = Field(None, description="Entity type filter")


class SearchResultDTO(BaseModel):
    """DTO for search results."""
    
    id: str = Field(..., description="Result ID")
    entity_id: str = Field(..., description="Entity ID")
    entity_type: str = Field(..., description="Entity type")
    similarity: float = Field(..., description="Similarity score")
    rank: int = Field(..., description="Result rank")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Result metadata")


class RAGPromptDTO(BaseModel):
    """DTO for RAG prompts."""
    
    query: str = Field(..., description="Query text")
    system_prompt: str = Field(..., description="System prompt")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    entity_id: Optional[str] = Field(None, description="Entity ID")
    entity_type: Optional[str] = Field(None, description="Entity type")


class RAGPromptResponseDTO(BaseModel):
    """DTO for RAG prompt responses."""
    
    system_prompt: str = Field(..., description="System prompt")
    user_prompt: str = Field(..., description="User prompt with context")


# Router factory
def create_ai_router() -> APIRouter:
    """
    Create FastAPI router for AI endpoints.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(
        prefix="/api/ai",
        tags=["ai"],
        responses={401: {"description": "Unauthorized"}},
    )
    
    # Embedding model endpoints
    @router.post(
        "/embedding-models",
        response_model=EmbeddingModelDTO,
        status_code=201,
        summary="Create embedding model",
        description="Create a new embedding model"
    )
    async def create_embedding_model(
        request: CreateEmbeddingModelDTO,
        model_service: EmbeddingModelService = Depends(get_embedding_model_service)
    ) -> EmbeddingModelDTO:
        """Create a new embedding model."""
        try:
            # Convert model type
            model_type = EmbeddingModelType(request.model_type)
            
            # Create model
            result = await model_service.create_model(
                name=request.name,
                model_type=model_type,
                dimensions=request.dimensions,
                api_key=request.api_key,
                normalize_vectors=request.normalize_vectors,
                metadata=request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            model = result.value
            
            # Convert to DTO
            return EmbeddingModelDTO(
                id=model.id.value,
                name=model.name,
                model_type=model.model_type.value,
                dimensions=model.dimensions,
                normalize_vectors=model.normalize_vectors,
                created_at=model.created_at,
                metadata=model.metadata
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create embedding model: {str(e)}")
    
    @router.get(
        "/embedding-models/{model_id}",
        response_model=EmbeddingModelDTO,
        summary="Get embedding model",
        description="Get an embedding model by ID"
    )
    async def get_embedding_model(
        model_id: str,
        model_service: EmbeddingModelService = Depends(get_embedding_model_service)
    ) -> EmbeddingModelDTO:
        """Get an embedding model by ID."""
        try:
            result = await model_service.get_model(model_id)
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=404, detail=result.error)
            
            model = result.value
            
            # Convert to DTO
            return EmbeddingModelDTO(
                id=model.id.value,
                name=model.name,
                model_type=model.model_type.value,
                dimensions=model.dimensions,
                normalize_vectors=model.normalize_vectors,
                created_at=model.created_at,
                metadata=model.metadata
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get embedding model: {str(e)}")
    
    @router.get(
        "/embedding-models",
        response_model=List[EmbeddingModelDTO],
        summary="List embedding models",
        description="List all embedding models"
    )
    async def list_embedding_models(
        model_service: EmbeddingModelService = Depends(get_embedding_model_service)
    ) -> List[EmbeddingModelDTO]:
        """List all embedding models."""
        try:
            result = await model_service.list_models()
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=500, detail=result.error)
            
            models = result.value
            
            # Convert to DTOs
            return [
                EmbeddingModelDTO(
                    id=model.id.value,
                    name=model.name,
                    model_type=model.model_type.value,
                    dimensions=model.dimensions,
                    normalize_vectors=model.normalize_vectors,
                    created_at=model.created_at,
                    metadata=model.metadata
                )
                for model in models
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list embedding models: {str(e)}")
    
    @router.put(
        "/embedding-models/{model_id}",
        response_model=EmbeddingModelDTO,
        summary="Update embedding model",
        description="Update an embedding model"
    )
    async def update_embedding_model(
        model_id: str,
        request: UpdateEmbeddingModelDTO,
        model_service: EmbeddingModelService = Depends(get_embedding_model_service)
    ) -> EmbeddingModelDTO:
        """Update an embedding model."""
        try:
            result = await model_service.update_model(
                model_id=model_id,
                name=request.name,
                api_key=request.api_key,
                normalize_vectors=request.normalize_vectors,
                metadata=request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=404, detail=result.error)
            
            model = result.value
            
            # Convert to DTO
            return EmbeddingModelDTO(
                id=model.id.value,
                name=model.name,
                model_type=model.model_type.value,
                dimensions=model.dimensions,
                normalize_vectors=model.normalize_vectors,
                created_at=model.created_at,
                metadata=model.metadata
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to update embedding model: {str(e)}")
    
    @router.delete(
        "/embedding-models/{model_id}",
        status_code=204,
        summary="Delete embedding model",
        description="Delete an embedding model"
    )
    async def delete_embedding_model(
        model_id: str,
        model_service: EmbeddingModelService = Depends(get_embedding_model_service)
    ) -> None:
        """Delete an embedding model."""
        try:
            result = await model_service.delete_model(model_id)
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=404, detail=result.error)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete embedding model: {str(e)}")
    
    # Embedding endpoints
    @router.post(
        "/embeddings/generate",
        summary="Generate embedding",
        description="Generate an embedding vector for text"
    )
    async def generate_embedding(
        request: GenerateEmbeddingDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> Dict[str, Any]:
        """Generate an embedding vector for text."""
        try:
            result = await embedding_service.generate_embedding(
                text=request.text,
                model_name=request.model_name
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            vector = result.value
            
            return {
                "text": request.text[:100] + "..." if len(request.text) > 100 else request.text,
                "dimensions": len(vector),
                "vector": vector,
                "model_name": request.model_name or "default"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")
    
    @router.post(
        "/embeddings",
        response_model=EmbeddingDTO,
        status_code=201,
        summary="Create embedding",
        description="Create and store an embedding for text"
    )
    async def create_embedding(
        request: CreateEmbeddingDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> EmbeddingDTO:
        """Create and store an embedding for text."""
        try:
            result = await embedding_service.create_embedding(
                text=request.text,
                source_id=request.source_id,
                source_type=request.source_type,
                model_name=request.model_name,
                metadata=request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            embedding = result.value
            
            # Convert to DTO
            return EmbeddingDTO(
                id=embedding.id.value,
                vector=embedding.vector,
                model_id=embedding.model_id.value,
                source_id=embedding.source_id,
                source_type=embedding.source_type,
                dimensions=embedding.dimensions,
                created_at=embedding.created_at,
                metadata=embedding.metadata
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create embedding: {str(e)}")
    
    @router.post(
        "/embeddings/batch",
        response_model=List[EmbeddingDTO],
        status_code=201,
        summary="Batch create embeddings",
        description="Batch create embeddings for multiple texts"
    )
    async def batch_create_embeddings(
        request: BatchCreateEmbeddingDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> List[EmbeddingDTO]:
        """Batch create embeddings for multiple texts."""
        try:
            if len(request.texts) != len(request.source_ids):
                raise HTTPException(status_code=400, detail="Number of texts and source IDs must match")
            
            if request.metadata_list and len(request.metadata_list) != len(request.texts):
                raise HTTPException(status_code=400, detail="Number of metadata items must match number of texts")
            
            result = await embedding_service.batch_create_embeddings(
                texts=request.texts,
                source_ids=request.source_ids,
                source_type=request.source_type,
                model_name=request.model_name,
                metadata_list=request.metadata_list
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            embeddings = result.value
            
            # Convert to DTOs
            return [
                EmbeddingDTO(
                    id=embedding.id.value,
                    vector=embedding.vector,
                    model_id=embedding.model_id.value,
                    source_id=embedding.source_id,
                    source_type=embedding.source_type,
                    dimensions=embedding.dimensions,
                    created_at=embedding.created_at,
                    metadata=embedding.metadata
                )
                for embedding in embeddings
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to batch create embeddings: {str(e)}")
    
    @router.post(
        "/embeddings/similarity",
        summary="Compute similarity",
        description="Compute similarity between two embedding vectors"
    )
    async def compute_similarity(
        request: ComputeSimilarityDTO,
        embedding_service: EmbeddingService = Depends(get_embedding_service)
    ) -> Dict[str, Any]:
        """Compute similarity between two embedding vectors."""
        try:
            result = await embedding_service.compute_similarity(
                embedding1=request.vector1,
                embedding2=request.vector2,
                metric=request.metric
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            similarity = result.value
            
            return {
                "similarity": similarity,
                "metric": request.metric
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to compute similarity: {str(e)}")
    
    # Semantic search endpoints
    @router.post(
        "/search/index",
        response_model=DocumentIndexDTO,
        status_code=201,
        summary="Index document",
        description="Index a document for semantic search"
    )
    async def index_document(
        request: IndexDocumentDTO,
        search_service: SemanticSearchService = Depends(get_semantic_search_service)
    ) -> DocumentIndexDTO:
        """Index a document for semantic search."""
        try:
            result = await search_service.index_document(
                content=request.content,
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                metadata=request.metadata
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            document = result.value
            
            # Convert to DTO
            return DocumentIndexDTO(
                id=document.id,
                content=document.content,
                entity_id=document.entity_id,
                entity_type=document.entity_type,
                embedding_id=document.embedding_id.value if document.embedding_id else None,
                created_at=document.created_at,
                updated_at=document.updated_at,
                metadata=document.metadata
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")
    
    @router.post(
        "/search/index/batch",
        response_model=List[DocumentIndexDTO],
        status_code=201,
        summary="Batch index documents",
        description="Batch index documents for semantic search"
    )
    async def batch_index_documents(
        request: BatchIndexDocumentDTO,
        search_service: SemanticSearchService = Depends(get_semantic_search_service)
    ) -> List[DocumentIndexDTO]:
        """Batch index documents for semantic search."""
        try:
            if len(request.contents) != len(request.entity_ids):
                raise HTTPException(status_code=400, detail="Number of contents and entity IDs must match")
            
            if request.metadata_list and len(request.metadata_list) != len(request.contents):
                raise HTTPException(status_code=400, detail="Number of metadata items must match number of contents")
            
            result = await search_service.batch_index(
                contents=request.contents,
                entity_ids=request.entity_ids,
                entity_type=request.entity_type,
                metadata_list=request.metadata_list
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            documents = result.value
            
            # Convert to DTOs
            return [
                DocumentIndexDTO(
                    id=document.id,
                    content=document.content,
                    entity_id=document.entity_id,
                    entity_type=document.entity_type,
                    embedding_id=document.embedding_id.value if document.embedding_id else None,
                    created_at=document.created_at,
                    updated_at=document.updated_at,
                    metadata=document.metadata
                )
                for document in documents
            ]
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to batch index documents: {str(e)}")
    
    @router.post(
        "/search",
        response_model=List[SearchResultDTO],
        summary="Semantic search",
        description="Perform a semantic search"
    )
    async def semantic_search(
        request: SearchQueryDTO,
        limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
        similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
        search_service: SemanticSearchService = Depends(get_semantic_search_service)
    ) -> List[SearchResultDTO]:
        """Perform a semantic search."""
        try:
            result = await search_service.search(
                query_text=request.query_text,
                user_id=request.user_id,
                entity_type=request.entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            search_results = result.value
            
            # Convert to DTOs
            return [
                SearchResultDTO(
                    id=sr.id,
                    entity_id=sr.entity_id,
                    entity_type=sr.entity_type,
                    similarity=sr.similarity,
                    rank=sr.rank,
                    metadata=sr.metadata
                )
                for sr in search_results
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to perform search: {str(e)}")
    
    @router.delete(
        "/search/documents/{entity_id}",
        status_code=200,
        summary="Delete document",
        description="Delete document from the search index"
    )
    async def delete_document(
        entity_id: str,
        entity_type: Optional[str] = Query(None, description="Entity type filter"),
        search_service: SemanticSearchService = Depends(get_semantic_search_service)
    ) -> Dict[str, Any]:
        """Delete document from the search index."""
        try:
            result = await search_service.delete_document(
                entity_id=entity_id,
                entity_type=entity_type
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            count = result.value
            
            return {
                "deleted": count,
                "entity_id": entity_id
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")
    
    # RAG endpoints
    @router.post(
        "/rag/prompt",
        response_model=RAGPromptResponseDTO,
        summary="Create RAG prompt",
        description="Create a RAG prompt with retrieved context"
    )
    async def create_rag_prompt(
        request: RAGPromptDTO,
        limit: int = Query(5, ge=1, le=10, description="Maximum number of results to retrieve"),
        similarity_threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold"),
        rag_service: RAGService = Depends(get_rag_service)
    ) -> RAGPromptResponseDTO:
        """Create a RAG prompt with retrieved context."""
        try:
            result = await rag_service.create_rag_prompt(
                query=request.query,
                system_prompt=request.system_prompt,
                user_id=request.user_id,
                session_id=request.session_id,
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold
            )
            
            if isinstance(result, Failure):
                raise HTTPException(status_code=400, detail=result.error)
            
            prompt = result.value
            
            # Convert to DTO
            return RAGPromptResponseDTO(
                system_prompt=prompt["system_prompt"],
                user_prompt=prompt["user_prompt"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create RAG prompt: {str(e)}")
    
    return router


# Create router instance
ai_router = create_ai_router()