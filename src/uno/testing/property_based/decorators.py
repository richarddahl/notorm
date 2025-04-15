# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Decorators for property-based testing of Uno components.

This module provides custom decorators that wrap Hypothesis's @given decorator
to provide more specialized and convenient ways of creating property-based tests
for Uno models and SQL statements.
"""

import functools
from typing import Any, Callable, Dict, Optional, Type, TypeVar, Union

from hypothesis import given, settings, HealthCheck
from hypothesis.strategies import SearchStrategy

from uno.model import UnoModel
from uno.sql.statement import SQLStatement
from uno.testing.property_based.strategies import ModelStrategy, SQLStrategy


# Type variables
T = TypeVar("T", bound=UnoModel)
S = TypeVar("S", bound=SQLStatement)
F = TypeVar("F", bound=Callable)


def given_model(
    model_class: Type[T],
    exclude_fields: Optional[list[str]] = None,
    min_examples: int = 20,
    max_examples: int = 100,
    field_overrides: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> Callable[[F], F]:
    """
    A decorator that provides property-based testing for functions that operate on Uno models.
    
    This is a convenience wrapper around Hypothesis's @given decorator that automatically
    creates appropriate strategies for Uno model instances.
    
    Args:
        model_class: The Uno model class to generate instances of
        exclude_fields: List of field names to exclude from generation
        min_examples: Minimum number of examples to test with
        max_examples: Maximum number of examples to test with
        field_overrides: Dictionary of field name to override strategy
        **kwargs: Additional field overrides (alternative to field_overrides)
        
    Returns:
        A decorator function that wraps the test function
    
    Example:
        ```python
        @given_model(User, exclude_fields=["password"])
        def test_user_validation(user: User):
            assert user.validate()
        ```
    """
    def decorator(func: F) -> F:
        # Combine both ways of providing field overrides
        all_overrides = {}
        if field_overrides:
            all_overrides.update(field_overrides)
        if kwargs:
            all_overrides.update(kwargs)
            
        strategy = ModelStrategy.for_model(
            model_class, 
            exclude_fields=exclude_fields,
            **all_overrides
        )
        
        @functools.wraps(func)
        @given(model=strategy)
        @settings(
            max_examples=max_examples,
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.data_too_large
            ]
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def given_sql(
    statement_class: Type[S],
    table_names: Optional[list[str]] = None,
    column_names: Optional[Dict[str, list[str]]] = None,
    min_examples: int = 20,
    max_examples: int = 100,
    **kwargs
) -> Callable[[F], F]:
    """
    A decorator that provides property-based testing for functions that operate on SQL statements.
    
    This is a convenience wrapper around Hypothesis's @given decorator that automatically
    creates appropriate strategies for SQL statement instances.
    
    Args:
        statement_class: The SQL statement class to generate instances of
        table_names: Optional list of table names to use
        column_names: Optional dictionary mapping table names to column lists
        min_examples: Minimum number of examples to test with
        max_examples: Maximum number of examples to test with
        **kwargs: Additional parameters to pass to the statement constructor
        
    Returns:
        A decorator function that wraps the test function
    
    Example:
        ```python
        @given_sql(SelectStatement, table_names=["users", "profiles"])
        def test_select_statement_validity(statement: SelectStatement):
            assert statement.is_valid()
        ```
    """
    def decorator(func: F) -> F:
        strategy = SQLStrategy.for_statement(
            statement_class,
            table_names=table_names,
            column_names=column_names,
            **kwargs
        )
        
        @functools.wraps(func)
        @given(statement=strategy)
        @settings(
            max_examples=max_examples,
            suppress_health_check=[
                HealthCheck.too_slow,
                HealthCheck.data_too_large
            ]
        )
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator