"""
Base renderer for documentation.

This module provides a base class for documentation renderers, defining
the common interface and utilities shared by all renderers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

from uno.core.docs.schema import DocSchema


class DocRenderer(ABC):
    """Base class for documentation renderers."""
    
    @abstractmethod
    def render(self, schema: DocSchema, config: Any) -> Dict[str, str]:
        """
        Render documentation schema into the target format.
        
        Args:
            schema: Documentation schema to render
            config: Configuration for rendering
            
        Returns:
            Dictionary of filenames to rendered content
        """
        pass