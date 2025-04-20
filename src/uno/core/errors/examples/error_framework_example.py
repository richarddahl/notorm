"""
Example demonstrating the error framework.

This module shows how to use the error framework for standardized error handling
across different components of an application.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel, Field

from uno.core.errors.framework import (
    ErrorCatalog,
    ValidationError,
    NotFoundError,
    DatabaseError,
    AuthorizationError,
    register_error,
    create_error,
    log_error,
    get_error_context,
    ErrorCategory,
    ErrorSeverity,
)
from uno.core.errors.result import Result


# --------------------------------------------------------------------------
# 1. Register custom errors in the catalog
# --------------------------------------------------------------------------

# Register application-specific errors
register_error(
    code="PRODUCT_OUT_OF_STOCK",
    message_template="Product {product_id} is out of stock. Available: {available}, requested: {requested}",
    category=ErrorCategory.BUSINESS,
    severity=ErrorSeverity.WARNING,
    http_status_code=400,
    help_text="Check product availability before placing an order.",
)

register_error(
    code="ORDER_ALREADY_SHIPPED",
    message_template="Order {order_id} has already been shipped on {ship_date} and cannot be modified",
    category=ErrorCategory.BUSINESS,
    severity=ErrorSeverity.ERROR,
    http_status_code=422,
    help_text="Only pending orders can be modified.",
)


# --------------------------------------------------------------------------
# 2. Domain layer - Business logic and entities
# --------------------------------------------------------------------------


class Product:
    """Example product entity."""

    def __init__(self, id: str, name: str, stock: int):
        self.id = id
        self.name = name
        self.stock = stock

    def check_stock(self, requested: int) -> Result[bool]:
        """Check if there's enough stock for the requested quantity."""
        if requested <= 0:
            return Failure(
                ValidationError(
                    "Requested quantity must be positive",
                    field="requested",
                )
            )

        if requested <= self.stock:
            return Success(True)

        # Use the catalog to create a standardized error
        return ErrorCatalog.to_result(
            code="PRODUCT_OUT_OF_STOCK",
            params={
                "product_id": self.id,
                "available": self.stock,
                "requested": requested,
            },
        )


class Order:
    """Example order entity."""

    def __init__(
        self,
        id: str,
        customer_id: str,
        products: Dict[str, int] = None,
        status: str = "pending",
        ship_date: Optional[datetime] = None,
    ):
        self.id = id
        self.customer_id = customer_id
        self.products = products or {}
        self.status = status
        self.ship_date = ship_date

    def add_product(self, product_id: str, quantity: int) -> Result[bool]:
        """Add a product to the order."""
        if self.status != "pending":
            return ErrorCatalog.to_result(
                code="ORDER_ALREADY_SHIPPED",
                params={
                    "order_id": self.id,
                    "ship_date": (
                        self.ship_date.isoformat() if self.ship_date else "N/A"
                    ),
                },
            )

        if quantity <= 0:
            return Failure(
                ValidationError(
                    "Quantity must be positive",
                    field="quantity",
                )
            )

        # Add or update product quantity
        self.products[product_id] = self.products.get(product_id, 0) + quantity
        return Success(True)


# --------------------------------------------------------------------------
# 3. Application layer - Services and use cases
# --------------------------------------------------------------------------


class ProductService:
    """Example product service."""

    def __init__(self):
        # Mock database
        self.products = {
            "p1": Product("p1", "Laptop", 10),
            "p2": Product("p2", "Phone", 20),
            "p3": Product("p3", "Tablet", 0),  # Out of stock
        }

    async def get_product(self, product_id: str) -> Result[Product]:
        """Get a product by ID."""
        # Simulate database operation that might fail
        try:
            if product_id not in self.products:
                return Failure(
                    NotFoundError(
                        f"Product with ID {product_id} not found",
                        code="PRODUCT_NOT_FOUND",
                    )
                )
            return Success(self.products[product_id])
        except Exception as e:
            return Failure(
                DatabaseError(
                    f"Database error while fetching product: {str(e)}",
                    code="DATABASE_ERROR",
                )
            )

    async def check_stock(self, product_id: str, quantity: int) -> Result[bool]:
        """Check if a product has enough stock."""
        # Get the product
        product_result = await self.get_product(product_id)
        if not isinstance(product_result, Success):
            return product_result

        product = product_result.value
        return product.check_stock(quantity)


class OrderService:
    """Example order service."""

    def __init__(self, product_service: ProductService):
        self.product_service = product_service
        # Mock database
        self.orders = {
            "o1": Order("o1", "c1", {"p1": 1}),
            "o2": Order("o2", "c2", {"p2": 2}, "shipped", datetime.now()),
        }

    async def get_order(self, order_id: str) -> Result[Order]:
        """Get an order by ID."""
        try:
            if order_id not in self.orders:
                return Failure(
                    NotFoundError(
                        f"Order with ID {order_id} not found",
                        code="ORDER_NOT_FOUND",
                    )
                )
            return Success(self.orders[order_id])
        except Exception as e:
            return Failure(
                DatabaseError(
                    f"Database error while fetching order: {str(e)}",
                    code="DATABASE_ERROR",
                )
            )

    async def add_product_to_order(
        self,
        order_id: str,
        product_id: str,
        quantity: int,
        user_id: str,
    ) -> Result[Order]:
        """Add a product to an order."""
        # Check authorization
        order_result = await self.get_order(order_id)
        if not isinstance(order_result, Success):
            return order_result

        order = order_result.value
        if order.customer_id != user_id:
            return Failure(
                AuthorizationError(
                    f"User {user_id} is not authorized to modify order {order_id}",
                    code="UNAUTHORIZED_ORDER_MODIFICATION",
                )
            )

        # Check stock
        stock_result = await self.product_service.check_stock(product_id, quantity)
        if not isinstance(stock_result, Success):
            return stock_result

        # Add product to order
        add_result = order.add_product(product_id, quantity)
        if not isinstance(add_result, Success):
            return add_result

        return Success(order)


# --------------------------------------------------------------------------
# 4. Interface layer - API endpoints
# --------------------------------------------------------------------------


# API Models
class AddProductRequest(BaseModel):
    """Request to add a product to an order."""

    product_id: str = Field(..., description="Product ID to add")
    quantity: int = Field(..., gt=0, description="Quantity to add")


class OrderResponse(BaseModel):
    """Order response model."""

    id: str = Field(..., description="Order ID")
    customer_id: str = Field(..., description="Customer ID")
    products: Dict[str, int] = Field(..., description="Product quantities")
    status: str = Field(..., description="Order status")
    ship_date: Optional[datetime] = Field(None, description="Ship date")


# Set up FastAPI application
app = FastAPI(title="Error Framework Example")

# Create services
product_service = ProductService()
order_service = OrderService(product_service)


# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """Middleware for handling errors and adding context."""
    try:
        # Create error context with request information
        context = get_error_context()
        context.request_id = request.headers.get("X-Request-ID")
        context.path = request.url.path
        context.method = request.method
        context.user_id = request.headers.get("X-User-ID")

        # Process the request
        return await call_next(request)
    except Exception as e:
        # Log the error with context
        error_log = log_error(e, include_traceback=True, context=context)

        # Return error response
        if hasattr(e, "status_code"):
            status_code = e.status_code
        else:
            status_code = 500

        return Response(
            content=f'{{"error": "{str(e)}", "code": "{getattr(e, "code", "INTERNAL_ERROR")}"}}',
            status_code=status_code,
            media_type="application/json",
        )


# API endpoints
@app.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get a product by ID."""
    result = await product_service.get_product(product_id)
    if isinstance(result, Success):
        return result.value.__dict__
    else:
        # The error handling middleware will catch and process the error
        error = result.error
        raise error


@app.get("/orders/{order_id}")
async def get_order(order_id: str):
    """Get an order by ID."""
    result = await order_service.get_order(order_id)
    if isinstance(result, Success):
        return OrderResponse(
            id=result.value.id,
            customer_id=result.value.customer_id,
            products=result.value.products,
            status=result.value.status,
            ship_date=result.value.ship_date,
        )
    else:
        # The error handling middleware will catch and process the error
        error = result.error
        raise error


@app.post("/orders/{order_id}/products")
async def add_product_to_order(
    order_id: str,
    data: AddProductRequest,
    user_id: str | None = None,
):
    """Add a product to an order."""
    if not user_id:
        raise AuthorizationError(
            "User ID is required",
            code="MISSING_USER_ID",
        )

    result = await order_service.add_product_to_order(
        order_id,
        data.product_id,
        data.quantity,
        user_id,
    )

    if isinstance(result, Success):
        return OrderResponse(
            id=result.value.id,
            customer_id=result.value.customer_id,
            products=result.value.products,
            status=result.value.status,
            ship_date=result.value.ship_date,
        )
    else:
        # The error handling middleware will catch and process the error
        error = result.error
        raise error


# --------------------------------------------------------------------------
# 5. Example Usage
# --------------------------------------------------------------------------


async def run_examples():
    """Run some example scenarios to demonstrate the error framework."""
    print("\n===== EXAMPLE 1: SUCCESSFUL SCENARIO =====")
    # Get a product (success case)
    result = await product_service.get_product("p1")
    if isinstance(result, Success):
        print(f"Got product: {result.value.name}, stock: {result.value.stock}")
    else:
        print(f"Error: {result.error}")

    # Check stock (success case)
    result = await product_service.check_stock("p1", 5)
    if isinstance(result, Success):
        print("Stock check passed successfully")
    else:
        print(f"Error: {result.error}")

    # Add product to order (success case)
    result = await order_service.add_product_to_order("o1", "p1", 5, "c1")
    if isinstance(result, Success):
        print(
            f"Added product to order: {result.value.id}, new quantities: {result.value.products}"
        )
    else:
        print(f"Error: {result.error}")

    print("\n===== EXAMPLE 2: PRODUCT NOT FOUND =====")
    # Get a non-existent product
    result = await product_service.get_product("non-existent")
    if isinstance(result, Success):
        print(f"Got product: {result.value.name}")
    else:
        # Log the error
        log_error(result.error)
        print(f"Error: {result.error}, code: {result.error.code}")

    print("\n===== EXAMPLE 3: PRODUCT OUT OF STOCK =====")
    # Check stock with insufficient quantity
    result = await product_service.check_stock("p1", 100)
    if isinstance(result, Success):
        print("Stock check passed successfully")
    else:
        # Log the error
        log_error(result.error)
        print(f"Error: {result.error}, code: {result.error.code}")

    print("\n===== EXAMPLE 4: UNAUTHORIZED ACCESS =====")
    # Try to modify an order as a different user
    result = await order_service.add_product_to_order("o1", "p1", 1, "wrong-user")
    if isinstance(result, Success):
        print(f"Added product to order: {result.value.id}")
    else:
        # Log the error
        log_error(result.error)
        print(f"Error: {result.error}, code: {result.error.code}")

    print("\n===== EXAMPLE 5: ORDER ALREADY SHIPPED =====")
    # Try to modify a shipped order
    result = await order_service.add_product_to_order("o2", "p1", 1, "c2")
    if isinstance(result, Success):
        print(f"Added product to order: {result.value.id}")
    else:
        # Log the error
        log_error(result.error)
        print(f"Error: {result.error}, code: {result.error.code}")


# Entry point for the examples
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run the examples
    asyncio.run(run_examples())

    print("\nTo run the API examples, use the following commands:")
    print("uvicorn error_framework_example:app --reload")
    print("Then visit http://localhost:8000/docs in your browser")
    print("")
    print("Example API requests:")
    print("GET /products/p1 - Success")
    print("GET /products/p9 - Not Found")
    print("GET /orders/o1 - Success")
    print("GET /orders/o9 - Not Found")
    print("POST /orders/o1/products - Add product (need user_id header)")
    print("POST /orders/o2/products - Order already shipped")
