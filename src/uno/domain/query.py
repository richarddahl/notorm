"""
Query system for domain objects.

This module provides a query system for retrieving domain objects with
complex filtering and projection capabilities.
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from abc import ABC, abstractmethod

from pydantic import BaseModel, create_model

from uno.domain.core import Entity
from uno.core.base.respository import Repository
from uno.queries.filter_manager import FilterManager


T = TypeVar("T", bound=Entity)
Q = TypeVar("Q", bound="QuerySpecification")


class QuerySpecification(BaseModel):
    """
    Base class for query specifications.

    Query specifications define the parameters for querying domain objects,
    including filters, sorting, pagination, and field selection.
    """

    filters: dict[str, Any] | None = None
    order_by: list[str] | None = None
    limit: int | None = None
    offset: Optional[int] = 0
    include: list[str] | None = None
    exclude: list[str] | None = None


class QueryResult(BaseModel, Generic[T]):
    """
    Result of a query operation.

    Contains the items matched by the query and metadata about the result.
    """

    items: list[T]
    total_count: int
    page_size: int | None = None
    page: int | None = None
    total_pages: int | None = None


class QueryExecutor(Generic[T, Q], ABC):
    """
    Abstract base class for query executors.

    Query executors take a query specification and return a query result,
    abstracting the details of how the query is executed.
    """

    def __init__(self, entity_type: Type[T], logger: logging.Logger | None = None):
        """
        Initialize a query executor.

        Args:
            entity_type: The type of entity this executor queries
            logger: Optional logger for diagnostic information
        """
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)

    @abstractmethod
    async def execute(self, query: Q) -> QueryResult[T]:
        """
        Execute a query and return the results.

        Args:
            query: The query specification to execute

        Returns:
            A query result containing the matched items and metadata
        """
        pass

    def select_fields(
        self,
        entity: T,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Select specific fields from an entity.

        Args:
            entity: The entity to process
            include: Optional list of fields to include (if not specified, include all)
            exclude: Optional list of fields to exclude

        Returns:
            A dictionary representation of the entity with the specified fields
        """
        # Start with all fields
        entity_dict = entity.model_dump()

        # If include is specified, keep only those fields
        if include:
            entity_dict = {k: v for k, v in entity_dict.items() if k in include}

        # If exclude is specified, remove those fields
        if exclude:
            entity_dict = {k: v for k, v in entity_dict.items() if k not in exclude}

        return entity_dict


class RepositoryQueryExecutor(QueryExecutor[T, Q]):
    """
    Query executor that uses a repository for data access.

    This executor leverages the repository pattern to execute queries against
    the domain model.
    """

    def __init__(
        self,
        entity_type: Type[T],
        repository: Repository[T],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize a repository query executor.

        Args:
            entity_type: The type of entity this executor queries
            repository: The repository to use for data access
            logger: Optional logger for diagnostic information
        """
        super().__init__(entity_type, logger)
        self.repository = repository

    async def execute(self, query: Q) -> QueryResult[T]:
        """
        Execute a query using the repository.

        Args:
            query: The query specification to execute

        Returns:
            A query result containing the matched items and metadata
        """
        # Retrieve the items
        items = await self.repository.list(
            filters=query.filters,
            order_by=query.order_by,
            limit=query.limit,
            offset=query.offset,
        )

        # Get the total count for pagination
        total_count = await self.repository.count(filters=query.filters)

        # Calculate pagination metadata
        page_size = query.limit
        page = None
        total_pages = None

        if page_size:
            page = (query.offset or 0) // page_size + 1
            total_pages = (total_count + page_size - 1) // page_size

        # Select specific fields if includes or excludes are specified
        if query.include or query.exclude:
            filtered_items = []
            for item in items:
                filtered_item = self.select_fields(item, query.include, query.exclude)
                # Create a new entity with only the selected fields
                filtered_entity = self.entity_type.model_validate(filtered_item)
                filtered_items.append(filtered_entity)
            items = filtered_items

        return QueryResult(
            items=items,
            total_count=total_count,
            page_size=page_size,
            page=page,
            total_pages=total_pages,
        )


class FilterQueryExecutor(QueryExecutor[T, Q]):
    """
    Query executor that uses FilterManager for complex filtering.

    This executor leverages Uno's FilterManager for executing complex queries
    with graph-based filtering.
    """

    def __init__(
        self,
        entity_type: Type[T],
        filter_manager: FilterManager,
        repository: Repository[T],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize a filter query executor.

        Args:
            entity_type: The type of entity this executor queries
            filter_manager: The filter manager to use for query processing
            repository: The repository to use for data access
            logger: Optional logger for diagnostic information
        """
        super().__init__(entity_type, logger)
        self.filter_manager = filter_manager
        self.repository = repository

    async def execute(self, query: Q) -> QueryResult[T]:
        """
        Execute a query using the filter manager and repository.

        Args:
            query: The query specification to execute

        Returns:
            A query result containing the matched items and metadata
        """
        # Process filters through the filter manager
        filter_params = self._prepare_filter_params(query.filters or {})

        # Get the filtered IDs
        filter_results = await self.filter_manager.apply_filters(filter_params)

        if not filter_results or not filter_results.ids:
            # No matching items
            return QueryResult(
                items=[], total_count=0, page_size=query.limit, page=1, total_pages=0
            )

        # Add ID filter to repository query
        id_filters = {"id": {"in": filter_results.ids}}

        # Apply offset and limit
        ids_subset = filter_results.ids
        if query.offset:
            ids_subset = ids_subset[query.offset :]
        if query.limit:
            ids_subset = ids_subset[: query.limit]

        # Retrieve the items by ID
        items = []
        for item_id in ids_subset:
            item = await self.repository.get(item_id)
            if item:
                items.append(item)

        # Apply ordering if specified
        if query.order_by:
            # Get the first ordering field and direction
            order_field = query.order_by[0]
            descending = order_field.startswith("-")
            if descending:
                order_field = order_field[1:]

            # Sort the items
            items.sort(key=lambda x: getattr(x, order_field), reverse=descending)

        # Select specific fields if includes or excludes are specified
        if query.include or query.exclude:
            filtered_items = []
            for item in items:
                filtered_item = self.select_fields(item, query.include, query.exclude)
                # Create a new entity with only the selected fields
                filtered_entity = self.entity_type.model_validate(filtered_item)
                filtered_items.append(filtered_entity)
            items = filtered_items

        return QueryResult(
            items=items,
            total_count=len(filter_results.ids),
            page_size=query.limit,
            page=(query.offset or 0) // query.limit + 1 if query.limit else 1,
            total_pages=(
                (len(filter_results.ids) + query.limit - 1) // query.limit
                if query.limit
                else 1
            ),
        )

    def _prepare_filter_params(self, filters: dict[str, Any]) -> dict[str, Any]:
        """
        Prepare filter parameters for the filter manager.

        Args:
            filters: The filters from the query

        Returns:
            Processed filter parameters for the filter manager
        """
        # Transform the filters to the format expected by the filter manager
        filter_params = {}

        for key, value in filters.items():
            if isinstance(value, dict) and "lookup" in value and "val" in value:
                # Already in the right format
                filter_params[key] = value
            else:
                # Create an equals lookup by default
                filter_params[key] = {"lookup": "eq", "val": value}

        return filter_params


class QueryService(Generic[T, Q]):
    """
    Service for executing queries against domain objects.

    This service provides a high-level interface for querying domain objects
    with various query executors.
    """

    def __init__(
        self,
        entity_type: Type[T],
        query_type: Type[Q],
        executors: list[QueryExecutor[T, Q]],
        logger: logging.Logger | None = None,
    ):
        """
        Initialize a query service.

        Args:
            entity_type: The type of entity this service queries
            query_type: The type of query specification this service accepts
            executors: Query executors to use for query execution
            logger: Optional logger for diagnostic information
        """
        self.entity_type = entity_type
        self.query_type = query_type
        self.executors = executors
        self.logger = logger or logging.getLogger(__name__)

    async def query(self, query_params: Union[Q, dict[str, Any]]) -> QueryResult[T]:
        """
        Execute a query and return the results.

        Args:
            query_params: The query parameters to execute

        Returns:
            A query result containing the matched items and metadata
        """
        # Convert dict to query specification if needed
        query = (
            query_params
            if isinstance(query_params, self.query_type)
            else self.query_type(**query_params)
        )

        # Execute the query using the first executor
        if not self.executors:
            raise ValueError("No query executors configured")

        return await self.executors[0].execute(query)

    def create_field_subset_model(
        self,
        name: str,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> Type[BaseModel]:
        """
        Create a Pydantic model with a subset of fields from the entity.

        Args:
            name: The name for the field subset model
            include: Optional list of fields to include
            exclude: Optional list of fields to exclude

        Returns:
            A Pydantic model class with the specified fields
        """
        # Get the entity's field definitions
        entity_fields = self.entity_type.model_fields

        # Apply include/exclude filters
        if include:
            fields = {k: entity_fields[k] for k in include if k in entity_fields}
        elif exclude:
            fields = {k: v for k, v in entity_fields.items() if k not in exclude}
        else:
            fields = entity_fields

        # Create a new model
        return create_model(f"{self.entity_type.__name__}{name}Subset", **fields)
