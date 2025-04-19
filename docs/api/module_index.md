# API Module

The API module provides a unified endpoint framework for creating FastAPI endpoints that integrate seamlessly with the domain entity framework. This module is part of Phase 3 of the UNO architecture modernization plan.

## Overview

The API module provides these key features:

- **Standardized Endpoint Classes**: BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint
- **CQRS Support**: Separation of query and command operations
- **Factory Pattern**: Automated endpoint creation with EndpointFactory and CrudEndpointFactory
- **Standardized Response Format**: Consistent response formatting for all endpoints
- **Error Handling**: Middleware and handlers for standardized error responses
- **FastAPI Integration**: Seamless integration with FastAPI applications

## Key Components

### Base Endpoint Framework

- **BaseEndpoint**: The foundation of all endpoints, providing common functionality for registering routes and handling responses.
- **CrudEndpoint**: Provides standardized implementation of CRUD operations for domain entities.
- **QueryEndpoint**: Provides standardized implementation of query operations.
- **CommandEndpoint**: Provides standardized implementation of command operations.

### CQRS Implementation

- **CqrsEndpoint**: Combines query and command handlers into a single endpoint.
- **QueryHandler**: Handles read operations with standardized patterns.
- **CommandHandler**: Handles write operations with standardized patterns.

### Factory Pattern

- **EndpointFactory**: Creates various endpoint types.
- **CrudEndpointFactory**: Simplifies creation of CRUD endpoints for domain entities.

### Response Formatting

- **DataResponse**: Standard format for data responses.
- **ErrorResponse**: Standard format for error responses.
- **PaginatedResponse**: Standard format for paginated data responses.

### Error Handling

- **ErrorHandlerMiddleware**: Middleware for handling errors in API requests.
- **setup_error_handlers**: Set up error handlers for a FastAPI application.

### FastAPI Integration

- **create_api**: Create a new FastAPI application with the unified endpoint framework.
- **setup_api**: Set up a FastAPI application with the unified endpoint framework.

## Getting Started

To get started with the API module, see the [Unified Endpoint Framework Developer Guide](unified_endpoint_framework.md).

### Basic CRUD Endpoint

```python
from fastapi import FastAPI
from uno.api.endpoint import CrudEndpoint, create_api

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create a CRUD endpoint
endpoint = CrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products"],
    path="/api/products",
)
endpoint.register(app)
```

### Basic CQRS Endpoint

```python
from fastapi import FastAPI
from uno.api.endpoint import CommandHandler, CqrsEndpoint, QueryHandler, create_api

# Create the API
app = create_api(title="Product CQRS API", description="API for managing products using CQRS")

# Create a CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[
        QueryHandler(
            service=search_products_service,
            response_model=List[ProductResponse],
            query_model=ProductSearchQuery,
            path="/search",
            method="get",
        ),
    ],
    commands=[
        CommandHandler(
            service=create_product_service,
            command_model=CreateProductCommand,
            response_model=ProductResponse,
            path="",
            method="post",
        ),
    ],
    tags=["Products"],
    base_path="/api/products",
)
endpoint.register(app)
```

## Advanced Topics

For more advanced topics, see:

- [CQRS Pattern](endpoint/cqrs_pattern.md): Learn how to implement the Command Query Responsibility Segregation pattern.
- [Response Formatting](endpoint/response_formatting.md): Learn how to format responses consistently.
- [Error Handling](endpoint/error_handling.md): Learn how to handle errors consistently.
- [OpenAPI Integration](endpoint/openapi_integration.md): Learn how to integrate with OpenAPI documentation.
- [Authentication and Authorization](endpoint/authentication_plan.md): Learn how to secure your endpoints.
- [Best Practices](endpoint/best_practices.md): Learn best practices for creating and structuring API endpoints.
- [Migration Guide](endpoint/migration_guide.md): Learn how to migrate from legacy API patterns to the unified endpoint framework.

## Examples

For examples, see:

- [CRUD Example](examples/crud_example.py): Example of a CRUD endpoint.
- [CQRS Example](examples/cqrs_example.py): Example of a CQRS endpoint.
- [Migration Example](examples/migration_example.py): Example of migrating from legacy API patterns to the unified endpoint framework.

## Next Steps

The next steps for the API module are:

1. **Authentication and Authorization**: Implement authentication and authorization for endpoints.
2. **OpenAPI Documentation**: Enhance OpenAPI documentation generation.
3. **Filtering Implementation**: Create a filtering mechanism based on specifications.