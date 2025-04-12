"""Network adapters for synchronization.

This package provides implementations of network adapters for communicating
with different types of servers during synchronization.
"""

from .rest import RestAdapter

__all__ = ["RestAdapter"]