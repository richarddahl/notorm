"""
Product API endpoints for the e-commerce application.

This module implements FastAPI endpoints for product management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from examples.ecommerce.domain.entities import User, Product
from examples.ecommerce.domain.services import ProductService
from examples.ecommerce.domain.value_objects import Money, Rating

from examples.ecommerce.api.dto.product import (
    ProductResponse, CreateProductRequest, UpdateProductRequest,
    ProductSearchParams, InventoryUpdateRequest, AddRatingRequest
)
from examples.ecommerce.api.dto.common import (
    ErrorResponse, PaginatedResponse, PaginationParams
)
from examples.ecommerce.api.dependencies import (
    get_product_service, get_current_user
)
from examples.ecommerce.api.mapper import map_product_to_response


router = APIRouter(
    prefix="/products",
    tags=["products"],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    }
)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: CreateProductRequest,
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Create a new product.
    
    This endpoint allows creating a new product in the catalog.
    Requires administrator privileges.
    """
    # Check if user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create products"
        )
    
    try:
        # Create the product
        product = await product_service.create_product({
            "name": product_data.name,
            "description": product_data.description,
            "price": product_data.price,
            "currency": product_data.currency,
            "category_id": product_data.category_id,
            "inventory_count": product_data.inventory_count,
            "attributes": product_data.attributes or {}
        })
        
        return map_product_to_response(product)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=PaginatedResponse)
async def search_products(
    params: ProductSearchParams = Depends(),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Search for products.
    
    This endpoint allows searching for products based on various criteria.
    """
    try:
        # Calculate limit and offset
        limit, offset = params.page_size, (params.page - 1) * params.page_size
        
        # Search for products
        products = await product_service.search_products(
            query=params.query,
            category_id=params.category_id,
            min_price=params.min_price,
            max_price=params.max_price,
            in_stock_only=params.in_stock_only,
            limit=limit,
            offset=offset
        )
        
        # Get total count (in a real implementation, this would be a separate query)
        total = await product_service.repository.count(filters={})
        
        # Map to response DTOs
        product_responses = [map_product_to_response(p) for p in products]
        
        # Create paginated response
        pagination = PaginationParams(page=params.page, page_size=params.page_size)
        return PaginatedResponse.create(
            items=product_responses,
            total=total,
            pagination=pagination
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str = Path(..., description="The ID of the product to retrieve"),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Get a product by ID.
    
    This endpoint retrieves a specific product by its ID.
    """
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return map_product_to_response(product)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    update_data: UpdateProductRequest,
    product_id: str = Path(..., description="The ID of the product to update"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Update a product.
    
    This endpoint allows updating a product's details.
    Requires administrator privileges.
    """
    # Check if user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update products"
        )
    
    # Get the product
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        # Update basic details
        if update_data.name is not None:
            product.name = update_data.name
        if update_data.description is not None:
            product.description = update_data.description
        if update_data.category_id is not None:
            product.category_id = update_data.category_id
        
        # Update price if provided
        if update_data.price is not None:
            currency = update_data.currency or product.price.currency
            product.update_price(Money(amount=update_data.price, currency=currency))
        
        # Update inventory if provided
        if update_data.inventory_count is not None:
            product.update_inventory(update_data.inventory_count)
        
        # Update active status if provided
        if update_data.is_active is not None:
            if update_data.is_active:
                product.reactivate()
            else:
                product.deactivate()
        
        # Update attributes if provided
        if update_data.attributes is not None:
            for key, value in update_data.attributes.items():
                product.update_attribute(key, value)
        
        # Save the product
        updated_product = await product_service.save(product)
        
        return map_product_to_response(updated_product)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{product_id}/inventory", response_model=ProductResponse)
async def update_inventory(
    update_data: InventoryUpdateRequest,
    product_id: str = Path(..., description="The ID of the product to update"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Update product inventory.
    
    This endpoint allows updating a product's inventory count.
    Requires administrator privileges.
    """
    # Check if user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update inventory"
        )
    
    try:
        # Update the inventory
        updated_product = await product_service.update_inventory(
            product_id=product_id,
            change=update_data.change,
            reason=update_data.reason
        )
        
        if not updated_product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inventory update failed"
            )
        
        return map_product_to_response(updated_product)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{product_id}/ratings", response_model=ProductResponse)
async def add_rating(
    rating_data: AddRatingRequest,
    product_id: str = Path(..., description="The ID of the product to rate"),
    current_user: User = Depends(get_current_user),
    product_service: ProductService = Depends(get_product_service)
):
    """
    Add a rating to a product.
    
    This endpoint allows adding a rating and optional review to a product.
    """
    # Get the product
    product = await product_service.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    try:
        # Create the rating
        rating = Rating(
            score=rating_data.score,
            comment=rating_data.comment
        )
        
        # Add the rating to the product
        product.add_rating(rating)
        
        # Save the product
        updated_product = await product_service.save(product)
        
        return map_product_to_response(updated_product)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )