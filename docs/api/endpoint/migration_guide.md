# Migration Guide: Legacy API to Unified Endpoint Framework

This guide will help you migrate from the legacy API endpoint patterns to the new unified endpoint framework in UNO.

## Overview of Changes

The unified endpoint framework introduces several improvements over the legacy API patterns:

1. **Standardized Base Classes**: New BaseEndpoint, CrudEndpoint, QueryEndpoint, CommandEndpoint classes
2. **CQRS Support**: Dedicated support for the Command Query Responsibility Segregation pattern
3. **Factory Pattern**: Improved factory classes for creating endpoints
4. **Standardized Responses**: Consistent response formatting for all endpoints
5. **Error Handling**: Improved error handling with middleware and standardized error responses
6. **FastAPI Integration**: Better integration with FastAPI features

## Step-by-Step Migration

### Step 1: Identify Legacy Endpoints

Identify which legacy endpoint patterns you're using:

1. **UnoEndpoint**: General-purpose endpoints
2. **CreateEndpoint, ViewEndpoint, ListEndpoint, UpdateEndpoint, DeleteEndpoint**: CRUD endpoints
3. **DomainServiceAdapter, EntityServiceAdapter**: Service adapters
4. **DomainServiceEndpointFactory**: Endpoint factory

### Step 2: Choose the Appropriate Replacement

Choose the appropriate replacement for each legacy component:

| Legacy Component | Replacement |
|------------------|-------------|
| UnoEndpoint | BaseEndpoint |
| CreateEndpoint, ViewEndpoint, ListEndpoint, UpdateEndpoint, DeleteEndpoint | CrudEndpoint |
| DomainServiceAdapter | CommandEndpoint or QueryEndpoint |
| EntityServiceAdapter | CrudEndpoint |
| DomainServiceEndpointFactory | EndpointFactory or CrudEndpointFactory |

### Step 3: Migrate CRUD Endpoints

For CRUD endpoints, replace legacy patterns with CrudEndpoint:

#### Legacy Code

```python
from fastapi import FastAPI
from uno.api.endpoint import CreateEndpoint, ViewEndpoint, ListEndpoint, UpdateEndpoint, DeleteEndpoint
from uno.api.service_endpoint_adapter import EntityServiceAdapter

# Create adapter
adapter = EntityServiceAdapter(
    service=product_service,
    entity_type=Product,
    input_model=ProductInput,
    output_model=ProductOutput,
)

# Create endpoints
app = FastAPI()
create_endpoint = CreateEndpoint(
    model=adapter,
    app=app,
    path_prefix="/api/products",
    tags=["Products"],
)
view_endpoint = ViewEndpoint(
    model=adapter,
    app=app,
    path_prefix="/api/products",
    tags=["Products"],
)
# ... and so on for other endpoints
```

#### Migrated Code

```python
from fastapi import FastAPI
from uno.api.endpoint.base import CrudEndpoint
from uno.api.endpoint.integration import create_api

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create a single CRUD endpoint for all operations
endpoint = CrudEndpoint(
    service=product_service,
    create_model=ProductInput,
    response_model=ProductOutput,
    update_model=ProductInput,
    tags=["Products"],
    path="/api/products",
)
endpoint.register(app)
```

### Step 4: Migrate Domain Service Endpoints

For domain service endpoints, choose between CommandEndpoint and QueryEndpoint based on the operation type:

#### Legacy Code

```python
from fastapi import FastAPI
from uno.api.service_endpoint_adapter import DomainServiceAdapter
from uno.api.service_endpoint_factory import DomainServiceEndpointFactory

# Create factory
factory = DomainServiceEndpointFactory()

# Create endpoint
app = FastAPI()
factory.create_domain_service_endpoint(
    app=app,
    service_class=SearchProductsService,
    path="/api/products/search",
    method="GET",
    tags=["Products"],
    summary="Search for products",
)
```

#### Migrated Code (Query)

```python
from fastapi import FastAPI
from uno.api.endpoint.cqrs import QueryHandler, CqrsEndpoint
from uno.api.endpoint.integration import create_api

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create query handler
search_query = QueryHandler(
    service=search_products_service,
    response_model=List[ProductSearchResult],
    query_model=ProductSearchQuery,
    path="/search",
    method="get",
)

# Create and register CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[search_query],
    tags=["Products"],
    base_path="/api/products",
)
endpoint.register(app)
```

#### Migrated Code (Command)

```python
from fastapi import FastAPI
from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint
from uno.api.endpoint.integration import create_api

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create command handler
create_command = CommandHandler(
    service=create_product_service,
    command_model=CreateProductCommand,
    response_model=ProductCreatedResult,
    path="",
    method="post",
)

# Create and register CQRS endpoint
endpoint = CqrsEndpoint(
    commands=[create_command],
    tags=["Products"],
    base_path="/api/products",
)
endpoint.register(app)
```

### Step 5: Migrate Factory Usage

For factory-based endpoint creation, use the new factory classes:

#### Legacy Code

```python
from fastapi import FastAPI
from uno.api.service_endpoint_factory import DomainServiceEndpointFactory

# Create factory
factory = DomainServiceEndpointFactory()

# Create entity service endpoints
app = FastAPI()
endpoints = factory.create_entity_service_endpoints(
    app=app,
    entity_type=Product,
    path_prefix="/api/products",
    tags=["Products"],
    input_model=ProductInput,
    output_model=ProductOutput,
)
```

#### Migrated Code

```python
from fastapi import FastAPI
from uno.api.endpoint.factory import CrudEndpointFactory
from uno.api.endpoint.integration import create_api
from uno.domain.entity.service import ServiceFactory

# Create the API
app = create_api(title="Product API", description="API for managing products")

# Create service factory
service_factory = ServiceFactory()

# Create endpoint factory
factory = CrudEndpointFactory(
    service_factory=service_factory,
    entity_name="Product",
    create_model=ProductInput,
    response_model=ProductOutput,
    tags=["Products"],
    path_prefix="/api",
)

# Create and register endpoints
factory.create_endpoints(app)
```

### Step 6: Update Response Formatting

Update your response formatting to use the standardized response classes:

#### Legacy Code

```python
from fastapi import FastAPI, HTTPException

@app.get("/api/products/{id}")
async def get_product(id: str):
    result = await product_service.get_by_id(id)
    if not result.is_success:
        raise HTTPException(status_code=404, detail="Product not found")
    return result.value

@app.get("/api/products")
async def list_products(page: int = 1, page_size: int = 50):
    result = await product_service.find({})
    count_result = await product_service.count({})
    return {
        "items": result.value,
        "page": page,
        "page_size": page_size,
        "total": count_result.value,
    }
```

#### Migrated Code

```python
from fastapi import FastAPI
from uno.api.endpoint.integration import create_api
from uno.api.endpoint.response import DataResponse, PaginatedResponse, paginated_response

# Create the API
app = create_api(title="Product API", description="API for managing products")

@app.get("/api/products/{id}", response_model=DataResponse[ProductOutput])
async def get_product(id: str):
    result = await product_service.get_by_id(id)
    # Error handling is done by the framework
    return DataResponse(data=result.value)

@app.get("/api/products", response_model=PaginatedResponse[ProductOutput])
async def list_products(page: int = 1, page_size: int = 50):
    result = await product_service.find({})
    count_result = await product_service.count({})
    return paginated_response(
        items=result.value,
        page=page,
        page_size=page_size,
        total_items=count_result.value,
    )
```

### Step 7: Update Error Handling

The new framework provides standardized error handling through middleware:

#### Migrated Code

```python
from fastapi import FastAPI
from uno.api.endpoint.integration import create_api
from uno.api.endpoint.middleware import ErrorHandlerMiddleware, setup_error_handlers

# Create the API with error handling enabled
app = create_api(
    title="Product API",
    description="API for managing products",
    enable_error_handling=True,
)

# Errors from domain services are automatically handled
@app.get("/api/products/{id}")
async def get_product(id: str):
    result = await product_service.get_by_id(id)
    # No need for manual error handling
    return result.value
```

## Using the Compatibility Layer

If you need a gradual migration, you can use the compatibility layer:

```python
from fastapi import FastAPI
from uno.api.endpoint.compatibility import create_legacy_endpoint

# Create the API
app = FastAPI()

# Create a modern endpoint from a legacy service
endpoint = create_legacy_endpoint(
    service=legacy_product_service,
    app=app,
    path="/api/legacy/products",
    tags=["Legacy"],
    input_model=ProductInput,
    output_model=ProductOutput,
)
```

## Common Migration Challenges

### 1. Error Handling Differences

The new framework handles errors differently:

- **Legacy**: Manual error handling with custom error mappings
- **New**: Standardized error handling through middleware and Result handling

Solution: Remove manual error handling and let the framework handle errors.

### 2. Response Format Differences

The new framework uses standardized response formats:

- **Legacy**: Custom response formats
- **New**: DataResponse, ErrorResponse, PaginatedResponse

Solution: Update response models to use the new standardized formats.

### 3. Service Integration Differences

The new framework integrates with services differently:

- **Legacy**: Uses adapters like DomainServiceAdapter and EntityServiceAdapter
- **New**: Direct integration with domain services via endpoint classes

Solution: Remove adapters and use the appropriate endpoint class.

## Next Steps

After migrating to the unified endpoint framework, consider these next steps:

1. **Update Documentation**: Update your OpenAPI documentation to reflect the new endpoints
2. **Add Authentication**: Integrate authentication and authorization with the new framework
3. **Implement CQRS**: Separate read and write operations using the CQRS pattern
4. **Add Validation**: Enhance input validation using Pydantic models
5. **Improve Testing**: Create comprehensive tests for your new endpoints

## Conclusion

Migrating to the unified endpoint framework will provide a more consistent, maintainable, and performant API layer for your application. By following this guide, you can smoothly transition from the legacy patterns to the new framework.

For more information, see:
- [Unified Endpoint Framework Developer Guide](../unified_endpoint_framework.md)
- [CQRS Pattern](cqrs_pattern.md)
- [Response Formatting](response_formatting.md)
- [Error Handling](error_handling.md)