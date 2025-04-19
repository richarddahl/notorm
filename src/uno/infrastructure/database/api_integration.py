"""
API integration for the Database module (infrastructure layer).

This module provides a unified function to register all database-related endpoints
with a FastAPI app or router, following the standard integration pattern.
"""

from fastapi import FastAPI, APIRouter
from typing import Any, Optional, Union

from .domain_endpoints import router as database_router

def register_database_endpoints(
    app_or_router: FastAPI | APIRouter,
    path_prefix: str = "/api/v1/database",
    dependencies: Optional[list[Any]] = None,
    include_auth: bool = True,
) -> dict[str, Any]:
    """
    Register all database-related API endpoints.
    
    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: API version prefix
        dependencies: Optional list of dependencies (unused, for compatibility)
        include_auth: Whether to include authentication dependencies (unused here)
    """
    # Register the router with standardized prefix
    app_or_router.include_router(database_router, prefix=path_prefix)
    return {"database": database_router}
