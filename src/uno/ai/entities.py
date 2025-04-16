"""
Domain entities for the AI module.

This module defines the core domain entities for the AI module,
including embeddings, semantic search, recommendations, content generation, and anomaly detection.
"""

from datetime import datetime, UTC
import uuid
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Union, TypeVar, Generic

from uno.domain.core import Entity, AggregateRoot, ValueObject


# Value Objects
@dataclass(frozen=True)
class EmbeddingId(ValueObject):
    """Identifier for an embedding."""
    value: str


@dataclass(frozen=True)
class SearchQueryId(ValueObject):
    """Identifier for a search query."""
    value: str


@dataclass(frozen=True)
class RecommendationId(ValueObject):
    """Identifier for a recommendation."""
    value: str


@dataclass(frozen=True)
class ContentRequestId(ValueObject):
    """Identifier for a content generation request."""
    value: str


@dataclass(frozen=True)
class AnomalyDetectionId(ValueObject):
    """Identifier for an anomaly detection."""
    value: str


@dataclass(frozen=True)
class ModelId(ValueObject):
    """Identifier for an AI model."""
    value: str


# Enums
class EmbeddingModelType(str, Enum):
    """Type of embedding model."""
    SENTENCE_TRANSFORMER = "sentence_transformer"
    HUGGINGFACE = "huggingface"
    OPENAI = "openai"
    CUSTOM = "custom"


class ContentGenerationType(str, Enum):
    """Type of content generation."""
    COMPLETION = "completion"
    CHAT = "chat"
    SUMMARIZATION = "summarization"
    TRANSLATION = "translation"
    PARAPHRASING = "paraphrasing"
    CUSTOM = "custom"


class AnomalyDetectionMethod(str, Enum):
    """Method for anomaly detection."""
    STATISTICAL = "statistical"
    ISOLATION_FOREST = "isolation_forest"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    AUTOENCODER = "autoencoder"
    ONE_CLASS_SVM = "one_class_svm"
    HYBRID = "hybrid"


class RecommendationMethod(str, Enum):
    """Method for recommendations."""
    CONTENT_BASED = "content_based"
    COLLABORATIVE_FILTERING = "collaborative_filtering"
    HYBRID = "hybrid"
    KNOWLEDGE_GRAPH = "knowledge_graph"
    NEURAL = "neural"


class SimilarityMetric(str, Enum):
    """Similarity metric for vector comparisons."""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"
    MANHATTAN = "manhattan"


# Entities
@dataclass
class EmbeddingModel(Entity):
    """An embedding model configuration."""
    
    id: ModelId
    name: str
    model_type: EmbeddingModelType
    dimensions: int
    api_key: Optional[str] = None
    normalize_vectors: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class Embedding(Entity):
    """A vector embedding."""
    
    id: EmbeddingId
    vector: List[float]
    model_id: ModelId
    source_id: str
    source_type: str
    dimensions: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchQuery(Entity):
    """A semantic search query."""
    
    id: SearchQueryId
    query_text: str
    user_id: Optional[str] = None
    entity_type: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_query_vector(self, embedding_service) -> List[float]:
        """
        Generate embedding vector for this query.
        
        Args:
            embedding_service: Service to generate embeddings
            
        Returns:
            Embedding vector
        """
        # This is a placeholder for the actual implementation
        # which would call the embedding service
        return []


@dataclass
class SearchResult(Entity):
    """A result from a semantic search."""
    
    id: str
    query_id: SearchQueryId
    entity_id: str
    entity_type: str
    similarity: float
    rank: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DocumentIndex(Entity):
    """A document indexed for search."""
    
    id: str
    content: str
    entity_id: str
    entity_type: str
    embedding_id: Optional[EmbeddingId] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationProfile(Entity):
    """A profile for generating recommendations."""
    
    id: str
    user_id: str
    preferences: Dict[str, Any] = field(default_factory=dict)
    embedding_id: Optional[EmbeddingId] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecommendationRequest(Entity):
    """A request for recommendations."""
    
    id: RecommendationId
    user_id: str
    context: Optional[str] = None
    category: Optional[str] = None
    limit: int = 10
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    method: RecommendationMethod = RecommendationMethod.HYBRID
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Recommendation(Entity):
    """A recommendation item."""
    
    id: str
    request_id: RecommendationId
    item_id: str
    item_type: str
    score: float
    rank: int
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ContentRequest(Entity):
    """A content generation request."""
    
    id: ContentRequestId
    prompt: str
    user_id: Optional[str] = None
    content_type: ContentGenerationType = ContentGenerationType.COMPLETION
    max_tokens: int = 500
    temperature: float = 0.7
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GeneratedContent(Entity):
    """Generated content from an AI model."""
    
    id: str
    request_id: ContentRequestId
    content: str
    model_id: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    completion_tokens: int = 0
    prompt_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionConfig(Entity):
    """Configuration for anomaly detection."""
    
    id: str
    name: str
    method: AnomalyDetectionMethod
    sensitivity: float = 0.95
    lookback_period: Optional[int] = None
    training_window: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionRequest(Entity):
    """A request for anomaly detection."""
    
    id: AnomalyDetectionId
    data_points: List[Dict[str, Any]]
    config_id: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnomalyDetectionResult(Entity):
    """Result from anomaly detection."""
    
    id: str
    request_id: AnomalyDetectionId
    anomalies: List[Dict[str, Any]]
    score: float
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AIContext(Entity):
    """Context information for AI operations."""
    
    id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    context_type: str
    context_source: str
    value: Any
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RAGQuery(Entity):
    """A Retrieval Augmented Generation query."""
    
    id: str
    query_text: str
    system_prompt: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def create_prompt(self, context_items: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Create a prompt for LLM with retrieved context.
        
        Args:
            context_items: List of context items
            
        Returns:
            Dictionary with system_prompt and user_prompt
        """
        # Format context for inclusion in prompt
        context_section = "\n\nContextual Information:\n"
        
        for idx, item in enumerate(context_items):
            context_section += f"\n[Context {idx+1}]\n"
            
            # Add metadata if available
            for key, value in item.items():
                if key != "content" and not key.startswith("_"):
                    context_section += f"{key}: {value}\n"
            
            # Add content
            if "content" in item:
                content = item["content"]
                # Limit very long content
                if isinstance(content, str) and len(content) > 1000:
                    content = content[:1000] + "..."
                context_section += f"Content: {content}\n"
                
            context_section += "\n"
        
        # Combine with query
        user_prompt = f"""I need information based on the following context:

{context_section}

My question is: {self.query_text}"""

        return {
            "system_prompt": self.system_prompt,
            "user_prompt": user_prompt
        }