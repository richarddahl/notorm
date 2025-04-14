"""
Example demonstrating cross-feature AI integration capabilities.

This example shows how to use the unified context manager and shared embedding service
to create an integrated experience that combines semantic search, recommendations,
content generation, and anomaly detection.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional

from uno.ai.integration import (
    ContextItem,
    ContextSource,
    ContextType,
    EnhancedRAGService,
    Relevance,
    SharedEmbeddingService,
    UnifiedContextManager,
)
from uno.ai.semantic_search.engine import SemanticSearchEngine
from uno.ai.recommendations.engine import RecommendationEngine
from uno.ai.content_generation.engine import ContentGenerationEngine
from uno.ai.anomaly_detection.engine import AnomalyDetectionEngine


async def setup_integration_example():
    """Set up the integration example with all components."""
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ai_integration_example")
    
    # Initialize unified context manager
    context_manager = UnifiedContextManager(
        connection_string="postgresql://postgres:postgres@localhost:5432/uno_test",
        logger=logger
    )
    await context_manager.initialize()
    
    # Initialize shared embedding service
    embedding_service = SharedEmbeddingService(logger=logger)
    await embedding_service.initialize()
    
    # Initialize enhanced RAG service
    rag_service = EnhancedRAGService(
        context_manager=context_manager,
        embedding_service=embedding_service,
        logger=logger
    )
    await rag_service.initialize()
    
    # Initialize the individual AI engines
    semantic_search = SemanticSearchEngine()
    recommendation_engine = RecommendationEngine()
    content_generation = ContentGenerationEngine()
    anomaly_detection = AnomalyDetectionEngine()
    
    return {
        "context_manager": context_manager,
        "embedding_service": embedding_service,
        "rag_service": rag_service,
        "semantic_search": semantic_search,
        "recommendation_engine": recommendation_engine,
        "content_generation": content_generation,
        "anomaly_detection": anomaly_detection,
        "logger": logger
    }


async def simulate_user_session(components: Dict, user_id: str, session_id: str):
    """
    Simulate a user session with multiple AI features using shared context.
    
    Args:
        components: Dictionary of AI components
        user_id: User ID for the session
        session_id: Session ID
    """
    logger = components["logger"]
    context_manager = components["context_manager"]
    embedding_service = components["embedding_service"]
    rag_service = components["rag_service"]
    semantic_search = components["semantic_search"]
    recommendation_engine = components["recommendation_engine"]
    content_generation = components["content_generation"]
    anomaly_detection = components["anomaly_detection"]
    
    # Step 1: User performs a search
    logger.info("Step 1: User performs a semantic search")
    search_query = "advanced database optimization techniques"
    search_results = await semantic_search.search(search_query)
    
    # Store search context
    await context_manager.create_search_context(
        query=search_query,
        results=search_results,
        user_id=user_id,
        session_id=session_id
    )
    
    # Step 2: System provides recommendations based on search
    logger.info("Step 2: System provides recommendations based on search context")
    recommendations = await recommendation_engine.get_recommendations(
        user_id=user_id,
        context_items=await context_manager.get_session_context(session_id)
    )
    
    # Store recommendation context
    await context_manager.create_recommendation_context(
        user_id=user_id,
        recommendations=recommendations,
        session_id=session_id
    )
    
    # Step 3: User requests content generation with context
    logger.info("Step 3: User requests content generation with shared context")
    generation_prompt = "Explain these database optimization techniques in simple terms"
    
    # Get all context to enrich the prompt
    context_items = await context_manager.query_context(
        query=context_manager.ContextQuery(
            user_id=user_id,
            session_id=session_id,
            limit=10
        )
    )
    
    # Use RAG service to enrich the prompt with context
    enriched_prompt = await rag_service.enrich_rag_prompt(
        prompt=generation_prompt,
        user_id=user_id,
        session_id=session_id
    )
    
    # Generate content
    generated_content = await content_generation.generate_content(
        prompt=enriched_prompt
    )
    
    # Store content generation context
    context_sources = [item.id for item in context_items]
    await context_manager.create_content_generation_context(
        prompt=generation_prompt,
        content=generated_content,
        user_id=user_id,
        session_id=session_id,
        context_sources=context_sources
    )
    
    # Step 4: Anomaly detection identifies unusual patterns
    logger.info("Step 4: Anomaly detection identifies unusual patterns")
    anomaly_results = await anomaly_detection.process_data(
        user_id=user_id,
        session_id=session_id,
        data_type="user_session",
        data={
            "search_query": search_query,
            "search_results_count": len(search_results),
            "recommendations_count": len(recommendations),
            "content_length": len(generated_content),
            "session_duration": 120,  # seconds
        }
    )
    
    # Store anomaly context if anomalies found
    if anomaly_results.get("anomalies"):
        for anomaly in anomaly_results["anomalies"]:
            await context_manager.create_anomaly_context(
                alert=anomaly,
                user_id=user_id,
                session_id=session_id
            )
    
    # Step 5: Query for all context created during this session
    logger.info("Step 5: Query for all context created during this session")
    all_context = await context_manager.get_session_context(
        session_id=session_id,
        limit=100,
        include_expired=True
    )
    
    logger.info(f"Generated {len(all_context)} context items during this session")
    
    # Print summary of context items by type
    context_by_type = {}
    for item in all_context:
        if item.type not in context_by_type:
            context_by_type[item.type] = 0
        context_by_type[item.type] += 1
    
    logger.info("Context items by type:")
    for type_name, count in context_by_type.items():
        logger.info(f"  - {type_name}: {count}")
    
    # Step 6: Use context to enhance the user experience in next session
    logger.info("Step 6: Use context to enhance user experience in next session")
    
    # This would be called in a new session
    new_session_id = f"{session_id}_followup"
    
    # Get context from previous session
    previous_context = await context_manager.get_user_context(
        user_id=user_id,
        limit=10
    )
    
    # Use context to create a personalized experience
    logger.info(f"Found {len(previous_context)} relevant context items from previous sessions")
    
    # Example of combining context from different AI features
    combined_context = {
        "search_history": [],
        "recommendations_history": [],
        "content_history": [],
        "anomalies": []
    }
    
    for item in previous_context:
        if item.source == ContextSource.SEARCH and item.type == ContextType.QUERY:
            combined_context["search_history"].append(item.value)
        elif item.source == ContextSource.RECOMMENDATION:
            combined_context["recommendations_history"].append(item.value)
        elif item.source == ContextSource.CONTENT_GENERATION and item.type == ContextType.RESULT:
            combined_context["content_history"].append(item.value)
        elif item.source == ContextSource.ANOMALY_DETECTION:
            combined_context["anomalies"].append(item.value)
    
    logger.info("Combined context summary:")
    logger.info(f"  - Search history: {len(combined_context['search_history'])} queries")
    logger.info(f"  - Recommendation history: {len(combined_context['recommendations_history'])} sets")
    logger.info(f"  - Content history: {len(combined_context['content_history'])} items")
    logger.info(f"  - Anomalies: {len(combined_context['anomalies'])} alerts")
    
    # Clean up
    await context_manager.close()
    await embedding_service.close()
    await rag_service.close()


async def main():
    """Run the integration example."""
    components = await setup_integration_example()
    
    user_id = "user123"
    session_id = "session456"
    
    await simulate_user_session(components, user_id, session_id)


if __name__ == "__main__":
    asyncio.run(main())