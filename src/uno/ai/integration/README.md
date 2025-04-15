# AI Cross-Feature Integration

This module provides integration between the different AI features in the uno platform, including:
- Semantic search
- Recommendations
- Content generation
- Anomaly detection

## Components

### Unified Context Manager

The `UnifiedContextManager` provides a central repository for sharing context between different AI features, enabling more effective integration and enhanced capabilities. It includes:

- In-memory and database storage for context items
- Context indexing for efficient retrieval
- Embedding-based semantic search for context
- Specialized context creation methods for each AI feature

### Shared Embedding Service

The `SharedEmbeddingService` provides a consolidated embedding infrastructure for all AI features, with support for:

- Multiple embedding model types (Sentence Transformers, Hugging Face, OpenAI)
- Efficient caching of embeddings
- Batch processing for performance
- Similarity computation between embeddings

### Enhanced RAG Service

The `EnhancedRAGService` integrates context management, embedding, and content generation to provide sophisticated RAG capabilities, including:

- Context retrieval from multiple sources
- Prompt enrichment with relevant context
- Integration with anomaly detection for more reliable RAG

### Intelligent Recommendation Service

The `IntelligentRecommendationService` combines behavioral analysis, semantic understanding, and anomaly detection to provide more effective recommendations, including:

- Context-aware recommendation generation
- Multiple recommendation strategies (behavior, similarity, popularity, complementary, expert)
- Anomaly filtering to prevent problematic recommendations
- Enhanced explanation generation

## Usage Example

See the integration example at `/src/uno/ai/examples/integration_example.py` for a demonstration of how these components work together.

## Key Benefits

1. **Shared Context**: All AI features can access and contribute to a unified context store, enabling more intelligent and coherent user experiences.

2. **Cross-Feature Insights**: Anomaly detection can inform recommendations, search can enhance content generation, and all features can leverage common embeddings.

3. **Unified Configuration**: Central management of shared resources like embeddings and database connections.

4. **Consistent API**: Similar patterns for accessing and utilizing resources across features.

5. **Enhanced Capabilities**: Each feature becomes more powerful when integrated with the others.