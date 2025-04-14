"""
Advanced property-based testing framework for Uno applications.

This module provides an enhanced framework for property-based testing that builds
on Hypothesis but adds domain-specific generators, test case reduction strategies,
and reporting capabilities specifically designed for Uno applications.
"""

import inspect
import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Type, Union, TypeVar, Generic

try:
    import hypothesis
    from hypothesis import strategies as st
    from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, precondition
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False

from uno.testing.property_based.strategies import (
    UnoStrategy,
    ModelStrategy,
    SQLStrategy,
    register_custom_strategy,
)


# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class PropertyTestError(Exception):
    """Exception raised when a property-based test fails."""
    pass


class PropertyTest:
    """Base class for property-based tests."""
    
    def __init__(
        self,
        max_examples: int = 100,
        deadline: Optional[int] = None,
        database: Optional[str] = None,
        verbosity: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the property test.
        
        Args:
            max_examples: Maximum number of examples to generate
            deadline: Maximum time in milliseconds per example
            database: Path to database for storing counterexamples
            verbosity: Verbosity level (0-2)
            logger: Optional logger instance
        """
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError(
                "Hypothesis is required for property-based testing. "
                "Please install it with: pip install hypothesis"
            )
        
        self.max_examples = max_examples
        self.deadline = deadline
        self.database = database
        self.verbosity = verbosity
        self.logger = logger or logging.getLogger(__name__)
        
        # Register default strategies
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """Register default strategies for common Uno types."""
        # These will be available by default in property tests
        pass
    
    def forall(self, *args, **kwargs):
        """
        Decorator for property test methods.
        
        This is a wrapper around hypothesis.given that adds
        domain-specific features for Uno applications.
        
        Example:
            @property_test.forall(x=st.integers(), y=st.integers())
            def test_addition_commutative(self, x, y):
                assert x + y == y + x
        """
        def decorator(func):
            # Configure Hypothesis settings
            settings_kwargs = {
                "max_examples": self.max_examples,
                "verbosity": getattr(hypothesis, f"Verbosity.{['quiet', 'normal', 'verbose'][self.verbosity]}")
            }
            
            if self.deadline is not None:
                settings_kwargs["deadline"] = self.deadline
                
            if self.database is not None:
                settings_kwargs["database"] = self.database
            
            # Apply Hypothesis settings and given decorator
            settings = hypothesis.settings(**settings_kwargs)
            given = hypothesis.given(*args, **kwargs)
            
            @functools.wraps(func)
            def wrapper(*wargs, **wkwargs):
                try:
                    return settings(given(func))(*wargs, **wkwargs)
                except Exception as e:
                    self.logger.error(f"Property test failed: {str(e)}")
                    raise PropertyTestError(f"Property test failed: {str(e)}") from e
            
            return wrapper
        
        return decorator
    
    def stateful_test(
        self,
        *,
        max_steps: int = 50,
        stateful_step_count: int = 10,
    ) -> Type[RuleBasedStateMachine]:
        """
        Create a stateful test class.
        
        This is a factory method that creates a RuleBasedStateMachine
        subclass configured for Uno applications.
        
        Args:
            max_steps: Maximum number of steps in generated test sequence
            stateful_step_count: Number of steps to run in each test
            
        Returns:
            A RuleBasedStateMachine subclass
        
        Example:
            DatabaseTest = property_test.stateful_test()
            
            class TestDatabaseOperations(DatabaseTest):
                def __init__(self):
                    super().__init__()
                    self.db = MockDatabase()
                
                @rule(key=st.text(), value=st.integers())
                def insert(self, key, value):
                    self.db.insert(key, value)
                
                @rule(key=st.text())
                def delete(self, key):
                    self.db.delete(key)
                
                @invariant()
                def db_is_consistent(self):
                    assert self.db.is_consistent()
        """
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError(
                "Hypothesis is required for stateful testing. "
                "Please install it with: pip install hypothesis"
            )
        
        # Configure settings for stateful testing
        settings_kwargs = {
            "max_examples": self.max_examples,
            "stateful_step_count": stateful_step_count,
            "verbosity": getattr(hypothesis, f"Verbosity.{['quiet', 'normal', 'verbose'][self.verbosity]}")
        }
        
        if self.deadline is not None:
            settings_kwargs["deadline"] = self.deadline
            
        if self.database is not None:
            settings_kwargs["database"] = self.database
        
        settings = hypothesis.settings(**settings_kwargs)
        
        # Create base class for stateful tests
        @settings
        class UnoStatefulTest(RuleBasedStateMachine):
            def teardown(self):
                super().teardown()
                # Add Uno-specific teardown logic here
        
        # Expose Hypothesis decorators on the class
        UnoStatefulTest.rule = rule
        UnoStatefulTest.invariant = invariant
        UnoStatefulTest.precondition = precondition
        
        return UnoStatefulTest
    
    def assume(self, condition: bool) -> None:
        """
        Assume a condition for property-based tests.
        
        This is a wrapper around hypothesis.assume that adds
        domain-specific features for Uno applications.
        
        Args:
            condition: Condition to assume
        """
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError(
                "Hypothesis is required for property-based testing. "
                "Please install it with: pip install hypothesis"
            )
        
        hypothesis.assume(condition)
    
    def note(self, message: str) -> None:
        """
        Add a note to the test output.
        
        This is a wrapper around hypothesis.note that adds
        domain-specific features for Uno applications.
        
        Args:
            message: Message to add to test output
        """
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError(
                "Hypothesis is required for property-based testing. "
                "Please install it with: pip install hypothesis"
            )
        
        hypothesis.note(message)
        self.logger.info(message)
    
    def event(self, event_name: str) -> None:
        """
        Record an event in the test.
        
        This is a wrapper around hypothesis.event that adds
        domain-specific features for Uno applications.
        
        Args:
            event_name: Name of the event to record
        """
        if not HYPOTHESIS_AVAILABLE:
            raise ImportError(
                "Hypothesis is required for property-based testing. "
                "Please install it with: pip install hypothesis"
            )
        
        hypothesis.event(event_name)
        self.logger.debug(f"Event occurred: {event_name}")


# Create default instance
default_property_test = PropertyTest()

# Add convenience methods at module level
forall = default_property_test.forall
stateful_test = default_property_test.stateful_test
assume = default_property_test.assume
note = default_property_test.note
event = default_property_test.event


class ModelPropertyTest(PropertyTest):
    """Property test utilities specifically for models."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Register model-specific strategies
        self._register_model_strategies()
    
    def _register_model_strategies(self):
        """Register model-specific strategies."""
        # These will be available by default in model property tests
        pass
    
    def model_builder(self, model_class: Type[T]) -> st.SearchStrategy[T]:
        """
        Create a strategy for building valid model instances.
        
        Args:
            model_class: Model class to build instances of
            
        Returns:
            Strategy for building valid model instances
        """
        strategy = ModelStrategy(model_class).build()
        return strategy
    
    def valid_field_values(self, model_class: Type[Any], field_name: str) -> st.SearchStrategy[Any]:
        """
        Create a strategy for generating valid values for a model field.
        
        Args:
            model_class: Model class
            field_name: Name of the field
            
        Returns:
            Strategy for generating valid field values
        """
        return ModelStrategy(model_class).field_values(field_name)


class SQLPropertyTest(PropertyTest):
    """Property test utilities specifically for SQL operations."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Register SQL-specific strategies
        self._register_sql_strategies()
    
    def _register_sql_strategies(self):
        """Register SQL-specific strategies."""
        # These will be available by default in SQL property tests
        pass
    
    def sql_builder(self, dialect: str = "postgresql") -> st.SearchStrategy[str]:
        """
        Create a strategy for building valid SQL queries.
        
        Args:
            dialect: SQL dialect (postgresql, mysql, sqlite, etc.)
            
        Returns:
            Strategy for building valid SQL queries
        """
        strategy = SQLStrategy(dialect).build()
        return strategy


# Create specialized instances
model_property_test = ModelPropertyTest()
sql_property_test = SQLPropertyTest()

# Export convenience functions
model_forall = model_property_test.forall
sql_forall = sql_property_test.forall