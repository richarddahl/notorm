"""
Tenant context management.

This module provides utilities for managing tenant context during request processing,
ensuring that all operations are scoped to the correct tenant.
"""

import asyncio
import contextvars
from typing import Optional, Any
from contextlib import asynccontextmanager

# Create a context variable to store the current tenant ID
_tenant_context = contextvars.ContextVar("tenant_context", default=None)


def get_current_tenant_context() -> Optional[str]:
    """
    Get the ID of the tenant in the current context.
    
    Returns:
        The tenant ID or None if no tenant is set in the current context
    """
    return _tenant_context.get()


def set_current_tenant_context(tenant_id: Optional[str]) -> None:
    """
    Set the tenant ID for the current context.
    
    Args:
        tenant_id: The tenant ID to set, or None to clear the tenant context
    """
    _tenant_context.set(tenant_id)


def clear_tenant_context() -> None:
    """Clear the tenant context for the current execution."""
    _tenant_context.set(None)


@asynccontextmanager
async def tenant_context(tenant_id: Optional[str]):
    """
    Context manager for tenant context.
    
    This creates a context where all operations are scoped to the specified tenant.
    The tenant context is cleared when the context is exited.
    
    Args:
        tenant_id: The tenant ID to set in the context, or None for global operations
    
    Example:
        async with tenant_context("tenant123"):
            # All operations here will be scoped to tenant "tenant123"
            await repository.find_all()
    """
    # Save the current context
    previous_context = get_current_tenant_context()
    
    # Set the new context
    set_current_tenant_context(tenant_id)
    
    # Set PostgreSQL session variable if we have a database connection
    try:
        conn = await get_database_connection()
        if conn:
            await conn.execute(
                "SELECT set_config('app.current_tenant_id', $1, true)",
                [tenant_id or '']
            )
    except Exception:
        # If there's an error getting the connection or setting the variable,
        # just continue without setting the PostgreSQL session variable
        pass
    
    try:
        # Yield control back to the caller
        yield
    finally:
        # Restore the previous context
        set_current_tenant_context(previous_context)
        
        # Restore PostgreSQL session variable
        try:
            conn = await get_database_connection()
            if conn:
                await conn.execute(
                    "SELECT set_config('app.current_tenant_id', $1, true)",
                    [previous_context or '']
                )
        except Exception:
            # If there's an error restoring the PostgreSQL session variable,
            # just continue without restoring it
            pass


class TenantContext:
    """
    Maintains the current tenant context.
    
    This class provides an async context manager for tenant context management.
    """
    
    def __init__(self, tenant_id: Optional[str] = None):
        """
        Initialize a tenant context.
        
        Args:
            tenant_id: The tenant ID to set in the context, or None for global operations
        """
        self.tenant_id = tenant_id
        self._previous_context = None
        self._token = None
    
    async def __aenter__(self):
        """Set this context as the current tenant context."""
        self._previous_context = get_current_tenant_context()
        self._token = _tenant_context.set(self.tenant_id)
        
        # Set PostgreSQL session variable if we have a database connection
        try:
            conn = await get_database_connection()
            if conn:
                await conn.execute(
                    "SELECT set_config('app.current_tenant_id', $1, true)",
                    [self.tenant_id or '']
                )
        except Exception:
            # If there's an error getting the connection or setting the variable,
            # just continue without setting the PostgreSQL session variable
            pass
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Restore the previous tenant context."""
        _tenant_context.reset(self._token)
        
        # Restore PostgreSQL session variable
        try:
            conn = await get_database_connection()
            if conn:
                await conn.execute(
                    "SELECT set_config('app.current_tenant_id', $1, true)",
                    [self._previous_context or '']
                )
        except Exception:
            # If there's an error restoring the PostgreSQL session variable,
            # just continue without restoring it
            pass


async def get_database_connection() -> Optional[Any]:
    """
    Get the current database connection if available.
    
    This is a stub function that should be replaced with the actual implementation
    that gets the current database connection from your connection management system.
    
    Returns:
        The current database connection, or None if not available
    """
    # In a real implementation, this would get the current database connection
    # from your connection pool or connection manager.
    #
    # For now, we return None to indicate that no connection is available.
    # This will be implemented properly when integrated with the database system.
    from uno.database import get_current_connection
    
    try:
        return await get_current_connection()
    except:
        return None