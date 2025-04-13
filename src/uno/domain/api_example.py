"""
Example of using the new dependency injection system in FastAPI endpoints.

This module demonstrates how to implement FastAPI endpoints using the new
dependency injection system in the Uno framework.
"""

from typing import List, Dict, Any, Optional
from fastapi import Path, Body, HTTPException, Query

from fastapi import APIRouter
# Legacy DIAPIRouter removed as part of backward compatibility removal
# Create regular APIRouter instead

from uno.domain.service_example import UserServiceProtocol

# Create a regular router instead of DIAPIRouter
router = APIRouter(
    prefix="/api/users",
    tags=["users"]
)


@router.get("/", response_model=None)
async def get_users(
    user_service: UserServiceProtocol = None,  # This will be injected automatically
    limit: int = Query(10, description="Maximum number of users to return")
) -> List[Dict[str, Any]]:
    """
    Get all users.
    
    Args:
        user_service: The user service (injected)
        limit: Maximum number of users to return
        
    Returns:
        A list of users
    """
    users = await user_service.get_users()
    return users[:limit]


@router.get("/{user_id}", response_model=None)
async def get_user(
    user_id: str = Path(..., description="The ID of the user to get"),
    user_service: UserServiceProtocol = None  # This will be injected automatically
) -> Dict[str, Any]:
    """
    Get a user by ID.
    
    Args:
        user_id: The user ID
        user_service: The user service (injected)
        
    Returns:
        The user data
    """
    user = await user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=None)
async def create_user(
    user_data: Dict[str, Any] = Body(..., description="The user data"),
    user_service: UserServiceProtocol = None  # This will be injected automatically
) -> Dict[str, Any]:
    """
    Create a new user.
    
    Args:
        user_data: The user data
        user_service: The user service (injected)
        
    Returns:
        The created user data
    """
    return await user_service.create_user(user_data)


@router.put("/{user_id}", response_model=None)
async def update_user(
    user_id: str = Path(..., description="The ID of the user to update"),
    user_data: Dict[str, Any] = Body(..., description="The updated user data"),
    user_service: UserServiceProtocol = None  # This will be injected automatically
) -> Dict[str, Any]:
    """
    Update a user.
    
    Args:
        user_id: The user ID
        user_data: The updated user data
        user_service: The user service (injected)
        
    Returns:
        The updated user data
    """
    user = await user_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", response_model=None)
async def delete_user(
    user_id: str = Path(..., description="The ID of the user to delete"),
    user_service: UserServiceProtocol = None  # This will be injected automatically
) -> Dict[str, Any]:
    """
    Delete a user.
    
    Args:
        user_id: The user ID
        user_service: The user service (injected)
        
    Returns:
        A confirmation message
    """
    success = await user_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"success": True, "message": f"User {user_id} deleted"}