"""
Intelligent recommendation service with cross-feature integration.

This module provides an enhanced recommendation service that integrates with
other AI features, including semantic search, anomaly detection, and content
generation for more effective recommendations.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np
from pydantic import BaseModel, Field

from uno.ai.integration.context import (
    ContextItem,
    ContextQuery,
    ContextSource,
    ContextType,
    Relevance,
    UnifiedContextManager,
)
from uno.ai.integration.embeddings import (
    EnhancedRAGService,
    SharedEmbeddingService,
)


class RecommendationStrength(str, Enum):
    """Strength of a recommendation."""

    STRONG = "strong"
    MEDIUM = "medium"
    WEAK = "weak"
    UNKNOWN = "unknown"


class RecommendationSource(str, Enum):
    """Source of a recommendation."""

    BEHAVIOR = "behavior"
    SIMILARITY = "similarity"
    POPULARITY = "popularity"
    COMPLEMENTARY = "complementary"
    EXPERT = "expert"
    HYBRID = "hybrid"


class RecommendationPriority(int, Enum):
    """Priority level for a recommendation."""

    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class RecommendationReason(BaseModel):
    """Explanation for why an item was recommended."""

    source: RecommendationSource
    explanation: str
    confidence: float = 0.0
    supporting_items: list[str] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    """Single item recommendation with metadata."""

    item_id: str
    item_type: str
    title: str
    description: str | None = None
    strength: RecommendationStrength = RecommendationStrength.MEDIUM
    priority: RecommendationPriority = RecommendationPriority.MEDIUM
    reasons: list[RecommendationReason] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    similarity_score: Optional[float] = None
    embedding: Optional[list[float]] = None
    created_at: datetime = Field(default_factory=datetime.now)


class RecommendationRequest(BaseModel):
    """Request for recommendations."""

    user_id: str | None = None
    session_id: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    limit: int = 10
    include_explanations: bool = True
    include_embeddings: bool = False
    min_strength: Optional[RecommendationStrength] = None
    sources: list[RecommendationSource] = Field(default_factory=list)
    max_priority: Optional[RecommendationPriority] = None


class RecommendationSet(BaseModel):
    """Set of recommendations with metadata."""

    items: list[RecommendationItem]
    user_id: str | None = None
    session_id: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    context_ids: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)


class IntelligentRecommendationService:
    """
    Enhanced recommendation service with cross-feature integration.

    This service combines behavioral analysis, semantic understanding, and
    anomaly detection to provide more effective recommendations. It integrates
    with the unified context manager to share and utilize context from other
    AI features.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        context_manager=None,
        embedding_service=None,
        rag_service=None,
        anomaly_detection_service=None,
        content_generation_service=None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the intelligent recommendation service.

        Args:
            connection_string: Database connection string
            context_manager: Optional context manager to use
            embedding_service: Optional embedding service to use
            rag_service: Optional RAG service to use
            anomaly_detection_service: Optional anomaly detection service
            content_generation_service: Optional content generation service
            logger: Logger to use
        """
        self.connection_string = connection_string
        self.context_manager = context_manager
        self.embedding_service = embedding_service
        self.rag_service = rag_service
        self.anomaly_detection_service = anomaly_detection_service
        self.content_generation_service = content_generation_service
        self.logger = logger or logging.getLogger(__name__)

        # Database connection pool
        self.pool = None

        # Cache for frequently used items
        self.item_cache = {}
        self.embedding_cache = {}

        # Active item registry
        self.active_items: Dict[str, Dict[str, Any]] = {}

        # Filter for anomalous items
        self.anomaly_filter_enabled = True

        # Initialized flag
        self.initialized = False

    async def initialize(self) -> None:
        """Initialize the recommendation service."""
        if self.initialized:
            return

        # Set up database connection
        if self.connection_string:
            import asyncpg

            self.pool = await asyncpg.create_pool(self.connection_string)

            # Initialize tables if needed
            async with self.pool.acquire() as conn:
                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recommendation_items (
                        item_id TEXT,
                        item_type TEXT,
                        title TEXT,
                        description TEXT,
                        metadata JSONB,
                        embedding VECTOR(384),
                        created_at TIMESTAMP WITH TIME ZONE,
                        PRIMARY KEY (item_id, item_type)
                    )
                """
                )

                await conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS recommendation_interactions (
                        user_id TEXT,
                        item_id TEXT,
                        item_type TEXT,
                        interaction_type TEXT,
                        timestamp TIMESTAMP WITH TIME ZONE,
                        context_id TEXT,
                        metadata JSONB,
                        PRIMARY KEY (user_id, item_id, item_type, interaction_type, timestamp)
                    )
                """
                )

        # Initialize context manager if not provided
        if not self.context_manager:
            from uno.ai.integration.context import UnifiedContextManager

            self.context_manager = UnifiedContextManager(
                connection_string=self.connection_string, logger=self.logger
            )
            await self.context_manager.initialize()

        # Initialize embedding service if not provided
        if not self.embedding_service:
            from uno.ai.integration.embeddings import SharedEmbeddingService

            self.embedding_service = SharedEmbeddingService(logger=self.logger)
            await self.embedding_service.initialize()

        # Initialize RAG service if not provided
        if not self.rag_service:
            from uno.ai.integration.embeddings import EnhancedRAGService

            self.rag_service = EnhancedRAGService(
                connection_string=self.connection_string,
                context_manager=self.context_manager,
                embedding_service=self.embedding_service,
                logger=self.logger,
            )
            await self.rag_service.initialize()

        # Try to initialize anomaly detection service
        if not self.anomaly_detection_service:
            try:
                from uno.ai.anomaly_detection.engine import AnomalyDetectionEngine

                self.anomaly_detection_service = AnomalyDetectionEngine()
                await self.anomaly_detection_service.initialize()
            except ImportError:
                self.logger.warning("Anomaly detection service not available")

        # Try to initialize content generation service
        if not self.content_generation_service:
            try:
                from uno.ai.content_generation.engine import ContentGenerationEngine

                self.content_generation_service = ContentGenerationEngine()
                await self.content_generation_service.initialize()
            except ImportError:
                self.logger.warning("Content generation service not available")

        self.initialized = True

    async def close(self) -> None:
        """Close the recommendation service and release resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None

        if self.context_manager:
            await self.context_manager.close()

        if self.embedding_service:
            await self.embedding_service.close()

        if self.rag_service:
            await self.rag_service.close()

        if self.anomaly_detection_service:
            await self.anomaly_detection_service.close()

        if self.content_generation_service:
            await self.content_generation_service.close()

        self.initialized = False

    async def get_recommendations(
        self,
        request: Optional[RecommendationRequest] = None,
        user_id: str | None = None,
        session_id: str | None = None,
        entity_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 10,
        context_items: Optional[list[ContextItem]] = None,
    ) -> RecommendationSet:
        """
        Get recommendations for a user, session, or entity.

        Args:
            request: Full recommendation request (takes precedence if provided)
            user_id: User ID to get recommendations for
            session_id: Session ID to get recommendations for
            entity_id: Entity ID to get recommendations for
            entity_type: Entity type to get recommendations for
            limit: Maximum number of recommendations to return
            context_items: Context items to use for recommendations

        Returns:
            Set of recommendations
        """
        if not self.initialized:
            await self.initialize()

        # Build request if not provided
        if not request:
            request = RecommendationRequest(
                user_id=user_id,
                session_id=session_id,
                entity_id=entity_id,
                entity_type=entity_type,
                limit=limit,
            )

            if context_items:
                request.context_ids = [item.id for item in context_items]

        # Collect context for recommendation
        context = await self._collect_context(request)

        # Generate candidate recommendations
        candidates = await self._generate_candidates(request, context)

        # Filter candidates using anomaly detection if available
        if self.anomaly_detection_service and self.anomaly_filter_enabled:
            candidates = await self._filter_anomalous_items(candidates, request)

        # Rank candidates
        ranked_candidates = await self._rank_candidates(candidates, request, context)

        # Apply limit
        if len(ranked_candidates) > request.limit:
            ranked_candidates = ranked_candidates[: request.limit]

        # Generate explanations if requested
        if request.include_explanations:
            await self._generate_explanations(ranked_candidates, context)

        # Create recommendation set
        recommendation_set = RecommendationSet(
            items=ranked_candidates,
            user_id=request.user_id,
            session_id=request.session_id,
            entity_id=request.entity_id,
            entity_type=request.entity_type,
            context_ids=request.context_ids,
            metadata={
                "sources": (
                    [source.value for source in request.sources]
                    if request.sources
                    else ["all"]
                ),
                "generated_at": datetime.now().isoformat(),
            },
        )

        # Store in context manager if available
        if self.context_manager:
            await self.context_manager.create_recommendation_context(
                user_id=request.user_id,
                recommendations=[item.dict() for item in ranked_candidates],
                session_id=request.session_id,
                metadata={
                    "entity_id": request.entity_id,
                    "entity_type": request.entity_type,
                },
            )

        return recommendation_set

    async def register_item(
        self,
        item_id: str,
        item_type: str,
        title: str,
        description: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Register an item for recommendation.

        Args:
            item_id: Unique ID of the item
            item_type: Type of the item
            title: Title of the item
            description: Description of the item
            metadata: Additional metadata for the item

        Returns:
            True if registration was successful
        """
        if not self.initialized:
            await self.initialize()

        # Create item data
        item_data = {
            "item_id": item_id,
            "item_type": item_type,
            "title": title,
            "description": description,
            "metadata": metadata or {},
            "created_at": datetime.now(),
        }

        # Compute embedding for item
        if self.embedding_service:
            text_to_embed = f"{title} {description}"
            embedding = await self.embedding_service.embed_text(text_to_embed)
            item_data["embedding"] = embedding.tolist()

        # Register in active items
        self.active_items[f"{item_type}:{item_id}"] = item_data

        # Store in database if available
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO recommendation_items
                        (item_id, item_type, title, description, metadata, embedding, created_at)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                        ON CONFLICT (item_id, item_type) DO UPDATE SET
                        title = EXCLUDED.title,
                        description = EXCLUDED.description,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding
                    """,
                        item_id,
                        item_type,
                        title,
                        description,
                        json.dumps(metadata) if metadata else None,
                        item_data.get("embedding"),
                        item_data["created_at"],
                    )

                    return True

            except Exception as e:
                self.logger.error(f"Failed to register item in database: {e}")
                return False

        return True

    async def record_interaction(
        self,
        user_id: str,
        item_id: str,
        item_type: str,
        interaction_type: str,
        context_id: str | None = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Record a user interaction with an item.

        Args:
            user_id: User ID
            item_id: Item ID
            item_type: Item type
            interaction_type: Type of interaction (e.g., view, click, purchase)
            context_id: Optional context ID for the interaction
            metadata: Additional metadata for the interaction

        Returns:
            True if recording was successful
        """
        if not self.initialized:
            await self.initialize()

        # Prepare interaction data
        timestamp = datetime.now()
        interaction_data = {
            "user_id": user_id,
            "item_id": item_id,
            "item_type": item_type,
            "interaction_type": interaction_type,
            "timestamp": timestamp,
            "context_id": context_id,
            "metadata": metadata or {},
        }

        # Store in database if available
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        """
                        INSERT INTO recommendation_interactions
                        (user_id, item_id, item_type, interaction_type, timestamp, context_id, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                        user_id,
                        item_id,
                        item_type,
                        interaction_type,
                        timestamp,
                        context_id,
                        json.dumps(metadata) if metadata else None,
                    )

                    return True

            except Exception as e:
                self.logger.error(f"Failed to record interaction in database: {e}")
                return False

        return True

    async def get_similar_items(
        self, item_id: str, item_type: str, limit: int = 10, min_similarity: float = 0.7
    ) -> list[Tuple[Dict[str, Any], float]]:
        """
        Get items similar to a specified item.

        Args:
            item_id: ID of the item to find similar items for
            item_type: Type of the item
            limit: Maximum number of similar items to return
            min_similarity: Minimum similarity score

        Returns:
            List of (item, similarity) tuples
        """
        if not self.initialized:
            await self.initialize()

        # Find item embedding
        item_key = f"{item_type}:{item_id}"
        item_embedding = None

        # Check active items first
        if item_key in self.active_items and "embedding" in self.active_items[item_key]:
            item_embedding = self.active_items[item_key]["embedding"]

        # Check database if not found
        if not item_embedding and self.pool:
            try:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(
                        """
                        SELECT embedding
                        FROM recommendation_items
                        WHERE item_id = $1 AND item_type = $2
                    """,
                        item_id,
                        item_type,
                    )

                    if row and row["embedding"]:
                        item_embedding = row["embedding"]

            except Exception as e:
                self.logger.error(f"Failed to get item embedding from database: {e}")

        # If embedding still not found, return empty list
        if not item_embedding:
            return []

        # Find similar items
        similar_items = []

        # Check database if available
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    # Convert embedding to database format
                    embedding_str = f"[{','.join(map(str, item_embedding))}]"

                    rows = await conn.fetch(
                        """
                        SELECT 
                            item_id,
                            item_type,
                            title,
                            description,
                            metadata,
                            embedding,
                            created_at,
                            1 - (embedding <-> $1::vector) as similarity
                        FROM recommendation_items
                        WHERE embedding IS NOT NULL
                        AND (item_id != $2 OR item_type != $3)
                        AND 1 - (embedding <-> $1::vector) >= $4
                        ORDER BY similarity DESC
                        LIMIT $5
                    """,
                        embedding_str,
                        item_id,
                        item_type,
                        min_similarity,
                        limit,
                    )

                    for row in rows:
                        item = {
                            "item_id": row["item_id"],
                            "item_type": row["item_type"],
                            "title": row["title"],
                            "description": row["description"],
                            "metadata": (
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            "embedding": row["embedding"],
                            "created_at": row["created_at"],
                        }
                        similarity = row["similarity"]
                        similar_items.append((item, similarity))

            except Exception as e:
                self.logger.error(f"Failed to get similar items from database: {e}")

        # Add items from active registry if not enough results
        if len(similar_items) < limit and self.embedding_service:
            for key, item in self.active_items.items():
                # Skip the input item and items without embeddings
                if key == item_key or "embedding" not in item:
                    continue

                # Skip items already in results
                if any(
                    result[0]["item_id"] == item["item_id"]
                    and result[0]["item_type"] == item["item_type"]
                    for result in similar_items
                ):
                    continue

                # Compute similarity
                similarity = self.embedding_service.compute_similarity(
                    item_embedding, item["embedding"]
                )

                # Add if meets minimum threshold
                if similarity >= min_similarity:
                    similar_items.append((item, similarity))

            # Sort by similarity
            similar_items.sort(key=lambda x: x[1], reverse=True)

            # Apply limit
            if len(similar_items) > limit:
                similar_items = similar_items[:limit]

        return similar_items

    async def _collect_context(self, request: RecommendationRequest) -> Dict[str, Any]:
        """
        Collect context for a recommendation request.

        Args:
            request: The recommendation request

        Returns:
            Dictionary of context information
        """
        context = {
            "user_context": [],
            "session_context": [],
            "entity_context": [],
            "specific_context": [],
            "embeddings": {},
        }

        # Skip if no context manager
        if not self.context_manager:
            return context

        # Collect user context
        if request.user_id:
            user_context = await self.context_manager.get_user_context(
                user_id=request.user_id, limit=20
            )
            context["user_context"] = user_context

        # Collect session context
        if request.session_id:
            session_context = await self.context_manager.get_session_context(
                session_id=request.session_id, limit=10
            )
            context["session_context"] = session_context

        # Collect entity context
        if request.entity_id:
            entity_context = await self.context_manager.get_entity_context(
                entity_id=request.entity_id, entity_type=request.entity_type, limit=10
            )
            context["entity_context"] = entity_context

        # Collect specific context from IDs
        if request.context_ids:
            for context_id in request.context_ids:
                item = await self.context_manager.get_context(context_id)
                if item:
                    context["specific_context"].append(item)

        # Compute embeddings for relevant context items
        if self.embedding_service:
            # Collect all text items from context
            text_items = []

            for item in (
                context["user_context"]
                + context["session_context"]
                + context["entity_context"]
                + context["specific_context"]
            ):

                if isinstance(item.value, str):
                    text_items.append((item.id, item.value))
                elif item.type == ContextType.QUERY:
                    text_items.append((item.id, str(item.value)))

            # Compute embeddings in batch
            if text_items:
                texts = [text for _, text in text_items]
                embeddings = await self.embedding_service.embed_batch(texts)

                # Store embeddings
                for i, (item_id, _) in enumerate(text_items):
                    context["embeddings"][item_id] = embeddings[i]

        return context

    async def _generate_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate candidate recommendations.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of candidate recommendation items
        """
        candidates = []
        candidate_ids = set()

        # Define sources to use
        sources = (
            request.sources
            if request.sources
            else [
                RecommendationSource.BEHAVIOR,
                RecommendationSource.SIMILARITY,
                RecommendationSource.POPULARITY,
                RecommendationSource.COMPLEMENTARY,
            ]
        )

        # Generate candidates from each source
        if RecommendationSource.BEHAVIOR in sources and request.user_id:
            behavior_candidates = await self._generate_behavior_candidates(
                request, context
            )
            for candidate in behavior_candidates:
                if (candidate.item_id, candidate.item_type) not in candidate_ids:
                    candidate_ids.add((candidate.item_id, candidate.item_type))
                    candidates.append(candidate)

        if RecommendationSource.SIMILARITY in sources:
            similarity_candidates = await self._generate_similarity_candidates(
                request, context
            )
            for candidate in similarity_candidates:
                if (candidate.item_id, candidate.item_type) not in candidate_ids:
                    candidate_ids.add((candidate.item_id, candidate.item_type))
                    candidates.append(candidate)

        if RecommendationSource.POPULARITY in sources:
            popularity_candidates = await self._generate_popularity_candidates(
                request, context
            )
            for candidate in popularity_candidates:
                if (candidate.item_id, candidate.item_type) not in candidate_ids:
                    candidate_ids.add((candidate.item_id, candidate.item_type))
                    candidates.append(candidate)

        if RecommendationSource.COMPLEMENTARY in sources:
            complementary_candidates = await self._generate_complementary_candidates(
                request, context
            )
            for candidate in complementary_candidates:
                if (candidate.item_id, candidate.item_type) not in candidate_ids:
                    candidate_ids.add((candidate.item_id, candidate.item_type))
                    candidates.append(candidate)

        if RecommendationSource.EXPERT in sources:
            expert_candidates = await self._generate_expert_candidates(request, context)
            for candidate in expert_candidates:
                if (candidate.item_id, candidate.item_type) not in candidate_ids:
                    candidate_ids.add((candidate.item_id, candidate.item_type))
                    candidates.append(candidate)

        # Filter by minimum strength if requested
        if request.min_strength:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.strength.value >= request.min_strength.value
            ]

        # Filter by maximum priority if requested
        if request.max_priority:
            candidates = [
                candidate
                for candidate in candidates
                if candidate.priority.value <= request.max_priority.value
            ]

        return candidates

    async def _generate_behavior_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate recommendations based on user behavior.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of recommendation candidates
        """
        candidates = []

        if not request.user_id or not self.pool:
            return candidates

        try:
            async with self.pool.acquire() as conn:
                # Get items the user has interacted with
                rows = await conn.fetch(
                    """
                    SELECT 
                        ri.item_id,
                        ri.item_type,
                        ri.interaction_type,
                        COUNT(*) as interaction_count,
                        MAX(ri.timestamp) as last_interaction
                    FROM recommendation_interactions ri
                    WHERE ri.user_id = $1
                    GROUP BY ri.item_id, ri.item_type, ri.interaction_type
                    ORDER BY last_interaction DESC
                    LIMIT 100
                """,
                    request.user_id,
                )

                # Get recommendations from similar users
                similar_items_rows = await conn.fetch(
                    """
                    SELECT 
                        ri.item_id,
                        ri.item_type,
                        COUNT(DISTINCT ri.user_id) as user_count
                    FROM recommendation_interactions ri
                    WHERE ri.user_id IN (
                        SELECT DISTINCT ri2.user_id
                        FROM recommendation_interactions ri2
                        WHERE ri2.user_id != $1
                        AND (ri2.item_id, ri2.item_type) IN (
                            SELECT ri3.item_id, ri3.item_type
                            FROM recommendation_interactions ri3
                            WHERE ri3.user_id = $1
                        )
                        LIMIT 50
                    )
                    AND (ri.item_id, ri.item_type) NOT IN (
                        SELECT ri4.item_id, ri4.item_type
                        FROM recommendation_interactions ri4
                        WHERE ri4.user_id = $1
                    )
                    GROUP BY ri.item_id, ri.item_type
                    ORDER BY user_count DESC
                    LIMIT 20
                """,
                    request.user_id,
                )

                # Get item details
                for row in similar_items_rows:
                    item_row = await conn.fetchrow(
                        """
                        SELECT 
                            item_id,
                            item_type,
                            title,
                            description,
                            metadata,
                            embedding
                        FROM recommendation_items
                        WHERE item_id = $1 AND item_type = $2
                    """,
                        row["item_id"],
                        row["item_type"],
                    )

                    if item_row:
                        # Create recommendation item
                        item = RecommendationItem(
                            item_id=item_row["item_id"],
                            item_type=item_row["item_type"],
                            title=item_row["title"],
                            description=item_row["description"],
                            strength=RecommendationStrength.MEDIUM,
                            priority=RecommendationPriority.MEDIUM,
                            metadata=(
                                json.loads(item_row["metadata"])
                                if item_row["metadata"]
                                else {}
                            ),
                            embedding=item_row["embedding"],
                            reasons=[
                                RecommendationReason(
                                    source=RecommendationSource.BEHAVIOR,
                                    explanation=f"Popular among users with similar interests",
                                    confidence=min(
                                        0.6 + (row["user_count"] / 20.0), 0.95
                                    ),
                                )
                            ],
                        )

                        candidates.append(item)

        except Exception as e:
            self.logger.error(f"Failed to generate behavior recommendations: {e}")

        return candidates

    async def _generate_similarity_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate recommendations based on semantic similarity.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of recommendation candidates
        """
        candidates = []

        # Need embedding service for similarity recommendations
        if not self.embedding_service:
            return candidates

        # Get embeddings for context
        context_embeddings = context.get("embeddings", {})
        if not context_embeddings and not context["specific_context"]:
            return candidates

        # Get most relevant context embeddings
        query_embeddings = []
        for item in context["specific_context"]:
            if item.id in context_embeddings:
                query_embeddings.append(context_embeddings[item.id])
            elif item.embedding:
                query_embeddings.append(np.array(item.embedding))

        # If no specific context, use recent search and content
        if not query_embeddings:
            for item in context["user_context"] + context["session_context"]:
                if (
                    item.type == ContextType.QUERY
                    or item.source == ContextSource.SEARCH
                    or item.source == ContextSource.CONTENT_GENERATION
                ):
                    if item.id in context_embeddings:
                        query_embeddings.append(context_embeddings[item.id])
                        if len(query_embeddings) >= 3:
                            break

        # If still no embeddings, can't do similarity recommendations
        if not query_embeddings:
            return candidates

        # Compute average embedding
        if len(query_embeddings) > 1:
            avg_embedding = np.mean(query_embeddings, axis=0)
            # Normalize
            norm = np.linalg.norm(avg_embedding)
            if norm > 0:
                avg_embedding = avg_embedding / norm
        else:
            avg_embedding = query_embeddings[0]

        # Query database for similar items
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    # Convert embedding to database format
                    embedding_str = f"[{','.join(map(str, avg_embedding))}]"

                    rows = await conn.fetch(
                        """
                        SELECT 
                            item_id,
                            item_type,
                            title,
                            description,
                            metadata,
                            embedding,
                            1 - (embedding <-> $1::vector) as similarity
                        FROM recommendation_items
                        WHERE embedding IS NOT NULL
                        AND 1 - (embedding <-> $1::vector) >= 0.7
                        ORDER BY similarity DESC
                        LIMIT 20
                    """,
                        embedding_str,
                    )

                    for row in rows:
                        item = RecommendationItem(
                            item_id=row["item_id"],
                            item_type=row["item_type"],
                            title=row["title"],
                            description=row["description"],
                            strength=RecommendationStrength.MEDIUM,
                            similarity_score=row["similarity"],
                            metadata=(
                                json.loads(row["metadata"]) if row["metadata"] else {}
                            ),
                            embedding=row["embedding"],
                            reasons=[
                                RecommendationReason(
                                    source=RecommendationSource.SIMILARITY,
                                    explanation=f"Similar to your recent interests",
                                    confidence=row["similarity"],
                                )
                            ],
                        )

                        # Adjust strength based on similarity
                        if row["similarity"] > 0.9:
                            item.strength = RecommendationStrength.STRONG
                        elif row["similarity"] < 0.8:
                            item.strength = RecommendationStrength.WEAK

                        candidates.append(item)

            except Exception as e:
                self.logger.error(f"Failed to generate similarity recommendations: {e}")

        return candidates

    async def _generate_popularity_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate recommendations based on overall popularity.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of recommendation candidates
        """
        candidates = []

        if not self.pool:
            return candidates

        try:
            async with self.pool.acquire() as conn:
                # Get most popular items
                rows = await conn.fetch(
                    """
                    SELECT 
                        ri.item_id,
                        ri.item_type,
                        COUNT(DISTINCT ri.user_id) as user_count
                    FROM recommendation_interactions ri
                    GROUP BY ri.item_id, ri.item_type
                    ORDER BY user_count DESC
                    LIMIT 10
                """
                )

                # Get item details and create recommendations
                for row in rows:
                    item_row = await conn.fetchrow(
                        """
                        SELECT 
                            item_id,
                            item_type,
                            title,
                            description,
                            metadata,
                            embedding
                        FROM recommendation_items
                        WHERE item_id = $1 AND item_type = $2
                    """,
                        row["item_id"],
                        row["item_type"],
                    )

                    if item_row:
                        # Create recommendation item
                        item = RecommendationItem(
                            item_id=item_row["item_id"],
                            item_type=item_row["item_type"],
                            title=item_row["title"],
                            description=item_row["description"],
                            strength=RecommendationStrength.MEDIUM,
                            priority=RecommendationPriority.LOW,  # Lower priority for generic popularity
                            metadata=(
                                json.loads(item_row["metadata"])
                                if item_row["metadata"]
                                else {}
                            ),
                            embedding=item_row["embedding"],
                            reasons=[
                                RecommendationReason(
                                    source=RecommendationSource.POPULARITY,
                                    explanation=f"Popular among many users",
                                    confidence=min(
                                        0.5 + (row["user_count"] / 100.0), 0.9
                                    ),
                                )
                            ],
                        )

                        candidates.append(item)

        except Exception as e:
            self.logger.error(f"Failed to generate popularity recommendations: {e}")

        return candidates

    async def _generate_complementary_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate recommendations that complement recent interactions.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of recommendation candidates
        """
        candidates = []

        # Find recent item interactions from context
        recent_items = set()
        for context_list in [
            context["specific_context"],
            context["session_context"],
            context["user_context"],
        ]:
            for item in context_list:
                if item.entity_id and item.entity_type:
                    recent_items.add((item.entity_id, item.entity_type))
                    if len(recent_items) >= 5:
                        break
            if len(recent_items) >= 5:
                break

        # For each recent item, find complementary items
        for item_id, item_type in recent_items:
            similar_items = await self.get_similar_items(
                item_id=item_id, item_type=item_type, limit=3, min_similarity=0.7
            )

            for similar_item, similarity in similar_items:
                # Create recommendation item
                recommendation = RecommendationItem(
                    item_id=similar_item["item_id"],
                    item_type=similar_item["item_type"],
                    title=similar_item["title"],
                    description=similar_item["description"],
                    strength=RecommendationStrength.MEDIUM,
                    priority=RecommendationPriority.MEDIUM,
                    similarity_score=similarity,
                    metadata=similar_item.get("metadata", {}),
                    embedding=similar_item.get("embedding"),
                    reasons=[
                        RecommendationReason(
                            source=RecommendationSource.COMPLEMENTARY,
                            explanation=f"Complements {item_type} '{item_id}'",
                            confidence=similarity,
                            supporting_items=[f"{item_type}:{item_id}"],
                        )
                    ],
                )

                candidates.append(recommendation)

        return candidates

    async def _generate_expert_candidates(
        self, request: RecommendationRequest, context: Dict[str, Any]
    ) -> list[RecommendationItem]:
        """
        Generate expert recommendations using content generation.

        Args:
            request: The recommendation request
            context: Context information

        Returns:
            List of recommendation candidates
        """
        # Skip if no content generation service
        if not self.content_generation_service:
            return []

        candidates = []

        # Build context for expert recommendations
        context_text = ""

        # Add user information
        if request.user_id:
            context_text += f"User ID: {request.user_id}\n"

        # Add recent interactions
        context_text += "Recent interactions:\n"
        for context_list in [
            context["specific_context"],
            context["session_context"],
            context["user_context"],
        ]:
            for item in context_list:
                if (
                    item.source == ContextSource.SEARCH
                    and item.type == ContextType.QUERY
                ):
                    context_text += f"- Search: {item.value}\n"
                elif item.source == ContextSource.CONTENT_GENERATION:
                    context_text += f"- Generated content about: {item.key}\n"
                elif item.entity_id and item.entity_type:
                    context_text += (
                        f"- Interaction with {item.entity_type}: {item.entity_id}\n"
                    )

        # Generate expert recommendations
        try:
            # Use RAG service if available
            if self.rag_service:
                prompt = await self.rag_service.enrich_rag_prompt(
                    prompt=f"""Based on the user's recent interactions, suggest 3 recommendations. 
                    For each recommendation, provide:
                    1. A unique item_id
                    2. An item_type
                    3. A title
                    4. A brief description
                    5. A reason for the recommendation
                    
                    Format your response as a JSON array of objects, each with fields:
                    item_id, item_type, title, description, reason
                    
                    User context:
                    {context_text}
                    """,
                    user_id=request.user_id,
                    session_id=request.session_id,
                    entity_id=request.entity_id,
                    entity_type=request.entity_type,
                )
            else:
                prompt = f"""Based on the user's recent interactions, suggest 3 recommendations. 
                For each recommendation, provide:
                1. A unique item_id
                2. An item_type
                3. A title
                4. A brief description
                5. A reason for the recommendation
                
                Format your response as a JSON array of objects, each with fields:
                item_id, item_type, title, description, reason
                
                User context:
                {context_text}
                """

            # Generate recommendations
            response = await self.content_generation_service.generate_content(prompt)

            # Parse response
            try:
                # Extract JSON from response
                import re

                json_match = re.search(r"\[\s*\{.*\}\s*\]", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    expert_recommendations = json.loads(json_str)
                else:
                    expert_recommendations = json.loads(response)

                # Create recommendation items
                for rec in expert_recommendations:
                    item = RecommendationItem(
                        item_id=rec["item_id"],
                        item_type=rec["item_type"],
                        title=rec["title"],
                        description=rec["description"],
                        strength=RecommendationStrength.MEDIUM,
                        priority=RecommendationPriority.MEDIUM,
                        reasons=[
                            RecommendationReason(
                                source=RecommendationSource.EXPERT,
                                explanation=rec["reason"],
                                confidence=0.8,
                            )
                        ],
                        metadata={"generated": True, "expert_recommendation": True},
                    )

                    candidates.append(item)

            except Exception as e:
                self.logger.error(
                    f"Failed to parse expert recommendations: {e}\nResponse: {response}"
                )

        except Exception as e:
            self.logger.error(f"Failed to generate expert recommendations: {e}")

        return candidates

    async def _filter_anomalous_items(
        self, candidates: list[RecommendationItem], request: RecommendationRequest
    ) -> list[RecommendationItem]:
        """
        Filter out potentially anomalous recommendations.

        Args:
            candidates: Candidate recommendations
            request: The recommendation request

        Returns:
            Filtered list of recommendations
        """
        if not self.anomaly_detection_service or not candidates:
            return candidates

        try:
            # Prepare data for anomaly detection
            data = {
                "items": [
                    {
                        "item_id": item.item_id,
                        "item_type": item.item_type,
                        "title": item.title,
                        "description": item.description,
                        "strength": item.strength.value,
                        "priority": item.priority.value,
                        "metadata": item.metadata,
                        "similarity_score": item.similarity_score,
                        "source": (
                            item.reasons[0].source.value if item.reasons else "unknown"
                        ),
                    }
                    for item in candidates
                ],
                "request": {
                    "user_id": request.user_id,
                    "session_id": request.session_id,
                    "entity_id": request.entity_id,
                    "entity_type": request.entity_type,
                },
            }

            # Process with anomaly detection
            results = await self.anomaly_detection_service.process_data(
                user_id=request.user_id,
                session_id=request.session_id,
                data_type="recommendations",
                data=data,
            )

            # Check for anomalies
            if not results.get("anomalies"):
                return candidates

            # Extract anomalous item IDs
            anomalous_items = set()
            for anomaly in results["anomalies"]:
                if "item_id" in anomaly and "item_type" in anomaly:
                    anomalous_items.add((anomaly["item_id"], anomaly["item_type"]))

            # Filter out anomalous items
            filtered_candidates = [
                item
                for item in candidates
                if (item.item_id, item.item_type) not in anomalous_items
            ]

            # If everything was filtered, return some of the original candidates
            # but mark them as potentially anomalous
            if not filtered_candidates and candidates:
                for item in candidates[:5]:
                    item.metadata["potentially_anomalous"] = True
                    item.priority = RecommendationPriority.LOW
                    item.reasons.append(
                        RecommendationReason(
                            source=RecommendationSource.HYBRID,
                            explanation="Unusual recommendation pattern detected",
                            confidence=0.5,
                        )
                    )

                return candidates[:5]

            return filtered_candidates

        except Exception as e:
            self.logger.error(f"Error in anomaly filtering: {e}")
            return candidates

    async def _rank_candidates(
        self,
        candidates: list[RecommendationItem],
        request: RecommendationRequest,
        context: Dict[str, Any],
    ) -> list[RecommendationItem]:
        """
        Rank recommendation candidates by relevance.

        Args:
            candidates: Candidate recommendations
            request: The recommendation request
            context: Context information

        Returns:
            Ranked list of recommendations
        """
        if not candidates:
            return []

        # Calculate a score for each candidate
        for candidate in candidates:
            # Base score from strength
            if candidate.strength == RecommendationStrength.STRONG:
                base_score = 0.8
            elif candidate.strength == RecommendationStrength.MEDIUM:
                base_score = 0.5
            else:
                base_score = 0.3

            # Adjust by priority (higher priority means higher in ranking)
            priority_boost = (6 - candidate.priority.value) * 0.05

            # Adjust by similarity if available
            similarity_boost = (
                candidate.similarity_score * 0.3 if candidate.similarity_score else 0
            )

            # Adjust by source confidence
            confidence_boost = 0
            for reason in candidate.reasons:
                confidence_boost += reason.confidence * 0.2

            # Combine scores
            candidate.metadata["rank_score"] = (
                base_score + priority_boost + similarity_boost + confidence_boost
            )

        # Sort by rank score (descending)
        ranked_candidates = sorted(
            candidates, key=lambda x: x.metadata.get("rank_score", 0), reverse=True
        )

        return ranked_candidates

    async def _generate_explanations(
        self, candidates: list[RecommendationItem], context: Dict[str, Any]
    ) -> None:
        """
        Generate human-readable explanations for recommendations.

        Args:
            candidates: Recommendation candidates to explain
            context: Context information
        """
        if not self.content_generation_service or not candidates:
            return

        # Only generate explanations for top items
        top_candidates = candidates[:5]

        try:
            # Generate explanations in batch
            items_data = []
            for i, item in enumerate(top_candidates):
                item_data = {
                    "index": i,
                    "title": item.title,
                    "description": item.description,
                    "type": item.item_type,
                    "reasons": [r.explanation for r in item.reasons],
                }
                items_data.append(item_data)

            prompt = f"""Generate concise, personalized explanations for each of these recommendations. 
            Each explanation should be 1-2 sentences and highlight why this item is relevant.
            
            Recommendations:
            {json.dumps(items_data, indent=2)}
            
            Format your response as a JSON object with indexes as keys and explanations as values:
            {{
              "0": "Explanation for first item",
              "1": "Explanation for second item",
              ...
            }}
            """

            # Generate explanations
            response = await self.content_generation_service.generate_content(prompt)

            # Parse response
            try:
                import re

                json_match = re.search(r"\{.*\}", response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    explanations = json.loads(json_str)
                else:
                    explanations = json.loads(response)

                # Add explanations to items
                for i, item in enumerate(top_candidates):
                    if str(i) in explanations:
                        existing_explanations = [r.explanation for r in item.reasons]

                        # Only add if it's a new explanation
                        if explanations[str(i)] not in existing_explanations:
                            item.reasons.append(
                                RecommendationReason(
                                    source=RecommendationSource.HYBRID,
                                    explanation=explanations[str(i)],
                                    confidence=0.8,
                                )
                            )

            except Exception as e:
                self.logger.error(
                    f"Failed to parse explanations: {e}\nResponse: {response}"
                )

        except Exception as e:
            self.logger.error(f"Failed to generate explanations: {e}")
