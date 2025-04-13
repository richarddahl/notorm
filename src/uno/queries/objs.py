# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Models are the Business Logic Layer Objects

from typing import Optional, Dict, List, Tuple, Any
from typing_extensions import Self
from pydantic import model_validator

from uno.schema.schema import UnoSchemaConfig
from uno.obj import UnoObj
from uno.mixins import ObjectMixin
from uno.authorization.mixins import DefaultObjectMixin
from uno.queries.models import QueryPathModel, QueryValueModel, QueryModel
from uno.meta.objs import MetaRecord, MetaType
from uno.enums import (
    Include,
    Match,
)
from uno.settings import uno_settings
from uno.database.db import FilterParam
from uno.queries.filter import UnoFilter
from uno.errors import UnoError
from uno.core.errors.result import Result, Success, Failure


class QueryPath(UnoObj[QueryPathModel], ObjectMixin):
    # Class variables
    model = QueryPathModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "source_meta_type",
                "destination_meta_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "source_meta_type_id",
                "cypher_path",
                "target_meta_type_id",
                "data_type",
            ],
        ),
    }
    endpoints = ["List", "View"]

    # Fields
    source_meta_type_id: str
    source_meta_type: Optional[MetaType] = None
    target_meta_type_id: str
    destination_meta_type: Optional[MetaType] = None
    cypher_path: str
    data_type: str
    # lookups: list[str]

    def __str__(self) -> str:
        return self.cypher_path

    async def create_query_paths(self) -> None:
        """
        Asynchronously processes UnoObj filters to create query paths.

        Analyzes object relationships to create unique query paths and
        persists them to the database. This enables efficient querying
        across object relationships.

        Raises:
            Exception: If query path creation fails
        """
        try:
            query_paths = self._collect_query_paths()
            await self._persist_query_paths(query_paths)
        except Exception as e:
            self.logger.error(f"Error creating query paths: {e}")
            raise

    def _collect_query_paths(self) -> Dict[str, "QueryPath"]:
        """
        Collects unique query paths from UnoObj filters.

        Returns:
            Dictionary of unique query paths keyed by cypher path

        Raises:
            ValueError: If filter configuration is invalid
        """
        query_paths: Dict[str, QueryPath] = {}

        def add_query_path(fltr: UnoFilter, parent: Optional[UnoFilter] = None) -> None:
            """Add a query path from the given filter and parent."""
            source_meta_type = (
                parent.source_meta_type_id if parent else fltr.source_meta_type_id
            )

            if not source_meta_type or not fltr.target_meta_type_id:
                raise ValueError(f"Invalid filter configuration: {fltr}")

            query_path = QueryPath(
                source_meta_type_id=source_meta_type,
                target_meta_type_id=fltr.target_meta_type_id,
                cypher_path=fltr.cypher_path(parent=parent),
                data_type=fltr.data_type,
            )

            if query_path.cypher_path not in query_paths:
                query_paths[query_path.cypher_path] = query_path

        def process_filters(fltr: UnoFilter) -> None:
            """Process a filter and its children recursively."""
            stack: List[Tuple[UnoFilter, Optional[UnoFilter]]] = [(fltr, None)]
            visited = set()

            while stack:
                current_fltr, parent = stack.pop()
                path = current_fltr.cypher_path(parent=parent)

                if path in visited:
                    continue

                visited.add(path)
                add_query_path(current_fltr, parent)

                if current_fltr.source_meta_type_id != current_fltr.target_meta_type_id:
                    # Get the target object and process its children
                    if current_fltr.target_meta_type_id not in self.registry:
                        self.logger.warning(
                            f"Target meta type not found: {current_fltr.target_meta_type_id}"
                        )
                        continue

                    child_obj = self.registry[current_fltr.target_meta_type_id]
                    for child_fltr in current_fltr.children(obj=child_obj):
                        stack.append((child_fltr, current_fltr))

        # Process all registered objects
        for obj in self.registry.values():
            obj.filter_manager.create_filters_from_table(
                obj.model,
                obj.exclude_from_filters,
                obj.terminate_field_filters,
            )
            for fltr in obj.filter_manager.filters.values():
                process_filters(fltr)

        return query_paths

    async def _persist_query_paths(self, query_paths: Dict[str, "QueryPath"]) -> None:
        """
        Persists collected query paths to the database.

        Args:
            query_paths: Dictionary of QueryPath objects to persist

        Raises:
            Exception: If persistence fails
        """
        for qp in query_paths.values():
            try:
                # The merge method is assumed to be async and returns query_path and an action identifier
                qp_obj, action = await qp.merge()
                self.logger.info(f"QueryPath: {qp_obj.cypher_path}, action: {action}")
            except Exception as e:
                self.logger.error(f"Failed to persist query path {qp.cypher_path}: {e}")
                # Continue processing other paths even if one fails
                continue


class QueryValue(UnoObj[QueryValueModel], DefaultObjectMixin):
    # Class variables
    model = QueryValueModel
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "query_path",
                "values",
                "queries",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "include",
                "match",
                "lookup",
            ],
        ),
    }

    # Fields
    query_path_id: int
    query_path: Optional[QueryPath] = None
    include: Include = Include.INCLUDE
    match: Match = Match.AND
    lookup: str = "equal"
    values: Optional[list[MetaRecord]] = []
    queries: Optional[list["Query"]] = []

    @model_validator(mode="after")
    def model_validator(self) -> Self:
        self.lookup = self.lookup
        self.include = Include[self.include]
        self.match = Match[self.match]
        if not self.values and not self.queries:
            raise ValueError("Must have either values or queries")
        return self


class Query(UnoObj[QueryModel], DefaultObjectMixin):
    # Class variables
    model = QueryModel
    display_name_plural = "Queries"
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "group",
                "tenant",
                "query_meta_type",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "description",
                "query_meta_type_id",
                "include_values",
                "match_values",
                "include_queries",
                "match_queries",
            ],
        ),
    }
    terminate_filters = True

    # Fields
    id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    query_meta_type_id: Optional[str] = None
    query_meta_type: Optional[MetaType] = None
    include_values: Optional[Include] = Include.INCLUDE
    match_values: Optional[Match] = Match.AND
    include_queries: Optional[Include] = Include.INCLUDE
    match_queries: Optional[Match] = Match.AND

    def __str__(self) -> str:
        return self.name if self.name else f"Query {self.id}"

    @classmethod
    async def filter(cls, filters: FilterParam = None) -> List["Query"]:
        """
        Filter Query objects from the database.

        Args:
            filters: Filter parameters

        Returns:
            A list of Query instances
        """
        # Create the database factory
        db = cls().db

        # Filter models from the database
        models = await db.filter(filters=filters)

        # Convert to Query instances
        return [cls(**model) for model in models]
        
    async def execute(self) -> Result[List[str]]:
        """
        Execute the query and return matching record IDs.
        
        Returns:
            Result containing a list of matching record IDs or an error
        """
        from uno.queries.executor import get_query_executor
        
        executor = get_query_executor()
        return await executor.execute_query(self)
    
    async def check_record_match(self, record_id: str) -> Result[bool]:
        """
        Check if a specific record matches this query.
        
        Args:
            record_id: The record ID to check
            
        Returns:
            Result containing True if the record matches, False otherwise
        """
        from uno.queries.executor import get_query_executor
        
        executor = get_query_executor()
        return await executor.check_record_matches_query(self, record_id)
    
    async def count_matches(self) -> Result[int]:
        """
        Count the number of records that match this query.
        
        Returns:
            Result containing the count of matching records
        """
        from uno.queries.executor import get_query_executor
        
        executor = get_query_executor()
        return await executor.count_query_matches(self)
