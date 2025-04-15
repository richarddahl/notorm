# Retrieval-Augmented Generation (RAG)

This guide explains how to use uno's vector search system for Retrieval-Augmented Generation (RAG) with LLMs.

## What is RAG?

Retrieval-Augmented Generation (RAG) is a technique that combines:

1. **Retrieval**: Finding relevant documents/information from a knowledge base
2. **Augmentation**: Adding this information to the prompt for an LLM
3. **Generation**: Having the LLM generate a response using the augmented context

RAG helps LLMs:
- Access domain-specific knowledge
- Provide more accurate and relevant responses
- Reduce hallucinations by grounding responses in facts
- Stay up-to-date with information beyond their training cutoff

## RAG Architecture in uno

uno's RAG system has these components:

1. **Vector Search Service**: Finds semantically relevant entities
2. **RAG Service**: Formats entities into context for LLM prompts
3. **Optional Integration**: Connect to your preferred LLM service

## Basic RAG Usage

Here's how to use the RAG service:

```python
from uno.domain.vector_search import RAGService, VectorSearchService

# Set up vector search
vector_search = VectorSearchService(
    entity_type=Document,
    table_name="document",
    repository=document_repository
)

# Create RAG service
rag_service = RAGService(vector_search=vector_search)

# Get a complete RAG prompt
rag_prompt = await rag_service.create_rag_prompt(
    query="How do I implement pagination in REST APIs?",
    system_prompt="You are a helpful technical assistant...",
    limit=5,
    threshold=0.7
)

# Use with your LLM integration
system_prompt = rag_prompt["system_prompt"]
user_prompt = rag_prompt["user_prompt"]

# ... Send to your LLM service
```

## Context Retrieval

To retrieve context without generating a prompt:

```python
# Get entities for context
entities, search_results = await rag_service.retrieve_context(
    query="Explain vector search in databases",
    limit=5,
    threshold=0.7
)

# Use entities directly
for entity in entities:
    print(f"Title: {entity.title}")
    print(f"Relevance: {search_results[i].similarity}")
```

## Customizing Context Formatting

You can customize how entities are formatted by subclassing `RAGService`:

```python
class DocumentRAG(RAGService[Document]):
    def format_context_for_prompt(self, entities: List[Document]) -> str:
        context_parts = []
        
        for i, doc in enumerate(entities):
            context_text = f"[Document {i+1}]\n"
            context_text += f"Title: {doc.title}\n"
            context_text += f"Summary: {doc.summary}\n"
            context_text += f"Content: {doc.content[:300]}...\n"
            
            if doc.source_url:
                context_text += f"Source: {doc.source_url}\n"
                
            context_parts.append(context_text)
        
        return "\n---\n".join(context_parts)
```

## Advanced RAG Patterns

### Hybrid RAG

Combine graph traversal with vector search for more contextual retrieval:

```python
from uno.domain.vector_search import HybridQuery

# Create a hybrid query
hybrid_query = HybridQuery(
    query_text="PostgreSQL performance tuning",
    start_node_type="Document",
    path_pattern="(n:Document)-[:TAGGED_WITH]->(:Tag {name: 'Database'})"
)

# Get results
hybrid_results = await vector_search.hybrid_search(hybrid_query)

# Extract entities
entities = [result.entity for result in hybrid_results if result.entity]

# Format as context
context = rag_service.format_context_for_prompt(entities)
```

## Graph-Enhanced RAG

uno provides advanced graph-enhanced RAG capabilities through the `GraphRAGService` class, which leverages the knowledge graph to provide richer context for LLM interactions.

### Setting Up Graph-Enhanced RAG

```python
from uno.ai.graph_integration.graph_rag import GraphRAGService, create_graph_rag_service

# Create the service with factory function
graph_rag = await create_graph_rag_service(
    connection_string="postgresql://user:password@localhost:5432/database",
    entity_type=Document,
    table_name="document",
    graph_name="knowledge_graph"
)

# Or create it with individual components
from uno.ai.graph_integration.graph_navigator import GraphNavigator
from uno.ai.graph_integration.knowledge_constructor import KnowledgeConstructor

graph_rag = GraphRAGService(
    vector_search=vector_search,
    graph_navigator=graph_navigator,
    knowledge_constructor=knowledge_constructor
)
```

### Using Graph-Enhanced RAG

```python
# Create a graph-enhanced prompt
prompt = await graph_rag.create_graph_enhanced_prompt(
    query="Explain the relationship between PostgreSQL and Apache AGE",
    system_prompt="You are a knowledgeable technical assistant...",
    limit=5,
    threshold=0.7,
    max_depth=3,
    strategy="hybrid"
)

# Use with your LLM integration
system_prompt = prompt["system_prompt"]
user_prompt = prompt["user_prompt"]
```

### Retrieve Graph Context

```python
# Get graph-based context for a query
graph_contexts = await graph_rag.retrieve_graph_context(
    query="How does Apache AGE integrate with PostgreSQL?",
    limit=5,
    threshold=0.7,
    max_depth=3,
    strategy="hybrid"
)

# Format contexts for display
formatted_context = graph_rag.format_context_for_prompt(graph_contexts)
print(formatted_context)
```

### Using Path-Based Context

```python
# Retrieve context from a path between two entities
path_context = await graph_rag.retrieve_path_context(
    start_node_id="document-123",
    end_node_id="document-456",
    max_depth=3,
    relationship_types=["REFERENCES", "RELATED_TO"],
    reasoning_type="causal"  # Optional reasoning type
)

# Access the formatted path context
if path_context:
    print(path_context.text)
```

### Using Subgraph Context

```python
# Retrieve context from a subgraph around an entity
subgraph_context = await graph_rag.retrieve_subgraph_context(
    center_node_id="document-123",
    max_depth=2,
    max_nodes=10,
    relationship_types=["AUTHORED_BY", "TAGGED_WITH"]
)

# Access the formatted subgraph context
if subgraph_context:
    print(subgraph_context.text)
```

### Combining Vector and Graph Context

```python
# Create a hybrid prompt with both vector and graph context
hybrid_prompt = await graph_rag.create_hybrid_rag_prompt(
    query="What are the best practices for using PostgreSQL with Apache AGE?",
    system_prompt="You are a helpful database expert...",
    vector_limit=3,
    graph_limit=3,
    threshold=0.7,
    max_depth=2
)

# Use with your LLM integration
system_prompt = hybrid_prompt["system_prompt"]
user_prompt = hybrid_prompt["user_prompt"]
```

## Multi-step RAG

For complex queries, you can implement multi-step RAG:

1. First retrieve general context
2. Then use that to formulate more specific queries
3. Retrieve specific information for those queries
4. Combine all context for the final prompt

## Chunking Strategy

For long documents, consider chunking strategies:

1. **Fixed-size Chunks**: Split documents into equal-sized chunks
2. **Semantic Chunks**: Split at semantic boundaries (paragraphs, sections)
3. **Sliding Window**: Create overlapping chunks for better context preservation

## Performance Tips

1. **Cache Common Queries**: Cache retrieval results for common queries
2. **Optimize Chunk Size**: Balance between specificity and context
3. **Set Appropriate Thresholds**: Adjust similarity thresholds to control quality
4. **Limit Context Size**: Keep total context within LLM token limits

## Example RAG Applications

- **Documentation Assistant**: Answer questions about your product documentation
- **Code Helper**: Retrieve relevant code examples for programming questions
- **Knowledge Base**: Create a conversational interface to a knowledge base
- **Research Tool**: Find and summarize relevant research papers