"""Query service implementation for the Uno framework.

This module defines query services that use read models for efficient querying
as part of the CQRS pattern's query side.
"""

import logging
import json
from typing import (
    Any, Dict, Generic, List, Optional, Type, TypeVar, Union, Protocol,
    cast, Tuple
)
from uuid import uuid4
from datetime import datetime, UTC

from pydantic import ConfigDict, BaseModel, Field
from uno.domain.cqrs import Query, QueryHandler, QueryResult
from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.cache_service import ReadModelCache

# Type variables
T = TypeVar('T', bound=ReadModel)
QueryT = TypeVar('QueryT', bound=Query)
ResultT = TypeVar('ResultT')


class ReadModelQuery(Query[T]):
    """
    Base class for read model queries.
    
    Read model queries are used to retrieve read models in a type-safe way.
    
    Type Parameters:
        T: The type of read model this query returns
    """
    pass


class GetByIdQuery(ReadModelQuery[T]):
    """Query to get a read model by ID."""
    
    model_config = ConfigDict(frozen=False)
    id: str
    
    def __init__(self, id: str):
        """
        Initialize the query.
        
        Args:
            id: The read model ID
        """
        super().__init__(id=id, query_id=str(uuid4()))


class FindByQuery(ReadModelQuery[T]):
    """Query to find read models by criteria."""
    
    model_config = ConfigDict(frozen=False)
    criteria: Dict[str, Any]
    
    def __init__(self, criteria: Dict[str, Any]):
        """
        Initialize the query.
        
        Args:
            criteria: The query criteria
        """
        super().__init__(criteria=criteria, query_id=str(uuid4()))


class PaginatedQuery(ReadModelQuery[T]):
    """Query with pagination support."""
    
    model_config = ConfigDict(frozen=False)
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_direction: str = "asc"
    
    def __init__(
        self,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_direction: str = "asc"
    ):
        """
        Initialize the query.
        
        Args:
            page: The page number (1-indexed)
            page_size: The page size
            sort_by: The field to sort by
            sort_direction: The sort direction ("asc" or "desc")
        """
        super().__init__(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction,
            query_id=str(uuid4())
        )


class SearchQuery(PaginatedQuery[T]):
    """Query for full-text search."""
    
    model_config = ConfigDict(frozen=False)
    text: str
    fields: Optional[List[str]] = None
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(
        self,
        text: str,
        fields: Optional[List[str]] = None,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: Optional[str] = None,
        sort_direction: str = "asc"
    ):
        """
        Initialize the query.
        
        Args:
            text: The search text
            fields: The fields to search in
            filters: Additional filters to apply
            page: The page number (1-indexed)
            page_size: The page size
            sort_by: The field to sort by
            sort_direction: The sort direction ("asc" or "desc")
        """
        super().__init__(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_direction=sort_direction
        )
        self.text = text
        self.fields = fields
        self.filters = filters or {}


class AggregateQuery(ReadModelQuery[T]):
    """Query for aggregation operations."""
    
    model_config = ConfigDict(frozen=False)
    group_by: List[str]
    aggregates: Dict[str, str]  # field -> operation (sum, avg, min, max, count)
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(
        self,
        group_by: List[str],
        aggregates: Dict[str, str],
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the query.
        
        Args:
            group_by: The fields to group by
            aggregates: The aggregation operations to perform
            filters: Additional filters to apply
        """
        super().__init__(
            group_by=group_by,
            aggregates=aggregates,
            filters=filters or {},
            query_id=str(uuid4())
        )


class GraphQuery(ReadModelQuery[T]):
    """Query for graph-based searches."""
    
    model_config = ConfigDict(frozen=False)
    start_node: str
    path_pattern: str
    max_depth: int = 3
    filters: Dict[str, Any] = Field(default_factory=dict)
    
    def __init__(
        self,
        start_node: str,
        path_pattern: str,
        max_depth: int = 3,
        filters: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the query.
        
        Args:
            start_node: The starting node ID or type
            path_pattern: The graph path pattern to traverse
            max_depth: Maximum traversal depth
            filters: Additional filters to apply
        """
        super().__init__(
            start_node=start_node,
            path_pattern=path_pattern,
            max_depth=max_depth,
            filters=filters or {},
            query_id=str(uuid4())
        )


class HybridQuery(ReadModelQuery[T]):
    """Query combining vector search with graph traversal."""
    
    model_config = ConfigDict(frozen=False)
    text: str
    path_pattern: Optional[str] = None
    vector_weight: float = 0.5
    graph_weight: float = 0.5
    filters: Dict[str, Any] = Field(default_factory=dict)
    page: int = 1
    page_size: int = 20
    
    def __init__(
        self,
        text: str,
        path_pattern: Optional[str] = None,
        vector_weight: float = 0.5,
        graph_weight: float = 0.5,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20
    ):
        """
        Initialize the query.
        
        Args:
            text: The search text for vector search
            path_pattern: Optional graph path pattern
            vector_weight: Weight for vector search results (0-1)
            graph_weight: Weight for graph search results (0-1)
            filters: Additional filters to apply
            page: The page number (1-indexed)
            page_size: The page size
        """
        super().__init__(
            text=text,
            path_pattern=path_pattern,
            vector_weight=vector_weight,
            graph_weight=graph_weight,
            filters=filters or {},
            page=page,
            page_size=page_size,
            query_id=str(uuid4())
        )


class PaginatedResult(Generic[T]):
    """
    Paginated result for queries.
    
    Attributes:
        items: The items in the current page
        total: The total number of items
        page: The current page number
        page_size: The page size
        pages: The total number of pages
    """
    
    def __init__(
        self,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ):
        """
        Initialize the paginated result.
        
        Args:
            items: The items in the current page
            total: The total number of items
            page: The current page number
            page_size: The page size
        """
        self.items = items
        self.total = total
        self.page = page
        self.page_size = page_size
        self.pages = (total + page_size - 1) // page_size if page_size > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "items": [item.model_dump() for item in self.items],
            "total": self.total,
            "page": self.page,
            "page_size": self.page_size,
            "pages": self.pages
        }
    
    @property
    def has_next(self) -> bool:
        """Check if there is a next page."""
        return self.page < self.pages
    
    @property
    def has_prev(self) -> bool:
        """Check if there is a previous page."""
        return self.page > 1


class QueryMetrics(BaseModel):
    """
    Metrics for query execution.
    
    Attributes:
        query_id: The query ID
        start_time: When the query started
        end_time: When the query completed
        duration_ms: Query duration in milliseconds
        cache_hit: Whether the result was from cache
        result_count: Number of results returned
    """
    
    query_id: str
    start_time: datetime = Field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    cache_hit: bool = False
    result_count: int = 0
    query_type: str = ""
    
    def complete(self, result_count: int) -> None:
        """
        Mark the query as complete.
        
        Args:
            result_count: Number of results returned
        """
        self.end_time = datetime.now(UTC)
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.result_count = result_count


class ReadModelQueryService(Generic[T]):
    """
    Service for querying read models.
    
    This service provides a high-level API for querying read models,
    with support for caching and other optimizations.
    """
    
    def __init__(
        self,
        repository: ReadModelRepository[T],
        model_type: Type[T],
        cache: Optional[ReadModelCache[T]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query service.
        
        Args:
            repository: The repository for retrieving read models
            model_type: The type of read model this service handles
            cache: Optional cache for read models
            logger: Optional logger instance
        """
        self.repository = repository
        self.model_type = model_type
        self.cache = cache
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.metrics_enabled = True
        self.recent_metrics: List[QueryMetrics] = []
        self.max_metrics_history = 100
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        # Create metrics
        metrics = QueryMetrics(query_id=str(uuid4()), query_type="get_by_id")
        
        # Try to get from cache first
        if self.cache:
            cached_model = await self.cache.get(id)
            if cached_model:
                self.logger.debug(f"Cache hit for read model {id}")
                metrics.cache_hit = True
                metrics.complete(1 if cached_model else 0)
                self._store_metrics(metrics)
                return cached_model
        
        # Get from repository
        model = await self.repository.get(id)
        
        # Cache the result if found
        if model and self.cache:
            await self.cache.set(id, model)
        
        # Complete metrics
        metrics.complete(1 if model else 0)
        self._store_metrics(metrics)
        
        return model
    
    async def find(self, criteria: Dict[str, Any]) -> List[T]:
        """
        Find read models matching criteria.
        
        Args:
            criteria: The query criteria
            
        Returns:
            List of matching read models
        """
        # Create metrics
        metrics = QueryMetrics(query_id=str(uuid4()), query_type="find")
        
        # Currently we don't cache find results, as it would be complex
        # to invalidate them correctly
        results = await self.repository.find(criteria)
        
        # Complete metrics
        metrics.complete(len(results))
        self._store_metrics(metrics)
        
        return results
    
    async def paginate(
        self,
        query: PaginatedQuery[T]
    ) -> PaginatedResult[T]:
        """
        Paginate query results.
        
        Args:
            query: The paginated query
            
        Returns:
            Paginated result
        """
        # Create metrics
        metrics = QueryMetrics(query_id=query.query_id, query_type="paginate")
        
        # To be implemented in subclasses
        # For now, use find as a basic implementation
        if hasattr(query, 'criteria'):
            all_results = await self.find(query.criteria)
        else:
            all_results = await self.find({})
        
        # Apply sorting
        if query.sort_by:
            reverse = query.sort_direction.lower() == "desc"
            all_results.sort(
                key=lambda x: getattr(x, query.sort_by) if hasattr(x, query.sort_by) else None,
                reverse=reverse
            )
        
        # Apply pagination
        total = len(all_results)
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        page_items = all_results[start_idx:end_idx]
        
        # Create result
        result = PaginatedResult(
            items=page_items,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
        
        # Complete metrics
        metrics.complete(len(page_items))
        self._store_metrics(metrics)
        
        return result
    
    async def handle_query(self, query: ReadModelQuery[T]) -> Any:
        """
        Handle a read model query.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        if isinstance(query, GetByIdQuery):
            return await self.get_by_id(query.id)
        elif isinstance(query, FindByQuery):
            return await self.find(query.criteria)
        elif isinstance(query, PaginatedQuery):
            return await self.paginate(query)
        else:
            raise ValueError(f"Unsupported query type: {type(query).__name__}")
    
    def _store_metrics(self, metrics: QueryMetrics) -> None:
        """Store query metrics."""
        if not self.metrics_enabled:
            return
        
        self.recent_metrics.append(metrics)
        
        # Trim metrics history if needed
        if len(self.recent_metrics) > self.max_metrics_history:
            self.recent_metrics = self.recent_metrics[-self.max_metrics_history:]
    
    def get_recent_metrics(self) -> List[Dict[str, Any]]:
        """Get recent query metrics."""
        return [m.model_dump() for m in self.recent_metrics]


class EnhancedQueryService(ReadModelQueryService[T]):
    """
    Enhanced query service with advanced search capabilities.
    
    This service extends the basic read model query service with
    full-text search, complex filtering, aggregation functions, 
    and integration with graph and vector search.
    """
    
    def __init__(
        self,
        repository: ReadModelRepository[T],
        model_type: Type[T],
        cache: Optional[ReadModelCache[T]] = None,
        graph_service: Optional[Any] = None,
        vector_service: Optional[Any] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the enhanced query service.
        
        Args:
            repository: The repository for retrieving read models
            model_type: The type of read model this service handles
            cache: Optional cache for read models
            graph_service: Optional graph service for graph-based queries
            vector_service: Optional vector service for similarity search
            logger: Optional logger instance
        """
        super().__init__(repository, model_type, cache, logger)
        self.graph_service = graph_service
        self.vector_service = vector_service
    
    async def search(
        self,
        query: SearchQuery[T]
    ) -> PaginatedResult[T]:
        """
        Perform a full-text search on read models.
        
        Args:
            query: The search query
            
        Returns:
            Paginated search results
        """
        # Create metrics
        metrics = QueryMetrics(query_id=query.query_id, query_type="search")
        
        # If vector service is available, use it for better results
        if self.vector_service:
            # Convert query to vector search format
            vector_query = {
                "text": query.text,
                "limit": query.page_size * query.page,  # Get more to apply filters
                "filters": query.filters
            }
            
            # Execute vector search
            vector_results = await self.vector_service.search(vector_query)
            
            # Get full read models for the vector results
            # Note: This assumes vector_results contains IDs
            model_ids = [result.id for result in vector_results]
            models = []
            
            for model_id in model_ids:
                model = await self.get_by_id(model_id)
                if model:
                    models.append(model)
            
            # Apply pagination
            total = len(models)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            page_items = models[start_idx:end_idx]
            
        else:
            # Fall back to basic text search if vector search is not available
            # This is a simplified implementation that doesn't do true full-text search
            all_results = await self.repository.find(query.filters)
            
            # Filter by text
            filtered_results = []
            search_text = query.text.lower()
            
            for model in all_results:
                # If fields are specified, search only in those fields
                if query.fields:
                    for field in query.fields:
                        if hasattr(model, field):
                            field_value = getattr(model, field)
                            if isinstance(field_value, str) and search_text in field_value.lower():
                                filtered_results.append(model)
                                break
                else:
                    # Search in all string fields
                    for field, value in model.model_dump().items():
                        if isinstance(value, str) and search_text in value.lower():
                            filtered_results.append(model)
                            break
            
            # Apply sorting if specified
            if query.sort_by:
                reverse = query.sort_direction.lower() == "desc"
                filtered_results.sort(
                    key=lambda x: getattr(x, query.sort_by) if hasattr(x, query.sort_by) else None,
                    reverse=reverse
                )
            
            # Apply pagination
            total = len(filtered_results)
            start_idx = (query.page - 1) * query.page_size
            end_idx = start_idx + query.page_size
            page_items = filtered_results[start_idx:end_idx]
        
        # Create result
        result = PaginatedResult(
            items=page_items,
            total=total,
            page=query.page,
            page_size=query.page_size
        )
        
        # Complete metrics
        metrics.complete(len(page_items))
        self._store_metrics(metrics)
        
        return result
    
    async def aggregate(
        self,
        query: AggregateQuery[T]
    ) -> List[Dict[str, Any]]:
        """
        Perform aggregation operations on read models.
        
        Args:
            query: The aggregation query
            
        Returns:
            List of aggregation results
        """
        # Create metrics
        metrics = QueryMetrics(query_id=query.query_id, query_type="aggregate")
        
        # Get all models matching the filters
        models = await self.repository.find(query.filters)
        
        # Group models by the specified fields
        groups: Dict[str, List[T]] = {}
        
        for model in models:
            # Create a group key by concatenating the values of the group_by fields
            group_values = []
            for field in query.group_by:
                if hasattr(model, field):
                    value = getattr(model, field)
                    group_values.append(str(value))
                else:
                    group_values.append("null")
            
            group_key = "|".join(group_values)
            
            if group_key not in groups:
                groups[group_key] = []
            
            groups[group_key].append(model)
        
        # Compute aggregates for each group
        results = []
        
        for group_key, group_models in groups.items():
            group_values = group_key.split("|")
            result = {}
            
            # Add group by values
            for i, field in enumerate(query.group_by):
                result[field] = group_values[i]
            
            # Compute aggregates
            for field, operation in query.aggregates.items():
                values = []
                for model in group_models:
                    if hasattr(model, field):
                        value = getattr(model, field)
                        if isinstance(value, (int, float)):
                            values.append(value)
                
                # Skip if no values
                if not values:
                    result[f"{operation}_{field}"] = None
                    continue
                
                # Compute aggregate value
                if operation == "sum":
                    result[f"{operation}_{field}"] = sum(values)
                elif operation == "avg":
                    result[f"{operation}_{field}"] = sum(values) / len(values)
                elif operation == "min":
                    result[f"{operation}_{field}"] = min(values)
                elif operation == "max":
                    result[f"{operation}_{field}"] = max(values)
                elif operation == "count":
                    result[f"{operation}_{field}"] = len(values)
                else:
                    result[f"{operation}_{field}"] = None
            
            results.append(result)
        
        # Complete metrics
        metrics.complete(len(results))
        self._store_metrics(metrics)
        
        return results
    
    async def graph_query(
        self,
        query: GraphQuery[T]
    ) -> List[T]:
        """
        Perform a graph-based query.
        
        Args:
            query: The graph query
            
        Returns:
            List of read models matching the graph criteria
        """
        # Create metrics
        metrics = QueryMetrics(query_id=query.query_id, query_type="graph_query")
        
        # Check if graph service is available
        if not self.graph_service:
            self.logger.warning("Graph service is not available")
            metrics.complete(0)
            self._store_metrics(metrics)
            return []
        
        # Execute graph query
        try:
            # Format for graph service
            graph_query = {
                "start_node": query.start_node,
                "path_pattern": query.path_pattern,
                "max_depth": query.max_depth,
                "filters": query.filters
            }
            
            # Execute query and get node IDs
            node_ids = await self.graph_service.query(graph_query)
            
            # Get read models for the node IDs
            models = []
            for node_id in node_ids:
                model = await self.get_by_id(node_id)
                if model:
                    models.append(model)
            
            # Complete metrics
            metrics.complete(len(models))
            self._store_metrics(metrics)
            
            return models
            
        except Exception as e:
            self.logger.error(f"Graph query failed: {e}")
            metrics.complete(0)
            self._store_metrics(metrics)
            return []
    
    async def hybrid_query(
        self,
        query: HybridQuery[T]
    ) -> PaginatedResult[T]:
        """
        Perform a hybrid query combining vector and graph search.
        
        Args:
            query: The hybrid query
            
        Returns:
            Paginated hybrid search results
        """
        # Create metrics
        metrics = QueryMetrics(query_id=query.query_id, query_type="hybrid_query")
        
        # Check if required services are available
        if not self.vector_service:
            self.logger.warning("Vector service is not available for hybrid query")
            
            # Fall back to text search
            search_query = SearchQuery(
                text=query.text,
                filters=query.filters,
                page=query.page,
                page_size=query.page_size
            )
            
            return await self.search(search_query)
        
        if not self.graph_service and query.path_pattern:
            self.logger.warning("Graph service is not available for hybrid query")
        
        # First, get vector search results
        vector_query = {
            "text": query.text,
            "limit": query.page_size * 2,  # Get more for blending
            "filters": query.filters
        }
        
        vector_results = await self.vector_service.search(vector_query)
        vector_ids = [result.id for result in vector_results]
        vector_scores = {result.id: result.score for result in vector_results}
        
        # If path pattern is specified and graph service is available,
        # get graph search results
        graph_ids = []
        graph_scores = {}
        
        if query.path_pattern and self.graph_service:
            graph_query = {
                "start_node": vector_ids[0] if vector_ids else None,  # Start from best vector match
                "path_pattern": query.path_pattern,
                "max_depth": 3,
                "filters": query.filters
            }
            
            graph_results = await self.graph_service.query(graph_query)
            graph_ids = [result.id for result in graph_results]
            graph_scores = {result.id: result.score for result in graph_results}
        
        # Blend results based on specified weights
        blended_scores = {}
        
        # Add vector scores
        for node_id, score in vector_scores.items():
            blended_scores[node_id] = score * query.vector_weight
        
        # Add graph scores
        for node_id, score in graph_scores.items():
            if node_id in blended_scores:
                blended_scores[node_id] += score * query.graph_weight
            else:
                blended_scores[node_id] = score * query.graph_weight
        
        # Sort by blended score
        sorted_ids = sorted(blended_scores.keys(), key=lambda x: blended_scores[x], reverse=True)
        
        # Apply pagination
        start_idx = (query.page - 1) * query.page_size
        end_idx = start_idx + query.page_size
        page_ids = sorted_ids[start_idx:end_idx]
        
        # Get read models for the page IDs
        page_items = []
        for node_id in page_ids:
            model = await self.get_by_id(node_id)
            if model:
                page_items.append(model)
        
        # Create result
        result = PaginatedResult(
            items=page_items,
            total=len(sorted_ids),
            page=query.page,
            page_size=query.page_size
        )
        
        # Complete metrics
        metrics.complete(len(page_items))
        self._store_metrics(metrics)
        
        return result
    
    async def handle_query(self, query: ReadModelQuery[T]) -> Any:
        """
        Handle a read model query with enhanced capabilities.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        # Handle query based on type
        if isinstance(query, SearchQuery):
            return await self.search(query)
        elif isinstance(query, AggregateQuery):
            return await self.aggregate(query)
        elif isinstance(query, GraphQuery):
            return await self.graph_query(query)
        elif isinstance(query, HybridQuery):
            return await self.hybrid_query(query)
        else:
            # Fall back to base handler
            return await super().handle_query(query)


class ReadModelQueryHandler(QueryHandler[QueryT, ResultT]):
    """
    Query handler for read model queries.
    
    This handler delegates to a query service to handle read model queries.
    """
    
    def __init__(
        self,
        query_type: Type[QueryT],
        query_service: ReadModelQueryService[Any],
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the query handler.
        
        Args:
            query_type: The type of query this handler processes
            query_service: The query service to delegate to
            logger: Optional logger instance
        """
        self.query_type = query_type
        self.query_service = query_service
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def handle(self, query: QueryT) -> ResultT:
        """
        Handle a query.
        
        Args:
            query: The query to handle
            
        Returns:
            The query result
        """
        if not isinstance(query, ReadModelQuery):
            raise ValueError(f"Query {query} is not a ReadModelQuery")
        
        return cast(ResultT, await self.query_service.handle_query(query))