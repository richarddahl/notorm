"""
Unified context management for AI features.

This module provides a central context repository and propagation system
for sharing context between different AI features such as semantic search,
recommendations, content generation, and anomaly detection.
"""

import asyncio
import datetime
import json
import logging
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union, cast

import numpy as np
import pandas as pd
from pydantic import BaseModel, Field, validator


class ContextSource(str, Enum):
    """Source of context information."""
    
    SEARCH = "search"
    RECOMMENDATION = "recommendation"
    CONTENT_GENERATION = "content_generation"
    ANOMALY_DETECTION = "anomaly_detection"
    USER_INTERACTION = "user_interaction"
    SYSTEM = "system"
    EXTERNAL = "external"


class ContextType(str, Enum):
    """Type of context information."""
    
    USER = "user"
    ENTITY = "entity"
    QUERY = "query"
    RESULT = "result"
    EVENT = "event"
    SESSION = "session"
    SYSTEM = "system"
    METRIC = "metric"
    ALERT = "alert"


class Relevance(str, Enum):
    """Relevance level of context to the current operation."""
    
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class ContextValidityPeriod(BaseModel):
    """Period for which context is valid."""
    
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    expires_at: Optional[datetime.datetime] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    
    @property
    def is_valid(self) -> bool:
        """Check if the context is still valid."""
        now = datetime.datetime.now()
        if self.expires_at and now > self.expires_at:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def use(self) -> None:
        """Mark the context as used once."""
        self.current_uses += 1


class ContextItem(BaseModel):
    """Single item of context information."""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: ContextSource
    type: ContextType
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    key: str
    value: Any
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance: Relevance = Relevance.UNKNOWN
    embedding: Optional[List[float]] = None
    validity: ContextValidityPeriod = Field(default_factory=ContextValidityPeriod)
    dependencies: List[str] = Field(default_factory=list)  # IDs of related context items
    
    @property
    def is_valid(self) -> bool:
        """Check if the context item is still valid."""
        return self.validity.is_valid
    
    def use(self) -> None:
        """Mark the context item as used once."""
        self.validity.use()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context item to dictionary."""
        result = {
            "id": self.id,
            "source": self.source.value,
            "type": self.type.value,
            "created_at": self.created_at.isoformat(),
            "key": self.key,
            "value": self.value,
            "relevance": self.relevance.value,
            "is_valid": self.is_valid,
        }
        
        # Add optional fields if they exist
        if self.entity_id:
            result["entity_id"] = self.entity_id
        if self.entity_type:
            result["entity_type"] = self.entity_type
        if self.user_id:
            result["user_id"] = self.user_id
        if self.session_id:
            result["session_id"] = self.session_id
        if self.metadata:
            result["metadata"] = self.metadata
        if self.dependencies:
            result["dependencies"] = self.dependencies
        
        return result


class ContextQuery(BaseModel):
    """Query for retrieving context items."""
    
    source: Optional[ContextSource] = None
    type: Optional[ContextType] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    key_pattern: Optional[str] = None
    min_relevance: Optional[Relevance] = None
    created_after: Optional[datetime.datetime] = None
    created_before: Optional[datetime.datetime] = None
    metadata_filters: Dict[str, Any] = Field(default_factory=dict)
    limit: int = 10
    valid_only: bool = True
    include_embeddings: bool = False


class ContextBatch(BaseModel):
    """Batch of context items."""
    
    items: List[ContextItem]
    batch_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class UnifiedContextManager:
    """
    Central context manager for AI features.
    
    This class provides a unified interface for storing, retrieving, and
    sharing context between different AI features, enabling more effective
    integration and enhanced capabilities.
    """
    
    def __init__(
        self,
        connection_string: Optional[str] = None,
        context_table: str = "ai_context",
        cache_size: int = 1000,
        default_ttl: int = 3600,  # seconds
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the unified context manager.
        
        Args:
            connection_string: Database connection for persistent storage
            context_table: Table name for storing context items
            cache_size: Maximum number of context items to keep in memory
            default_ttl: Default time-to-live for context items in seconds
            logger: Logger to use
        """
        self.connection_string = connection_string
        self.context_table = context_table
        self.cache_size = cache_size
        self.default_ttl = default_ttl
        self.logger = logger or logging.getLogger(__name__)
        
        # In-memory cache
        self.context_cache: Dict[str, ContextItem] = {}
        
        # Indexes for efficient retrieval
        self.entity_index: Dict[str, Set[str]] = {}  # entity_id -> context_ids
        self.user_index: Dict[str, Set[str]] = {}    # user_id -> context_ids
        self.session_index: Dict[str, Set[str]] = {} # session_id -> context_ids
        self.key_index: Dict[str, Set[str]] = {}     # key -> context_ids
        self.source_index: Dict[ContextSource, Set[str]] = {}  # source -> context_ids
        self.type_index: Dict[ContextType, Set[str]] = {}      # type -> context_ids
        
        # Database connection pool
        self.pool = None
        self.initialized = False
        
        # Context embedding service
        self.embedding_service = None
    
    async def initialize(self) -> None:
        """Initialize the context manager."""
        if self.initialized:
            return
        
        if self.connection_string:
            import asyncpg
            
            # Initialize database connection pool
            self.pool = await asyncpg.create_pool(self.connection_string)
            
            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                # Create context table
                await conn.execute(f"""
                    CREATE TABLE IF NOT EXISTS {self.context_table} (
                        id TEXT PRIMARY KEY,
                        source TEXT NOT NULL,
                        type TEXT NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE NOT NULL,
                        expires_at TIMESTAMP WITH TIME ZONE,
                        entity_id TEXT,
                        entity_type TEXT,
                        user_id TEXT,
                        session_id TEXT,
                        key TEXT NOT NULL,
                        value JSONB NOT NULL,
                        metadata JSONB,
                        relevance TEXT NOT NULL,
                        embedding VECTOR(384),
                        max_uses INTEGER,
                        current_uses INTEGER DEFAULT 0,
                        dependencies JSONB
                    )
                """)
                
                # Create indexes
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.context_table}_created_at 
                    ON {self.context_table}(created_at)
                """)
                
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.context_table}_entity_id 
                    ON {self.context_table}(entity_id) WHERE entity_id IS NOT NULL
                """)
                
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.context_table}_user_id 
                    ON {self.context_table}(user_id) WHERE user_id IS NOT NULL
                """)
                
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.context_table}_session_id 
                    ON {self.context_table}(session_id) WHERE session_id IS NOT NULL
                """)
                
                await conn.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.context_table}_key 
                    ON {self.context_table}(key)
                """)
                
                # Enable vector operations if embedding is used
                try:
                    await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    # Create vector index if not exists
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.context_table}_embedding 
                        ON {self.context_table} USING ivfflat (embedding vector_l2_ops)
                        WITH (lists = 100) WHERE embedding IS NOT NULL
                    """)
                except Exception:
                    self.logger.warning("Vector extension not available, embedding search will be disabled")
        
        # Try to initialize the embedding service for context items
        try:
            from uno.ai.integration.embeddings import SharedEmbeddingService
            self.embedding_service = SharedEmbeddingService()
            await self.embedding_service.initialize()
        except Exception as e:
            self.logger.warning(f"Could not initialize embedding service: {e}")
            self.embedding_service = None
        
        self.initialized = True
    
    async def close(self) -> None:
        """Close the context manager and release resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        
        if self.embedding_service:
            await self.embedding_service.close()
            self.embedding_service = None
        
        self.initialized = False
    
    async def store_context(self, item: ContextItem) -> str:
        """
        Store a context item.
        
        Args:
            item: The context item to store
            
        Returns:
            ID of the stored context item
        """
        if not self.initialized:
            await self.initialize()
        
        # Set expiration if not set
        if not item.validity.expires_at and self.default_ttl > 0:
            item.validity.expires_at = datetime.datetime.now() + datetime.timedelta(seconds=self.default_ttl)
        
        # Add embedding if possible
        if self.embedding_service and not item.embedding:
            try:
                context_text = self._create_context_text(item)
                if context_text:
                    embedding = await self.embedding_service.embed_text(context_text)
                    item.embedding = embedding.tolist()
            except Exception as e:
                self.logger.warning(f"Failed to create embedding for context item: {e}")
        
        # Store in memory cache
        self.context_cache[item.id] = item
        
        # Update indexes
        if item.entity_id:
            if item.entity_id not in self.entity_index:
                self.entity_index[item.entity_id] = set()
            self.entity_index[item.entity_id].add(item.id)
        
        if item.user_id:
            if item.user_id not in self.user_index:
                self.user_index[item.user_id] = set()
            self.user_index[item.user_id].add(item.id)
        
        if item.session_id:
            if item.session_id not in self.session_index:
                self.session_index[item.session_id] = set()
            self.session_index[item.session_id].add(item.id)
        
        if item.key:
            if item.key not in self.key_index:
                self.key_index[item.key] = set()
            self.key_index[item.key].add(item.id)
        
        if item.source:
            if item.source not in self.source_index:
                self.source_index[item.source] = set()
            self.source_index[item.source].add(item.id)
        
        if item.type:
            if item.type not in self.type_index:
                self.type_index[item.type] = set()
            self.type_index[item.type].add(item.id)
        
        # Prune cache if it exceeds size limit
        if len(self.context_cache) > self.cache_size:
            self._prune_cache()
        
        # Store in database if available
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute(f"""
                        INSERT INTO {self.context_table} (
                            id, source, type, created_at, expires_at, entity_id, entity_type,
                            user_id, session_id, key, value, metadata, relevance, embedding,
                            max_uses, current_uses, dependencies
                        ) VALUES (
                            $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17
                        )
                        ON CONFLICT (id) DO UPDATE SET
                            expires_at = $5,
                            value = $11,
                            metadata = $12,
                            relevance = $13,
                            embedding = $14,
                            max_uses = $15,
                            current_uses = $16,
                            dependencies = $17
                    """,
                    item.id,
                    item.source.value,
                    item.type.value,
                    item.created_at,
                    item.validity.expires_at,
                    item.entity_id,
                    item.entity_type,
                    item.user_id,
                    item.session_id,
                    item.key,
                    json.dumps(item.value),
                    json.dumps(item.metadata) if item.metadata else None,
                    item.relevance.value,
                    item.embedding,
                    item.validity.max_uses,
                    item.validity.current_uses,
                    json.dumps(item.dependencies) if item.dependencies else None
                    )
            except Exception as e:
                self.logger.error(f"Failed to store context item in database: {e}")
        
        return item.id
    
    async def store_context_batch(self, batch: ContextBatch) -> List[str]:
        """
        Store a batch of context items.
        
        Args:
            batch: The batch of context items to store
            
        Returns:
            List of IDs of the stored context items
        """
        if not self.initialized:
            await self.initialize()
        
        ids = []
        for item in batch.items:
            item_id = await self.store_context(item)
            ids.append(item_id)
        
        return ids
    
    async def get_context(
        self,
        context_id: str,
        mark_as_used: bool = True
    ) -> Optional[ContextItem]:
        """
        Get a context item by ID.
        
        Args:
            context_id: ID of the context item to retrieve
            mark_as_used: Whether to mark the item as used
            
        Returns:
            The context item if found and valid, None otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Check cache first
        if context_id in self.context_cache:
            item = self.context_cache[context_id]
            if item.is_valid:
                if mark_as_used:
                    item.use()
                return item
            else:
                # Remove invalid item from cache
                self._remove_from_cache(context_id)
                return None
        
        # If not in cache, check database
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    row = await conn.fetchrow(f"""
                        SELECT 
                            id, source, type, created_at, expires_at, entity_id, entity_type,
                            user_id, session_id, key, value, metadata, relevance, embedding,
                            max_uses, current_uses, dependencies
                        FROM {self.context_table}
                        WHERE id = $1
                    """, context_id)
                    
                    if not row:
                        return None
                    
                    # Create context item
                    item = self._row_to_context_item(row)
                    
                    # Check if valid
                    if not item.is_valid:
                        return None
                    
                    # Mark as used if requested
                    if mark_as_used:
                        item.use()
                        
                        # Update usage count in database
                        await conn.execute(f"""
                            UPDATE {self.context_table}
                            SET current_uses = current_uses + 1
                            WHERE id = $1
                        """, context_id)
                    
                    # Add to cache
                    self.context_cache[item.id] = item
                    self._update_indexes(item)
                    
                    return item
            
            except Exception as e:
                self.logger.error(f"Failed to retrieve context item from database: {e}")
        
        return None
    
    async def query_context(
        self,
        query: ContextQuery
    ) -> List[ContextItem]:
        """
        Query for context items.
        
        Args:
            query: The query to find matching context items
            
        Returns:
            List of matching context items
        """
        if not self.initialized:
            await self.initialize()
        
        results = []
        
        # First check cache
        cache_results = self._query_cache(query)
        results.extend(cache_results)
        
        # If we have database connection, check there too
        if self.pool and (not query.limit or len(results) < query.limit):
            db_results = await self._query_database(query, already_found=set(item.id for item in results))
            results.extend(db_results)
        
        # Apply limit
        if query.limit and len(results) > query.limit:
            results = results[:query.limit]
        
        return results
    
    async def query_by_embedding(
        self,
        embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Tuple[ContextItem, float]]:
        """
        Query for context items by embedding similarity.
        
        Args:
            embedding: The query embedding
            entity_type: Optional filter by entity type
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of (context item, similarity score) tuples
        """
        if not self.initialized:
            await self.initialize()
        
        if not self.pool:
            self.logger.warning("Database connection required for embedding search")
            return []
        
        try:
            async with self.pool.acquire() as conn:
                # Convert embedding to database format
                embedding_str = f"[{','.join(map(str, embedding))}]"
                
                # Prepare query
                query = f"""
                    SELECT 
                        id, source, type, created_at, expires_at, entity_id, entity_type,
                        user_id, session_id, key, value, metadata, relevance, embedding,
                        max_uses, current_uses, dependencies,
                        1 - (embedding <-> $1::vector) as similarity
                    FROM {self.context_table}
                    WHERE embedding IS NOT NULL
                    AND (expires_at IS NULL OR expires_at > NOW())
                    AND (max_uses IS NULL OR current_uses < max_uses)
                    AND 1 - (embedding <-> $1::vector) >= $2
                """
                
                params = [embedding_str, similarity_threshold]
                
                if entity_type:
                    query += " AND entity_type = $3"
                    params.append(entity_type)
                
                query += f" ORDER BY similarity DESC LIMIT {limit}"
                
                rows = await conn.fetch(query, *params)
                
                results = []
                for row in rows:
                    item = self._row_to_context_item(row)
                    similarity = row["similarity"]
                    
                    # Add to cache
                    self.context_cache[item.id] = item
                    self._update_indexes(item)
                    
                    results.append((item, similarity))
                
                return results
        
        except Exception as e:
            self.logger.error(f"Failed to query context by embedding: {e}")
            return []
    
    async def update_context_relevance(
        self,
        context_id: str,
        relevance: Relevance
    ) -> bool:
        """
        Update the relevance of a context item.
        
        Args:
            context_id: ID of the context item to update
            relevance: New relevance value
            
        Returns:
            True if the update was successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Update in cache
        if context_id in self.context_cache:
            self.context_cache[context_id].relevance = relevance
        
        # Update in database
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    result = await conn.execute(f"""
                        UPDATE {self.context_table}
                        SET relevance = $1
                        WHERE id = $2
                    """, relevance.value, context_id)
                    
                    return result == "UPDATE 1"
            
            except Exception as e:
                self.logger.error(f"Failed to update context relevance: {e}")
                return False
        
        return True
    
    async def delete_context(self, context_id: str) -> bool:
        """
        Delete a context item.
        
        Args:
            context_id: ID of the context item to delete
            
        Returns:
            True if the deletion was successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()
        
        # Remove from cache
        self._remove_from_cache(context_id)
        
        # Remove from database
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    result = await conn.execute(f"""
                        DELETE FROM {self.context_table}
                        WHERE id = $1
                    """, context_id)
                    
                    return result == "DELETE 1"
            
            except Exception as e:
                self.logger.error(f"Failed to delete context from database: {e}")
                return False
        
        return True
    
    async def create_search_context(
        self,
        query: str,
        results: List[Dict[str, Any]],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextItem:
        """
        Create context from a search operation.
        
        Args:
            query: The search query
            results: The search results
            user_id: Optional user ID
            session_id: Optional session ID
            metadata: Optional additional metadata
            
        Returns:
            The created context item
        """
        # Create query context
        query_item = ContextItem(
            source=ContextSource.SEARCH,
            type=ContextType.QUERY,
            user_id=user_id,
            session_id=session_id,
            key="search_query",
            value=query,
            metadata=metadata or {},
            relevance=Relevance.HIGH
        )
        
        # Store query context
        await self.store_context(query_item)
        
        # Create results context
        results_item = ContextItem(
            source=ContextSource.SEARCH,
            type=ContextType.RESULT,
            user_id=user_id,
            session_id=session_id,
            key="search_results",
            value=results,
            metadata=metadata or {},
            relevance=Relevance.HIGH,
            dependencies=[query_item.id]
        )
        
        # Store results context
        await self.store_context(results_item)
        
        return results_item
    
    async def create_recommendation_context(
        self,
        user_id: str,
        recommendations: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextItem:
        """
        Create context from a recommendation operation.
        
        Args:
            user_id: The user ID
            recommendations: The recommended items
            session_id: Optional session ID
            metadata: Optional additional metadata
            
        Returns:
            The created context item
        """
        # Create recommendation context
        item = ContextItem(
            source=ContextSource.RECOMMENDATION,
            type=ContextType.RESULT,
            user_id=user_id,
            session_id=session_id,
            key="recommendations",
            value=recommendations,
            metadata=metadata or {},
            relevance=Relevance.HIGH
        )
        
        # Store context
        await self.store_context(item)
        
        return item
    
    async def create_content_generation_context(
        self,
        prompt: str,
        content: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        context_sources: Optional[List[str]] = None
    ) -> ContextItem:
        """
        Create context from a content generation operation.
        
        Args:
            prompt: The generation prompt
            content: The generated content
            user_id: Optional user ID
            session_id: Optional session ID
            metadata: Optional additional metadata
            context_sources: Optional list of context source IDs used for generation
            
        Returns:
            The created context item
        """
        # Create prompt context
        prompt_item = ContextItem(
            source=ContextSource.CONTENT_GENERATION,
            type=ContextType.QUERY,
            user_id=user_id,
            session_id=session_id,
            key="generation_prompt",
            value=prompt,
            metadata=metadata or {},
            relevance=Relevance.HIGH,
            dependencies=context_sources or []
        )
        
        # Store prompt context
        await self.store_context(prompt_item)
        
        # Create content context
        content_item = ContextItem(
            source=ContextSource.CONTENT_GENERATION,
            type=ContextType.RESULT,
            user_id=user_id,
            session_id=session_id,
            key="generated_content",
            value=content,
            metadata=metadata or {},
            relevance=Relevance.HIGH,
            dependencies=[prompt_item.id]
        )
        
        # Store content context
        await self.store_context(content_item)
        
        return content_item
    
    async def create_anomaly_context(
        self,
        alert: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContextItem:
        """
        Create context from an anomaly detection operation.
        
        Args:
            alert: The anomaly alert
            user_id: Optional user ID
            session_id: Optional session ID
            metadata: Optional additional metadata
            
        Returns:
            The created context item
        """
        # Create anomaly context
        item = ContextItem(
            source=ContextSource.ANOMALY_DETECTION,
            type=ContextType.ALERT,
            user_id=user_id,
            session_id=session_id,
            entity_id=alert.get("entity_id"),
            entity_type=alert.get("entity_type"),
            key=f"anomaly_{alert.get('anomaly_type', 'unknown')}",
            value=alert,
            metadata=metadata or {},
            relevance=Relevance.HIGH
        )
        
        # Store context
        await self.store_context(item)
        
        return item
    
    async def get_user_context(
        self,
        user_id: str,
        limit: int = 10,
        source: Optional[ContextSource] = None,
        include_expired: bool = False
    ) -> List[ContextItem]:
        """
        Get context items for a user.
        
        Args:
            user_id: The user ID
            limit: Maximum number of items to return
            source: Optional filter by source
            include_expired: Whether to include expired items
            
        Returns:
            List of context items
        """
        query = ContextQuery(
            user_id=user_id,
            limit=limit,
            source=source,
            valid_only=not include_expired
        )
        
        return await self.query_context(query)
    
    async def get_session_context(
        self,
        session_id: str,
        limit: int = 10,
        source: Optional[ContextSource] = None,
        include_expired: bool = False
    ) -> List[ContextItem]:
        """
        Get context items for a session.
        
        Args:
            session_id: The session ID
            limit: Maximum number of items to return
            source: Optional filter by source
            include_expired: Whether to include expired items
            
        Returns:
            List of context items
        """
        query = ContextQuery(
            session_id=session_id,
            limit=limit,
            source=source,
            valid_only=not include_expired
        )
        
        return await self.query_context(query)
    
    async def get_entity_context(
        self,
        entity_id: str,
        entity_type: Optional[str] = None,
        limit: int = 10,
        source: Optional[ContextSource] = None,
        include_expired: bool = False
    ) -> List[ContextItem]:
        """
        Get context items for an entity.
        
        Args:
            entity_id: The entity ID
            entity_type: Optional entity type
            limit: Maximum number of items to return
            source: Optional filter by source
            include_expired: Whether to include expired items
            
        Returns:
            List of context items
        """
        query = ContextQuery(
            entity_id=entity_id,
            entity_type=entity_type,
            limit=limit,
            source=source,
            valid_only=not include_expired
        )
        
        return await self.query_context(query)
    
    def _query_cache(self, query: ContextQuery) -> List[ContextItem]:
        """
        Query the in-memory cache for context items.
        
        Args:
            query: The query parameters
            
        Returns:
            List of matching context items from cache
        """
        # Find candidate IDs using indexes for faster filtering
        candidate_ids = set()
        
        # Use the most specific index first
        if query.entity_id and query.entity_id in self.entity_index:
            candidate_ids = self.entity_index[query.entity_id].copy()
        elif query.user_id and query.user_id in self.user_index:
            candidate_ids = self.user_index[query.user_id].copy()
        elif query.session_id and query.session_id in self.session_index:
            candidate_ids = self.session_index[query.session_id].copy()
        elif query.source and query.source in self.source_index:
            candidate_ids = self.source_index[query.source].copy()
        elif query.type and query.type in self.type_index:
            candidate_ids = self.type_index[query.type].copy()
        elif query.key_pattern and query.key_pattern in self.key_index:
            candidate_ids = self.key_index[query.key_pattern].copy()
        else:
            # If no specific index matches, use all cached items
            candidate_ids = set(self.context_cache.keys())
        
        # Apply filters to candidates
        results = []
        for context_id in candidate_ids:
            if context_id not in self.context_cache:
                continue
            
            item = self.context_cache[context_id]
            
            # Skip invalid items if requested
            if query.valid_only and not item.is_valid:
                continue
            
            # Apply entity filter
            if query.entity_id and item.entity_id != query.entity_id:
                continue
            
            # Apply entity type filter
            if query.entity_type and item.entity_type != query.entity_type:
                continue
            
            # Apply user filter
            if query.user_id and item.user_id != query.user_id:
                continue
            
            # Apply session filter
            if query.session_id and item.session_id != query.session_id:
                continue
            
            # Apply source filter
            if query.source and item.source != query.source:
                continue
            
            # Apply type filter
            if query.type and item.type != query.type:
                continue
            
            # Apply key pattern filter
            if query.key_pattern and query.key_pattern not in item.key:
                continue
            
            # Apply relevance filter
            if query.min_relevance and item.relevance.value < query.min_relevance.value:
                continue
            
            # Apply created_after filter
            if query.created_after and item.created_at < query.created_after:
                continue
            
            # Apply created_before filter
            if query.created_before and item.created_at > query.created_before:
                continue
            
            # Apply metadata filters
            if query.metadata_filters:
                skip = False
                for key, value in query.metadata_filters.items():
                    if key not in item.metadata or item.metadata[key] != value:
                        skip = True
                        break
                if skip:
                    continue
            
            # Check if embeddings should be included
            if not query.include_embeddings:
                item_copy = item.copy()
                item_copy.embedding = None
                results.append(item_copy)
            else:
                results.append(item)
        
        # Sort by creation time (newest first)
        results.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply limit
        if query.limit and len(results) > query.limit:
            results = results[:query.limit]
        
        return results
    
    async def _query_database(
        self,
        query: ContextQuery,
        already_found: Set[str] = None
    ) -> List[ContextItem]:
        """
        Query the database for context items.
        
        Args:
            query: The query parameters
            already_found: Set of context IDs already found in cache
            
        Returns:
            List of matching context items from database
        """
        if not self.pool:
            return []
        
        already_found = already_found or set()
        
        try:
            async with self.pool.acquire() as conn:
                # Build SQL query
                sql = f"""
                    SELECT 
                        id, source, type, created_at, expires_at, entity_id, entity_type,
                        user_id, session_id, key, value, metadata, relevance, 
                        {'' if query.include_embeddings else 'NULL AS'} embedding,
                        max_uses, current_uses, dependencies
                    FROM {self.context_table}
                    WHERE id NOT IN ({','.join('$' + str(i+1) for i in range(len(already_found)))})
                """
                
                params = list(already_found)
                param_idx = len(params) + 1
                
                # Add filters
                where_clauses = []
                
                if query.valid_only:
                    where_clauses.append(f"(expires_at IS NULL OR expires_at > NOW())")
                    where_clauses.append(f"(max_uses IS NULL OR current_uses < max_uses)")
                
                if query.entity_id:
                    where_clauses.append(f"entity_id = ${param_idx}")
                    params.append(query.entity_id)
                    param_idx += 1
                
                if query.entity_type:
                    where_clauses.append(f"entity_type = ${param_idx}")
                    params.append(query.entity_type)
                    param_idx += 1
                
                if query.user_id:
                    where_clauses.append(f"user_id = ${param_idx}")
                    params.append(query.user_id)
                    param_idx += 1
                
                if query.session_id:
                    where_clauses.append(f"session_id = ${param_idx}")
                    params.append(query.session_id)
                    param_idx += 1
                
                if query.source:
                    where_clauses.append(f"source = ${param_idx}")
                    params.append(query.source.value)
                    param_idx += 1
                
                if query.type:
                    where_clauses.append(f"type = ${param_idx}")
                    params.append(query.type.value)
                    param_idx += 1
                
                if query.key_pattern:
                    where_clauses.append(f"key LIKE ${param_idx}")
                    params.append(f"%{query.key_pattern}%")
                    param_idx += 1
                
                if query.min_relevance:
                    where_clauses.append(f"relevance IN ({','.join(['$' + str(param_idx + i) for i in range(len(relevance_values))])})")
                    relevance_values = [r.value for r in Relevance if r.value >= query.min_relevance.value]
                    params.extend(relevance_values)
                    param_idx += len(relevance_values)
                
                if query.created_after:
                    where_clauses.append(f"created_at >= ${param_idx}")
                    params.append(query.created_after)
                    param_idx += 1
                
                if query.created_before:
                    where_clauses.append(f"created_at <= ${param_idx}")
                    params.append(query.created_before)
                    param_idx += 1
                
                # Add metadata filters
                for key, value in query.metadata_filters.items():
                    where_clauses.append(f"metadata->>'${param_idx}' = ${param_idx + 1}")
                    params.append(key)
                    params.append(str(value))
                    param_idx += 2
                
                # Add where clauses to SQL
                if where_clauses:
                    sql += " AND " + " AND ".join(where_clauses)
                
                # Add order by and limit
                sql += " ORDER BY created_at DESC"
                
                if query.limit:
                    sql += f" LIMIT {query.limit}"
                
                # Execute query
                rows = await conn.fetch(sql, *params)
                
                # Convert rows to context items
                results = []
                for row in rows:
                    item = self._row_to_context_item(row)
                    
                    # Add to cache
                    self.context_cache[item.id] = item
                    self._update_indexes(item)
                    
                    results.append(item)
                
                return results
        
        except Exception as e:
            self.logger.error(f"Failed to query context from database: {e}")
            return []
    
    def _row_to_context_item(self, row) -> ContextItem:
        """
        Convert a database row to a context item.
        
        Args:
            row: Database row
            
        Returns:
            Context item
        """
        # Parse JSON fields
        value = json.loads(row["value"]) if isinstance(row["value"], str) else row["value"]
        metadata = json.loads(row["metadata"]) if row["metadata"] and isinstance(row["metadata"], str) else row["metadata"] or {}
        dependencies = json.loads(row["dependencies"]) if row["dependencies"] and isinstance(row["dependencies"], str) else row["dependencies"] or []
        
        # Create validity period
        validity = ContextValidityPeriod(
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            max_uses=row["max_uses"],
            current_uses=row["current_uses"] or 0
        )
        
        # Create context item
        return ContextItem(
            id=row["id"],
            source=ContextSource(row["source"]),
            type=ContextType(row["type"]),
            created_at=row["created_at"],
            entity_id=row["entity_id"],
            entity_type=row["entity_type"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            key=row["key"],
            value=value,
            metadata=metadata,
            relevance=Relevance(row["relevance"]),
            embedding=row["embedding"],
            validity=validity,
            dependencies=dependencies
        )
    
    def _create_context_text(self, item: ContextItem) -> str:
        """
        Create text representation of a context item for embedding.
        
        Args:
            item: The context item
            
        Returns:
            Text representation
        """
        parts = []
        
        # Add key
        parts.append(f"Key: {item.key}")
        
        # Add type and source
        parts.append(f"Type: {item.type.value}")
        parts.append(f"Source: {item.source.value}")
        
        # Add entity information if available
        if item.entity_type and item.entity_id:
            parts.append(f"Entity: {item.entity_type}/{item.entity_id}")
        
        # Add value
        if isinstance(item.value, str):
            parts.append(f"Value: {item.value}")
        elif isinstance(item.value, (list, dict)):
            try:
                parts.append(f"Value: {json.dumps(item.value)}")
            except:
                parts.append(f"Value: (Complex value)")
        else:
            parts.append(f"Value: {str(item.value)}")
        
        # Add metadata
        if item.metadata:
            try:
                parts.append(f"Metadata: {json.dumps(item.metadata)}")
            except:
                pass
        
        return "\n".join(parts)
    
    def _prune_cache(self) -> None:
        """Prune the least recently used items from the cache."""
        # Sort items by creation time (oldest first)
        items = sorted(self.context_cache.values(), key=lambda x: x.created_at)
        
        # Remove oldest items until we're under the limit
        items_to_remove = max(len(items) - self.cache_size, len(items) // 4)
        for item in items[:items_to_remove]:
            self._remove_from_cache(item.id)
    
    def _remove_from_cache(self, context_id: str) -> None:
        """
        Remove a context item from the cache.
        
        Args:
            context_id: ID of the context item to remove
        """
        if context_id not in self.context_cache:
            return
        
        item = self.context_cache[context_id]
        
        # Remove from main cache
        del self.context_cache[context_id]
        
        # Remove from indexes
        if item.entity_id and item.entity_id in self.entity_index:
            self.entity_index[item.entity_id].discard(context_id)
        
        if item.user_id and item.user_id in self.user_index:
            self.user_index[item.user_id].discard(context_id)
        
        if item.session_id and item.session_id in self.session_index:
            self.session_index[item.session_id].discard(context_id)
        
        if item.key and item.key in self.key_index:
            self.key_index[item.key].discard(context_id)
        
        if item.source and item.source in self.source_index:
            self.source_index[item.source].discard(context_id)
        
        if item.type and item.type in self.type_index:
            self.type_index[item.type].discard(context_id)
    
    def _update_indexes(self, item: ContextItem) -> None:
        """
        Update indexes for a context item.
        
        Args:
            item: The context item to index
        """
        # Update entity index
        if item.entity_id:
            if item.entity_id not in self.entity_index:
                self.entity_index[item.entity_id] = set()
            self.entity_index[item.entity_id].add(item.id)
        
        # Update user index
        if item.user_id:
            if item.user_id not in self.user_index:
                self.user_index[item.user_id] = set()
            self.user_index[item.user_id].add(item.id)
        
        # Update session index
        if item.session_id:
            if item.session_id not in self.session_index:
                self.session_index[item.session_id] = set()
            self.session_index[item.session_id].add(item.id)
        
        # Update key index
        if item.key:
            if item.key not in self.key_index:
                self.key_index[item.key] = set()
            self.key_index[item.key].add(item.id)
        
        # Update source index
        if item.source:
            if item.source not in self.source_index:
                self.source_index[item.source] = set()
            self.source_index[item.source].add(item.id)
        
        # Update type index
        if item.type:
            if item.type not in self.type_index:
                self.type_index[item.type] = set()
            self.type_index[item.type].add(item.id)