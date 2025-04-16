"""
Repository interfaces and implementations for multi-tenancy.

This module provides repository protocols and implementations for managing
tenant entities, user-tenant associations, and tenant invitations.
"""

from typing import Protocol, List, Optional, Dict, Any, TypeVar, Generic, Union
from dataclasses import dataclass
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert, update, delete, func, text

from uno.core.errors.result import Result, Success, Failure
from uno.core.errors.catalog import ErrorCodes
from uno.domain.repositories import Repository
from uno.core.multitenancy.context import get_current_tenant_context

from .entities import (
    Tenant, TenantId, UserTenantAssociation, UserTenantAssociationId, 
    TenantInvitation, TenantInvitationId, TenantSetting, TenantSettingId,
    UserId, TenantSlug
)


# Type variables
T = TypeVar('T')
EntityT = TypeVar('EntityT')


class TenantRepositoryProtocol(Repository[Tenant, TenantId], Protocol):
    """
    Repository interface for tenant entities.
    
    This repository manages the tenant entities in the system.
    """
    
    async def get_by_slug(self, slug: str) -> Result[Optional[Tenant]]:
        """
        Get a tenant by its slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing the tenant if found, or None
        """
        ...
    
    async def get_by_domain(self, domain: str) -> Result[Optional[Tenant]]:
        """
        Get a tenant by its domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing the tenant if found, or None
        """
        ...
    
    async def exists_by_slug(self, slug: str) -> Result[bool]:
        """
        Check if a tenant exists with the given slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing True if the tenant exists, False otherwise
        """
        ...
    
    async def exists_by_domain(self, domain: str) -> Result[bool]:
        """
        Check if a tenant exists with the given domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing True if the tenant exists, False otherwise
        """
        ...


class UserTenantAssociationRepositoryProtocol(Repository[UserTenantAssociation, UserTenantAssociationId], Protocol):
    """
    Repository interface for user-tenant association entities.
    
    This repository manages associations between users and tenants.
    """
    
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
    
    async def get_user_tenant(self, user_id: str, tenant_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get a specific user-tenant association.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the association if found, or None
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
    
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get the user's primary tenant association.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing the primary association if found, or None
        """
        ...
    
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Set a tenant as the user's primary tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated association
        """
        ...


class TenantInvitationRepositoryProtocol(Repository[TenantInvitation, TenantInvitationId], Protocol):
    """
    Repository interface for tenant invitation entities.
    
    This repository manages invitations to join tenants.
    """
    
    async def get_by_email_and_tenant(self, email: str, tenant_id: str) -> Result[Optional[TenantInvitation]]:
        """
        Get an invitation by email and tenant ID.
        
        Args:
            email: The invitee's email
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the invitation if found, or None
        """
        ...
    
    async def get_by_token(self, token: str) -> Result[Optional[TenantInvitation]]:
        """
        Get an invitation by its token.
        
        Args:
            token: The invitation token
            
        Returns:
            A Result containing the invitation if found, or None
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


class TenantSettingRepositoryProtocol(Repository[TenantSetting, TenantSettingId], Protocol):
    """
    Repository interface for tenant setting entities.
    
    This repository manages settings for tenants.
    """
    
    async def get_by_key(self, tenant_id: str, key: str) -> Result[Optional[TenantSetting]]:
        """
        Get a setting by its key for a specific tenant.
        
        Args:
            tenant_id: The tenant ID
            key: The setting key
            
        Returns:
            A Result containing the setting if found, or None
        """
        ...
    
    async def get_tenant_settings(self, tenant_id: str) -> Result[List[TenantSetting]]:
        """
        Get all settings for a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of settings
        """
        ...
    
    async def set_value(self, tenant_id: str, key: str, value: Any, description: Optional[str] = None) -> Result[TenantSetting]:
        """
        Set a setting value for a tenant.
        
        Creates the setting if it doesn't exist, or updates it if it does.
        
        Args:
            tenant_id: The tenant ID
            key: The setting key
            value: The setting value
            description: Optional description
            
        Returns:
            A Result containing the created or updated setting
        """
        ...


class TenantAwareRepositoryProtocol(Repository[EntityT, Any], Protocol, Generic[EntityT, Any]):
    """
    Repository interface for tenant-aware entities.
    
    This repository automatically filters queries by the current tenant context,
    ensuring proper data isolation between tenants.
    """
    
    async def get_tenant_id(self) -> Result[Optional[str]]:
        """
        Get the current tenant ID from the context.
        
        Returns:
            A Result containing the current tenant ID, or None
        """
        ...


@dataclass
class TenantSQLAlchemyRepository(TenantRepositoryProtocol):
    """
    SQLAlchemy implementation of the tenant repository.
    
    This repository uses SQLAlchemy to interact with the database.
    """
    
    session: AsyncSession
    
    async def get_by_id(self, id: Union[TenantId, str]) -> Result[Optional[Tenant]]:
        """
        Get a tenant by ID.
        
        Args:
            id: The tenant ID
            
        Returns:
            A Result containing the tenant if found, or None
        """
        # Normalize the ID
        if isinstance(id, TenantId):
            tenant_id = id.value
        else:
            tenant_id = str(id)
            if not tenant_id.startswith("ten_"):
                tenant_id = f"ten_{tenant_id}"
        
        try:
            # Execute query
            query = text("""
                SELECT id, name, slug, status, tier, domain, settings, metadata, created_at, updated_at
                FROM tenants
                WHERE id = :tenant_id
            """)
            result = await self.session.execute(query, {"tenant_id": tenant_id})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            tenant = Tenant(
                id=TenantId(row.id),
                name=row.name,
                slug=TenantSlug(row.slug),
                status=row.status,
                tier=row.tier,
                domain=row.domain,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(tenant)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving tenant: {str(e)}",
                context={"tenant_id": tenant_id}
            )
    
    async def get_by_slug(self, slug: str) -> Result[Optional[Tenant]]:
        """
        Get a tenant by slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing the tenant if found, or None
        """
        try:
            # Execute query
            query = text("""
                SELECT id, name, slug, status, tier, domain, settings, metadata, created_at, updated_at
                FROM tenants
                WHERE slug = :slug
            """)
            result = await self.session.execute(query, {"slug": slug})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            tenant = Tenant(
                id=TenantId(row.id),
                name=row.name,
                slug=TenantSlug(row.slug),
                status=row.status,
                tier=row.tier,
                domain=row.domain,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(tenant)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving tenant by slug: {str(e)}",
                context={"slug": slug}
            )
    
    async def get_by_domain(self, domain: str) -> Result[Optional[Tenant]]:
        """
        Get a tenant by domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing the tenant if found, or None
        """
        try:
            # Execute query
            query = text("""
                SELECT id, name, slug, status, tier, domain, settings, metadata, created_at, updated_at
                FROM tenants
                WHERE domain = :domain
            """)
            result = await self.session.execute(query, {"domain": domain})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            tenant = Tenant(
                id=TenantId(row.id),
                name=row.name,
                slug=TenantSlug(row.slug),
                status=row.status,
                tier=row.tier,
                domain=row.domain,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(tenant)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving tenant by domain: {str(e)}",
                context={"domain": domain}
            )
    
    async def exists_by_slug(self, slug: str) -> Result[bool]:
        """
        Check if a tenant exists with the given slug.
        
        Args:
            slug: The tenant slug
            
        Returns:
            A Result containing True if the tenant exists, False otherwise
        """
        try:
            query = text("""
                SELECT EXISTS(SELECT 1 FROM tenants WHERE slug = :slug)
            """)
            result = await self.session.execute(query, {"slug": slug})
            exists = result.scalar_one()
            return Success(exists)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error checking tenant existence by slug: {str(e)}",
                context={"slug": slug}
            )
    
    async def exists_by_domain(self, domain: str) -> Result[bool]:
        """
        Check if a tenant exists with the given domain.
        
        Args:
            domain: The tenant domain
            
        Returns:
            A Result containing True if the tenant exists, False otherwise
        """
        try:
            query = text("""
                SELECT EXISTS(SELECT 1 FROM tenants WHERE domain = :domain)
            """)
            result = await self.session.execute(query, {"domain": domain})
            exists = result.scalar_one()
            return Success(exists)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error checking tenant existence by domain: {str(e)}",
                context={"domain": domain}
            )
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> Result[List[Tenant]]:
        """
        List tenants with optional filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            options: Optional pagination, sorting options
            
        Returns:
            A Result containing a list of tenants
        """
        try:
            # Start building the query
            query_parts = [
                "SELECT id, name, slug, status, tier, domain, settings, metadata, created_at, updated_at",
                "FROM tenants",
                "WHERE 1=1"
            ]
            params = {}
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key == "status":
                        query_parts.append(f"AND status = :status")
                        params["status"] = value
                    elif key == "tier":
                        query_parts.append(f"AND tier = :tier")
                        params["tier"] = value
                    elif key == "name_contains":
                        query_parts.append(f"AND name ILIKE :name_pattern")
                        params["name_pattern"] = f"%{value}%"
                    elif key == "domain_contains":
                        query_parts.append(f"AND domain ILIKE :domain_pattern")
                        params["domain_pattern"] = f"%{value}%"
            
            # Apply sorting
            if options and "sort" in options:
                sort = options["sort"]
                direction = "ASC" if sort.get("direction", "asc").upper() == "ASC" else "DESC"
                
                if sort.get("field") == "name":
                    query_parts.append(f"ORDER BY name {direction}")
                elif sort.get("field") == "created_at":
                    query_parts.append(f"ORDER BY created_at {direction}")
                elif sort.get("field") == "updated_at":
                    query_parts.append(f"ORDER BY updated_at {direction}")
                else:
                    query_parts.append("ORDER BY created_at DESC")
            else:
                query_parts.append("ORDER BY created_at DESC")
            
            # Apply pagination
            if options and "pagination" in options:
                pagination = options["pagination"]
                limit = pagination.get("limit", 50)
                offset = pagination.get("offset", 0)
                
                query_parts.append("LIMIT :limit OFFSET :offset")
                params["limit"] = limit
                params["offset"] = offset
            
            # Execute query
            query = text(" ".join(query_parts))
            result = await self.session.execute(query, params)
            rows = result.fetchall()
            
            # Build tenant entities
            tenants = []
            for row in rows:
                tenant = Tenant(
                    id=TenantId(row.id),
                    name=row.name,
                    slug=TenantSlug(row.slug),
                    status=row.status,
                    tier=row.tier,
                    domain=row.domain,
                    settings=row.settings or {},
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                tenants.append(tenant)
            
            return Success(tenants)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error listing tenants: {str(e)}",
                context={"filters": filters, "options": options}
            )
    
    async def add(self, entity: Tenant) -> Result[Tenant]:
        """
        Add a new tenant.
        
        Args:
            entity: The tenant to add
            
        Returns:
            A Result containing the added tenant
        """
        try:
            # Check if slug is already taken
            slug_exists_result = await self.exists_by_slug(entity.slug.value)
            if slug_exists_result.is_failure():
                return slug_exists_result
                
            if slug_exists_result.value:
                return Failure(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"Tenant with slug '{entity.slug.value}' already exists",
                    context={"slug": entity.slug.value}
                )
            
            # Check if domain is already taken (if provided)
            if entity.domain:
                domain_exists_result = await self.exists_by_domain(entity.domain)
                if domain_exists_result.is_failure():
                    return domain_exists_result
                    
                if domain_exists_result.value:
                    return Failure(
                        code=ErrorCodes.DUPLICATE_RESOURCE,
                        message=f"Tenant with domain '{entity.domain}' already exists",
                        context={"domain": entity.domain}
                    )
            
            # Insert the tenant
            query = text("""
                INSERT INTO tenants 
                (id, name, slug, status, tier, domain, settings, metadata, created_at, updated_at)
                VALUES 
                (:id, :name, :slug, :status, :tier, :domain, :settings, :metadata, :created_at, :updated_at)
                RETURNING id
            """)
            
            result = await self.session.execute(query, {
                "id": entity.id.value,
                "name": entity.name,
                "slug": entity.slug.value,
                "status": entity.status.value,
                "tier": entity.tier,
                "domain": entity.domain,
                "settings": entity.settings,
                "metadata": entity.metadata,
                "created_at": entity.created_at,
                "updated_at": entity.updated_at
            })
            
            await self.session.commit()
            
            # Return the added entity
            return Success(entity)
        except Exception as e:
            await self.session.rollback()
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error adding tenant: {str(e)}",
                context={"tenant": entity}
            )
    
    async def update(self, entity: Tenant) -> Result[Tenant]:
        """
        Update an existing tenant.
        
        Args:
            entity: The tenant to update
            
        Returns:
            A Result containing the updated tenant
        """
        try:
            # Check if the tenant exists
            exists_result = await self.get_by_id(entity.id)
            if exists_result.is_failure():
                return exists_result
                
            if not exists_result.value:
                return Failure(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"Tenant with ID '{entity.id.value}' not found",
                    context={"tenant_id": entity.id.value}
                )
            
            # Check if slug is already taken by a different tenant
            slug_result = await self.get_by_slug(entity.slug.value)
            if slug_result.is_failure():
                return slug_result
                
            if slug_result.value and slug_result.value.id.value != entity.id.value:
                return Failure(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"Tenant with slug '{entity.slug.value}' already exists",
                    context={"slug": entity.slug.value}
                )
            
            # Check if domain is already taken by a different tenant (if provided)
            if entity.domain:
                domain_result = await self.get_by_domain(entity.domain)
                if domain_result.is_failure():
                    return domain_result
                    
                if domain_result.value and domain_result.value.id.value != entity.id.value:
                    return Failure(
                        code=ErrorCodes.DUPLICATE_RESOURCE,
                        message=f"Tenant with domain '{entity.domain}' already exists",
                        context={"domain": entity.domain}
                    )
            
            # Update the tenant
            query = text("""
                UPDATE tenants SET
                name = :name,
                slug = :slug,
                status = :status,
                tier = :tier,
                domain = :domain,
                settings = :settings,
                metadata = :metadata,
                updated_at = :updated_at
                WHERE id = :id
            """)
            
            await self.session.execute(query, {
                "id": entity.id.value,
                "name": entity.name,
                "slug": entity.slug.value,
                "status": entity.status.value,
                "tier": entity.tier,
                "domain": entity.domain,
                "settings": entity.settings,
                "metadata": entity.metadata,
                "updated_at": entity.updated_at
            })
            
            await self.session.commit()
            
            # Return the updated entity
            return Success(entity)
        except Exception as e:
            await self.session.rollback()
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error updating tenant: {str(e)}",
                context={"tenant": entity}
            )
    
    async def delete(self, id: Union[TenantId, str]) -> Result[bool]:
        """
        Delete a tenant.
        
        Args:
            id: The ID of the tenant to delete
            
        Returns:
            A Result containing True if the tenant was deleted, False otherwise
        """
        # Normalize the ID
        if isinstance(id, TenantId):
            tenant_id = id.value
        else:
            tenant_id = str(id)
            if not tenant_id.startswith("ten_"):
                tenant_id = f"ten_{tenant_id}"
        
        try:
            # Check if the tenant exists
            exists_result = await self.get_by_id(tenant_id)
            if exists_result.is_failure():
                return exists_result
                
            if not exists_result.value:
                return Success(False)
            
            # Delete the tenant
            query = text("""
                DELETE FROM tenants WHERE id = :id
            """)
            
            await self.session.execute(query, {"id": tenant_id})
            await self.session.commit()
            
            return Success(True)
        except Exception as e:
            await self.session.rollback()
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error deleting tenant: {str(e)}",
                context={"tenant_id": tenant_id}
            )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count tenants matching the given filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            A Result containing the count of matching tenants
        """
        try:
            # Start building the query
            query_parts = [
                "SELECT COUNT(*)",
                "FROM tenants",
                "WHERE 1=1"
            ]
            params = {}
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key == "status":
                        query_parts.append(f"AND status = :status")
                        params["status"] = value
                    elif key == "tier":
                        query_parts.append(f"AND tier = :tier")
                        params["tier"] = value
                    elif key == "name_contains":
                        query_parts.append(f"AND name ILIKE :name_pattern")
                        params["name_pattern"] = f"%{value}%"
                    elif key == "domain_contains":
                        query_parts.append(f"AND domain ILIKE :domain_pattern")
                        params["domain_pattern"] = f"%{value}%"
            
            # Execute query
            query = text(" ".join(query_parts))
            result = await self.session.execute(query, params)
            count = result.scalar_one()
            
            return Success(count)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error counting tenants: {str(e)}",
                context={"filters": filters}
            )


@dataclass
class UserTenantAssociationSQLAlchemyRepository(UserTenantAssociationRepositoryProtocol):
    """
    SQLAlchemy implementation of the user-tenant association repository.
    
    This repository uses SQLAlchemy to interact with the database.
    """
    
    session: AsyncSession
    
    async def get_by_id(self, id: Union[UserTenantAssociationId, str]) -> Result[Optional[UserTenantAssociation]]:
        """
        Get a user-tenant association by ID.
        
        Args:
            id: The association ID
            
        Returns:
            A Result containing the association if found, or None
        """
        # Normalize the ID
        if isinstance(id, UserTenantAssociationId):
            association_id = id.value
        else:
            association_id = str(id)
            if not association_id.startswith("uta_"):
                association_id = f"uta_{association_id}"
        
        try:
            # Execute query
            query = text("""
                SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                FROM user_tenant_associations
                WHERE id = :id
            """)
            result = await self.session.execute(query, {"id": association_id})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            association = UserTenantAssociation(
                id=UserTenantAssociationId(row.id),
                user_id=UserId(row.user_id),
                tenant_id=TenantId(row.tenant_id),
                roles=row.roles or [],
                is_primary=row.is_primary,
                status=row.status,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(association)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving user-tenant association: {str(e)}",
                context={"association_id": association_id}
            )
    
    async def get_user_tenants(self, user_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all tenants associated with a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        try:
            # Execute query
            query = text("""
                SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                FROM user_tenant_associations
                WHERE user_id = :user_id
                ORDER BY is_primary DESC, created_at ASC
            """)
            result = await self.session.execute(query, {"user_id": user_id})
            rows = result.fetchall()
            
            # Build association entities
            associations = []
            for row in rows:
                association = UserTenantAssociation(
                    id=UserTenantAssociationId(row.id),
                    user_id=UserId(row.user_id),
                    tenant_id=TenantId(row.tenant_id),
                    roles=row.roles or [],
                    is_primary=row.is_primary,
                    status=row.status,
                    settings=row.settings or {},
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                associations.append(association)
            
            return Success(associations)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving user tenants: {str(e)}",
                context={"user_id": user_id}
            )
    
    async def get_tenant_users(self, tenant_id: str) -> Result[List[UserTenantAssociation]]:
        """
        Get all users associated with a tenant.
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        try:
            # Execute query
            query = text("""
                SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                FROM user_tenant_associations
                WHERE tenant_id = :tenant_id
                ORDER BY created_at ASC
            """)
            result = await self.session.execute(query, {"tenant_id": tenant_id})
            rows = result.fetchall()
            
            # Build association entities
            associations = []
            for row in rows:
                association = UserTenantAssociation(
                    id=UserTenantAssociationId(row.id),
                    user_id=UserId(row.user_id),
                    tenant_id=TenantId(row.tenant_id),
                    roles=row.roles or [],
                    is_primary=row.is_primary,
                    status=row.status,
                    settings=row.settings or {},
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                associations.append(association)
            
            return Success(associations)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving tenant users: {str(e)}",
                context={"tenant_id": tenant_id}
            )
    
    async def get_user_tenant(self, user_id: str, tenant_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get a specific user-tenant association.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the association if found, or None
        """
        try:
            # Execute query
            query = text("""
                SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                FROM user_tenant_associations
                WHERE user_id = :user_id AND tenant_id = :tenant_id
            """)
            result = await self.session.execute(query, {"user_id": user_id, "tenant_id": tenant_id})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            association = UserTenantAssociation(
                id=UserTenantAssociationId(row.id),
                user_id=UserId(row.user_id),
                tenant_id=TenantId(row.tenant_id),
                roles=row.roles or [],
                is_primary=row.is_primary,
                status=row.status,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(association)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving user-tenant association: {str(e)}",
                context={"user_id": user_id, "tenant_id": tenant_id}
            )
    
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> Result[bool]:
        """
        Check if a user has access to a tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing True if the user has access, False otherwise
        """
        try:
            # Execute query
            query = text("""
                SELECT EXISTS(
                    SELECT 1 FROM user_tenant_associations
                    WHERE user_id = :user_id
                    AND tenant_id = :tenant_id
                    AND status = 'active'
                )
            """)
            result = await self.session.execute(query, {"user_id": user_id, "tenant_id": tenant_id})
            exists = result.scalar_one()
            
            return Success(exists)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error checking user tenant access: {str(e)}",
                context={"user_id": user_id, "tenant_id": tenant_id}
            )
    
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]:
        """
        Get the user's primary tenant association.
        
        Args:
            user_id: The user ID
            
        Returns:
            A Result containing the primary association if found, or None
        """
        try:
            # Execute query
            query = text("""
                SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                FROM user_tenant_associations
                WHERE user_id = :user_id AND is_primary = TRUE
                LIMIT 1
            """)
            result = await self.session.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            if not row:
                return Success(None)
                
            # Create and return entity
            association = UserTenantAssociation(
                id=UserTenantAssociationId(row.id),
                user_id=UserId(row.user_id),
                tenant_id=TenantId(row.tenant_id),
                roles=row.roles or [],
                is_primary=row.is_primary,
                status=row.status,
                settings=row.settings or {},
                metadata=row.metadata or {},
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            return Success(association)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error retrieving primary tenant: {str(e)}",
                context={"user_id": user_id}
            )
    
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]:
        """
        Set a tenant as the user's primary tenant.
        
        Args:
            user_id: The user ID
            tenant_id: The tenant ID
            
        Returns:
            A Result containing the updated association
        """
        try:
            # Check if association exists
            association_result = await self.get_user_tenant(user_id, tenant_id)
            if association_result.is_failure():
                return association_result
                
            if not association_result.value:
                return Failure(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"User-tenant association not found",
                    context={"user_id": user_id, "tenant_id": tenant_id}
                )
            
            # Begin a transaction
            async with self.session.begin():
                # Clear primary flag from all other associations for this user
                clear_query = text("""
                    UPDATE user_tenant_associations
                    SET is_primary = FALSE, updated_at = NOW()
                    WHERE user_id = :user_id AND is_primary = TRUE
                """)
                await self.session.execute(clear_query, {"user_id": user_id})
                
                # Set primary flag on this association
                update_query = text("""
                    UPDATE user_tenant_associations
                    SET is_primary = TRUE, updated_at = NOW()
                    WHERE user_id = :user_id AND tenant_id = :tenant_id
                    RETURNING id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at
                """)
                result = await self.session.execute(update_query, {"user_id": user_id, "tenant_id": tenant_id})
                row = result.fetchone()
                
                # Create and return entity
                association = UserTenantAssociation(
                    id=UserTenantAssociationId(row.id),
                    user_id=UserId(row.user_id),
                    tenant_id=TenantId(row.tenant_id),
                    roles=row.roles or [],
                    is_primary=row.is_primary,
                    status=row.status,
                    settings=row.settings or {},
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                return Success(association)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error setting primary tenant: {str(e)}",
                context={"user_id": user_id, "tenant_id": tenant_id}
            )
    
    async def list(self, filters: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None) -> Result[List[UserTenantAssociation]]:
        """
        List user-tenant associations with optional filtering and pagination.
        
        Args:
            filters: Optional filters to apply
            options: Optional pagination, sorting options
            
        Returns:
            A Result containing a list of user-tenant associations
        """
        try:
            # Start building the query
            query_parts = [
                "SELECT id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at",
                "FROM user_tenant_associations",
                "WHERE 1=1"
            ]
            params = {}
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key == "user_id":
                        query_parts.append(f"AND user_id = :user_id")
                        params["user_id"] = value
                    elif key == "tenant_id":
                        query_parts.append(f"AND tenant_id = :tenant_id")
                        params["tenant_id"] = value
                    elif key == "status":
                        query_parts.append(f"AND status = :status")
                        params["status"] = value
                    elif key == "is_primary":
                        query_parts.append(f"AND is_primary = :is_primary")
                        params["is_primary"] = value
                    elif key == "role":
                        query_parts.append(f"AND :role = ANY(roles)")
                        params["role"] = value
            
            # Apply sorting
            if options and "sort" in options:
                sort = options["sort"]
                direction = "ASC" if sort.get("direction", "asc").upper() == "ASC" else "DESC"
                
                if sort.get("field") == "created_at":
                    query_parts.append(f"ORDER BY created_at {direction}")
                elif sort.get("field") == "updated_at":
                    query_parts.append(f"ORDER BY updated_at {direction}")
                elif sort.get("field") == "is_primary":
                    query_parts.append(f"ORDER BY is_primary {direction}")
                else:
                    query_parts.append("ORDER BY created_at DESC")
            else:
                query_parts.append("ORDER BY is_primary DESC, created_at ASC")
            
            # Apply pagination
            if options and "pagination" in options:
                pagination = options["pagination"]
                limit = pagination.get("limit", 50)
                offset = pagination.get("offset", 0)
                
                query_parts.append("LIMIT :limit OFFSET :offset")
                params["limit"] = limit
                params["offset"] = offset
            
            # Execute query
            query = text(" ".join(query_parts))
            result = await self.session.execute(query, params)
            rows = result.fetchall()
            
            # Build association entities
            associations = []
            for row in rows:
                association = UserTenantAssociation(
                    id=UserTenantAssociationId(row.id),
                    user_id=UserId(row.user_id),
                    tenant_id=TenantId(row.tenant_id),
                    roles=row.roles or [],
                    is_primary=row.is_primary,
                    status=row.status,
                    settings=row.settings or {},
                    metadata=row.metadata or {},
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                associations.append(association)
            
            return Success(associations)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error listing user-tenant associations: {str(e)}",
                context={"filters": filters, "options": options}
            )
    
    async def add(self, entity: UserTenantAssociation) -> Result[UserTenantAssociation]:
        """
        Add a new user-tenant association.
        
        Args:
            entity: The user-tenant association to add
            
        Returns:
            A Result containing the added user-tenant association
        """
        try:
            # Check if association already exists
            existing_result = await self.get_user_tenant(entity.user_id.value, entity.tenant_id.value)
            if existing_result.is_failure():
                return existing_result
                
            if existing_result.value:
                return Failure(
                    code=ErrorCodes.DUPLICATE_RESOURCE,
                    message=f"User-tenant association already exists",
                    context={"user_id": entity.user_id.value, "tenant_id": entity.tenant_id.value}
                )
            
            # Begin a transaction
            async with self.session.begin():
                # If this is primary, clear other primary associations
                if entity.is_primary:
                    clear_query = text("""
                        UPDATE user_tenant_associations
                        SET is_primary = FALSE, updated_at = NOW()
                        WHERE user_id = :user_id AND is_primary = TRUE
                    """)
                    await self.session.execute(clear_query, {"user_id": entity.user_id.value})
                
                # Insert the association
                query = text("""
                    INSERT INTO user_tenant_associations 
                    (id, user_id, tenant_id, roles, is_primary, status, settings, metadata, created_at, updated_at)
                    VALUES 
                    (:id, :user_id, :tenant_id, :roles, :is_primary, :status, :settings, :metadata, :created_at, :updated_at)
                    RETURNING id
                """)
                
                result = await self.session.execute(query, {
                    "id": entity.id.value,
                    "user_id": entity.user_id.value,
                    "tenant_id": entity.tenant_id.value,
                    "roles": entity.roles,
                    "is_primary": entity.is_primary,
                    "status": entity.status.value,
                    "settings": entity.settings,
                    "metadata": entity.metadata,
                    "created_at": entity.created_at,
                    "updated_at": entity.updated_at
                })
                
                # Return the added entity
                return Success(entity)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error adding user-tenant association: {str(e)}",
                context={"association": entity}
            )
    
    async def update(self, entity: UserTenantAssociation) -> Result[UserTenantAssociation]:
        """
        Update an existing user-tenant association.
        
        Args:
            entity: The user-tenant association to update
            
        Returns:
            A Result containing the updated user-tenant association
        """
        try:
            # Check if the association exists
            exists_result = await self.get_by_id(entity.id)
            if exists_result.is_failure():
                return exists_result
                
            if not exists_result.value:
                return Failure(
                    code=ErrorCodes.RESOURCE_NOT_FOUND,
                    message=f"User-tenant association with ID '{entity.id.value}' not found",
                    context={"association_id": entity.id.value}
                )
            
            # Begin a transaction
            async with self.session.begin():
                # If this is becoming primary, clear other primary associations
                if entity.is_primary and not exists_result.value.is_primary:
                    clear_query = text("""
                        UPDATE user_tenant_associations
                        SET is_primary = FALSE, updated_at = NOW()
                        WHERE user_id = :user_id AND is_primary = TRUE
                    """)
                    await self.session.execute(clear_query, {"user_id": entity.user_id.value})
                
                # Update the association
                query = text("""
                    UPDATE user_tenant_associations SET
                    roles = :roles,
                    is_primary = :is_primary,
                    status = :status,
                    settings = :settings,
                    metadata = :metadata,
                    updated_at = :updated_at
                    WHERE id = :id
                """)
                
                await self.session.execute(query, {
                    "id": entity.id.value,
                    "roles": entity.roles,
                    "is_primary": entity.is_primary,
                    "status": entity.status.value,
                    "settings": entity.settings,
                    "metadata": entity.metadata,
                    "updated_at": entity.updated_at
                })
                
                # Return the updated entity
                return Success(entity)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error updating user-tenant association: {str(e)}",
                context={"association": entity}
            )
    
    async def delete(self, id: Union[UserTenantAssociationId, str]) -> Result[bool]:
        """
        Delete a user-tenant association.
        
        Args:
            id: The ID of the user-tenant association to delete
            
        Returns:
            A Result containing True if the association was deleted, False otherwise
        """
        # Normalize the ID
        if isinstance(id, UserTenantAssociationId):
            association_id = id.value
        else:
            association_id = str(id)
            if not association_id.startswith("uta_"):
                association_id = f"uta_{association_id}"
        
        try:
            # Check if the association exists
            exists_result = await self.get_by_id(association_id)
            if exists_result.is_failure():
                return exists_result
                
            if not exists_result.value:
                return Success(False)
            
            # Delete the association
            query = text("""
                DELETE FROM user_tenant_associations WHERE id = :id
            """)
            
            await self.session.execute(query, {"id": association_id})
            await self.session.commit()
            
            return Success(True)
        except Exception as e:
            await self.session.rollback()
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error deleting user-tenant association: {str(e)}",
                context={"association_id": association_id}
            )
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]:
        """
        Count user-tenant associations matching the given filters.
        
        Args:
            filters: Optional filters to apply
            
        Returns:
            A Result containing the count of matching user-tenant associations
        """
        try:
            # Start building the query
            query_parts = [
                "SELECT COUNT(*)",
                "FROM user_tenant_associations",
                "WHERE 1=1"
            ]
            params = {}
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if key == "user_id":
                        query_parts.append(f"AND user_id = :user_id")
                        params["user_id"] = value
                    elif key == "tenant_id":
                        query_parts.append(f"AND tenant_id = :tenant_id")
                        params["tenant_id"] = value
                    elif key == "status":
                        query_parts.append(f"AND status = :status")
                        params["status"] = value
                    elif key == "is_primary":
                        query_parts.append(f"AND is_primary = :is_primary")
                        params["is_primary"] = value
                    elif key == "role":
                        query_parts.append(f"AND :role = ANY(roles)")
                        params["role"] = value
            
            # Execute query
            query = text(" ".join(query_parts))
            result = await self.session.execute(query, params)
            count = result.scalar_one()
            
            return Success(count)
        except Exception as e:
            return Failure(
                code=ErrorCodes.DATABASE_ERROR,
                message=f"Error counting user-tenant associations: {str(e)}",
                context={"filters": filters}
            )


@dataclass
class TenantAwareSQLAlchemyRepository(TenantAwareRepositoryProtocol, Generic[EntityT, Any]):
    """
    SQLAlchemy implementation of a tenant-aware repository.
    
    This repository automatically filters all queries by the current tenant ID,
    ensuring proper data isolation between tenants.
    """
    
    session: AsyncSession
    model_class: Any
    
    async def get_tenant_id(self) -> Result[Optional[str]]:
        """
        Get the current tenant ID from the context.
        
        Returns:
            A Result containing the current tenant ID, or None
        """
        tenant_id = get_current_tenant_context()
        if not tenant_id:
            return Failure(
                code=ErrorCodes.TENANT_REQUIRED,
                message="No tenant context found. Use tenant_context or set_current_tenant_context to set a tenant.",
                context={}
            )
        return Success(tenant_id)
    
    def _apply_tenant_filter(self, query: str, tenant_id: str) -> str:
        """
        Apply tenant filtering to a query string.
        
        Args:
            query: The query string
            tenant_id: The tenant ID
            
        Returns:
            The modified query string with tenant filtering
        """
        # Add tenant_id condition if not already present in the WHERE clause
        if "WHERE" in query:
            return query.replace("WHERE", f"WHERE tenant_id = '{tenant_id}' AND")
        elif "GROUP BY" in query:
            # Insert before GROUP BY
            return query.replace("GROUP BY", f"WHERE tenant_id = '{tenant_id}' GROUP BY")
        elif "ORDER BY" in query:
            # Insert before ORDER BY
            return query.replace("ORDER BY", f"WHERE tenant_id = '{tenant_id}' ORDER BY")
        elif "LIMIT" in query:
            # Insert before LIMIT
            return query.replace("LIMIT", f"WHERE tenant_id = '{tenant_id}' LIMIT")
        else:
            # Add at the end
            return f"{query} WHERE tenant_id = '{tenant_id}'"
    
    async def add(self, entity: EntityT) -> Result[EntityT]:
        """
        Add an entity, automatically setting the tenant ID from the current context.
        
        Args:
            entity: The entity to add
            
        Returns:
            A Result containing the added entity
        """
        # Get the current tenant ID
        tenant_id_result = await self.get_tenant_id()
        if tenant_id_result.is_failure():
            return tenant_id_result
        
        tenant_id = tenant_id_result.value
        
        # Set tenant_id on the entity
        if hasattr(entity, "tenant_id"):
            entity.tenant_id = tenant_id
        
        # Implement base repository add logic here
        # ...
        
        return Success(entity)
    
    # Implement other methods with tenant filtering...