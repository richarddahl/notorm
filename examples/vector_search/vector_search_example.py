"""
Vector search example for Uno framework.

This example demonstrates basic vector search usage, RAG implementation,
and hybrid search combining vector similarity with graph traversal.
"""

import asyncio
import json
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Import Uno framework components
from uno.dependencies import get_service_provider
from uno.domain.vector_search import VectorQuery, HybridQuery
from uno.domain.vector_update_service import VectorUpdateService


async def demonstrate_basic_search():
    """Demonstrate basic vector search functionality."""
    logger.info("Demonstrating basic vector search...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get vector search service for documents
    document_search = provider.get_vector_search_service(
        entity_type="document",
        table_name="documents"
    )
    
    # Define a search query
    query = VectorQuery(
        query_text="How does vector search work?",
        limit=5,
        threshold=0.7,
        metric="cosine"  # Options: cosine, l2, dot
    )
    
    # Execute the search
    results = await document_search.search(query)
    
    # Display results
    logger.info(f"Found {len(results)} results for basic search:")
    for i, result in enumerate(results, 1):
        logger.info(f"Result {i}: ID={result.id}, Similarity={result.similarity:.4f}")
        if result.entity:
            logger.info(f"  Title: {result.entity.title}")
            logger.info(f"  Content: {result.entity.content[:100]}...")
        
    return results


async def demonstrate_filtered_search():
    """Demonstrate vector search with additional filters."""
    logger.info("Demonstrating filtered vector search...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get vector search service for documents
    document_search = provider.get_vector_search_service(
        entity_type="document",
        table_name="documents"
    )
    
    # Define a search query
    query = VectorQuery(
        query_text="database performance",
        limit=5,
        threshold=0.7
    )
    
    # Define additional filters (SQL WHERE conditions)
    filters = [
        ("metadata->>'category'", "=", "technical"),
        ("created_at", ">", "2023-01-01")
    ]
    
    # Execute the search with filters
    results = await document_search.search(query, filters=filters)
    
    # Display results
    logger.info(f"Found {len(results)} results for filtered search:")
    for i, result in enumerate(results, 1):
        logger.info(f"Result {i}: ID={result.id}, Similarity={result.similarity:.4f}")
        if result.entity:
            logger.info(f"  Title: {result.entity.title}")
            logger.info(f"  Content: {result.entity.content[:100]}...")
            if hasattr(result.entity, "metadata") and result.entity.metadata:
                metadata = (
                    json.loads(result.entity.metadata) 
                    if isinstance(result.entity.metadata, str) 
                    else result.entity.metadata
                )
                logger.info(f"  Category: {metadata.get('category')}")
    
    return results


async def demonstrate_hybrid_search():
    """Demonstrate hybrid search combining vector similarity with graph traversal."""
    logger.info("Demonstrating hybrid search...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get vector search service for documents
    document_search = provider.get_vector_search_service(
        entity_type="document",
        table_name="documents"
    )
    
    # Define a hybrid search query
    query = HybridQuery(
        query_text="machine learning algorithms",
        limit=5,
        threshold=0.7,
        graph_depth=2,  # How deep to traverse the graph
        graph_weight=0.3  # How much to weight graph connections vs vector similarity
    )
    
    # Execute the hybrid search
    results = await document_search.hybrid_search(query)
    
    # Display results
    logger.info(f"Found {len(results)} results for hybrid search:")
    for i, result in enumerate(results, 1):
        logger.info(f"Result {i}: ID={result.id}, Similarity={result.similarity:.4f}")
        if result.entity:
            logger.info(f"  Title: {result.entity.title}")
            logger.info(f"  Content: {result.entity.content[:100]}...")
        
        # Check if graph metadata is available
        if result.metadata and "graph_distance" in result.metadata:
            logger.info(f"  Graph Distance: {result.metadata['graph_distance']}")
    
    return results


async def demonstrate_rag():
    """Demonstrate Retrieval-Augmented Generation (RAG)."""
    logger.info("Demonstrating RAG (Retrieval-Augmented Generation)...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get RAG service for documents
    rag_service = provider.get_rag_service(
        entity_type="document",
        table_name="documents"
    )
    
    # Define the user query
    query = "What are the key principles of effective database design?"
    
    # Define the system prompt
    system_prompt = "You are a helpful assistant that provides information about databases and data modeling."
    
    # Create a RAG prompt
    prompt = await rag_service.create_rag_prompt(
        query=query,
        system_prompt=system_prompt,
        limit=3,  # Number of documents to retrieve
        threshold=0.7  # Minimum similarity threshold
    )
    
    # Display the generated prompt
    logger.info("Generated RAG prompt:")
    logger.info(f"System prompt: {prompt['system_prompt'][:100]}...")
    logger.info(f"User prompt: {prompt['user_prompt'][:100]}...")
    
    # In a real application, you would now send this prompt to an LLM
    logger.info("In a real application, this prompt would be sent to an LLM for generation.")
    
    return prompt


async def demonstrate_embedding_generation():
    """Demonstrate embedding generation for text."""
    logger.info("Demonstrating embedding generation...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get vector search service
    document_search = provider.get_vector_search_service(
        entity_type="document",
        table_name="documents"
    )
    
    # Sample text to embed
    text = "Vector embeddings are numerical representations of text that capture semantic meaning."
    
    # Generate embedding
    embedding = await document_search.generate_embedding(text)
    
    # Display embedding information
    logger.info(f"Generated embedding for text: '{text}'")
    logger.info(f"Embedding dimensions: {len(embedding)}")
    logger.info(f"First 5 values: {embedding[:5]}")
    
    return embedding


async def demonstrate_vector_update():
    """Demonstrate vector content updates."""
    logger.info("Demonstrating vector content updates...")
    
    # Get the service provider
    provider = get_service_provider()
    
    # Get vector update service
    update_service = provider.get_vector_update_service()
    
    # Start the update service if not already running
    if not update_service._running:
        await update_service.start()
    
    # Queue an update
    document_id = "example123"
    content = "This is example content that will be vectorized and stored in the database."
    
    await update_service.queue_update(
        entity_id=document_id,
        entity_type="document",
        content=content,
        priority=5  # Higher number means higher priority
    )
    
    # Get service statistics
    stats = update_service.get_stats()
    
    logger.info("Vector update service statistics:")
    logger.info(f"Queue size: {stats['queue_size']}")
    logger.info(f"Processed count: {stats['processed_count']}")
    logger.info(f"Error count: {stats['error_count']}")
    logger.info(f"Uptime: {stats['uptime']} seconds")
    
    # In a real application, you would wait for the update to be processed
    # Here we'll just wait a short time for demonstration purposes
    logger.info("Waiting for update to be processed...")
    await asyncio.sleep(2)
    
    # Get updated statistics
    stats = update_service.get_stats()
    logger.info(f"Updated queue size: {stats['queue_size']}")
    
    return stats


async def main():
    """Run the vector search examples."""
    try:
        logger.info("Starting vector search examples...")
        
        # Basic search
        await demonstrate_basic_search()
        
        # Filtered search
        await demonstrate_filtered_search()
        
        # Hybrid search
        await demonstrate_hybrid_search()
        
        # RAG
        await demonstrate_rag()
        
        # Embedding generation
        await demonstrate_embedding_generation()
        
        # Vector updates
        await demonstrate_vector_update()
        
        logger.info("Vector search examples completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in vector search examples: {e}")
        raise
    finally:
        # Clean up any resources
        provider = get_service_provider()
        update_service = provider.get_vector_update_service()
        if update_service._running:
            await update_service.stop()


if __name__ == "__main__":
    asyncio.run(main())