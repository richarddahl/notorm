"""
Vector search functionality for the UNO framework.

This module provides vector search capabilities using PostgreSQL's pgvector
extension, including similarity search, hybrid search combining graph and vector search,
and classes for managing embeddings.
"""

import logging
import json
from typing import Dict, List, Any, Optional, TypeVar, Type, Generic, Union, Tuple

from pydantic import BaseModel

from uno.database.session import async_session
from uno.settings import uno_settings
from uno.domain.core import Entity
from uno.domain.repository import Repository
from uno.sql.emitters.vector import VectorSearchEmitter

T = TypeVar('T', bound=Entity)


class VectorSearchResult(BaseModel):
    """
    Result from a vector search operation.
    
    Attributes:
        id: Entity ID
        similarity: Similarity score (0-1 where 1 is most similar)
        entity: Optional full entity object if loaded
        metadata: Additional metadata about the search result
    """
    
    id: str
    similarity: float
    entity: Optional[Any] = None
    metadata: Dict[str, Any] = {}


class VectorQuery(BaseModel):
    """
    Vector search query specification.
    
    Attributes:
        query_text: The text to search for
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0-1)
        metric: Distance metric to use (cosine, l2, dot)
    """
    
    query_text: str
    limit: int = 10
    threshold: float = 0.7
    metric: str = "cosine"  # Options: "cosine", "l2", "dot"


class HybridQuery(VectorQuery):
    """
    Hybrid search query combining graph traversal and vector search.
    
    Attributes:
        start_node_type: Type of node to start graph traversal from
        start_filters: Filters to apply to the start node
        path_pattern: Cypher path pattern for traversal
        combine_method: How to combine graph and vector results
        graph_weight: Weight to give graph results (0-1)
        vector_weight: Weight to give vector results (0-1)
    """
    
    start_node_type: str
    start_filters: Dict[str, Any] = {}
    path_pattern: str
    combine_method: str = "intersect"  # Options: "intersect", "union", "weighted"
    graph_weight: float = 0.5
    vector_weight: float = 0.5


class VectorSearchService(Generic[T]):
    """
    Service for performing vector search operations.
    
    This service provides methods for performing vector similarity search,
    integrating with the repository pattern to load full entities.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        table_name: str,
        repository: Optional[Repository[T]] = None,
        schema: Optional[str] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize vector search service.
        
        Args:
            entity_type: The entity type this service searches for
            table_name: The database table name containing embeddings
            repository: Optional repository for loading full entities
            schema: Optional database schema name (defaults to settings.DB_SCHEMA)
            logger: Optional logger for diagnostics
        """
        from uno.settings import uno_settings
        
        self.entity_type = entity_type
        self.table_name = table_name
        self.repository = repository
        self.schema = schema or uno_settings.DB_SCHEMA
        self.logger = logger or logging.getLogger(__name__)
        
        # Create a VectorSearchEmitter for this service
        self.emitter = VectorSearchEmitter(
            table_name=self.table_name,
            column_name="embedding",  # Default column name
            schema=self.schema
        )
    
    async def search(self, query: VectorQuery) -> List[VectorSearchResult]:
        """
        Perform a vector similarity search.
        
        Args:
            query: The vector search query
            
        Returns:
            List of search results
        """
        try:
            async with async_session() as session:
                # Use the emitter to execute the search
                results = await self.emitter.execute_search(
                    connection=session,
                    query_text=query.query_text,
                    limit=query.limit,
                    threshold=query.threshold,
                    metric=query.metric
                )
                
                # Create result objects
                search_results = []
                
                for result in results:
                    # Create VectorSearchResult instance
                    search_result = VectorSearchResult(
                        id=result["id"],
                        similarity=result["similarity"],
                        metadata={"row_data": result.get("row_data", {})}
                    )
                    search_results.append(search_result)
                
                # Load entities if repository is available
                if self.repository and search_results:
                    for result_obj in search_results:
                        entity = await self.repository.get(result_obj.id)
                        if entity:
                            result_obj.entity = entity
                
                return search_results
                
        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            raise
    
    async def hybrid_search(self, query: HybridQuery) -> List[VectorSearchResult]:
        """
        Perform a hybrid search combining graph traversal and vector search.
        
        Args:
            query: The hybrid search query
            
        Returns:
            List of search results
        """
        try:
            # Convert start_filters to JSON for use in the graph query
            filters_json = json.dumps(query.start_filters)
            
            # Construct the graph traversal query
            graph_query = f"""
            SELECT 
                id::TEXT,
                distance
            FROM
                {self.schema}.graph_traverse(
                    '{query.start_node_type}',
                    '{filters_json}',
                    '{query.path_pattern}'
                )
            """
            
            async with async_session() as session:
                # Use the emitter to execute the hybrid search
                results = await self.emitter.execute_hybrid_search(
                    connection=session,
                    query_text=query.query_text,
                    graph_query=graph_query,
                    limit=query.limit,
                    threshold=query.threshold
                )
                
                # Create result objects
                search_results = []
                
                for result in results:
                    # Create VectorSearchResult instance with graph distance metadata
                    search_result = VectorSearchResult(
                        id=result["id"],
                        similarity=result["similarity"],
                        metadata={
                            "row_data": result.get("row_data", {}),
                            "graph_distance": result.get("graph_distance", 999999)
                        }
                    )
                    search_results.append(search_result)
                
                # Load entities if repository is available
                if self.repository and search_results:
                    for result_obj in search_results:
                        entity = await self.repository.get(result_obj.id)
                        if entity:
                            result_obj.entity = entity
                
                return search_results
                
        except Exception as e:
            self.logger.error(f"Hybrid search error: {e}")
            raise
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for text using the database function.
        
        This is useful for getting consistent embeddings for external use.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        try:
            async with async_session() as session:
                # Use the emitter to execute the embedding generation
                return await self.emitter.execute_generate_embedding(
                    connection=session,
                    text=text
                )
                
        except Exception as e:
            self.logger.error(f"Embedding generation error: {e}")
            raise


class RAGService(Generic[T]):
    """
    Retrieval-Augmented Generation (RAG) service.
    
    This service provides RAG capabilities by combining vector search with
    prompt construction for LLM interactions. It uses PostgreSQL for efficient
    vector storage and retrieval.
    """
    
    def __init__(
        self,
        vector_search: VectorSearchService[T],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize RAG service.
        
        Args:
            vector_search: Vector search service to use for retrieval
            logger: Optional logger for diagnostics
        """
        self.vector_search = vector_search
        self.logger = logger or logging.getLogger(__name__)
    
    async def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> Tuple[List[T], List[VectorSearchResult]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query text
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (entities, search_results)
        """
        # Use vector search to find relevant context
        search_query = VectorQuery(
            query_text=query,
            limit=limit,
            threshold=threshold
        )
        
        search_results = await self.vector_search.search(search_query)
        
        # Extract entities from results
        entities = [result.entity for result in search_results if result.entity is not None]
        
        return entities, search_results
    
    def format_context_for_prompt(self, entities: List[T]) -> str:
        """
        Format retrieved entities as context for an LLM prompt.
        
        Args:
            entities: The retrieved entities
            
        Returns:
            Formatted context string
        """
        # Default implementation - override this in subclasses
        # to format the context according to your entity structure
        
        context_parts = []
        
        for i, entity in enumerate(entities):
            # Convert entity to a string representation
            entity_dict = entity.model_dump()
            
            # Format as a numbered context item
            context_text = f"[{i+1}] "
            
            # Add ID
            if hasattr(entity, "id"):
                context_text += f"ID: {entity.id}\n"
            
            # Add fields that might be useful as context
            for field, value in entity_dict.items():
                if field == "id":
                    continue
                    
                if isinstance(value, str) and len(value) > 0:
                    # Limit very long text fields
                    if len(value) > 500:
                        value = value[:500] + "..."
                    context_text += f"{field}: {value}\n"
            
            context_parts.append(context_text)
        
        # Join all context items with separators
        return "\n---\n".join(context_parts)
    
    async def create_rag_prompt(
        self,
        query: str,
        system_prompt: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> Dict[str, str]:
        """
        Create a RAG prompt with retrieved context.
        
        Args:
            query: The user's query
            system_prompt: The system prompt 
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Dictionary with system_prompt and user_prompt keys
        """
        # Retrieve relevant context
        entities, _ = await self.retrieve_context(query, limit, threshold)
        
        # Format context
        context = self.format_context_for_prompt(entities)
        
        # Create user prompt with context and query
        user_prompt = f"""I need information based on the following context:

{context}

My question is: {query}"""
        
        return {
            "system_prompt": system_prompt,
            "user_prompt": user_prompt
        }