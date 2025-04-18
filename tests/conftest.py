"""
Pytest configuration file for the Uno framework.

This module provides common fixtures and setup for testing the framework.
"""

import logging
import os
import sys
import pytest
from pathlib import Path

# Add the project root to sys.path to make imports work
project_root = Path(__file__).parent.parent.absolute()
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session", autouse=True)
def setup_logging():
    """Set up logging for tests."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger("uno.tests")


@pytest.fixture(scope="session", autouse=True)
def setup_environment():
    """Set up environment variables for testing."""
    # Force test environment
    os.environ["ENV"] = "test"
    
    # Reset after tests if needed
    original_env = os.environ.get("ENV")
    yield
    if original_env:
        os.environ["ENV"] = original_env


@pytest.fixture(scope="session", autouse=True)
def prepare_import_paths():
    """Ensure import paths are set up correctly."""
    sys.stdout.write(f"Python path: {sys.path}\n")
    sys.stdout.write(f"Working directory: {os.getcwd()}\n")
    yield