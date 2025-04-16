# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Filter management component for Domain entities and database models.

This module provides functionality for creating and managing filters for Domain entities and database models,
with performance optimizations for common filter patterns including:

- Filter generation caching for commonly-used models
- Optimized filter validation for large result sets
- Cached model schema analysis for faster filter creation
- Intelligent filter key generation for repeated filter operations
"""

import datetime
import decimal
import functools
import hashlib
import json
import logging
import time
from typing import Dict, Type, Any, List, NamedTuple, Optional, cast, Set, Tuple, Union, TYPE_CHECKING, Callable
from collections import OrderedDict, namedtuple

from pydantic import BaseModel, create_model, Field
from fastapi import Query, HTTPException
from sqlalchemy import Column, Table

from uno.core.errors import ValidationContext
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
from uno.core.protocols.filter_protocols import UnoFilterProtocol
from uno.core.types import FilterParam
from uno.queries.errors import FilterError

# Use TYPE_CHECKING for imports that are only needed for type annotations
if TYPE_CHECKING:
    from uno.core.protocols import FilterManagerProtocol
    from uno.core.caching import CacheManager
else:
    # Runtime import from the core protocols
    from uno.core.protocols import FilterManagerProtocol
    from uno.core.caching import get_cache_manager

# Cache configuration
FILTER_CACHE_ENABLED = True
FILTER_CACHE_TTL = 3600  # 1 hour default TTL for filter definitions
FILTER_CACHE_MAX_SIZE = 500  # Max cached filter definitions
FILTER_MODEL_CACHE_TTL = 7200  # 2 hours for filter parameter models
VALIDATION_RESULT_CACHE_TTL = 300  # 5 minutes for validation results



class UnoFilterManager(FilterManagerProtocol):
    """
    Manager for domain entity and database model filters.

    This class handles the creation and management of filters for domain entities and database models,
    with performance optimizations including:
    
    - Caching of generated filters to avoid repeated processing
    - Optimized filter lookup and validation
    - Model schema caching for faster filter parameter generation
    - Intelligent cache invalidation based on model changes
    """

    # Class-level caches for static filters and parameter models
    _filter_cache: Dict[str, Dict[str, UnoFilterProtocol]] = {}
    _model_cache: Dict[str, Type[BaseModel]] = {}
    _validation_cache: Dict[str, List[Tuple[str, Any, str]]] = {}
    _column_type_cache: Dict[str, Dict[str, Any]] = {}
    
    # Cache management timestamps
    _last_cleanup = time.time()
    _cache_hits = 0
    _cache_misses = 0

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the filter manager.
        
        Args:
            logger: Optional logger for diagnostic output
        """
        self.filters: Dict[str, UnoFilterProtocol] = {}
        self.logger = logger or logging.getLogger(__name__)
        
        # Perform periodic cache cleanup on instantiation
        if time.time() - self._last_cleanup > 3600:  # 1 hour
            self._cleanup_caches()
    
    def _cleanup_caches(self) -> None:
        """Perform periodic cleanup of internal caches to prevent memory bloat."""
        now = time.time()
        
        # Only perform cleanup if another instance hasn't done it recently
        if now - self._last_cleanup < 3600:  # 1 hour
            return
            
        try:
            # Clean up filter cache if too large
            if len(self._filter_cache) > FILTER_CACHE_MAX_SIZE:
                # Simple LRU-like implementation - keep newest 3/4 of entries
                keep_count = int(FILTER_CACHE_MAX_SIZE * 0.75)
                self._filter_cache = dict(
                    sorted(self._filter_cache.items(), 
                           key=lambda x: hash(x[0]))[:keep_count]
                )
            
            # Clean up validation cache (this should be time-based)
            self._validation_cache.clear()  # Simpler to just clear it
            
            # Update last cleanup time
            UnoFilterManager._last_cleanup = now
            
            if self.logger and (self._cache_hits + self._cache_misses) > 0:
                hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses)
                self.logger.debug(
                    f"Filter cache cleanup performed. Hit rate: {hit_rate:.2%}, "
                    f"Hits: {self._cache_hits}, Misses: {self._cache_misses}"
                )
        except Exception as e:
            # Don't let cache cleanup errors affect normal operation
            if self.logger:
                self.logger.warning(f"Error during filter cache cleanup: {e}")
    
    def _generate_cache_key(self, model_class: Type[BaseModel]) -> str:
        """
        Generate a cache key for filter data.
        
        Args:
            model_class: The model class to generate a key for
            
        Returns:
            A unique cache key string
        """
        # Combine class name with model hash for uniqueness
        class_name = model_class.__name__
        
        # Include schema version if available for cache invalidation on schema changes
        schema_version = getattr(model_class, "schema_version", "")
        
        # Include table name if available
        table_name = getattr(model_class, "__tablename__", "")
        
        # Create key
        key_parts = [class_name, table_name, schema_version]
        return ":".join([p for p in key_parts if p])

    def create_filters_from_table(
        self,
        model_class: Type[BaseModel],
        exclude_from_filters: bool = False,
        exclude_fields: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> Dict[str, UnoFilterProtocol]:
        """
        Create filters from a model's table.

        Args:
            model_class: The model class to create filters from
            exclude_from_filters: Whether to exclude this model from filters
            exclude_fields: List of field names to exclude from filtering
            use_cache: Whether to use cached filters (default: True)

        Returns:
            A dictionary of filter names to filter objects
        """
        if exclude_from_filters:
            return {}
            
        exclude_fields = exclude_fields or []
        
        # Try to get from cache if enabled
        if FILTER_CACHE_ENABLED and use_cache:
            cache_key = self._generate_cache_key(model_class)
            
            # Check class-level cache
            if cache_key in self._filter_cache:
                UnoFilterManager._cache_hits += 1
                if self.logger and UnoFilterManager._cache_hits % 100 == 0:
                    self.logger.debug(f"Filter cache hit for {cache_key}")
                
                # Use cached filters
                cached_filters = self._filter_cache[cache_key]
                
                # Filter out any excluded fields
                if exclude_fields:
                    # Make a deep copy to avoid modifying the cached filters
                    filters = {k: v for k, v in cached_filters.items() 
                              if not any(ef in v.label.lower() for ef in exclude_fields)}
                else:
                    # Use cached filters directly if no exclusions
                    filters = cached_filters.copy()
                
                self.filters = filters
                return filters
            else:
                UnoFilterManager._cache_misses += 1
        
        # Cache miss or caching disabled - create filters from scratch
        filters: Dict[str, UnoFilterProtocol] = {}
        
        # Handle case where model_class might not have __table__ attribute
        if not hasattr(model_class, "__table__"):
            return filters
            
        table = model_class.__table__

        # Get column type information from cache or compute it
        column_cache_key = f"{model_class.__name__}_columns"
        column_types = self._column_type_cache.get(column_cache_key, {})
        
        # Process each column
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
                    
                    # Cache column type for future use
                    if FILTER_CACHE_ENABLED and column.name not in column_types:
                        try:
                            column_types[column.name] = {
                                "python_type": column.type.python_type.__name__,
                                "is_foreign_key": bool(column.foreign_keys),
                                "table_name": column.table.name
                            }
                        except (AttributeError, TypeError):
                            # Skip for columns without python_type
                            pass

        # Store in column type cache
        if FILTER_CACHE_ENABLED and column_types:
            self._column_type_cache[column_cache_key] = column_types
            
        # Store in class-level cache if enabled
        if FILTER_CACHE_ENABLED and use_cache:
            cache_key = self._generate_cache_key(model_class)
            UnoFilterManager._filter_cache[cache_key] = filters.copy()
            
            if self.logger and UnoFilterManager._cache_misses % 50 == 0:
                self.logger.debug(f"Added filters to cache for {cache_key}")

        self.filters = filters
        return filters

    def _create_filter_from_column(
        self,
        column: Column,
        table: Table,
    ) -> Optional[UnoFilterProtocol]:
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
        use_cache: bool = True,
    ) -> Type[BaseModel]:
        """
        Create a filter parameters model for a model class.

        Args:
            model_class: The model class to create filter parameters for
            use_cache: Whether to use cached filter parameter models

        Returns:
            A Pydantic model class for filter parameters
        """
        # Try to get from cache if enabled
        if FILTER_CACHE_ENABLED and use_cache:
            cache_key = f"filter_params:{self._generate_cache_key(model_class)}"
            
            # Check if we have a cached model
            if cache_key in self._model_cache:
                UnoFilterManager._cache_hits += 1
                if self.logger and UnoFilterManager._cache_hits % 100 == 0:
                    self.logger.debug(f"Filter params model cache hit for {cache_key}")
                return self._model_cache[cache_key]
            else:
                UnoFilterManager._cache_misses += 1
        
        # Cache miss or caching disabled - create filter parameters model from scratch
        filter_names = list(self.filters.keys())
        filter_names.sort()

        # Get the fields from the model class
        try:
            # Use view_schema if available, otherwise use the model directly
            schema_model = getattr(model_class, "view_schema", model_class)
            order_by_choices = list(schema_model.model_fields.keys())
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

        # Add filters for each field - optimization: batch process filters
        # by processing filters in logical groups to reduce iterations
        processed_labels = set()
        lookup_groups = {
            "boolean": boolean_lookups,
            "numeric": numeric_lookups,
            "datetime": datetime_lookups,
            "text": text_lookups
        }
        
        # Group filters by data type for more efficient processing
        type_groups = {"boolean": [], "numeric": [], "datetime": [], "text": []}
        for name in filter_names:
            fltr = self.filters[name]
            
            # Determine which group this filter belongs to
            if fltr.data_type in ("bool", "boolean"):
                type_groups["boolean"].append(fltr)
            elif fltr.data_type in ("int", "float", "Decimal"):
                type_groups["numeric"].append(fltr)
            elif fltr.data_type in ("datetime", "date", "time"):
                type_groups["datetime"].append(fltr)
            else:
                type_groups["text"].append(fltr)
        
        # Process each group together
        for type_name, filters in type_groups.items():
            for fltr in filters:
                label = fltr.label.lower()
                if label in processed_labels:
                    continue
                
                processed_labels.add(label)
                
                # Add the base filter with proper type annotation
                python_type = self._get_python_type_from_data_type(fltr.data_type)
                model_filter_dict.update({
                    label: (
                        Optional[python_type],
                        Field(None, description=f"Filter by {label}")
                    )
                })

                # Add lookup-specific filters
                lookups = lookup_groups.get(type_name, text_lookups)
                for lookup in fltr.lookups:
                    if lookup in lookups:
                        label_ = f"{label}.{lookup.lower()}"
                        model_filter_dict.update({
                            label_: (
                                Optional[python_type],
                                Field(None, description=f"Filter by {label} with {lookup} comparison")
                            )
                        })

        # Create the filter parameters model
        model_name = f"{model_class.__name__}FilterParam"
        filter_model = create_model(
            model_name,
            **model_filter_dict,
            __base__=FilterParam,
        )
        
        # Store in cache if enabled
        if FILTER_CACHE_ENABLED and use_cache:
            cache_key = f"filter_params:{self._generate_cache_key(model_class)}"
            UnoFilterManager._model_cache[cache_key] = filter_model
            
            if self.logger and UnoFilterManager._cache_misses % 50 == 0:
                self.logger.debug(f"Added filter params model to cache for {cache_key}")
        
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
        use_cache: bool = True,
        use_or_condition: bool = False,
    ) -> List[Tuple[str, Any, str]]:
        """
        Validate filter parameters.

        Args:
            filter_params: The filter parameters to validate
            model_class: The model class to validate against
            use_cache: Whether to use cached validation results
            use_or_condition: Whether to process filter conditions as OR instead of AND

        Returns:
            A list of validated filter tuples with an optional condition indicator

        Raises:
            FilterError: If validation fails
        """
        # Try to get validation result from cache for common filter patterns
        if FILTER_CACHE_ENABLED and use_cache and not use_or_condition:  # Skip cache for OR conditions
            try:
                # Generate a cache key based on filter parameters and model
                model_key = self._generate_cache_key(model_class)
                # Convert parameters to a sorted, stringified representation for caching
                param_dict = filter_params.model_dump()
                param_items = sorted(
                    [(k, str(v)) for k, v in param_dict.items() if v is not None],
                    key=lambda x: x[0]
                )
                param_str = json.dumps(param_items)
                cache_key = f"validate:{model_key}:{hashlib.md5(param_str.encode('utf-8')).hexdigest()}"
                
                # Check if we have cached results
                if cache_key in self._validation_cache:
                    UnoFilterManager._cache_hits += 1
                    if self.logger and UnoFilterManager._cache_hits % 100 == 0:
                        self.logger.debug(f"Validation cache hit for {cache_key}")
                    return self._validation_cache[cache_key]
                else:
                    UnoFilterManager._cache_misses += 1
            except Exception as e:
                # Don't let cache errors affect validation logic
                if self.logger:
                    self.logger.warning(f"Error checking validation cache: {e}")
        
        # Create a validation context
        context = ValidationContext(f"{model_class.__name__}Filters")
        
        # Create a named tuple for the filter - add a 'condition' field for OR/AND logic
        FilterTuple = namedtuple("FilterTuple", ["label", "val", "lookup", "condition"])
        filters: List[FilterTuple] = []

        # Get expected parameters - use a set for O(1) lookups
        expected_params = set([key.lower() for key in self.filters.keys()])
        expected_params.update(["limit", "offset", "order_by", "or"])  # Add 'or' as acceptable prefix

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

        # Optimization: Pre-filter parameters to exclude None values
        # and pre-group parameters by type for more efficient processing
        non_null_params = {
            k: v for k, v in filter_params.model_dump().items()
            if v is not None
        }
        
        # Process special parameters first (limit, offset, order_by)
        special_params = {
            k: v for k, v in non_null_params.items()
            if k.split(".")[0] in ["limit", "offset", "order_by"]
        }
        
        # Process each special parameter
        for key, val in special_params.items():
            filter_components = key.split(".")
            edge = filter_components[0]
            
            try:
                self._validate_special_param(
                    edge, val, filter_components, model_class, filters, FilterTuple, context
                )
            except Exception as e:
                context.add_error(key, str(e), "SPECIAL_PARAM_VALIDATION_ERROR", val)

        # Process regular filters
        regular_params = {
            k: v for k, v in non_null_params.items()
            if k.split(".")[0] not in ["limit", "offset", "order_by"]
        }
        
        # Group regular params by field name for OR condition processing
        or_condition_params = {}
        and_condition_params = {}
        
        # First pass - separate OR params from regular params
        for key, val in regular_params.items():
            if key.startswith("or."):
                # This is an OR filter parameter (e.g., or.name.contains=John)
                # Extract the actual filter name (removing or. prefix)
                actual_key = key[3:]  # Remove "or." prefix
                or_condition_params[actual_key] = val
            else:
                # Regular AND filter parameter
                and_condition_params[key] = val
        
        # Process AND condition filters
        for key, val in and_condition_params.items():
            filter_components = key.split(".")
            edge = filter_components[0]
            edge_upper = edge.upper()
            
            # Check if filter key is valid
            if edge_upper not in self.filters.keys():
                context.add_error(
                    key,
                    f"Invalid filter key: {key}",
                    "INVALID_FILTER_KEY",
                    val
                )
                continue

            # Determine lookup type
            lookup = filter_components[1] if len(filter_components) > 1 else "equal"
            
            # Check if lookup is valid for this filter
            if lookup not in self.filters[edge_upper].lookups:
                context.add_error(
                    key, 
                    f"Invalid filter lookup: {lookup}",
                    "INVALID_FILTER_LOOKUP",
                    val
                )
                continue

            # Get filter definition once
            filter_def = self.filters[edge_upper]
            
            # Validate the value type
            expected_type = self._get_python_type_from_data_type(filter_def.data_type)
            if not isinstance(val, (expected_type, type(None))):
                context.add_error(
                    key,
                    f"Invalid value type for {key}: expected {expected_type.__name__}, got {type(val).__name__}",
                    "INVALID_VALUE_TYPE",
                    val
                )
                continue

            # Add to validated filters with AND condition
            filters.append(FilterTuple(edge_upper, val, lookup, "AND"))
        
        # Process OR condition filters
        for key, val in or_condition_params.items():
            filter_components = key.split(".")
            edge = filter_components[0]
            edge_upper = edge.upper()
            
            # Check if filter key is valid
            if edge_upper not in self.filters.keys():
                context.add_error(
                    f"or.{key}",
                    f"Invalid filter key: or.{key}",
                    "INVALID_FILTER_KEY",
                    val
                )
                continue

            # Determine lookup type
            lookup = filter_components[1] if len(filter_components) > 1 else "equal"
            
            # Check if lookup is valid for this filter
            if lookup not in self.filters[edge_upper].lookups:
                context.add_error(
                    f"or.{key}", 
                    f"Invalid filter lookup: {lookup}",
                    "INVALID_FILTER_LOOKUP",
                    val
                )
                continue

            # Get filter definition once
            filter_def = self.filters[edge_upper]
            
            # Validate the value type
            expected_type = self._get_python_type_from_data_type(filter_def.data_type)
            if not isinstance(val, (expected_type, type(None))):
                context.add_error(
                    f"or.{key}",
                    f"Invalid value type for or.{key}: expected {expected_type.__name__}, got {type(val).__name__}",
                    "INVALID_VALUE_TYPE",
                    val
                )
                continue

            # Add to validated filters with OR condition
            filters.append(FilterTuple(edge_upper, val, lookup, "OR"))

        # For global OR mode, set all conditions to OR
        if use_or_condition and not any(f.condition == "OR" for f in filters):
            # Convert all existing filters to OR mode (except special params)
            new_filters = []
            for f in filters:
                if f.label in ["limit", "offset", "order_by"]:
                    # Keep special params as they are
                    new_filters.append(f)
                else:
                    # Change condition to OR for regular filters
                    new_filters.append(FilterTuple(f.label, f.val, f.lookup, "OR"))
            filters = new_filters

        # Raise if there are validation errors
        if context.has_errors():
            raise FilterError(
                reason=f"Filter validation failed for {context.entity_name}",
                validation_errors=context.errors
            )
        
        # Cache valid results if caching is enabled (only for standard AND conditions)
        if FILTER_CACHE_ENABLED and use_cache and not use_or_condition and not any(f.condition == "OR" for f in filters):
            try:
                model_key = self._generate_cache_key(model_class)
                # Convert parameters to a sorted, stringified representation for caching
                param_dict = filter_params.model_dump()
                param_items = sorted(
                    [(k, str(v)) for k, v in param_dict.items() if v is not None],
                    key=lambda x: x[0]
                )
                param_str = json.dumps(param_items)
                cache_key = f"validate:{model_key}:{hashlib.md5(param_str.encode('utf-8')).hexdigest()}"
                
                # Store in cache
                self._validation_cache[cache_key] = filters
                
                # Periodic cleanup to avoid memory bloat
                if len(self._validation_cache) > FILTER_CACHE_MAX_SIZE:
                    # Keep only newest entries
                    keep_count = int(FILTER_CACHE_MAX_SIZE * 0.75)
                    cache_items = list(self._validation_cache.items())
                    self._validation_cache = {
                        k: v for k, v in cache_items[-keep_count:]
                    }
            except Exception as e:
                # Don't let cache errors affect validation logic
                if self.logger:
                    self.logger.warning(f"Error storing in validation cache: {e}")
        
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
            FilterError: If validation fails
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
                
                # Special parameters always use AND condition (condition field is now required)
                if len(tuple_class._fields) >= 4 and 'condition' in tuple_class._fields:
                    filters.append(tuple_class(param_name, value, components[1], "AND"))
                else:
                    # Backward compatibility for old namedtuple format
                    filters.append(tuple_class(param_name, value, components[1]))
            else:
                # Default to 'asc' if not specified
                if len(tuple_class._fields) >= 4 and 'condition' in tuple_class._fields:
                    filters.append(tuple_class(param_name, value, "asc", "AND"))
                else:
                    # Backward compatibility for old namedtuple format
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
            
            # Special parameters always use AND condition
            if len(tuple_class._fields) >= 4 and 'condition' in tuple_class._fields:
                filters.append(tuple_class(param_name, value, param_name, "AND"))
            else:
                # Backward compatibility for old namedtuple format
                filters.append(tuple_class(param_name, value, param_name))


# Alias UnoFilterManager as FilterManager for backward compatibility
FilterManager = UnoFilterManager

# Singleton instance for reuse
_filter_manager_instance = None

def get_filter_manager(logger=None) -> UnoFilterManager:
    """
    Get or create the filter manager singleton instance.
    
    This function provides a convenient way to access a shared filter manager
    instance, which helps with caching and performance by reusing filter definitions.
    
    Args:
        logger: Optional logger for diagnostic output
        
    Returns:
        The filter manager singleton instance
    """
    global _filter_manager_instance
    
    if _filter_manager_instance is None:
        _filter_manager_instance = UnoFilterManager(logger=logger)
    
    return _filter_manager_instance

class FilterConnection:
    """Simple connection class for filters"""
    pass