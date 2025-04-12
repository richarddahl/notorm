"""
Data models for multi-tenancy.

This module defines the core data models for multi-tenancy, including
Tenant and UserTenantAssociation models.
"""

import uuid
from enum import Enum
from datetime import datetime
from typing import Dict, List, Optional, Any

from uno.model import UnoModel
from uno.mixins import TimestampMixin


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


class Tenant(UnoModel, TimestampMixin):
    """
    Representation of a tenant in the system.
    
    A tenant is a logical isolation boundary for data and users.
    """
    id: str = None  # Will be set by the database
    name: str
    slug: str  # URL-friendly identifier
    status: TenantStatus = TenantStatus.ACTIVE
    tier: str = "standard"  # e.g., "basic", "premium", "enterprise"
    domain: Optional[str] = None  # Custom domain for the tenant
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """Initialize a tenant."""
        if 'id' not in data or data['id'] is None:
            # Generate a UUID prefixed with 'ten_' for tenant IDs
            data['id'] = f"ten_{uuid.uuid4().hex}"
        super().__init__(**data)
    
    class Config:
        """Configuration for the Tenant model."""
        table = "tenants"
        schema = {
            "id": {"primary": True},
            "name": {"index": True},
            "slug": {"unique": True, "index": True},
            "domain": {"unique": True, "index": True, "nullable": True}
        }


class UserTenantAssociation(UnoModel, TimestampMixin):
    """
    Associates users with tenants and defines their role within that tenant.
    
    This is the core model for implementing multi-tenancy at the user level.
    """
    id: str = None  # Will be set by the database
    user_id: str
    tenant_id: str
    roles: List[str] = []  # Role within this tenant 
    is_primary: bool = False  # Is this the user's primary tenant?
    status: UserTenantStatus = UserTenantStatus.ACTIVE
    settings: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """Initialize a user-tenant association."""
        if 'id' not in data or data['id'] is None:
            # Generate a UUID prefixed with 'uta_' for user-tenant associations
            data['id'] = f"uta_{uuid.uuid4().hex}"
        super().__init__(**data)
    
    class Config:
        """Configuration for the UserTenantAssociation model."""
        table = "user_tenant_associations"
        schema = {
            "id": {"primary": True},
            "user_id": {"index": True},
            "tenant_id": {"index": True},
            "constraints": [{
                "type": "unique",
                "fields": ["user_id", "tenant_id"]
            }]
        }


class TenantAwareModel(UnoModel):
    """
    Base class for all tenant-scoped entities.
    
    All models that should be tenant-isolated should inherit from this class.
    """
    tenant_id: str
    
    class Config:
        """Configuration for tenant-aware models."""
        abstract = True  # This is an abstract base class
        tenant_aware = True  # Mark this model as tenant-aware for automatic filtering


class TenantSettings(UnoModel, TimestampMixin):
    """
    Settings for a tenant.
    
    Stores configuration settings specific to a tenant.
    """
    id: str = None  # Will be set by the database
    tenant_id: str
    key: str
    value: Any
    description: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize tenant settings."""
        if 'id' not in data or data['id'] is None:
            # Generate a UUID prefixed with 'tset_' for tenant settings
            data['id'] = f"tset_{uuid.uuid4().hex}"
        super().__init__(**data)
    
    class Config:
        """Configuration for the TenantSettings model."""
        table = "tenant_settings"
        schema = {
            "id": {"primary": True},
            "tenant_id": {"index": True},
            "key": {"index": True},
            "constraints": [{
                "type": "unique",
                "fields": ["tenant_id", "key"]
            }]
        }


class TenantInvitation(UnoModel, TimestampMixin):
    """
    Invitation for a user to join a tenant.
    
    Tracks invitations sent to users to join a tenant.
    """
    id: str = None  # Will be set by the database
    tenant_id: str
    email: str
    roles: List[str] = []
    invited_by: str  # User ID who sent the invitation
    token: str  # Unique token for accepting the invitation
    expires_at: datetime
    status: str = "pending"  # pending, accepted, declined, expired
    metadata: Dict[str, Any] = {}
    
    def __init__(self, **data):
        """Initialize a tenant invitation."""
        if 'id' not in data or data['id'] is None:
            # Generate a UUID prefixed with 'inv_' for invitations
            data['id'] = f"inv_{uuid.uuid4().hex}"
        if 'token' not in data or data['token'] is None:
            # Generate a unique token for the invitation
            data['token'] = uuid.uuid4().hex
        super().__init__(**data)
    
    class Config:
        """Configuration for the TenantInvitation model."""
        table = "tenant_invitations"
        schema = {
            "id": {"primary": True},
            "tenant_id": {"index": True},
            "email": {"index": True},
            "token": {"unique": True, "index": True}
        }