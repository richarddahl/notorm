"""
Export all components of the unified endpoint framework.

This module re-exports all the main components of the unified endpoint framework
for convenient import.
"""

from .base import BaseEndpoint, CommandEndpoint, CrudEndpoint, QueryEndpoint
from .cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from .factory import CrudEndpointFactory, EndpointFactory
from .integration import create_api, setup_api
from .middleware import ErrorHandlerMiddleware, setup_error_handlers
from .response import (
    DataResponse,
    ErrorDetail,
    ErrorResponse,
    PaginatedResponse,
    PaginationMetadata,
    paginated_response,
    response_handler,
)

__all__ = [
    # Base endpoint classes
    "BaseEndpoint",
    "CrudEndpoint",
    "QueryEndpoint",
    "CommandEndpoint",
    
    # CQRS components
    "CqrsEndpoint",
    "QueryHandler",
    "CommandHandler",
    
    # Factory components
    "EndpointFactory",
    "CrudEndpointFactory",
    
    # Integration utilities
    "setup_api",
    "create_api",
    
    # Middleware components
    "ErrorHandlerMiddleware",
    "setup_error_handlers",
    
    # Response components
    "DataResponse",
    "ErrorResponse",
    "ErrorDetail",
    "PaginatedResponse",
    "PaginationMetadata",
    "response_handler",
    "paginated_response",
]