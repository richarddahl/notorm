"""
Domain repositories for the Vector Search module.

This module defines repository interfaces and implementations for the Vector Search module,
providing data access patterns for vector search entities.
"""

from abc import ABC
from datetime import datetime
from typing import Dict, List, Optional, Protocol, runtime_checkable, Any, AsyncIterator, TypeVar, Generic

from uno.core.result import Result
from uno.domain.repository import AsyncDomainRepository

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
    EmbeddingModel
)

T = TypeVar('T')


@runtime_checkable
class VectorIndexRepositoryProtocol(Protocol):
    """Protocol for vector index repository."""
    
    async def create(self, index: VectorIndex) -> Result[VectorIndex]:
        """
        Create a new vector index.
        
        Args:
            index: Index to create
            
        Returns:
            Result containing the created index or an error
        """
        ...
    
    async def get(self, index_id: IndexId) -> Result[VectorIndex]:
        """
        Get a vector index by ID.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing the index or an error if not found
        """
        ...
    
    async def get_by_name(self, name: str) -> Result[VectorIndex]:
        """
        Get a vector index by name.
        
        Args:
            name: Index name
            
        Returns:
            Result containing the index or an error if not found
        """
        ...
    
    async def update(self, index: VectorIndex) -> Result[VectorIndex]:
        """
        Update a vector index.
        
        Args:
            index: Updated index
            
        Returns:
            Result containing the updated index or an error
        """
        ...
    
    async def delete(self, index_id: IndexId) -> Result[bool]:
        """
        Delete a vector index.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        ...
    
    async def list(self) -> Result[List[VectorIndex]]:
        """
        List all vector indexes.
        
        Returns:
            Result containing a list of vector indexes or an error
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
    
    async def list_by_source_type(self, source_type: str, limit: int = 100, offset: int = 0) -> Result[List[Embedding]]:
        """
        List embeddings by source type.
        
        Args:
            source_type: Source type
            limit: Maximum number of embeddings to return
            offset: Offset to start from
            
        Returns:
            Result containing a list of embeddings or an error
        """
        ...
    
    async def bulk_create(self, embeddings: List[Embedding]) -> Result[List[Embedding]]:
        """
        Bulk create embeddings.
        
        Args:
            embeddings: List of embeddings to create
            
        Returns:
            Result containing the created embeddings or an error
        """
        ...


@runtime_checkable
class SearchRepositoryProtocol(Protocol):
    """Protocol for search repository."""
    
    async def search(self, query: SearchQuery) -> Result[List[SearchResult]]:
        """
        Perform a vector search.
        
        Args:
            query: Search query
            
        Returns:
            Result containing a list of search results or an error
        """
        ...
    
    async def hybrid_search(self, query: HybridSearchQuery) -> Result[List[SearchResult]]:
        """
        Perform a hybrid search combining graph and vector search.
        
        Args:
            query: Hybrid search query
            
        Returns:
            Result containing a list of search results or an error
        """
        ...
    
    async def generate_embedding(self, text: str) -> Result[List[float]]:
        """
        Generate an embedding vector for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Result containing the embedding vector or an error
        """
        ...
    
    async def save_query(self, query: SearchQuery) -> Result[SearchQuery]:
        """
        Save a search query.
        
        Args:
            query: Search query to save
            
        Returns:
            Result containing the saved query or an error
        """
        ...
    
    async def save_results(self, results: List[SearchResult]) -> Result[List[SearchResult]]:
        """
        Save search results.
        
        Args:
            results: Search results to save
            
        Returns:
            Result containing the saved results or an error
        """
        ...


# Repository Implementations
class VectorIndexRepository(AsyncDomainRepository, VectorIndexRepositoryProtocol):
    """Implementation of vector index repository."""
    
    async def create(self, index: VectorIndex) -> Result[VectorIndex]:
        """
        Create a new vector index.
        
        Args:
            index: Index to create
            
        Returns:
            Result containing the created index or an error
        """
        try:
            async with self.session() as session:
                # Check if index with same name already exists
                query = """
                SELECT id FROM vector_indices WHERE name = :name
                """
                result = await session.execute(query, {"name": index.name})
                existing = await result.fetchone()
                
                if existing:
                    return Result.failure(f"Vector index with name '{index.name}' already exists")
                
                # Insert new index
                query = """
                INSERT INTO vector_indices (
                    id, name, dimension, index_type, distance_metric, metadata
                ) VALUES (
                    :id, :name, :dimension, :index_type, :distance_metric, :metadata
                ) RETURNING id
                """
                
                params = {
                    "id": index.id.value,
                    "name": index.name,
                    "dimension": index.dimension,
                    "index_type": index.index_type.value,
                    "distance_metric": index.distance_metric.value,
                    "metadata": index.metadata
                }
                
                result = await session.execute(query, params)
                await session.commit()
                
                return Result.success(index)
        except Exception as e:
            return Result.failure(f"Failed to create vector index: {str(e)}")
    
    async def get(self, index_id: IndexId) -> Result[VectorIndex]:
        """
        Get a vector index by ID.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing the index or an error if not found
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, dimension, index_type, distance_metric, 
                    created_at, updated_at, metadata
                FROM vector_indices 
                WHERE id = :id
                """
                
                result = await session.execute(query, {"id": index_id.value})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Vector index with ID '{index_id.value}' not found")
                
                index = VectorIndex(
                    id=IndexId(row.id),
                    name=row.name,
                    dimension=row.dimension,
                    index_type=IndexType(row.index_type),
                    distance_metric=DistanceMetric(row.distance_metric),
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    metadata=row.metadata
                )
                
                return Result.success(index)
        except Exception as e:
            return Result.failure(f"Failed to get vector index: {str(e)}")
    
    async def get_by_name(self, name: str) -> Result[VectorIndex]:
        """
        Get a vector index by name.
        
        Args:
            name: Index name
            
        Returns:
            Result containing the index or an error if not found
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, dimension, index_type, distance_metric, 
                    created_at, updated_at, metadata
                FROM vector_indices 
                WHERE name = :name
                """
                
                result = await session.execute(query, {"name": name})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Vector index with name '{name}' not found")
                
                index = VectorIndex(
                    id=IndexId(row.id),
                    name=row.name,
                    dimension=row.dimension,
                    index_type=IndexType(row.index_type),
                    distance_metric=DistanceMetric(row.distance_metric),
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    metadata=row.metadata
                )
                
                return Result.success(index)
        except Exception as e:
            return Result.failure(f"Failed to get vector index by name: {str(e)}")
    
    async def update(self, index: VectorIndex) -> Result[VectorIndex]:
        """
        Update a vector index.
        
        Args:
            index: Updated index
            
        Returns:
            Result containing the updated index or an error
        """
        try:
            async with self.session() as session:
                query = """
                UPDATE vector_indices
                SET name = :name,
                    distance_metric = :distance_metric,
                    updated_at = :updated_at,
                    metadata = :metadata
                WHERE id = :id
                RETURNING id
                """
                
                params = {
                    "id": index.id.value,
                    "name": index.name,
                    "distance_metric": index.distance_metric.value,
                    "updated_at": index.updated_at,
                    "metadata": index.metadata
                }
                
                result = await session.execute(query, params)
                updated = await result.fetchone()
                
                if not updated:
                    return Result.failure(f"Vector index with ID '{index.id.value}' not found")
                
                await session.commit()
                
                return Result.success(index)
        except Exception as e:
            return Result.failure(f"Failed to update vector index: {str(e)}")
    
    async def delete(self, index_id: IndexId) -> Result[bool]:
        """
        Delete a vector index.
        
        Args:
            index_id: Index ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            async with self.session() as session:
                query = """
                DELETE FROM vector_indices
                WHERE id = :id
                RETURNING id
                """
                
                result = await session.execute(query, {"id": index_id.value})
                deleted = await result.fetchone()
                
                if not deleted:
                    return Result.failure(f"Vector index with ID '{index_id.value}' not found")
                
                await session.commit()
                
                return Result.success(True)
        except Exception as e:
            return Result.failure(f"Failed to delete vector index: {str(e)}")
    
    async def list(self) -> Result[List[VectorIndex]]:
        """
        List all vector indexes.
        
        Returns:
            Result containing a list of vector indexes or an error
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, name, dimension, index_type, distance_metric, 
                    created_at, updated_at, metadata
                FROM vector_indices 
                ORDER BY name
                """
                
                result = await session.execute(query)
                rows = await result.fetchall()
                
                indexes = []
                for row in rows:
                    index = VectorIndex(
                        id=IndexId(row.id),
                        name=row.name,
                        dimension=row.dimension,
                        index_type=IndexType(row.index_type),
                        distance_metric=DistanceMetric(row.distance_metric),
                        created_at=row.created_at,
                        updated_at=row.updated_at,
                        metadata=row.metadata
                    )
                    indexes.append(index)
                
                return Result.success(indexes)
        except Exception as e:
            return Result.failure(f"Failed to list vector indexes: {str(e)}")


class EmbeddingRepository(AsyncDomainRepository, EmbeddingRepositoryProtocol):
    """Implementation of embedding repository."""
    
    async def create(self, embedding: Embedding) -> Result[Embedding]:
        """
        Create a new embedding.
        
        Args:
            embedding: Embedding to create
            
        Returns:
            Result containing the created embedding or an error
        """
        try:
            async with self.session() as session:
                # Check if embedding for same source already exists
                query = """
                SELECT id FROM embeddings 
                WHERE source_id = :source_id AND source_type = :source_type
                """
                result = await session.execute(query, {
                    "source_id": embedding.source_id,
                    "source_type": embedding.source_type
                })
                existing = await result.fetchone()
                
                if existing:
                    return Result.failure(
                        f"Embedding for source '{embedding.source_type}/{embedding.source_id}' already exists"
                    )
                
                # Insert new embedding
                query = """
                INSERT INTO embeddings (
                    id, vector, source_id, source_type, model, dimension, metadata
                ) VALUES (
                    :id, :vector, :source_id, :source_type, :model, :dimension, :metadata
                ) RETURNING id
                """
                
                params = {
                    "id": embedding.id.value,
                    "vector": embedding.vector,
                    "source_id": embedding.source_id,
                    "source_type": embedding.source_type,
                    "model": embedding.model.value,
                    "dimension": embedding.dimension,
                    "metadata": embedding.metadata
                }
                
                result = await session.execute(query, params)
                await session.commit()
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to create embedding: {str(e)}")
    
    async def get(self, embedding_id: EmbeddingId) -> Result[Embedding]:
        """
        Get an embedding by ID.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, vector, source_id, source_type, model, 
                    dimension, created_at, metadata
                FROM embeddings 
                WHERE id = :id
                """
                
                result = await session.execute(query, {"id": embedding_id.value})
                row = await result.fetchone()
                
                if not row:
                    return Result.failure(f"Embedding with ID '{embedding_id.value}' not found")
                
                embedding = Embedding(
                    id=EmbeddingId(row.id),
                    vector=row.vector,
                    source_id=row.source_id,
                    source_type=row.source_type,
                    model=EmbeddingModel(row.model),
                    dimension=row.dimension,
                    created_at=row.created_at,
                    metadata=row.metadata
                )
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to get embedding: {str(e)}")
    
    async def get_by_source(self, source_id: str, source_type: str) -> Result[Embedding]:
        """
        Get an embedding by source.
        
        Args:
            source_id: Source ID
            source_type: Source type
            
        Returns:
            Result containing the embedding or an error if not found
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, vector, source_id, source_type, model, 
                    dimension, created_at, metadata
                FROM embeddings 
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
                    source_id=row.source_id,
                    source_type=row.source_type,
                    model=EmbeddingModel(row.model),
                    dimension=row.dimension,
                    created_at=row.created_at,
                    metadata=row.metadata
                )
                
                return Result.success(embedding)
        except Exception as e:
            return Result.failure(f"Failed to get embedding by source: {str(e)}")
    
    async def update(self, embedding: Embedding) -> Result[Embedding]:
        """
        Update an embedding.
        
        Args:
            embedding: Updated embedding
            
        Returns:
            Result containing the updated embedding or an error
        """
        try:
            async with self.session() as session:
                query = """
                UPDATE embeddings
                SET vector = :vector,
                    dimension = :dimension,
                    metadata = :metadata
                WHERE id = :id
                RETURNING id
                """
                
                params = {
                    "id": embedding.id.value,
                    "vector": embedding.vector,
                    "dimension": embedding.dimension,
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
        """
        Delete an embedding.
        
        Args:
            embedding_id: Embedding ID
            
        Returns:
            Result containing a boolean indicating success or an error
        """
        try:
            async with self.session() as session:
                query = """
                DELETE FROM embeddings
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
    
    async def list_by_source_type(self, source_type: str, limit: int = 100, offset: int = 0) -> Result[List[Embedding]]:
        """
        List embeddings by source type.
        
        Args:
            source_type: Source type
            limit: Maximum number of embeddings to return
            offset: Offset to start from
            
        Returns:
            Result containing a list of embeddings or an error
        """
        try:
            async with self.session() as session:
                query = """
                SELECT 
                    id, vector, source_id, source_type, model, 
                    dimension, created_at, metadata
                FROM embeddings 
                WHERE source_type = :source_type
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
                """
                
                result = await session.execute(query, {
                    "source_type": source_type,
                    "limit": limit,
                    "offset": offset
                })
                rows = await result.fetchall()
                
                embeddings = []
                for row in rows:
                    embedding = Embedding(
                        id=EmbeddingId(row.id),
                        vector=row.vector,
                        source_id=row.source_id,
                        source_type=row.source_type,
                        model=EmbeddingModel(row.model),
                        dimension=row.dimension,
                        created_at=row.created_at,
                        metadata=row.metadata
                    )
                    embeddings.append(embedding)
                
                return Result.success(embeddings)
        except Exception as e:
            return Result.failure(f"Failed to list embeddings by source type: {str(e)}")
    
    async def bulk_create(self, embeddings: List[Embedding]) -> Result[List[Embedding]]:
        """
        Bulk create embeddings.
        
        Args:
            embeddings: List of embeddings to create
            
        Returns:
            Result containing the created embeddings or an error
        """
        try:
            async with self.session() as session:
                # Bulk insert new embeddings
                query = """
                INSERT INTO embeddings (
                    id, vector, source_id, source_type, model, dimension, metadata
                ) VALUES (
                    :id, :vector, :source_id, :source_type, :model, :dimension, :metadata
                ) RETURNING id
                """
                
                params = []
                for embedding in embeddings:
                    params.append({
                        "id": embedding.id.value,
                        "vector": embedding.vector,
                        "source_id": embedding.source_id,
                        "source_type": embedding.source_type,
                        "model": embedding.model.value,
                        "dimension": embedding.dimension,
                        "metadata": embedding.metadata
                    })
                
                await session.execute_many(query, params)
                await session.commit()
                
                return Result.success(embeddings)
        except Exception as e:
            return Result.failure(f"Failed to bulk create embeddings: {str(e)}")


class SearchRepository(AsyncDomainRepository, SearchRepositoryProtocol):
    """Implementation of search repository."""
    
    async def search(self, query: SearchQuery) -> Result[List[SearchResult]]:
        """
        Perform a vector search.
        
        Args:
            query: Search query
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            from uno.sql.emitters.vector import VectorSearchEmitter
            
            # Save query for logging/analytics
            save_result = await self.save_query(query)
            if save_result.is_failure():
                return Result.failure(f"Failed to save search query: {save_result.error}")
            
            query_obj = save_result.value
            
            # If query doesn't have a vector but has text, generate the embedding
            if query.query_vector is None and query.query_text is not None:
                embedding_result = await self.generate_embedding(query.query_text)
                if embedding_result.is_failure():
                    return Result.failure(f"Failed to generate embedding: {embedding_result.error}")
                
                query.query_vector = embedding_result.value
            
            # Use VectorSearchEmitter to execute search
            async with self.session() as session:
                emitter = VectorSearchEmitter(
                    table_name="embeddings",
                    column_name="vector"
                )
                
                search_params = {
                    "vector": query.query_vector,
                    "limit": query.limit,
                    "threshold": query.threshold,
                    "metric": query.metric
                }
                
                # Add filters if provided
                if query.filters:
                    search_params["filters"] = query.filters
                
                # Execute search
                raw_results = await emitter.execute_search(session, **search_params)
                
                # Convert to SearchResult objects
                results = []
                for i, raw in enumerate(raw_results):
                    result = SearchResult(
                        id=str(uuid.uuid4()),
                        similarity=raw["similarity"],
                        entity_id=raw["id"],
                        entity_type=raw.get("entity_type", "unknown"),
                        query_id=query.id.value,
                        rank=i + 1,
                        metadata={"raw_data": raw.get("row_data", {})}
                    )
                    results.append(result)
                
                # Save results for logging/analytics
                await self.save_results(results)
                
                return Result.success(results)
                
        except Exception as e:
            return Result.failure(f"Failed to perform vector search: {str(e)}")
    
    async def hybrid_search(self, query: HybridSearchQuery) -> Result[List[SearchResult]]:
        """
        Perform a hybrid search combining graph and vector search.
        
        Args:
            query: Hybrid search query
            
        Returns:
            Result containing a list of search results or an error
        """
        try:
            from uno.sql.emitters.vector import VectorSearchEmitter
            import json
            
            # Save query for logging/analytics
            save_result = await self.save_query(query)
            if save_result.is_failure():
                return Result.failure(f"Failed to save hybrid search query: {save_result.error}")
            
            query_obj = save_result.value
            
            # If query doesn't have a vector but has text, generate the embedding
            if query.query_vector is None and query.query_text is not None:
                embedding_result = await self.generate_embedding(query.query_text)
                if embedding_result.is_failure():
                    return Result.failure(f"Failed to generate embedding: {embedding_result.error}")
                
                query.query_vector = embedding_result.value
            
            # Construct graph traversal query
            filters_json = json.dumps(query.start_filters)
            graph_query = f"""
            SELECT 
                id::TEXT,
                distance
            FROM
                graph_traverse(
                    '{query.start_node_type}',
                    '{filters_json}',
                    '{query.path_pattern}'
                )
            """
            
            # Use VectorSearchEmitter to execute hybrid search
            async with self.session() as session:
                emitter = VectorSearchEmitter(
                    table_name="embeddings",
                    column_name="vector"
                )
                
                hybrid_params = {
                    "vector": query.query_vector,
                    "graph_query": graph_query,
                    "limit": query.limit,
                    "threshold": query.threshold,
                    "metric": query.metric,
                    "combine_method": query.combine_method,
                    "graph_weight": query.graph_weight,
                    "vector_weight": query.vector_weight
                }
                
                # Execute hybrid search
                raw_results = await emitter.execute_hybrid_search(session, **hybrid_params)
                
                # Convert to SearchResult objects
                results = []
                for i, raw in enumerate(raw_results):
                    result = SearchResult(
                        id=str(uuid.uuid4()),
                        similarity=raw["similarity"],
                        entity_id=raw["id"],
                        entity_type=raw.get("entity_type", "unknown"),
                        query_id=query.id.value,
                        rank=i + 1,
                        metadata={
                            "raw_data": raw.get("row_data", {}),
                            "graph_distance": raw.get("graph_distance", 999999)
                        }
                    )
                    results.append(result)
                
                # Save results for logging/analytics
                await self.save_results(results)
                
                return Result.success(results)
                
        except Exception as e:
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
            from uno.sql.emitters.vector import VectorSearchEmitter
            
            # Use VectorSearchEmitter to generate embedding
            async with self.session() as session:
                emitter = VectorSearchEmitter(
                    table_name="embeddings",
                    column_name="vector"
                )
                
                vector = await emitter.execute_generate_embedding(session, text)
                
                return Result.success(vector)
                
        except Exception as e:
            return Result.failure(f"Failed to generate embedding: {str(e)}")
    
    async def save_query(self, query: SearchQuery) -> Result[SearchQuery]:
        """
        Save a search query.
        
        Args:
            query: Search query to save
            
        Returns:
            Result containing the saved query or an error
        """
        try:
            async with self.session() as session:
                # Generate ID if not provided
                if not query.id:
                    query.id = SearchQueryId(str(uuid.uuid4()))
                
                # Insert query
                query_type = type(query).__name__
                
                save_query = """
                INSERT INTO search_queries (
                    id, query_text, query_vector, filters, limit_val, 
                    threshold, metric, index_id, query_type, metadata
                ) VALUES (
                    :id, :query_text, :query_vector, :filters, :limit_val,
                    :threshold, :metric, :index_id, :query_type, :metadata
                ) RETURNING id
                """
                
                params = {
                    "id": query.id.value,
                    "query_text": query.query_text,
                    "query_vector": query.query_vector,
                    "filters": query.filters,
                    "limit_val": query.limit,
                    "threshold": query.threshold,
                    "metric": query.metric,
                    "index_id": query.index_id.value if query.index_id else None,
                    "query_type": query_type,
                    "metadata": query.metadata
                }
                
                # Add hybrid search specific fields if applicable
                if isinstance(query, HybridSearchQuery):
                    params["metadata"] = {
                        **(params["metadata"] or {}),
                        "start_node_type": query.start_node_type,
                        "start_filters": query.start_filters,
                        "path_pattern": query.path_pattern,
                        "combine_method": query.combine_method,
                        "graph_weight": query.graph_weight,
                        "vector_weight": query.vector_weight
                    }
                
                result = await session.execute(save_query, params)
                await session.commit()
                
                return Result.success(query)
        except Exception as e:
            return Result.failure(f"Failed to save search query: {str(e)}")
    
    async def save_results(self, results: List[SearchResult]) -> Result[List[SearchResult]]:
        """
        Save search results.
        
        Args:
            results: Search results to save
            
        Returns:
            Result containing the saved results or an error
        """
        try:
            if not results:
                return Result.success([])
                
            async with self.session() as session:
                # Bulk insert results
                save_query = """
                INSERT INTO search_results (
                    id, similarity, entity_id, entity_type, query_id, rank, metadata
                ) VALUES (
                    :id, :similarity, :entity_id, :entity_type, :query_id, :rank, :metadata
                ) RETURNING id
                """
                
                params = []
                for result in results:
                    params.append({
                        "id": result.id,
                        "similarity": result.similarity,
                        "entity_id": result.entity_id,
                        "entity_type": result.entity_type,
                        "query_id": result.query_id,
                        "rank": result.rank,
                        "metadata": result.metadata
                    })
                
                await session.execute_many(save_query, params)
                await session.commit()
                
                return Result.success(results)
        except Exception as e:
            return Result.failure(f"Failed to save search results: {str(e)}")