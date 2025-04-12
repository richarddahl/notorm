"""
Tests for CLI modules.

This module contains tests for the CLI modules in the devtools package.
"""

import pytest
import importlib


def test_debug_module_imports():
    """Test that the debug module imports correctly."""
    debug_module = importlib.import_module("uno.devtools.cli.debug")
    assert hasattr(debug_module, "setup_parser")
    assert hasattr(debug_module, "handle_command")


def test_profile_module_imports():
    """Test that the profile module imports correctly."""
    profile_module = importlib.import_module("uno.devtools.cli.profile")
    assert hasattr(profile_module, "setup_parser")
    assert hasattr(profile_module, "handle_command")


def test_hotspot_module_imports():
    """Test that the hotspot module imports correctly."""
    hotspot_module = importlib.import_module("uno.devtools.profiling.hotspot")
    assert hasattr(hotspot_module, "find_hotspots")
    assert hasattr(hotspot_module, "analyze_performance")


def test_visualization_module_imports():
    """Test that the visualization module imports correctly."""
    visualization_module = importlib.import_module("uno.devtools.profiling.visualization")
    assert hasattr(visualization_module, "visualize_profile")
    assert hasattr(visualization_module, "_generate_basic_html")