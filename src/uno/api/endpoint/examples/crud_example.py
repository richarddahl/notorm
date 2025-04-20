"""
Example implementation of CRUD endpoints with the unified endpoint framework.

This module demonstrates how to use the unified endpoint framework to create
CRUD endpoints for a domain entity.
"""

from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from uno.api.endpoint.base import CrudEndpoint
from uno.api.endpoint.factory import CrudEndpointFactory
from uno.api.endpoint.integration import create_api
from uno.domain.entity.examples.service_example import (
    Product,
    ProductCreateDTO,
    ProductDTO,
    ProductService,
    ProductUpdateDTO,
)
from uno.domain.entity.service import CrudService


class ProductResponse(BaseModel):
    """Product response model."""

    id: str = Field(..., description="Product ID")
    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(..., description="Whether the product is active")


class CreateProductRequest(BaseModel):
    """Create product request model."""

    name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    price: float = Field(..., description="Product price")
    stock: int = Field(..., description="Product stock")
    is_active: bool = Field(True, description="Whether the product is active")


class UpdateProductRequest(BaseModel):
    """Update product request model."""

    name: str | None = Field(None, description="Product name")
    description: str | None = Field(None, description="Product description")
    price: Optional[float] = Field(None, description="Product price")
    stock: Optional[int] = Field(None, description="Product stock")
    is_active: Optional[bool] = Field(None, description="Whether the product is active")


def create_product_service() -> CrudService:
    """Create a product service for the example."""
    return ProductService()


def create_product_endpoints(app: FastAPI) -> CrudEndpoint:
    """
    Create and register product endpoints.

    Args:
        app: The FastAPI application to register endpoints with.

    Returns:
        The created CrudEndpoint instance.
    """
    # Create the product service
    service = create_product_service()

    # Create the endpoint
    endpoint = CrudEndpoint(
        service=service,
        create_model=CreateProductRequest,
        response_model=ProductResponse,
        update_model=UpdateProductRequest,
        tags=["Products"],
        path="/api/products",
    )

    # Register the endpoint
    endpoint.register(app)

    return endpoint


def create_app() -> FastAPI:
    """
    Create a FastAPI application with product endpoints.

    Returns:
        A FastAPI application with product endpoints.
    """
    # Create the API
    app = create_api(
        title="Product API",
        description="API for managing products",
        version="1.0.0",
    )

    # Create and register product endpoints
    create_product_endpoints(app)

    return app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
