"""
API endpoints for the recommendation engine.

This module provides FastAPI endpoints for the recommendation system.
"""

import logging
from typing import List, Dict, Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field, validator

from uno.ai.recommendations.engine import RecommendationEngine

# Set up logger
logger = logging.getLogger(__name__)


# Model definitions
class InteractionCreate(BaseModel):
    """Request model for creating an interaction."""

    user_id: str = Field(..., description="User identifier")
    item_id: str = Field(..., description="Item identifier")
    item_type: str = Field("item", description="Item type")
    interaction_type: str = Field(
        "view", description="Interaction type (view, like, purchase, etc.)"
    )
    rating: Optional[float] = Field(None, description="Optional explicit rating (0-5)")
    timestamp: Optional[str] = Field(
        None, description="Interaction timestamp (ISO format)"
    )
    content: Optional[str] = Field(
        None, description="Item content for content-based recommendations"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BatchInteractionCreate(BaseModel):
    """Request model for batch creating interactions."""

    interactions: list[InteractionCreate] = Field(
        ..., description="List of interactions"
    )


class RecommendationRequest(BaseModel):
    """Request model for generating recommendations."""

    user_id: str = Field(..., description="User to generate recommendations for")
    limit: int = Field(
        10, ge=1, le=100, description="Maximum number of recommendations"
    )
    exclusions: list[str] | None = Field(None, description="Items to exclude")
    item_type: Optional[str] = Field(None, description="Filter by item type")


class Recommendation(BaseModel):
    """Model for a recommendation result."""

    item_id: str = Field(..., description="Recommended item ID")
    item_type: str = Field(..., description="Item type")
    score: float = Field(..., description="Recommendation score (higher = better)")
    sources: Optional[list[int]] = Field(
        None, description="Source algorithms (for hybrid recommenders)"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class RecommendationResponse(BaseModel):
    """Response model for recommendations."""

    recommendations: list[Recommendation] = Field(
        ..., description="List of recommendations"
    )
    user_id: str = Field(..., description="User ID")
    count: int = Field(..., description="Number of recommendations")


def create_recommendation_router(
    engine: RecommendationEngine,
    prefix: str = "/recommendations",
    tags: list[str] = ["recommendations"],
) -> APIRouter:
    """
    Create a FastAPI router for recommendation endpoints.

    Args:
        engine: Configured RecommendationEngine instance
        prefix: URL prefix for all routes
        tags: OpenAPI tags for the routes

    Returns:
        FastAPI router with recommendation endpoints
    """
    router = APIRouter(prefix=prefix, tags=tags)

    @router.post("/interactions", status_code=201)
    async def create_interaction(interaction: InteractionCreate):
        """
        Record a user-item interaction.

        Args:
            interaction: Interaction data

        Returns:
            Success status
        """
        try:
            await engine.add_interaction(interaction.dict())
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error creating interaction: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create interaction: {str(e)}"
            )

    @router.post("/interactions/batch", status_code=201)
    async def create_interactions_batch(request: BatchInteractionCreate):
        """
        Record multiple user-item interactions in batch.

        Args:
            request: Batch of interaction data

        Returns:
            Success status
        """
        try:
            interactions = [interaction.dict() for interaction in request.interactions]

            await engine.train(interactions)
            return {"status": "success", "count": len(interactions)}
        except Exception as e:
            logger.error(f"Error creating interactions batch: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to create interactions batch: {str(e)}"
            )

    @router.post("/recommend", response_model=RecommendationResponse)
    async def recommend(request: RecommendationRequest):
        """
        Generate recommendations for a user.

        Args:
            request: Recommendation request

        Returns:
            List of recommendations
        """
        try:
            recommendations = await engine.recommend(
                user_id=request.user_id,
                limit=request.limit,
                exclusions=request.exclusions,
                item_type=request.item_type,
            )

            return {
                "recommendations": recommendations,
                "user_id": request.user_id,
                "count": len(recommendations),
            }
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
            )

    @router.get("/recommend/{user_id}", response_model=RecommendationResponse)
    async def recommend_get(
        user_id: str,
        limit: int = Query(
            10, ge=1, le=100, description="Maximum number of recommendations"
        ),
        item_type: Optional[str] = Query(None, description="Filter by item type"),
    ):
        """
        Generate recommendations for a user (GET method).

        This endpoint provides the same functionality as the POST method
        but uses query parameters for simpler direct API calls.

        Args:
            user_id: User to generate recommendations for
            limit: Maximum number of recommendations
            item_type: Filter by item type

        Returns:
            List of recommendations
        """
        try:
            recommendations = await engine.recommend(
                user_id=user_id, limit=limit, item_type=item_type
            )

            return {
                "recommendations": recommendations,
                "user_id": user_id,
                "count": len(recommendations),
            }
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate recommendations: {str(e)}"
            )

    return router


# Function to integrate with FastAPI application
def integrate_recommendations(
    app,
    connection_string: str,
    prefix: str = "/api/recommendations",
    tags: list[str] = ["recommendations"],
):
    """
    Integrate recommendations into a FastAPI application.

    Args:
        app: FastAPI application
        connection_string: Database connection string
        prefix: URL prefix for recommendation endpoints
        tags: OpenAPI tags for the routes
    """
    from uno.ai.recommendations.engine import RecommendationEngine

    # Create recommendation engine
    engine = RecommendationEngine(connection_string=connection_string)

    # Create router
    router = create_recommendation_router(engine, prefix=prefix.lstrip("/"), tags=tags)

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
