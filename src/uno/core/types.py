# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Core type definitions for the Uno framework.

This module contains shared base classes and types used throughout the framework.
These types are designed to break circular dependencies and provide a consistent
type system across the codebase.
"""

from typing import Dict, Type, List, Optional, TypeVar, Generic, Any, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field

# Type variables
T = TypeVar('T')
ModelT = TypeVar('ModelT', bound=BaseModel)


class FilterParam(BaseModel):
    """Base class for filter parameters."""
    model_config = ConfigDict(extra="forbid")


class FilterItem:
    """Item for storing filter information."""
    
    def __init__(self, name: str, value: Any, lookup: str):
        self.name = name
        self.value = value
        self.lookup = lookup
        
    def __repr__(self) -> str:
        return f"FilterItem(name={self.name}, value={self.value}, lookup={self.lookup})"