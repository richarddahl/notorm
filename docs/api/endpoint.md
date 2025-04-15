# UnoEndpoint - FastAPI Integration

The `UnoEndpoint` system provides a powerful, declarative approach to creating RESTful API endpoints with FastAPI. It automatically handles routing, serialization, validation, and documentation, making it easy to expose your business models through a consistent API.

## Overview

UnoEndpoint integrates with FastAPI to provide:

- Standardized RESTful API endpoints
- Automatic request validation
- Response serialization with schema selection
- Comprehensive error handling
- OpenAPI documentation
- Filtering, pagination, and advanced querying
- Field selection for partial responses
- Streaming support for large datasets

## Core Components

### UnoEndpoint

The base class for all API endpoints, using a registry pattern to track endpoint implementations:

```python
class UnoEndpoint(BaseModel):
    registry: ClassVar[dict[str, "UnoEndpoint"]] = {}
    
    model: type[BaseModel]           # The model to expose
    router: UnoRouter                # Router implementation 
    body_model: Optional[str]        # Schema for request body
    response_model: Optional[str]    # Schema for responses
    include_in_schema: bool = True   # Include in OpenAPI docs
    status_code: int = 200           # Default HTTP status code
```

### UnoRouter

Abstract base class for router implementations that handles path construction, HTTP method, and endpoint creation:

```python
class UnoRouter(BaseModel, ABC):
    model: type[BaseModel]
    response_model: type[BaseModel] | None = None
    body_model: type[BaseModel] | None = None
    path_suffix: str                 # Path suffix (e.g., "/{id}")
    method: str                      # HTTP method (GET, POST, etc.)
    path_prefix: str = "/api"        # Path prefix
    api_version: str = "v1"          # API version
    
    @abstractmethod
    def endpoint_factory(self):
        """Create the endpoint function."""
        raise NotImplementedError
```

### Standard Endpoint Types

The framework provides several standard endpoint types:

- **CreateEndpoint**: Create new resources (POST)
- **ViewEndpoint**: Retrieve specific resources (GET /{id})
- **ListEndpoint**: List resources with filtering (GET)
- **UpdateEndpoint**: Update resources (PATCH /{id})
- **DeleteEndpoint**: Delete resources (DELETE /{id})
- **ImportEndpoint**: Import/bulk create resources (PUT)

### UnoEndpointFactory

A factory class for easily creating multiple endpoints for a model:

```python
factory = UnoEndpointFactory()
factory.create_endpoints(
    app=app,
    model_obj=Product,
    endpoints=["Create", "View", "List", "Update", "Delete"]
)
```

## Getting Started

### Prerequisites

To use UnoEndpoint, your model must provide:

1. A `schema_manager` with appropriate schemas:
   - `edit_schema`: For creating and updating
   - `view_schema`: For displaying the model

2. Required class methods:
   - `get(id)`: Retrieve by ID
   - `filter(filters, page, page_size)`: List with filtering
   - `save(body, importing=False)`: Create or update
   - `delete_(id)`: Delete by ID
   - `create_filter_params()`: Define filter parameters
   - `validate_filter_params(params)`: Process filters

3. Class variables:
   - `display_name`: Singular display name
   - `display_name_plural`: Plural display name

### Basic Example

Here's a complete example setting up endpoints for a Product model:

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from uno.api.endpoint_factory import UnoEndpointFactory
from uno.api.error_handlers import configure_error_handlers
from uno.schema.schema_manager import UnoSchemaManager

# Create FastAPI app
app = FastAPI(title="Product API")

# Configure error handlers
configure_error_handlers(app)

# Define model
class Product(BaseModel):
    id: str = ""
    name: str
    description: Optional[str] = None
    price: float
    sku: str
    inventory_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    
    # Required class variables
    display_name: str = "Product"
    display_name_plural: str = "Products"
    
    # Schema manager
    schema_manager = UnoSchemaManager()
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    @classmethod
    async def get(cls, id: str):
        """Get a product by ID."""
        # Implementation with database access
        # For demo, return a mock product
        if id == "not-found":
            return None
            
        return Product(
            id=id,
            name="Example Product",
            description="This is an example product",
            price=29.99,
            sku=f"SKU-{id}"
        )
    
    @classmethod
    async def filter(cls, filters=None, page=1, page_size=50):
        """Filter products."""
        # Implementation with database query
        # For demo, return mock data
        products = [
            Product(
                id=f"prod-{i}",
                name=f"Product {i}",
                price=10.0 + i,
                sku=f"SKU-{i}"
            )
            for i in range(1, 6)
        ]
        
        # Apply filtering
        if filters and "min_price" in filters:
            products = [p for p in products if p.price >= filters["min_price"]]
            
        # Apply pagination
        start = (page - 1) * page_size
        end = start + page_size
        
        # Create paginated result
        class PaginatedResult:
            def __init__(self, items, total, page, page_size):
                self.items = items
                self.total = total
                self.page = page
                self.page_size = page_size
                
        return PaginatedResult(
            items=products[start:end],
            total=len(products),
            page=page,
            page_size=page_size
        )
    
    @classmethod
    async def save(cls, body, importing=False):
        """Save a product."""
        # Implementation with database save
        # For demo, just create a product instance
        data = body.model_dump()
        
        # Generate ID if not provided
        if not data.get("id"):
            data["id"] = f"prod-{hash(data['name']) % 1000}"
            
        return Product(**data)
    
    @classmethod
    async def delete_(cls, id):
        """Delete a product."""
        # Implementation with database delete
        # For demo, just return success
        return True
    
    @classmethod
    def create_filter_params(cls):
        """Create filter parameters."""
        # Define filter parameters
        class ProductFilterParams(BaseModel):
            name: Optional[str] = None
            min_price: Optional[float] = None
            max_price: Optional[float] = None
            in_stock: Optional[bool] = None
            
        return ProductFilterParams
    
    @classmethod
    def validate_filter_params(cls, params):
        """Validate and process filter parameters."""
        if params is None:
            return {}
            
        filters = {}
        
        # Copy valid parameters
        if hasattr(params, "name") and params.name:
            filters["name"] = params.name
            
        if hasattr(params, "min_price") and params.min_price is not None:
            filters["min_price"] = params.min_price
            
        if hasattr(params, "max_price") and params.max_price is not None:
            filters["max_price"] = params.max_price
            
        if hasattr(params, "in_stock") and params.in_stock is not None:
            filters["in_stock"] = params.in_stock
        
        # Validate filter combinations
        if "min_price" in filters and "max_price" in filters:
            if filters["min_price"] > filters["max_price"]:
                raise ValidationError("min_price must be less than max_price")
                
        return filters

# Define schemas
class ProductCreateSchema(BaseModel):
    name: str = Field(..., description="Product name", min_length=3)
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price", gt=0)
    sku: str = Field(..., description="Stock keeping unit")
    inventory_count: int = Field(0, description="Inventory count", ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Premium Headphones",
                "description": "Noise-cancelling wireless headphones",
                "price": 199.99,
                "sku": "SKU-HEADPHONE-1",
                "inventory_count": 45
            }
        }
    }

class ProductUpdateSchema(BaseModel):
    name: Optional[str] = Field(None, description="Product name", min_length=3)
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price", gt=0)
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    inventory_count: Optional[int] = Field(None, description="Inventory count", ge=0)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "price": 179.99,
                "inventory_count": 50
            }
        }
    }

class ProductViewSchema(BaseModel):
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    sku: str = Field(..., description="Stock keeping unit")
    inventory_count: int = Field(..., description="Inventory count")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    # Computed fields
    @computed_field
    def is_in_stock(self) -> bool:
        return self.inventory_count > 0
        
    @computed_field
    def price_with_tax(self) -> float:
        return round(self.price * 1.1, 2)

# Register schemas with the model
Product.schema_manager.register_schema("edit_schema", ProductCreateSchema)
Product.schema_manager.register_schema("update_schema", ProductUpdateSchema)
Product.schema_manager.register_schema("view_schema", ProductViewSchema)

# Create endpoints using the factory
factory = UnoEndpointFactory()
factory.create_endpoints(
    app=app,
    model_obj=Product,
    endpoints=["Create", "View", "List", "Update", "Delete"]
)

# Run the app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

This example creates:
- `POST /api/v1/product` - Create a product
- `GET /api/v1/product/{id}` - Get a product by ID
- `GET /api/v1/product` - List products (with filtering)
- `PATCH /api/v1/product/{id}` - Update a product
- `DELETE /api/v1/product/{id}` - Delete a product

## Advanced Features

### Filtering and Pagination

The `ListEndpoint` automatically supports filtering and pagination:

```
GET /api/v1/product?name=Headphones&min_price=50&page=2&page_size=20
```

Filter parameters are defined in your model's `create_filter_params()` method and processed in the `validate_filter_params()` method.

### Field Selection

All endpoints support field selection for partial responses:

```
GET /api/v1/product/123?fields=id,name,price
GET /api/v1/product?fields=id,name,price
```

This allows clients to request only the fields they need, reducing response size.

### Streaming Responses

The `ListEndpoint` supports streaming for large datasets:

```
GET /api/v1/product?stream=true
```

Set the `Accept` header to `application/x-ndjson` to receive newline-delimited JSON.

### Error Handling

UnoEndpoint integrates with Uno's error handling system to provide consistent error responses:

```python
# Configure error handlers
from uno.api.error_handlers import configure_error_handlers
configure_error_handlers(app)
```

Error responses follow a consistent format:

```json
{
  "code": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "field1": "Error details for field1",
    "field2": "Error details for field2"
  },
  "help_text": "Optional help text to guide users"
}
```

### Custom Endpoint Types

You can create custom endpoint types by subclassing `UnoEndpoint` and implementing a custom router:

```python
class ExportRouter(UnoRouter):
    """Router for exporting data as CSV."""
    
    path_suffix: str = "/export"
    method: str = "GET"
    
    @computed_field
    def summary(self) -> str:
        return f"Export {self.model.display_name_plural} as CSV"
        
    @computed_field
    def description(self) -> str:
        return f"Export all {self.model.display_name_plural} as CSV file"
    
    def endpoint_factory(self):
        async def endpoint(self):
            # Get all items
            items = await self.model.filter(limit=1000)
            
            # Convert to CSV
            csv_content = "id,name,price,sku\n"
            for item in items:
                csv_content += f"{item.id},{item.name},{item.price},{item.sku}\n"
            
            # Return CSV response
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename={self.model.__name__.lower()}.csv"
                }
            )
            
        setattr(self.__class__, "endpoint", endpoint)

class ExportEndpoint(UnoEndpoint):
    """Endpoint for exporting data as CSV."""
    
    router: UnoRouter = ExportRouter
    body_model: UnoSchema = None
    response_model: UnoSchema = None
```

Then use it like any other endpoint:

```python
ExportEndpoint(model=Product, app=app)
```

## Best Practices

### 1. Use the EndpointFactory

Always use `UnoEndpointFactory` to create standard endpoints:

```python
factory = UnoEndpointFactory()
factory.create_endpoints(
    app=app,
    model_obj=Product,
    endpoints=["Create", "View", "List", "Update", "Delete"]
)
```

### 2. Model Schema Organization

Organize your model schemas clearly:

```python
# Main edit schema for creating/updating
class ProductEditSchema(BaseModel):
    name: str
    price: float
    # ...

# View schema for responses
class ProductViewSchema(BaseModel):
    id: str
    name: str
    price: float
    created_at: datetime
    # ...

# Register with the model
Product.schema_manager.register_schema("edit_schema", ProductEditSchema)
Product.schema_manager.register_schema("view_schema", ProductViewSchema)
```

### 3. Consistent Error Handling

Use the error handling system for consistent responses:

```python
from uno.api.error_handlers import configure_error_handlers
configure_error_handlers(app)
```

### 4. Field Validation

Add detailed validation to your schemas:

```python
class ProductCreateSchema(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    price: float = Field(..., gt=0, lt=10000)
    sku: str = Field(..., pattern=r"^[A-Z0-9-]+$")
```

### 5. Documentation

Add examples and descriptions to your schemas:

```python
class ProductCreateSchema(BaseModel):
    name: str = Field(
        ..., 
        description="Product name (3-50 characters)",
        min_length=3, 
        max_length=50
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Premium Headphones",
                "price": 199.99
            }
        }
    }
```

### 6. Testing

Create comprehensive tests for your endpoints:

```python
def test_create_product():
    client = TestClient(app)
    response = client.post(
        "/api/v1/product",
        json={"name": "Test Product", "price": 10.99, "sku": "TEST-123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Product"
    assert data["price"] == 10.99
```

## Common Patterns

### Adding Computed Fields

Use Pydantic's `computed_field` for derived data:

```python
class ProductViewSchema(BaseModel):
    id: str
    price: float
    
    @computed_field
    def price_with_tax(self) -> float:
        return round(self.price * 1.1, 2)
```

### Custom Filtering Logic

Implement custom filtering in your model:

```python
@classmethod
def validate_filter_params(cls, params):
    """Process filter parameters."""
    filters = {}
    
    # Text search with case-insensitive matching
    if hasattr(params, "search") and params.search:
        filters["search"] = params.search.lower()
    
    # Date range filtering
    if hasattr(params, "start_date") and params.start_date:
        filters["start_date"] = params.start_date
        
    if hasattr(params, "end_date") and params.end_date:
        filters["end_date"] = params.end_date
    
    return filters
```

### Adding Authorization

Add authorization to your model methods:

```python
@classmethod
async def get(cls, id: str, *, user_context=None):
    """Get a product by ID with authorization."""
    # Verify permissions
    if user_context and not user_context.has_permission("products:read"):
        raise AuthorizationError("You don't have permission to access this product")
        
    # Proceed with retrieval
    product = await cls._get_from_database(id)
    return product
```

### Custom Response Headers

Add custom headers in your router:

```python
def endpoint_factory(self):
    async def endpoint(self, id: str, response: Response):
        # Get the entity
        result = await self.model.get(id=id)
        
        # Add custom headers
        response.headers["X-Custom-Header"] = "Custom Value"
        response.headers["X-Rate-Limit"] = "100"
        
        return result
        
    endpoint.__annotations__["return"] = self.response_model
    setattr(self.__class__, "endpoint", endpoint)
```