"""
Product API endpoints for the catalog context.

This module defines the REST API endpoints for working with products.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from decimal import Decimal

from uno.api.service_endpoint_adapter import DomainServiceAdapter
from uno.core.errors.result import Result
from uno.domain.unit_of_work import UnitOfWorkManager

from uno.examples.ecommerce_app.catalog.domain.entities import Product
from uno.examples.ecommerce_app.catalog.domain.value_objects import ProductStatus
from uno.examples.ecommerce_app.catalog.services.product_service import (
    ProductService,
    ProductQueryService,
    ProductCreateCommand,
    ProductUpdateCommand,
    ProductListQuery,
    ProductDetailQuery,
    ProductVariantDTO,
    ProductImageDTO,
    ProductWeightDTO,
    ProductDimensionsDTO,
)


# Create router
router = APIRouter(prefix="/api/catalog/products", tags=["catalog"])


# DTO models for API responses
class ProductResponse(ProductCreateCommand):
    """Product response model."""

    id: str
    version: int
    created_at: str
    updated_at: Optional[str] = None


class ProductVariantResponse(ProductVariantDTO):
    """Product variant response model."""

    id: str
    created_at: str
    updated_at: Optional[str] = None


class ProductImageResponse(ProductImageDTO):
    """Product image response model."""

    id: str
    created_at: str
    updated_at: Optional[str] = None


class ProductListResponse(ProductResponse):
    """Simplified product response for list views."""

    class Config:
        from_attributes = True


class ProductSummaryResponse(ProductResponse):
    """Summary of a product with minimal information."""

    class Config:
        from_attributes = True


# Dependency functions
def get_product_service(uow_manager: UnitOfWorkManager = Depends()) -> ProductService:
    """Get product service as a FastAPI dependency."""
    uow = uow_manager.create_uow()
    return ProductService(uow=uow)


def get_product_query_service(
    uow_manager: UnitOfWorkManager = Depends(),
) -> ProductQueryService:
    """Get product query service as a FastAPI dependency."""
    uow = uow_manager.create_uow()
    return ProductQueryService(uow=uow)


# Adapter functions
def product_to_response(product: Product) -> ProductResponse:
    """Convert a product entity to API response model."""
    response = ProductResponse(
        id=str(product.id),
        name=product.name,
        slug=product.slug,
        description=product.description,
        sku=product.sku,
        price_amount=product.price.amount,
        price_currency=product.price.currency,
        status=product.status,
        inventory_quantity=product.inventory.quantity,
        inventory_reserved=product.inventory.reserved,
        inventory_backorderable=product.inventory.backorderable,
        inventory_restock_threshold=product.inventory.restock_threshold,
        category_ids=product.category_ids,
        attributes=product.attributes,
        tags=product.tags,
        seo_title=product.seo_title,
        seo_description=product.seo_description,
        version=product.version,
        created_at=product.created_at.isoformat() if product.created_at else None,
        updated_at=product.updated_at.isoformat() if product.updated_at else None,
    )

    # Add weight if available
    if product.weight:
        response.weight = ProductWeightDTO(
            value=product.weight.value, unit=product.weight.unit
        )

    # Add dimensions if available
    if product.dimensions:
        response.dimensions = ProductDimensionsDTO(
            length=product.dimensions.length,
            width=product.dimensions.width,
            height=product.dimensions.height,
            unit=product.dimensions.unit,
        )

    # Add variants
    response.variants = [
        ProductVariantResponse(
            id=str(variant.id),
            sku=variant.sku,
            name=variant.name,
            price_amount=variant.price.amount,
            price_currency=variant.price.currency,
            inventory_quantity=variant.inventory.quantity,
            inventory_reserved=variant.inventory.reserved,
            inventory_backorderable=variant.inventory.backorderable,
            inventory_restock_threshold=variant.inventory.restock_threshold,
            attributes=variant.attributes,
            is_active=variant.is_active,
            created_at=variant.created_at.isoformat() if variant.created_at else None,
            updated_at=variant.updated_at.isoformat() if variant.updated_at else None,
        )
        for variant in product.variants
    ]

    # Add images
    response.images = [
        ProductImageResponse(
            id=str(image.id),
            url=image.url,
            alt_text=image.alt_text,
            sort_order=image.sort_order,
            is_primary=image.is_primary,
            created_at=image.created_at.isoformat() if image.created_at else None,
            updated_at=image.updated_at.isoformat() if image.updated_at else None,
        )
        for image in product.images
    ]

    return response


def product_list_to_response(products: List[Product]) -> List[ProductSummaryResponse]:
    """Convert a list of product entities to API response model."""
    return [
        ProductSummaryResponse(
            id=str(product.id),
            name=product.name,
            slug=product.slug,
            description=product.description,
            sku=product.sku,
            price_amount=product.price.amount,
            price_currency=product.price.currency,
            status=product.status,
            inventory_quantity=product.inventory.quantity,
            category_ids=product.category_ids,
            tags=product.tags,
            version=product.version,
            created_at=product.created_at.isoformat() if product.created_at else None,
            updated_at=product.updated_at.isoformat() if product.updated_at else None,
            variants=[],  # Simplified response without variants
            images=[
                ProductImageResponse(
                    id=str(image.id),
                    url=image.url,
                    alt_text=image.alt_text,
                    sort_order=image.sort_order,
                    is_primary=image.is_primary,
                    created_at=(
                        image.created_at.isoformat() if image.created_at else None
                    ),
                    updated_at=(
                        image.updated_at.isoformat() if image.updated_at else None
                    ),
                )
                for image in product.images
                if image.is_primary
            ][
                :1
            ],  # Only include the primary image
        )
        for product in products
    ]


# API endpoints
@router.get("/", response_model=List[ProductSummaryResponse])
async def list_products(
    status: Optional[str] = Query(None, description="Filter by product status"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    search: Optional[str] = Query(None, description="Search products by name"),
    min_price: Optional[Decimal] = Query(None, description="Minimum price"),
    max_price: Optional[Decimal] = Query(None, description="Maximum price"),
    limit: Optional[int] = Query(
        50, description="Maximum number of products to return"
    ),
    offset: Optional[int] = Query(0, description="Number of products to skip"),
    sort_by: Optional[str] = Query("name", description="Field to sort by"),
    sort_direction: Optional[str] = Query(
        "asc", description="Sort direction (asc or desc)"
    ),
    query_service: ProductQueryService = Depends(get_product_query_service),
):
    """
    List products with filtering and pagination.

    Parameters:
    - status: Filter by product status (draft, active, inactive, discontinued)
    - category_id: Filter by category ID
    - search: Search products by name
    - min_price: Minimum price filter
    - max_price: Maximum price filter
    - limit: Maximum number of products to return
    - offset: Number of products to skip
    - sort_by: Field to sort by (name, price, created_at)
    - sort_direction: Sort direction (asc or desc)
    """
    query = ProductListQuery(
        status=status,
        category_id=category_id,
        search_term=search,
        min_price=min_price,
        max_price=max_price,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_direction=sort_direction,
    )

    adapter = DomainServiceAdapter[ProductListQuery, List[Product]](query_service)
    result: Result[List[Product]] = await adapter.execute(query)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return product_list_to_response(result.value)


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(..., description="The ID of the product"),
    query_service: ProductQueryService = Depends(get_product_query_service),
):
    """
    Get detailed information for a specific product.

    Parameters:
    - product_id: The ID of the product
    """
    query = ProductDetailQuery(id=product_id)

    adapter = DomainServiceAdapter[ProductDetailQuery, Product](query_service)
    result: Result[Product] = await adapter.execute(query)

    if result.is_failure:
        raise HTTPException(
            status_code=404, detail=f"Product not found: {result.error}"
        )

    return product_to_response(result.value)


@router.post("/", response_model=ProductResponse, status_code=201)
async def create_product(
    command: ProductCreateCommand,
    service: ProductService = Depends(get_product_service),
):
    """
    Create a new product.

    The request body should contain all required product details.
    """
    adapter = DomainServiceAdapter[ProductCreateCommand, Product](service)
    result: Result[Product] = await adapter.execute(command)

    if result.is_failure:
        raise HTTPException(status_code=400, detail=result.error)

    return product_to_response(result.value)


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str = Path(..., description="The ID of the product"),
    command: ProductUpdateCommand = None,
    service: ProductService = Depends(get_product_service),
):
    """
    Update an existing product.

    Parameters:
    - product_id: The ID of the product to update

    The request body should contain the fields to update.
    """
    # Ensure product_id in path matches the one in the command
    if command.id != product_id:
        raise HTTPException(
            status_code=400,
            detail="Product ID in path does not match ID in request body",
        )

    adapter = DomainServiceAdapter[ProductUpdateCommand, Product](service)
    result: Result[Product] = await adapter.execute(command)

    if result.is_failure:
        if "not found" in result.error:
            raise HTTPException(status_code=404, detail=result.error)
        if "Concurrency conflict" in result.error:
            raise HTTPException(status_code=409, detail=result.error)
        raise HTTPException(status_code=400, detail=result.error)

    return product_to_response(result.value)
