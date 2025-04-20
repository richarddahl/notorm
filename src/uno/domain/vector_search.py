"""
Vector search functionality for the UNO framework.

This module provides vector search capabilities using PostgreSQL's pgvector
extension, including similarity search, hybrid search combining graph and vector search,
and classes for managing embeddings.
"""

import logging
import json
from typing import Dict, List, Any, Optional, TypeVar, Type, Generic, Union, Tuple

from pydantic import BaseModel

from uno.database.session import async_session
from uno.settings import uno_settings
from uno.domain.core import Entity
from uno.core.base.respository import Repository
from uno.sql.emitters.vector import VectorSearchEmitter

T = TypeVar("T", bound=Entity)


class VectorSearchResult(BaseModel):
    """
    Result from a vector search operation.

    Attributes:
        id: Entity ID
        similarity: Similarity score (0-1 where 1 is most similar)
        entity: Optional full entity object if loaded
        metadata: Additional metadata about the search result
    """

    id: str
    similarity: float
    entity: Optional[Any] = None
    metadata: dict[str, Any] = {}

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from metadata with default fallback.

        Args:
            key: Metadata key to retrieve
            default: Default value if key is not found

        Returns:
            Value from metadata or default
        """
        return self.metadata.get(key, default)


class TypedVectorSearchResult(Generic[T]):
    """
    Typed wrapper for vector search results.

    This class provides a generic wrapper for vector search results,
    allowing results to be typed to a specific model type.
    """

    def __init__(
        self,
        id: str,
        entity: T,
        similarity: float,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize the typed vector search result.

        Args:
            id: Entity ID
            entity: Typed entity object
            similarity: Similarity score (0-1 where 1 is most similar)
            metadata: Additional metadata about the search result
        """
        self.id = id
        self.entity = entity
        self.similarity = similarity
        self.metadata = metadata or {}

    def get_metadata_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from metadata with default fallback.

        Args:
            key: Metadata key to retrieve
            default: Default value if key is not found

        Returns:
            Value from metadata or default
        """
        return self.metadata.get(key, default)

    @classmethod
    def from_result(
        cls, result: VectorSearchResult, entity: T
    ) -> "TypedVectorSearchResult[T]":
        """
        Create a typed result from a regular search result.

        Args:
            result: Regular vector search result
            entity: Typed entity object

        Returns:
            Typed vector search result
        """
        return cls(
            id=result.id,
            entity=entity,
            similarity=result.similarity,
            metadata=result.metadata,
        )


class VectorQuery(BaseModel):
    """
    Vector search query specification.

    Attributes:
        query_text: The text to search for
        limit: Maximum number of results to return
        threshold: Minimum similarity score (0-1)
        metric: Distance metric to use (cosine, l2, dot)
    """

    query_text: str
    limit: int = 10
    threshold: float = 0.7
    metric: str = "cosine"  # Options: "cosine", "l2", "dot"


class HybridQuery(VectorQuery):
    """
    Hybrid search query combining graph traversal and vector search.

    Attributes:
        start_node_type: Type of node to start graph traversal from
        start_filters: Filters to apply to the start node
        path_pattern: Cypher path pattern for traversal
        combine_method: How to combine graph and vector results
        graph_weight: Weight to give graph results (0-1)
        vector_weight: Weight to give vector results (0-1)
    """

    start_node_type: str
    start_filters: dict[str, Any] = {}
    path_pattern: str
    combine_method: str = "intersect"  # Options: "intersect", "union", "weighted"
    graph_weight: float = 0.5
    vector_weight: float = 0.5


class VectorSearchService(Generic[T]):
    """
    Service for performing vector search operations.

    This service provides methods for performing vector similarity search,
    integrating with the repository pattern to load full entities.
    """

    def __init__(
        self,
        entity_type: Type[T],
        table_name: str,
        repository: Optional[Repository[T]] = None,
        schema: str | None = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize vector search service.

        Args:
            entity_type: The entity type this service searches for
            table_name: The database table name containing embeddings
            repository: Optional repository for loading full entities
            schema: Optional database schema name (defaults to settings.DB_SCHEMA)
            logger: Optional logger for diagnostics
        """
        from uno.settings import uno_settings

        self.entity_type = entity_type
        self.table_name = table_name
        self.repository = repository
        self.schema = schema or uno_settings.DB_SCHEMA
        self.logger = logger or logging.getLogger(__name__)

        # Create a VectorSearchEmitter for this service
        self.emitter = VectorSearchEmitter(
            table_name=self.table_name,
            column_name="embedding",  # Default column name
            schema=self.schema,
        )

    async def search(self, query: VectorQuery) -> list[VectorSearchResult]:
        """
        Perform a vector similarity search.

        Args:
            query: The vector search query

        Returns:
            List of search results
        """
        try:
            async with async_session() as session:
                # Use the emitter to execute the search
                results = await self.emitter.execute_search(
                    connection=session,
                    query_text=query.query_text,
                    limit=query.limit,
                    threshold=query.threshold,
                    metric=query.metric,
                )

                # Create result objects
                search_results = []

                for result in results:
                    # Create VectorSearchResult instance
                    search_result = VectorSearchResult(
                        id=result["id"],
                        similarity=result["similarity"],
                        metadata={"row_data": result.get("row_data", {})},
                    )
                    search_results.append(search_result)

                # Load entities if repository is available
                if self.repository and search_results:
                    for result_obj in search_results:
                        entity = await self.repository.get(result_obj.id)
                        if entity:
                            result_obj.entity = entity

                return search_results

        except Exception as e:
            self.logger.error(f"Vector search error: {e}")
            raise

    async def hybrid_search(self, query: HybridQuery) -> list[VectorSearchResult]:
        """
        Perform a hybrid search combining graph traversal and vector search.

        Args:
            query: The hybrid search query

        Returns:
            List of search results
        """
        try:
            # Convert start_filters to JSON for use in the graph query
            filters_json = json.dumps(query.start_filters)

            # Construct the graph traversal query
            graph_query = f"""
            SELECT 
                id::TEXT,
                distance
            FROM
                {self.schema}.graph_traverse(
                    '{query.start_node_type}',
                    '{filters_json}',
                    '{query.path_pattern}'
                )
            """

            async with async_session() as session:
                # Use the emitter to execute the hybrid search
                results = await self.emitter.execute_hybrid_search(
                    connection=session,
                    query_text=query.query_text,
                    graph_query=graph_query,
                    limit=query.limit,
                    threshold=query.threshold,
                )

                # Create result objects
                search_results = []

                for result in results:
                    # Create VectorSearchResult instance with graph distance metadata
                    search_result = VectorSearchResult(
                        id=result["id"],
                        similarity=result["similarity"],
                        metadata={
                            "row_data": result.get("row_data", {}),
                            "graph_distance": result.get("graph_distance", 999999),
                        },
                    )
                    search_results.append(search_result)

                # Load entities if repository is available
                if self.repository and search_results:
                    for result_obj in search_results:
                        entity = await self.repository.get(result_obj.id)
                        if entity:
                            result_obj.entity = entity

                return search_results

        except Exception as e:
            self.logger.error(f"Hybrid search error: {e}")
            raise

    async def generate_embedding(self, text: str) -> list[float]:
        """
        Generate an embedding vector for text using the database function.

        This is useful for getting consistent embeddings for external use.

        Args:
            text: The text to embed

        Returns:
            Embedding vector as a list of floats
        """
        try:
            async with async_session() as session:
                # Use the emitter to execute the embedding generation
                return await self.emitter.execute_generate_embedding(
                    connection=session, text=text
                )

        except Exception as e:
            self.logger.error(f"Embedding generation error: {e}")
            raise

    async def search_typed(
        self, query: Union[VectorQuery, HybridQuery]
    ) -> TypedVectorSearchResponse[T]:
        """
        Perform a vector search with typed results.

        This method performs a vector search and returns the results wrapped
        in a typed response container for better type safety and utility.

        Args:
            query: Vector query or hybrid query parameters

        Returns:
            Typed response container with strongly-typed entity objects
        """
        import time

        start_time = time.time()

        # Execute the appropriate search based on query type
        if isinstance(query, HybridQuery):
            results = await self.hybrid_search(query)
        else:
            results = await self.search(query)

        # Calculate execution time
        execution_time_ms = (time.time() - start_time) * 1000

        # Define an entity loader function for lazy loading
        async def entity_loader(entity_id: str) -> Optional[T]:
            if self.repository:
                return await self.repository.get(entity_id)
            return None

        # Create typed results
        typed_results = []
        for result in results:
            # Use existing entity if available, otherwise it will be None
            entity = result.entity
            if entity:
                typed_result = TypedVectorSearchResult(
                    id=result.id,
                    entity=entity,
                    similarity=result.similarity,
                    metadata=result.metadata,
                )
                typed_results.append(typed_result)

        # Create response container
        return TypedVectorSearchResponse(
            results=typed_results,
            query=query.query_text,
            total_found=len(results),
            execution_time_ms=execution_time_ms,
            metadata={"query_type": type(query).__name__},
        )


class TypedVectorSearchResponse(Generic[T]):
    """
    Typed response container for vector search results.

    This class provides a generic container for vector search results,
    with typed entity objects for better type safety.
    """

    def __init__(
        self,
        results: list[TypedVectorSearchResult[T]],
        query: str,
        total_found: int,
        execution_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Initialize the typed vector search response.

        Args:
            results: List of typed search results
            query: Original search query
            total_found: Total number of matching results
            execution_time_ms: Execution time in milliseconds
            metadata: Additional metadata about the search
        """
        self.results = results
        self.query = query
        self.total_found = total_found
        self.execution_time_ms = execution_time_ms
        self.metadata = metadata or {}

    def get_best_match(self) -> Optional[TypedVectorSearchResult[T]]:
        """
        Get the highest-scoring result.

        Returns:
            Highest-scoring result or None if no results
        """
        if not self.results:
            return None
        return max(self.results, key=lambda x: x.similarity)

    def get_result_by_id(self, id: str) -> Optional[TypedVectorSearchResult[T]]:
        """
        Find a result by its ID.

        Args:
            id: Result ID to find

        Returns:
            Matching result or None if not found
        """
        for result in self.results:
            if result.id == id:
                return result
        return None

    def filter_by_similarity(
        self, min_similarity: float
    ) -> list[TypedVectorSearchResult[T]]:
        """
        Filter results by minimum similarity score.

        Args:
            min_similarity: Minimum similarity threshold

        Returns:
            List of results with similarity >= min_similarity
        """
        return [r for r in self.results if r.similarity >= min_similarity]

    def filter_by_metadata(
        self, key: str, value: Any
    ) -> list[TypedVectorSearchResult[T]]:
        """
        Filter results by metadata value.

        Args:
            key: Metadata key to check
            value: Value to match

        Returns:
            List of results with matching metadata
        """
        return [r for r in self.results if r.get_metadata_value(key) == value]

    def get_entities(self) -> list[T]:
        """
        Get all typed entities from results.

        Returns:
            List of typed entities
        """
        return [r.entity for r in self.results]

    @classmethod
    def from_results(
        cls,
        results: list[VectorSearchResult],
        query: str,
        entity_loader: callable,
        total_found: int | None = None,
        execution_time_ms: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> "TypedVectorSearchResponse[T]":
        """
        Create a typed response from regular search results.

        Args:
            results: List of regular search results
            query: Original search query
            entity_loader: Function to load entity by ID
            total_found: Total number of matching results
            execution_time_ms: Execution time in milliseconds
            metadata: Additional metadata about the search

        Returns:
            Typed vector search response
        """
        typed_results = []

        for result in results:
            # Use existing entity if available, otherwise load it
            entity = result.entity or entity_loader(result.id)
            if entity:
                typed_result = TypedVectorSearchResult.from_result(result, entity)
                typed_results.append(typed_result)

        return cls(
            results=typed_results,
            query=query,
            total_found=total_found or len(typed_results),
            execution_time_ms=execution_time_ms,
            metadata=metadata,
        )


class RAGService(Generic[T]):
    """
    Retrieval-Augmented Generation (RAG) service.

    This service provides RAG capabilities by combining vector search with
    prompt construction for LLM interactions. It uses PostgreSQL for efficient
    vector storage and retrieval.
    """

    def __init__(
        self,
        vector_search: VectorSearchService[T],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize RAG service.

        Args:
            vector_search: Vector search service to use for retrieval
            logger: Optional logger for diagnostics
        """
        self.vector_search = vector_search
        self.logger = logger or logging.getLogger(__name__)

    async def retrieve_context(
        self, query: str, limit: int = 5, threshold: float = 0.7
    ) -> Tuple[list[T], list[VectorSearchResult]]:
        """
        Retrieve relevant context for a query.

        Args:
            query: The query text
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold

        Returns:
            Tuple of (entities, search_results)
        """
        # Use vector search to find relevant context
        search_query = VectorQuery(query_text=query, limit=limit, threshold=threshold)

        search_results = await self.vector_search.search(search_query)

        # Extract entities from results
        entities = [
            result.entity for result in search_results if result.entity is not None
        ]

        return entities, search_results

    def format_context_for_prompt(self, entities: list[T]) -> str:
        """
        Format retrieved entities as context for an LLM prompt.

        Args:
            entities: The retrieved entities

        Returns:
            Formatted context string
        """
        # Default implementation - override this in subclasses
        # to format the context according to your entity structure

        context_parts = []

        for i, entity in enumerate(entities):
            # Convert entity to a string representation
            entity_dict = entity.model_dump()

            # Format as a numbered context item
            context_text = f"[{i+1}] "

            # Add ID
            if hasattr(entity, "id"):
                context_text += f"ID: {entity.id}\n"

            # Add fields that might be useful as context
            for field, value in entity_dict.items():
                if field == "id":
                    continue

                if isinstance(value, str) and len(value) > 0:
                    # Limit very long text fields
                    if len(value) > 500:
                        value = value[:500] + "..."
                    context_text += f"{field}: {value}\n"

            context_parts.append(context_text)

        # Join all context items with separators
        return "\n---\n".join(context_parts)

    async def create_rag_prompt(
        self, query: str, system_prompt: str, limit: int = 5, threshold: float = 0.7
    ) -> dict[str, str]:
        """
        Create a RAG prompt with retrieved context.

        Args:
            query: The user's query
            system_prompt: The system prompt
            limit: Maximum number of results to retrieve
            threshold: Minimum similarity threshold

        Returns:
            Dictionary with system_prompt and user_prompt keys
        """
        # Retrieve relevant context
        entities, _ = await self.retrieve_context(query, limit, threshold)

        # Format context
        context = self.format_context_for_prompt(entities)

        # Create user prompt with context and query
        user_prompt = f"""I need information based on the following context:

{context}

My question is: {query}"""

        return {"system_prompt": system_prompt, "user_prompt": user_prompt}
