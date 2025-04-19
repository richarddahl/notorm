"""
Migration example from legacy API patterns to the unified endpoint framework.

This example demonstrates how to migrate from legacy API patterns to the new unified endpoint framework.
"""

from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint import (
    BaseEndpoint,
    CommandHandler,
    CqrsEndpoint,
    CrudEndpoint,
    CrudEndpointFactory,
    DataResponse,
    EndpointFactory,
    PaginatedResponse,
    QueryHandler,
    create_api,
)
from uno.domain.entity.service import ApplicationService, CrudService, DomainService, ServiceFactory
from uno.core.errors.result import Result, Success

# Define models
class ProductSchema(BaseModel):
    """Product schema."""
    
    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(..., description="Whether the product is active")


class CreateProductRequest(BaseModel):
    """Create product request."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(True, description="Whether the product is active")


class UpdateProductRequest(BaseModel):
    """Update product request."""
    
    name: Optional[str] = Field(None, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    stock: Optional[int] = Field(None, description="Product stock")
    is_active: Optional[bool] = Field(None, description="Whether the product is active")


# Query and Command models for CQRS
class ProductSearchQuery(BaseModel):
    """Product search query."""
    
    name: Optional[str] = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    category_id: Optional[str] = Field(None, description="Category ID")


class CreateProductCommand(BaseModel):
    """Create product command."""
    
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    category_id: str = Field(..., description="Category ID")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(True, description="Whether the product is active")


# Example services
class ProductService(CrudService):
    """Example product service implementing CRUD operations."""
    
    async def create(self, data):
        # In a real service, this would create a product in the database
        return Success({"id": "new-id", **data})
    
    async def get_by_id(self, id):
        # In a real service, this would get a product from the database
        return Success({
            "id": id,
            "name": "Example Product",
            "description": "This is an example product",
            "price": 19.99,
            "stock": 100,
            "is_active": True,
        })
    
    async def update(self, id, data):
        # In a real service, this would update a product in the database
        return Success({
            "id": id,
            **data,
        })
    
    async def delete(self, id):
        # In a real service, this would delete a product from the database
        return Success(True)
    
    async def find(self, criteria=None):
        # In a real service, this would find products in the database
        return Success([
            {
                "id": "1",
                "name": "Product 1",
                "description": "This is product 1",
                "price": 19.99,
                "stock": 100,
                "is_active": True,
            },
            {
                "id": "2",
                "name": "Product 2",
                "description": "This is product 2",
                "price": 29.99,
                "stock": 50,
                "is_active": True,
            },
        ])


class SearchProductsService(ApplicationService):
    """Example search products service implementing a query operation."""
    
    async def execute(self, query: ProductSearchQuery) -> Result[List[ProductSchema]]:
        """Execute the search products query."""
        # In a real service, this would search products in the database
        results = [
            ProductSchema(
                id="1",
                name="Product 1",
                description="This is product 1",
                price=19.99,
                stock=100,
                is_active=True,
            ),
            ProductSchema(
                id="2",
                name="Product 2",
                description="This is product 2",
                price=29.99,
                stock=50,
                is_active=True,
            ),
        ]
        
        # Filter results based on query parameters
        if query.name:
            results = [r for r in results if query.name.lower() in r.name.lower()]
        if query.min_price is not None:
            results = [r for r in results if r.price >= query.min_price]
        if query.max_price is not None:
            results = [r for r in results if r.price <= query.max_price]
        
        return Success(results)


class CreateProductService(ApplicationService):
    """Example create product service implementing a command operation."""
    
    async def execute(self, command: CreateProductCommand) -> Result[ProductSchema]:
        """Execute the create product command."""
        # In a real service, this would create a product in the database
        product = ProductSchema(
            id="new-id",
            name=command.name,
            description=command.description,
            price=command.price,
            stock=command.stock,
            is_active=command.is_active,
        )
        
        return Success(product)


# Example 1: Migrating CRUD endpoints
def example_crud_migration():
    """Example of migrating CRUD endpoints."""
    
    print("Example: Migrating CRUD endpoints")
    print("--------------------------------")
    
    # Legacy pattern (would typically use UnoEndpoint, CreateEndpoint, etc.)
    print("Legacy pattern:")
    print("app = FastAPI()")
    print("adapter = EntityServiceAdapter(")
    print("    service=ProductService(),")
    print("    entity_type=Product,")
    print("    input_model=CreateProductRequest,")
    print("    output_model=ProductSchema,")
    print(")")
    print("create_endpoint = CreateEndpoint(")
    print("    model=adapter,")
    print("    app=app,")
    print("    path_prefix='/api/products',")
    print("    tags=['Products'],")
    print(")")
    print("view_endpoint = ViewEndpoint(")
    print("    model=adapter,")
    print("    app=app,")
    print("    path_prefix='/api/products',")
    print("    tags=['Products'],")
    print(")")
    print("# ... and so on for other endpoints")
    
    # New pattern with unified endpoint framework
    print("\nNew pattern with unified endpoint framework:")
    print("app = create_api(title='Product API', description='API for managing products')")
    print("endpoint = CrudEndpoint(")
    print("    service=ProductService(),")
    print("    create_model=CreateProductRequest,")
    print("    response_model=ProductSchema,")
    print("    update_model=UpdateProductRequest,")
    print("    tags=['Products'],")
    print("    path='/api/products',")
    print(")")
    print("endpoint.register(app)")
    
    # Create a real example
    app = create_api(title="Product API", description="API for managing products")
    endpoint = CrudEndpoint(
        service=ProductService(),
        create_model=CreateProductRequest,
        response_model=ProductSchema,
        update_model=UpdateProductRequest,
        tags=["Products"],
        path="/api/products",
    )
    endpoint.register(app)
    
    # Show the generated routes
    print("\nGenerated routes:")
    for route in app.routes:
        print(f"  {route.path} ({route.methods})")


# Example 2: Migrating to CQRS pattern
def example_cqrs_migration():
    """Example of migrating to CQRS pattern."""
    
    print("\nExample: Migrating to CQRS pattern")
    print("--------------------------------")
    
    # Legacy pattern (would typically use DomainServiceAdapter and direct FastAPI routes)
    print("Legacy pattern:")
    print("app = FastAPI()")
    print("factory = DomainServiceEndpointFactory()")
    print("factory.create_domain_service_endpoint(")
    print("    app=app,")
    print("    service_class=SearchProductsService,")
    print("    path='/api/products/search',")
    print("    method='GET',")
    print("    tags=['Products'],")
    print("    summary='Search for products',")
    print(")")
    print("factory.create_domain_service_endpoint(")
    print("    app=app,")
    print("    service_class=CreateProductService,")
    print("    path='/api/products',")
    print("    method='POST',")
    print("    tags=['Products'],")
    print("    summary='Create a product',")
    print(")")
    
    # New pattern with unified endpoint framework and CQRS
    print("\nNew pattern with unified endpoint framework and CQRS:")
    print("app = create_api(title='Product CQRS API', description='API for managing products using CQRS')")
    print("# Create query handler")
    print("search_query = QueryHandler(")
    print("    service=SearchProductsService(),")
    print("    response_model=List[ProductSchema],")
    print("    query_model=ProductSearchQuery,")
    print("    path='/search',")
    print("    method='get',")
    print(")")
    print("# Create command handler")
    print("create_command = CommandHandler(")
    print("    service=CreateProductService(),")
    print("    command_model=CreateProductCommand,")
    print("    response_model=ProductSchema,")
    print("    path='',")
    print("    method='post',")
    print(")")
    print("# Create and register CQRS endpoint")
    print("endpoint = CqrsEndpoint(")
    print("    queries=[search_query],")
    print("    commands=[create_command],")
    print("    tags=['Products'],")
    print("    base_path='/api/products',")
    print(")")
    print("endpoint.register(app)")
    
    # Create a real example
    app = create_api(title="Product CQRS API", description="API for managing products using CQRS")
    
    # Create query handler
    search_query = QueryHandler(
        service=SearchProductsService(),
        response_model=List[ProductSchema],
        query_model=ProductSearchQuery,
        path="/search",
        method="get",
    )
    
    # Create command handler
    create_command = CommandHandler(
        service=CreateProductService(),
        command_model=CreateProductCommand,
        response_model=ProductSchema,
        path="",
        method="post",
    )
    
    # Create and register CQRS endpoint
    endpoint = CqrsEndpoint(
        queries=[search_query],
        commands=[create_command],
        tags=["Products"],
        base_path="/api/products",
    )
    endpoint.register(app)
    
    # Show the generated routes
    print("\nGenerated routes:")
    for route in app.routes:
        print(f"  {route.path} ({route.methods})")


# Example 3: Using the factory pattern
def example_factory_pattern():
    """Example of using the factory pattern."""
    
    print("\nExample: Using the factory pattern")
    print("--------------------------------")
    
    # Legacy pattern (would typically use DomainServiceEndpointFactory)
    print("Legacy pattern:")
    print("app = FastAPI()")
    print("factory = DomainServiceEndpointFactory()")
    print("factory.create_entity_service_endpoints(")
    print("    app=app,")
    print("    entity_type=Product,")
    print("    path_prefix='/api/products',")
    print("    tags=['Products'],")
    print("    input_model=ProductInput,")
    print("    output_model=ProductOutput,")
    print(")")
    
    # New pattern with unified endpoint framework and factory
    print("\nNew pattern with unified endpoint framework and factory:")
    print("app = create_api(title='Product Factory API', description='API for managing products using factory')")
    print("# Create service factory")
    print("service_factory = ServiceFactory()")
    print("# Create endpoint factory")
    print("factory = CrudEndpointFactory.from_schema(")
    print("    service_factory=service_factory,")
    print("    entity_name='Product',")
    print("    schema=ProductSchema,")
    print("    tags=['Products'],")
    print("    path_prefix='/api',")
    print("    exclude_fields=['created_at', 'updated_at'],")
    print("    readonly_fields=['id'],")
    print(")")
    print("# Create and register endpoints")
    print("factory.create_endpoints(app)")
    
    # Create a real example
    app = create_api(title="Product Factory API", description="API for managing products using factory")
    
    # Create mock service factory
    class MockServiceFactory(ServiceFactory):
        def create_crud_service(self, entity_name):
            return ProductService()
    
    # Create endpoint factory
    factory = CrudEndpointFactory.from_schema(
        service_factory=MockServiceFactory(),
        entity_name="Product",
        schema=ProductSchema,
        tags=["Products"],
        path_prefix="/api",
        exclude_fields=["created_at", "updated_at"],
        readonly_fields=["id"],
    )
    
    # Create and register endpoints
    factory.create_endpoints(app)
    
    # Show the generated routes
    print("\nGenerated routes:")
    for route in app.routes:
        print(f"  {route.path} ({route.methods})")


if __name__ == "__main__":
    example_crud_migration()
    example_cqrs_migration()
    example_factory_pattern()