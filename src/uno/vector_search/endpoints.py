"""
FastAPI endpoints for vector search functionality.

These endpoints demonstrate using vector search services through
the dependency injection system, providing a complete API for
vector search capabilities.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body

from uno.dependencies import (
    get_service_provider,
    VectorConfigServiceProtocol,
    VectorSearchServiceProtocol,
    RAGServiceProtocol,
    get_vector_search_service
)
# Helper function to replace inject_dependency
def inject_dependency(interface_type):
    def _inject(request):
        from uno.dependencies.modern_provider import get_service_provider
        provider = get_service_provider()
        return provider.get_service(interface_type)
    return _inject
from uno.domain.vector_search import VectorQuery


router = APIRouter(
    prefix="/api/vector",
    tags=["Vector Search"],
    responses={404: {"description": "Not found"}},
)


# Define our query model
class VectorSearchQuery:
    """Vector search query model."""
    
    def __init__(self, 
                query_text: str, 
                limit: int = 10, 
                threshold: float = 0.7,
                metric: str = "cosine"):
        self.query_text = query_text
        self.limit = limit
        self.threshold = threshold
        self.metric = metric
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "query_text": self.query_text,
            "limit": self.limit,
            "threshold": self.threshold,
            "metric": self.metric
        }


# Define result model for API responses
class VectorSearchResult:
    """API response model for vector search results."""
    
    id: str
    similarity: float
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


# Helper function to get the config service
def get_vector_config():
    """Get the vector configuration service."""
    provider = get_service_provider()
    return provider.get_vector_config()


# Helper function to get a search service for a specific entity type
def get_documents_search_service():
    """Get the document search service."""
    provider = get_service_provider()
    return provider.get_vector_search_service(
        entity_type="document",
        table_name="documents"
    )


@router.get("/config")
async def get_config(
    config: VectorConfigServiceProtocol = Depends(inject_dependency(VectorConfigServiceProtocol))
):
    """Get vector search configuration."""
    return {
        "default_dimensions": config.get_dimensions(),
        "default_index_type": config.get_index_type(),
        "vectorizable_entities": list(config.get_all_vectorizable_entities().keys())
    }


@router.post("/search/documents")
async def search_documents(
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    metric: str = "cosine",
    search_service = Depends(get_documents_search_service)
):
    """
    Search documents using vector similarity.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
        threshold: Minimum similarity threshold
        metric: Distance metric to use (cosine, l2, dot)
        
    Returns:
        List of document search results
    """
    try:
        # Create a query object
        search_query = VectorSearchQuery(
            query_text=query,
            limit=limit,
            threshold=threshold,
            metric=metric
        )
        
        # Execute the search
        results = await search_service.search(search_query)
        
        # Convert to API response format
        response = []
        for result in results:
            response.append({
                "id": result.id,
                "similarity": result.similarity,
                "metadata": result.metadata,
                "title": getattr(result.entity, "title", None),
                "content": getattr(result.entity, "content", None)
            })
            
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@router.post("/hybrid/documents")
async def hybrid_search_documents(
    query: str,
    limit: int = 10,
    threshold: float = 0.7,
    search_service = Depends(get_documents_search_service)
):
    """
    Perform hybrid search on documents.
    
    This endpoint combines graph traversal with vector similarity search.
    
    Args:
        query: The search query text
        limit: Maximum number of results to return
        threshold: Minimum similarity threshold
        
    Returns:
        List of document search results
    """
    try:
        # Create a query object
        search_query = VectorSearchQuery(
            query_text=query,
            limit=limit,
            threshold=threshold
        )
        
        # Execute the hybrid search
        results = await search_service.hybrid_search(search_query)
        
        # Convert to API response format
        response = []
        for result in results:
            response.append({
                "id": result.id,
                "similarity": result.similarity,
                "metadata": result.metadata,
                "title": getattr(result.entity, "title", None),
                "content": getattr(result.entity, "content", None)
            })
            
        return response
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hybrid search error: {str(e)}")


@router.post("/embed")
async def generate_embedding(
    text: str = Body(..., description="Text to embed"),
    search_service = Depends(get_documents_search_service)
):
    """
    Generate an embedding vector for text.
    
    This endpoint allows clients to generate embeddings using the same
    underlying system used by the vector search functionality.
    
    Args:
        text: The text to generate an embedding for
        
    Returns:
        Object with the embedding vector
    """
    try:
        embedding = await search_service.generate_embedding(text)
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "dimensions": len(embedding),
            "embedding": embedding
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Embedding generation error: {str(e)}"
        )


@router.post("/rag/prompt")
async def generate_rag_prompt(
    query: str = Body(..., description="User query"),
    system_prompt: str = Body(..., description="System prompt"),
    limit: int = Body(3, description="Maximum number of documents to retrieve"),
    threshold: float = Body(0.7, description="Minimum similarity threshold"),
    provider = Depends(get_service_provider)
):
    """
    Generate a RAG prompt with retrieved context.
    
    This endpoint retrieves relevant documents based on the query,
    and formats them as context for a prompt to send to an LLM.
    
    Args:
        query: The user's query
        system_prompt: System prompt for the LLM
        limit: Maximum number of documents to retrieve
        threshold: Minimum similarity threshold
        
    Returns:
        Dictionary with system_prompt and user_prompt
    """
    try:
        # Get the RAG service
        rag_service = provider.get_rag_service(
            entity_type="document",
            table_name="documents"
        )
        
        # Generate the RAG prompt
        prompt = await rag_service.create_rag_prompt(
            query=query,
            system_prompt=system_prompt,
            limit=limit,
            threshold=threshold
        )
        
        return prompt
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"RAG prompt generation error: {str(e)}"
        )


@router.post("/examples/create")
async def create_examples():
    """Create example documents for vector search."""
    try:
        from uno.vector_search.examples import create_example_documents
        
        document_ids = await create_example_documents()
        return {
            "status": "success",
            "message": f"Created {len(document_ids)} example documents",
            "document_ids": document_ids
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to create example documents: {str(e)}"
        )