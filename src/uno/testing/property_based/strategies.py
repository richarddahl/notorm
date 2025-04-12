# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Hypothesis strategies for property-based testing of Uno components.

This module provides custom strategies for generating test data for Uno models,
SQL operations, and other components. These strategies can be used with the
Hypothesis library's @given decorator to generate property-based tests.
"""

from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union
from datetime import datetime, date, time
from enum import Enum
import re
import uuid

from hypothesis import strategies as st
from pydantic import BaseModel

from uno.model import UnoModel
from uno.sql.statement import SQLStatement


# Type variables
T = TypeVar("T", bound=UnoModel)
S = TypeVar("S", bound=SQLStatement)


# Strategy registry for custom types
_STRATEGY_REGISTRY: Dict[Type, st.SearchStrategy] = {}


def register_custom_strategy(
    type_: Type, strategy: st.SearchStrategy
) -> None:
    """
    Register a custom Hypothesis strategy for a specific type.

    Args:
        type_: The type to register a strategy for
        strategy: The Hypothesis strategy to use for this type
    """
    _STRATEGY_REGISTRY[type_] = strategy


# Register some default strategies for common types
register_custom_strategy(uuid.UUID, st.uuids())
register_custom_strategy(datetime, st.datetimes())
register_custom_strategy(date, st.dates())
register_custom_strategy(time, st.times())


class UnoStrategy:
    """
    Base class for Uno testing strategies.
    
    This class provides common functionality for generating 
    hypothesis strategies for Uno components.
    """
    
    @staticmethod
    def from_type(
        field_type: Type, 
        min_size: int = 0,
        max_size: int = 10,
        **kwargs
    ) -> st.SearchStrategy:
        """
        Create a Hypothesis strategy from a Python type.
        
        Args:
            field_type: The Python type to create a strategy for
            min_size: Minimum size for container types
            max_size: Maximum size for container types
            **kwargs: Additional arguments to pass to the strategy
            
        Returns:
            A Hypothesis strategy for generating values of the given type
        """
        # Check if we have a registered strategy for this type
        if field_type in _STRATEGY_REGISTRY:
            return _STRATEGY_REGISTRY[field_type]
        
        # Handle standard Python types
        if field_type == str:
            return st.text(min_size=min_size, max_size=max_size, **kwargs)
        elif field_type == int:
            return st.integers(**kwargs)
        elif field_type == float:
            return st.floats(allow_nan=False, allow_infinity=False, **kwargs)
        elif field_type == bool:
            return st.booleans()
        elif field_type == bytes:
            return st.binary(min_size=min_size, max_size=max_size, **kwargs)
        elif field_type == dict:
            return st.dictionaries(
                keys=st.text(min_size=1),
                values=st.text(),
                min_size=min_size,
                max_size=max_size,
                **kwargs
            )
        elif field_type == list:
            return st.lists(
                st.text(),
                min_size=min_size,
                max_size=max_size,
                **kwargs
            )
        
        # Handle enum types
        if isinstance(field_type, type) and issubclass(field_type, Enum):
            return st.sampled_from(list(field_type))
        
        # Fallback to just()
        return st.just(None)


class ModelStrategy(UnoStrategy):
    """
    Strategy for generating instances of Uno models for property-based testing.
    """
    
    @classmethod
    def for_model(
        cls, 
        model_class: Type[T],
        exclude_fields: Optional[list[str]] = None,
        **field_overrides
    ) -> st.SearchStrategy[T]:
        """
        Create a strategy for generating instances of a specific Uno model.
        
        Args:
            model_class: The Uno model class to create a strategy for
            exclude_fields: List of field names to exclude from generation
            **field_overrides: Override strategies for specific fields
            
        Returns:
            A strategy that generates instances of the specified model
        """
        if exclude_fields is None:
            exclude_fields = []
            
        # Get field types from model annotations or Pydantic model
        if issubclass(model_class, BaseModel):
            fields = {
                name: field.annotation 
                for name, field in model_class.model_fields.items()
                if name not in exclude_fields
            }
        else:
            fields = {
                name: hint 
                for name, hint in model_class.__annotations__.items()
                if name not in exclude_fields and not name.startswith("_")
            }
        
        # Create a strategy for each field
        field_strategies = {}
        for field_name, field_type in fields.items():
            if field_name in field_overrides:
                field_strategies[field_name] = field_overrides[field_name]
            else:
                field_strategies[field_name] = cls.from_type(field_type)
        
        # Combine field strategies using a Hypothesis fixed_dictionaries strategy
        return st.builds(model_class, **field_strategies)


class SQLStrategy(UnoStrategy):
    """
    Strategy for generating SQL statements for property-based testing.
    """
    
    @classmethod
    def for_statement(
        cls,
        statement_class: Type[S],
        table_names: Optional[list[str]] = None,
        column_names: Optional[Dict[str, list[str]]] = None,
        **kwargs
    ) -> st.SearchStrategy[S]:
        """
        Create a strategy for generating SQL statement instances.
        
        Args:
            statement_class: The SQL statement class to create a strategy for
            table_names: Optional list of table names to use
            column_names: Optional dictionary mapping table names to column lists
            **kwargs: Additional parameters to pass to the statement constructor
            
        Returns:
            A strategy that generates instances of the specified SQL statement
        """
        if table_names is None:
            table_names = [f"table_{i}" for i in range(1, 6)]
            
        if column_names is None:
            column_names = {
                table: [f"col_{i}" for i in range(1, 6)]
                for table in table_names
            }
        
        # Create strategies for common SQL statement components
        table_strategy = st.sampled_from(table_names)
        
        def columns_for_table(table):
            return st.lists(
                st.sampled_from(column_names.get(table, [])),
                min_size=1,
                unique=True
            )
        
        # Strategy for conditions (WHERE clauses)
        condition_strategy = st.lists(
            st.builds(
                lambda col, op, val: f"{col} {op} {val}",
                col=st.text(min_size=1, max_size=20, 
                           alphabet=st.characters(whitelist_categories=('Ll',))),
                op=st.sampled_from(["=", ">", "<", ">=", "<=", "!=", "LIKE"]),
                val=st.one_of(
                    st.integers().map(str),
                    st.text(min_size=1, max_size=10).map(lambda s: f"'{s}'")
                )
            ),
            min_size=0,
            max_size=3
        )
        
        # Build specific strategies based on the statement type
        class_name = statement_class.__name__.lower()
        
        if "select" in class_name:
            return st.builds(
                statement_class,
                table=table_strategy,
                columns=st.builds(
                    lambda t: columns_for_table(t).example(),
                    t=table_strategy
                ),
                where=condition_strategy,
                **kwargs
            )
        elif "insert" in class_name:
            return st.builds(
                statement_class,
                table=table_strategy,
                columns=st.builds(
                    lambda t: columns_for_table(t).example(),
                    t=table_strategy
                ),
                values=st.lists(
                    st.one_of(
                        st.integers().map(str),
                        st.text(min_size=1, max_size=10).map(lambda s: f"'{s}'")
                    ),
                    min_size=1,
                    max_size=5
                ),
                **kwargs
            )
        elif "update" in class_name:
            return st.builds(
                statement_class,
                table=table_strategy,
                set_values=st.dictionaries(
                    keys=st.text(min_size=1, max_size=10),
                    values=st.one_of(
                        st.integers().map(str),
                        st.text(min_size=1, max_size=10).map(lambda s: f"'{s}'")
                    ),
                    min_size=1,
                    max_size=5
                ),
                where=condition_strategy,
                **kwargs
            )
        elif "delete" in class_name:
            return st.builds(
                statement_class,
                table=table_strategy,
                where=condition_strategy,
                **kwargs
            )
        else:
            # Generic fallback for other statement types
            return st.builds(statement_class, **kwargs)