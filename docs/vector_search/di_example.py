"""
Example of using vector search components with dependency injection.

This example demonstrates how to use the ServiceProvider to access
and work with vector search services in a type-safe and consistent manner.
"""

import asyncio
from typing import List, Dict, Any, Optional

from uno.dependencies import (
    initialize_services,
    get_service_provider,
    VectorConfigServiceProtocol,
    VectorSearchServiceProtocol,
    VectorUpdateServiceProtocol,
    RAGServiceProtocol
)
from uno.dependencies.vector_interfaces import VectorQueryProtocol


# Example entity class that would be returned from vector search
class Document:
    """Example document class for demonstration."""
    
    def __init__(self, id: str, title: str, content: str):
        self.id = id
        self.title = title
        self.content = content
        

async def initialize_application():
    """Initialize the application's services."""
    print("Initializing application services...")
    
    # Initialize all services at the application's entry point
    # This will also initialize vector search components
    initialize_services()
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get configuration and check vector settings
    config = provider.get_config()
    print(f"Application initialized with vector dimensions: {config.get_value('VECTOR_DIMENSIONS', 1536)}")
    
    # Get vector-specific configuration
    vector_config = provider.get_vector_config()
    print(f"Vector index type: {vector_config.get_index_type()}")
    
    # Register a new vectorizable entity
    vector_config.register_vectorizable_entity(
        entity_type="document",
        fields=["title", "content"],
        dimensions=1536,
        index_type="hnsw"
    )
    print(f"Registered entity types: {list(vector_config.get_all_vectorizable_entities().keys())}")
    
    return provider


async def vector_search_example(provider):
    """
    Demonstrate using vector search services.
    
    Args:
        provider: The service provider
    """
    print("\nDemonstrating vector search...")
    
    # Create a vector search service for documents
    document_search = provider.get_vector_search_service(
        entity_type=Document,
        table_name="documents"
    )
    
    # Create a simple query - in a real application this would
    # be a proper class implementing VectorQueryProtocol
    class DocumentQuery:
        def __init__(self, query_text: str, limit: int = 5, threshold: float = 0.7):
            self.query_text = query_text
            self.limit = limit
            self.threshold = threshold
            self.metric = "cosine"
            
        def model_dump(self) -> Dict[str, Any]:
            return {
                "query_text": self.query_text,
                "limit": self.limit,
                "threshold": self.threshold,
                "metric": self.metric
            }
    
    # Perform a vector search
    query = DocumentQuery("Example search query")
    results = await document_search.search(query)
    print(f"Search returned {len(results)} results")
    
    # Create a RAG service using the document search
    rag_service = provider.get_rag_service(document_search)
    
    # Create a RAG prompt
    prompt = await rag_service.create_rag_prompt(
        query="How do I use vector search?",
        system_prompt="You are a helpful assistant.",
        limit=3,
        threshold=0.7
    )
    
    print("Generated RAG prompt with system prompt:", prompt["system_prompt"][:50] + "...")
    print("User prompt:", prompt["user_prompt"][:50] + "...")
    
    return rag_service


async def vector_update_example(provider):
    """
    Demonstrate using vector update services.
    
    Args:
        provider: The service provider
    """
    print("\nDemonstrating vector updates...")
    
    # Get the vector update service
    update_service = provider.get_vector_update_service()
    
    # Queue some updates
    await update_service.queue_update(
        entity_id="doc-1",
        entity_type="document",
        content="This is an example document for vector search",
        priority=1
    )
    
    await update_service.queue_update(
        entity_id="doc-2",
        entity_type="document",
        content="Another example document with different content",
        priority=0
    )
    
    # Get service statistics
    stats = update_service.get_stats()
    print(f"Update service stats: {stats}")
    
    # Get the batch update service for bulk operations
    batch_service = provider.get_batch_vector_update_service()
    
    # Update multiple entities by ID
    result = await batch_service.update_entities_by_ids(
        entity_type="document",
        entity_ids=["doc-3", "doc-4", "doc-5"],
        content_fields=["title", "content"]
    )
    
    print(f"Batch update result: {result}")
    
    return update_service


async def main():
    """Main example function."""
    provider = await initialize_application()
    
    # Demonstrate vector search
    rag_service = await vector_search_example(provider)
    
    # Demonstrate vector updates
    update_service = await vector_update_example(provider)
    
    # Clean up (stop any background services)
    try:
        await update_service.stop()
        print("Vector update service stopped")
    except Exception as e:
        print(f"Error stopping update service: {e}")


if __name__ == "__main__":
    asyncio.run(main())