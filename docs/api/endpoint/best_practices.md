# API Endpoint Best Practices

This guide outlines best practices for creating and structuring API endpoints using the unified endpoint framework.

## Endpoint Organization

### Module Structure

When organizing API endpoints for a module, follow this structure:

```
src/uno/your_module/
├── api/
│   ├── __init__.py
│   ├── endpoints.py       # Main endpoint definitions using unified framework
│   ├── dto.py             # Data Transfer Objects (DTOs) for the API
│   ├── responses.py       # Response models
│   ├── parsers.py         # Query parameter parsers
│   └── examples/
│       └── example_api.py # Example usage
```

### Endpoint Class Naming

Use descriptive names for your endpoint classes:

```python
# For CRUD endpoints
class ProductEndpoint(CrudEndpoint):
    """API endpoints for products."""
    ...

# For CQRS endpoints
class ProductQueryEndpoint(CqrsEndpoint):
    """Query endpoints for products."""
    ...

class ProductCommandEndpoint(CqrsEndpoint):
    """Command endpoints for products."""
    ...
```

## Choosing the Right Endpoint Type

### When to Use CrudEndpoint

Use `CrudEndpoint` when:

- You need standard CRUD operations (Create, Read, Update, Delete)
- Your resource maps directly to a domain entity
- You have a straightforward domain service that provides CRUD operations

```python
endpoint = CrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products"],
    path="/api/products",
)
```

### When to Use CqrsEndpoint

Use `CqrsEndpoint` when:

- You need to separate read and write operations
- Your operations involve complex business logic
- You want to optimize read and write paths separately
- You need fine-grained control over individual operations

```python
endpoint = CqrsEndpoint(
    queries=[
        QueryHandler(
            service=get_products_service,
            response_model=list[ProductResponse],
            path="/list",
            method="get",
        ),
        QueryHandler(
            service=search_products_service,
            response_model=list[ProductResponse],
            query_model=ProductSearchQuery,
            path="/search",
            method="get",
        ),
    ],
    commands=[
        CommandHandler(
            service=create_product_service,
            command_model=CreateProductCommand,
            response_model=ProductCreatedResponse,
            path="",
            method="post",
        ),
        CommandHandler(
            service=update_product_service,
            command_model=UpdateProductCommand,
            response_model=ProductUpdatedResponse,
            path="/{id}",
            method="put",
        ),
    ],
    tags=["Products"],
    base_path="/api/products",
)
```

### When to Use QueryEndpoint or CommandEndpoint

Use `QueryEndpoint` or `CommandEndpoint` when:

- You need a single specific operation
- You want to create standalone endpoints
- You want to mix and match different endpoint types

```python
query_endpoint = QueryEndpoint(
    service=search_products_service,
    response_model=list[ProductResponse],
    query_model=ProductSearchQuery,
    router=router,
    tags=["Products"],
    path="/api/products/search",
    method="get",
)

command_endpoint = CommandEndpoint(
    service=create_product_service,
    command_model=CreateProductCommand,
    response_model=ProductCreatedResponse,
    router=router,
    tags=["Products"],
    path="/api/products",
    method="post",
)
```

## Request and Response Models

### Request Model Design

- Use separate models for create and update operations
- Make all fields required for create operations
- Make all fields optional for update operations
- Include validation rules using Pydantic field validators

```python
class CreateProductRequest(BaseModel):
    """Create product request model."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price", gt=0)
    stock: int = Field(..., description="Product stock", ge=0)
    
    @field_validator("name")
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Name must not be empty")
        return v.strip()


class UpdateProductRequest(BaseModel):
    """Update product request model."""
    
    name: str | None = Field(None, description="Product name")
    description: str | None = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price", gt=0)
    stock: Optional[int] = Field(None, description="Product stock", ge=0)
```

### Response Model Design

- Include all fields that clients might need
- Use descriptive field names
- Provide rich metadata

```python
class ProductResponse(BaseModel):
    """Product response model."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(..., description="Whether the product is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "prod_123",
                "name": "Example Product",
                "description": "This is an example product",
                "price": 19.99,
                "stock": 100,
                "is_active": True,
                "created_at": "2025-04-20T12:00:00Z",
                "updated_at": "2025-04-20T12:00:00Z",
            }
        }
```

## Error Handling

### Use the Standard Error Format

All endpoints should use the standard error format:

```python
class ErrorDetail(BaseModel):
    """Error detail model."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: str | None = Field(None, description="Field associated with the error")
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class ErrorResponse(BaseModel):
    """Error response model."""
    
    error: ErrorDetail = Field(..., description="Error details")
    meta: dict[str, Any] | None = Field(None, description="Response metadata")
```

### Standardized Error Codes

Use standardized error codes across your API:

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| NOT_FOUND | 404 | Resource not found |
| VALIDATION_ERROR | 400 | Input validation error |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Permission denied |
| CONFLICT | 409 | Resource conflict |
| INTERNAL_ERROR | 500 | Internal server error |

## Pagination and Filtering

### Standardized Pagination

Use the standard pagination format:

```python
class PaginationMetadata(BaseModel):
    """Pagination metadata model."""
    
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    total_items: int = Field(..., description="Total number of items")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_previous: bool = Field(..., description="Whether there is a previous page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response model."""
    
    data: list[T] = Field(..., description="List of items")
    meta: PaginationMetadata = Field(..., description="Pagination metadata")
```

### Filtering Parameters

Define standard filtering parameters:

```python
@app.get("/api/products", response_model=PaginatedResponse[ProductResponse])
async def list_products(
    # Sorting parameters
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_dir: str = Query("desc", description="Sort direction (asc or desc)"),
    
    # Pagination parameters
    page: int = Query(1, description="Page number", ge=1),
    page_size: int = Query(50, description="Items per page", ge=1, le=100),
    
    # Filtering parameters
    name: str | None = Query(None, description="Filter by name"),
    min_price: Optional[float] = Query(None, description="Minimum price"),
    max_price: Optional[float] = Query(None, description="Maximum price"),
    category_id: str | None = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
):
    # Implementation...
```

## Documentation

### Include Rich Documentation

- Use descriptive docstrings for all endpoint classes and methods
- Include example request and response models
- Provide clear descriptions for all parameters

```python
class ProductEndpoint(CrudEndpoint):
    """
    API endpoints for managing products.
    
    This endpoint provides CRUD operations for products, including:
    - Creating new products
    - Retrieving products by ID
    - Listing all products with filtering and pagination
    - Updating existing products
    - Deleting products
    
    Permissions:
    - Creating products requires the 'products:create' permission
    - Updating products requires the 'products:update' permission
    - Deleting products requires the 'products:delete' permission
    - Listing and retrieving products requires the 'products:read' permission
    """
```

### OpenAPI Tags and Groups

Organize your endpoints with meaningful tags and groups:

```python
endpoint = CrudEndpoint(
    service=product_service,
    create_model=CreateProductRequest,
    response_model=ProductResponse,
    update_model=UpdateProductRequest,
    tags=["Products", "Catalog"],
    path="/api/products",
)
```

## Testing

### Test All Endpoint Operations

Write comprehensive tests for all endpoint operations:

```python
async def test_create_product():
    """Test creating a product."""
    # Arrange
    app = create_test_app()
    endpoint = create_product_endpoint(app)
    client = TestClient(app)
    
    # Act
    response = client.post(
        "/api/products",
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": 19.99,
            "stock": 100,
        },
    )
    
    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["name"] == "Test Product"
    assert data["data"]["price"] == 19.99
```

### Test Error Handling

Write tests for error cases:

```python
async def test_create_product_validation_error():
    """Test creating a product with invalid data."""
    # Arrange
    app = create_test_app()
    endpoint = create_product_endpoint(app)
    client = TestClient(app)
    
    # Act
    response = client.post(
        "/api/products",
        json={
            "name": "Test Product",
            "description": "Test Description",
            "price": -19.99,  # Invalid price
            "stock": 100,
        },
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "price" in data["error"]["message"]
```

## Conclusion

Following these best practices will help you create consistent, maintainable, and well-documented API endpoints using the unified endpoint framework. By standardizing your approach to API design, you'll improve the developer experience for both your team and API consumers.