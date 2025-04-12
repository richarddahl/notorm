"""
Tenant management services.

This module provides services for managing tenants, including
creation, updates, and user associations.
"""

import asyncio
from typing import List, Dict, Optional, Any, Type, Union
from datetime import datetime, timedelta
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from uno.core.multitenancy.models import (
    Tenant, TenantStatus, UserTenantAssociation, UserTenantStatus, TenantInvitation
)
from uno.core.multitenancy.repository import (
    TenantRepository, UserTenantAssociationRepository
)
from uno.core.multitenancy.context import tenant_context, get_current_tenant_context


class TenantService:
    """
    Service for tenant management operations.
    
    This class provides high-level operations for managing tenants,
    including creation, updates, and user associations.
    """
    
    def __init__(
        self,
        session: AsyncSession,
        tenant_repo: Optional[TenantRepository] = None,
        user_tenant_repo: Optional[UserTenantAssociationRepository] = None,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the tenant service.
        
        Args:
            session: SQLAlchemy async session
            tenant_repo: Repository for tenant operations
            user_tenant_repo: Repository for user-tenant associations
            logger: Optional logger instance
        """
        self.session = session
        self.tenant_repo = tenant_repo or TenantRepository(session, Tenant)
        self.user_tenant_repo = user_tenant_repo or UserTenantAssociationRepository(
            session, UserTenantAssociation
        )
        self.logger = logger or logging.getLogger(__name__)
    
    async def create_tenant(
        self, name: str, slug: str, **kwargs
    ) -> Tenant:
        """
        Create a new tenant.
        
        Args:
            name: Name of the tenant
            slug: URL-friendly identifier for the tenant
            **kwargs: Additional tenant properties
            
        Returns:
            The created tenant
        """
        # Check if a tenant with this slug already exists
        existing = await self.get_tenant_by_slug(slug)
        if existing:
            raise ValueError(f"Tenant with slug '{slug}' already exists")
        
        # Create the tenant
        tenant_data = {
            "name": name,
            "slug": slug,
            "status": kwargs.pop("status", TenantStatus.ACTIVE),
            **kwargs
        }
        
        tenant = await self.tenant_repo.create(tenant_data)
        self.logger.info(f"Created tenant: {tenant.id} - {tenant.name}")
        return tenant
    
    async def update_tenant(
        self, tenant_id: str, **kwargs
    ) -> Optional[Tenant]:
        """
        Update an existing tenant.
        
        Args:
            tenant_id: ID of the tenant to update
            **kwargs: Properties to update
            
        Returns:
            The updated tenant, or None if not found
        """
        # Prevent changing slug to one that already exists
        if "slug" in kwargs:
            existing = await self.get_tenant_by_slug(kwargs["slug"])
            if existing and existing.id != tenant_id:
                raise ValueError(f"Tenant with slug '{kwargs['slug']}' already exists")
        
        tenant = await self.tenant_repo.update(tenant_id, kwargs)
        if tenant:
            self.logger.info(f"Updated tenant: {tenant.id} - {tenant.name}")
        return tenant
    
    async def delete_tenant(self, tenant_id: str) -> bool:
        """
        Delete a tenant.
        
        This method doesn't actually delete the tenant, but sets its status to DELETED.
        
        Args:
            tenant_id: ID of the tenant to delete
            
        Returns:
            True if the tenant was deleted, False if not found
        """
        tenant = await self.tenant_repo.get(tenant_id)
        if not tenant:
            return False
        
        # Set the tenant's status to DELETED
        await self.tenant_repo.update(tenant_id, {"status": TenantStatus.DELETED})
        self.logger.info(f"Deleted tenant: {tenant_id} - {tenant.name}")
        return True
    
    async def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: ID of the tenant
            
        Returns:
            The tenant if found, None otherwise
        """
        return await self.tenant_repo.get(tenant_id)
    
    async def get_tenant_by_slug(self, slug: str) -> Optional[Tenant]:
        """
        Get a tenant by slug.
        
        Args:
            slug: Slug of the tenant
            
        Returns:
            The tenant if found, None otherwise
        """
        tenants = await self.tenant_repo.list(filters={"slug": slug}, limit=1)
        return tenants[0] if tenants else None
    
    async def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """
        Get a tenant by domain.
        
        Args:
            domain: Domain of the tenant
            
        Returns:
            The tenant if found, None otherwise
        """
        tenants = await self.tenant_repo.list(filters={"domain": domain}, limit=1)
        return tenants[0] if tenants else None
    
    async def list_tenants(
        self,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[Tenant]:
        """
        List tenants with optional filtering, ordering, and pagination.
        
        Args:
            filters: Dictionary of filters to apply
            order_by: List of fields to order by
            limit: Maximum number of results to return
            offset: Number of results to skip
            
        Returns:
            List of tenants matching the criteria
        """
        return await self.tenant_repo.list(
            filters=filters, order_by=order_by, limit=limit, offset=offset
        )
    
    async def count_tenants(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count tenants matching the given filters.
        
        Args:
            filters: Dictionary of filters to apply
            
        Returns:
            The number of matching tenants
        """
        return await self.tenant_repo.count(filters=filters)
    
    async def add_user_to_tenant(
        self,
        user_id: str,
        tenant_id: str,
        roles: List[str] = None,
        is_primary: bool = False,
        status: UserTenantStatus = UserTenantStatus.ACTIVE,
        **kwargs
    ) -> UserTenantAssociation:
        """
        Add a user to a tenant.
        
        Args:
            user_id: ID of the user
            tenant_id: ID of the tenant
            roles: Roles of the user in the tenant
            is_primary: Whether this is the user's primary tenant
            status: Status of the user in the tenant
            **kwargs: Additional properties
            
        Returns:
            The created user-tenant association
        """
        # Check if the user is already associated with the tenant
        existing = await self.user_tenant_repo.get_user_tenant(user_id, tenant_id)
        if existing:
            raise ValueError(f"User {user_id} is already associated with tenant {tenant_id}")
        
        # Add the user to the tenant
        association_data = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "roles": roles or [],
            "is_primary": is_primary,
            "status": status,
            **kwargs
        }
        
        association = await self.user_tenant_repo.create(association_data)
        self.logger.info(
            f"Added user {user_id} to tenant {tenant_id} with roles {roles}"
        )
        return association
    
    async def update_user_tenant(
        self,
        user_id: str,
        tenant_id: str,
        **kwargs
    ) -> Optional[UserTenantAssociation]:
        """
        Update a user's association with a tenant.
        
        Args:
            user_id: ID of the user
            tenant_id: ID of the tenant
            **kwargs: Properties to update
            
        Returns:
            The updated association, or None if not found
        """
        # Get the association
        association = await self.user_tenant_repo.get_user_tenant(user_id, tenant_id)
        if not association:
            return None
        
        # Update the association
        updated = await self.user_tenant_repo.update(association.id, kwargs)
        if updated:
            self.logger.info(
                f"Updated user {user_id}'s association with tenant {tenant_id}"
            )
        return updated
    
    async def remove_user_from_tenant(
        self, user_id: str, tenant_id: str
    ) -> bool:
        """
        Remove a user from a tenant.
        
        Args:
            user_id: ID of the user
            tenant_id: ID of the tenant
            
        Returns:
            True if the user was removed, False if not found
        """
        # Get the association
        association = await self.user_tenant_repo.get_user_tenant(user_id, tenant_id)
        if not association:
            return False
        
        # Delete the association
        deleted = await self.user_tenant_repo.delete(association.id)
        if deleted:
            self.logger.info(f"Removed user {user_id} from tenant {tenant_id}")
        return deleted
    
    async def get_user_tenants(self, user_id: str) -> List[UserTenantAssociation]:
        """
        Get all tenants associated with a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of tenant associations for the user
        """
        return await self.user_tenant_repo.get_user_tenants(user_id)
    
    async def get_tenant_users(self, tenant_id: str) -> List[UserTenantAssociation]:
        """
        Get all users associated with a tenant.
        
        Args:
            tenant_id: ID of the tenant
            
        Returns:
            List of user associations for the tenant
        """
        return await self.user_tenant_repo.get_tenant_users(tenant_id)
    
    async def get_user_tenant(
        self, user_id: str, tenant_id: str
    ) -> Optional[UserTenantAssociation]:
        """
        Get a specific user-tenant association.
        
        Args:
            user_id: ID of the user
            tenant_id: ID of the tenant
            
        Returns:
            The association if it exists, None otherwise
        """
        return await self.user_tenant_repo.get_user_tenant(user_id, tenant_id)
    
    async def user_has_access_to_tenant(
        self, user_id: str, tenant_id: str
    ) -> bool:
        """
        Check if a user has access to a tenant.
        
        Args:
            user_id: ID of the user
            tenant_id: ID of the tenant
            
        Returns:
            True if the user has access to the tenant, False otherwise
        """
        return await self.user_tenant_repo.user_has_access_to_tenant(user_id, tenant_id)
    
    async def invite_user_to_tenant(
        self,
        email: str,
        tenant_id: str,
        invited_by: str,
        roles: List[str] = None,
        expires_in_days: int = 7,
        **kwargs
    ) -> TenantInvitation:
        """
        Invite a user to join a tenant.
        
        Args:
            email: Email of the user to invite
            tenant_id: ID of the tenant
            invited_by: ID of the user sending the invitation
            roles: Roles to assign to the user
            expires_in_days: Number of days until the invitation expires
            **kwargs: Additional invitation properties
            
        Returns:
            The created invitation
        """
        # Check if the tenant exists
        tenant = await self.get_tenant(tenant_id)
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        
        # Check if the inviter has access to the tenant
        if not await self.user_has_access_to_tenant(invited_by, tenant_id):
            raise ValueError(f"User {invited_by} does not have access to tenant {tenant_id}")
        
        # Create the invitation
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
        # For a complete implementation, you would create a TenantInvitationRepository
        # and use it here. For simplicity, we'll leave this as a stub.
        self.logger.info(
            f"Invited user {email} to tenant {tenant_id} with roles {roles}"
        )
        
        # In a real implementation, you would also send an email to the invited user
        # with a link to accept the invitation.
        invitation = TenantInvitation(
            tenant_id=tenant_id,
            email=email,
            roles=roles or [],
            invited_by=invited_by,
            expires_at=expires_at,
            **kwargs
        )
        return invitation
    
    async def accept_invitation(
        self, token: str, user_id: str
    ) -> Optional[UserTenantAssociation]:
        """
        Accept a tenant invitation.
        
        Args:
            token: Token of the invitation
            user_id: ID of the user accepting the invitation
            
        Returns:
            The created user-tenant association, or None if the invitation is invalid
        """
        # For a complete implementation, you would create a TenantInvitationRepository
        # and use it here. For simplicity, we'll leave this as a stub.
        self.logger.info(f"User {user_id} accepted invitation with token {token}")
        
        # In a real implementation, you would:
        # 1. Retrieve the invitation by token
        # 2. Verify that it hasn't expired
        # 3. Create a user-tenant association
        # 4. Update the invitation status
        
        return None