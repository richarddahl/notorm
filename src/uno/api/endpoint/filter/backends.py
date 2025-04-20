"""
Filter backends for the unified endpoint framework.

This module provides filter backends for the unified endpoint framework,
including a SQL backend and a graph backend using Apache AGE.
"""

import logging
from typing import Any, Dict, List, Optional, Union, cast

from uno.api.endpoint.filter.protocol import FilterBackend, QueryParameter
from uno.api.endpoint.filter.models import FilterOperator

logger = logging.getLogger(__name__)


class SqlFilterBackend(FilterBackend):
    """
    SQL filter backend.

    This backend uses SQL queries for filtering entities. It works with any SQL database.
    """

    def __init__(self, session_factory):
        """
        Initialize a new SQL filter backend.

        Args:
            session_factory: Factory for creating database sessions
        """
        self.session_factory = session_factory

    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
        *,
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[list[str], Optional[int]]:
        """
        Filter entities based on criteria using SQL.

        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities

        Returns:
            Tuple of (list of entity IDs, total count if include_count is True)
        """
        # Get a database session
        async with self.session_factory() as session:
            # Build SQL query
            query = await self._build_sql_query(
                session=session,
                entity_type=entity_type,
                filter_criteria=filter_criteria,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )

            # Execute query to get entity IDs
            result = await session.execute(query)
            entity_ids = [row[0] for row in result.fetchall()]

            # Get total count if requested
            total = None
            if include_count:
                total = await self.count_entities(entity_type, filter_criteria)

            return entity_ids, total

    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
    ) -> int:
        """
        Count entities based on criteria using SQL.

        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria as a dictionary or list of query parameters

        Returns:
            Total count of matching entities
        """
        # Get a database session
        async with self.session_factory() as session:
            # Build SQL count query
            query = await self._build_sql_count_query(
                session=session,
                entity_type=entity_type,
                filter_criteria=filter_criteria,
            )

            # Execute query to get count
            result = await session.execute(query)
            count = result.scalar()

            return count or 0

    async def _build_sql_query(
        self,
        session,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ):
        """
        Build a SQL query for filtering entities.

        Args:
            session: Database session
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions
            limit: Optional maximum number of results
            offset: Optional offset for pagination

        Returns:
            SQL query
        """
        # Implementation would depend on the specific ORM or database library used
        # This is a placeholder that would need to be implemented
        # with the actual SQL query building logic
        pass

    async def _build_sql_count_query(
        self,
        session,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
    ):
        """
        Build a SQL query for counting entities.

        Args:
            session: Database session
            entity_type: The type of entity to count
            filter_criteria: Filter criteria

        Returns:
            SQL count query
        """
        # Implementation would depend on the specific ORM or database library used
        # This is a placeholder that would need to be implemented
        # with the actual SQL count query building logic
        pass


class GraphFilterBackend(FilterBackend):
    """
    Apache AGE graph filter backend.

    This backend uses the Apache AGE knowledge graph for filtering entities.
    It offers more powerful relationship-based filtering capabilities than SQL.
    """

    def __init__(self, session_factory, fallback_backend=None):
        """
        Initialize a new graph filter backend.

        Args:
            session_factory: Factory for creating database sessions
            fallback_backend: Optional backend to use if Apache AGE is not available
        """
        self.session_factory = session_factory
        self.fallback_backend = fallback_backend

        # Check if Apache AGE is available
        self.age_available = self._check_age_available()

        if not self.age_available and not self.fallback_backend:
            logger.warning(
                "Apache AGE is not available and no fallback backend was provided. "
                "Filtering operations will fail. Consider providing a fallback backend "
                "like SqlFilterBackend."
            )

    def _check_age_available(self) -> bool:
        """
        Check if Apache AGE is available in the database.

        Returns:
            True if Apache AGE is available, False otherwise
        """
        # This would check if Apache AGE is installed in the database
        # For now, we assume it is available
        return True

    async def filter_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
        *,
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_count: bool = True,
    ) -> tuple[list[str], Optional[int]]:
        """
        Filter entities based on criteria using Apache AGE.

        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria as a dictionary or list of query parameters
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions (asc or desc) for each sort field
            limit: Optional maximum number of results to return
            offset: Optional offset for pagination
            include_count: Whether to include the total count of matching entities

        Returns:
            Tuple of (list of entity IDs, total count if include_count is True)
        """
        # If Apache AGE is not available, use fallback backend
        if not self.age_available:
            if self.fallback_backend:
                return await self.fallback_backend.filter_entities(
                    entity_type=entity_type,
                    filter_criteria=filter_criteria,
                    sort_by=sort_by,
                    sort_dir=sort_dir,
                    limit=limit,
                    offset=offset,
                    include_count=include_count,
                )
            else:
                raise RuntimeError(
                    "Apache AGE is not available and no fallback backend was provided."
                )

        # Get a database session
        async with self.session_factory() as session:
            # Build and execute Cypher query
            cypher_query, params = self._build_cypher_query(
                entity_type=entity_type,
                filter_criteria=filter_criteria,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )

            # Execute Cypher query
            result = await session.execute(
                f"SELECT * FROM cypher('graph', $cypher, $params) AS (id agtype)",
                {"cypher": cypher_query, "params": params},
            )

            # Extract entity IDs from result
            entity_ids = [row[0] for row in result.fetchall()]

            # Get total count if requested
            total = None
            if include_count:
                total = await self.count_entities(entity_type, filter_criteria)

            return entity_ids, total

    async def count_entities(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
    ) -> int:
        """
        Count entities based on criteria using Apache AGE.

        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria as a dictionary or list of query parameters

        Returns:
            Total count of matching entities
        """
        # If Apache AGE is not available, use fallback backend
        if not self.age_available:
            if self.fallback_backend:
                return await self.fallback_backend.count_entities(
                    entity_type=entity_type,
                    filter_criteria=filter_criteria,
                )
            else:
                raise RuntimeError(
                    "Apache AGE is not available and no fallback backend was provided."
                )

        # Get a database session
        async with self.session_factory() as session:
            # Build and execute Cypher count query
            cypher_query, params = self._build_cypher_count_query(
                entity_type=entity_type,
                filter_criteria=filter_criteria,
            )

            # Execute Cypher query
            result = await session.execute(
                f"SELECT * FROM cypher('graph', $cypher, $params) AS (count agtype)",
                {"cypher": cypher_query, "params": params},
            )

            # Extract count from result
            count = result.scalar()

            return count or 0

    def _build_cypher_query(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
        sort_by: list[str] | None = None,
        sort_dir: list[str] | None = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a Cypher query for filtering entities.

        Args:
            entity_type: The type of entity to filter
            filter_criteria: Filter criteria
            sort_by: Optional fields to sort by
            sort_dir: Optional sort directions
            limit: Optional maximum number of results
            offset: Optional offset for pagination

        Returns:
            Tuple of (Cypher query, query parameters)
        """
        # Convert filter criteria to list of QueryParameter objects
        if isinstance(filter_criteria, dict):
            parameters = []
            for field, value in filter_criteria.items():
                if isinstance(value, dict) and "operator" in value and "value" in value:
                    parameters.append(
                        QueryParameter(
                            field=field,
                            operator=value["operator"],
                            value=value["value"],
                        )
                    )
                else:
                    parameters.append(
                        QueryParameter(
                            field=field,
                            operator="eq",
                            value=value,
                        )
                    )
        else:
            parameters = filter_criteria

        # Start building the Cypher query
        query = f"MATCH (n:{entity_type})"

        # Add filter conditions
        if parameters:
            conditions = []
            params = {}

            for i, param in enumerate(parameters):
                condition, param_values = self._build_condition(param, i)
                conditions.append(condition)
                params.update(param_values)

            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
        else:
            params = {}

        # Add sorting
        if sort_by and sort_dir:
            sort_clauses = []
            for i, field in enumerate(sort_by):
                direction = sort_dir[i] if i < len(sort_dir) else "asc"
                sort_clauses.append(f"n.{field} {direction}")

            if sort_clauses:
                query += f" ORDER BY {', '.join(sort_clauses)}"

        # Add limit and offset
        if limit is not None:
            query += f" LIMIT {limit}"

        if offset is not None:
            query += f" SKIP {offset}"

        # Return only the ID
        query += " RETURN n.id"

        return query, params

    def _build_cypher_count_query(
        self,
        entity_type: str,
        filter_criteria: Union[Dict[str, Any], list[QueryParameter]],
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a Cypher query for counting entities.

        Args:
            entity_type: The type of entity to count
            filter_criteria: Filter criteria

        Returns:
            Tuple of (Cypher count query, query parameters)
        """
        # Convert filter criteria to list of QueryParameter objects
        if isinstance(filter_criteria, dict):
            parameters = []
            for field, value in filter_criteria.items():
                if isinstance(value, dict) and "operator" in value and "value" in value:
                    parameters.append(
                        QueryParameter(
                            field=field,
                            operator=value["operator"],
                            value=value["value"],
                        )
                    )
                else:
                    parameters.append(
                        QueryParameter(
                            field=field,
                            operator="eq",
                            value=value,
                        )
                    )
        else:
            parameters = filter_criteria

        # Start building the Cypher query
        query = f"MATCH (n:{entity_type})"

        # Add filter conditions
        if parameters:
            conditions = []
            params = {}

            for i, param in enumerate(parameters):
                condition, param_values = self._build_condition(param, i)
                conditions.append(condition)
                params.update(param_values)

            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
        else:
            params = {}

        # Return count
        query += " RETURN count(n)"

        return query, params

    def _build_condition(
        self, param: QueryParameter, index: int
    ) -> tuple[str, Dict[str, Any]]:
        """
        Build a Cypher condition for a query parameter.

        Args:
            param: Query parameter
            index: Parameter index for generating unique parameter names

        Returns:
            Tuple of (condition string, parameter values)
        """
        field = param.field
        operator = param.operator
        value = param.value
        param_name = f"p{index}"
        params = {}

        # Handle different operators
        if operator == FilterOperator.EQUAL or operator == "eq":
            condition = f"n.{field} = ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.NOT_EQUAL or operator == "ne":
            condition = f"n.{field} <> ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.GREATER_THAN or operator == "gt":
            condition = f"n.{field} > ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.GREATER_THAN_OR_EQUAL or operator == "gte":
            condition = f"n.{field} >= ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.LESS_THAN or operator == "lt":
            condition = f"n.{field} < ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.LESS_THAN_OR_EQUAL or operator == "lte":
            condition = f"n.{field} <= ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.IN or operator == "in":
            condition = f"n.{field} IN ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.NOT_IN or operator == "not_in":
            condition = f"NOT n.{field} IN ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.CONTAINS or operator == "contains":
            condition = f"n.{field} CONTAINS ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.STARTS_WITH or operator == "starts_with":
            condition = f"n.{field} STARTS WITH ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.ENDS_WITH or operator == "ends_with":
            condition = f"n.{field} ENDS WITH ${param_name}"
            params[param_name] = value
        elif operator == FilterOperator.IS_NULL or operator == "is_null":
            condition = f"n.{field} IS NULL"
        elif operator == FilterOperator.IS_NOT_NULL or operator == "is_not_null":
            condition = f"n.{field} IS NOT NULL"
        elif operator == FilterOperator.BETWEEN or operator == "between":
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError(
                    f"Operator 'between' requires a list of 2 values, got {value}"
                )
            condition = (
                f"n.{field} >= ${param_name}_min AND n.{field} <= ${param_name}_max"
            )
            params[f"{param_name}_min"] = value[0]
            params[f"{param_name}_max"] = value[1]
        else:
            raise ValueError(f"Unsupported operator: {operator}")

        return condition, params
