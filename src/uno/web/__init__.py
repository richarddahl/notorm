"""
Uno Web Module.

This module provides static assets and templates for Uno applications.
"""

import os
from pathlib import Path

# Define paths to static and template directories
STATIC_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "static"
TEMPLATES_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "templates"

__all__ = ["STATIC_DIR", "TEMPLATES_DIR"]