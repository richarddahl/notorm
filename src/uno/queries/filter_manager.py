# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Filter management component for UnoObj models.

This module provides functionality for creating and managing filters for UnoObj models.
"""

import datetime
import decimal
from typing import Dict, Type, Any, List, NamedTuple, Optional, cast, Set, Tuple, Union
from collections import OrderedDict, namedtuple

from pydantic import BaseModel, create_model, Field
from fastapi import Query, HTTPException
from sqlalchemy import Column, Table

from uno.errors import UnoError, ValidationError, ValidationContext
from uno.queries.filter import (
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
from uno.protocols import FilterManagerProtocol


class FilterValidationError(ValidationError):
    """Error raised when a filter validation fails."""
    pass


class UnoFilterManager(FilterManagerProtocol):
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
        exclude_fields: Optional[List[str]] = None,
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
        filters: Dict[str, UnoFilter] = {}
        
        # Handle case where model_class might not have __table__ attribute
        if not hasattr(model_class, "__table__"):
            return filters
            
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
        table: Table,
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
        try:
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
        except (AttributeError, TypeError):
            # Default to text lookups if we can't determine the type
            lookups = text_lookups

        # Get the edge label from the column info or use the column name
        edge = column.info.get("edge", column.name)

        # Determine the source and target node labels and meta_types
        try:
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
        except (AttributeError, TypeError, IndexError):
            # If there's an error determining the labels, return None
            return None

        return UnoFilter(
            source_node_label=source_node_label,
            source_meta_type_id=source_meta_type_id,
            label=label,
            target_node_label=target_node_label,
            target_meta_type_id=target_meta_type_id,
            data_type=getattr(column.type, "python_type", str).__name__,
            raw_data_type=getattr(column.type, "python_type", str),
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
        from uno.database.db import FilterParam  # Import here to avoid circular imports

        filter_names = list(self.filters.keys())
        filter_names.sort()

        # Get the fields from the model class
        try:
            order_by_choices = list(model_class.model_fields.keys())
        except AttributeError:
            # Handle case where model_fields might not be available
            order_by_choices = []

        # Create a dictionary of filter parameters
        model_filter_dict = OrderedDict(
            {
                "limit": (Optional[int], Field(None, description="Maximum number of results to return")),
                "offset": (Optional[int], Field(None, description="Number of results to skip")),
                "order_by": (Optional[str], Field(None, description="Field to order by")),
            }
        )

        # Add the order_by.asc and order_by.desc "lookup" fields
        for direction in ["asc", "desc"]:
            model_filter_dict.update({
                f"order_by.{direction}": (
                    Optional[str],
                    Field(None, description=f"Field to order by in {direction}ending order")
                )
            })

        # Add filters for each field
        for name in filter_names:
            fltr = self.filters[name]
            label = fltr.label.lower()

            # Add the base filter with proper type annotation
            python_type = self._get_python_type_from_data_type(fltr.data_type)
            model_filter_dict.update({
                label: (
                    Optional[python_type],
                    Field(None, description=f"Filter by {label}")
                )
            })

            # Add lookup-specific filters
            for lookup in fltr.lookups:
                label_ = f"{label}.{lookup.lower()}"
                model_filter_dict.update({
                    label_: (
                        Optional[python_type],
                        Field(None, description=f"Filter by {label} with {lookup} comparison")
                    )
                })

        # Create and return the filter parameters model
        filter_model = create_model(
            f"{model_class.__name__}FilterParam",
            **model_filter_dict,
            __base__=FilterParam,
        )
        
        return cast(Type[BaseModel], filter_model)
        
    def _get_python_type_from_data_type(self, data_type: str) -> Type:
        """
        Get the Python type from a data type string.
        
        Args:
            data_type: The data type string
            
        Returns:
            The Python type
        """
        type_mapping = {
            "str": str,
            "int": int,
            "float": float,
            "bool": bool,
            "dict": dict,
            "list": list,
            "datetime": datetime.datetime,
            "date": datetime.date,
            "time": datetime.time,
            "Decimal": decimal.Decimal,
        }
        
        return type_mapping.get(data_type, Any)

    def validate_filter_params(
        self,
        filter_params: BaseModel,
        model_class: Type[BaseModel],
    ) -> List[Tuple[str, Any, str]]:
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
        # Create a validation context
        context = ValidationContext(f"{model_class.__name__}Filters")
        
        # Create a named tuple for the filter
        FilterTuple = namedtuple("FilterTuple", ["label", "val", "lookup"])
        filters: List[FilterTuple] = []

        # Get expected parameters
        expected_params = set([key.lower() for key in self.filters.keys()])
        expected_params.update(["limit", "offset", "order_by"])

        # Check for unexpected parameters
        param_fields = getattr(filter_params, "model_fields", {})
        filter_param_fields = set([key.split(".")[0] for key in param_fields])
        unexpected_params = filter_param_fields - expected_params
        
        if unexpected_params:
            unexpected_param_list = ", ".join(unexpected_params)
            context.add_error(
                "",
                f"Unexpected query parameter(s): {unexpected_param_list}. Check spelling and case.",
                "UNEXPECTED_FILTER_PARAMS"
            )

        # Process parameters
        for key, val in filter_params.model_dump().items():
            if val is None:
                continue

            filter_components = key.split(".")
            edge = filter_components[0]

            # Handle special parameters
            if edge in ["limit", "offset", "order_by"]:
                try:
                    self._validate_special_param(
                        edge, val, filter_components, model_class, filters, FilterTuple, context
                    )
                except Exception as e:
                    context.add_error(key, str(e), "SPECIAL_PARAM_VALIDATION_ERROR", val)
                continue

            # Handle regular filters
            edge_upper = edge.upper()
            if edge_upper not in self.filters.keys():
                context.add_error(
                    key,
                    f"Invalid filter key: {key}",
                    "INVALID_FILTER_KEY",
                    val
                )
                continue

            lookup = filter_components[1] if len(filter_components) > 1 else "equal"
            if lookup not in self.filters[edge_upper].lookups:
                context.add_error(
                    key, 
                    f"Invalid filter lookup: {lookup}",
                    "INVALID_FILTER_LOOKUP",
                    val
                )
                continue

            # Validate the value type
            expected_type = self._get_python_type_from_data_type(self.filters[edge_upper].data_type)
            if not isinstance(val, (expected_type, type(None))):
                context.add_error(
                    key,
                    f"Invalid value type for {key}: expected {expected_type.__name__}, got {type(val).__name__}",
                    "INVALID_VALUE_TYPE",
                    val
                )
                continue

            filters.append(FilterTuple(edge_upper, val, lookup))

        # Raise if there are validation errors
        context.raise_if_errors()
        
        return filters

    def _validate_special_param(
        self,
        param_name: str,
        value: Any,
        components: List[str],
        model_class: Type[BaseModel],
        filters: List[NamedTuple],
        tuple_class: Type[NamedTuple],
        context: ValidationContext,
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
            context: The validation context

        Raises:
            ValidationError: If validation fails
        """
        if param_name == "order_by":
            # Get the fields from the model's view schema
            try:
                order_by_choices = [
                    name for name in getattr(model_class, "view_schema", model_class).model_fields.keys()
                ]
            except AttributeError:
                # Handle case where view_schema or model_fields might not be available
                order_by_choices = []

            if value not in order_by_choices:
                context.add_error(
                    f"{param_name}",
                    f"Invalid order_by value: {value}. Must be one of {order_by_choices}.",
                    "INVALID_ORDER_BY_VALUE",
                    value
                )
                return

            if len(components) > 1:
                if components[1] not in ["asc", "desc"]:
                    context.add_error(
                        f"{param_name}.{components[1]}",
                        f"Invalid order direction: {components[1]}. Must be 'asc' or 'desc'.",
                        "INVALID_ORDER_DIRECTION",
                        value
                    )
                    return
                filters.append(tuple_class(param_name, value, components[1]))
            else:
                # Default to 'asc' if not specified
                filters.append(tuple_class(param_name, value, "asc"))

        elif param_name in ["limit", "offset"]:
            if not isinstance(value, int) or value < 0:
                context.add_error(
                    param_name,
                    f"Invalid {param_name} value: {value}. Must be a positive integer.",
                    f"INVALID_{param_name.upper()}_VALUE",
                    value
                )
                return

            filters.append(tuple_class(param_name, value, param_name))