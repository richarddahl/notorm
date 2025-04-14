# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the registry.py module.

These tests verify the singleton behavior, registration, and lookup functionality
of the UnoRegistry class with the get_registry() function.
"""

import pytest
from typing import Type
from pydantic import BaseModel
from functools import lru_cache

from uno.registry import UnoRegistry, get_registry
from uno.registry_errors import RegistryDuplicateError


# Test model classes (not actual test classes, hence the underscore prefix)
class _TestModelA(BaseModel):
    """Test model class A for registry tests."""
    name: str


class _TestModelB(BaseModel):
    """Test model class B for registry tests."""
    value: int


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset the UnoRegistry singleton before and after each test."""
    # Reset before test
    registry = get_registry()
    registry.clear()
    # Clear the lru_cache to get a fresh instance
    get_registry.cache_clear()
    yield
    # Reset after test
    registry = get_registry()
    registry.clear()
    get_registry.cache_clear()


class TestUnoRegistry:
    """Tests for the UnoRegistry class."""

    def test_singleton_pattern(self):
        """Test that UnoRegistry follows the singleton pattern with get_registry()."""
        instance1 = get_registry()
        instance2 = get_registry()
        
        assert instance1 is instance2
        assert isinstance(instance1, UnoRegistry)

    def test_register(self):
        """Test registering a model class."""
        registry = get_registry()
        registry.register(_TestModelA, "model_a")
        
        assert registry.get("model_a") == _TestModelA
        assert "model_a" in registry.get_all()

    def test_register_duplicate(self):
        """Test that registering a duplicate table name raises an error."""
        registry = get_registry()
        registry.register(_TestModelA, "model_a")
        
        with pytest.raises(RegistryDuplicateError) as excinfo:
            registry.register(_TestModelB, "model_a")
        
        # Different error format used in new registry implementation
        assert "DUPLICATE_MODEL" in str(excinfo.value) or "REG-0001" in str(excinfo.value)
        
        # Check the error_code property exists and has expected content
        assert hasattr(excinfo.value, 'error_code')
        assert "REG-0001" in excinfo.value.error_code or "DUPLICATE_MODEL" in excinfo.value.error_code

    def test_get_nonexistent(self):
        """Test getting a non-existent model returns None."""
        registry = get_registry()
        
        assert registry.get("nonexistent") is None

    def test_get_all(self):
        """Test getting all registered models."""
        registry = get_registry()
        registry.register(_TestModelA, "model_a")
        registry.register(_TestModelB, "model_b")
        
        all_models = registry.get_all()
        assert len(all_models) == 2
        assert all_models["model_a"] == _TestModelA
        assert all_models["model_b"] == _TestModelB
        
        # Verify that get_all returns a copy
        all_models["new_key"] = "new_value"
        assert "new_key" not in registry.get_all()

    def test_clear(self):
        """Test clearing the registry."""
        registry = get_registry()
        registry.register(_TestModelA, "model_a")
        registry.register(_TestModelB, "model_b")
        
        assert len(registry.get_all()) == 2
        
        registry.clear()
        assert len(registry.get_all()) == 0
        assert registry.get("model_a") is None
        assert registry.get("model_b") is None

    def test_registry_clearing(self):
        """Test that clearing the registry works as expected."""
        # First registry instance
        registry = get_registry()
        registry.register(_TestModelA, "model_a")
        
        # Verify model is registered
        assert registry.get("model_a") == _TestModelA
        
        # Clear the registry
        registry.clear()
        
        # Verify model is no longer registered
        assert registry.get("model_a") is None
        
        # Register a different model
        registry.register(_TestModelB, "model_b")
        assert registry.get("model_b") == _TestModelB