"""
Admin interfaces for tenant management.

This module provides the necessary components for administering tenants,
including API routes and service functions for tenant management operations.
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel, EmailStr

from uno.core.multitenancy.service import TenantService
from uno.core.multitenancy.models import Tenant, TenantStatus, UserTenantAssociation
from uno.core.multitenancy.utils import tenant_admin_required, is_tenant_admin
from uno.database.session import get_session


# Request/response models for the admin API
class TenantCreate(BaseModel):
    """Request model for creating a tenant."""
    name: str
    slug: str
    domain: Optional[str] = None
    tier: str = "standard"
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class TenantUpdate(BaseModel):
    """Request model for updating a tenant."""
    name: Optional[str] = None
    domain: Optional[str] = None
    tier: Optional[str] = None
    status: Optional[TenantStatus] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Response model for tenant data."""
    id: str
    name: str
    slug: str
    domain: Optional[str]
    tier: str
    status: str
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: Optional[str]


class UserTenantRequest(BaseModel):
    """Request model for user-tenant operations."""
    user_id: str
    roles: List[str] = ["user"]
    is_primary: bool = False


class UserTenantResponse(BaseModel):
    """Response model for user-tenant data."""
    id: str
    user_id: str
    tenant_id: str
    roles: List[str]
    is_primary: bool
    status: str
    created_at: str
    updated_at: Optional[str]


class TenantInviteRequest(BaseModel):
    """Request model for inviting a user to a tenant."""
    email: EmailStr
    roles: List[str] = ["user"]
    expires_in_days: int = 7
    message: Optional[str] = None


class TenantAdminService:
    """
    Service for tenant administration operations.
    
    This service provides methods for managing tenants, including creating,
    updating, and deleting tenants, as well as managing tenant users.
    """
    
    def __init__(self, tenant_service: TenantService):
        """
        Initialize the tenant admin service.
        
        Args:
            tenant_service: Service for tenant operations
        """
        self.tenant_service = tenant_service
    
    async def create_tenant(self, tenant_data: TenantCreate) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            tenant_data: Data for the new tenant
            
        Returns:
            The created tenant
            
        Raises:
            ValueError: If a tenant with the same slug already exists
        """
        return await self.tenant_service.create_tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            tier=tenant_data.tier,
            settings=tenant_data.settings,
            metadata=tenant_data.metadata
        )
    
    async def update_tenant(self, tenant_id: str, tenant_data: TenantUpdate) -> Optional[Tenant]:
        """
        Update an existing tenant.
        
        Args:
            tenant_id: ID of the tenant to update
            tenant_data: Data to update the tenant with
            
        Returns:
            The updated tenant, or None if not found
            
        Raises:
            ValueError: If updating to a slug that's already in use
        """
        # Convert the model to a dict and remove None values
        update_data = tenant_data.dict(exclude_unset=True)
        return await self.tenant_service.update_tenant(tenant_id, **update_data)
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        This doesn't actually delete the tenant from the database, but sets its
        status to DELETED.
        
        Args:
            tenant_id: ID of the tenant to delete
            
        Returns:
            True if the tenant was deleted, False if not found
        """
        return await self.tenant_service.delete_tenant(tenant_id)
    
    async def add_user_to_tenant(
        self, tenant_id: str, user_data: UserTenantRequest
    ) -> UserTenantAssociation:
        """
        Add a user to a tenant.
        
        Args:
            tenant_id: ID of the tenant
            user_data: Data for the user-tenant association
            
        Returns:
            The created user-tenant association
            
        Raises:
            ValueError: If the user is already associated with the tenant
        """
        return await self.tenant_service.add_user_to_tenant(
            user_id=user_data.user_id,
            tenant_id=tenant_id,
            roles=user_data.roles,
            is_primary=user_data.is_primary
        )
    
    async def update_user_tenant(
        self, tenant_id: str, user_id: str, user_data: UserTenantRequest
    ) -> Optional[UserTenantAssociation]:
        """
        Update a user's association with a tenant.
        
        Args:
            tenant_id: ID of the tenant
            user_id: ID of the user
            user_data: Data to update the association with
            
        Returns:
            The updated association, or None if not found
        """
        # Only update roles and is_primary
        update_data = {
            "roles": user_data.roles,
            "is_primary": user_data.is_primary
        }
        return await self.tenant_service.update_user_tenant(
            user_id=user_id,
            tenant_id=tenant_id,
            **update_data
        )
    
    async def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> bool:
        """
        Remove a user from a tenant.
        
        Args:
            tenant_id: ID of the tenant
            user_id: ID of the user
            
        Returns:
            True if the user was removed, False if not found
        """
        return await self.tenant_service.remove_user_from_tenant(user_id, tenant_id)
    
    async def invite_user_to_tenant(
        self, tenant_id: str, invite_data: TenantInviteRequest, invited_by: str
    ):
        """
        Invite a user to join a tenant.
        
        Args:
            tenant_id: ID of the tenant
            invite_data: Data for the invitation
            invited_by: ID of the user sending the invitation
            
        Returns:
            The created invitation
            
        Raises:
            ValueError: If the tenant doesn't exist or the inviter doesn't have access
        """
        return await self.tenant_service.invite_user_to_tenant(
            email=invite_data.email,
            tenant_id=tenant_id,
            invited_by=invited_by,
            roles=invite_data.roles,
            expires_in_days=invite_data.expires_in_days,
            metadata={"message": invite_data.message} if invite_data.message else {}
        )


def create_tenant_admin_router() -> APIRouter:
    """
    Create an API router for tenant administration.
    
    Returns:
        A FastAPI router with tenant admin endpoints
    """
    router = APIRouter(prefix="/admin/tenants", tags=["Tenant Administration"])
    
    # Dependency for getting the tenant admin service
    async def get_tenant_admin_service():
        session = await get_session()
        tenant_service = TenantService(session)
        return TenantAdminService(tenant_service)
    
    # Super admin authorization dependency
    # This would typically check a real permission system
    async def super_admin_required(request: Request):
        if not hasattr(request.user, "is_superadmin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superadmin privileges required"
            )
        
        if not request.user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Superadmin privileges required"
            )
        
        return True
    
    # --- Tenant management endpoints (superadmin only) ---
    
    @router.post(
        "/",
        response_model=TenantResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(super_admin_required)]
    )
    async def create_tenant(
        tenant_data: TenantCreate,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Create a new tenant."""
        try:
            tenant = await admin_service.create_tenant(tenant_data)
            return tenant
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.get(
        "/",
        response_model=List[TenantResponse],
        dependencies=[Depends(super_admin_required)]
    )
    async def list_tenants(
        status: Optional[TenantStatus] = None,
        tier: Optional[str] = None,
        limit: int = Query(50, ge=1, le=100),
        offset: int = Query(0, ge=0),
        tenant_service: TenantService = Depends(TenantService)
    ):
        """List all tenants."""
        filters = {}
        if status:
            filters["status"] = status
        if tier:
            filters["tier"] = tier
        
        tenants = await tenant_service.list_tenants(
            filters=filters,
            limit=limit,
            offset=offset
        )
        return tenants
    
    @router.get(
        "/{tenant_id}",
        response_model=TenantResponse,
        dependencies=[Depends(super_admin_required)]
    )
    async def get_tenant(
        tenant_id: str,
        tenant_service: TenantService = Depends(TenantService)
    ):
        """Get a specific tenant by ID."""
        tenant = await tenant_service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        return tenant
    
    @router.put(
        "/{tenant_id}",
        response_model=TenantResponse,
        dependencies=[Depends(super_admin_required)]
    )
    async def update_tenant(
        tenant_id: str,
        tenant_data: TenantUpdate,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Update a tenant."""
        try:
            tenant = await admin_service.update_tenant(tenant_id, tenant_data)
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant {tenant_id} not found"
                )
            return tenant
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.delete(
        "/{tenant_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(super_admin_required)]
    )
    async def delete_tenant(
        tenant_id: str,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Delete a tenant."""
        success = await admin_service.delete_tenant(tenant_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found"
            )
        return None
    
    # --- Tenant user management endpoints (tenant admin only) ---
    
    @router.post(
        "/{tenant_id}/users",
        response_model=UserTenantResponse,
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def add_user_to_tenant(
        tenant_id: str,
        user_data: UserTenantRequest,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Add a user to a tenant."""
        try:
            association = await admin_service.add_user_to_tenant(tenant_id, user_data)
            return association
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.get(
        "/{tenant_id}/users",
        response_model=List[UserTenantResponse],
        dependencies=[Depends(tenant_admin_required())]
    )
    async def list_tenant_users(
        tenant_id: str,
        tenant_service: TenantService = Depends(TenantService)
    ):
        """List all users in a tenant."""
        associations = await tenant_service.get_tenant_users(tenant_id)
        return associations
    
    @router.put(
        "/{tenant_id}/users/{user_id}",
        response_model=UserTenantResponse,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def update_tenant_user(
        tenant_id: str,
        user_id: str,
        user_data: UserTenantRequest,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Update a user's association with a tenant."""
        try:
            association = await admin_service.update_user_tenant(
                tenant_id, user_id, user_data
            )
            if not association:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"User {user_id} not found in tenant {tenant_id}"
                )
            return association
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    @router.delete(
        "/{tenant_id}/users/{user_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def remove_user_from_tenant(
        tenant_id: str,
        user_id: str,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Remove a user from a tenant."""
        success = await admin_service.remove_user_from_tenant(tenant_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found in tenant {tenant_id}"
            )
        return None
    
    @router.post(
        "/{tenant_id}/invitations",
        status_code=status.HTTP_201_CREATED,
        dependencies=[Depends(tenant_admin_required())]
    )
    async def invite_user_to_tenant(
        tenant_id: str,
        invite_data: TenantInviteRequest,
        request: Request,
        admin_service: TenantAdminService = Depends(get_tenant_admin_service)
    ):
        """Invite a user to join a tenant."""
        user_id = getattr(request.user, "id", None)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        try:
            invitation = await admin_service.invite_user_to_tenant(
                tenant_id, invite_data, user_id
            )
            return {"id": invitation.id, "email": invitation.email, "token": invitation.token}
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    
    return router