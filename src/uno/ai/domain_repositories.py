"""
Domain repositories for the AI module.

This module defines repository interfaces and implementations for the AI module,
providing data access patterns for AI features like embeddings, semantic search,
recommendations, content generation, and anomaly detection.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, TypeVar, Generic

from uno.core.result import Result
from uno.domain.repository import AsyncDomainRepository

from uno.ai.entities import (
    EmbeddingId,
    SearchQueryId,
    RecommendationId,
    ContentRequestId,
    AnomalyDetectionId,
    ModelId,
    EmbeddingModel,
    Embedding,
    SearchQuery,
    SearchResult,
    DocumentIndex,
    RecommendationProfile,
    RecommendationRequest,
    Recommendation,
    ContentRequest,
    GeneratedContent,
    AnomalyDetectionConfig,
    AnomalyDetectionRequest,
    AnomalyDetectionResult,
    AIContext,
    RAGQuery,
    EmbeddingModelType,
    ContentGenerationType,
    AnomalyDetectionMethod,
    RecommendationMethod
)


@runtime_checkable
class EmbeddingModelRepositoryProtocol(Protocol):
    """Protocol for embedding model repository."""
    
    async def create(self, model: EmbeddingModel) -> Result[EmbeddingModel]:
        """
        Create a new embedding model.
        
        Args:
            model: Model to create
            
        Returns:
            Result containing the created model or an error
        """
        ...
    
    async def get(self, model_id: ModelId) -> Result[EmbeddingModel]:
        """
        Get an embedding model by ID.
        
        Args:
            model_id: Model ID
            
        Returns:
            Result containing the model or an error if not found
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[EmbeddingModel]:
        """
        Get an embedding model by name.
        
        Args:
            name: Model name
            
        Returns:
            Result containing the model or an error if not found
        """
        ...
    
    async def update(self, model: EmbeddingModel) -> Result[EmbeddingModel]:
        """
        Update an embedding model.
        
        Args:
            model: Updated model
            
        Returns:
            Result containing the updated model or an error
        """
        ...
    
    async def delete(self, model_id: ModelId) -> Result[bool]:
        """
        Delete an embedding model.
        
        Args:
            model_id: Model ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def list(self) -> Result[List[EmbeddingModel]]:
        """
        List all embedding models.
        
        Returns:
            Result containing a list of models or an error
        """
        ...


@runtime_checkable
class EmbeddingRepositoryProtocol(Protocol):
    """Protocol for embedding repository."""
    
    async def create(self, embedding: Embedding) -> Result[Embedding]:
        """
        Create a new embedding.
        
        Args:
            embedding: Embedding to create
            
        Returns:
            Result containing the created embedding or an error
        """
        ...
    
    async def get(self, embedding_id: EmbeddingId) -> Result[Embedding]:
        """
        Get an embedding by ID.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing the embedding or an error if not found
        """
        ...
    
    async def get_by_source(self, source_id: str, source_type: str) -> Result[Embedding]:
        """
        Get an embedding by source.
        
        Args:
            source_id: Source ID
            source_type: Source type
            
        Returns:
            Result containing the embedding or an error if not found
        """
        ...
    
    async def update(self, embedding: Embedding) -> Result[Embedding]:
        """
        Update an embedding.
        
        Args:
            embedding: Updated embedding
            
        Returns:
            Result containing the updated embedding or an error
        """
        ...
    
    async def delete(self, embedding_id: EmbeddingId) -> Result[bool]:
        """
        Delete an embedding.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def batch_create(self, embeddings: List[Embedding]) -> Result[List[Embedding]]:
        """
        Batch create embeddings.
        
        Args:
            embeddings: List of embeddings to create
            
        Returns:
            Result containing the created embeddings or an error
        """
        ...


@runtime_checkable
class SearchRepositoryProtocol(Protocol):
    """Protocol for semantic search repository."""
    
    async def index_document(self, document: DocumentIndex) -> Result[DocumentIndex]:
        """
        Index a document for search.
        
        Args:
            document: Document to index
            
        Returns:
            Result containing the indexed document or an error
        """
        ...
    
    async def batch_index(self, documents: List[DocumentIndex]) -> Result[List[DocumentIndex]]:
        """
        Batch index documents.
        
        Args:
            documents: List of documents to index
            
        Returns:
            Result containing the indexed documents or an error
        """
        ...
    
    async def search(
        self,
        query: SearchQuery,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """
        Perform a semantic search.
        
        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of search results or an error
        """
        ...
    
    async def search_by_vector(
        self,
        vector: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """
        Perform a search using a vector.
        
        Args:
            vector: Query vector
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity threshold
            
        Returns:
            Result containing a list of search results or an error
        """
        ...
    
    async def delete_document(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> Result[int]:
        """
        Delete document from the index.
        
        Args:
            entity_id: Entity ID
            entity_type: Optional entity type filter
            
        Returns:
            Result containing the count of deleted documents or an error
        """
        ...
    
    async def get_document(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> Result[DocumentIndex]:
        """
        Get an indexed document.
        
        Args:
            entity_id: Entity ID
            entity_type: Optional entity type filter
            
        Returns:
            Result containing the document or an error if not found
        """
        ...


@runtime_checkable
class RecommendationRepositoryProtocol(Protocol):
    """Protocol for recommendation repository."""
    
    async def create_profile(self, profile: RecommendationProfile) -> Result[RecommendationProfile]:
        """
        Create a recommendation profile.
        
        Args:
            profile: Profile to create
            
        Returns:
            Result containing the created profile or an error
        """
        ...
    
    async def get_profile(self, user_id: str) -> Result[RecommendationProfile]:
        """
        Get a recommendation profile by user ID.
        
        Args:
            user_id: User ID
            
        Returns:
            Result containing the profile or an error if not found
        """
        ...
    
    async def update_profile(self, profile: RecommendationProfile) -> Result[RecommendationProfile]:
        """
        Update a recommendation profile.
        
        Args:
            profile: Updated profile
            
        Returns:
            Result containing the updated profile or an error
        """
        ...
    
    async def save_request(self, request: RecommendationRequest) -> Result[RecommendationRequest]:
        """
        Save a recommendation request.
        
        Args:
            request: Request to save
            
        Returns:
            Result containing the saved request or an error
        """
        ...
    
    async def save_recommendations(self, recommendations: List[Recommendation]) -> Result[List[Recommendation]]:
        """
        Save recommendations.
        
        Args:
            recommendations: Recommendations to save
            
        Returns:
            Result containing the saved recommendations or an error
        """
        ...
    
    async def get_recommendations(
        self,
        request_id: RecommendationId
    ) -> Result[List[Recommendation]]:
        """
        Get recommendations by request ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            Result containing a list of recommendations or an error
        """
        ...


@runtime_checkable
class ContentGenerationRepositoryProtocol(Protocol):
    """Protocol for content generation repository."""
    
    async def save_request(self, request: ContentRequest) -> Result[ContentRequest]:
        """
        Save a content generation request.
        
        Args:
            request: Request to save
            
        Returns:
            Result containing the saved request or an error
        """
        ...
    
    async def save_content(self, content: GeneratedContent) -> Result[GeneratedContent]:
        """
        Save generated content.
        
        Args:
            content: Content to save
            
        Returns:
            Result containing the saved content or an error
        """
        ...
    
    async def get_content(self, request_id: ContentRequestId) -> Result[GeneratedContent]:
        """
        Get generated content by request ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            Result containing the content or an error if not found
        """
        ...


@runtime_checkable
class AnomalyDetectionRepositoryProtocol(Protocol):
    """Protocol for anomaly detection repository."""
    
    async def save_config(self, config: AnomalyDetectionConfig) -> Result[AnomalyDetectionConfig]:
        """
        Save an anomaly detection configuration.
        
        Args:
            config: Configuration to save
            
        Returns:
            Result containing the saved configuration or an error
        """
        ...
    
    async def get_config(self, config_id: str) -> Result[AnomalyDetectionConfig]:
        """
        Get an anomaly detection configuration by ID.
        
        Args:
            config_id: Configuration ID
            
        Returns:
            Result containing the configuration or an error if not found
        """
        ...
    
    async def list_configs(self) -> Result[List[AnomalyDetectionConfig]]:
        """
        List all anomaly detection configurations.
        
        Returns:
            Result containing a list of configurations or an error
        """
        ...
    
    async def save_request(self, request: AnomalyDetectionRequest) -> Result[AnomalyDetectionRequest]:
        """
        Save an anomaly detection request.
        
        Args:
            request: Request to save
            
        Returns:
            Result containing the saved request or an error
        """
        ...
    
    async def save_result(self, result: AnomalyDetectionResult) -> Result[AnomalyDetectionResult]:
        """
        Save an anomaly detection result.
        
        Args:
            result: Result to save
            
        Returns:
            Result containing the saved result or an error
        """
        ...
    
    async def get_result(self, request_id: AnomalyDetectionId) -> Result[AnomalyDetectionResult]:
        """
        Get an anomaly detection result by request ID.
        
        Args:
            request_id: Request ID
            
        Returns:
            Result containing the result or an error if not found
        """
        ...


@runtime_checkable
class AIContextRepositoryProtocol(Protocol):
    """Protocol for AI context repository."""
    
    async def save_context(self, context: AIContext) -> Result[AIContext]:
        """
        Save an AI context.
        
        Args:
            context: Context to save
            
        Returns:
            Result containing the saved context or an error
        """
        ...
    
    async def get_user_context(
        self,
        user_id: str,
        limit: int = 10
    ) -> Result[List[AIContext]]:
        """
        Get context for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of contexts to return
            
        Returns:
            Result containing a list of contexts or an error
        """
        ...
    
    async def get_session_context(
        self,
        session_id: str,
        limit: int = 10
    ) -> Result[List[AIContext]]:
        """
        Get context for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of contexts to return
            
        Returns:
            Result containing a list of contexts or an error
        """
        ...
    
    async def get_entity_context(
        self,
        entity_id: str,
        entity_type: Optional[str] = None,
        limit: int = 10
    ) -> Result[List[AIContext]]:
        """
        Get context for an entity.
        
        Args:
            entity_id: Entity ID
            entity_type: Optional entity type filter
            limit: Maximum number of contexts to return
            
        Returns:
            Result containing a list of contexts or an error
        """
        ...


# Repository Implementations
class EmbeddingModelRepository(AsyncDomainRepository, EmbeddingModelRepositoryProtocol):
    """Repository implementation for embedding models."""
    
    async def create(self, model: EmbeddingModel) -> Result[EmbeddingModel]:
        """Create a new embedding model."""
        try:
            async with self.session() as session:
                # Check if model with same name already exists
                query = """
                SELECT id FROM ai_embedding_models WHERE name = :name
                """
                result = await session.execute(query, {"name": model.name})
                existing = await result.fetchone()
                
                if existing:
                    return Result.failure(f"Embedding model with name '{model.name}' already exists")
                
                # Insert new model
                query = """
                INSERT INTO ai_embedding_models (
                    id, name, model_type, dimensions, api_key, normalize_vectors, metadata, created_at
                ) VALUES (
                    :id, :name, :model_type, :dimensions, :api_key, :normalize_vectors, :metadata, :created_at
                ) RETURNING id
                """
                
                params = {
                    "id": model.id.value,
                    "name": model.name,
                    "model_type": model.model_type.value,
                    "dimensions": model.dimensions,
                    "api_key": model.api_key,
                    "normalize_vectors": model.normalize_vectors,
                    "metadata": model.metadata,
                    "created_at": model.created_at
                }
                
                result = await session.execute(query, params)
                await session.commit()
                
                return Result.success(model)
        except Exception as e:
            return Result.failure(f"Failed to create embedding model: {str(e)}")
    
    async def get(self, model_id: ModelId) -> Result[EmbeddingModel]:
        """Get an embedding model by ID."""
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, model_type, dimensions, api_key, 
                    normalize_vectors, metadata, created_at
                FROM ai_embedding_models 
                WHERE id = :id
                """
                
                result = await session.execute(query, {"id": model_id.value})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Embedding model with ID '{model_id.value}' not found")
                
                model = EmbeddingModel(
                    id=ModelId(row.id),
                    name=row.name,
                    model_type=EmbeddingModelType(row.model_type),
                    dimensions=row.dimensions,
                    api_key=row.api_key,
                    normalize_vectors=row.normalize_vectors,
                    metadata=row.metadata,
                    created_at=row.created_at
                )
                
                return Result.success(model)
        except Exception as e:
            return Result.failure(f"Failed to get embedding model: {str(e)}")
    
    async def get_by_name(self, name: str) -> Result[EmbeddingModel]:
        """Get an embedding model by name."""
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, model_type, dimensions, api_key, 
                    normalize_vectors, metadata, created_at
                FROM ai_embedding_models 
                WHERE name = :name
                """
                
                result = await session.execute(query, {"name": name})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Embedding model with name '{name}' not found")
                
                model = EmbeddingModel(
                    id=ModelId(row.id),
                    name=row.name,
                    model_type=EmbeddingModelType(row.model_type),
                    dimensions=row.dimensions,
                    api_key=row.api_key,
                    normalize_vectors=row.normalize_vectors,
                    metadata=row.metadata,
                    created_at=row.created_at
                )
                
                return Result.success(model)
        except Exception as e:
            return Result.failure(f"Failed to get embedding model by name: {str(e)}")
    
    async def update(self, model: EmbeddingModel) -> Result[EmbeddingModel]:
        """Update an embedding model."""
        try:
            async with self.session() as session:
                query = """
                UPDATE ai_embedding_models
                SET name = :name,
                    model_type = :model_type,
                    dimensions = :dimensions,
                    api_key = :api_key,
                    normalize_vectors = :normalize_vectors,
                    metadata = :metadata
                WHERE id = :id
                RETURNING id
                """
                
                params = {
                    "id": model.id.value,
                    "name": model.name,
                    "model_type": model.model_type.value,
                    "dimensions": model.dimensions,
                    "api_key": model.api_key,
                    "normalize_vectors": model.normalize_vectors,
                    "metadata": model.metadata
                }
                
                result = await session.execute(query, params)
                updated = await result.fetchone()
                
                if not updated:
                    return Result.failure(f"Embedding model with ID '{model.id.value}' not found")
                
                await session.commit()
                
                return Result.success(model)
        except Exception as e:
            return Result.failure(f"Failed to update embedding model: {str(e)}")
    
    async def delete(self, model_id: ModelId) -> Result[bool]:
        """Delete an embedding model."""
        try:
            async with self.session() as session:
                query = """
                DELETE FROM ai_embedding_models
                WHERE id = :id
                RETURNING id
                """
                
                result = await session.execute(query, {"id": model_id.value})
                deleted = await result.fetchone()
                
                if not deleted:
                    return Result.failure(f"Embedding model with ID '{model_id.value}' not found")
                
                await session.commit()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete embedding model: {str(e)}")
    
    async def list(self) -> Result[List[EmbeddingModel]]:
        """List all embedding models."""
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, model_type, dimensions, api_key, 
                    normalize_vectors, metadata, created_at
                FROM ai_embedding_models 
                ORDER BY name
                """
                
                result = await session.execute(query)
                rows = await result.fetchall()
                
                models = []
                for row in rows:
                    model = EmbeddingModel(
                        id=ModelId(row.id),
                        name=row.name,
                        model_type=EmbeddingModelType(row.model_type),
                        dimensions=row.dimensions,
                        api_key=row.api_key,
                        normalize_vectors=row.normalize_vectors,
                        metadata=row.metadata,
                        created_at=row.created_at
                    )
                    models.append(model)
                
                return Result.success(models)
        except Exception as e:
            return Result.failure(f"Failed to list embedding models: {str(e)}")


class EmbeddingRepository(AsyncDomainRepository, EmbeddingRepositoryProtocol):
    """Repository implementation for embeddings."""
    
    async def create(self, embedding: Embedding) -> Result[Embedding]:
        """Create a new embedding."""
        try:
            async with self.session() as session:
                # Insert new embedding
                query = """
                INSERT INTO ai_embeddings (
                    id, vector, model_id, source_id, source_type, 
                    dimensions, created_at, metadata
                ) VALUES (
                    :id, :vector, :model_id, :source_id, :source_type, 
                    :dimensions, :created_at, :metadata
                ) RETURNING id
                """
                
                params = {
                    "id": embedding.id.value,
                    "vector": embedding.vector,
                    "model_id": embedding.model_id.value,
                    "source_id": embedding.source_id,
                    "source_type": embedding.source_type,
                    "dimensions": embedding.dimensions,
                    "created_at": embedding.created_at,
                    "metadata": embedding.metadata
                }
                
                result = await session.execute(query, params)
                await session.commit()
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to create embedding: {str(e)}")
    
    async def get(self, embedding_id: EmbeddingId) -> Result[Embedding]:
        """Get an embedding by ID."""
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, vector, model_id, source_id, source_type, 
                    dimensions, created_at, metadata
                FROM ai_embeddings 
                WHERE id = :id
                """
                
                result = await session.execute(query, {"id": embedding_id.value})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Embedding with ID '{embedding_id.value}' not found")
                
                embedding = Embedding(
                    id=EmbeddingId(row.id),
                    vector=row.vector,
                    model_id=ModelId(row.model_id),
                    source_id=row.source_id,
                    source_type=row.source_type,
                    dimensions=row.dimensions,
                    created_at=row.created_at,
                    metadata=row.metadata
                )
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to get embedding: {str(e)}")
    
    async def get_by_source(self, source_id: str, source_type: str) -> Result[Embedding]:
        """Get an embedding by source."""
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, vector, model_id, source_id, source_type, 
                    dimensions, created_at, metadata
                FROM ai_embeddings 
                WHERE source_id = :source_id AND source_type = :source_type
                """
                
                result = await session.execute(query, {
                    "source_id": source_id,
                    "source_type": source_type
                })
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(
                        f"Embedding for source '{source_type}/{source_id}' not found"
                    )
                
                embedding = Embedding(
                    id=EmbeddingId(row.id),
                    vector=row.vector,
                    model_id=ModelId(row.model_id),
                    source_id=row.source_id,
                    source_type=row.source_type,
                    dimensions=row.dimensions,
                    created_at=row.created_at,
                    metadata=row.metadata
                )
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to get embedding by source: {str(e)}")
    
    async def update(self, embedding: Embedding) -> Result[Embedding]:
        """Update an embedding."""
        try:
            async with self.session() as session:
                query = """
                UPDATE ai_embeddings
                SET vector = :vector,
                    dimensions = :dimensions,
                    metadata = :metadata
                WHERE id = :id
                RETURNING id
                """
                
                params = {
                    "id": embedding.id.value,
                    "vector": embedding.vector,
                    "dimensions": embedding.dimensions,
                    "metadata": embedding.metadata
                }
                
                result = await session.execute(query, params)
                updated = await result.fetchone()
                
                if not updated:
                    return Result.failure(f"Embedding with ID '{embedding.id.value}' not found")
                
                await session.commit()
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to update embedding: {str(e)}")
    
    async def delete(self, embedding_id: EmbeddingId) -> Result[bool]:
        """Delete an embedding."""
        try:
            async with self.session() as session:
                query = """
                DELETE FROM ai_embeddings
                WHERE id = :id
                RETURNING id
                """
                
                result = await session.execute(query, {"id": embedding_id.value})
                deleted = await result.fetchone()
                
                if not deleted:
                    return Result.failure(f"Embedding with ID '{embedding_id.value}' not found")
                
                await session.commit()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete embedding: {str(e)}")
    
    async def batch_create(self, embeddings: List[Embedding]) -> Result[List[Embedding]]:
        """Batch create embeddings."""
        try:
            async with self.session() as session:
                # Bulk insert new embeddings
                query = """
                INSERT INTO ai_embeddings (
                    id, vector, model_id, source_id, source_type, 
                    dimensions, created_at, metadata
                ) VALUES (
                    :id, :vector, :model_id, :source_id, :source_type, 
                    :dimensions, :created_at, :metadata
                )
                """
                
                params = []
                for embedding in embeddings:
                    params.append({
                        "id": embedding.id.value,
                        "vector": embedding.vector,
                        "model_id": embedding.model_id.value,
                        "source_id": embedding.source_id,
                        "source_type": embedding.source_type,
                        "dimensions": embedding.dimensions,
                        "created_at": embedding.created_at,
                        "metadata": embedding.metadata
                    })
                
                await session.execute_many(query, params)
                await session.commit()
                
                return Result.success(embeddings)
        except Exception as e:
            return Result.failure(f"Failed to batch create embeddings: {str(e)}")


class SearchRepository(AsyncDomainRepository, SearchRepositoryProtocol):
    """Repository implementation for semantic search."""
    
    async def index_document(self, document: DocumentIndex) -> Result[DocumentIndex]:
        """Index a document for search."""
        try:
            async with self.session() as session:
                # Insert document into index
                query = """
                INSERT INTO ai_document_index (
                    id, content, entity_id, entity_type, embedding_id,
                    created_at, updated_at, metadata
                ) VALUES (
                    :id, :content, :entity_id, :entity_type, :embedding_id,
                    :created_at, :updated_at, :metadata
                ) RETURNING id
                """
                
                params = {
                    "id": document.id,
                    "content": document.content,
                    "entity_id": document.entity_id,
                    "entity_type": document.entity_type,
                    "embedding_id": document.embedding_id.value if document.embedding_id else None,
                    "created_at": document.created_at,
                    "updated_at": document.updated_at,
                    "metadata": document.metadata
                }
                
                result = await session.execute(query, params)
                await session.commit()
                
                return Result.success(document)
        except Exception as e:
            return Result.failure(f"Failed to index document: {str(e)}")
    
    async def batch_index(self, documents: List[DocumentIndex]) -> Result[List[DocumentIndex]]:
        """Batch index documents."""
        try:
            async with self.session() as session:
                # Bulk insert documents
                query = """
                INSERT INTO ai_document_index (
                    id, content, entity_id, entity_type, embedding_id,
                    created_at, updated_at, metadata
                ) VALUES (
                    :id, :content, :entity_id, :entity_type, :embedding_id,
                    :created_at, :updated_at, :metadata
                )
                """
                
                params = []
                for document in documents:
                    params.append({
                        "id": document.id,
                        "content": document.content,
                        "entity_id": document.entity_id,
                        "entity_type": document.entity_type,
                        "embedding_id": document.embedding_id.value if document.embedding_id else None,
                        "created_at": document.created_at,
                        "updated_at": document.updated_at,
                        "metadata": document.metadata
                    })
                
                await session.execute_many(query, params)
                await session.commit()
                
                return Result.success(documents)
        except Exception as e:
            return Result.failure(f"Failed to batch index documents: {str(e)}")
    
    async def search(
        self,
        query: SearchQuery,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """Perform a semantic search."""
        try:
            from uno.sql.emitters.vector import VectorSearchEmitter
            
            async with self.session() as session:
                # Log the search query
                log_query = """
                INSERT INTO ai_search_queries (
                    id, query_text, user_id, entity_type, created_at, metadata
                ) VALUES (
                    :id, :query_text, :user_id, :entity_type, :created_at, :metadata
                )
                """
                
                log_params = {
                    "id": query.id.value,
                    "query_text": query.query_text,
                    "user_id": query.user_id,
                    "entity_type": query.entity_type,
                    "created_at": query.created_at,
                    "metadata": query.metadata
                }
                
                await session.execute(log_query, log_params)
                
                # Get the query vector
                # In a real implementation, this would call an embedding service
                # For now, we assume vector is provided or can be derived
                
                # Execute vector search using SQL emitter
                emitter = VectorSearchEmitter(
                    table_name="ai_document_index",
                    column_name="vector"
                )
                
                # This is a placeholder - in reality we'd use the actual vector
                query_vector = [0.0] * 384  # Example dimension
                
                raw_results = await emitter.execute_search(
                    connection=session,
                    query_text=query.query_text,
                    # query_vector=query_vector,  # would use this if available
                    limit=limit,
                    threshold=similarity_threshold,
                    entity_type=query.entity_type
                )
                
                # Convert to SearchResult entities
                results = []
                for i, raw in enumerate(raw_results):
                    result = SearchResult(
                        id=str(uuid.uuid4()),
                        query_id=query.id,
                        entity_id=raw["entity_id"],
                        entity_type=raw.get("entity_type", "unknown"),
                        similarity=raw["similarity"],
                        rank=i + 1,
                        metadata={"raw_data": raw.get("metadata", {})}
                    )
                    results.append(result)
                
                # Log the results
                for result in results:
                    log_result_query = """
                    INSERT INTO ai_search_results (
                        id, query_id, entity_id, entity_type, similarity, rank, 
                        created_at, metadata
                    ) VALUES (
                        :id, :query_id, :entity_id, :entity_type, :similarity, :rank, 
                        :created_at, :metadata
                    )
                    """
                    
                    log_result_params = {
                        "id": result.id,
                        "query_id": result.query_id.value,
                        "entity_id": result.entity_id,
                        "entity_type": result.entity_type,
                        "similarity": result.similarity,
                        "rank": result.rank,
                        "created_at": result.created_at,
                        "metadata": result.metadata
                    }
                    
                    await session.execute(log_result_query, log_result_params)
                
                await session.commit()
                
                return Result.success(results)
        except Exception as e:
            return Result.failure(f"Failed to perform search: {str(e)}")
    
    async def search_by_vector(
        self,
        vector: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> Result[List[SearchResult]]:
        """Perform a search using a vector."""
        try:
            from uno.sql.emitters.vector import VectorSearchEmitter
            
            async with self.session() as session:
                # Create a query object
                query_id = SearchQueryId(str(uuid.uuid4()))
                
                # Execute vector search using SQL emitter
                emitter = VectorSearchEmitter(
                    table_name="ai_document_index",
                    column_name="vector"
                )
                
                raw_results = await emitter.execute_search(
                    connection=session,
                    query_vector=vector,
                    limit=limit,
                    threshold=similarity_threshold,
                    entity_type=entity_type
                )
                
                # Convert to SearchResult entities
                results = []
                for i, raw in enumerate(raw_results):
                    result = SearchResult(
                        id=str(uuid.uuid4()),
                        query_id=query_id,
                        entity_id=raw["entity_id"],
                        entity_type=raw.get("entity_type", "unknown"),
                        similarity=raw["similarity"],
                        rank=i + 1,
                        metadata={"raw_data": raw.get("metadata", {})}
                    )
                    results.append(result)
                
                return Result.success(results)
        except Exception as e:
            return Result.failure(f"Failed to perform vector search: {str(e)}")
    
    async def delete_document(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> Result[int]:
        """Delete document from the index."""
        try:
            async with self.session() as session:
                # Build query based on provided filters
                if entity_type:
                    query = """
                    DELETE FROM ai_document_index
                    WHERE entity_id = :entity_id AND entity_type = :entity_type
                    RETURNING id
                    """
                    params = {"entity_id": entity_id, "entity_type": entity_type}
                else:
                    query = """
                    DELETE FROM ai_document_index
                    WHERE entity_id = :entity_id
                    RETURNING id
                    """
                    params = {"entity_id": entity_id}
                
                result = await session.execute(query, params)
                deleted = await result.fetchall()
                
                count = len(deleted)
                
                await session.commit()
                
                return Result.success(count)
        except Exception as e:
            return Result.failure(f"Failed to delete document: {str(e)}")
    
    async def get_document(
        self,
        entity_id: str,
        entity_type: Optional[str] = None
    ) -> Result[DocumentIndex]:
        """Get an indexed document."""
        try:
            async with self.session() as session:
                # Build query based on provided filters
                if entity_type:
                    query = """
                    SELECT * FROM ai_document_index
                    WHERE entity_id = :entity_id AND entity_type = :entity_type
                    """
                    params = {"entity_id": entity_id, "entity_type": entity_type}
                else:
                    query = """
                    SELECT * FROM ai_document_index
                    WHERE entity_id = :entity_id
                    """
                    params = {"entity_id": entity_id}
                
                result = await session.execute(query, params)
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Document with entity_id '{entity_id}' not found")
                
                document = DocumentIndex(
                    id=row.id,
                    content=row.content,
                    entity_id=row.entity_id,
                    entity_type=row.entity_type,
                    embedding_id=EmbeddingId(row.embedding_id) if row.embedding_id else None,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    metadata=row.metadata
                )
                
                return Result.success(document)
        except Exception as e:
            return Result.failure(f"Failed to get document: {str(e)}")


# Additional repository implementations would follow a similar pattern
# For brevity, we'll implement them as needed