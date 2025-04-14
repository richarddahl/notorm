"""
Advanced graph integration for AI features.

This module provides enhanced knowledge graph capabilities and integrations
for the AI features, enabling more sophisticated context retrieval, 
knowledge construction, and graph-based reasoning.
"""

from uno.ai.graph_integration.graph_navigator import (
    GraphNavigator,
    GraphNavigatorConfig,
    NavigationAlgorithm,
    NavigationStrategy,
    NodeFilter,
    PathConstraint,
    RelationshipType,
    TraversalMode
)
from uno.ai.graph_integration.knowledge_constructor import (
    KnowledgeConstructor,
    KnowledgeConstructorConfig,
    EntityExtractionMethod,
    RelationshipExtractionMethod,
    ConstructionPipeline,
    TextSource,
    ValidationMethod
)
from uno.ai.graph_integration.graph_reasoning import (
    GraphReasoner,
    GraphReasoningConfig,
    InferenceMethod,
    ReasoningStrategy,
    ShortestPathMethod,
    TripleValidation
)
from uno.ai.graph_integration.rag_enhancer import (
    GraphRAGEnhancer,
    GraphRAGConfig,
    ContextEnrichmentStrategy,
    RelevanceMethod,
    GraphQuery,
    ContextNode
)

__all__ = [
    # Graph navigation
    'GraphNavigator',
    'GraphNavigatorConfig',
    'NavigationAlgorithm',
    'NavigationStrategy',
    'NodeFilter',
    'PathConstraint',
    'RelationshipType',
    'TraversalMode',
    
    # Knowledge construction
    'KnowledgeConstructor',
    'KnowledgeConstructorConfig',
    'EntityExtractionMethod',
    'RelationshipExtractionMethod',
    'ConstructionPipeline',
    'TextSource',
    'ValidationMethod',
    
    # Graph reasoning
    'GraphReasoner',
    'GraphReasoningConfig',
    'InferenceMethod',
    'ReasoningStrategy',
    'ShortestPathMethod',
    'TripleValidation',
    
    # RAG enhancement
    'GraphRAGEnhancer',
    'GraphRAGConfig',
    'ContextEnrichmentStrategy',
    'RelevanceMethod',
    'GraphQuery',
    'ContextNode'
]