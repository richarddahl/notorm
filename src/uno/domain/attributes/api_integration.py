"""
API integration for the Attributes module (domain layer).

This module provides a unified function to register all attribute-related endpoints
with a FastAPI app or router, following the standard integration pattern.
"""

from typing import Any, Dict, List, Optional, Union
from fastapi import FastAPI, APIRouter

from uno.domain.domain_endpoints import attribute_router, attribute_type_router


def register_attributes_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: Optional[list[Any]] = None,
    include_auth: bool = True,
) -> Dict[str, Any]:
    """
    Register all attribute-related API endpoints (attributes and attribute types).

    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: API version prefix
        dependencies: Optional list of dependencies (unused, for compatibility)
        include_auth: Whether to include authentication dependencies (unused here)
    """
    # Register routers with standardized prefixes
    app_or_router.include_router(attribute_router, prefix=f"{path_prefix}/attributes")
    app_or_router.include_router(
        attribute_type_router, prefix=f"{path_prefix}/attribute-types"
    )
    return {
        "attributes": attribute_router,
        "attribute_types": attribute_type_router,
    }
