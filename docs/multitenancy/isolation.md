# Tenant Isolation

This document describes the tenant isolation strategy implemented using PostgreSQL Row Level Security (RLS).

## Overview

Tenant isolation ensures that each tenant's data is completely separated from other tenants. The Uno framework implements tenant isolation at the database level using PostgreSQL's Row Level Security (RLS) feature.

RLS allows you to define policies that restrict which rows a user can see or modify in a table. These policies are enforced by the database itself, providing a strong security boundary.

## PostgreSQL Row Level Security

PostgreSQL RLS works by attaching policies to tables that filter the rows a user can access. For multi-tenancy, we use the `current_setting` function to retrieve the current tenant ID from a session variable and compare it to the `tenant_id` column in each table.

For example, for a `products` table, the RLS policies would look like:

```sql
-- Enable RLS on the table
ALTER TABLE public.products ENABLE ROW LEVEL SECURITY;

-- Policy for SELECT operations
CREATE POLICY select_tenant_rows ON public.products 
FOR SELECT USING (tenant_id = current_setting('app.current_tenant_id')::text);

-- Policy for INSERT operations
CREATE POLICY insert_tenant_rows ON public.products 
FOR INSERT WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::text);

-- Policy for UPDATE operations
CREATE POLICY update_tenant_rows ON public.products 
FOR UPDATE USING (tenant_id = current_setting('app.current_tenant_id')::text) 
WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::text);

-- Policy for DELETE operations
CREATE POLICY delete_tenant_rows ON public.products 
FOR DELETE USING (tenant_id = current_setting('app.current_tenant_id')::text);
```

These policies ensure that:
1. Users can only see rows where `tenant_id` matches the current setting
2. Users can only insert rows with the correct `tenant_id`
3. Users can only update rows that belong to their tenant, and cannot change the `tenant_id`
4. Users can only delete rows that belong to their tenant

## RLS Isolation Strategy

The `RLSIsolationStrategy` class provides methods for applying RLS policies to tenant-aware tables and managing tenant contexts in PostgreSQL.

```python
from uno.core.multitenancy import RLSIsolationStrategy

# Initialize the strategy
isolation_strategy = RLSIsolationStrategy(```

session=db_session,
schema="public",
tenant_column="tenant_id",
excluded_tables={"logs", "audit_trail"}
```
)

# Enable RLS for all tenant-aware tables
await isolation_strategy.enable_rls_for_all_tenant_tables()

# Enable RLS for a specific table
await isolation_strategy.enable_rls_for_table("products")

# Disable RLS for a specific table
await isolation_strategy.disable_rls_for_table("products")

# Create tenant context functions in the database
await isolation_strategy.create_tenant_context_functions()

# Run all necessary migrations to set up RLS
await isolation_strategy.ensure_tenant_migrations()
```

## Session Variables

The isolation strategy uses PostgreSQL session variables to track the current tenant context. Specifically, it uses the `app.current_tenant_id` variable.

The following SQL functions are created to manage tenant context:

```sql
-- Get the current tenant ID
CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS TEXT AS $$
BEGIN```

RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '');
```
END;
$$ LANGUAGE plpgsql;

-- Set the current tenant ID
CREATE OR REPLACE FUNCTION set_current_tenant_id(tenant_id TEXT)
RETURNS VOID AS $$
BEGIN```

PERFORM set_config('app.current_tenant_id', tenant_id, FALSE);
```
END;
$$ LANGUAGE plpgsql;

-- Clear the current tenant ID
CREATE OR REPLACE FUNCTION clear_current_tenant_id()
RETURNS VOID AS $$
BEGIN```

PERFORM set_config('app.current_tenant_id', '', FALSE);
```
END;
$$ LANGUAGE plpgsql;
```

These functions can be called from within SQL queries or from application code.

## Superuser Bypass

For administrative purposes, sometimes it's necessary to bypass tenant isolation. The `SuperuserBypassMixin` provides a way for database superusers to temporarily bypass RLS.

```python
from uno.core.multitenancy import SuperuserBypassMixin
from sqlalchemy import text

class AdminService(SuperuserBypassMixin):```

def __init__(self, session):```

super().__init__(session)
```
``````

```
```

async def get_all_products_across_tenants(self):```

async with self:  # Enter the bypass context
    # This query will bypass RLS and return all products from all tenants
    result = await self.session.execute(text("SELECT * FROM products"))
    return result.fetchall()
```
```
```

A bypass function is created in the database to facilitate this:

```sql
CREATE OR REPLACE FUNCTION bypass_rls()
RETURNS VOID AS $$
BEGIN```

-- Only superusers can execute this function
IF NOT (SELECT usesuper FROM pg_user WHERE usename = current_user) THEN```

RAISE EXCEPTION 'Only superusers can bypass RLS';
```
END IF;
``````

```
```

-- Temporary table for the session
CREATE TEMP TABLE IF NOT EXISTS _rls_bypass (bypass BOOLEAN);
TRUNCATE TABLE _rls_bypass;
INSERT INTO _rls_bypass VALUES (TRUE);
```
END;
$$ LANGUAGE plpgsql;
```

## Admin Tenant Switching

For cross-tenant operations, the `AdminTenantMixin` provides methods for switching between tenant contexts.

```python
from uno.core.multitenancy import AdminTenantMixin

class TenantAdminService(AdminTenantMixin):```

def __init__(self, session):```

super().__init__(session)
```
``````

```
```

async def count_products_by_tenant(self, tenant_ids):```

results = {}
```
    ```

for tenant_id in tenant_ids:
    # Switch to the tenant's context
    await self.switch_tenant(tenant_id)
    
    # Run a query in the tenant's context
    result = await self.session.execute(text("SELECT COUNT(*) FROM products"))
    count = result.scalar()
    results[tenant_id] = count
    
    # Optional: restore the original tenant context when done
    await self.restore_tenant()
```
    ```

return results
```
```
```

## Security Considerations

1. **Database Users**: Ensure that application database users do not have the `BYPASSRLS` permission.
2. **Superuser Access**: Restrict superuser access to trusted administrators only.
3. **Session Variables**: Be cautious when writing code that manipulates PostgreSQL session variables, as they could potentially bypass tenant isolation if misused.
4. **SQL Injection**: Be vigilant about SQL injection vulnerabilities, as they could potentially alter the tenant context.
5. **Custom Queries**: When writing raw SQL queries, ensure they respect tenant isolation.

## Best Practices

1. **Always Set Tenant Context**: Ensure that tenant context is set before performing any database operations.
2. **Test Isolation**: Write tests to verify that tenant isolation is working as expected.
3. **Apply RLS to All Tables**: Make sure all tenant-aware tables have RLS enabled.
4. **Audit Bypass Usage**: Monitor and audit any usage of RLS bypass functionality.
5. **Parametrized Queries**: Use parametrized queries to prevent SQL injection vulnerabilities.
6. **Restrict Superuser Access**: Limit superuser access to only trusted administrators.