"""Progressive enhancement support for offline applications.

This module provides tools and utilities for enhancing application functionality
based on network connectivity and client capabilities.
"""

from .detector import ConnectivityDetector, CapabilityDetector
from .enhancer import ProgressiveEnhancer
from .strategies import EnhancementStrategy, DefaultStrategy
from .config import ProgressiveConfig

__all__ = [
    "ConnectivityDetector",
    "CapabilityDetector",
    "ProgressiveEnhancer",
    "EnhancementStrategy",
    "DefaultStrategy",
    "ProgressiveConfig"
]