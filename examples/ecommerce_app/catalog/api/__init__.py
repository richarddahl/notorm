"""
API layer for the catalog context.

This module exposes the catalog context functionality via REST API endpoints.
"""

from uno.examples.ecommerce_app.catalog.api.product_endpoints import router as product_router
from uno.examples.ecommerce_app.catalog.api.category_endpoints import router as category_router

__all__ = ["product_router", "category_router"]