"""
Service implementations for multi-tenancy.

This module provides service protocols and implementations for tenant management,
user-tenant associations, and tenant invitations.
"""

from typing import Protocol, List, Optional, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import logging
import uuid

from uno.domain.service import Service
from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.catalog import ErrorCodes, UnoError
from uno.domain.repositories import Repository

from .entities import (
    Tenant, TenantId, TenantSlug, UserTenantAssociation, UserTenantAssociationId, 
    TenantInvitation, TenantInvitationId, TenantSetting, TenantSettingId,
    UserId, TenantCreateRequest, TenantUpdateRequest, UserTenantAssociationCreateRequest,
    TenantInvitationCreateRequest, TenantStatus, UserTenantStatus
)
from .domain_repositories import (
    TenantRepositoryProtocol, UserTenantAssociationRepositoryProtocol,
    TenantInvitationRepositoryProtocol, TenantSettingRepositoryProtocol
)


class TenantServiceProtocol(Service, Protocol):
    """
    Service interface for tenant management.
    
    This service defines operations for managing tenants, including creating,
    retrieving, updating, and deleting tenants.
    """
    
    async def create_tenant(self, request: TenantCreateRequest) -> Result[Tenant]:
        """
        Create a new tenant.
        
        Args:
            request: The tenant creation request
            
        Returns:
            A Result containing the created tenant if successful
        """
        ...
    
    async def get_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the tenant if found
        """
        ...
    
    async def get_tenant_by_slug(self, slug: str) -> Result[Tenant]:
        """
        Get a tenant by slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing the tenant if found
        """
        ...
    
    async def get_tenant_by_domain(self, domain: str) -> Result[Tenant]:
        """
        Get a tenant by domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing the tenant if found
        """
        ...
    
    async def update_tenant(self, tenant_id: str, request: TenantUpdateRequest) -> Result[Tenant]:
        """
        Update a tenant.
        
        Args:
            tenant_id: The tenant ID
            request: The tenant update request
            
        Returns:
            A Result containing the updated tenant if successful
        """
        ...
    
    async def delete_tenant(self, tenant_id: str) -> Result[bool]:
        """
        Delete a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing True if the tenant was deleted
        """
        ...
    
    async def list_tenants(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        page: int = 1, 
        page_size: int = 50,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None
    ) -> Result[List[Tenant]]:
        """
        List tenants with optional filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_field: Field to sort by
            sort_direction: Sort direction ("asc" or "desc")
            
        Returns:
            A Result containing a list of tenants
        """
        ...
    
    async def count_tenants(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count tenants matching the given filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            A Result containing the count of matching tenants
        """
        ...
    
    async def suspend_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Suspend a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated tenant if successful
        """
        ...
    
    async def activate_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Activate a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated tenant if successful
        """
        ...
    
    async def update_tenant_settings(self, tenant_id: str, settings: Dict[str, Any]) -> Result[Tenant]:
        """
        Update tenant settings.
        
        Args:
            tenant_id: The tenant ID
            settings: The settings to update
            
        Returns:
            A Result containing the updated tenant if successful
        """
        ...


class UserTenantServiceProtocol(Service, Protocol):
    """
    Service interface for user-tenant association management.
    
    This service defines operations for managing associations between users and tenants,
    including creating, retrieving, updating, and deleting associations.
    """
    
    async def create_association(self, request: UserTenantAssociationCreateRequest) -> Result[UserTenantAssociation]:
        """
        Create a new user-tenant association.
        
        Args:
            request: The association creation request
            
        Returns:
            A Result containing the created association if successful
        """
        ...
    
    async def get_association(self, association_id: str) -> Result[UserTenantAssociation]:
        """
        Get a user-tenant association by ID.
        
        Args:
            association_id: The association ID
            
        Returns:
            A Result containing the association if found
        """
        ...
    
    async def get_user_tenant_association(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Get a user-tenant association by user ID and tenant ID.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the association if found
        """
        ...
    
    async def update_association_roles(self, association_id: str, roles: List[str]) -> Result[UserTenantAssociation]:
        """
        Update the roles for a user-tenant association.
        
        Args:
            association_id: The association ID
            roles: The new roles
            
        Returns:
            A Result containing the updated association if successful
        """
        ...
    
    async def update_association_status(self, association_id: str, status: UserTenantStatus) -> Result[UserTenantAssociation]:
        """
        Update the status of a user-tenant association.
        
        Args:
            association_id: The association ID
            status: The new status
            
        Returns:
            A Result containing the updated association if successful
        """
        ...
    
    async def delete_association(self, association_id: str) -> Result[bool]:
        """
        Delete a user-tenant association.
        
        Args:
            association_id: The association ID
            
        Returns:
            A Result containing True if the association was deleted
        """
        ...
    
    async def get_user_tenants(self, user_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all tenants associated with a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        ...
    
    async def get_tenant_users(self, tenant_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all users associated with a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        ...
    
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Set a tenant as the user's primary tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated association if successful
        """
        ...
    
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get the user's primary tenant association.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing the primary association if found, or None
        """
        ...
    
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> Result[bool]:
        """
        Check if a user has access to a tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing True if the user has access, False otherwise
        """
        ...


class TenantInvitationServiceProtocol(Service, Protocol):
    """
    Service interface for tenant invitation management.
    
    This service defines operations for managing invitations to join tenants,
    including creating, retrieving, and processing invitations.
    """
    
    async def create_invitation(self, request: TenantInvitationCreateRequest, invited_by: str) -> Result[TenantInvitation]:
        """
        Create a new tenant invitation.
        
        Args:
            request: The invitation creation request
            invited_by: The ID of the user who is sending the invitation
            
        Returns:
            A Result containing the created invitation if successful
        """
        ...
    
    async def get_invitation(self, invitation_id: str) -> Result[TenantInvitation]:
        """
        Get a tenant invitation by ID.
        
        Args:
            invitation_id: The invitation ID
            
        Returns:
            A Result containing the invitation if found
        """
        ...
    
    async def get_invitation_by_token(self, token: str) -> Result[TenantInvitation]:
        """
        Get a tenant invitation by token.
        
        Args:
            token: The invitation token
            
        Returns:
            A Result containing the invitation if found
        """
        ...
    
    async def accept_invitation(self, token: str, user_id: str) -> Result[UserTenantAssociation]:
        """
        Accept a tenant invitation.
        
        Args:
            token: The invitation token
            user_id: The ID of the user accepting the invitation
            
        Returns:
            A Result containing the created user-tenant association if successful
        """
        ...
    
    async def decline_invitation(self, token: str) -> Result[TenantInvitation]:
        """
        Decline a tenant invitation.
        
        Args:
            token: The invitation token
            
        Returns:
            A Result containing the updated invitation if successful
        """
        ...
    
    async def get_tenant_invitations(self, tenant_id: str) -> Result[List[TenantInvitation]]:
        """
        Get all invitations for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of invitations
        """
        ...
    
    async def get_user_invitations(self, email: str) -> Result[List[TenantInvitation]]:
        """
        Get all invitations for a user email.
        
        Args:
            email: The user's email
            
        Returns:
            A Result containing a list of invitations
        """
        ...
    
    async def delete_invitation(self, invitation_id: str) -> Result[bool]:
        """
        Delete a tenant invitation.
        
        Args:
            invitation_id: The invitation ID
            
        Returns:
            A Result containing True if the invitation was deleted
        """
        ...


@dataclass
class TenantService(TenantServiceProtocol):
    """
    Implementation of the tenant management service.
    
    This service manages tenants, including creating, retrieving, updating,
    and deleting tenants.
    """
    
    tenant_repository: TenantRepositoryProtocol
    logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        """Initialize the service."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
    
    async def create_tenant(self, request: TenantCreateRequest) -> Result[Tenant]:
        """
        Create a new tenant.
        
        Args:
            request: The tenant creation request
            
        Returns:
            A Result containing the created tenant if successful
        """
        # Check if tenant with the same slug already exists
        slug_exists = await self.tenant_repository.exists_by_slug(request.slug)
        if slug_exists.is_failure():
            return slug_exists
        
        if slug_exists.value:
            return Failure(
                code=ErrorCodes.DUPLICATE_RESOURCE,
                message=f"Tenant with slug '{request.slug}' already exists",
                context={"slug": request.slug}
            )
        
        # Check if tenant with the same domain already exists (if provided)
        if request.domain:
            domain_exists = await self.tenant_repository.exists_by_domain(request.domain)
            if domain_exists.is_failure():
                return domain_exists
            
            if domain_exists.value:
                return Failure(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"Tenant with domain '{request.domain}' already exists",
                    context={"domain": request.domain}
                )
        
        # Create the tenant entity
        tenant = Tenant.create(
            name=request.name,
            slug=request.slug,
            tier=request.tier,
            domain=request.domain
        )
        
        # Apply settings and metadata if provided
        if request.settings:
            tenant.settings = request.settings
        
        if request.metadata:
            tenant.metadata = request.metadata
        
        # Save the tenant
        result = await self.tenant_repository.add(tenant)
        return result
    
    async def get_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Get a tenant by ID.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the tenant if found
        """
        result = await self.tenant_repository.get_by_id(tenant_id)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant with ID '{tenant_id}' not found",
                context={"tenant_id": tenant_id}
            )
        
        return result
    
    async def get_tenant_by_slug(self, slug: str) -> Result[Tenant]:
        """
        Get a tenant by slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing the tenant if found
        """
        result = await self.tenant_repository.get_by_slug(slug)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant with slug '{slug}' not found",
                context={"slug": slug}
            )
        
        return result
    
    async def get_tenant_by_domain(self, domain: str) -> Result[Tenant]:
        """
        Get a tenant by domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing the tenant if found
        """
        result = await self.tenant_repository.get_by_domain(domain)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant with domain '{domain}' not found",
                context={"domain": domain}
            )
        
        return result
    
    async def update_tenant(self, tenant_id: str, request: TenantUpdateRequest) -> Result[Tenant]:
        """
        Update a tenant.
        
        Args:
            tenant_id: The tenant ID
            request: The tenant update request
            
        Returns:
            A Result containing the updated tenant if successful
        """
        # Get the tenant
        get_result = await self.get_tenant(tenant_id)
        if get_result.is_failure():
            return get_result
        
        tenant = get_result.value
        
        # Check if slug is changing and if the new slug is available
        if request.name is not None:
            tenant.name = request.name
        
        # Check if domain is changing and if the new domain is available
        if request.domain is not None and request.domain != tenant.domain:
            if request.domain != "":  # Allow clearing the domain
                domain_exists = await self.tenant_repository.exists_by_domain(request.domain)
                if domain_exists.is_failure():
                    return domain_exists
                
                if domain_exists.value:
                    return Failure(
                        code=ErrorCodes.DUPLICATE_RESOURCE,
                        message=f"Tenant with domain '{request.domain}' already exists",
                        context={"domain": request.domain}
                    )
            
            tenant.domain = request.domain
        
        # Update tier if provided
        if request.tier is not None:
            tenant.tier = request.tier
        
        # Update settings if provided
        if request.settings is not None:
            tenant.update_settings(request.settings)
        
        # Update metadata if provided
        if request.metadata is not None:
            tenant.update_metadata(request.metadata)
        
        # Update the tenant
        tenant.updated_at = datetime.now(timezone.UTC)
        result = await self.tenant_repository.update(tenant)
        return result
    
    async def delete_tenant(self, tenant_id: str) -> Result[bool]:
        """
        Delete a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing True if the tenant was deleted
        """
        # Check if the tenant exists
        get_result = await self.get_tenant(tenant_id)
        if get_result.is_failure():
            if get_result.error.code == ErrorCodes.RESOURCE_NOT_FOUND:
                # If tenant doesn't exist, consider the deletion successful
                return Success(False)
            return get_result
        
        # Delete the tenant
        result = await self.tenant_repository.delete(tenant_id)
        return result
    
    async def list_tenants(
        self, 
        filters: Optional[Dict[str, Any]] = None, 
        page: int = 1, 
        page_size: int = 50,
        sort_field: Optional[str] = None,
        sort_direction: Optional[str] = None
    ) -> Result[List[Tenant]]:
        """
        List tenants with optional filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            page: Page number (1-indexed)
            page_size: Number of items per page
            sort_field: Field to sort by
            sort_direction: Sort direction ("asc" or "desc")
            
        Returns:
            A Result containing a list of tenants
        """
        # Configure pagination
        options = {
            "pagination": {
                "limit": page_size,
                "offset": (page - 1) * page_size
            }
        }
        
        # Configure sorting
        if sort_field:
            options["sort"] = {
                "field": sort_field,
                "direction": sort_direction or "asc"
            }
        
        # Get the tenants
        result = await self.tenant_repository.list(filters, options)
        return result
    
    async def count_tenants(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count tenants matching the given filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            A Result containing the count of matching tenants
        """
        result = await self.tenant_repository.count(filters)
        return result
    
    async def suspend_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Suspend a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated tenant if successful
        """
        # Get the tenant
        get_result = await self.get_tenant(tenant_id)
        if get_result.is_failure():
            return get_result
        
        tenant = get_result.value
        
        # Update the tenant status
        tenant.suspend()
        
        # Save the tenant
        result = await self.tenant_repository.update(tenant)
        return result
    
    async def activate_tenant(self, tenant_id: str) -> Result[Tenant]:
        """
        Activate a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated tenant if successful
        """
        # Get the tenant
        get_result = await self.get_tenant(tenant_id)
        if get_result.is_failure():
            return get_result
        
        tenant = get_result.value
        
        # Update the tenant status
        tenant.activate()
        
        # Save the tenant
        result = await self.tenant_repository.update(tenant)
        return result
    
    async def update_tenant_settings(self, tenant_id: str, settings: Dict[str, Any]) -> Result[Tenant]:
        """
        Update tenant settings.
        
        Args:
            tenant_id: The tenant ID
            settings: The settings to update
            
        Returns:
            A Result containing the updated tenant if successful
        """
        # Get the tenant
        get_result = await self.get_tenant(tenant_id)
        if get_result.is_failure():
            return get_result
        
        tenant = get_result.value
        
        # Update the tenant settings
        tenant.update_settings(settings)
        
        # Save the tenant
        result = await self.tenant_repository.update(tenant)
        return result


@dataclass
class UserTenantService(UserTenantServiceProtocol):
    """
    Implementation of the user-tenant association management service.
    
    This service manages associations between users and tenants, including
    creating, retrieving, updating, and deleting associations.
    """
    
    association_repository: UserTenantAssociationRepositoryProtocol
    tenant_repository: TenantRepositoryProtocol
    logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        """Initialize the service."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
    
    async def create_association(self, request: UserTenantAssociationCreateRequest) -> Result[UserTenantAssociation]:
        """
        Create a new user-tenant association.
        
        Args:
            request: The association creation request
            
        Returns:
            A Result containing the created association if successful
        """
        # Check if the tenant exists
        tenant_result = await self.tenant_repository.get_by_id(request.tenant_id)
        if tenant_result.is_failure():
            return tenant_result
        
        if tenant_result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant with ID '{request.tenant_id}' not found",
                context={"tenant_id": request.tenant_id}
            )
        
        # Check if the association already exists
        existing_result = await self.association_repository.get_user_tenant(request.user_id, request.tenant_id)
        if existing_result.is_failure():
            return existing_result
        
        if existing_result.value is not None:
            return Failure(
                code=ErrorCodes.DUPLICATE_RESOURCE,
                message=f"User already has an association with this tenant",
                context={"user_id": request.user_id, "tenant_id": request.tenant_id}
            )
        
        # Create the association
        association = UserTenantAssociation.create(
            user_id=request.user_id,
            tenant_id=request.tenant_id,
            roles=request.roles or [],
            is_primary=request.is_primary or False
        )
        
        # Apply settings and metadata if provided
        if request.settings:
            association.settings = request.settings
        
        if request.metadata:
            association.metadata = request.metadata
        
        # Save the association
        result = await self.association_repository.add(association)
        return result
    
    async def get_association(self, association_id: str) -> Result[UserTenantAssociation]:
        """
        Get a user-tenant association by ID.
        
        Args:
            association_id: The association ID
            
        Returns:
            A Result containing the association if found
        """
        result = await self.association_repository.get_by_id(association_id)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"User-tenant association with ID '{association_id}' not found",
                context={"association_id": association_id}
            )
        
        return result
    
    async def get_user_tenant_association(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Get a user-tenant association by user ID and tenant ID.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the association if found
        """
        result = await self.association_repository.get_user_tenant(user_id, tenant_id)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"User-tenant association not found",
                context={"user_id": user_id, "tenant_id": tenant_id}
            )
        
        return result
    
    async def update_association_roles(self, association_id: str, roles: List[str]) -> Result[UserTenantAssociation]:
        """
        Update the roles for a user-tenant association.
        
        Args:
            association_id: The association ID
            roles: The new roles
            
        Returns:
            A Result containing the updated association if successful
        """
        # Get the association
        get_result = await self.get_association(association_id)
        if get_result.is_failure():
            return get_result
        
        association = get_result.value
        
        # Update the roles
        association.roles = roles
        association.updated_at = datetime.now(timezone.UTC)
        
        # Save the association
        result = await self.association_repository.update(association)
        return result
    
    async def update_association_status(self, association_id: str, status: UserTenantStatus) -> Result[UserTenantAssociation]:
        """
        Update the status of a user-tenant association.
        
        Args:
            association_id: The association ID
            status: The new status
            
        Returns:
            A Result containing the updated association if successful
        """
        # Get the association
        get_result = await self.get_association(association_id)
        if get_result.is_failure():
            return get_result
        
        association = get_result.value
        
        # Update the status
        association.status = status
        association.updated_at = datetime.now(timezone.UTC)
        
        # Save the association
        result = await self.association_repository.update(association)
        return result
    
    async def delete_association(self, association_id: str) -> Result[bool]:
        """
        Delete a user-tenant association.
        
        Args:
            association_id: The association ID
            
        Returns:
            A Result containing True if the association was deleted
        """
        # Delete the association
        result = await self.association_repository.delete(association_id)
        return result
    
    async def get_user_tenants(self, user_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all tenants associated with a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        # Get the associations
        result = await self.association_repository.get_user_tenants(user_id)
        return result
    
    async def get_tenant_users(self, tenant_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all users associated with a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        # Get the associations
        result = await self.association_repository.get_tenant_users(tenant_id)
        return result
    
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Set a tenant as the user's primary tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated association if successful
        """
        # Check if the user has an association with the tenant
        association_result = await self.association_repository.get_user_tenant(user_id, tenant_id)
        if association_result.is_failure():
            return association_result
        
        if association_result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"User does not have an association with this tenant",
                context={"user_id": user_id, "tenant_id": tenant_id}
            )
        
        # Set the tenant as primary
        result = await self.association_repository.set_primary_tenant(user_id, tenant_id)
        return result
    
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get the user's primary tenant association.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing the primary association if found, or None
        """
        # Get the primary association
        result = await self.association_repository.get_primary_tenant(user_id)
        return result
    
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> Result[bool]:
        """
        Check if a user has access to a tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing True if the user has access, False otherwise
        """
        # Check if the user has access
        result = await self.association_repository.user_has_access_to_tenant(user_id, tenant_id)
        return result


@dataclass
class TenantInvitationService(TenantInvitationServiceProtocol):
    """
    Implementation of the tenant invitation management service.
    
    This service manages invitations to join tenants, including creating,
    retrieving, and processing invitations.
    """
    
    invitation_repository: TenantInvitationRepositoryProtocol
    tenant_repository: TenantRepositoryProtocol
    user_tenant_service: UserTenantServiceProtocol
    logger: Optional[logging.Logger] = None
    
    def __post_init__(self):
        """Initialize the service."""
        if self.logger is None:
            self.logger = logging.getLogger(__name__)
    
    async def create_invitation(self, request: TenantInvitationCreateRequest, invited_by: str) -> Result[TenantInvitation]:
        """
        Create a new tenant invitation.
        
        Args:
            request: The invitation creation request
            invited_by: The ID of the user who is sending the invitation
            
        Returns:
            A Result containing the created invitation if successful
        """
        # Check if the tenant exists
        tenant_result = await self.tenant_repository.get_by_id(request.tenant_id)
        if tenant_result.is_failure():
            return tenant_result
        
        if tenant_result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant with ID '{request.tenant_id}' not found",
                context={"tenant_id": request.tenant_id}
            )
        
        # Calculate expiration date
        expiration_days = request.expiration_days or 7
        expires_at = datetime.now(timezone.UTC) + timedelta(days=expiration_days)
        
        # Create the invitation
        invitation = TenantInvitation.create(
            tenant_id=request.tenant_id,
            email=request.email,
            invited_by=invited_by,
            roles=request.roles or [],
            expires_at=expires_at
        )
        
        # Apply metadata if provided
        if request.metadata:
            invitation.metadata = request.metadata
        
        # Save the invitation
        result = await self.invitation_repository.add(invitation)
        return result
    
    async def get_invitation(self, invitation_id: str) -> Result[TenantInvitation]:
        """
        Get a tenant invitation by ID.
        
        Args:
            invitation_id: The invitation ID
            
        Returns:
            A Result containing the invitation if found
        """
        result = await self.invitation_repository.get_by_id(invitation_id)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant invitation with ID '{invitation_id}' not found",
                context={"invitation_id": invitation_id}
            )
        
        return result
    
    async def get_invitation_by_token(self, token: str) -> Result[TenantInvitation]:
        """
        Get a tenant invitation by token.
        
        Args:
            token: The invitation token
            
        Returns:
            A Result containing the invitation if found
        """
        result = await self.invitation_repository.get_by_token(token)
        if result.is_failure():
            return result
        
        if result.value is None:
            return Failure(
                code=ErrorCodes.RESOURCE_NOT_FOUND,
                message=f"Tenant invitation with token '{token}' not found",
                context={"token": token}
            )
        
        return result
    
    async def accept_invitation(self, token: str, user_id: str) -> Result[UserTenantAssociation]:
        """
        Accept a tenant invitation.
        
        Args:
            token: The invitation token
            user_id: The ID of the user accepting the invitation
            
        Returns:
            A Result containing the created user-tenant association if successful
        """
        # Get the invitation
        invitation_result = await self.get_invitation_by_token(token)
        if invitation_result.is_failure():
            return invitation_result
        
        invitation = invitation_result.value
        
        # Check if the invitation is expired
        if invitation.is_expired():
            return Failure(
                code=ErrorCodes.INVALID_STATE,
                message=f"Invitation has expired",
                context={"invitation_id": invitation.id.value}
            )
        
        # Check if the invitation is already accepted or declined
        if invitation.status != "pending":
            return Failure(
                code=ErrorCodes.INVALID_STATE,
                message=f"Invitation has already been {invitation.status}",
                context={"invitation_id": invitation.id.value}
            )
        
        # Create the user-tenant association
        association_request = UserTenantAssociationCreateRequest(
            user_id=user_id,
            tenant_id=invitation.tenant_id.value,
            roles=invitation.roles,
            is_primary=False
        )
        
        association_result = await self.user_tenant_service.create_association(association_request)
        if association_result.is_failure():
            return association_result
        
        # Mark the invitation as accepted
        invitation.accept()
        await self.invitation_repository.update(invitation)
        
        return association_result
    
    async def decline_invitation(self, token: str) -> Result[TenantInvitation]:
        """
        Decline a tenant invitation.
        
        Args:
            token: The invitation token
            
        Returns:
            A Result containing the updated invitation if successful
        """
        # Get the invitation
        invitation_result = await self.get_invitation_by_token(token)
        if invitation_result.is_failure():
            return invitation_result
        
        invitation = invitation_result.value
        
        # Check if the invitation is already accepted or declined
        if invitation.status != "pending":
            return Failure(
                code=ErrorCodes.INVALID_STATE,
                message=f"Invitation has already been {invitation.status}",
                context={"invitation_id": invitation.id.value}
            )
        
        # Mark the invitation as declined
        invitation.decline()
        result = await self.invitation_repository.update(invitation)
        return result
    
    async def get_tenant_invitations(self, tenant_id: str) -> Result[List[TenantInvitation]]:
        """
        Get all invitations for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of invitations
        """
        # Get the invitations
        result = await self.invitation_repository.get_tenant_invitations(tenant_id)
        return result
    
    async def get_user_invitations(self, email: str) -> Result[List[TenantInvitation]]:
        """
        Get all invitations for a user email.
        
        Args:
            email: The user's email
            
        Returns:
            A Result containing a list of invitations
        """
        # Get the invitations
        result = await self.invitation_repository.get_user_invitations(email)
        return result
    
    async def delete_invitation(self, invitation_id: str) -> Result[bool]:
        """
        Delete a tenant invitation.
        
        Args:
            invitation_id: The invitation ID
            
        Returns:
            A Result containing True if the invitation was deleted
        """
        # Delete the invitation
        result = await self.invitation_repository.delete(invitation_id)
        return result