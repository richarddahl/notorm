"""
Query parser for the filtering system.

This module provides utilities for parsing query parameters into filter criteria.
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import Query
from pydantic import BaseModel, ValidationError

from .models import (
    FilterCondition,
    FilterConditionGroup,
    FilterCriteria,
    FilterField,
    FilterOperator,
    SortDirection,
    SortField,
)
from .protocol import QueryParameter


class QueryParser:
    """
    Parser for converting query parameters to filter criteria.

    This class provides utilities for parsing query parameters into filter criteria.
    """

    @staticmethod
    def parse_filter_params(
        filter_field: list[str] | None = Query(
            None, description="Filter field in format field:operator:value"
        ),
        sort: list[str] | None = Query(
            None, description="Sort fields in format field:direction"
        ),
        limit: Optional[int] = Query(
            None, description="Maximum number of results to return"
        ),
        offset: Optional[int] = Query(None, description="Offset for pagination"),
    ) -> FilterCriteria:
        """
        Parse filter parameters from query parameters.

        Args:
            filter_field: List of filter fields in format field:operator:value
            sort: List of sort fields in format field:direction
            limit: Maximum number of results to return
            offset: Offset for pagination

        Returns:
            Filter criteria
        """
        # Parse filter fields
        conditions = []
        if filter_field:
            for field_str in filter_field:
                try:
                    parts = field_str.split(":", 2)
                    if len(parts) < 2:
                        continue

                    field_name = parts[0]
                    operator = parts[1]
                    value = parts[2] if len(parts) > 2 else None

                    # Convert value to appropriate type
                    if operator in ("is_null", "is_not_null"):
                        value = None
                    elif operator in ("in", "not_in"):
                        value = value.split(",") if value else []
                    elif operator == "between":
                        value = value.split(",", 1) if value else []
                        if len(value) == 2:
                            try:
                                value = [float(v) for v in value]
                            except ValueError:
                                pass
                    elif value is not None:
                        # Try to convert to number
                        try:
                            if "." in value:
                                value = float(value)
                            else:
                                value = int(value)
                        except ValueError:
                            # If not a number, try boolean
                            if value.lower() in ("true", "false"):
                                value = value.lower() == "true"

                    # Create filter field
                    filter_field = FilterField(
                        name=field_name,
                        operator=operator,
                        value=value,
                    )

                    # Add to conditions
                    conditions.append(
                        FilterCondition(
                            type="field",
                            field=filter_field,
                        )
                    )
                except ValueError:
                    continue

        # Parse sort fields
        sort_fields = []
        if sort:
            for sort_str in sort:
                try:
                    parts = sort_str.split(":", 1)
                    field_name = parts[0]
                    direction = parts[1].lower() if len(parts) > 1 else "asc"

                    # Create sort field
                    sort_field = SortField(
                        name=field_name,
                        direction=(
                            SortDirection.ASCENDING
                            if direction == "asc"
                            else SortDirection.DESCENDING
                        ),
                    )

                    # Add to sort fields
                    sort_fields.append(sort_field)
                except ValueError:
                    continue

        # Create filter criteria
        criteria = FilterCriteria(
            conditions=conditions,
            sort=sort_fields or None,
            limit=limit,
            offset=offset,
        )

        return criteria

    @staticmethod
    def parse_json_filter(filter_json: dict[str, Any]) -> FilterCriteria:
        """
        Parse filter criteria from JSON.

        Args:
            filter_json: Filter criteria as JSON

        Returns:
            Filter criteria
        """
        try:
            return FilterCriteria.model_validate(filter_json)
        except ValidationError as e:
            raise ValueError(f"Invalid filter criteria: {e}")

    @staticmethod
    def convert_to_query_parameters(criteria: FilterCriteria) -> list[QueryParameter]:
        """
        Convert filter criteria to query parameters.

        Args:
            criteria: Filter criteria

        Returns:
            List of query parameters
        """
        parameters = []

        # Process conditions
        conditions = criteria.conditions
        if not isinstance(conditions, list):
            conditions = [conditions]

        for condition in conditions:
            params = QueryParser._process_condition(condition)
            parameters.extend(params)

        return parameters

    @staticmethod
    def _process_condition(condition: FilterCondition) -> list[QueryParameter]:
        """
        Process a filter condition.

        Args:
            condition: Filter condition

        Returns:
            List of query parameters
        """
        parameters = []

        if condition.type == "field" and condition.field:
            # Field condition
            parameters.append(
                QueryParameter(
                    field=condition.field.name,
                    operator=condition.field.operator,
                    value=condition.field.value,
                )
            )
        elif condition.type == "group" and condition.group:
            # Group condition
            for subcondition in condition.group.conditions:
                params = QueryParser._process_condition(subcondition)
                parameters.extend(params)

        return parameters
