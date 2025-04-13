# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Filter protocol definitions for the Uno framework.

This module contains protocol definitions for filter components.
"""

from typing import Any, Dict, List, Optional, Protocol, Type, TypeVar, runtime_checkable
from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


@runtime_checkable
class UnoFilterProtocol(Protocol):
    """Protocol for UnoFilter objects."""
    
    source_node_label: str
    source_meta_type_id: str
    label: str
    target_node_label: str
    target_meta_type_id: str
    data_type: str
    raw_data_type: type
    lookups: List[str]
    source_path_fragment: str
    middle_path_fragment: str
    target_path_fragment: str
    documentation: str
    
    def cypher_path(self, parent=None, for_cypher: bool = False) -> str:
        """
        Construct a Cypher path string.
        
        Args:
            parent: Optional parent filter
            for_cypher: Whether to escape characters for Cypher
            
        Returns:
            A Cypher path string
        """
        ...
    
    def cypher_query(self, value: Any, lookup: str) -> str:
        """
        Generate a Cypher query.
        
        Args:
            value: The value to filter by
            lookup: The lookup operation to use
            
        Returns:
            A Cypher query string
        """
        ...