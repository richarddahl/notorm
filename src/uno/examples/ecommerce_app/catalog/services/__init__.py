"""
Service layer for the catalog context.

This module makes the catalog services available to other layers.
"""

from uno.examples.ecommerce_app.catalog.services.product_service import (
    ProductService,
    CategoryService,
    ProductCreateCommand,
    ProductUpdateCommand,
    ProductListQuery,
    ProductDetailQuery,
    CategoryCreateCommand,
    CategoryUpdateCommand,
    CategoryListQuery,
)

__all__ = [
    "ProductService",
    "CategoryService",
    "ProductCreateCommand",
    "ProductUpdateCommand",
    "ProductListQuery",
    "ProductDetailQuery",
    "CategoryCreateCommand",
    "CategoryUpdateCommand",
    "CategoryListQuery",
]