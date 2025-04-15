# Multi-Tenancy Support

The Uno framework provides comprehensive multi-tenancy support, allowing you to build applications that serve multiple customers (tenants) from a single deployment while keeping their data isolated.

## Overview

Multi-tenancy is an architecture where a single instance of software serves multiple customers (tenants). Each tenant's data is isolated and remains invisible to other tenants. This model offers several advantages:

- **Cost Efficiency**: Shared infrastructure reduces operational costs
- **Simplified Maintenance**: Single codebase to maintain and update
- **Scalability**: Resources can be allocated dynamically based on tenant needs
- **Rapid Onboarding**: New tenants can be added without infrastructure changes

The Uno framework implements a **shared schema multi-tenancy** approach, where all tenants share the same database schema but rows are filtered by tenant ID. This approach offers a good balance between resource efficiency and data isolation.

## Architecture

The multi-tenancy implementation in Uno consists of several key components:

1. **Database Isolation**: PostgreSQL Row Level Security (RLS) policies ensure tenant data isolation at the database level
2. **Tenant Context**: Context variables track the current tenant throughout request processing
3. **Tenant-Aware Models**: Base models that automatically include tenant ID fields
4. **Tenant-Aware Repositories**: Data access components that automatically filter by tenant ID
5. **Middleware**: Components that identify the current tenant from HTTP requests
6. **Utility Functions**: Helper functions for working with multi-tenant applications

### Database Isolation with PostgreSQL RLS

At the core of the multi-tenancy implementation is PostgreSQL's Row Level Security (RLS) feature. RLS allows you to define policies that restrict which rows a user can see in a table.

For tenant-aware tables, the framework applies the following RLS policies:

- **SELECT**: Only return rows where `tenant_id` matches the current tenant
- **INSERT**: Only allow inserts where `tenant_id` matches the current tenant
- **UPDATE**: Only allow updates where `tenant_id` matches the current tenant
- **DELETE**: Only allow deletes where `tenant_id` matches the current tenant

These policies are enforced at the database level, providing a robust security boundary.

### Tenant Context Management

To keep track of the current tenant throughout request processing, the framework uses context variables (specifically, AsyncIO's `ContextVar`). This allows the tenant context to flow naturally through asynchronous code.

The tenant context is typically set by middleware at the beginning of request processing and then used by tenant-aware repositories to filter queries.

### Tenant-Aware Models

Tenant-aware models inherit from the `TenantAwareModel` base class, which includes a `tenant_id` field. This field is automatically populated when creating new records.

```python
from uno.core.multitenancy import TenantAwareModel

class Product(TenantAwareModel):```

name: str
price: float
description: str
```
```

### Tenant-Aware Repositories

The `TenantAwareRepository` class automatically filters queries by the current tenant ID. It ensures that a tenant can only access its own data.

```python
from uno.core.multitenancy import TenantAwareRepository

class ProductRepository(TenantAwareRepository):```

# All methods inherit tenant filtering behavior
pass
```
```

## Getting Started

### 1. Configure Middleware

Add the tenant identification middleware to your application:

```python
from uno.core.multitenancy import TenantIdentificationMiddleware, TenantService

app = FastAPI()

# Add the middleware
app.add_middleware(```

TenantIdentificationMiddleware,
tenant_service=TenantService(),
header_name="X-Tenant-ID",
subdomain_pattern=r"(.+)\.example\.com",
path_prefix=True,
exclude_paths=["/api/docs", "/api/auth"]
```
)
```

### 2. Create Tenant-Aware Models

Define your tenant-aware models by inheriting from `TenantAwareModel`:

```python
from uno.core.multitenancy import TenantAwareModel

class Customer(TenantAwareModel):```

name: str
email: str
status: str = "active"
```
```

### 3. Use Tenant-Aware Repositories

Create repositories for your tenant-aware models:

```python
from uno.core.multitenancy import TenantAwareRepository
from .models import Customer

class CustomerRepository(TenantAwareRepository):```

def __init__(self, session):```

super().__init__(session, Customer)
```
``````

```
```

# Add custom query methods as needed
async def find_active_customers(self):```

return await self.find_by(status="active")
```
```
```

### 4. Protect Routes with Tenant Validation

Use the tenant dependencies to ensure routes are protected:

```python
from fastapi import Depends, APIRouter
from uno.core.multitenancy import tenant_required, TenantService

router = APIRouter()

@router.get("/customers")
async def list_customers(```

tenant_id: str = Depends(tenant_required()),
customer_repo: CustomerRepository = Depends()
```
):```

# tenant_id parameter ensures tenant access is validated
# and sets the current tenant context
customers = await customer_repo.list()
return customers
```
```

## Tenant Identification Strategies

The framework supports multiple strategies for identifying the current tenant:

1. **Header**: Extract tenant ID from a request header (e.g., `X-Tenant-ID`)
2. **Subdomain**: Extract tenant ID from a subdomain (e.g., `tenant1.example.com`)
3. **Path Prefix**: Extract tenant ID from URL path prefix (e.g., `/tenant1/resource`)
4. **JWT Claim**: Extract tenant ID from a JWT claim in the authentication token

You can configure which strategies to use when setting up the middleware.

## Advanced Usage

### Managing Tenants

The `TenantService` provides methods for managing tenants:

```python
from uno.core.multitenancy import TenantService

async def create_new_tenant(tenant_data):```

tenant_service = TenantService()
tenant = await tenant_service.create_tenant(```

name=tenant_data.name,
slug=tenant_data.slug,
settings=tenant_data.settings
```
)
return tenant
```
```

### Cross-Tenant Operations

For administrative purposes, you might need to perform operations across tenants. The `AdminTenantMixin` allows you to temporarily switch tenant context:

```python
from uno.core.multitenancy import AdminTenantMixin

class AdminService(AdminTenantMixin):```

def __init__(self, session):```

super().__init__(session)
```
``````

```
```

async def count_users_across_tenants(self, tenant_ids):```

results = {}
for tenant_id in tenant_ids:
    # Switch to tenant context
    await self.switch_tenant(tenant_id)
    
    # Run tenant-scoped query
    user_count = await user_repository.count()
    results[tenant_id] = user_count
    
    # Restore original tenant context
    await self.restore_tenant()
``````

```
```

return results
```
```
```

### Superuser Access

The `SuperuserBypassMixin` allows database superusers to bypass tenant isolation for maintenance tasks:

```python
from uno.core.multitenancy import SuperuserBypassMixin

class MaintenanceService(SuperuserBypassMixin):```

def __init__(self, session):```

super().__init__(session)
```
``````

```
```

async def perform_maintenance(self):```

# Temporarily bypass RLS (only works for database superusers)
async with self:
    # Run queries without tenant filtering
    results = await session.execute("SELECT * FROM user_data")
    return results.fetchall()
```
```
```

## Security Considerations

- **RLS Enforcement**: The framework relies on PostgreSQL RLS policies for tenant isolation. Ensure your database users (except superusers) cannot bypass RLS.
- **Tenant Context**: Always validate the tenant context before performing data operations.
- **Middleware Configuration**: Configure the middleware to exclude public routes and authentication endpoints.
- **SQL Injection**: Be vigilant about SQL injection vulnerabilities, as they could potentially bypass tenant isolation.