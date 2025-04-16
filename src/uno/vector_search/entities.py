"""
Domain entities for the Vector Search module.

This module defines the core domain entities for the Vector Search module,
including vector embeddings, queries, search results, and related value objects.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, TypeVar, Generic

from uno.domain.core import Entity, ValueObject


# Value Objects
@dataclass(frozen=True)
class VectorId(ValueObject):
    """Identifier for a vector entity."""
    value: str


@dataclass(frozen=True)
class IndexId(ValueObject):
    """Identifier for a vector index."""
    value: str


@dataclass(frozen=True)
class EmbeddingId(ValueObject):
    """Identifier for an embedding."""
    value: str


@dataclass(frozen=True)
class SearchQueryId(ValueObject):
    """Identifier for a search query."""
    value: str


# Enums
class IndexType(str, Enum):
    """Type of vector index."""
    HNSW = "hnsw"
    IVFFLAT = "ivfflat"
    NONE = "none"


class DistanceMetric(str, Enum):
    """Distance metric for vector similarity."""
    COSINE = "cosine"
    L2 = "l2"
    DOT = "dot"


class EmbeddingModel(str, Enum):
    """Embedding model types."""
    DEFAULT = "default"
    OPENAI = "openai"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


# Entities
@dataclass
class VectorIndex(Entity):
    """A vector search index."""
    
    id: IndexId
    name: str
    dimension: int
    index_type: IndexType
    distance_metric: DistanceMetric
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update(self, 
               name: Optional[str] = None, 
               distance_metric: Optional[DistanceMetric] = None,
               metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update vector index properties.
        
        Args:
            name: New name for the index
            distance_metric: New distance metric
            metadata: Additional metadata to merge
        """
        if name:
            self.name = name
        if distance_metric:
            self.distance_metric = distance_metric
        if metadata:
            self.metadata.update(metadata)
        self.updated_at = datetime.now(UTC)


@dataclass
class Embedding(Entity):
    """An embedding vector."""
    
    id: EmbeddingId
    vector: List[float]
    source_id: str
    source_type: str
    model: EmbeddingModel
    dimension: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_vector(self, new_vector: List[float]) -> None:
        """
        Update the embedding vector.
        
        Args:
            new_vector: New embedding vector
        """
        self.vector = new_vector
        self.dimension = len(new_vector)


@dataclass
class SearchQuery(Entity):
    """A vector search query."""
    
    id: SearchQueryId
    query_text: Optional[str] = None
    query_vector: Optional[List[float]] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    limit: int = 10
    threshold: float = 0.7
    metric: str = "cosine"
    index_id: Optional[IndexId] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResult(Entity):
    """A vector search result."""
    
    id: str
    similarity: float
    entity_id: str
    entity_type: str
    query_id: str
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HybridSearchQuery(SearchQuery):
    """A hybrid search query combining graph and vector search."""
    
    start_node_type: str
    start_filters: Dict[str, Any] = field(default_factory=dict)
    path_pattern: str = ""
    combine_method: str = "intersect"
    graph_weight: float = 0.5
    vector_weight: float = 0.5


T = TypeVar('T')


@dataclass
class TypedSearchResult(Generic[T]):
    """A search result with a typed entity."""
    
    id: str
    similarity: float
    entity: T
    rank: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGContext:
    """Retrieval-augmented generation context."""
    
    query: str
    system_prompt: str
    results: List[SearchResult]
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    formatted_context: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def format_context(self, context_formatter: callable) -> str:
        """
        Format the retrieval results into a context string.
        
        Args:
            context_formatter: Function to format results into context
            
        Returns:
            Formatted context string
        """
        self.formatted_context = context_formatter(self.results)
        return self.formatted_context
    
    def create_prompt(self) -> Dict[str, str]:
        """
        Create a prompt for LLM with retrieved context.
        
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        if not self.formatted_context:
            raise ValueError("Context has not been formatted yet")
        
        user_prompt = f"""I need information based on the following context:

{self.formatted_context}

My question is: {self.query}"""

        return {
            "system_prompt": self.system_prompt,
            "user_prompt": user_prompt
        }