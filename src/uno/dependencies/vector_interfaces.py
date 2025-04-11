"""
Protocol definitions for vector search components.

This module defines Protocol classes for vector search services,
ensuring consistent interfaces for dependency injection and testing.
"""

from typing import Protocol, List, Dict, Any, Optional, Type, Generic, Tuple, Union
from datetime import datetime

from uno.dependencies.interfaces import EntityT, QueryT, ResultT, VectorT


class VectorQueryProtocol(Protocol, Generic[QueryT]):
    """Protocol for vector search queries."""
    
    query_text: str
    limit: int
    threshold: float
    metric: str
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        ...


class VectorResultProtocol(Protocol, Generic[EntityT]):
    """Protocol for vector search results."""
    
    id: str
    similarity: float
    entity: Optional[EntityT]
    metadata: Dict[str, Any]


class VectorSearchServiceProtocol(Protocol, Generic[EntityT, QueryT, ResultT]):
    """Protocol for vector search services."""
    
    async def search(self, query: QueryT) -> List[ResultT]:
        """
        Perform a vector similarity search.
        
        Args:
            query: The vector search query
            
        Returns:
            List of search results
        """
        ...
    
    async def hybrid_search(self, query: QueryT) -> List[ResultT]:
        """
        Perform a hybrid search combining graph traversal and vector search.
        
        Args:
            query: The hybrid search query
            
        Returns:
            List of search results
        """
        ...
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for text.
        
        Args:
            text: The text to embed
            
        Returns:
            Embedding vector as a list of floats
        """
        ...


class RAGServiceProtocol(Protocol, Generic[EntityT, ResultT]):
    """Protocol for RAG (Retrieval-Augmented Generation) services."""
    
    async def retrieve_context(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.7
    ) -> Tuple[List[EntityT], List[ResultT]]:
        """
        Retrieve relevant context for a query.
        
        Args:
            query: The query text
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold
            
        Returns:
            Tuple of (entities, search_results)
        """
        ...
    
    def format_context_for_prompt(self, entities: List[EntityT]) -> str:
        """
        Format retrieved entities as context for an LLM prompt.
        
        Args:
            entities: The retrieved entities
            
        Returns:
            Formatted context string
        """
        ...
    
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
        ...


class VectorUpdateServiceProtocol(Protocol):
    """Protocol for vector update services."""
    
    async def start(self) -> None:
        """Start the update service."""
        ...
    
    async def stop(self) -> None:
        """Stop the update service."""
        ...
    
    async def queue_update(
        self,
        entity_id: str,
        entity_type: str,
        content: str,
        priority: int = 0
    ) -> None:
        """
        Queue an embedding update.
        
        Args:
            entity_id: ID of the entity to update
            entity_type: Type of the entity
            content: Text content to embed
            priority: Priority level (higher values = higher priority)
        """
        ...
    
    async def process_event(self, event: Any) -> None:
        """
        Process vector-related events.
        
        Args:
            event: The domain event to process
        """
        ...
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get service statistics.
        
        Returns:
            Dictionary with service statistics
        """
        ...


class BatchVectorUpdateServiceProtocol(Protocol):
    """Protocol for batch vector update services."""
    
    async def update_all_entities(
        self,
        entity_type: str,
        content_fields: List[str]
    ) -> Dict[str, int]:
        """
        Update embeddings for all entities of a given type.
        
        Args:
            entity_type: The type of entity to update
            content_fields: Fields containing content to vectorize
            
        Returns:
            Dictionary with operation statistics
        """
        ...
    
    async def update_entities_by_ids(
        self,
        entity_type: str,
        entity_ids: List[str],
        content_fields: List[str]
    ) -> Dict[str, int]:
        """
        Update embeddings for specific entities by ID.
        
        Args:
            entity_type: The type of entity to update
            entity_ids: List of entity IDs to update
            content_fields: Fields containing content to vectorize
            
        Returns:
            Dictionary with operation statistics
        """
        ...


class VectorConfigServiceProtocol(Protocol):
    """Protocol for vector configuration services."""
    
    def get_dimensions(self, entity_type: Optional[str] = None) -> int:
        """
        Get the embedding dimensions for an entity type.
        
        Args:
            entity_type: Optional entity type to get dimensions for
            
        Returns:
            Number of dimensions for embeddings
        """
        ...
    
    def get_index_type(self, entity_type: Optional[str] = None) -> str:
        """
        Get the index type for an entity type.
        
        Args:
            entity_type: Optional entity type to get index type for
            
        Returns:
            Index type ("hnsw", "ivfflat", or "none")
        """
        ...
    
    def get_vectorizable_fields(self, entity_type: str) -> List[str]:
        """
        Get fields that should be vectorized for an entity type.
        
        Args:
            entity_type: The entity type to get fields for
            
        Returns:
            List of field names to vectorize
        """
        ...
    
    def is_vectorizable(self, entity_type: str) -> bool:
        """
        Check if an entity type is vectorizable.
        
        Args:
            entity_type: The entity type to check
            
        Returns:
            True if the entity type is vectorizable
        """
        ...
    
    def register_vectorizable_entity(
        self,
        entity_type: str,
        fields: List[str],
        dimensions: int = 1536,
        index_type: str = "hnsw"
    ) -> None:
        """
        Register an entity type as vectorizable.
        
        Args:
            entity_type: The entity type to register
            fields: Fields to vectorize
            dimensions: Embedding dimensions
            index_type: Index type
        """
        ...