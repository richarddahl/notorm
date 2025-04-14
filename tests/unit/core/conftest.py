"""
Pytest configuration for core unit tests.

This conftest.py allows running core tests without the full database setup.
"""

import pytest
import inject

@pytest.fixture(autouse=True)
def setup_test_injector():
    """Set up a test injector for unit tests."""
    # Create a simple injector configuration
    def config(binder):
        pass
    
    # Configure the injector
    inject.clear_and_configure(config)
    
    yield
    
    # Clear the injector after the test
    inject.clear()