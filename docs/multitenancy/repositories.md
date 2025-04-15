# Tenant-Aware Repositories and Context Management

This document describes the tenant-aware repositories and context management components of the multi-tenancy system.

## Tenant Context Management

Tenant context management is the foundation of the multi-tenancy system. It uses context variables to track the current tenant ID throughout request processing.

### Context Variables

The tenant context is maintained using AsyncIO's `ContextVar`, which provides a way to store and retrieve context-local state in asynchronous code.

```python
# Create a context variable to store the current tenant ID
_tenant_context = contextvars.ContextVar("tenant_context", default=None)

def get_current_tenant_context() -> Optional[str]:```

"""Get the ID of the tenant in the current context."""
return _tenant_context.get()
```

def set_current_tenant_context(tenant_id: Optional[str]) -> None:```

"""Set the tenant ID for the current context."""
_tenant_context.set(tenant_id)
```

def clear_tenant_context() -> None:```

"""Clear the tenant context for the current execution."""
_tenant_context.set(None)
```
```

### Context Manager

The `tenant_context` context manager provides a convenient way to scope operations to a specific tenant:

```python
@asynccontextmanager
async def tenant_context(tenant_id: Optional[str]):```

"""
Context manager for tenant context.
``````

```
```

This creates a context where all operations are scoped to the specified tenant.
The tenant context is cleared when the context is exited.
"""
# Save the current context
previous_context = get_current_tenant_context()
``````

```
```

# Set the new context
set_current_tenant_context(tenant_id)
``````

```
```

# Set PostgreSQL session variable
await set_postgresql_context(tenant_id)
``````

```
```

try:```

# Yield control back to the caller
yield
```
finally:```

# Restore the previous context
set_current_tenant_context(previous_context)
``````

```
```

# Restore PostgreSQL session variable
await set_postgresql_context(previous_context)
```
```
```

### TenantContext Class

The `TenantContext` class provides an object-oriented interface for tenant context management:

```python
class TenantContext:```

"""
Maintains the current tenant context.
``````

```
```

This class provides an async context manager for tenant context management.
"""
``````

```
```

def __init__(self, tenant_id: Optional[str] = None):```

"""Initialize a tenant context."""
self.tenant_id = tenant_id
self._previous_context = None
self._token = None
```
``````

```
```

async def __aenter__(self):```

"""Set this context as the current tenant context."""
self._previous_context = get_current_tenant_context()
self._token = _tenant_context.set(self.tenant_id)
``````

```
```

# Set PostgreSQL session variable
await set_postgresql_context(self.tenant_id)
``````

```
```

return self
```
``````

```
```

async def __aexit__(self, exc_type, exc_val, exc_tb):```

"""Restore the previous tenant context."""
_tenant_context.reset(self._token)
``````

```
```

# Restore PostgreSQL session variable
await set_postgresql_context(self._previous_context)
```
```
```

## Tenant-Aware Repositories

Tenant-aware repositories automatically filter queries by the current tenant ID, ensuring that a tenant can only access its own data.

### TenantAwareRepository Class

The `TenantAwareRepository` class extends the base repository to include tenant filtering:

```python
class TenantAwareRepository(UnoBaseRepository[ModelT]):```

"""
Repository for tenant-aware models.
``````

```
```

This repository automatically filters all queries by the current tenant ID,
ensuring that data is properly isolated between tenants.
"""
``````

```
```

def __init__(self, session: AsyncSession, model_class: Type[ModelT], **kwargs):```

"""Initialize the repository."""
super().__init__(session, model_class, **kwargs)
``````

```
```

# Verify that the model class is tenant-aware
if not issubclass(model_class, TenantAwareModel):
    raise TypeError(
        f"Model class {model_class.__name__} is not tenant-aware. "
        f"Tenant-aware models must inherit from TenantAwareModel."
    )
```
``````

```
```

def _apply_tenant_filter(self, stmt: Select) -> Select:```

"""
Apply tenant filtering to a query.
``````

```
```

This method adds a tenant_id filter to the query based on the current tenant context.
"""
tenant_id = get_current_tenant_context()
if tenant_id:
    return stmt.where(self.model_class.tenant_id == tenant_id)
``````

```
```

# If no tenant is set in the context, return a query that will never match anything
# This is a safety measure to ensure that tenant isolation is maintained
return stmt.where(False)
```
```
```

All repository methods are overridden to apply tenant filtering:

```python
async def get(self, id: str) -> Optional[ModelT]:```

"""Get a model by ID, filtered by the current tenant."""
stmt = select(self.model_class).where(self.model_class.id == id)
stmt = self._apply_tenant_filter(stmt)
``````

```
```

result = await self.session.execute(stmt)
return result.scalars().first()
```

async def list(```

self, 
filters: Optional[Dict[str, Any]] = None,
order_by: Optional[List[str]] = None,
limit: Optional[int] = None,
offset: Optional[int] = None
```
) -> List[ModelT]:```

"""List models with optional filtering, ordering, and pagination."""
# Start with a basic select statement
stmt = select(self.model_class)
``````

```
```

# Apply tenant filtering
stmt = self._apply_tenant_filter(stmt)
``````

```
```

# Apply additional filters, ordering, pagination...
# ...
``````

```
```

result = await self.session.execute(stmt)
return list(result.scalars().all())
```
```

### Automatic Tenant ID Setting

The `TenantAwareRepository` also ensures that new records are created with the correct tenant ID:

```python
async def create(self, data: Dict[str, Any]) -> ModelT:```

"""
Create a new model in the current tenant's context.
``````

```
```

This method automatically sets the tenant_id based on the current tenant context.
"""
# Get current tenant ID
tenant_id = get_current_tenant_context()
if not tenant_id:```

raise ValueError(
    "Cannot create tenant-aware model without a tenant context. "
    "Use TenantContext or tenant_context to set the current tenant."
)
```
``````

```
```

# Set tenant_id in the data
data["tenant_id"] = tenant_id
``````

```
```

# Create the model
return await super().create(data)
```
```

### Tenant ID Protection

The repository prevents changing the tenant ID of an existing record:

```python
async def update(self, id: str, data: Dict[str, Any]) -> Optional[ModelT]:```

"""
Update an existing model, ensuring it belongs to the current tenant.
"""
# Prevent changing the tenant_id
if "tenant_id" in data:```

raise ValueError("Cannot change tenant_id of an existing model")
```
``````

```
```

# Use get() to verify the model exists and belongs to the current tenant
model = await self.get(id)
if not model:```

return None
```
``````

```
```

# Perform the update with tenant filtering for extra safety
# ...
```
```

## Usage Examples

### Setting Tenant Context

```python
# Using the context manager
async with tenant_context("tenant123"):```

# All operations here will be scoped to tenant "tenant123"
products = await product_repository.list()
```

# Using the TenantContext class
async with TenantContext("tenant456") as context:```

# All operations here will be scoped to tenant "tenant456"
customers = await customer_repository.list()
```
```

### Using Tenant-Aware Repositories

```python
from uno.core.multitenancy import TenantAwareRepository, tenant_context
from app.models import Product

class ProductRepository(TenantAwareRepository):```

def __init__(self, session):```

super().__init__(session, Product)
```
``````

```
```

# Custom methods that inherit tenant filtering
async def find_by_category(self, category: str):```

return await self.find_by(category=category)
```
```

# Usage
async def get_products_for_tenant(tenant_id: str):```

async with tenant_context(tenant_id):```

product_repo = ProductRepository(session)
```
    ```

# These queries will be automatically filtered by tenant_id
all_products = await product_repo.list()
electronics = await product_repo.find_by_category("electronics")
```
    ```

return all_products, electronics
```
```
```

### Middleware Integration

The tenant context is typically set by middleware at the beginning of request processing:

```python
class TenantMiddleware(BaseHTTPMiddleware):```

async def dispatch(self, request: Request, call_next: Callable) -> Response:```

# Extract tenant ID from request (header, subdomain, etc.)
tenant_id = extract_tenant_id(request)
```
    ```

if tenant_id:
    # Set tenant context for the duration of the request
    async with TenantContext(tenant_id):
        # Store tenant ID in request state for easy access
        request.state.tenant_id = tenant_id
        
        # Process the request
        return await call_next(request)
else:
    # No tenant identified, proceed without tenant context
    return await call_next(request)
```
```
```

## Security Considerations

1. **Context Initialization**: Always ensure that tenant context is properly initialized before performing database operations.
2. **Clear Context**: Always clear the tenant context when it's no longer needed to prevent context leakage.
3. **Verify Tenant Access**: Verify that the current user has access to the requested tenant before setting the tenant context.
4. **Validate Tenant ID**: Validate the tenant ID before setting it in the context to prevent spoofing.
5. **Security Boundaries**: Remember that context variables are a convenience mechanism, not a security boundary. The actual security is provided by PostgreSQL RLS.