"""
API layer for the e-commerce application.

This package contains FastAPI endpoints and related components
for the e-commerce application's API.
"""

from examples.ecommerce.api.user import router as user_router
from examples.ecommerce.api.product import router as product_router
from examples.ecommerce.api.order import router as order_router