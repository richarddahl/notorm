"""
Domain-specific adaptation module for AI features.

This module provides tools and utilities for adapting the general AI features
to specific domains and industries with custom models, training pipelines,
and domain knowledge integration.
"""

from uno.ai.domain_adaptation.embedding_adapter import (
    DomainEmbeddingAdapter,
    EmbeddingAdapterConfig,
    EmbeddingTrainingConfig,
    FineTuningMethod
)
from uno.ai.domain_adaptation.knowledge_integration import (
    DomainKnowledgeManager,
    KnowledgeImportConfig,
    KnowledgeSource,
    PromptEnhancementMode
)
from uno.ai.domain_adaptation.recommendation_adapter import (
    DomainRecommendationAdapter,
    RecommendationAdapterConfig,
    RecommendationTrainingConfig,
    VerticalType
)
from uno.ai.domain_adaptation.template_manager import (
    ContentTemplateManager,
    DomainTemplate,
    TemplateVariable,
    TemplateCategory
)

__all__ = [
    # Embedding adaptation
    'DomainEmbeddingAdapter',
    'EmbeddingAdapterConfig',
    'EmbeddingTrainingConfig',
    'FineTuningMethod',
    
    # Knowledge integration
    'DomainKnowledgeManager',
    'KnowledgeImportConfig',
    'KnowledgeSource',
    'PromptEnhancementMode',
    
    # Recommendation adaptation
    'DomainRecommendationAdapter',
    'RecommendationAdapterConfig',
    'RecommendationTrainingConfig',
    'VerticalType',
    
    # Template management
    'ContentTemplateManager',
    'DomainTemplate',
    'TemplateVariable',
    'TemplateCategory',
]