"""
API endpoints for semantic search.

This module provides FastAPI endpoints for the semantic search functionality.
"""

import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator

from uno.ai.semantic_search.engine import SemanticSearchEngine

# Set up logger
logger = logging.getLogger(__name__)


# Model definitions
class DocumentIndexRequest(BaseModel):
    """Request model for indexing a document."""

    text: str = Field(..., description="Document text content")
    entity_id: str = Field(..., description="Unique entity identifier")
    entity_type: str = Field(..., description="Entity type")
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional metadata"
    )

    @field_validator("entity_id")
    def entity_id_not_empty(cls, v):
        """Validate that entity_id is not empty."""
        if not v.strip():
            raise ValueError("entity_id cannot be empty")
        return v

    @field_validator("entity_type")
    def entity_type_not_empty(cls, v):
        """Validate that entity_type is not empty."""
        if not v.strip():
            raise ValueError("entity_type cannot be empty")
        return v


class BatchIndexRequest(BaseModel):
    """Request model for batch indexing documents."""

    documents: list[DocumentIndexRequest] = Field(
        ..., description="List of documents to index"
    )


class IndexResponse(BaseModel):
    """Response model for indexing operations."""

    ids: list[int] = Field(..., description="IDs of indexed documents")


class SearchRequest(BaseModel):
    """Request model for semantic search."""

    query: str = Field(..., description="Search query text")
    entity_type: str | None = Field(default=None, description="Filter by entity type")
    limit: int = Field(
        default=10, ge=1, le=100, description="Maximum number of results"
    )
    similarity_threshold: float = Field(
        default=0.7, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )


class SearchResult(BaseModel):
    """Model for a single search result."""

    id: int = Field(..., description="Internal ID of the document")
    entity_id: str = Field(..., description="Entity identifier")
    entity_type: str = Field(..., description="Entity type")
    metadata: dict[str, Any] = Field(..., description="Entity metadata")
    similarity: float = Field(..., description="Similarity score (0-1)")


class DeleteRequest(BaseModel):
    """Request model for deleting documents."""

    entity_id: str = Field(..., description="Entity identifier to delete")
    entity_type: str | None = Field(default=None, description="Entity type filter")


class DeleteResponse(BaseModel):
    """Response model for delete operations."""

    deleted: int = Field(..., description="Number of documents deleted")


def create_search_router(
    engine: SemanticSearchEngine,
    prefix: str = "/semantic",
    tags: list[str] = ["semantic-search"],
) -> APIRouter:
    """
    Create a FastAPI router for semantic search endpoints.

    Args:
        engine: Configured SemanticSearchEngine instance
        prefix: URL prefix for all routes
        tags: OpenAPI tags for the routes

    Returns:
        FastAPI router with search endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags)

    @router.post("/index", response_model=IndexResponse)
    async def index_document(request: DocumentIndexRequest):
        """
        Index a document for semantic search.

        Args:
            request: Document indexing request

        Returns:
            ID of the indexed document
        """
        try:
            doc_id = await engine.index_document(
                document=request.text,
                entity_id=request.entity_id,
                entity_type=request.entity_type,
                metadata=request.metadata,
            )
            return {"ids": [doc_id]}
        except Exception as e:
            logger.error(f"Error indexing document: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to index document: {str(e)}"
            )

    @router.post("/batch", response_model=IndexResponse)
    async def index_batch(request: BatchIndexRequest):
        """
        Index multiple documents in batch.

        Args:
            request: Batch indexing request

        Returns:
            IDs of indexed documents
        """
        try:
            docs = [
                {
                    "text": doc.text,
                    "entity_id": doc.entity_id,
                    "entity_type": doc.entity_type,
                    "metadata": doc.metadata,
                }
                for doc in request.documents
            ]

            doc_ids = await engine.index_batch(docs)
            return {"ids": doc_ids}
        except Exception as e:
            logger.error(f"Error indexing batch: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to index batch: {str(e)}"
            )

    @router.post("/search", response_model=list[SearchResult])
    async def semantic_search(request: SearchRequest):
        """
        Search for documents similar to the query.

        Args:
            request: Search request

        Returns:
            List of search results
        """
        try:
            results = await engine.search(
                query=request.query,
                entity_type=request.entity_type,
                limit=request.limit,
                similarity_threshold=request.similarity_threshold,
            )

            return [
                SearchResult(
                    id=result["id"],
                    entity_id=result["entity_id"],
                    entity_type=result["entity_type"],
                    metadata=result["metadata"],
                    similarity=result["similarity"],
                )
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    @router.post("/delete", response_model=DeleteResponse)
    async def delete_document(request: DeleteRequest):
        """
        Delete document from the index.

        Args:
            request: Delete request

        Returns:
            Number of deleted documents
        """
        try:
            count = await engine.delete_document(
                entity_id=request.entity_id, entity_type=request.entity_type
            )
            return {"deleted": count}
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

    @router.get("/search", response_model=list[SearchResult])
    async def semantic_search_get(
        query: str = Query(..., description="Search query text"),
        entity_type: str | None = Query(None, description="Filter by entity type"),
        limit: int = Query(10, ge=1, le=100, description="Maximum number of results"),
        similarity_threshold: float = Query(
            0.7, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
        ),
    ):
        """
        Search for documents similar to the query (GET method).

        This endpoint provides the same functionality as the POST method
        but uses query parameters for simpler direct API calls.

        Args:
            query: Search query text
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            List of search results
        """
        try:
            results = await engine.search(
                query=query,
                entity_type=entity_type,
                limit=limit,
                similarity_threshold=similarity_threshold,
            )

            return [
                SearchResult(
                    id=result["id"],
                    entity_id=result["entity_id"],
                    entity_type=result["entity_type"],
                    metadata=result["metadata"],
                    similarity=result["similarity"],
                )
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

    @router.delete("/documents/{entity_id}")
    async def delete_document_get(
        entity_id: str,
        entity_type: str | None = Query(None, description="Entity type filter"),
    ):
        """
        Delete document from the index (DELETE method).

        This endpoint provides the same functionality as the POST method
        but uses path and query parameters for simpler direct API calls.

        Args:
            entity_id: Entity identifier to delete
            entity_type: Optional entity type filter

        Returns:
            Number of deleted documents
        """
        try:
            count = await engine.delete_document(
                entity_id=entity_id, entity_type=entity_type
            )
            return {"deleted": count}
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

    return router


# Function to integrate with FastAPI application
def integrate_semantic_search(
    app,
    connection_string: str,
    prefix: str = "/api/semantic",
    tags: list[str] = ["semantic-search"],
):
    """
    Integrate semantic search into a FastAPI application.

    Args:
        app: FastAPI application
        connection_string: Database connection string
        prefix: URL prefix for search endpoints
        tags: OpenAPI tags for the routes
    """
    from uno.ai.embeddings import get_embedding_model

    # Create search engine
    engine = SemanticSearchEngine(
        embedding_model=get_embedding_model(), connection_string=connection_string
    )

    # Create router
    router = create_search_router(engine, prefix=prefix.lstrip("/"), tags=tags)

    # Add router to app
    app.include_router(router, prefix=prefix)

    # Initialize on startup
    @app.on_event("startup")
    async def startup():
        await engine.initialize()

    # Close on shutdown
    @app.on_event("shutdown")
    async def shutdown():
        await engine.close()
