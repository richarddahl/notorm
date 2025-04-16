"""
Domain entities for multi-tenancy.

This module defines the core domain entities for multi-tenancy, including
Tenant, UserTenantAssociation, and TenantInvitation.
"""

import uuid
from enum import Enum
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from uno.domain.core import Entity, AggregateRoot, ValueObject


class TenantStatus(str, Enum):
    """Status of a tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"
    PENDING = "pending"
    TRIAL = "trial"


class UserTenantStatus(str, Enum):
    """Status of a user's association with a tenant."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INVITED = "invited"
    DECLINED = "declined"


@dataclass(frozen=True)
class TenantId(ValueObject):
    """Value object representing a tenant identifier."""
    value: str
    
    def __post_init__(self):
        """Validate the tenant ID."""
        if not self.value:
            raise ValueError("Tenant ID cannot be empty")
        if not self.value.startswith("ten_"):
            # Using object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "value", f"ten_{self.value}")


@dataclass(frozen=True)
class UserId(ValueObject):
    """Value object representing a user identifier."""
    value: str
    
    def __post_init__(self):
        """Validate the user ID."""
        if not self.value:
            raise ValueError("User ID cannot be empty")


@dataclass(frozen=True)
class UserTenantAssociationId(ValueObject):
    """Value object representing a user-tenant association identifier."""
    value: str
    
    def __post_init__(self):
        """Validate the association ID."""
        if not self.value:
            raise ValueError("User-tenant association ID cannot be empty")
        if not self.value.startswith("uta_"):
            # Using object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "value", f"uta_{self.value}")


@dataclass(frozen=True)
class TenantInvitationId(ValueObject):
    """Value object representing a tenant invitation identifier."""
    value: str
    
    def __post_init__(self):
        """Validate the invitation ID."""
        if not self.value:
            raise ValueError("Tenant invitation ID cannot be empty")
        if not self.value.startswith("inv_"):
            # Using object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "value", f"inv_{self.value}")


@dataclass(frozen=True)
class TenantSlug(ValueObject):
    """Value object representing a tenant slug."""
    value: str
    
    def __post_init__(self):
        """Validate the slug."""
        if not self.value:
            raise ValueError("Tenant slug cannot be empty")
        if not self.value.isascii() or ' ' in self.value:
            raise ValueError("Tenant slug must contain only ASCII characters and no spaces")


@dataclass
class Tenant(AggregateRoot[TenantId]):
    """
    Representation of a tenant in the system.
    
    A tenant is a logical isolation boundary for data and users.
    """
    id: TenantId
    name: str
    slug: TenantSlug
    status: TenantStatus = TenantStatus.ACTIVE
    tier: str = "standard"
    domain: Optional[str] = None
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    
    @classmethod
    def create(cls, name: str, slug: str, tier: str = "standard", domain: Optional[str] = None) -> "Tenant":
        """
        Create a new tenant.
        
        Args:
            name: The name of the tenant
            slug: The slug for the tenant
            tier: The tier of the tenant (e.g., "basic", "premium")
            domain: The custom domain for the tenant
            
        Returns:
            A new Tenant instance
        """
        return cls(
            id=TenantId(f"ten_{uuid.uuid4().hex}"),
            name=name,
            slug=TenantSlug(slug),
            tier=tier,
            domain=domain,
            created_at=datetime.now(timezone.UTC),
            updated_at=datetime.now(timezone.UTC)
        )
    
    def suspend(self) -> None:
        """Suspend this tenant."""
        if self.status == TenantStatus.SUSPENDED:
            return  # Already suspended
            
        self.status = TenantStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.UTC)
    
    def activate(self) -> None:
        """Activate this tenant."""
        if self.status == TenantStatus.ACTIVE:
            return  # Already active
            
        self.status = TenantStatus.ACTIVE
        self.updated_at = datetime.now(timezone.UTC)
    
    def delete(self) -> None:
        """Mark this tenant as deleted."""
        self.status = TenantStatus.DELETED
        self.updated_at = datetime.now(timezone.UTC)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update the tenant settings.
        
        Args:
            settings: The new settings to apply
        """
        self.settings.update(settings)
        self.updated_at = datetime.now(timezone.UTC)
    
    def update_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update the tenant metadata.
        
        Args:
            metadata: The new metadata to apply
        """
        self.metadata.update(metadata)
        self.updated_at = datetime.now(timezone.UTC)
        
    def update(self, 
               name: Optional[str] = None, 
               domain: Optional[str] = None, 
               tier: Optional[str] = None) -> None:
        """
        Update tenant properties.
        
        Args:
            name: New name for the tenant
            domain: New domain for the tenant
            tier: New tier for the tenant
        """
        if name is not None:
            self.name = name
        
        if domain is not None:
            self.domain = domain
            
        if tier is not None:
            self.tier = tier
            
        self.updated_at = datetime.now(timezone.UTC)
        

@dataclass
class UserTenantAssociation(Entity[UserTenantAssociationId]):
    """
    Associates users with tenants and defines their role within that tenant.
    
    This is the core entity for implementing multi-tenancy at the user level.
    """
    id: UserTenantAssociationId
    user_id: UserId
    tenant_id: TenantId
    roles: List[str] = field(default_factory=list)
    is_primary: bool = False
    status: UserTenantStatus = UserTenantStatus.ACTIVE
    settings: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    
    @classmethod
    def create(cls, user_id: str, tenant_id: str, roles: List[str] = None, is_primary: bool = False) -> "UserTenantAssociation":
        """
        Create a new user-tenant association.
        
        Args:
            user_id: The ID of the user
            tenant_id: The ID of the tenant
            roles: The roles of the user in this tenant
            is_primary: Whether this is the user's primary tenant
            
        Returns:
            A new UserTenantAssociation instance
        """
        return cls(
            id=UserTenantAssociationId(f"uta_{uuid.uuid4().hex}"),
            user_id=UserId(user_id),
            tenant_id=TenantId(tenant_id),
            roles=roles or [],
            is_primary=is_primary,
            created_at=datetime.now(timezone.UTC),
            updated_at=datetime.now(timezone.UTC)
        )
    
    def suspend(self) -> None:
        """Suspend this user-tenant association."""
        if self.status == UserTenantStatus.SUSPENDED:
            return  # Already suspended
            
        self.status = UserTenantStatus.SUSPENDED
        self.updated_at = datetime.now(timezone.UTC)
    
    def activate(self) -> None:
        """Activate this user-tenant association."""
        if self.status == UserTenantStatus.ACTIVE:
            return  # Already active
            
        self.status = UserTenantStatus.ACTIVE
        self.updated_at = datetime.now(timezone.UTC)
    
    def set_primary(self, is_primary: bool) -> None:
        """
        Set whether this is the user's primary tenant.
        
        Args:
            is_primary: Whether this is the primary tenant
        """
        if self.is_primary == is_primary:
            return  # No change
            
        self.is_primary = is_primary
        self.updated_at = datetime.now(timezone.UTC)
    
    def add_role(self, role: str) -> None:
        """
        Add a role to this user-tenant association.
        
        Args:
            role: The role to add
        """
        if role in self.roles:
            return  # Already has this role
            
        self.roles.append(role)
        self.updated_at = datetime.now(timezone.UTC)
    
    def remove_role(self, role: str) -> None:
        """
        Remove a role from this user-tenant association.
        
        Args:
            role: The role to remove
        """
        if role not in self.roles:
            return  # Doesn't have this role
            
        self.roles.remove(role)
        self.updated_at = datetime.now(timezone.UTC)
    
    def update_settings(self, settings: Dict[str, Any]) -> None:
        """
        Update the association settings.
        
        Args:
            settings: The new settings to apply
        """
        self.settings.update(settings)
        self.updated_at = datetime.now(timezone.UTC)


@dataclass(frozen=True)
class TenantSettingId(ValueObject):
    """Value object representing a tenant setting identifier."""
    value: str
    
    def __post_init__(self):
        """Validate the tenant setting ID."""
        if not self.value:
            raise ValueError("Tenant setting ID cannot be empty")
        if not self.value.startswith("tset_"):
            # Using object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "value", f"tset_{self.value}")


@dataclass
class TenantSetting(Entity[TenantSettingId]):
    """
    Settings for a tenant.
    
    Stores configuration settings specific to a tenant.
    """
    id: TenantSettingId
    tenant_id: TenantId
    key: str
    value: Any
    description: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    
    @classmethod
    def create(cls, tenant_id: str, key: str, value: Any, description: Optional[str] = None) -> "TenantSetting":
        """
        Create a new tenant setting.
        
        Args:
            tenant_id: The ID of the tenant
            key: The setting key
            value: The setting value
            description: Optional description of the setting
            
        Returns:
            A new TenantSetting instance
        """
        return cls(
            id=TenantSettingId(f"tset_{uuid.uuid4().hex}"),
            tenant_id=TenantId(tenant_id),
            key=key,
            value=value,
            description=description,
            created_at=datetime.now(timezone.UTC),
            updated_at=datetime.now(timezone.UTC)
        )
    
    def update_value(self, value: Any) -> None:
        """
        Update the setting value.
        
        Args:
            value: The new value for the setting
        """
        self.value = value
        self.updated_at = datetime.now(timezone.UTC)
    
    def update_description(self, description: Optional[str]) -> None:
        """
        Update the setting description.
        
        Args:
            description: The new description for the setting
        """
        self.description = description
        self.updated_at = datetime.now(timezone.UTC)


@dataclass
class TenantInvitation(Entity[TenantInvitationId]):
    """
    Invitation for a user to join a tenant.
    
    Tracks invitations sent to users to join a tenant.
    """
    id: TenantInvitationId
    tenant_id: TenantId
    email: str
    roles: List[str] = field(default_factory=list)
    invited_by: UserId
    token: str
    expires_at: datetime
    status: str = "pending"
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.UTC))
    
    @classmethod
    def create(cls, tenant_id: str, email: str, invited_by: str, 
               roles: List[str] = None, expires_at: Optional[datetime] = None) -> "TenantInvitation":
        """
        Create a new tenant invitation.
        
        Args:
            tenant_id: The ID of the tenant
            email: The email of the invitee
            invited_by: The ID of the user who sent the invitation
            roles: The roles to grant to the user
            expires_at: When the invitation expires, defaults to 7 days from now
            
        Returns:
            A new TenantInvitation instance
        """
        if expires_at is None:
            # Default to 7 days from now
            expires_at = datetime.now(timezone.UTC) + datetime.timedelta(days=7)
            
        return cls(
            id=TenantInvitationId(f"inv_{uuid.uuid4().hex}"),
            tenant_id=TenantId(tenant_id),
            email=email,
            roles=roles or [],
            invited_by=UserId(invited_by),
            token=uuid.uuid4().hex,
            expires_at=expires_at,
            created_at=datetime.now(timezone.UTC),
            updated_at=datetime.now(timezone.UTC)
        )
    
    def accept(self) -> None:
        """Mark the invitation as accepted."""
        if self.status != "pending":
            raise ValueError(f"Cannot accept invitation with status '{self.status}'")
            
        if self.is_expired():
            raise ValueError("Cannot accept expired invitation")
            
        self.status = "accepted"
        self.updated_at = datetime.now(timezone.UTC)
    
    def decline(self) -> None:
        """Mark the invitation as declined."""
        if self.status != "pending":
            raise ValueError(f"Cannot decline invitation with status '{self.status}'")
            
        self.status = "declined"
        self.updated_at = datetime.now(timezone.UTC)
    
    def is_expired(self) -> bool:
        """
        Check if the invitation has expired.
        
        Returns:
            True if the invitation has expired, False otherwise
        """
        return self.expires_at < datetime.now(timezone.UTC)
    
    def is_valid(self) -> bool:
        """
        Check if the invitation is valid (pending and not expired).
        
        Returns:
            True if the invitation is valid, False otherwise
        """
        return self.status == "pending" and not self.is_expired()


# Request/Response models for API integration

@dataclass
class TenantCreateRequest:
    """Request model for creating a tenant."""
    name: str
    slug: str
    tier: Optional[str] = "standard"
    domain: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TenantUpdateRequest:
    """Request model for updating a tenant."""
    name: Optional[str] = None
    domain: Optional[str] = None
    tier: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class UserTenantAssociationCreateRequest:
    """Request model for creating a user-tenant association."""
    user_id: str
    tenant_id: str
    roles: Optional[List[str]] = None
    is_primary: Optional[bool] = False
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TenantInvitationCreateRequest:
    """Request model for creating a tenant invitation."""
    tenant_id: str
    email: str
    roles: Optional[List[str]] = None
    expiration_days: Optional[int] = 7
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class TenantResponse:
    """Response model for a tenant."""
    id: str
    name: str
    slug: str
    status: str
    tier: str
    domain: Optional[str]
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, tenant: Tenant) -> "TenantResponse":
        """
        Create a response model from a tenant entity.
        
        Args:
            tenant: The tenant entity
            
        Returns:
            A TenantResponse instance
        """
        return cls(
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


@dataclass
class UserTenantAssociationResponse:
    """Response model for a user-tenant association."""
    id: str
    user_id: str
    tenant_id: str
    roles: List[str]
    is_primary: bool
    status: str
    settings: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, association: UserTenantAssociation) -> "UserTenantAssociationResponse":
        """
        Create a response model from a user-tenant association entity.
        
        Args:
            association: The user-tenant association entity
            
        Returns:
            A UserTenantAssociationResponse instance
        """
        return cls(
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


@dataclass
class TenantInvitationResponse:
    """Response model for a tenant invitation."""
    id: str
    tenant_id: str
    email: str
    roles: List[str]
    invited_by: str
    expires_at: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def from_entity(cls, invitation: TenantInvitation) -> "TenantInvitationResponse":
        """
        Create a response model from a tenant invitation entity.
        
        Args:
            invitation: The tenant invitation entity
            
        Returns:
            A TenantInvitationResponse instance
        """
        return cls(
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