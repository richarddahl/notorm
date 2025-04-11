"""
User API endpoints for the e-commerce application.

This module implements FastAPI endpoints for user management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from examples.ecommerce.domain.entities import User
from examples.ecommerce.domain.services import UserService
from examples.ecommerce.domain.value_objects import EmailAddress, PhoneNumber

from examples.ecommerce.api.dto.user import (
    UserResponse, CreateUserRequest, UpdateUserRequest
)
from examples.ecommerce.api.dto.common import ErrorResponse
from examples.ecommerce.api.dependencies import get_user_service, get_current_user
from examples.ecommerce.api.mapper import (
    map_user_to_response, map_dto_to_address
)


router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
        status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
        status.HTTP_403_FORBIDDEN: {"model": ErrorResponse},
    }
)


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get the current user's profile.
    
    This endpoint returns the profile information for the authenticated user.
    """
    return map_user_to_response(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_current_user_profile(
    update_data: UpdateUserRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Update the current user's profile.
    
    This endpoint allows the authenticated user to update their profile information.
    """
    # Update name if provided
    if update_data.first_name is not None:
        current_user.first_name = update_data.first_name
    if update_data.last_name is not None:
        current_user.last_name = update_data.last_name
    
    # Update phone if provided
    if update_data.phone is not None:
        try:
            current_user.phone = PhoneNumber(number=update_data.phone)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid phone number: {str(e)}"
            )
    
    # Update addresses if provided
    billing_address = None
    shipping_address = None
    use_billing_for_shipping = None
    
    if update_data.billing_address is not None:
        billing_address = map_dto_to_address(update_data.billing_address)
    
    if update_data.shipping_address is not None:
        shipping_address = map_dto_to_address(update_data.shipping_address)
    
    if update_data.use_billing_for_shipping is not None:
        use_billing_for_shipping = update_data.use_billing_for_shipping
    
    if billing_address is not None or shipping_address is not None or use_billing_for_shipping is not None:
        current_user.update_addresses(
            billing_address=billing_address,
            shipping_address=shipping_address,
            use_billing_for_shipping=use_billing_for_shipping or False
        )
    
    # Save the updated user
    updated_user = await user_service.save(current_user)
    
    return map_user_to_response(updated_user)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_profile(
    user_data: CreateUserRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Create a new user profile.
    
    This endpoint allows creating a new user profile.
    Note: In a real application, this would typically be part of the registration flow.
    """
    try:
        # Convert DTOs to domain objects
        billing_address = map_dto_to_address(user_data.billing_address)
        shipping_address = map_dto_to_address(user_data.shipping_address)
        
        if user_data.use_billing_for_shipping and billing_address:
            shipping_address = billing_address
        
        # Register the user
        user = await user_service.register_user({
            "username": user_data.username,
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "billing_address": billing_address,
            "shipping_address": shipping_address
        })
        
        return map_user_to_response(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )