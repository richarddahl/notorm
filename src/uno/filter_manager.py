# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Filter management component for UnoObj models.

This module provides functionality for creating and managing filters for UnoObj models.
"""

import datetime
import decimal
from typing import Dict, Type, Any, List, NamedTuple, Optional
from collections import OrderedDict, namedtuple

from pydantic import BaseModel, create_model
from fastapi import Query, HTTPException
from sqlalchemy import Column

from uno.errors import UnoError
from uno.filter import (
    UnoFilter,
    boolean_lookups,
    numeric_lookups,
    datetime_lookups,
    text_lookups,
)
from uno.utilities import (
    snake_to_title,
    snake_to_camel,
    snake_to_caps_snake,
)


class FilterValidationError(UnoError):
    """Error raised when a filter validation fails."""

    pass


class UnoFilterManager:
    """
    Manager for UnoObj filters.

    This class handles the creation and management of filters for UnoObj models.
    """

    def __init__(self):
        """Initialize the filter manager."""
        self.filters: Dict[str, UnoFilter] = {}

    def create_filters_from_table(
        self,
        model_class: Type[BaseModel],
        exclude_from_filters: bool = False,
        exclude_fields: List[str] = None,
    ) -> Dict[str, UnoFilter]:
        """
        Create filters from a model's table.

        Args:
            model_class: The model class to create filters from
            exclude_from_filters: Whether to exclude this model from filters
            exclude_fields: List of field names to exclude from filtering

        Returns:
            A dictionary of filter names to filter objects
        """
        if exclude_from_filters:
            return {}

        exclude_fields = exclude_fields or []
        filters = {}
        table = model_class.__table__

        for column in table.columns.values():
            if (
                column.info.get("graph_excludes", False)
                or column.name in exclude_fields
            ):
                continue

            if fltr := self._create_filter_from_column(column, table):
                filter_key = fltr.label
                if filter_key not in filters:
                    filters[filter_key] = fltr

        self.filters = filters
        return filters

    def _create_filter_from_column(
        self,
        column: Column,
        table,
    ) -> Optional[UnoFilter]:
        """
        Create a filter from a column.

        Args:
            column: The column to create a filter from
            table: The table the column belongs to

        Returns:
            A filter object if creation is successful, None otherwise
        """
        # Determine the lookups based on the column type
        if column.type.python_type == bool:
            lookups = boolean_lookups
        elif column.type.python_type in [
            int,
            decimal.Decimal,
            float,
        ]:
            lookups = numeric_lookups
        elif column.type.python_type in [
            datetime.date,
            datetime.datetime,
            datetime.time,
        ]:
            lookups = datetime_lookups
        else:
            lookups = text_lookups

        # Get the edge label from the column info or use the column name
        edge = column.info.get("edge", column.name)

        # Determine the source and target node labels and meta_types
        if column.foreign_keys:
            # If the column has foreign keys, use the foreign key to determine the
            # source and target node labels and meta_types
            source_node_label = snake_to_camel(column.table.name)
            source_meta_type_id = column.table.name
            target_node_label = snake_to_camel(
                list(column.foreign_keys)[0].column.table.name
            )
            target_meta_type_id = list(column.foreign_keys)[0].column.table.name
            label = snake_to_caps_snake(
                column.info.get(edge, column.name.replace("_id", ""))
            )
        else:
            # If the column does not have foreign keys, use the column name to determine
            # the source and target node labels and meta_types
            source_node_label = snake_to_camel(table.name)
            source_meta_type_id = table.name
            target_node_label = snake_to_camel(column.name)
            target_meta_type_id = source_meta_type_id
            label = snake_to_caps_snake(
                column.info.get(edge, column.name.replace("_id", ""))
            )

        return UnoFilter(
            source_node_label=source_node_label,
            source_meta_type_id=source_meta_type_id,
            label=label,
            target_node_label=target_node_label,
            target_meta_type_id=target_meta_type_id,
            data_type=column.type.python_type.__name__,
            raw_data_type=column.type.python_type,
            lookups=lookups,
            source_path_fragment=f"(s:{source_node_label})-[:{label}]",
            middle_path_fragment=f"(:{source_node_label})-[:{label}]",
            target_path_fragment=f"(t:{target_node_label})",
            documentation=column.doc or label,
        )

    def create_filter_params(
        self,
        model_class: Type[BaseModel],
    ) -> Type[BaseModel]:
        """
        Create a filter parameters model for a model class.

        Args:
            model_class: The model class to create filter parameters for

        Returns:
            A Pydantic model class for filter parameters
        """
        from uno.db.db import FilterParam  # Import here to avoid circular imports

        filter_names = list(self.filters.keys())
        filter_names.sort()

        try:
            order_by_choices = [name for name in model_class.model_fields.keys()]
        except AttributeError:
            # Handle case where model_fields might not be available
            order_by_choices = []

        # Create a dictionary of filter parameters
        model_filter_dict = OrderedDict(
            {
                "limit": (Any, None),  # Use Any for simplicity in this example
                "offset": (Any, None),
                "order_by": (Any, None),
            }
        )

        # Add the order_by.asc and order_by.desc "lookup" fields
        for direction in ["asc", "desc"]:
            model_filter_dict.update({f"order_by.{direction}": (Any, None)})

        # Add filters for each field
        for name in filter_names:
            fltr = self.filters[name]
            label = fltr.label.lower()

            # Add the base filter
            model_filter_dict.update({label: (Any, None)})

            # Add lookup-specific filters
            for lookup in fltr.lookups:
                label_ = f"{label}.{lookup.lower()}"
                model_filter_dict.update({label_: (Any, None)})

        return create_model(
            f"{model_class.__name__}FilterParam",
            **model_filter_dict,
            __base__=FilterParam,
        )

    def validate_filter_params(
        self,
        filter_params: BaseModel,
        model_class: Type[BaseModel],
    ) -> List[NamedTuple]:
        """
        Validate filter parameters.

        Args:
            filter_params: The filter parameters to validate
            model_class: The model class to validate against

        Returns:
            A list of validated filter tuples

        Raises:
            FilterValidationError: If validation fails
        """
        FilterTuple = namedtuple("FilterTuple", ["label", "val", "lookup"])
        filters = []

        # Get expected parameters
        expected_params = set([key.lower() for key in self.filters.keys()])
        expected_params.update(["limit", "offset", "order_by"])

        # Check for unexpected parameters
        unexpected_params = (
            set([key.split(".")[0] for key in filter_params.model_fields])
            - expected_params
        )
        if unexpected_params:
            unexpected_param_list = ", ".join(unexpected_params)
            raise FilterValidationError(
                f"Unexpected query parameter(s): {unexpected_param_list}. Check spelling and case.",
                "UNEXPECTED_FILTER_PARAMS",
            )

        # Process parameters
        for key, val in filter_params.model_dump().items():
            if val is None:
                continue

            filter_components = key.split(".")
            edge = filter_components[0]

            # Handle special parameters
            if edge in ["limit", "offset", "order_by"]:
                self._validate_special_param(
                    edge, val, filter_components, model_class, filters, FilterTuple
                )
                continue

            # Handle regular filters
            edge_upper = edge.upper()
            if edge_upper not in self.filters.keys():
                raise FilterValidationError(
                    f"Invalid filter key: {key}", "INVALID_FILTER_KEY"
                )

            lookup = filter_components[1] if len(filter_components) > 1 else "equal"
            if lookup not in self.filters[edge_upper].lookups:
                raise FilterValidationError(
                    f"Invalid filter lookup: {lookup}", "INVALID_FILTER_LOOKUP"
                )

            filters.append(FilterTuple(edge_upper, val, lookup))

        return filters

    def _validate_special_param(
        self,
        param_name: str,
        value: Any,
        components: List[str],
        model_class: Type[BaseModel],
        filters: List[NamedTuple],
        tuple_class: Type[NamedTuple],
    ) -> None:
        """
        Validate a special parameter (limit, offset, order_by).

        Args:
            param_name: The parameter name
            value: The parameter value
            components: The parameter components (for order_by.asc, etc.)
            model_class: The model class to validate against
            filters: The list of filters to append to
            tuple_class: The named tuple class to use for filters

        Raises:
            FilterValidationError: If validation fails
        """
        if param_name == "order_by":
            try:
                order_by_choices = [
                    name for name in model_class.view_schema.model_fields.keys()
                ]
            except AttributeError:
                order_by_choices = []

            if value not in order_by_choices:
                raise FilterValidationError(
                    f"Invalid order_by value: {value}. Must be one of {order_by_choices}.",
                    "INVALID_ORDER_BY_VALUE",
                )

            if len(components) > 1:
                if components[1] not in ["asc", "desc"]:
                    raise FilterValidationError(
                        f"Invalid order direction: {components[1]}. Must be 'asc' or 'desc'.",
                        "INVALID_ORDER_DIRECTION",
                    )
                filters.append(tuple_class(param_name, value, components[1]))
            else:
                # Default to 'asc' if not specified
                filters.append(tuple_class(param_name, value, "asc"))

        elif param_name in ["limit", "offset"]:
            if not isinstance(value, int) or value < 0:
                raise FilterValidationError(
                    f"Invalid {param_name} value: {value}. Must be a positive integer.",
                    f"INVALID_{param_name.upper()}_VALUE",
                )

            filters.append(tuple_class(param_name, value, param_name))
