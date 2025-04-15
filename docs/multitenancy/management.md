# Tenant Management Interfaces

This document describes the administrative interfaces for managing tenants, users, and tenant-specific configuration settings.

## Tenant Administration

Tenant administration interfaces allow system administrators to create, update, and manage tenants in the system.

### TenantAdminService

The `TenantAdminService` class provides methods for managing tenants, including creating, updating, and deleting tenants, as well as managing tenant users.

```python
from uno.core.multitenancy import TenantAdminService, TenantService

# Create a tenant admin service
tenant_service = TenantService(session)
admin_service = TenantAdminService(tenant_service)

# Create a new tenant
tenant = await admin_service.create_tenant(```

name="ACME Corporation",
slug="acme",
domain="acme.example.com",
tier="premium",
settings={"theme": "dark"}
```
)

# Update an existing tenant
updated_tenant = await admin_service.update_tenant(```

tenant_id=tenant.id,
name="ACME Inc.",
domain="acme-inc.example.com"
```
)

# Delete a tenant (sets status to DELETED)
deleted = await admin_service.delete_tenant(tenant.id)

# Add a user to a tenant
association = await admin_service.add_user_to_tenant(```

tenant_id=tenant.id,
user_data={"user_id": "user123", "roles": ["admin", "editor"]}
```
)

# Update a user's roles in a tenant
updated_association = await admin_service.update_user_tenant(```

tenant_id=tenant.id,
user_id="user123",
user_data={"roles": ["admin", "editor", "viewer"]}
```
)

# Remove a user from a tenant
removed = await admin_service.remove_user_from_tenant(```

tenant_id=tenant.id,
user_id="user123"
```
)

# Invite a user to join a tenant
invitation = await admin_service.invite_user_to_tenant(```

tenant_id=tenant.id,
invite_data={```

"email": "user@example.com",
"roles": ["editor"],
"expires_in_days": 7,
"message": "Please join our tenant"
```
},
invited_by="admin_user_id"
```
)
```

### Admin API Router

The `create_tenant_admin_router` function creates a FastAPI router with endpoints for tenant administration:

```python
from fastapi import FastAPI
from uno.core.multitenancy import create_tenant_admin_router

app = FastAPI()

# Add tenant admin routes
tenant_admin_router = create_tenant_admin_router()
app.include_router(tenant_admin_router)
```

This adds the following API endpoints:

#### Tenant Management (Superadmin Only)

- `POST /admin/tenants/` - Create a new tenant
- `GET /admin/tenants/` - List all tenants
- `GET /admin/tenants/{tenant_id}` - Get a specific tenant
- `PUT /admin/tenants/{tenant_id}` - Update a tenant
- `DELETE /admin/tenants/{tenant_id}` - Delete a tenant

#### Tenant User Management (Tenant Admin Only)

- `POST /admin/tenants/{tenant_id}/users` - Add a user to a tenant
- `GET /admin/tenants/{tenant_id}/users` - List all users in a tenant
- `PUT /admin/tenants/{tenant_id}/users/{user_id}` - Update a user's association with a tenant
- `DELETE /admin/tenants/{tenant_id}/users/{user_id}` - Remove a user from a tenant
- `POST /admin/tenants/{tenant_id}/invitations` - Invite a user to join a tenant

## Tenant Configuration Management

Tenant configuration management interfaces allow tenant administrators to manage tenant-specific configuration settings.

### TenantConfig and TenantConfigService

The `TenantConfig` and `TenantConfigService` classes provide methods for managing tenant-specific configuration settings:

```python
from uno.core.multitenancy import TenantConfig, TenantConfigService, DEFAULT_CONFIG

# Create a tenant config manager
tenant_config = TenantConfig(```

default_config=DEFAULT_CONFIG,
settings_repo=settings_repository
```
)

# Create a tenant config service
config_service = TenantConfigService(```

tenant_config=tenant_config,
schema=CONFIG_SCHEMA
```
)

# Get the configuration for the current tenant
config = await config_service.get_config()

# Get a specific setting with metadata
setting = await config_service.get_setting("appearance.theme")

# Set a specific setting
updated_setting = await config_service.set_setting(```

"appearance.theme", "dark"
```
)

# Delete a specific setting (reset to default)
deleted = await config_service.delete_setting("appearance.theme")

# Reset all settings to defaults
reset_count = await config_service.reset_config()
```

### Configuration API Router

The `create_tenant_config_router` function creates a FastAPI router with endpoints for tenant configuration management:

```python
from fastapi import FastAPI
from uno.core.multitenancy import create_tenant_config_router, DEFAULT_CONFIG, CONFIG_SCHEMA

app = FastAPI()

# Add tenant config routes
tenant_config_router = create_tenant_config_router(```

default_config=DEFAULT_CONFIG,
schema=CONFIG_SCHEMA
```
)
app.include_router(tenant_config_router)

# Or use the default tenant config router
from uno.core.multitenancy import default_tenant_config_router
app.include_router(default_tenant_config_router)
```

This adds the following API endpoints:

- `GET /admin/config/` - Get the configuration for the current tenant
- `GET /admin/config/keys` - List all available configuration keys with metadata
- `GET /admin/config/{key}` - Get a specific configuration value
- `PUT /admin/config/{key}` - Set a specific configuration value
- `DELETE /admin/config/{key}` - Delete a specific configuration value (reset to default)
- `POST /admin/config/reset` - Reset all configuration values to defaults

## Default Configuration

The multi-tenancy system comes with a default configuration that includes settings for:

- **Appearance**: Theme, logo, colors
- **Features**: Enabling/disabling various features
- **Security**: Password policy, session timeout
- **Integrations**: Email, Slack, webhooks
- **Notifications**: Email, in-app, push
- **Defaults**: Page size, date/time formats, timezone, language

The default configuration can be found in the `DEFAULT_CONFIG` constant, and its schema in the `CONFIG_SCHEMA` constant.

## Usage in Applications

### Adding to FastAPI Application

```python
from fastapi import FastAPI
from uno.core.multitenancy import (```

TenantIdentificationMiddleware, TenantService,
create_tenant_admin_router, default_tenant_config_router
```
)

app = FastAPI()

# Add tenant identification middleware
app.add_middleware(```

TenantIdentificationMiddleware,
tenant_service=TenantService(session_factory),
header_name="X-Tenant-ID",
subdomain_pattern=r"(.+)\.example\.com",
path_prefix=True,
exclude_paths=["/api/docs", "/api/auth"]
```
)

# Add tenant admin routes
app.include_router(create_tenant_admin_router())

# Add tenant config routes
app.include_router(default_tenant_config_router)
```

### Using Configuration Values in Application Code

```python
from uno.core.multitenancy import TenantConfig, DEFAULT_CONFIG, tenant_context

# Create a tenant config manager
tenant_config = TenantConfig(```

default_config=DEFAULT_CONFIG,
settings_repo=settings_repository
```
)

# Get configuration in a tenant context
async with tenant_context("tenant123"):```

config = await tenant_config.get_tenant_config()
``````

```
```

# Use configuration values
theme = config["appearance"]["theme"]
page_size = config["defaults"]["page_size"]
``````

```
```

# Check if features are enabled
if config["features"][`analytics`]:```

# Provide analytics features
pass
```
```
```

## Security Considerations

When implementing tenant management interfaces, consider the following security considerations:

1. **Authorization**: Ensure that only appropriate users can access management interfaces:
   - Superadmins for global tenant management
   - Tenant admins for tenant-specific settings and user management
   
2. **Validation**: Validate all inputs to prevent security issues:
   - Validate configuration values against a schema
   - Check access permissions before performing operations
   
3. **Audit Trail**: Keep an audit trail of management operations:
   - Who created or updated a tenant
   - Who added or removed users
   - What configuration settings were changed
   
4. **Tenant Isolation**: Ensure strict tenant isolation:
   - Tenant-specific settings should only be accessible to users in that tenant
   - User management operations should respect tenant boundaries