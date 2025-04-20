"""
Example demonstrating OpenAPI documentation capabilities.

This example shows how to use the OpenAPI documentation utilities
to enhance API documentation with examples, descriptions, and security information.
"""

import asyncio
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.core.errors.result import Result, Success
from uno.domain.entity.service import CrudService

from uno.api.endpoint.openapi import OpenApiEnhancer, ResponseExample
from uno.api.endpoint.openapi_extensions import (
    DocumentedCrudEndpoint,
    DocumentedQueryEndpoint,
    DocumentedCommandEndpoint,
    DocumentedCqrsEndpoint,
    DocumentedFilterableCrudEndpoint,
)
from uno.api.endpoint.cqrs import CommandHandler, CqrsEndpoint, QueryHandler


# Example models
class ProductCreateDTO(BaseModel):
    """Data transfer object for creating a product."""

    name: str = Field(..., description="The name of the product")
    description: str = Field(..., description="A description of the product")
    price: float = Field(..., gt=0, description="The price of the product")
    category: str = Field(..., description="The category of the product")


class ProductUpdateDTO(BaseModel):
    """Data transfer object for updating a product."""

    name: Optional[str] = Field(None, description="The name of the product")
    description: Optional[str] = Field(None, description="A description of the product")
    price: Optional[float] = Field(None, gt=0, description="The price of the product")
    category: Optional[str] = Field(None, description="The category of the product")


class ProductResponseDTO(BaseModel):
    """Data transfer object for product responses."""

    id: str = Field(..., description="The unique identifier of the product")
    name: str = Field(..., description="The name of the product")
    description: str = Field(..., description="A description of the product")
    price: float = Field(..., description="The price of the product")
    category: str = Field(..., description="The category of the product")
    created_at: str = Field(..., description="The creation timestamp")
    updated_at: str = Field(..., description="The last update timestamp")


# Example service implementation
class ProductService(CrudService):
    """Example product service for demonstration purposes."""

    async def create(self, data: ProductCreateDTO) -> Result[ProductResponseDTO]:
        """Create a new product."""
        # Simulated product creation
        product = ProductResponseDTO(
            id="123",
            name=data.name,
            description=data.description,
            price=data.price,
            category=data.category,
            created_at="2025-04-18T12:00:00Z",
            updated_at="2025-04-18T12:00:00Z",
        )
        return Success(product)

    async def get_by_id(self, id: str) -> Result[ProductResponseDTO]:
        """Get a product by ID."""
        # Simulated product retrieval
        if id == "123":
            product = ProductResponseDTO(
                id=id,
                name="Example Product",
                description="This is an example product",
                price=99.99,
                category="Example Category",
                created_at="2025-04-18T12:00:00Z",
                updated_at="2025-04-18T12:00:00Z",
            )
            return Success(product)
        return Error("Product not found", code="NOT_FOUND")

    async def get_all(self) -> Result[list[ProductResponseDTO]]:
        """Get all products."""
        # Simulated product list
        products = [
            ProductResponseDTO(
                id="123",
                name="Example Product",
                description="This is an example product",
                price=99.99,
                category="Example Category",
                created_at="2025-04-18T12:00:00Z",
                updated_at="2025-04-18T12:00:00Z",
            )
        ]
        return Success(products)

    async def update(
        self, id: str, data: ProductUpdateDTO
    ) -> Result[ProductResponseDTO]:
        """Update a product."""
        # Simulated product update
        if id == "123":
            product = ProductResponseDTO(
                id=id,
                name=data.name or "Example Product",
                description=data.description or "This is an example product",
                price=data.price or 99.99,
                category=data.category or "Example Category",
                created_at="2025-04-18T12:00:00Z",
                updated_at="2025-04-18T12:30:00Z",
            )
            return Success(product)
        return Error("Product not found", code="NOT_FOUND")

    async def delete(self, id: str) -> Result[None]:
        """Delete a product."""
        # Simulated product deletion
        if id == "123":
            return Success(None)
        return Error("Product not found", code="NOT_FOUND")


# CQRS Models
class GetProductsByCategoryQuery(BaseModel):
    """Query to get products by category."""

    category: str = Field(..., description="The category to filter by")


class CreateProductDiscountCommand(BaseModel):
    """Command to create a product discount."""

    product_id: str = Field(..., description="The ID of the product")
    discount_percentage: float = Field(
        ..., gt=0, lt=100, description="The discount percentage"
    )
    valid_until: str = Field(..., description="The expiration date of the discount")


class DiscountResponseDTO(BaseModel):
    """Response DTO for discount creation."""

    id: str = Field(..., description="The unique identifier of the discount")
    product_id: str = Field(..., description="The ID of the product")
    discount_percentage: float = Field(..., description="The discount percentage")
    valid_until: str = Field(..., description="The expiration date of the discount")
    created_at: str = Field(..., description="The creation timestamp")


# Example CQRS handlers
class GetProductsByCategoryHandler:
    """Handler for GetProductsByCategoryQuery."""

    async def execute(
        self, query: GetProductsByCategoryQuery
    ) -> Result[list[ProductResponseDTO]]:
        """Execute the query."""
        # Simulated query execution
        products = [
            ProductResponseDTO(
                id="123",
                name="Example Product",
                description="This is an example product",
                price=99.99,
                category=query.category,
                created_at="2025-04-18T12:00:00Z",
                updated_at="2025-04-18T12:00:00Z",
            )
        ]
        return Success(products)


class CreateProductDiscountHandler:
    """Handler for CreateProductDiscountCommand."""

    async def execute(
        self, command: CreateProductDiscountCommand
    ) -> Result[DiscountResponseDTO]:
        """Execute the command."""
        # Simulated command execution
        discount = DiscountResponseDTO(
            id="456",
            product_id=command.product_id,
            discount_percentage=command.discount_percentage,
            valid_until=command.valid_until,
            created_at="2025-04-18T12:00:00Z",
        )
        return Success(discount)


def create_app():
    """Create and configure a FastAPI application with documented endpoints."""
    app = FastAPI(
        title="Example API",
        description="An example API demonstrating OpenAPI documentation capabilities",
        version="1.0.0",
    )

    # Initialize OpenAPI enhancer
    enhancer = OpenApiEnhancer(app)

    # Configure JWT authentication
    enhancer.setup_jwt_auth(
        description="JWT token authentication for secure endpoints",
        scheme_name="BearerAuth",
    )

    # Add tags with descriptions
    enhancer.add_tag(
        name="Products",
        description="Operations related to products",
        external_docs={
            "url": "https://example.com/docs/products",
            "description": "Product documentation",
        },
    )
    enhancer.add_tag(
        name="Discounts",
        description="Operations related to product discounts",
        external_docs={
            "url": "https://example.com/docs/discounts",
            "description": "Discount documentation",
        },
    )

    # Create a product service
    product_service = ProductService()

    # Example 1: Documented CRUD endpoint
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
                    "content": {
                        "id": "123",
                        "name": "New Product",
                        "description": "A brand new product",
                        "price": 49.99,
                        "category": "Electronics",
                        "created_at": "2025-04-18T12:00:00Z",
                        "updated_at": "2025-04-18T12:00:00Z",
                    },
                    "description": "The product was created successfully",
                },
                "400": {
                    "content": {
                        "message": "Invalid input data",
                        "code": "VALIDATION_ERROR",
                        "details": {"price": ["must be greater than 0"]},
                    },
                    "description": "The request contained invalid data",
                },
            }
        },
    )

    # Example 2: Documented CQRS endpoint
    # Create query and command handlers
    get_products_by_category_handler = GetProductsByCategoryHandler()
    create_product_discount_handler = CreateProductDiscountHandler()

    # Create CQRS endpoint
    cqrs_endpoint = DocumentedCqrsEndpoint(
        queries=[
            QueryHandler(
                path="/products/by-category",
                handler=get_products_by_category_handler.execute,
                query_model=GetProductsByCategoryQuery,
                response_model=list[ProductResponseDTO],
                name="GetProductsByCategory",
            ),
        ],
        commands=[
            CommandHandler(
                path="/products/{product_id}/discounts",
                handler=create_product_discount_handler.execute,
                command_model=CreateProductDiscountCommand,
                response_model=DiscountResponseDTO,
                name="CreateProductDiscount",
            ),
        ],
        tags=["Products", "Discounts"],
        summary="Product and discount operations",
        description="Endpoints for querying products and managing discounts",
        operation_examples={
            "query_GetProductsByCategory": {
                "200": {
                    "content": [
                        {
                            "id": "123",
                            "name": "Example Product",
                            "description": "This is an example product",
                            "price": 99.99,
                            "category": "Electronics",
                            "created_at": "2025-04-18T12:00:00Z",
                            "updated_at": "2025-04-18T12:00:00Z",
                        }
                    ],
                    "description": "Products in the requested category",
                },
            },
            "command_CreateProductDiscount": {
                "201": {
                    "content": {
                        "id": "456",
                        "product_id": "123",
                        "discount_percentage": 10.5,
                        "valid_until": "2025-05-18T12:00:00Z",
                        "created_at": "2025-04-18T12:00:00Z",
                    },
                    "description": "The discount was created successfully",
                },
            },
        },
    )

    # Example 3: Documented filterable CRUD endpoint
    filterable_product_endpoint = DocumentedFilterableCrudEndpoint(
        service=product_service,
        create_model=ProductCreateDTO,
        update_model=ProductUpdateDTO,
        response_model=ProductResponseDTO,
        path="/filterable-products",
        tags=["Products"],
        summary="Filterable product management endpoints",
        description="Endpoints for creating, retrieving, updating, and deleting products with filtering capabilities",
        filter_fields=["name", "category", "price"],
        use_graph_backend=True,  # Demonstrate Apache AGE integration
    )

    # Register all endpoints with the application
    product_endpoint.register(app)
    cqrs_endpoint.register(app)
    filterable_product_endpoint.register(app)

    # Manually add some additional OpenAPI documentation
    enhancer.document_operation(
        "/products",
        "get",
        summary="List all products",
        description=(
            "Returns a list of all products in the catalog.\n\n"
            "Use this endpoint when you need to display all available products."
        ),
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
                        "category": "Example Category",
                        "created_at": "2025-04-18T12:00:00Z",
                        "updated_at": "2025-04-18T12:00:00Z",
                    }
                ],
                description="A list of products was retrieved successfully",
            ),
        },
    )

    return app


# For testing purposes
if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
