# CQRS Pattern in the Unified Endpoint Framework

This guide explains how to implement the Command Query Responsibility Segregation (CQRS) pattern using the Unified Endpoint Framework.

## What is CQRS?

Command Query Responsibility Segregation (CQRS) is a pattern that separates read and write operations for a data store:

- **Commands**: Write operations that modify state (create, update, delete)
- **Queries**: Read operations that return data without modifying state

By separating these concerns, CQRS allows for more scalable, maintainable, and performant systems.

## CQRS Components in the Framework

The Unified Endpoint Framework provides first-class support for CQRS with the following components:

### QueryHandler

Handles read operations with standardized patterns:

```python
class QueryHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a query operation in a CQRS endpoint."""
    
    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        response_model: Type[ResponseModel],
        query_model: Optional[Type[RequestModel]] = None,
        path: str = "",
        method: str = "get",
    ):
        """Initialize a new query handler."""
        # Implementation details...
```

### CommandHandler

Handles write operations with standardized patterns:

```python
class CommandHandler(Generic[RequestModel, ResponseModel]):
    """Handler for a command operation in a CQRS endpoint."""
    
    def __init__(
        self,
        service: Union[ApplicationService, DomainService],
        command_model: Type[RequestModel],
        response_model: Optional[Type[ResponseModel]] = None,
        path: str = "",
        method: str = "post",
    ):
        """Initialize a new command handler."""
        # Implementation details...
```

### CqrsEndpoint

Combines query and command handlers into a single endpoint:

```python
class CqrsEndpoint(BaseEndpoint[RequestModel, ResponseModel, IdType]):
    """Endpoint that implements the CQRS pattern."""
    
    def __init__(
        self,
        *,
        queries: list[QueryHandler] = None,
        commands: list[CommandHandler] = None,
        router: Optional[APIRouter] = None,
        tags: list[str] | None = None,
        base_path: str = "",
    ):
        """Initialize a new CQRS endpoint instance."""
        # Implementation details...
    
    def add_query(self, query: QueryHandler) -> "CqrsEndpoint":
        """Add a query handler to this endpoint."""
        # Implementation details...
    
    def add_command(self, command: CommandHandler) -> "CqrsEndpoint":
        """Add a command handler to this endpoint."""
        # Implementation details...
```

## Implementing CQRS Endpoints

### Step 1: Define Command and Query Models

First, define your command and query models using Pydantic:

```python
class ProductSearchQuery(BaseModel):
    """Query model for searching products."""
    
    name: str | None = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    category: str | None = Field(None, description="Product category")


class ProductSearchResult(BaseModel):
    """Result model for product search."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")


class CreateProductCommand(BaseModel):
    """Command model for creating a product."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    stock: int = Field(..., description="Product stock")


class ProductCreatedResult(BaseModel):
    """Result model for product creation."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
```

### Step 2: Implement Query and Command Services

Next, implement the services that will handle the queries and commands:

```python
class SearchProductsService(ApplicationService):
    """Service for searching products."""
    
    async def execute(self, query: ProductSearchQuery) -> Result[list[ProductSearchResult]]:
        """Execute the search query."""
        # Query implementation...


class CreateProductService(ApplicationService):
    """Service for creating a product."""
    
    async def execute(self, command: CreateProductCommand) -> Result[ProductCreatedResult]:
        """Execute the create product command."""
        # Command implementation...
```

### Step 3: Create QueryHandler and CommandHandler Instances

Create the handlers for your queries and commands:

```python
# Create query handler
search_query = QueryHandler(
    service=search_service,
    response_model=list[ProductSearchResult],
    query_model=ProductSearchQuery,
    path="/search",
    method="get",
)

# Create command handler
create_command = CommandHandler(
    service=create_service,
    command_model=CreateProductCommand,
    response_model=ProductCreatedResult,
    path="",
    method="post",
)
```

### Step 4: Create and Register CqrsEndpoint

Finally, create and register the CQRS endpoint:

```python
# Create CQRS endpoint
endpoint = CqrsEndpoint(
    queries=[search_query],
    commands=[create_command],
    tags=["Products"],
    base_path="/api/products",
)

# Register the endpoint
endpoint.register(app)
```

### Adding Handlers Dynamically

You can also add handlers dynamically:

```python
# Create CQRS endpoint
endpoint = CqrsEndpoint(
    tags=["Products"],
    base_path="/api/products",
)

# Add query handler
endpoint.add_query(search_query)

# Add command handler
endpoint.add_command(create_command)

# Register the endpoint
endpoint.register(app)
```

## Complete Example

Here's a complete example of implementing CQRS endpoints for a product catalog:

```python
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint, QueryHandler
from uno.api.endpoint.integration import create_api
from uno.core.errors.result import Result, Success
from uno.domain.entity.service import ApplicationService


# Domain models and services
class ProductSearchQuery(BaseModel):
    """Query model for searching products."""
    
    name: str | None = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    category: str | None = Field(None, description="Product category")


class ProductSearchResult(BaseModel):
    """Result model for product search."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")


class CreateProductCommand(BaseModel):
    """Command model for creating a product."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category: str = Field(..., description="Product category")
    stock: int = Field(..., description="Product stock")


class ProductCreatedResult(BaseModel):
    """Result model for product creation."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")


# Query handlers
class SearchProductsService(ApplicationService):
    """Service for searching products."""
    
    async def execute(self, query: ProductSearchQuery) -> Result[list[ProductSearchResult]]:
        """Execute the search query."""
        # In a real application, this would query the database
        results = [
            ProductSearchResult(
                id="1",
                name="Product 1",
                price=10.0,
                category="Category 1",
            ),
            ProductSearchResult(
                id="2",
                name="Product 2",
                price=20.0,
                category="Category 2",
            ),
        ]
        
        # Filter results based on query parameters
        if query.name:
            results = [r for r in results if query.name.lower() in r.name.lower()]
        if query.min_price is not None:
            results = [r for r in results if r.price >= query.min_price]
        if query.max_price is not None:
            results = [r for r in results if r.price <= query.max_price]
        if query.category:
            results = [r for r in results if r.category == query.category]
        
        return Success(results)


# Command handlers
class CreateProductService(ApplicationService):
    """Service for creating a product."""
    
    async def execute(self, command: CreateProductCommand) -> Result[ProductCreatedResult]:
        """Execute the create product command."""
        # In a real application, this would create a product in the database
        result = ProductCreatedResult(
            id="new-product-id",
            name=command.name,
        )
        
        return Success(result)


def create_product_endpoints(app: FastAPI) -> CqrsEndpoint:
    """Create and register product CQRS endpoints."""
    # Create services
    search_service = SearchProductsService()
    create_service = CreateProductService()
    
    # Create query handlers
    search_query = QueryHandler(
        service=search_service,
        response_model=list[ProductSearchResult],
        query_model=ProductSearchQuery,
        path="/search",
        method="get",
    )
    
    # Create command handlers
    create_command = CommandHandler(
        service=create_service,
        command_model=CreateProductCommand,
        response_model=ProductCreatedResult,
        path="",
        method="post",
    )
    
    # Create CQRS endpoint
    endpoint = CqrsEndpoint(
        queries=[search_query],
        commands=[create_command],
        tags=["Products"],
        base_path="/api/products",
    )
    
    # Register the endpoint
    endpoint.register(app)
    
    return endpoint


def create_app() -> FastAPI:
    """Create a FastAPI application with product CQRS endpoints."""
    # Create the API
    app = create_api(
        title="Product CQRS API",
        description="API for managing products using CQRS pattern",
        version="1.0.0",
    )
    
    # Create and register product endpoints
    create_product_endpoints(app)
    
    return app
```

## Benefits of CQRS

Using the CQRS pattern with the Unified Endpoint Framework provides several benefits:

1. **Separation of Concerns**: Read and write operations are clearly separated
2. **Optimization**: Query and command models can be optimized independently
3. **Scalability**: Read and write operations can be scaled independently
4. **Flexibility**: Different data stores can be used for reads and writes
5. **Performance**: Read operations can use denormalized views for better performance

## When to Use CQRS

CQRS is particularly useful for:

- Complex domains with different read and write requirements
- Applications with high read-to-write ratios
- Systems where performance and scalability are critical
- Scenarios requiring event sourcing or complex audit trails

For simpler applications, the standard `CrudEndpoint` may be more appropriate and requires less boilerplate code.

## Next Steps

- [Advanced CQRS with Event Sourcing](../advanced/event_sourcing.md)
- [Implementing Read Models](../advanced/read_models.md)
- [Performance Optimization for CQRS](../advanced/cqrs_performance.md)