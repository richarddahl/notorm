# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API module for Uno.

This module provides tools and utilities for creating API endpoints in the
Uno framework using a domain-driven design approach. It includes repository interfaces,
services, and dependency injection providers for building RESTful APIs.

Key components:
- Domain Entities: Core business objects for API resources
  - ApiResource: Represents a collection of related endpoints
  - EndpointConfig: Represents configuration for an individual endpoint
- Domain Repositories: Data access interfaces and implementations
  - ApiResourceRepository: Manages API resource data
  - EndpointConfigRepository: Manages endpoint configuration data
- Domain Services: Business logic for API operations
  - ApiResourceService: Manages API resources
  - EndpointFactoryService: Creates endpoints for entity types
  - RepositoryAdapterService: Creates adapters for domain repositories
- Dependency Injection: Configures and provides services
  - ApiProvider: Configures dependencies for the API module
  - TestingApiProvider: Configures dependencies for testing
- Repository Adapters: Bridge domain repositories with API endpoints
  - RepositoryAdapter: Standard adapter for repositories
  - ReadOnlyRepositoryAdapter: Adapter for read-only repositories
  - BatchRepositoryAdapter: Adapter for batch operations
"""

# Domain entities
from uno.api.entities import ApiResource, EndpointConfig, HttpMethod

# Domain repositories
from uno.api.domain_repositories import (
    ApiResourceRepositoryProtocol,
    EndpointConfigRepositoryProtocol,
    InMemoryApiResourceRepository,
    InMemoryEndpointConfigRepository,
    FileApiResourceRepository,
)

# Domain services
from uno.api.domain_services import (
    ApiResourceServiceProtocol,
    EndpointFactoryServiceProtocol,
    RepositoryAdapterServiceProtocol,
    ApiResourceService,
    EndpointFactoryService,
    RepositoryAdapterService,
)

# Domain provider


# Domain endpoints
from uno.api.domain_endpoints import router as api_resource_router

# Repository adapters
from uno.api.repository_adapter import (
    RepositoryAdapter, 
    ReadOnlyRepositoryAdapter,
    BatchRepositoryAdapter,
)

# Error handlers (still used in modern implementation)
from uno.api.error_handlers import (
    register_error_handlers,
    default_error_handler,
    validation_error_handler,
    not_found_error_handler,
)

__all__ = [
    # Domain Entities
    "ApiResource",
    "EndpointConfig",
    "HttpMethod",
    
    # Domain Repositories
    "ApiResourceRepositoryProtocol",
    "EndpointConfigRepositoryProtocol",
    "InMemoryApiResourceRepository",
    "InMemoryEndpointConfigRepository",
    "FileApiResourceRepository",
    
    # Domain Services
    "ApiResourceServiceProtocol",
    "EndpointFactoryServiceProtocol",
    "RepositoryAdapterServiceProtocol",
    "ApiResourceService",
    "EndpointFactoryService",
    "RepositoryAdapterService",
    
    # Domain Provider
    "ApiProvider",
    "TestingApiProvider",
    
    # Domain Endpoints
    "api_resource_router",
    
    # Repository Adapters
    "RepositoryAdapter",
    "ReadOnlyRepositoryAdapter",
    "BatchRepositoryAdapter",
    
    # Error handlers
    "register_error_handlers",
    "default_error_handler",
    "validation_error_handler",
    "not_found_error_handler",
]
