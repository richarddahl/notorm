"""
Example implementation of CQRS endpoints with the unified endpoint framework.

This module demonstrates how to use the unified endpoint framework to create
CQRS endpoints that separate read and write operations.
"""

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

    name: Optional[str] = Field(None, description="Product name contains")
    min_price: Optional[float] = Field(None, description="Minimum price")
    max_price: Optional[float] = Field(None, description="Maximum price")
    category: Optional[str] = Field(None, description="Product category")


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


class UpdateProductPriceCommand(BaseModel):
    """Command model for updating a product's price."""

    product_id: str = Field(..., description="Product ID")
    new_price: float = Field(..., description="New product price")


# Query handlers
class SearchProductsService(ApplicationService):
    """Service for searching products."""

    async def execute(
        self, query: ProductSearchQuery
    ) -> Result[list[ProductSearchResult]]:
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


class GetFeaturedProductsService(ApplicationService):
    """Service for getting featured products."""

    async def execute(self) -> Result[list[ProductSearchResult]]:
        """Execute the query for featured products."""
        # In a real application, this would query the database
        results = [
            ProductSearchResult(
                id="1",
                name="Featured Product 1",
                price=10.0,
                category="Category 1",
            ),
            ProductSearchResult(
                id="2",
                name="Featured Product 2",
                price=20.0,
                category="Category 2",
            ),
        ]

        return Success(results)


# Command handlers
class CreateProductService(ApplicationService):
    """Service for creating a product."""

    async def execute(
        self, command: CreateProductCommand
    ) -> Result[ProductCreatedResult]:
        """Execute the create product command."""
        # In a real application, this would create a product in the database
        result = ProductCreatedResult(
            id="new-product-id",
            name=command.name,
        )

        return Success(result)


class UpdateProductPriceService(ApplicationService):
    """Service for updating a product's price."""

    async def execute(self, command: UpdateProductPriceCommand) -> Result[None]:
        """Execute the update product price command."""
        # In a real application, this would update the product in the database
        # Here we just return a success result with no value
        return Success(None)


def create_product_endpoints(app: FastAPI) -> CqrsEndpoint:
    """
    Create and register product CQRS endpoints.

    Args:
        app: The FastAPI application to register endpoints with.

    Returns:
        The created CqrsEndpoint instance.
    """
    # Create services
    search_service = SearchProductsService()
    featured_service = GetFeaturedProductsService()
    create_service = CreateProductService()
    update_price_service = UpdateProductPriceService()

    # Create query handlers
    search_query = QueryHandler(
        service=search_service,
        response_model=list[ProductSearchResult],
        query_model=ProductSearchQuery,
        path="/search",
        method="get",
    )

    featured_query = QueryHandler(
        service=featured_service,
        response_model=list[ProductSearchResult],
        path="/featured",
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

    update_price_command = CommandHandler(
        service=update_price_service,
        command_model=UpdateProductPriceCommand,
        path="/update-price",
        method="put",
    )

    # Create CQRS endpoint
    endpoint = CqrsEndpoint(
        queries=[search_query, featured_query],
        commands=[create_command, update_price_command],
        tags=["Products"],
        base_path="/api/products",
    )

    # Register the endpoint
    endpoint.register(app)

    return endpoint


def create_app() -> FastAPI:
    """
    Create a FastAPI application with product CQRS endpoints.

    Returns:
        A FastAPI application with product CQRS endpoints.
    """
    # Create the API
    app = create_api(
        title="Product CQRS API",
        description="API for managing products using CQRS pattern",
        version="1.0.0",
    )

    # Create and register product endpoints
    create_product_endpoints(app)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
