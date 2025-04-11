"""
Order API endpoints for the e-commerce application.

This module implements FastAPI endpoints for order management.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import List, Optional

from examples.ecommerce.domain.entities import User, Order
from examples.ecommerce.domain.services import OrderService
from examples.ecommerce.domain.value_objects import Address

from examples.ecommerce.api.dto.order import (
    OrderResponse, CreateOrderRequest, ProcessPaymentRequest,
    UpdateOrderStatusRequest, CancelOrderRequest
)
from examples.ecommerce.api.dto.common import (
    ErrorResponse, PaginatedResponse, PaginationParams
)
from examples.ecommerce.api.dependencies import (
    get_order_service, get_current_user
)
from examples.ecommerce.api.mapper import (
    map_order_to_response, map_dto_to_address
)


router = APIRouter(
    prefix="/orders",
    tags=["orders"],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    }
)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: CreateOrderRequest,
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Create a new order.
    
    This endpoint allows creating a new order with the specified items.
    """
    try:
        # Convert DTOs to domain objects
        shipping_address = map_dto_to_address(order_data.shipping_address)
        billing_address = map_dto_to_address(order_data.billing_address)
        
        # Prepare items
        items = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity
            }
            for item in order_data.items
        ]
        
        # Create the order
        order, errors = await order_service.create_order(
            user_id=current_user.id,
            shipping_address=shipping_address,
            billing_address=billing_address,
            items=items
        )
        
        # If there are errors but order is created, return warnings
        if errors and order:
            # In a real implementation, we'd return warnings alongside the order
            pass
        
        # If there are errors and no order, raise an exception
        if errors and not order:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=errors[0]  # Return the first error
            )
        
        return map_order_to_response(order)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=PaginatedResponse)
async def get_user_orders(
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get the current user's orders.
    
    This endpoint returns all orders for the authenticated user.
    """
    try:
        # Calculate limit and offset
        limit, offset = pagination.get_limit_offset()
        
        # Get orders
        orders = await order_service.get_orders_for_user(
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        # Get total count (in a real implementation, this would be a separate query)
        total = await order_service.repository.count(filters={"user_id": current_user.id})
        
        # Map to response DTOs
        order_responses = [map_order_to_response(o) for o in orders]
        
        # Create paginated response
        return PaginatedResponse.create(
            items=order_responses,
            total=total,
            pagination=pagination
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: str = Path(..., description="The ID of the order to retrieve"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Get an order by ID.
    
    This endpoint retrieves a specific order by its ID.
    """
    order = await order_service.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if the order belongs to the current user or if user is admin
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return map_order_to_response(order)


@router.post("/{order_id}/payment", response_model=OrderResponse)
async def process_payment(
    payment_data: ProcessPaymentRequest,
    order_id: str = Path(..., description="The ID of the order to process payment for"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Process payment for an order.
    
    This endpoint processes a payment for the specified order.
    """
    # Get the order
    order = await order_service.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Process the payment
        updated_order, error = await order_service.process_payment(
            order_id=order_id,
            payment_method=payment_data.payment_method,
            payment_details=payment_data.payment_details
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return map_order_to_response(updated_order)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    status_data: UpdateOrderStatusRequest,
    order_id: str = Path(..., description="The ID of the order to update"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Update an order's status.
    
    This endpoint updates the status of the specified order.
    Requires administrator privileges.
    """
    # Check if user is an admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update order status"
        )
    
    try:
        # Update the order status
        updated_order, error = await order_service.update_order_status(
            order_id=order_id,
            new_status=status_data.status,
            notes=status_data.notes
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return map_order_to_response(updated_order)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    cancel_data: CancelOrderRequest,
    order_id: str = Path(..., description="The ID of the order to cancel"),
    current_user: User = Depends(get_current_user),
    order_service: OrderService = Depends(get_order_service)
):
    """
    Cancel an order.
    
    This endpoint cancels the specified order.
    """
    # Get the order
    order = await order_service.get_by_id(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check if the order belongs to the current user or if user is admin
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Cancel the order
        updated_order, error = await order_service.cancel_order(
            order_id=order_id,
            reason=cancel_data.reason
        )
        
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error
            )
        
        return map_order_to_response(updated_order)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )