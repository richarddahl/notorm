"""
Unified Endpoint Framework for UNO API.

This module re-exports all the main components of the unified endpoint framework
for convenient import without requiring users to know the internal structure.
"""

# Re-export everything from the unified endpoint framework
from uno.api.endpoint.base import BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint
from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from uno.api.endpoint.factory import CrudEndpointFactory, EndpointFactory
from uno.api.endpoint.integration import create_api, setup_api
from uno.api.endpoint.middleware import ErrorHandlerMiddleware, setup_error_handlers
from uno.api.endpoint.response import (
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