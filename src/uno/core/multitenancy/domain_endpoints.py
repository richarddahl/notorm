"""
FastAPI endpoints for multi-tenancy.

This module provides HTTP API endpoints for managing tenants, user-tenant associations,
and tenant invitations.
"""

from typing import List, Optional, Dict, Any, Union
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from pydantic import BaseModel, Field, EmailStr

from uno.core.errors.result import Result
from uno.core.errors.catalog import ErrorCodes
from uno.dependencies.fastapi import inject_dependency

from .domain_services import (
    TenantServiceProtocol,
    UserTenantServiceProtocol,
    TenantInvitationServiceProtocol
)
from .entities import (
    TenantCreateRequest, TenantUpdateRequest, TenantResponse,
    UserTenantAssociationCreateRequest, UserTenantAssociationResponse,
    TenantInvitationCreateRequest, TenantInvitationResponse,
    TenantStatus, UserTenantStatus
)


# Pydantic models for API requests and responses
class TenantCreateRequestModel(BaseModel):
    """API request model for creating a tenant."""
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="URL-friendly identifier")
    tier: str = Field("standard", description="Tenant tier (e.g., basic, premium)")
    domain: Optional[str] = Field(None, description="Custom domain for the tenant")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Tenant metadata")


class TenantUpdateRequestModel(BaseModel):
    """API request model for updating a tenant."""
    name: Optional[str] = Field(None, description="Tenant name")
    domain: Optional[str] = Field(None, description="Custom domain for the tenant")
    tier: Optional[str] = Field(None, description="Tenant tier")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant settings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Tenant metadata")


class TenantResponseModel(BaseModel):
    """API response model for a tenant."""
    id: str = Field(..., description="Tenant ID")
    name: str = Field(..., description="Tenant name")
    slug: str = Field(..., description="URL-friendly identifier")
    status: str = Field(..., description="Tenant status")
    tier: str = Field(..., description="Tenant tier")
    domain: Optional[str] = Field(None, description="Custom domain for the tenant")
    settings: Dict[str, Any] = Field({}, description="Tenant settings")
    metadata: Dict[str, Any] = Field({}, description="Tenant metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TenantListResponseModel(BaseModel):
    """API response model for a list of tenants."""
    items: List[TenantResponseModel] = Field(..., description="List of tenants")
    total: int = Field(..., description="Total number of matching tenants")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(50, description="Number of items per page")
    next_page: Optional[int] = Field(None, description="Next page number, if available")
    prev_page: Optional[int] = Field(None, description="Previous page number, if available")


class UserTenantAssociationCreateRequestModel(BaseModel):
    """API request model for creating a user-tenant association."""
    user_id: str = Field(..., description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    roles: Optional[List[str]] = Field(None, description="User roles in this tenant")
    is_primary: Optional[bool] = Field(False, description="Is this the user's primary tenant")
    settings: Optional[Dict[str, Any]] = Field(None, description="Association settings")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Association metadata")


class UserTenantAssociationResponseModel(BaseModel):
    """API response model for a user-tenant association."""
    id: str = Field(..., description="Association ID")
    user_id: str = Field(..., description="User ID")
    tenant_id: str = Field(..., description="Tenant ID")
    roles: List[str] = Field([], description="User roles in this tenant")
    is_primary: bool = Field(False, description="Is this the user's primary tenant")
    status: str = Field(..., description="Association status")
    settings: Dict[str, Any] = Field({}, description="Association settings")
    metadata: Dict[str, Any] = Field({}, description="Association metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class TenantInvitationCreateRequestModel(BaseModel):
    """API request model for creating a tenant invitation."""
    tenant_id: str = Field(..., description="Tenant ID")
    email: EmailStr = Field(..., description="Invitee's email")
    roles: Optional[List[str]] = Field(None, description="Roles to grant to the user")
    expiration_days: Optional[int] = Field(7, description="Number of days until the invitation expires")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Invitation metadata")


class TenantInvitationResponseModel(BaseModel):
    """API response model for a tenant invitation."""
    id: str = Field(..., description="Invitation ID")
    tenant_id: str = Field(..., description="Tenant ID")
    email: str = Field(..., description="Invitee's email")
    roles: List[str] = Field([], description="Roles to grant to the user")
    invited_by: str = Field(..., description="ID of the user who sent the invitation")
    expires_at: datetime = Field(..., description="When the invitation expires")
    status: str = Field(..., description="Invitation status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AcceptInvitationRequestModel(BaseModel):
    """API request model for accepting a tenant invitation."""
    token: str = Field(..., description="Invitation token")
    user_id: str = Field(..., description="ID of the user accepting the invitation")


class DeclineInvitationRequestModel(BaseModel):
    """API request model for declining a tenant invitation."""
    token: str = Field(..., description="Invitation token")


# Create API router
router = APIRouter(prefix="/api/v1", tags=["Multi-tenancy"])


# Error handling helper function
def handle_result_error(result: Result) -> Any:
    """
    Handle errors from Result objects, raising appropriate HTTP exceptions.
    
    Args:
        result: The Result object to check for errors
        
    Returns:
        The result value if successful
        
    Raises:
        HTTPException: If the result is a failure
    """
    if result.is_failure():
        error = result.error
        status_code = status.HTTP_400_BAD_REQUEST
        
        if error.code == ErrorCodes.RESOURCE_NOT_FOUND:
            status_code = status.HTTP_404_NOT_FOUND
        elif error.code == ErrorCodes.DUPLICATE_RESOURCE:
            status_code = status.HTTP_409_CONFLICT
        elif error.code == ErrorCodes.UNAUTHORIZED:
            status_code = status.HTTP_401_UNAUTHORIZED
        elif error.code == ErrorCodes.FORBIDDEN:
            status_code = status.HTTP_403_FORBIDDEN
        elif error.code == ErrorCodes.INVALID_STATE:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        elif error.code == ErrorCodes.TENANT_REQUIRED:
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        
        raise HTTPException(
            status_code=status_code,
            detail={
                "code": error.code,
                "message": error.message,
                "context": error.context
            }
        )
    
    return result.value


# Tenant endpoints
@router.post(
    "/tenants",
    response_model=TenantResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant",
    description="Create a new tenant"
)
async def create_tenant(
    request: TenantCreateRequestModel = Body(...),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Create a new tenant."""
    # Convert to domain request
    domain_request = TenantCreateRequest(
        name=request.name,
        slug=request.slug,
        tier=request.tier,
        domain=request.domain,
        settings=request.settings,
        metadata=request.metadata
    )
    
    # Create the tenant
    result = await tenant_service.create_tenant(domain_request)
    tenant = handle_result_error(result)
    
    # Convert to response model
    return TenantResponseModel(
        id=tenant.id.value,
        name=tenant.name,
        slug=tenant.slug.value,
        status=tenant.status.value,
        tier=tenant.tier,
        domain=tenant.domain,
        settings=tenant.settings,
        metadata=tenant.metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.get(
    "/tenants/{tenant_id}",
    response_model=TenantResponseModel,
    summary="Get tenant",
    description="Get a tenant by ID"
)
async def get_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Get a tenant by ID."""
    # Get the tenant
    result = await tenant_service.get_tenant(tenant_id)
    tenant = handle_result_error(result)
    
    # Convert to response model
    return TenantResponseModel(
        id=tenant.id.value,
        name=tenant.name,
        slug=tenant.slug.value,
        status=tenant.status.value,
        tier=tenant.tier,
        domain=tenant.domain,
        settings=tenant.settings,
        metadata=tenant.metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.get(
    "/tenants",
    response_model=TenantListResponseModel,
    summary="List tenants",
    description="List tenants with filtering and pagination"
)
async def list_tenants(
    page: int = Query(1, gt=0, description="Page number"),
    page_size: int = Query(50, gt=0, le=100, description="Number of items per page"),
    status: Optional[str] = Query(None, description="Filter by status"),
    tier: Optional[str] = Query(None, description="Filter by tier"),
    name_contains: Optional[str] = Query(None, description="Filter by name containing text"),
    domain_contains: Optional[str] = Query(None, description="Filter by domain containing text"),
    sort_field: Optional[str] = Query(None, description="Field to sort by"),
    sort_direction: Optional[str] = Query("asc", description="Sort direction (asc or desc)"),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """List tenants with filtering and pagination."""
    # Build filters
    filters = {}
    if status:
        filters["status"] = status
    if tier:
        filters["tier"] = tier
    if name_contains:
        filters["name_contains"] = name_contains
    if domain_contains:
        filters["domain_contains"] = domain_contains
    
    # Get tenants
    result = await tenant_service.list_tenants(
        filters=filters,
        page=page,
        page_size=page_size,
        sort_field=sort_field,
        sort_direction=sort_direction
    )
    tenants = handle_result_error(result)
    
    # Get total count
    count_result = await tenant_service.count_tenants(filters=filters)
    total = handle_result_error(count_result)
    
    # Build response
    response = TenantListResponseModel(
        items=[
            TenantResponseModel(
                id=tenant.id.value,
                name=tenant.name,
                slug=tenant.slug.value,
                status=tenant.status.value,
                tier=tenant.tier,
                domain=tenant.domain,
                settings=tenant.settings,
                metadata=tenant.metadata,
                created_at=tenant.created_at,
                updated_at=tenant.updated_at
            )
            for tenant in tenants
        ],
        total=total,
        page=page,
        page_size=page_size
    )
    
    # Add pagination links
    if page > 1:
        response.prev_page = page - 1
    if (page * page_size) < total:
        response.next_page = page + 1
    
    return response


@router.patch(
    "/tenants/{tenant_id}",
    response_model=TenantResponseModel,
    summary="Update tenant",
    description="Update a tenant"
)
async def update_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    request: TenantUpdateRequestModel = Body(...),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Update a tenant."""
    # Convert to domain request
    domain_request = TenantUpdateRequest(
        name=request.name,
        domain=request.domain,
        tier=request.tier,
        settings=request.settings,
        metadata=request.metadata
    )
    
    # Update the tenant
    result = await tenant_service.update_tenant(tenant_id, domain_request)
    tenant = handle_result_error(result)
    
    # Convert to response model
    return TenantResponseModel(
        id=tenant.id.value,
        name=tenant.name,
        slug=tenant.slug.value,
        status=tenant.status.value,
        tier=tenant.tier,
        domain=tenant.domain,
        settings=tenant.settings,
        metadata=tenant.metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.delete(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant",
    description="Delete a tenant"
)
async def delete_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Delete a tenant."""
    # Delete the tenant
    result = await tenant_service.delete_tenant(tenant_id)
    handle_result_error(result)
    return None


@router.post(
    "/tenants/{tenant_id}/suspend",
    response_model=TenantResponseModel,
    summary="Suspend tenant",
    description="Suspend a tenant"
)
async def suspend_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Suspend a tenant."""
    # Suspend the tenant
    result = await tenant_service.suspend_tenant(tenant_id)
    tenant = handle_result_error(result)
    
    # Convert to response model
    return TenantResponseModel(
        id=tenant.id.value,
        name=tenant.name,
        slug=tenant.slug.value,
        status=tenant.status.value,
        tier=tenant.tier,
        domain=tenant.domain,
        settings=tenant.settings,
        metadata=tenant.metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


@router.post(
    "/tenants/{tenant_id}/activate",
    response_model=TenantResponseModel,
    summary="Activate tenant",
    description="Activate a tenant"
)
async def activate_tenant(
    tenant_id: str = Path(..., description="Tenant ID"),
    tenant_service: TenantServiceProtocol = Depends(inject_dependency(TenantServiceProtocol))
):
    """Activate a tenant."""
    # Activate the tenant
    result = await tenant_service.activate_tenant(tenant_id)
    tenant = handle_result_error(result)
    
    # Convert to response model
    return TenantResponseModel(
        id=tenant.id.value,
        name=tenant.name,
        slug=tenant.slug.value,
        status=tenant.status.value,
        tier=tenant.tier,
        domain=tenant.domain,
        settings=tenant.settings,
        metadata=tenant.metadata,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at
    )


# User-tenant association endpoints
@router.post(
    "/user-tenants",
    response_model=UserTenantAssociationResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create user-tenant association",
    description="Create a new user-tenant association"
)
async def create_user_tenant_association(
    request: UserTenantAssociationCreateRequestModel = Body(...),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Create a new user-tenant association."""
    # Convert to domain request
    domain_request = UserTenantAssociationCreateRequest(
        user_id=request.user_id,
        tenant_id=request.tenant_id,
        roles=request.roles,
        is_primary=request.is_primary,
        settings=request.settings,
        metadata=request.metadata
    )
    
    # Create the association
    result = await user_tenant_service.create_association(domain_request)
    association = handle_result_error(result)
    
    # Convert to response model
    return UserTenantAssociationResponseModel(
        id=association.id.value,
        user_id=association.user_id.value,
        tenant_id=association.tenant_id.value,
        roles=association.roles,
        is_primary=association.is_primary,
        status=association.status.value,
        settings=association.settings,
        metadata=association.metadata,
        created_at=association.created_at,
        updated_at=association.updated_at
    )


@router.get(
    "/user-tenants/{association_id}",
    response_model=UserTenantAssociationResponseModel,
    summary="Get user-tenant association",
    description="Get a user-tenant association by ID"
)
async def get_user_tenant_association(
    association_id: str = Path(..., description="Association ID"),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Get a user-tenant association by ID."""
    # Get the association
    result = await user_tenant_service.get_association(association_id)
    association = handle_result_error(result)
    
    # Convert to response model
    return UserTenantAssociationResponseModel(
        id=association.id.value,
        user_id=association.user_id.value,
        tenant_id=association.tenant_id.value,
        roles=association.roles,
        is_primary=association.is_primary,
        status=association.status.value,
        settings=association.settings,
        metadata=association.metadata,
        created_at=association.created_at,
        updated_at=association.updated_at
    )


@router.get(
    "/users/{user_id}/tenants",
    response_model=List[UserTenantAssociationResponseModel],
    summary="Get user tenants",
    description="Get all tenants associated with a user"
)
async def get_user_tenants(
    user_id: str = Path(..., description="User ID"),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Get all tenants associated with a user."""
    # Get the associations
    result = await user_tenant_service.get_user_tenants(user_id)
    associations = handle_result_error(result)
    
    # Convert to response models
    return [
        UserTenantAssociationResponseModel(
            id=association.id.value,
            user_id=association.user_id.value,
            tenant_id=association.tenant_id.value,
            roles=association.roles,
            is_primary=association.is_primary,
            status=association.status.value,
            settings=association.settings,
            metadata=association.metadata,
            created_at=association.created_at,
            updated_at=association.updated_at
        )
        for association in associations
    ]


@router.get(
    "/tenants/{tenant_id}/users",
    response_model=List[UserTenantAssociationResponseModel],
    summary="Get tenant users",
    description="Get all users associated with a tenant"
)
async def get_tenant_users(
    tenant_id: str = Path(..., description="Tenant ID"),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Get all users associated with a tenant."""
    # Get the associations
    result = await user_tenant_service.get_tenant_users(tenant_id)
    associations = handle_result_error(result)
    
    # Convert to response models
    return [
        UserTenantAssociationResponseModel(
            id=association.id.value,
            user_id=association.user_id.value,
            tenant_id=association.tenant_id.value,
            roles=association.roles,
            is_primary=association.is_primary,
            status=association.status.value,
            settings=association.settings,
            metadata=association.metadata,
            created_at=association.created_at,
            updated_at=association.updated_at
        )
        for association in associations
    ]


@router.post(
    "/users/{user_id}/tenants/{tenant_id}/primary",
    response_model=UserTenantAssociationResponseModel,
    summary="Set primary tenant",
    description="Set a tenant as the user's primary tenant"
)
async def set_primary_tenant(
    user_id: str = Path(..., description="User ID"),
    tenant_id: str = Path(..., description="Tenant ID"),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Set a tenant as the user's primary tenant."""
    # Set the primary tenant
    result = await user_tenant_service.set_primary_tenant(user_id, tenant_id)
    association = handle_result_error(result)
    
    # Convert to response model
    return UserTenantAssociationResponseModel(
        id=association.id.value,
        user_id=association.user_id.value,
        tenant_id=association.tenant_id.value,
        roles=association.roles,
        is_primary=association.is_primary,
        status=association.status.value,
        settings=association.settings,
        metadata=association.metadata,
        created_at=association.created_at,
        updated_at=association.updated_at
    )


@router.delete(
    "/user-tenants/{association_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user-tenant association",
    description="Delete a user-tenant association"
)
async def delete_user_tenant_association(
    association_id: str = Path(..., description="Association ID"),
    user_tenant_service: UserTenantServiceProtocol = Depends(inject_dependency(UserTenantServiceProtocol))
):
    """Delete a user-tenant association."""
    # Delete the association
    result = await user_tenant_service.delete_association(association_id)
    handle_result_error(result)
    return None


# Tenant invitation endpoints
@router.post(
    "/tenant-invitations",
    response_model=TenantInvitationResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create tenant invitation",
    description="Create a new tenant invitation"
)
async def create_tenant_invitation(
    request: TenantInvitationCreateRequestModel = Body(...),
    invited_by: str = Query(..., description="ID of the user sending the invitation"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Create a new tenant invitation."""
    # Convert to domain request
    domain_request = TenantInvitationCreateRequest(
        tenant_id=request.tenant_id,
        email=request.email,
        roles=request.roles,
        expiration_days=request.expiration_days,
        metadata=request.metadata
    )
    
    # Create the invitation
    result = await invitation_service.create_invitation(domain_request, invited_by)
    invitation = handle_result_error(result)
    
    # Convert to response model
    return TenantInvitationResponseModel(
        id=invitation.id.value,
        tenant_id=invitation.tenant_id.value,
        email=invitation.email,
        roles=invitation.roles,
        invited_by=invitation.invited_by.value,
        expires_at=invitation.expires_at,
        status=invitation.status,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at
    )


@router.get(
    "/tenant-invitations/{invitation_id}",
    response_model=TenantInvitationResponseModel,
    summary="Get tenant invitation",
    description="Get a tenant invitation by ID"
)
async def get_tenant_invitation(
    invitation_id: str = Path(..., description="Invitation ID"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Get a tenant invitation by ID."""
    # Get the invitation
    result = await invitation_service.get_invitation(invitation_id)
    invitation = handle_result_error(result)
    
    # Convert to response model
    return TenantInvitationResponseModel(
        id=invitation.id.value,
        tenant_id=invitation.tenant_id.value,
        email=invitation.email,
        roles=invitation.roles,
        invited_by=invitation.invited_by.value,
        expires_at=invitation.expires_at,
        status=invitation.status,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at
    )


@router.get(
    "/tenant-invitations/token/{token}",
    response_model=TenantInvitationResponseModel,
    summary="Get tenant invitation by token",
    description="Get a tenant invitation by token"
)
async def get_tenant_invitation_by_token(
    token: str = Path(..., description="Invitation token"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Get a tenant invitation by token."""
    # Get the invitation
    result = await invitation_service.get_invitation_by_token(token)
    invitation = handle_result_error(result)
    
    # Convert to response model
    return TenantInvitationResponseModel(
        id=invitation.id.value,
        tenant_id=invitation.tenant_id.value,
        email=invitation.email,
        roles=invitation.roles,
        invited_by=invitation.invited_by.value,
        expires_at=invitation.expires_at,
        status=invitation.status,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at
    )


@router.post(
    "/tenant-invitations/accept",
    response_model=UserTenantAssociationResponseModel,
    summary="Accept tenant invitation",
    description="Accept a tenant invitation"
)
async def accept_tenant_invitation(
    request: AcceptInvitationRequestModel = Body(...),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Accept a tenant invitation."""
    # Accept the invitation
    result = await invitation_service.accept_invitation(request.token, request.user_id)
    association = handle_result_error(result)
    
    # Convert to response model
    return UserTenantAssociationResponseModel(
        id=association.id.value,
        user_id=association.user_id.value,
        tenant_id=association.tenant_id.value,
        roles=association.roles,
        is_primary=association.is_primary,
        status=association.status.value,
        settings=association.settings,
        metadata=association.metadata,
        created_at=association.created_at,
        updated_at=association.updated_at
    )


@router.post(
    "/tenant-invitations/decline",
    response_model=TenantInvitationResponseModel,
    summary="Decline tenant invitation",
    description="Decline a tenant invitation"
)
async def decline_tenant_invitation(
    request: DeclineInvitationRequestModel = Body(...),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Decline a tenant invitation."""
    # Decline the invitation
    result = await invitation_service.decline_invitation(request.token)
    invitation = handle_result_error(result)
    
    # Convert to response model
    return TenantInvitationResponseModel(
        id=invitation.id.value,
        tenant_id=invitation.tenant_id.value,
        email=invitation.email,
        roles=invitation.roles,
        invited_by=invitation.invited_by.value,
        expires_at=invitation.expires_at,
        status=invitation.status,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at
    )


@router.get(
    "/tenants/{tenant_id}/invitations",
    response_model=List[TenantInvitationResponseModel],
    summary="Get tenant invitations",
    description="Get all invitations for a tenant"
)
async def get_tenant_invitations(
    tenant_id: str = Path(..., description="Tenant ID"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Get all invitations for a tenant."""
    # Get the invitations
    result = await invitation_service.get_tenant_invitations(tenant_id)
    invitations = handle_result_error(result)
    
    # Convert to response models
    return [
        TenantInvitationResponseModel(
            id=invitation.id.value,
            tenant_id=invitation.tenant_id.value,
            email=invitation.email,
            roles=invitation.roles,
            invited_by=invitation.invited_by.value,
            expires_at=invitation.expires_at,
            status=invitation.status,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at
        )
        for invitation in invitations
    ]


@router.get(
    "/users/email/{email}/invitations",
    response_model=List[TenantInvitationResponseModel],
    summary="Get user invitations",
    description="Get all invitations for a user email"
)
async def get_user_invitations(
    email: str = Path(..., description="User email"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Get all invitations for a user email."""
    # Get the invitations
    result = await invitation_service.get_user_invitations(email)
    invitations = handle_result_error(result)
    
    # Convert to response models
    return [
        TenantInvitationResponseModel(
            id=invitation.id.value,
            tenant_id=invitation.tenant_id.value,
            email=invitation.email,
            roles=invitation.roles,
            invited_by=invitation.invited_by.value,
            expires_at=invitation.expires_at,
            status=invitation.status,
            created_at=invitation.created_at,
            updated_at=invitation.updated_at
        )
        for invitation in invitations
    ]


@router.delete(
    "/tenant-invitations/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete tenant invitation",
    description="Delete a tenant invitation"
)
async def delete_tenant_invitation(
    invitation_id: str = Path(..., description="Invitation ID"),
    invitation_service: TenantInvitationServiceProtocol = Depends(inject_dependency(TenantInvitationServiceProtocol))
):
    """Delete a tenant invitation."""
    # Delete the invitation
    result = await invitation_service.delete_invitation(invitation_id)
    handle_result_error(result)
    return None