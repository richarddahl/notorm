# Multi-tenancy in Uno

Multi-tenancy is a software architecture pattern where a single instance of an application serves multiple tenants. In Uno, comprehensive multi-tenancy support is provided through a domain-driven design approach with clear separation of concerns.

## Overview

The multi-tenancy module in Uno provides:

1. **Tenant Management**: Create, update, and delete tenants
2. **User-Tenant Associations**: Manage which users have access to which tenants and with what roles
3. **Tenant Invitations**: Invite users to join tenants
4. **Context Management**: Track and manage the current tenant in the execution context
5. **Isolation Strategies**: Ensure data isolation between tenants
6. **Middleware**: Support for identifying the tenant in HTTP requests

## Domain Model

The multi-tenancy module follows a domain-driven design approach with the following key entities:

### Tenant

```python
@dataclass
class Tenant(AggregateRoot[TenantId]):
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
```

A tenant represents a logical separation within the application. Each tenant has:
- A unique ID
- A name and slug (URL-friendly identifier)
- A status (active, suspended, etc.)
- A tier (standard, premium, etc.)
- An optional custom domain
- Settings and metadata dictionaries
- Creation and update timestamps

### UserTenantAssociation

```python
@dataclass
class UserTenantAssociation(Entity[UserTenantAssociationId]):
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
```

A user-tenant association represents the relationship between a user and a tenant. Each association has:
- A unique ID
- References to the user and tenant
- A list of roles the user has in the tenant
- A flag indicating if this is the user's primary tenant
- A status (active, suspended, etc.)
- Settings and metadata dictionaries
- Creation and update timestamps

### TenantInvitation

```python
@dataclass
class TenantInvitation(Entity[TenantInvitationId]):
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
```

A tenant invitation represents an invitation for a user to join a tenant. Each invitation has:
- A unique ID
- A reference to the tenant
- The invitee's email
- The roles the invitee will have
- A reference to the user who sent the invitation
- A token for accepting the invitation
- An expiration date
- A status (pending, accepted, declined, etc.)
- Metadata dictionary
- Creation and update timestamps

## Repositories

The multi-tenancy module provides the following repository interfaces:

```python
class TenantRepositoryProtocol(Repository[Tenant, TenantId], Protocol):
    """Repository interface for tenant entities."""
    
    async def get_by_slug(self, slug: str) -> Result[Optional[Tenant]]: ...
    async def get_by_domain(self, domain: str) -> Result[Optional[Tenant]]: ...
    async def exists_by_slug(self, slug: str) -> Result[bool]: ...
    async def exists_by_domain(self, domain: str) -> Result[bool]: ...

class UserTenantAssociationRepositoryProtocol(Repository[UserTenantAssociation, UserTenantAssociationId], Protocol):
    """Repository interface for user-tenant association entities."""
    
    async def get_user_tenants(self, user_id: str) -> Result[List[UserTenantAssociation]]: ...
    async def get_tenant_users(self, tenant_id: str) -> Result[List[UserTenantAssociation]]: ...
    async def get_user_tenant(self, user_id: str, tenant_id: str) -> Result[Optional[UserTenantAssociation]]: ...
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> Result[bool]: ...
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]: ...
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]: ...

class TenantInvitationRepositoryProtocol(Repository[TenantInvitation, TenantInvitationId], Protocol):
    """Repository interface for tenant invitation entities."""
    
    async def get_by_email_and_tenant(self, email: str, tenant_id: str) -> Result[Optional[TenantInvitation]]: ...
    async def get_by_token(self, token: str) -> Result[Optional[TenantInvitation]]: ...
    async def get_tenant_invitations(self, tenant_id: str) -> Result[List[TenantInvitation]]: ...
    async def get_user_invitations(self, email: str) -> Result[List[TenantInvitation]]: ...
```

## Services

The multi-tenancy module provides the following service interfaces:

```python
class TenantServiceProtocol(Service, Protocol):
    """Service interface for tenant management."""
    
    async def create_tenant(self, request: TenantCreateRequest) -> Result[Tenant]: ...
    async def get_tenant(self, tenant_id: str) -> Result[Tenant]: ...
    async def get_tenant_by_slug(self, slug: str) -> Result[Tenant]: ...
    async def get_tenant_by_domain(self, domain: str) -> Result[Tenant]: ...
    async def update_tenant(self, tenant_id: str, request: TenantUpdateRequest) -> Result[Tenant]: ...
    async def delete_tenant(self, tenant_id: str) -> Result[bool]: ...
    async def list_tenants(self, filters: Optional[Dict[str, Any]] = None, ...) -> Result[List[Tenant]]: ...
    async def count_tenants(self, filters: Optional[Dict[str, Any]] = None) -> Result[int]: ...
    async def suspend_tenant(self, tenant_id: str) -> Result[Tenant]: ...
    async def activate_tenant(self, tenant_id: str) -> Result[Tenant]: ...
    async def update_tenant_settings(self, tenant_id: str, settings: Dict[str, Any]) -> Result[Tenant]: ...

class UserTenantServiceProtocol(Service, Protocol):
    """Service interface for user-tenant association management."""
    
    async def create_association(self, request: UserTenantAssociationCreateRequest) -> Result[UserTenantAssociation]: ...
    async def get_association(self, association_id: str) -> Result[UserTenantAssociation]: ...
    async def get_user_tenant_association(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]: ...
    async def update_association_roles(self, association_id: str, roles: List[str]) -> Result[UserTenantAssociation]: ...
    async def update_association_status(self, association_id: str, status: UserTenantStatus) -> Result[UserTenantAssociation]: ...
    async def delete_association(self, association_id: str) -> Result[bool]: ...
    async def get_user_tenants(self, user_id: str) -> Result[List[UserTenantAssociation]]: ...
    async def get_tenant_users(self, tenant_id: str) -> Result[List[UserTenantAssociation]]: ...
    async def set_primary_tenant(self, user_id: str, tenant_id: str) -> Result[UserTenantAssociation]: ...
    async def get_primary_tenant(self, user_id: str) -> Result[Optional[UserTenantAssociation]]: ...
    async def user_has_access_to_tenant(self, user_id: str, tenant_id: str) -> Result[bool]: ...

class TenantInvitationServiceProtocol(Service, Protocol):
    """Service interface for tenant invitation management."""
    
    async def create_invitation(self, request: TenantInvitationCreateRequest, invited_by: str) -> Result[TenantInvitation]: ...
    async def get_invitation(self, invitation_id: str) -> Result[TenantInvitation]: ...
    async def get_invitation_by_token(self, token: str) -> Result[TenantInvitation]: ...
    async def accept_invitation(self, token: str, user_id: str) -> Result[UserTenantAssociation]: ...
    async def decline_invitation(self, token: str) -> Result[TenantInvitation]: ...
    async def get_tenant_invitations(self, tenant_id: str) -> Result[List[TenantInvitation]]: ...
    async def get_user_invitations(self, email: str) -> Result[List[TenantInvitation]]: ...
    async def delete_invitation(self, invitation_id: str) -> Result[bool]: ...
```

## Context Management

The multi-tenancy module provides context management utilities for tracking the current tenant:

```python
# Get the current tenant ID
tenant_id = get_current_tenant_context()

# Set the current tenant ID
set_current_tenant_context("tenant_123")

# Clear the tenant context
clear_tenant_context()

# Use context manager for scoped tenant context
async with tenant_context("tenant_123"):
    # All operations in this block are scoped to tenant_123
    result = await repository.find_all()

# Or use the class-based context manager
async with TenantContext("tenant_123"):
    # All operations in this block are scoped to tenant_123
    result = await repository.find_all()
```

## Dependency Injection

The multi-tenancy module provides a dependency injection provider for configuring the dependencies:

```python
from uno.core.multitenancy import MultitenancyProvider

# Configure with default in-memory repositories
MultitenancyProvider.configure()

# Configure with a session factory for SQLAlchemy repositories
MultitenancyProvider.configure(session_factory=session_factory)

# Configure with custom repositories
MultitenancyProvider.configure(
    tenant_repository=custom_tenant_repository,
    user_tenant_repository=custom_user_tenant_repository,
    tenant_invitation_repository=custom_tenant_invitation_repository
)

# Get the tenant service
tenant_service = MultitenancyProvider.get_tenant_service()

# Get the user-tenant service
user_tenant_service = MultitenancyProvider.get_user_tenant_service()

# Get the tenant invitation service
tenant_invitation_service = MultitenancyProvider.get_tenant_invitation_service()
```

## FastAPI Integration

The multi-tenancy module provides FastAPI endpoints for managing tenants, user-tenant associations, and tenant invitations:

```python
from fastapi import FastAPI
from uno.core.multitenancy import multitenancy_router, MultitenancyProvider

# Configure the provider
MultitenancyProvider.configure(session_factory=session_factory)

# Create FastAPI app
app = FastAPI()

# Include the multitenancy router
app.include_router(multitenancy_router)
```

This router provides the following endpoints:

### Tenant Endpoints

- `POST /api/v1/tenants`: Create a new tenant
- `GET /api/v1/tenants/{tenant_id}`: Get a tenant by ID
- `GET /api/v1/tenants`: List tenants with filtering and pagination
- `PATCH /api/v1/tenants/{tenant_id}`: Update a tenant
- `DELETE /api/v1/tenants/{tenant_id}`: Delete a tenant
- `POST /api/v1/tenants/{tenant_id}/suspend`: Suspend a tenant
- `POST /api/v1/tenants/{tenant_id}/activate`: Activate a tenant

### User-Tenant Association Endpoints

- `POST /api/v1/user-tenants`: Create a new user-tenant association
- `GET /api/v1/user-tenants/{association_id}`: Get a user-tenant association by ID
- `GET /api/v1/users/{user_id}/tenants`: Get all tenants associated with a user
- `GET /api/v1/tenants/{tenant_id}/users`: Get all users associated with a tenant
- `POST /api/v1/users/{user_id}/tenants/{tenant_id}/primary`: Set a tenant as the user's primary tenant
- `DELETE /api/v1/user-tenants/{association_id}`: Delete a user-tenant association

### Tenant Invitation Endpoints

- `POST /api/v1/tenant-invitations`: Create a new tenant invitation
- `GET /api/v1/tenant-invitations/{invitation_id}`: Get a tenant invitation by ID
- `GET /api/v1/tenant-invitations/token/{token}`: Get a tenant invitation by token
- `POST /api/v1/tenant-invitations/accept`: Accept a tenant invitation
- `POST /api/v1/tenant-invitations/decline`: Decline a tenant invitation
- `GET /api/v1/tenants/{tenant_id}/invitations`: Get all invitations for a tenant
- `GET /api/v1/users/email/{email}/invitations`: Get all invitations for a user email
- `DELETE /api/v1/tenant-invitations/{invitation_id}`: Delete a tenant invitation

## Middleware

The multi-tenancy module provides FastAPI middleware for identifying the tenant in HTTP requests:

```python
from fastapi import FastAPI
from uno.core.multitenancy import TenantHeaderMiddleware

app = FastAPI()

# Add middleware to identify tenant from header
app.add_middleware(TenantHeaderMiddleware, header_name="X-Tenant-ID")
```

Available middleware:

- `TenantHeaderMiddleware`: Identifies tenant from a request header
- `TenantHostMiddleware`: Identifies tenant from the request hostname
- `TenantPathMiddleware`: Identifies tenant from a path parameter or prefix

## Example Usage

### Create and Configure a Tenant

```python
import asyncio
from uno.core.multitenancy import MultitenancyProvider, TenantCreateRequest

async def create_tenant_example():
    # Configure the provider
    MultitenancyProvider.configure()
    
    # Get the tenant service
    tenant_service = MultitenancyProvider.get_tenant_service()
    
    # Create a tenant
    create_request = TenantCreateRequest(
        name="Example Company",
        slug="example-company",
        tier="premium",
        domain="example.com"
    )
    
    result = await tenant_service.create_tenant(create_request)
    if result.is_success():
        tenant = result.value
        print(f"Created tenant: {tenant.name} (ID: {tenant.id.value})")
    else:
        print(f"Error: {result.error.message}")

asyncio.run(create_tenant_example())
```

### Assign a User to a Tenant

```python
import asyncio
from uno.core.multitenancy import MultitenancyProvider, UserTenantAssociationCreateRequest

async def assign_user_example():
    # Configure the provider
    MultitenancyProvider.configure()
    
    # Get the user-tenant service
    user_tenant_service = MultitenancyProvider.get_user_tenant_service()
    
    # Create an association
    create_request = UserTenantAssociationCreateRequest(
        user_id="user_123",
        tenant_id="ten_456",
        roles=["admin", "user"],
        is_primary=True
    )
    
    result = await user_tenant_service.create_association(create_request)
    if result.is_success():
        association = result.value
        print(f"Created association: User {association.user_id.value} -> Tenant {association.tenant_id.value}")
        print(f"Roles: {', '.join(association.roles)}")
    else:
        print(f"Error: {result.error.message}")

asyncio.run(assign_user_example())
```

### Invite a User to a Tenant

```python
import asyncio
from uno.core.multitenancy import MultitenancyProvider, TenantInvitationCreateRequest

async def invite_user_example():
    # Configure the provider
    MultitenancyProvider.configure()
    
    # Get the tenant invitation service
    invitation_service = MultitenancyProvider.get_tenant_invitation_service()
    
    # Create an invitation
    create_request = TenantInvitationCreateRequest(
        tenant_id="ten_456",
        email="user@example.com",
        roles=["user"],
        expiration_days=7
    )
    
    result = await invitation_service.create_invitation(create_request, invited_by="user_789")
    if result.is_success():
        invitation = result.value
        print(f"Created invitation: {invitation.email} -> Tenant {invitation.tenant_id.value}")
        print(f"Token: {invitation.token}")
        print(f"Expires: {invitation.expires_at}")
    else:
        print(f"Error: {result.error.message}")

asyncio.run(invite_user_example())
```

### Using Tenant-Aware Repositories

```python
import asyncio
from uno.core.multitenancy import tenant_context, TenantAwareRepositoryProtocol
from uno.core.di import inject

@inject
async def example_query(repository: TenantAwareRepositoryProtocol):
    # Without tenant context, operations will fail
    try:
        result = await repository.list()
        print("This should not succeed without tenant context")
    except Exception as e:
        print(f"Expected error: {str(e)}")
    
    # With tenant context, operations work
    async with tenant_context("ten_123"):
        result = await repository.list()
        print(f"Found {len(result.value)} items in tenant ten_123")

asyncio.run(example_query())
```

## Testing

For testing, the multi-tenancy module provides a testing provider:

```python
from unittest.mock import Mock
from uno.core.multitenancy import TestingMultitenancyProvider

# Configure with mock repositories
mock_tenant_repo = Mock()
mock_user_tenant_repo = Mock()
mock_invitation_repo = Mock()

dependencies = TestingMultitenancyProvider.configure(
    tenant_repository=mock_tenant_repo,
    user_tenant_repository=mock_user_tenant_repo,
    tenant_invitation_repository=mock_invitation_repo
)

# Access services for testing
tenant_service = dependencies["tenant_service"]
user_tenant_service = dependencies["user_tenant_service"]
invitation_service = dependencies["tenant_invitation_service"]
```

## Conclusion

The multi-tenancy module provides a complete solution for building multi-tenant applications with Uno. It follows a domain-driven design approach with clear separation of concerns, making it easy to extend and customize for specific needs.

The module provides all the necessary components for managing tenants, user-tenant associations, and tenant invitations, as well as context management, isolation strategies, and middleware for identifying tenants in HTTP requests.

By using the multi-tenancy module, you can easily add multi-tenancy support to your Uno application, ensuring proper data isolation between tenants and providing a seamless experience for users across multiple tenants.