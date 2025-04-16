# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API module for Uno.

This module provides tools and utilities for creating API endpoints in the
Uno framework. It includes endpoint factories, schema managers, and other
components for building RESTful APIs.

Key components:
- Domain Entities: Core business objects for API resources
  - ApiResource: Represents a collection of related endpoints
  - EndpointConfig: Represents configuration for an individual endpoint
- Endpoint Factory: Creates FastAPI endpoints from domain entities
- Schema Manager: Manages data transfer object schemas
- Repository Adapter: Adapts domain repositories to API endpoints
"""

# Domain entities (DDD)
from uno.api.entities import ApiResource, EndpointConfig, HttpMethod

# Endpoint factory
from uno.api.endpoint_factory import UnoEndpointFactory, UnoEndpoint

# Schema manager
from uno.api.endpoint import DomainRouter, domain_endpoint

# Repository adapter
from uno.api.repository_adapter import RepositoryAdapter

# Error handling
from uno.api.error_handlers import (
    register_error_handlers,
    default_error_handler,
    validation_error_handler,
    not_found_error_handler,
)

__all__ = [
    # Domain Entities (DDD)
    "ApiResource",
    "EndpointConfig",
    "HttpMethod",
    
    # Endpoint Factory
    "UnoEndpointFactory",
    "UnoEndpoint",
    
    # Schema Manager
    "DomainRouter",
    "domain_endpoint",
    
    # Repository Adapter
    "RepositoryAdapter",
    
    # Error Handling
    "register_error_handlers",
    "default_error_handler",
    "validation_error_handler",
    "not_found_error_handler",
]
