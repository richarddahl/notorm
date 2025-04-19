"""
Filtering utilities for the unified endpoint framework.

This module provides filtering capabilities that integrate with the unified endpoint framework
and optionally support the Apache AGE knowledge graph for advanced filtering capabilities.
"""

from .protocol import FilterBackend, FilterProtocol, QueryParameter
from .models import (
    FilterCondition,
    FilterCriteria,
    FilterField,
    FilterOperator,
    FilterRequest,
    FilterResponse,
    FilterResult,
    SortDirection,
    SortField,
)
from .backends import SqlFilterBackend, GraphFilterBackend
from .middleware import FilterMiddleware
from .query_parser import QueryParser
from .endpoints import FilterableEndpoint, FilterableCrudEndpoint, FilterableCqrsEndpoint

__all__ = [
    # Protocols
    "FilterBackend",
    "FilterProtocol",
    "QueryParameter",
    
    # Models
    "FilterCondition",
    "FilterCriteria",
    "FilterField",
    "FilterOperator",
    "FilterRequest",
    "FilterResponse",
    "FilterResult",
    "SortDirection",
    "SortField",
    
    # Backends
    "SqlFilterBackend",
    "GraphFilterBackend",
    
    # Middleware
    "FilterMiddleware",
    
    # Query Parsing
    "QueryParser",
    
    # Endpoints
    "FilterableEndpoint",
    "FilterableCrudEndpoint",
    "FilterableCqrsEndpoint",
]