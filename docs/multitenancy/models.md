# Multi-Tenancy Models

This document describes the core data models for the multi-tenancy system.

## Tenant Model

The `Tenant` model represents a tenant in the system. Each tenant has its own isolated data space.

```python
class Tenant(UnoModel, TimestampMixin):```

id: str = None  # Automatically set to "ten_<uuid>"
name: str
slug: str  # URL-friendly identifier
status: TenantStatus = TenantStatus.ACTIVE
tier: str = "standard"  # e.g., "basic", "premium", "enterprise"
domain: Optional[str] = None  # Custom domain for the tenant
settings: Dict[str, Any] = {}
metadata: Dict[str, Any] = {}
```
```

### Tenant Status

The `TenantStatus` enum defines the possible states of a tenant:

- `ACTIVE`: Tenant is active and can be accessed
- `SUSPENDED`: Tenant is temporarily suspended (e.g., for billing issues)
- `DELETED`: Tenant has been deleted (soft delete)
- `PENDING`: Tenant is in the process of being set up
- `TRIAL`: Tenant is in trial period

## User-Tenant Association

The `UserTenantAssociation` model associates users with tenants and defines their roles within each tenant.

```python
class UserTenantAssociation(UnoModel, TimestampMixin):```

id: str = None  # Automatically set to "uta_<uuid>"
user_id: str
tenant_id: str
roles: List[str] = []  # Roles within this tenant 
is_primary: bool = False  # Is this the user's primary tenant?
status: UserTenantStatus = UserTenantStatus.ACTIVE
settings: Dict[str, Any] = {}
metadata: Dict[str, Any] = {}
```
```

### User-Tenant Status

The `UserTenantStatus` enum defines the possible states of a user's association with a tenant:

- `ACTIVE`: User has active access to the tenant
- `SUSPENDED`: User's access is temporarily suspended
- `INVITED`: User has been invited but hasn't accepted yet
- `DECLINED`: User has declined the invitation

## Tenant-Aware Model

The `TenantAwareModel` is a base class for all tenant-scoped entities. Models that should be tenant-isolated should inherit from this class.

```python
class TenantAwareModel(UnoModel):```

tenant_id: str
``````

```
```

class Config:```

abstract = True  # This is an abstract base class
tenant_aware = True  # Mark this model as tenant-aware for automatic filtering
```
```
```

Using this base class ensures that:

1. All models derived from it have a `tenant_id` field
2. The tenant ID is automatically set when creating new records
3. Queries against these models are automatically filtered by tenant ID when using tenant-aware repositories

## Tenant Settings

The `TenantSettings` model stores configuration settings specific to a tenant.

```python
class TenantSettings(UnoModel, TimestampMixin):```

id: str = None  # Automatically set to "tset_<uuid>"```
```

tenant_id: str
``````

key: str
value: Any
description: Optional[str] = None
```
```

This model allows tenants to have customized settings without modifying the core application.

## Tenant Invitation

The `TenantInvitation` model tracks invitations sent to users to join a tenant.

```python
class TenantInvitation(UnoModel, TimestampMixin):```

id: str = None  # Automatically set to "inv_<uuid>"```
```

tenant_id: str
``````

email: str
roles: List[str] = []
invited_by: str  # User ID who sent the invitation
token: str  # Unique token for accepting the invitation
expires_at: datetime
status: str = "pending"  # pending, accepted, declined, expired
metadata: Dict[str, Any] = {}
```
```

The invitation system allows tenants to invite users and assign them roles without requiring those users to already exist in the system.

## Usage Examples

### Creating a Tenant

```python
# Create a new tenant
tenant = Tenant(```

name="ACME Corporation",
slug="acme",
tier="premium",
domain="acme.example.com",
settings={"theme": "dark", "features": ["analytics", "reporting"]}
```
)

# Save the tenant
tenant_repo = TenantRepository(session, Tenant)
saved_tenant = await tenant_repo.create(tenant.model_dump())
```

### Creating a Tenant-Aware Model

```python
from uno.core.multitenancy import TenantAwareModel

class Product(TenantAwareModel):```

name: str
price: float
description: str
sku: str
stock: int = 0
```

# Create a new product within a tenant context
async with tenant_context("tenant123"):```

product = Product(```

name="Premium Widget",
price=99.99,
description="The best widget money can buy",
sku="WDG-001",
stock=100
```
)
``````

```
```

# The tenant_id will be automatically set to "tenant123"
product_repo = TenantAwareRepository(session, Product)
saved_product = await product_repo.create(product.model_dump())
```
```

### Adding a User to a Tenant

```python
# Associate a user with a tenant
association = UserTenantAssociation(```

user_id="user123",
tenant_id="tenant456",
roles=["admin", "editor"],
is_primary=True
```
)

# Save the association
assoc_repo = UserTenantAssociationRepository(session, UserTenantAssociation)
saved_assoc = await assoc_repo.create(association.model_dump())
```