"""
API endpoints for the authorization domain.

This module provides FastAPI endpoints for the authorization domain,
using dependency injection for services and repositories.

IMPORTANT NOTE:
This module uses a different pattern than the standard UnoObj approach.
It demonstrates how to use dependency injection with FastAPI directly,
while the rest of the application uses the UnoObj pattern.
"""

from typing import List, Optional, Annotated
import logging

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.fastapi import get_db_session, get_repository
from uno.authorization.models import UserModel, GroupModel
from uno.authorization.repositories import UserRepository, GroupRepository
from uno.authorization.services import UserService, GroupService
from uno.schema.schema_manager import UnoSchemaManager

# Create schema manager for generating response models
schema_manager = UnoSchemaManager()

# Generate Pydantic schemas for our models
UserSchema = schema_manager.get_schema(UserModel)
UserListSchema = schema_manager.get_list_schema(UserModel)
GroupSchema = schema_manager.get_schema(GroupModel)
GroupListSchema = schema_manager.get_list_schema(GroupModel)

# Create router
router = APIRouter(prefix="/api/v1.0", tags=["Authorization"])


@router.get(
    "/users",
    response_model=UserListSchema,
    summary="List users",
    description="Retrieve a list of users based on optional filters"
)
async def list_users(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    group_id: Optional[str] = Query(None, description="Filter by group ID"),
    role_id: Optional[str] = Query(None, description="Filter by role ID"),
    superusers_only: bool = Query(False, description="Filter to only superusers"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_repository(UserRepository))
):
    """
    List users with optional filtering.
    
    This endpoint supports filtering by tenant, group, role, or superuser status.
    Results are paginated using limit and offset parameters.
    """
    # Create and use the service
    service = UserService(repository)
    
    users = await service.execute(
        tenant_id=tenant_id,
        group_id=group_id,
        role_id=role_id,
        superusers_only=superusers_only,
        limit=limit,
        offset=offset
    )
    
    # Convert to schema
    user_schemas = [UserSchema.model_validate(user) for user in users]
    return {"items": user_schemas, "count": len(user_schemas)}


@router.get(
    "/users/{user_id}",
    response_model=UserSchema,
    summary="Get user by ID",
    description="Retrieve a specific user by their ID"
)
async def get_user(
    user_id: str,
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_repository(UserRepository))
):
    """Get a specific user by ID."""
    user = await repository.get(user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    return UserSchema.model_validate(user)


@router.get(
    "/users/lookup/{identifier}",
    response_model=UserSchema,
    summary="Look up user by email or handle",
    description="Retrieve a user by their email address or handle"
)
async def lookup_user(
    identifier: str,
    tenant_id: Optional[str] = Query(None, description="Tenant ID for handle lookups"),
    session: AsyncSession = Depends(get_db_session),
    repository: UserRepository = Depends(get_repository(UserRepository))
):
    """
    Look up a user by email address or handle.
    
    This endpoint first tries to find a user by email (which is unique across tenants),
    then falls back to searching by handle within the specified tenant.
    """
    # Create and use the service
    service = UserService(repository)
    
    user = await service.get_user_by_email_or_handle(
        identifier=identifier,
        tenant_id=tenant_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with identifier {identifier} not found"
        )
    
    return UserSchema.model_validate(user)


@router.get(
    "/groups",
    response_model=GroupListSchema,
    summary="List groups",
    description="Retrieve a list of groups based on optional filters"
)
async def list_groups(
    tenant_id: Optional[str] = Query(None, description="Filter by tenant ID"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    name: Optional[str] = Query(None, description="Filter by group name"),
    limit: int = Query(100, description="Maximum number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    session: AsyncSession = Depends(get_db_session),
    repository: GroupRepository = Depends(get_repository(GroupRepository))
):
    """
    List groups with optional filtering.
    
    This endpoint supports filtering by tenant, user, or name.
    Results are paginated using limit and offset parameters.
    """
    # Create and use the service
    service = GroupService(repository)
    
    groups = await service.execute(
        tenant_id=tenant_id,
        user_id=user_id,
        name=name,
        limit=limit,
        offset=offset
    )
    
    # Convert to schema
    group_schemas = [GroupSchema.model_validate(group) for group in groups]
    return {"items": group_schemas, "count": len(group_schemas)}


@router.get(
    "/groups/{group_id}",
    response_model=GroupSchema,
    summary="Get group by ID",
    description="Retrieve a specific group by its ID"
)
async def get_group(
    group_id: str,
    session: AsyncSession = Depends(get_db_session),
    repository: GroupRepository = Depends(get_repository(GroupRepository))
):
    """Get a specific group by ID."""
    group = await repository.get(group_id)
    
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    return GroupSchema.model_validate(group)