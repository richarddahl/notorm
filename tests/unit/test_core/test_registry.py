# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for the registry.py module.

These tests verify the singleton behavior, registration, and lookup functionality
of the UnoRegistry class.
"""

import pytest
from typing import Type
from pydantic import BaseModel

from uno.registry import UnoRegistry
from uno.errors import UnoRegistryError


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
    UnoRegistry._instance = None
    UnoRegistry._models = {}
    yield
    # Reset after test
    UnoRegistry._instance = None
    UnoRegistry._models = {}


class TestUnoRegistry:
    """Tests for the UnoRegistry class."""

    def test_singleton_pattern(self):
        """Test that UnoRegistry follows the singleton pattern."""
        instance1 = UnoRegistry.get_instance()
        instance2 = UnoRegistry.get_instance()
        
        assert instance1 is instance2
        assert UnoRegistry._instance is instance1

    def test_register(self):
        """Test registering a model class."""
        registry = UnoRegistry.get_instance()
        registry.register(_TestModelA, "model_a")
        
        assert registry.get("model_a") == _TestModelA
        assert "model_a" in registry.get_all()

    def test_register_duplicate(self):
        """Test that registering a duplicate table name raises an error."""
        registry = UnoRegistry.get_instance()
        registry.register(_TestModelA, "model_a")
        
        with pytest.raises(UnoRegistryError) as excinfo:
            registry.register(_TestModelB, "model_a")
        
        assert "already exists in the registry" in str(excinfo.value)
        assert excinfo.value.error_code == "DUPLICATE_MODEL"

    def test_get_nonexistent(self):
        """Test getting a non-existent model returns None."""
        registry = UnoRegistry.get_instance()
        
        assert registry.get("nonexistent") is None

    def test_get_all(self):
        """Test getting all registered models."""
        registry = UnoRegistry.get_instance()
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
        registry = UnoRegistry.get_instance()
        registry.register(_TestModelA, "model_a")
        registry.register(_TestModelB, "model_b")
        
        assert len(registry.get_all()) == 2
        
        registry.clear()
        assert len(registry.get_all()) == 0
        assert registry.get("model_a") is None
        assert registry.get("model_b") is None

    def test_independence_after_reset(self):
        """Test that registry instances are independent after reset."""
        # First registry instance
        registry1 = UnoRegistry.get_instance()
        registry1.register(_TestModelA, "model_a")
        
        # Reset the singleton
        UnoRegistry._instance = None
        UnoRegistry._models = {}
        
        # Second registry instance
        registry2 = UnoRegistry.get_instance()
        
        # Verify that registry2 is a new instance
        assert registry1 is not registry2
        assert registry2.get("model_a") is None