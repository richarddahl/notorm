# OpenAPI Documentation

The UNO framework provides comprehensive tools for enhancing the OpenAPI documentation of your API. This makes it easier for developers to understand and use your API, and it improves the developer experience when using tools like Swagger UI or Redoc.

## Overview

The OpenAPI documentation system in UNO consists of:

1. **OpenAPI Utilities**: Core utilities for enhancing OpenAPI schema generation
2. **Documented Endpoint Classes**: Extended endpoint classes with built-in documentation capabilities
3. **Examples and Schema Enhancements**: Utilities for adding examples and additional schema information

## Getting Started

### Using the OpenAPI Enhancer

The `OpenApiEnhancer` class provides a convenient way to enhance the OpenAPI documentation of a FastAPI application:

```python
from fastapi import FastAPI
from uno.api.endpoint.openapi import OpenApiEnhancer

app = FastAPI(
    title="My API",
    description="API for my awesome application",
    version="1.0.0"
)

# Create an OpenAPI enhancer
enhancer = OpenApiEnhancer(app)

# Set up JWT authentication
enhancer.setup_jwt_auth(
    description="JWT token authentication for secure endpoints",
    scheme_name="BearerAuth"
)

# Add tags with descriptions
enhancer.add_tag(
    name="Products",
    description="Operations related to products",
    external_docs={"url": "https://example.com/docs/products", "description": "Product documentation"}
)

# Document a specific operation
enhancer.document_operation(
    "/products",
    "get",
    summary="List all products",
    description="Returns a list of all products in the catalog.",
    operation_id="listProducts",
    responses={
        "200": ResponseExample(
            status_code=200,
            example=[{"id": "123", "name": "Example Product"}],
            description="A list of products"
        )
    }
)

# Apply all enhancements
enhancer.apply()
```

### Using Documented Endpoint Classes

UNO provides documented versions of all endpoint classes, which automatically generate appropriate OpenAPI documentation:

```python
from uno.api.endpoint.openapi_extensions import DocumentedCrudEndpoint

product_endpoint = DocumentedCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    update_model=ProductUpdateDTO,
    response_model=ProductResponseDTO,
    path="/products",
    tags=["Products"],
    summary="Product management endpoints",
    description="Endpoints for creating, retrieving, updating, and deleting products",
    operation_examples={
        "create": {
            "201": {
                "content": {"id": "123", "name": "New Product"},
                "description": "The product was created successfully"
            }
        }
    }
)

# Register with FastAPI application
product_endpoint.register(app)
```

## Core Components

### OpenAPI Utilities

- **OpenApiEnhancer**: Main class for enhancing OpenAPI documentation
- **ApiDocumentation**: Container for API documentation metadata
- **ResponseExample**: Class for defining response examples
- **Utility Functions**:
  - `add_response_example`: Add an example to a response
  - `add_security_schema`: Add a security schema
  - `add_operation_id`: Add an operation ID
  - `document_operation`: Add comprehensive documentation to an operation

### Documented Endpoint Classes

These classes extend the standard endpoint classes with documentation capabilities:

- **DocumentedBaseEndpoint**: Base class for all documented endpoints
- **DocumentedCrudEndpoint**: CRUD endpoint with documentation
- **DocumentedQueryEndpoint**: Query endpoint with documentation
- **DocumentedCommandEndpoint**: Command endpoint with documentation
- **DocumentedCqrsEndpoint**: CQRS endpoint with documentation
- **DocumentedFilterableCrudEndpoint**: Filterable CRUD endpoint with documentation
- **DocumentedFilterableCqrsEndpoint**: Filterable CQRS endpoint with documentation

## Examples

### CRUD Endpoint with Documentation

```python
from uno.api.endpoint.openapi_extensions import DocumentedCrudEndpoint

product_endpoint = DocumentedCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    update_model=ProductUpdateDTO,
    response_model=ProductResponseDTO,
    path="/products",
    tags=["Products"],
    summary="Product management endpoints",
    description="Endpoints for creating, retrieving, updating, and deleting products"
)

# Register with FastAPI application
product_endpoint.register(app)
```

### CQRS Endpoint with Documentation

```python
from uno.api.endpoint.openapi_extensions import DocumentedCqrsEndpoint
from uno.api.endpoint.cqrs import QueryHandler, CommandHandler

# Create CQRS endpoint with documentation
cqrs_endpoint = DocumentedCqrsEndpoint(
    queries=[
        QueryHandler(
            path="/products/by-category",
            handler=get_products_by_category_handler.execute,
            query_model=GetProductsByCategoryQuery,
            response_model=List[ProductResponseDTO],
            name="GetProductsByCategory"
        )
    ],
    commands=[
        CommandHandler(
            path="/products/{product_id}/discounts",
            handler=create_product_discount_handler.execute,
            command_model=CreateProductDiscountCommand,
            response_model=DiscountResponseDTO,
            name="CreateProductDiscount"
        )
    ],
    tags=["Products", "Discounts"],
    summary="Product and discount operations",
    description="Endpoints for querying products and managing discounts"
)

# Register with FastAPI application
cqrs_endpoint.register(app)
```

### Filterable Endpoint with Documentation

```python
from uno.api.endpoint.openapi_extensions import DocumentedFilterableCrudEndpoint

# Create filterable CRUD endpoint with documentation
filterable_endpoint = DocumentedFilterableCrudEndpoint(
    service=product_service,
    create_model=ProductCreateDTO,
    update_model=ProductUpdateDTO,
    response_model=ProductResponseDTO,
    path="/filterable-products",
    tags=["Products"],
    summary="Filterable product management endpoints",
    description="Endpoints with filtering capabilities",
    filter_fields=["name", "category", "price"],
    use_graph_backend=True  # Use Apache AGE knowledge graph for filtering
)

# Register with FastAPI application
filterable_endpoint.register(app)
```

### Setting Up JWT Authentication

```python
from uno.api.endpoint.openapi import OpenApiEnhancer

# Initialize OpenAPI enhancer
enhancer = OpenApiEnhancer(app)

# Configure JWT authentication
enhancer.setup_jwt_auth(
    description="JWT token authentication for secure endpoints",
    scheme_name="BearerAuth"
)

# Apply all enhancements
enhancer.apply()
```

### Adding Examples to Responses

```python
from uno.api.endpoint.openapi import ResponseExample, OpenApiEnhancer

# Initialize OpenAPI enhancer
enhancer = OpenApiEnhancer(app)

# Document operation with examples
enhancer.document_operation(
    "/products",
    "get",
    summary="List all products",
    description="Returns a list of all products in the catalog.",
    operation_id="listProducts",
    responses={
        "200": ResponseExample(
            status_code=200,
            example=[
                {
                    "id": "123",
                    "name": "Example Product",
                    "description": "This is an example product",
                    "price": 99.99,
                    "category": "Example Category"
                }
            ],
            description="A list of products was retrieved successfully"
        ),
        "401": ResponseExample(
            status_code=401,
            example={"message": "Not authenticated", "code": "UNAUTHORIZED"},
            description="Authentication is required to access this resource"
        )
    },
    security=[{"BearerAuth": []}]  # Require JWT authentication
)

# Apply all enhancements
enhancer.apply()
```

## Complete Example

See the `uno.api.endpoint.examples.openapi_example` module for a complete example of how to use the OpenAPI documentation features in a real application.

```python
from uno.api.endpoint.examples.openapi_example import create_app

# Create and start the example app
app = create_app()
```

## Best Practices

1. **Use Documented Endpoint Classes**: Prefer the documented endpoint classes over manually enhancing the OpenAPI schema.
2. **Provide Meaningful Examples**: Always include realistic examples for your API responses.
3. **Document Authentication Requirements**: Clearly indicate which endpoints require authentication.
4. **Use Tags for Organization**: Use tags to group related endpoints together.
5. **Add Descriptions**: Include detailed descriptions for each endpoint and parameter.
6. **Use Operation IDs**: Provide unique operation IDs for all endpoints to make them easier to reference.
7. **Include Error Responses**: Document all possible error responses for each endpoint.
8. **Update Documentation When API Changes**: Keep the OpenAPI documentation up to date when you make changes to your API.

## Integration with SwaggerUI and Redoc

FastAPI automatically integrates with SwaggerUI and Redoc. When you enhance your OpenAPI schema using UNO's utilities, those enhancements will be reflected in the SwaggerUI and Redoc interfaces.

Access the documentation at:
- SwaggerUI: `/docs`
- Redoc: `/redoc`