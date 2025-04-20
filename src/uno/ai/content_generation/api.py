"""
API module for content generation in the Uno framework.

This module provides FastAPI endpoints for content generation, summarization,
and integration with the Uno framework.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, Field

from uno.ai.content_generation.engine import (
    ContentEngine,
    ContentType,
    ContentMode,
    ContentFormat,
    RAGStrategy,
)

# Set up logger
logger = logging.getLogger(__name__)


# Request/Response Models
class IndexContentRequest(BaseModel):
    """Request model for indexing content."""

    content: str = Field(..., description="Text content to index")
    entity_id: str = Field(..., description="Unique identifier for the content")
    entity_type: str = Field(..., description="Type of content")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata"
    )
    graph_nodes: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Additional nodes to add to the graph"
    )
    graph_relationships: Optional[list[dict[str, Any]]] = Field(
        default=None, description="Relationships to add to the graph"
    )


class GenerateContentRequest(BaseModel):
    """Request model for generating content."""

    prompt: str = Field(..., description="Content generation prompt")
    content_type: ContentType = Field(
        default=ContentType.TEXT, description="Type of content to generate"
    )
    mode: ContentMode = Field(
        default=ContentMode.BALANCED,
        description="Generation mode (creative, balanced, precise)",
    )
    format: ContentFormat = Field(
        default=ContentFormat.PLAIN, description="Output format"
    )
    max_length: int = Field(
        default=500, description="Maximum length of generated content"
    )
    context_entity_ids: list[str] | None = Field(
        default=None, description="Optional specific entity IDs to include as context"
    )
    context_entity_types: list[str] | None = Field(
        default=None, description="Optional entity types to search for context"
    )
    rag_strategy: Optional[RAGStrategy] = Field(
        default=None, description="Strategy for retrieval (overrides default)"
    )
    max_context_items: int = Field(
        default=5, description="Maximum number of context items to retrieve"
    )


class SummarizeRequest(BaseModel):
    """Request model for summarizing text."""

    text: str = Field(..., description="Text to summarize")
    max_length: int = Field(default=200, description="Maximum length of summary")
    format: ContentFormat = Field(
        default=ContentFormat.PLAIN, description="Output format"
    )
    mode: ContentMode = Field(
        default=ContentMode.BALANCED, description="Summarization mode"
    )
    bullet_points: bool = Field(
        default=False, description="Whether to generate bullet points"
    )


class ContentResponse(BaseModel):
    """Response model for content generation."""

    content: str = Field(..., description="Generated content")
    content_type: ContentType = Field(..., description="Type of content generated")
    mode: ContentMode = Field(..., description="Generation mode used")
    format: ContentFormat = Field(..., description="Output format")
    context_count: Optional[int] = Field(
        default=None, description="Number of context items used"
    )
    context_sources: list[str] | None = Field(
        default=None, description="Sources of context used"
    )


class SummaryResponse(BaseModel):
    """Response model for summarization."""

    content: str = Field(..., description="Generated summary")
    content_type: ContentType = Field(..., description="Type of content generated")
    mode: ContentMode = Field(..., description="Generation mode used")
    format: ContentFormat = Field(..., description="Output format")
    original_length: int = Field(..., description="Length of original text")
    summary_length: int = Field(..., description="Length of summary")
    reduction_ratio: float = Field(
        ..., description="Ratio of summary to original length"
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(
        default=None, description="Detailed error information"
    )


def create_content_router(engine: ContentEngine) -> APIRouter:
    """
    Create a FastAPI router for content generation endpoints.

    Args:
        engine: ContentEngine instance for content generation

    Returns:
        FastAPI router with content generation endpoints
    """
    router = APIRouter(tags=["Content Generation"])

    @router.post("/content/index", response_model=Dict[str, Any])
    async def index_content(request: IndexContentRequest):
        """
        Index content for retrieval augmented generation.

        Args:
            request: Index content request

        Returns:
            Record ID of indexed content
        """
        try:
            record_id = await engine.index_content(
                content=request.content,
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                metadata=request.metadata,
                graph_nodes=request.graph_nodes,
                graph_relationships=request.graph_relationships,
            )
            return {"record_id": record_id}
        except Exception as e:
            logger.error(f"Error indexing content: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to index content: {str(e)}"
            )

    @router.post("/content/generate", response_model=ContentResponse)
    async def generate_content(request: GenerateContentRequest):
        """
        Generate content using retrieval augmented generation.

        Args:
            request: Generate content request

        Returns:
            Generated content with metadata
        """
        try:
            result = await engine.generate_content(
                prompt=request.prompt,
                content_type=request.content_type,
                mode=request.mode,
                format=request.format,
                max_length=request.max_length,
                context_entity_ids=request.context_entity_ids,
                context_entity_types=request.context_entity_types,
                rag_strategy=request.rag_strategy,
                max_context_items=request.max_context_items,
            )
            return result
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate content: {str(e)}"
            )

    @router.post("/content/summarize", response_model=SummaryResponse)
    async def summarize(request: SummarizeRequest):
        """
        Summarize text content.

        Args:
            request: Summarize request

        Returns:
            Summary with metadata
        """
        try:
            result = await engine.summarize(
                text=request.text,
                max_length=request.max_length,
                format=request.format,
                mode=request.mode,
                bullet_points=request.bullet_points,
            )
            return result
        except Exception as e:
            logger.error(f"Error summarizing content: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to summarize content: {str(e)}"
            )

    return router


def integrate_content_generation(
    app,
    connection_string: str,
    embedding_model: str = "default",
    llm_provider: str = "openai",
    llm_model: str = "gpt-3.5-turbo",
    api_key: str | None = None,
    use_graph_db: bool = True,
    graph_schema: str | None = None,
    rag_strategy: RAGStrategy = RAGStrategy.HYBRID,
    table_name: str = "content_embeddings",
    path_prefix: str = "/api",
):
    """
    Integrate content generation with a FastAPI application.

    Args:
        app: FastAPI application
        connection_string: Database connection string
        embedding_model: Name of embedding model to use
        llm_provider: Provider for language model
        llm_model: Model name for language model
        api_key: API key for language model provider
        use_graph_db: Whether to use Apache AGE graph database
        graph_schema: Schema for graph database
        rag_strategy: Strategy for retrieval augmented generation
        table_name: Table name for vector storage
        path_prefix: Prefix for API routes
    """
    # Create content engine
    engine = ContentEngine(
        embedding_model=embedding_model,
        connection_string=connection_string,
        table_name=table_name,
        llm_provider=llm_provider,
        llm_model=llm_model,
        api_key=api_key,
        use_graph_db=use_graph_db,
        graph_schema=graph_schema,
        rag_strategy=rag_strategy,
    )

    # Create router
    router = create_content_router(engine)

    # Include router
    app.include_router(router, prefix=path_prefix)

    # Initialize on startup
    @app.on_event("startup")
    async def startup():
        await engine.initialize()
        logger.info("Content generation engine initialized")

    # Close on shutdown
    @app.on_event("shutdown")
    async def shutdown():
        await engine.close()
        logger.info("Content generation engine closed")
