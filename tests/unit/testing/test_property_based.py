# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Tests for the property-based testing module.

These tests verify the functionality of the property-based testing utilities.
"""

import pytest
from typing import Dict, Any, List

from uno.testing.property_based import (
    UnoStrategy,
    ModelStrategy,
    SQLStrategy,
    register_custom_strategy,
    given_model,
)
from uno.model import UnoModel
from pydantic import BaseModel, Field


class SamplePydanticModel(BaseModel):
    """Sample Pydantic model for testing."""
    
    name: str
    age: int
    is_active: bool = True
    
    
class SampleUnoModel(UnoModel):
    """Sample Uno model for testing."""
    
    name: str
    age: int
    scores: List[int] = []
    
    def validate(self) -> bool:
        """Validate the model."""
        return len(self.name) > 0 and self.age >= 0


class TestUnoStrategy:
    """Tests for the UnoStrategy class."""
    
    def test_from_type_basic_types(self):
        """Test creating strategies for basic types."""
        # String strategy
        str_strategy = UnoStrategy.from_type(str)
        str_value = str_strategy.example()
        assert isinstance(str_value, str)
        
        # Integer strategy
        int_strategy = UnoStrategy.from_type(int)
        int_value = int_strategy.example()
        assert isinstance(int_value, int)
        
        # Boolean strategy
        bool_strategy = UnoStrategy.from_type(bool)
        bool_value = bool_strategy.example()
        assert isinstance(bool_value, bool)
    
    def test_register_custom_strategy(self):
        """Test registering a custom strategy."""
        from hypothesis import strategies as st
        
        # Define a custom type
        class CustomType:
            def __init__(self, value):
                self.value = value
        
        # Define a custom strategy
        custom_strategy = st.builds(
            CustomType,
            value=st.integers(min_value=1, max_value=100)
        )
        
        # Register the custom strategy
        register_custom_strategy(CustomType, custom_strategy)
        
        # Use the custom strategy
        strategy = UnoStrategy.from_type(CustomType)
        value = strategy.example()
        
        # Check the result
        assert isinstance(value, CustomType)
        assert 1 <= value.value <= 100


class TestModelStrategy:
    """Tests for the ModelStrategy class."""
    
    def test_for_model_pydantic(self):
        """Test creating strategies for Pydantic models."""
        # Create a strategy for the Pydantic model
        strategy = ModelStrategy.for_model(SamplePydanticModel)
        
        # Generate an example
        model = strategy.example()
        
        # Check the result
        assert isinstance(model, SamplePydanticModel)
        assert isinstance(model.name, str)
        assert isinstance(model.age, int)
        assert isinstance(model.is_active, bool)
    
    def test_for_model_uno(self):
        """Test creating strategies for Uno models."""
        # Create a strategy for the Uno model
        strategy = ModelStrategy.for_model(SampleUnoModel)
        
        # Generate an example
        model = strategy.example()
        
        # Check the result
        assert isinstance(model, SampleUnoModel)
        assert isinstance(model.name, str)
        assert isinstance(model.age, int)
        assert isinstance(model.scores, list)
    
    def test_for_model_with_overrides(self):
        """Test creating strategies with field overrides."""
        from hypothesis import strategies as st
        
        # Create a strategy with field overrides
        strategy = ModelStrategy.for_model(
            SamplePydanticModel,
            field_overrides={
                "name": st.just("Test Name"),
                "age": st.integers(min_value=18, max_value=65)
            }
        )
        
        # Generate an example
        model = strategy.example()
        
        # Check the result
        assert model.name == "Test Name"
        assert 18 <= model.age <= 65


class TestGivenModelDecorator:
    """Tests for the given_model decorator."""
    
    @given_model(SampleUnoModel)
    def test_given_model_decorator(self, model):
        """Test the given_model decorator with a Uno model."""
        # The decorator automatically generates a model instance
        assert isinstance(model, SampleUnoModel)
        assert isinstance(model.name, str)
        assert isinstance(model.age, int)
        
        # The model should pass validation
        assert model.validate()
    
    @given_model(
        SamplePydanticModel,
        exclude_fields=["is_active"],
        field_overrides={"name": "Static Name"}
    )
    def test_given_model_with_options(self, model):
        """Test the given_model decorator with options."""
        # The decorator generates a model with the specified options
        assert isinstance(model, SamplePydanticModel)
        assert model.name == "Static Name"
        assert isinstance(model.age, int)
        assert model.is_active is True  # Default value since excluded