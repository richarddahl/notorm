"""
Apache AGE integration for the Read Model query system.

This module provides integration between the Read Model query system and
Apache AGE knowledge graph. It enables graph-based queries to be used
with the EnhancedQueryService for richer query capabilities.
"""

import logging
import json
import asyncio
from typing import Dict, List, Any, Optional, Type, TypeVar, Generic, Union
from datetime import datetime, UTC

import asyncpg
from pydantic import BaseModel, Field

from uno.read_model.read_model import ReadModel
from uno.domain.graph_path_query import GraphPathQuery, PathQuerySpecification, QueryPath

# Type variable for read models
T = TypeVar('T', bound=ReadModel)


class AGEQueryResult(BaseModel):
    """
    Result of an Apache AGE query.
    
    Attributes:
        id: Entity ID
        score: Relevance score
        path: Optional path information if path query was executed
        metadata: Additional metadata about the result
    """
    
    id: str
    score: float
    path: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GraphQueryConfiguration(BaseModel):
    """
    Configuration for graph query integration.
    
    Attributes:
        graph_name: Name of the graph in Apache AGE
        age_schema: Schema name for AGE extension
        default_max_depth: Default maximum depth for graph traversals
        cache_results: Whether to cache query results
        cache_ttl: TTL for cached results in seconds
        enable_metrics: Whether to enable performance metrics
    """
    
    graph_name: str = "knowledge_graph"
    age_schema: str = "ag_catalog"
    default_max_depth: int = 3
    cache_results: bool = True
    cache_ttl: int = 300  # seconds
    enable_metrics: bool = True


class GraphQueryMetrics(BaseModel):
    """
    Metrics for graph query execution.
    
    Attributes:
        query_id: The query ID
        query_type: Type of query executed
        start_time: When the query started
        end_time: When the query completed
        duration_ms: Query duration in milliseconds
        node_count: Number of nodes processed
        path_count: Number of paths found
        cache_hit: Whether the result was from cache
    """
    
    query_id: str
    query_type: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    node_count: int = 0
    path_count: int = 0
    cache_hit: bool = False
    
    def complete(self, node_count: int, path_count: int) -> None:
        """
        Mark the query as complete.
        
        Args:
            node_count: Number of nodes processed
            path_count: Number of paths found
        """
        self.end_time = datetime.now(UTC)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.node_count = node_count
        self.path_count = path_count


class AGEGraphService:
    """
    Apache AGE graph service for enhanced querying capabilities.
    
    This service provides an interface to execute graph queries using
    Apache AGE and integrate the results with the read model query system.
    """
    
    def __init__(
        self,
        connection_pool: asyncpg.Pool,
        config: GraphQueryConfiguration = GraphQueryConfiguration(),
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the AGE graph service.
        
        Args:
            connection_pool: Database connection pool
            config: Graph query configuration
            logger: Optional logger for diagnostics
        """
        self.connection_pool = connection_pool
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        
        # Cache for query results
        self.cache: Dict[str, List[AGEQueryResult]] = {}
        self.cache_timestamps: Dict[str, float] = {}
        
        # Metrics storage
        self.metrics_enabled = config.enable_metrics
        self.recent_metrics: List[GraphQueryMetrics] = []
        self.max_metrics_history = 100
    
    async def query(self, query_dict: Dict[str, Any]) -> List[AGEQueryResult]:
        """
        Execute a graph query.
        
        Args:
            query_dict: Query parameters
                start_node: The starting node ID or type
                path_pattern: The graph path pattern to traverse
                max_depth: Maximum traversal depth
                filters: Additional filters to apply
            
        Returns:
            List of query results
        """
        # Create metrics
        metrics = GraphQueryMetrics(
            query_id=query_dict.get("query_id", f"graph_{datetime.now(UTC).timestamp()}"),
            query_type="path_query"
        )
        
        # Extract query parameters
        start_node = query_dict.get("start_node")
        path_pattern = query_dict.get("path_pattern")
        max_depth = query_dict.get("max_depth", self.config.default_max_depth)
        filters = query_dict.get("filters", {})
        
        if not start_node or not path_pattern:
            self.logger.error("Missing required parameters: start_node and path_pattern")
            return []
        
        # Check cache
        cache_key = self._generate_cache_key(query_dict)
        if self.config.cache_results and cache_key in self.cache:
            cache_time = self.cache_timestamps.get(cache_key, 0)
            if (asyncio.get_event_loop().time() - cache_time) < self.config.cache_ttl:
                # Update metrics
                if self.metrics_enabled:
                    metrics.cache_hit = True
                    metrics.complete(
                        node_count=len(self.cache[cache_key]),
                        path_count=len(self.cache[cache_key])
                    )
                    self._store_metrics(metrics)
                
                return self.cache[cache_key]
        
        try:
            # Convert to PathQuerySpecification
            path_query = PathQuerySpecification(
                path=path_pattern,
                params=filters,
                limit=100,  # Default large limit
                offset=0
            )
            
            # Create GraphPathQuery
            path_executor = GraphPathQuery(
                track_performance=True,
                use_cache=False  # We handle caching at this level
            )
            
            # Execute the query
            entity_ids, query_metadata = await path_executor.execute(path_query)
            
            # Create results
            results = []
            for i, entity_id in enumerate(entity_ids):
                # Calculate a score based on position (earlier = higher score)
                score = 1.0 - (i / max(len(entity_ids), 1))
                
                result = AGEQueryResult(
                    id=entity_id,
                    score=score,
                    metadata={
                        "query_path": path_pattern,
                        "position": i,
                        "query_metadata": query_metadata.dict() if hasattr(query_metadata, "dict") else {}
                    }
                )
                results.append(result)
            
            # Cache results if enabled
            if self.config.cache_results:
                self.cache[cache_key] = results
                self.cache_timestamps[cache_key] = asyncio.get_event_loop().time()
            
            # Update metrics
            if self.metrics_enabled:
                metrics.complete(
                    node_count=len(results),
                    path_count=len(results)
                )
                self._store_metrics(metrics)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing graph query: {e}")
            
            # Update metrics for failed query
            if self.metrics_enabled:
                metrics.complete(node_count=0, path_count=0)
                self._store_metrics(metrics)
            
            return []
    
    async def hybrid_query(
        self,
        text_query: str,
        vector_results: List[Dict[str, Any]],
        path_pattern: Optional[str] = None,
        max_depth: int = 2,
        vector_weight: float = 0.5,
        graph_weight: float = 0.5
    ) -> List[AGEQueryResult]:
        """
        Execute a hybrid query combining vector search with graph traversal.
        
        Args:
            text_query: Text query for context
            vector_results: Results from vector search
            path_pattern: Optional graph path pattern
            max_depth: Maximum graph traversal depth
            vector_weight: Weight for vector search results (0-1)
            graph_weight: Weight for graph search results (0-1)
            
        Returns:
            List of hybrid query results
        """
        # Create metrics
        metrics = GraphQueryMetrics(
            query_id=f"hybrid_{datetime.now(UTC).timestamp()}",
            query_type="hybrid_query"
        )
        
        # If no path pattern, just return vector results
        if not path_pattern or not vector_results:
            # Convert vector results to AGEQueryResult format
            results = []
            for i, result in enumerate(vector_results):
                results.append(AGEQueryResult(
                    id=result.get("id", f"unknown_{i}"),
                    score=result.get("score", 0.5),
                    metadata={"source": "vector_only"}
                ))
            
            # Update metrics
            if self.metrics_enabled:
                metrics.complete(node_count=len(results), path_count=0)
                self._store_metrics(metrics)
            
            return results
        
        try:
            # Extract IDs from vector results
            vector_ids = [result.get("id") for result in vector_results if "id" in result]
            if not vector_ids:
                return []
            
            # Store original vector scores
            vector_scores = {result.get("id"): result.get("score", 0.5) 
                            for result in vector_results if "id" in result}
            
            # Use the best vector match as starting point for graph query
            start_node = vector_ids[0]
            
            # Execute graph query
            graph_query = {
                "start_node": start_node,
                "path_pattern": path_pattern,
                "max_depth": max_depth
            }
            
            graph_results = await self.query(graph_query)
            
            # Extract graph scores
            graph_scores = {result.id: result.score for result in graph_results}
            
            # Blend scores
            blended_scores = {}
            
            # Add vector scores with weight
            for node_id, score in vector_scores.items():
                blended_scores[node_id] = score * vector_weight
            
            # Add graph scores with weight
            for node_id, score in graph_scores.items():
                if node_id in blended_scores:
                    blended_scores[node_id] += score * graph_weight
                else:
                    blended_scores[node_id] = score * graph_weight
            
            # Create results
            results = []
            for node_id, score in blended_scores.items():
                # Find original metadata
                metadata = {}
                
                # Add vector metadata if available
                if node_id in vector_scores:
                    metadata["vector_score"] = vector_scores[node_id]
                    metadata["vector_rank"] = vector_ids.index(node_id)
                
                # Add graph metadata if available
                for graph_result in graph_results:
                    if graph_result.id == node_id:
                        if graph_result.metadata:
                            metadata["graph_metadata"] = graph_result.metadata
                        break
                
                metadata["source"] = "hybrid"
                metadata["blend_weights"] = {
                    "vector": vector_weight,
                    "graph": graph_weight
                }
                
                result = AGEQueryResult(
                    id=node_id,
                    score=score,
                    metadata=metadata
                )
                results.append(result)
            
            # Sort by blended score
            results.sort(key=lambda x: x.score, reverse=True)
            
            # Update metrics
            if self.metrics_enabled:
                metrics.complete(
                    node_count=len(results),
                    path_count=len(graph_results)
                )
                self._store_metrics(metrics)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error executing hybrid query: {e}")
            
            # Update metrics for failed query
            if self.metrics_enabled:
                metrics.complete(node_count=0, path_count=0)
                self._store_metrics(metrics)
            
            return []
    
    def _generate_cache_key(self, query_dict: Dict[str, Any]) -> str:
        """
        Generate a cache key for a query.
        
        Args:
            query_dict: The query dictionary
            
        Returns:
            Cache key string
        """
        # Create a sorted, deterministic representation of the query
        sorted_dict = {k: query_dict[k] for k in sorted(query_dict.keys())
                       if k != "query_id"}  # Exclude query_id from cache key
        
        # Convert to JSON
        query_json = json.dumps(sorted_dict, sort_keys=True)
        
        # Use query JSON as cache key
        return f"age_query:{hash(query_json)}"
    
    def _store_metrics(self, metrics: GraphQueryMetrics) -> None:
        """
        Store query metrics.
        
        Args:
            metrics: The metrics to store
        """
        if not self.metrics_enabled:
            return
        
        self.recent_metrics.append(metrics)
        
        # Trim metrics history if needed
        if len(self.recent_metrics) > self.max_metrics_history:
            self.recent_metrics = self.recent_metrics[-self.max_metrics_history:]
    
    def get_recent_metrics(self) -> List[Dict[str, Any]]:
        """
        Get recent query metrics.
        
        Returns:
            List of metrics dictionaries
        """
        return [m.model_dump() for m in self.recent_metrics]
    
    def clear_cache(self) -> None:
        """Clear the query result cache."""
        self.cache.clear()
        self.cache_timestamps.clear()


class ReadModelGraphAdapter(Generic[T]):
    """
    Adapter to connect graph queries with read models.
    
    This adapter enables executing graph queries and converting the results
    to read model instances through a repository.
    """
    
    def __init__(
        self,
        graph_service: AGEGraphService,
        read_model_type: Type[T],
        repository: Any,  # ReadModelRepository[T]
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the read model graph adapter.
        
        Args:
            graph_service: The graph service for executing queries
            read_model_type: The type of read model
            repository: Repository for fetching read models
            logger: Optional logger for diagnostics
        """
        self.graph_service = graph_service
        self.read_model_type = read_model_type
        self.repository = repository
        self.logger = logger or logging.getLogger(__name__)
    
    async def query(
        self,
        path_pattern: str,
        start_node: str,
        filters: Optional[Dict[str, Any]] = None,
        max_depth: int = 3
    ) -> List[T]:
        """
        Execute a graph query and retrieve read models.
        
        Args:
            path_pattern: The graph path pattern to traverse
            start_node: The starting node ID or type
            filters: Additional filters to apply
            max_depth: Maximum traversal depth
            
        Returns:
            List of read models matching the query
        """
        # Prepare query
        query_dict = {
            "start_node": start_node,
            "path_pattern": path_pattern,
            "max_depth": max_depth,
            "filters": filters or {}
        }
        
        # Execute query
        graph_results = await self.graph_service.query(query_dict)
        
        # Retrieve read models
        read_models = []
        for result in graph_results:
            model = await self.repository.get(result.id)
            if model:
                read_models.append(model)
        
        return read_models
    
    async def hybrid_query(
        self,
        text_query: str,
        vector_results: List[Dict[str, Any]],
        path_pattern: Optional[str] = None,
        max_depth: int = 2,
        vector_weight: float = 0.5,
        graph_weight: float = 0.5
    ) -> List[Tuple[T, float]]:
        """
        Execute a hybrid query and retrieve read models with scores.
        
        Args:
            text_query: Text query for context
            vector_results: Results from vector search
            path_pattern: Optional graph path pattern
            max_depth: Maximum graph traversal depth
            vector_weight: Weight for vector search results (0-1)
            graph_weight: Weight for graph search results (0-1)
            
        Returns:
            List of (read model, score) tuples
        """
        # Execute hybrid query
        hybrid_results = await self.graph_service.hybrid_query(
            text_query=text_query,
            vector_results=vector_results,
            path_pattern=path_pattern,
            max_depth=max_depth,
            vector_weight=vector_weight,
            graph_weight=graph_weight
        )
        
        # Retrieve read models with scores
        scored_models = []
        for result in hybrid_results:
            model = await self.repository.get(result.id)
            if model:
                scored_models.append((model, result.score))
        
        return scored_models


async def create_age_graph_service(
    connection_string: str,
    graph_name: str = "knowledge_graph",
    logger: Optional[logging.Logger] = None
) -> AGEGraphService:
    """
    Create an AGE graph service.
    
    Args:
        connection_string: Database connection string
        graph_name: Name of the graph in Apache AGE
        logger: Optional logger for diagnostics
        
    Returns:
        Initialized AGE graph service
    """
    # Create connection pool
    pool = await asyncpg.create_pool(connection_string)
    
    # Create configuration
    config = GraphQueryConfiguration(
        graph_name=graph_name,
        age_schema="ag_catalog",
        default_max_depth=3,
        cache_results=True
    )
    
    # Create service
    service = AGEGraphService(
        connection_pool=pool,
        config=config,
        logger=logger
    )
    
    return service