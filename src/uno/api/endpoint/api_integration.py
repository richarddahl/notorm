"""
API integration for the Unified Endpoint Framework (src/uno/api/endpoint).

This module provides a unified function to register all example endpoints from the framework
with a FastAPI app or router, following the standard integration pattern.
"""

from typing import Any, Dict, Optional, Union
from fastapi import FastAPI, APIRouter

from .examples.crud_example import create_crud_example_app
from .examples.cqrs_example import create_cqrs_example_app
from .examples.filter_example import create_filter_example_app
from .examples.openapi_example import create_openapi_example_app


def register_unified_example_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1/examples",
    dependencies: Optional[list[Any]] = None,
    include_auth: bool = True,
) -> dict[str, Any]:
    """
    Register all example endpoints from the unified endpoint framework.

    Args:
        app_or_router: FastAPI app or APIRouter
        path_prefix: API version prefix for examples
        dependencies: Optional list of dependencies (unused, for compatibility)
        include_auth: Whether to include authentication dependencies (unused here)
    """
    # Register each example app as a router under the examples prefix
    # Each example factory returns a FastAPI app, so we mount them as sub-applications
    app_or_router.mount(f"{path_prefix}/crud", create_crud_example_app())
    app_or_router.mount(f"{path_prefix}/cqrs", create_cqrs_example_app())
    app_or_router.mount(f"{path_prefix}/filter", create_filter_example_app())
    app_or_router.mount(f"{path_prefix}/openapi", create_openapi_example_app())
    return {
        "crud": "crud_example",
        "cqrs": "cqrs_example",
        "filter": "filter_example",
        "openapi": "openapi_example",
    }
