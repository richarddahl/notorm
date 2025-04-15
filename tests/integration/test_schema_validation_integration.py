"""
Integration tests for schema validation with endpoints and database.

This module tests the integration of UnoSchema validation with UnoEndpoints
and database operations, ensuring proper validation throughout the API pipeline.
"""

import pytest
import json
import re
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple, Type

from fastapi import FastAPI, status, Depends
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field, field_validator, model_validator, ValidationError as PydanticValidationError

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchema, UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError
from uno.api.endpoint import UnoEndpoint, UnoRouter
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.database.db import FilterParam


# ===== TEST MODELS =====

class ProductModel(UnoModel):
    """Database model for products with complex validation."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    min_order_quantity: Mapped[int] = mapped_column(nullable=True)
    max_order_quantity: Mapped[int] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    tags: Mapped[str] = mapped_column(nullable=True)  # Comma-separated
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class OrderItemModel(UnoModel):
    """Database model for order items."""
    
    __tablename__ = "order_items"
    
    order_id: Mapped[str] = mapped_column(nullable=False)
    product_id: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)


class OrderModel(UnoModel):
    """Database model for orders."""
    
    __tablename__ = "orders"
    
    customer_name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    customer_email: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    total_amount: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


# ===== BUSINESS OBJECTS WITH VALIDATION =====

class Product(UnoObj[ProductModel]):
    """Product business object with complex validation rules."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(
            exclude_fields=set()  # Include all fields
        ),
        "edit_schema": UnoSchemaConfig(
            exclude_fields={"created_at", "updated_at"}
        ),
        "list_schema": UnoSchemaConfig(
            include_fields={"id", "name", "price", "category", "inventory_count", "is_active"}
        ),
        "create_schema": UnoSchemaConfig(
            exclude_fields={"id", "created_at", "updated_at"}
        )
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for products."""
        # Call parent validation first
        context = super().validate(schema_name)
        
        # Name validation
        if hasattr(self, "name") and self.name is not None:
            if len(self.name) < 3:
                context.add_error(
                    field="name",
                    message="Name must be at least 3 characters long",
                    error_code="NAME_TOO_SHORT"
                )
            
            if len(self.name) > 255:
                context.add_error(
                    field="name",
                    message="Name must be at most 255 characters long",
                    error_code="NAME_TOO_LONG"
                )
        
        # Price validation
        if hasattr(self, "price") and self.price is not None:
            if self.price <= Decimal("0.00"):
                context.add_error(
                    field="price",
                    message="Price must be greater than zero",
                    error_code="INVALID_PRICE"
                )
        
        # SKU validation - must follow pattern ABC-12345
        if hasattr(self, "sku") and self.sku:
            sku_pattern = r"^[A-Z]{3}-\d{5}$"
            if not re.match(sku_pattern, self.sku):
                context.add_error(
                    field="sku",
                    message="SKU must follow pattern ABC-12345 (3 uppercase letters, dash, 5 digits)",
                    error_code="INVALID_SKU_FORMAT"
                )
        
        # Category validation
        if hasattr(self, "category") and self.category:
            valid_categories = ["Electronics", "Clothing", "Books", "Home", "Toys"]
            if self.category not in valid_categories:
                context.add_error(
                    field="category",
                    message=f"Invalid category. Must be one of {', '.join(valid_categories)}",
                    error_code="INVALID_CATEGORY"
                )
        
        # Min/max order quantities validation
        if (hasattr(self, "min_order_quantity") and self.min_order_quantity is not None and
            hasattr(self, "max_order_quantity") and self.max_order_quantity is not None):
            if self.min_order_quantity > self.max_order_quantity:
                context.add_error(
                    field="max_order_quantity",
                    message="Maximum order quantity must be greater than or equal to minimum order quantity",
                    error_code="INVALID_ORDER_QUANTITIES"
                )
        
        # Tags validation
        if hasattr(self, "tags") and self.tags:
            tags = self.tags.split(",")
            if len(tags) > 10:
                context.add_error(
                    field="tags",
                    message="Too many tags. Maximum is 10",
                    error_code="TOO_MANY_TAGS"
                )
            
            for tag in tags:
                if not tag.strip():
                    context.add_error(
                        field="tags",
                        message="Empty tags are not allowed",
                        error_code="EMPTY_TAG"
                    )
                elif not all(c.isalnum() or c == '-' for c in tag.strip()):
                    context.add_error(
                        field="tags",
                        message=f"Tag '{tag.strip()}' contains invalid characters. Only alphanumeric and hyphen are allowed",
                        error_code="INVALID_TAG_FORMAT"
                    )
        
        return context
    
    # Example business method with validation
    async def reserve_inventory(self, quantity: int) -> bool:
        """Reserve inventory for an order with validation."""
        # Check quantity
        if quantity <= 0:
            raise UnoError(
                f"Cannot reserve non-positive quantity: {quantity}",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity
            )
        
        # Check minimum order quantity
        if self.min_order_quantity is not None and quantity < self.min_order_quantity:
            raise UnoError(
                f"Order quantity below minimum: {quantity} < {self.min_order_quantity}",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity,
                min_quantity=self.min_order_quantity
            )
        
        # Check maximum order quantity
        if self.max_order_quantity is not None and quantity > self.max_order_quantity:
            raise UnoError(
                f"Order quantity exceeds maximum: {quantity} > {self.max_order_quantity}",
                ErrorCode.BUSINESS_RULE,
                quantity=quantity,
                max_quantity=self.max_order_quantity
            )
        
        # Check inventory
        if quantity > self.inventory_count:
            raise UnoError(
                f"Insufficient inventory: requested {quantity}, available {self.inventory_count}",
                ErrorCode.BUSINESS_RULE,
                requested_quantity=quantity,
                available_quantity=self.inventory_count
            )
        
        # Reserve inventory
        self.inventory_count -= quantity
        await self.save()
        return True


class OrderItem(UnoObj[OrderItemModel]):
    """Order item business object with validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "order_id", "product_id", "quantity", "unit_price"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for order items."""
        context = super().validate(schema_name)
        
        # Quantity validation
        if hasattr(self, "quantity") and self.quantity is not None:
            if self.quantity <= 0:
                context.add_error(
                    field="quantity",
                    message="Quantity must be greater than zero",
                    error_code="INVALID_QUANTITY"
                )
        
        # Unit price validation
        if hasattr(self, "unit_price") and self.unit_price is not None:
            if self.unit_price <= Decimal("0.00"):
                context.add_error(
                    field="unit_price",
                    message="Unit price must be greater than zero",
                    error_code="INVALID_UNIT_PRICE"
                )
        
        return context


class Order(UnoObj[OrderModel]):
    """Order business object with validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "customer_name", "total_amount", "status"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for orders."""
        context = super().validate(schema_name)
        
        # Customer name validation
        if hasattr(self, "customer_name") and self.customer_name is not None:
            if len(self.customer_name) < 3:
                context.add_error(
                    field="customer_name",
                    message="Customer name must be at least 3 characters long",
                    error_code="NAME_TOO_SHORT"
                )
        
        # Email validation
        if hasattr(self, "customer_email") and self.customer_email is not None:
            email_pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
            if not re.match(email_pattern, self.customer_email):
                context.add_error(
                    field="customer_email",
                    message="Invalid email format",
                    error_code="INVALID_EMAIL_FORMAT"
                )
        
        # Total amount validation
        if hasattr(self, "total_amount") and self.total_amount is not None:
            if self.total_amount <= Decimal("0.00"):
                context.add_error(
                    field="total_amount",
                    message="Total amount must be greater than zero",
                    error_code="INVALID_TOTAL_AMOUNT"
                )
        
        # Status validation
        if hasattr(self, "status") and self.status is not None:
            valid_statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
            if self.status not in valid_statuses:
                context.add_error(
                    field="status",
                    message=f"Invalid status. Must be one of {', '.join(valid_statuses)}",
                    error_code="INVALID_STATUS"
                )
        
        return context


# ===== MOCK DATABASE FUNCTIONS =====

# In-memory mock database
products_db = {}
order_items_db = {}
orders_db = {}

async def mock_get_product(id):
    """Mock Product.get method."""
    return products_db.get(id)

async def mock_filter_products(filters=None, **kwargs):
    """Mock Product.filter method."""
    if not filters:
        return list(products_db.values())
    
    # Simple filtering
    if isinstance(filters, dict):
        results = []
        for product in products_db.values():
            match = True
            for key, value in filters.items():
                if key == "category":
                    if getattr(product, key, None) != value:
                        match = False
                        break
                elif key == "price__gte":
                    if getattr(product, "price", None) < value:
                        match = False
                        break
                elif key == "price__lte":
                    if getattr(product, "price", None) > value:
                        match = False
                        break
                elif key == "is_active":
                    if getattr(product, key, None) != value:
                        match = False
                        break
            
            if match:
                results.append(product)
        
        return results
    
    return list(products_db.values())

async def mock_save_product(self):
    """Mock Product.save method."""
    products_db[self.id] = self
    return self

async def mock_delete_product(self):
    """Mock Product.delete method."""
    if self.id in products_db:
        del products_db[self.id]
    return True

async def mock_get_order_item(id):
    """Mock OrderItem.get method."""
    return order_items_db.get(id)

async def mock_filter_order_items(filters=None, **kwargs):
    """Mock OrderItem.filter method."""
    if not filters:
        return list(order_items_db.values())
    
    # Simple filtering
    if isinstance(filters, dict):
        results = []
        for item in order_items_db.values():
            match = True
            for key, value in filters.items():
                if key == "order_id":
                    if getattr(item, key, None) != value:
                        match = False
                        break
            
            if match:
                results.append(item)
        
        return results
    
    return list(order_items_db.values())

async def mock_save_order_item(self):
    """Mock OrderItem.save method."""
    order_items_db[self.id] = self
    return self

async def mock_get_order(id):
    """Mock Order.get method."""
    return orders_db.get(id)

async def mock_filter_orders(filters=None, **kwargs):
    """Mock Order.filter method."""
    if not filters:
        return list(orders_db.values())
    
    # Simple filtering
    if isinstance(filters, dict):
        results = []
        for order in orders_db.values():
            match = True
            for key, value in filters.items():
                if key == "status":
                    if getattr(order, key, None) != value:
                        match = False
                        break
                elif key == "customer_name":
                    if getattr(order, key, None) != value:
                        match = False
                        break
            
            if match:
                results.append(order)
        
        return results
    
    return list(orders_db.values())

async def mock_save_order(self):
    """Mock Order.save method."""
    orders_db[self.id] = self
    return self


# ===== API ENDPOINT SETUP =====

def setup_mock_methods():
    """Set up mock methods for testing."""
    # Product methods
    Product.get = mock_get_product
    Product.filter = mock_filter_products
    Product.save = mock_save_product
    Product.delete = mock_delete_product
    
    # OrderItem methods
    OrderItem.get = mock_get_order_item
    OrderItem.filter = mock_filter_order_items
    OrderItem.save = mock_save_order_item
    
    # Order methods
    Order.get = mock_get_order
    Order.filter = mock_filter_orders
    Order.save = mock_save_order


def create_test_app():
    """Create a test FastAPI application with endpoints."""
    # Create the app
    app = FastAPI()
    
    # Create the endpoint factory
    factory = UnoEndpointFactory()
    
    # Create endpoints for Product
    product_endpoints = factory.create_endpoints(
        app=app,
        model_obj=Product,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        endpoint_tags=["Products"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Create endpoints for Order
    order_endpoints = factory.create_endpoints(
        app=app,
        model_obj=Order,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        endpoint_tags=["Orders"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Create endpoints for OrderItem
    order_item_endpoints = factory.create_endpoints(
        app=app,
        model_obj=OrderItem,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        endpoint_tags=["OrderItems"],
        path_prefix="/api/v1",
        include_in_schema=True
    )
    
    # Add a custom endpoint for product inventory reservation
    @app.post("/api/v1/products/{product_id}/reserve", tags=["Products"])
    async def reserve_inventory(product_id: str, quantity: int):
        """Reserve product inventory."""
        try:
            product = await Product.get(product_id)
            if not product:
                return {
                    "status": "error",
                    "message": f"Product not found: {product_id}",
                    "code": ErrorCode.RESOURCE_NOT_FOUND
                }
            
            await product.reserve_inventory(quantity)
            
            return {
                "status": "success",
                "data": {
                    "product_id": product_id,
                    "reserved_quantity": quantity,
                    "remaining_inventory": product.inventory_count
                }
            }
        except UnoError as e:
            return {
                "status": "error",
                "message": str(e),
                "code": e.error_code,
                "details": e.get_details()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    # Add a custom endpoint for creating an order with items
    @app.post("/api/v1/orders/complete", tags=["Orders"])
    async def create_complete_order(data: dict):
        """Create an order with items in a single operation."""
        try:
            # Extract order data
            order_data = {
                "customer_name": data.get("customer_name"),
                "customer_email": data.get("customer_email"),
                "total_amount": Decimal("0.00"),  # Will be calculated
                "status": "pending"
            }
            
            # Create new order
            order = Order(**order_data)
            
            # Validate order
            validation_context = order.validate("edit_schema")
            if validation_context.has_errors():
                return {
                    "status": "error",
                    "message": "Invalid order data",
                    "errors": validation_context.errors,
                    "code": ErrorCode.VALIDATION_ERROR
                }
            
            # Get order items
            items_data = data.get("items", [])
            order_items = []
            total_amount = Decimal("0.00")
            
            # Process each item
            for item_data in items_data:
                # Get product
                product_id = item_data.get("product_id")
                product = await Product.get(product_id)
                
                if not product:
                    return {
                        "status": "error",
                        "message": f"Product not found: {product_id}",
                        "code": ErrorCode.RESOURCE_NOT_FOUND
                    }
                
                # Get quantity
                quantity = item_data.get("quantity", 0)
                
                # Reserve inventory
                try:
                    await product.reserve_inventory(quantity)
                except UnoError as e:
                    # Unreserve any already reserved inventory
                    for order_item in order_items:
                        product = await Product.get(order_item.product_id)
                        if product:
                            product.inventory_count += order_item.quantity
                            await product.save()
                    
                    return {
                        "status": "error",
                        "message": str(e),
                        "code": e.error_code,
                        "details": e.get_details()
                    }
                
                # Create order item
                order_item = OrderItem(
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=product.price
                )
                
                # Validate order item
                validation_context = order_item.validate("edit_schema")
                if validation_context.has_errors():
                    # Unreserve inventory
                    for order_item in order_items:
                        product = await Product.get(order_item.product_id)
                        if product:
                            product.inventory_count += order_item.quantity
                            await product.save()
                    
                    # Also unreserve current product's inventory
                    product.inventory_count += quantity
                    await product.save()
                    
                    return {
                        "status": "error",
                        "message": "Invalid order item data",
                        "errors": validation_context.errors,
                        "code": ErrorCode.VALIDATION_ERROR
                    }
                
                # Add to order items
                order_items.append(order_item)
                
                # Update total amount
                item_total = order_item.unit_price * order_item.quantity
                total_amount += item_total
            
            # Update order total
            order.total_amount = total_amount
            
            # Save order
            await order.save()
            
            # Save order items and link to order
            for order_item in order_items:
                order_item.order_id = order.id
                await order_item.save()
            
            # Return success response
            return {
                "status": "success",
                "data": {
                    "order": {
                        "id": order.id,
                        "customer_name": order.customer_name,
                        "customer_email": order.customer_email,
                        "total_amount": str(order.total_amount),
                        "status": order.status
                    },
                    "items": [
                        {
                            "id": item.id,
                            "product_id": item.product_id,
                            "quantity": item.quantity,
                            "unit_price": str(item.unit_price)
                        }
                        for item in order_items
                    ]
                }
            }
        except ValidationError as e:
            return {
                "status": "error",
                "message": str(e),
                "errors": e.validation_errors,
                "code": e.error_code
            }
        except UnoError as e:
            return {
                "status": "error",
                "message": str(e),
                "code": e.error_code,
                "details": e.get_details()
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }
    
    return app


# ===== TEST FIXTURES =====

@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    # Set up mock methods
    setup_mock_methods()
    
    # Clear databases
    products_db.clear()
    order_items_db.clear()
    orders_db.clear()
    
    # Create test app
    app = create_test_app()
    
    # Create test client
    client = TestClient(app)
    
    # Seed test data
    seed_test_data()
    
    return client


def seed_test_data():
    """Seed test data for the tests."""
    # Create some products
    products = [
        Product(
            id="prod-1",
            name="Laptop",
            description="High performance laptop",
            price=Decimal("999.99"),
            sku="ELE-12345",
            category="Electronics",
            inventory_count=50,
            min_order_quantity=1,
            max_order_quantity=5,
            is_active=True,
            tags="laptop,electronics,computer"
        ),
        Product(
            id="prod-2",
            name="T-Shirt",
            description="Cotton t-shirt",
            price=Decimal("19.99"),
            sku="CLO-67890",
            category="Clothing",
            inventory_count=200,
            min_order_quantity=1,
            max_order_quantity=20,
            is_active=True,
            tags="tshirt,clothing,cotton"
        ),
        Product(
            id="prod-3",
            name="Book",
            description="Bestselling novel",
            price=Decimal("14.99"),
            sku="BOO-12345",
            category="Books",
            inventory_count=100,
            min_order_quantity=1,
            is_active=True,
            tags="book,novel,fiction"
        ),
        Product(
            id="prod-4",
            name="Coffee Maker",
            description="Automatic coffee maker",
            price=Decimal("79.99"),
            sku="HOM-54321",
            category="Home",
            inventory_count=30,
            min_order_quantity=1,
            max_order_quantity=3,
            is_active=True,
            tags="coffee,kitchen,appliance"
        ),
        Product(
            id="prod-5",
            name="Phone Case",
            description="Protective phone case",
            price=Decimal("29.99"),
            sku="ELE-98765",
            category="Electronics",
            inventory_count=150,
            min_order_quantity=1,
            max_order_quantity=10,
            is_active=True,
            tags="phone,case,accessory"
        ),
        Product(
            id="prod-6",
            name="Headphones",
            description="Wireless headphones",
            price=Decimal("149.99"),
            sku="ELE-24680",
            category="Electronics",
            inventory_count=0,  # Out of stock
            min_order_quantity=1,
            max_order_quantity=5,
            is_active=True,
            tags="headphones,audio,wireless"
        )
    ]
    
    # Save products to mock database
    for product in products:
        products_db[product.id] = product
    
    # Create some orders
    orders = [
        Order(
            id="order-1",
            customer_name="John Doe",
            customer_email="john.doe@example.com",
            total_amount=Decimal("1019.98"),
            status="pending"
        ),
        Order(
            id="order-2",
            customer_name="Jane Smith",
            customer_email="jane.smith@example.com",
            total_amount=Decimal("94.98"),
            status="processing"
        )
    ]
    
    # Save orders to mock database
    for order in orders:
        orders_db[order.id] = order
    
    # Create order items
    order_items = [
        OrderItem(
            id="item-1",
            order_id="order-1",
            product_id="prod-1",
            quantity=1,
            unit_price=Decimal("999.99")
        ),
        OrderItem(
            id="item-2",
            order_id="order-1",
            product_id="prod-5",
            quantity=1,
            unit_price=Decimal("19.99")
        ),
        OrderItem(
            id="item-3",
            order_id="order-2",
            product_id="prod-3",
            quantity=2,
            unit_price=Decimal("14.99")
        ),
        OrderItem(
            id="item-4",
            order_id="order-2",
            product_id="prod-5",
            quantity=1,
            unit_price=Decimal("29.99")
        )
    ]
    
    # Save order items to mock database
    for item in order_items:
        order_items_db[item.id] = item


# ===== INTEGRATION TESTS =====

def test_product_creation_validation(test_client):
    """Test validation when creating a product."""
    # Valid product data
    valid_data = {
        "name": "Test Product",
        "description": "A test product",
        "price": "49.99",
        "sku": "TST-12345",
        "category": "Electronics",
        "inventory_count": 100,
        "min_order_quantity": 1,
        "max_order_quantity": 10,
        "is_active": True,
        "tags": "test,product,electronics"
    }
    
    # Create valid product
    response = test_client.post("/api/v1/product", json=valid_data)
    assert response.status_code == 201  # Created
    data = response.json()
    assert "id" in data
    assert data["name"] == "Test Product"
    assert data["price"] == "49.99"
    
    # Invalid product data with multiple validation errors
    invalid_data = {
        "name": "Te",  # Too short
        "description": "Invalid product",
        "price": "-10.00",  # Negative price
        "sku": "invalid-sku",  # Invalid format
        "category": "InvalidCategory",  # Invalid category
        "inventory_count": 100,
        "min_order_quantity": 10,
        "max_order_quantity": 5,  # min > max
        "is_active": True,
        "tags": "test,product,electronics,with spaces,invalid!char"  # Invalid tags
    }
    
    # Try to create invalid product
    response = test_client.post("/api/v1/product", json=invalid_data)
    assert response.status_code == 422  # Unprocessable entity
    data = response.json()
    assert "detail" in data
    
    # Check validation errors
    errors = data["detail"]
    error_fields = [error["loc"][1] for error in errors if len(error["loc"]) > 1]
    
    # Verify that all expected validation errors are present
    assert "name" in error_fields
    assert "price" in error_fields
    assert "sku" in error_fields
    assert "category" in error_fields
    assert "min_order_quantity" in error_fields or "max_order_quantity" in error_fields
    
    # Check specific message for name error
    name_error = next((e for e in errors if len(e["loc"]) > 1 and e["loc"][1] == "name"), None)
    assert name_error is not None
    assert "at least 3" in name_error["msg"].lower()


def test_product_update_validation(test_client):
    """Test validation when updating a product."""
    # Valid update data
    valid_data = {
        "price": "59.99",
        "inventory_count": 200
    }
    
    # Update with valid data
    response = test_client.patch("/api/v1/product/prod-1", json=valid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["price"] == "59.99"
    assert data["inventory_count"] == 200
    
    # Invalid update data
    invalid_data = {
        "price": "-10.00",  # Negative price
        "sku": "invalid-sku"  # Invalid format
    }
    
    # Try to update with invalid data
    response = test_client.patch("/api/v1/product/prod-1", json=invalid_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    # Check validation errors
    errors = data["detail"]
    error_fields = [error["loc"][1] for error in errors if len(error["loc"]) > 1]
    
    assert "price" in error_fields
    assert "sku" in error_fields


def test_order_validation(test_client):
    """Test validation when creating an order."""
    # Valid order data
    valid_data = {
        "customer_name": "Test Customer",
        "customer_email": "test@example.com",
        "total_amount": "99.99",
        "status": "pending"
    }
    
    # Create valid order
    response = test_client.post("/api/v1/order", json=valid_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["customer_name"] == "Test Customer"
    
    # Invalid order data
    invalid_data = {
        "customer_name": "Te",  # Too short
        "customer_email": "invalid-email",  # Invalid email
        "total_amount": "-10.00",  # Negative amount
        "status": "invalid-status"  # Invalid status
    }
    
    # Try to create invalid order
    response = test_client.post("/api/v1/order", json=invalid_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    # Check validation errors
    errors = data["detail"]
    error_fields = [error["loc"][1] for error in errors if len(error["loc"]) > 1]
    
    assert "customer_name" in error_fields
    assert "customer_email" in error_fields
    assert "total_amount" in error_fields
    assert "status" in error_fields


def test_order_item_validation(test_client):
    """Test validation when creating an order item."""
    # Valid order item data
    valid_data = {
        "order_id": "order-1",
        "product_id": "prod-1",
        "quantity": 1,
        "unit_price": "999.99"
    }
    
    # Create valid order item
    response = test_client.post("/api/v1/orderitem", json=valid_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["order_id"] == "order-1"
    assert data["product_id"] == "prod-1"
    
    # Invalid order item data
    invalid_data = {
        "order_id": "order-1",
        "product_id": "prod-1",
        "quantity": 0,  # Invalid quantity (must be > 0)
        "unit_price": "-10.00"  # Invalid price
    }
    
    # Try to create invalid order item
    response = test_client.post("/api/v1/orderitem", json=invalid_data)
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    
    # Check validation errors
    errors = data["detail"]
    error_fields = [error["loc"][1] for error in errors if len(error["loc"]) > 1]
    
    assert "quantity" in error_fields
    assert "unit_price" in error_fields


def test_product_inventory_reservation(test_client):
    """Test product inventory reservation with validation."""
    # Valid reservation
    response = test_client.post("/api/v1/products/prod-1/reserve", json={"quantity": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["reserved_quantity"] == 2
    assert data["data"]["remaining_inventory"] == 48  # 50 - 2 = 48
    
    # Verify inventory was updated
    response = test_client.get("/api/v1/product/prod-1")
    assert response.status_code == 200
    data = response.json()
    assert data["inventory_count"] == 48
    
    # Invalid reservation (quantity = 0)
    response = test_client.post("/api/v1/products/prod-1/reserve", json={"quantity": 0})
    assert response.status_code == 200  # API always returns 200 with error status
    data = response.json()
    assert data["status"] == "error"
    assert "non-positive quantity" in data["message"]
    
    # Invalid reservation (below minimum)
    product = products_db["prod-4"]  # min_order_quantity = 1
    product.min_order_quantity = 2
    products_db["prod-4"] = product
    
    response = test_client.post("/api/v1/products/prod-4/reserve", json={"quantity": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "below minimum" in data["message"]
    
    # Invalid reservation (above maximum)
    response = test_client.post("/api/v1/products/prod-4/reserve", json={"quantity": 4})  # max is 3
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "exceeds maximum" in data["message"]
    
    # Invalid reservation (insufficient inventory)
    response = test_client.post("/api/v1/products/prod-1/reserve", json={"quantity": 100})  # only 48 left
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Insufficient inventory" in data["message"]
    
    # Invalid reservation (out of stock)
    response = test_client.post("/api/v1/products/prod-6/reserve", json={"quantity": 1})  # inventory = 0
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Insufficient inventory" in data["message"]


def test_create_complete_order(test_client):
    """Test creating a complete order with items in a single operation."""
    # Valid order data
    valid_data = {
        "customer_name": "Complete Order Customer",
        "customer_email": "complete@example.com",
        "items": [
            {
                "product_id": "prod-1",
                "quantity": 1
            },
            {
                "product_id": "prod-2",
                "quantity": 2
            }
        ]
    }
    
    # Create valid complete order
    response = test_client.post("/api/v1/orders/complete", json=valid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "data" in data
    assert "order" in data["data"]
    assert "items" in data["data"]
    
    # Check order details
    order = data["data"]["order"]
    assert order["customer_name"] == "Complete Order Customer"
    assert order["customer_email"] == "complete@example.com"
    assert order["status"] == "pending"
    
    # Check items
    items = data["data"]["items"]
    assert len(items) == 2
    
    # Check total amount (999.99 + 2 * 19.99 = 1039.97)
    expected_total = Decimal("999.99") + (Decimal("19.99") * 2)
    assert Decimal(order["total_amount"]) == expected_total
    
    # Verify inventory was updated
    response = test_client.get("/api/v1/product/prod-1")
    assert response.status_code == 200
    data = response.json()
    assert data["inventory_count"] == 47  # 48 - 1 = 47
    
    response = test_client.get("/api/v1/product/prod-2")
    assert response.status_code == 200
    data = response.json()
    assert data["inventory_count"] == 198  # 200 - 2 = 198
    
    # Invalid order data (invalid customer data)
    invalid_data = {
        "customer_name": "Te",  # Too short
        "customer_email": "invalid-email",  # Invalid email
        "items": [
            {
                "product_id": "prod-3",
                "quantity": 1
            }
        ]
    }
    
    response = test_client.post("/api/v1/orders/complete", json=invalid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Invalid order data" in data["message"]
    assert "errors" in data
    assert len(data["errors"]) == 2  # Two validation errors
    
    # Invalid order data (invalid item)
    invalid_data = {
        "customer_name": "Valid Customer",
        "customer_email": "valid@example.com",
        "items": [
            {
                "product_id": "prod-1",
                "quantity": 0  # Invalid quantity
            }
        ]
    }
    
    response = test_client.post("/api/v1/orders/complete", json=invalid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "non-positive quantity" in data["message"]
    
    # Invalid order data (nonexistent product)
    invalid_data = {
        "customer_name": "Valid Customer",
        "customer_email": "valid@example.com",
        "items": [
            {
                "product_id": "nonexistent-product",
                "quantity": 1
            }
        ]
    }
    
    response = test_client.post("/api/v1/orders/complete", json=invalid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Product not found" in data["message"]
    
    # Invalid order data (insufficient inventory)
    invalid_data = {
        "customer_name": "Valid Customer",
        "customer_email": "valid@example.com",
        "items": [
            {
                "product_id": "prod-1",
                "quantity": 100  # More than available
            }
        ]
    }
    
    response = test_client.post("/api/v1/orders/complete", json=invalid_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Insufficient inventory" in data["message"]


def test_cross_entity_validation(test_client):
    """Test validation across multiple entities."""
    # Scenario: Order must have at least one item
    # This would require custom validation in the API endpoint
    
    # Create order through the complete order endpoint
    empty_order = {
        "customer_name": "Empty Order Customer",
        "customer_email": "empty@example.com",
        "items": []  # No items
    }
    
    # Custom validation to check for empty items list
    def validate_order_items(items):
        context = ValidationContext()
        if not items:
            context.add_error(
                field="items",
                message="Order must contain at least one item",
                error_code="EMPTY_ORDER"
            )
        return context
    
    # Override the endpoint handler to include custom validation
    app = create_test_app()
    original_handler = app.routes[-1].endpoint
    
    async def enhanced_handler(data: dict):
        # Perform custom validation
        items = data.get("items", [])
        context = validate_order_items(items)
        
        if context.has_errors():
            return {
                "status": "error",
                "message": "Invalid order data",
                "errors": context.errors,
                "code": ErrorCode.VALIDATION_ERROR
            }
        
        # Call original handler
        return await original_handler(data)
    
    # Replace the handler
    app.routes[-1].endpoint = enhanced_handler
    
    # Create test client with the modified app
    client = TestClient(app)
    
    # Test with empty items
    response = client.post("/api/v1/orders/complete", json=empty_order)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert data["errors"][0]["field"] == "items"
    assert "must contain at least one item" in data["errors"][0]["message"]


def test_complex_validation_pipeline(test_client):
    """Test a complex validation pipeline with multiple steps."""
    # Scenario: A product bundle that requires validation across multiple entities
    # 1. Bundle must have at least 2 unique products
    # 2. Bundle price must be less than sum of individual product prices
    # 3. Products must be in stock
    # 4. Products must be from at least 2 different categories
    
    # Create a product bundle data structure
    class ProductBundle:
        def __init__(self, name, price, products):
            self.name = name
            self.price = price
            self.products = products  # List of (product_id, quantity) tuples
    
    # Create a validation function
    async def validate_bundle(bundle):
        context = ValidationContext()
        
        # 1. Check that bundle has at least 2 unique products
        unique_products = set(product_id for product_id, _ in bundle.products)
        if len(unique_products) < 2:
            context.add_error(
                field="products",
                message="Bundle must contain at least 2 unique products",
                error_code="INSUFFICIENT_BUNDLE_PRODUCTS"
            )
        
        # Get product objects
        products = []
        for product_id, _ in bundle.products:
            product = await Product.get(product_id)
            if not product:
                context.add_error(
                    field="products",
                    message=f"Product not found: {product_id}",
                    error_code="PRODUCT_NOT_FOUND"
                )
                continue
            products.append(product)
        
        if len(products) < len(bundle.products):
            # Some products were not found, skip remaining validation
            return context
        
        # 2. Check bundle price
        individual_sum = sum(
            product.price * quantity
            for (_, quantity), product in zip(bundle.products, products)
        )
        if bundle.price >= individual_sum:
            context.add_error(
                field="price",
                message="Bundle price must be less than sum of individual product prices",
                error_code="INVALID_BUNDLE_PRICE",
                details={
                    "bundle_price": str(bundle.price),
                    "individual_sum": str(individual_sum)
                }
            )
        
        # 3. Check product inventory
        for (product_id, quantity), product in zip(bundle.products, products):
            if product.inventory_count < quantity:
                context.add_error(
                    field="products",
                    message=f"Insufficient inventory for product {product_id}: {product.inventory_count} available, {quantity} requested",
                    error_code="INSUFFICIENT_INVENTORY",
                    details={
                        "product_id": product_id,
                        "available": product.inventory_count,
                        "requested": quantity
                    }
                )
        
        # 4. Check product categories
        categories = set(product.category for product in products)
        if len(categories) < 2:
            context.add_error(
                field="products",
                message="Bundle must contain products from at least 2 different categories",
                error_code="INSUFFICIENT_CATEGORY_VARIETY"
            )
        
        return context
    
    # Test valid bundle
    valid_bundle = ProductBundle(
        name="Test Bundle",
        price=Decimal("1009.99"),  # Less than sum of individual prices
        products=[
            ("prod-1", 1),  # Electronics - 999.99
            ("prod-2", 1)   # Clothing - 19.99
        ]
    )
    
    context = await validate_bundle(valid_bundle)
    assert not context.has_errors()
    
    # Test bundle with insufficient products
    invalid_bundle = ProductBundle(
        name="Invalid Bundle",
        price=Decimal("899.99"),
        products=[
            ("prod-1", 1)  # Only one product
        ]
    )
    
    context = await validate_bundle(invalid_bundle)
    assert context.has_errors()
    assert len(context.errors) == 1
    assert "at least 2 unique products" in context.errors[0]["message"]
    
    # Test bundle with price too high
    invalid_bundle = ProductBundle(
        name="Expensive Bundle",
        price=Decimal("1100.00"),  # Higher than sum of individual prices
        products=[
            ("prod-1", 1),  # 999.99
            ("prod-2", 1)   # 19.99
        ]
    )
    
    context = await validate_bundle(invalid_bundle)
    assert context.has_errors()
    assert len(context.errors) == 1
    assert "must be less than sum" in context.errors[0]["message"]
    
    # Test bundle with insufficient inventory
    invalid_bundle = ProductBundle(
        name="Out of Stock Bundle",
        price=Decimal("900.00"),
        products=[
            ("prod-1", 100),  # More than available
            ("prod-2", 1)
        ]
    )
    
    context = await validate_bundle(invalid_bundle)
    assert context.has_errors()
    assert len(context.errors) == 1
    assert "Insufficient inventory" in context.errors[0]["message"]
    
    # Test bundle with same category products
    invalid_bundle = ProductBundle(
        name="Same Category Bundle",
        price=Decimal("900.00"),
        products=[
            ("prod-1", 1),  # Electronics
            ("prod-5", 1)   # Also Electronics
        ]
    )
    
    context = await validate_bundle(invalid_bundle)
    assert context.has_errors()
    assert len(context.errors) == 1
    assert "at least 2 different categories" in context.errors[0]["message"]
    
    # Test bundle with multiple validation errors
    invalid_bundle = ProductBundle(
        name="Multiple Errors Bundle",
        price=Decimal("2000.00"),  # Too high
        products=[
            ("prod-1", 100),  # Insufficient inventory
            ("prod-5", 1)     # Same category as prod-1
        ]
    )
    
    context = await validate_bundle(invalid_bundle)
    assert context.has_errors()
    assert len(context.errors) == 3  # Price, inventory, and category errors


def test_schema_validation_exception_handling(test_client):
    """Test proper handling of schema validation exceptions in API context."""
    
    # Define an invalid product with multiple validation issues
    severely_invalid_product = {
        "name": "",  # Empty
        "description": "X" * 5000,  # Too long
        "price": "invalid",  # Not a decimal
        "sku": "",  # Empty
        "category": None,  # Invalid type
        "inventory_count": -10,  # Negative
        "min_order_quantity": "abc",  # Invalid type
        "is_active": "not-boolean"  # Invalid type
    }
    
    # Send request and check the response
    response = test_client.post("/api/v1/product", json=severely_invalid_product)
    assert response.status_code == 422
    
    # Verify error response structure
    data = response.json()
    assert "detail" in data
    errors = data["detail"]
    
    # Check that we received multiple validation errors
    assert len(errors) >= 4
    
    # Check for field-specific errors
    error_fields = [error["loc"][1] for error in errors if len(error["loc"]) > 1]
    assert "name" in error_fields
    assert "price" in error_fields
    assert "sku" in error_fields
    assert "category" in error_fields


def test_schema_dependency_validation(test_client):
    """Test validation with dependencies in a schema."""
    
    # Create a schema with dependent fields
    class ProductPromoSchema(UnoSchema):
        """Schema for product promotions with dependent fields."""
        product_id: str
        promotion_type: str  # 'sale', 'clearance', 'bundle'
        discount_percentage: Optional[int] = None  # Required for 'sale'
        bundle_product_ids: Optional[List[str]] = None  # Required for 'bundle'
        clearance_price: Optional[Decimal] = None  # Required for 'clearance'
        
        @model_validator(mode='after')
        def validate_promotion_type_dependencies(self):
            """Validate that required fields are present for each promotion type."""
            if self.promotion_type == 'sale' and self.discount_percentage is None:
                raise ValueError("discount_percentage is required for 'sale' promotions")
            elif self.promotion_type == 'bundle' and not self.bundle_product_ids:
                raise ValueError("bundle_product_ids is required for 'bundle' promotions")
            elif self.promotion_type == 'clearance' and self.clearance_price is None:
                raise ValueError("clearance_price is required for 'clearance' promotions")
            return self
    
    # Create a test endpoint for this schema
    app = create_test_app()
    
    @app.post("/api/v1/product-promotions")
    async def create_promotion(data: ProductPromoSchema):
        return data.model_dump()
    
    client = TestClient(app)
    
    # Test valid sale promotion
    valid_sale = {
        "product_id": "prod-1",
        "promotion_type": "sale",
        "discount_percentage": 20
    }
    response = client.post("/api/v1/product-promotions", json=valid_sale)
    assert response.status_code == 200
    
    # Test valid bundle promotion
    valid_bundle = {
        "product_id": "prod-1",
        "promotion_type": "bundle",
        "bundle_product_ids": ["prod-2", "prod-3"]
    }
    response = client.post("/api/v1/product-promotions", json=valid_bundle)
    assert response.status_code == 200
    
    # Test valid clearance promotion
    valid_clearance = {
        "product_id": "prod-1",
        "promotion_type": "clearance",
        "clearance_price": "49.99"
    }
    response = client.post("/api/v1/product-promotions", json=valid_clearance)
    assert response.status_code == 200
    
    # Test invalid sale (missing discount)
    invalid_sale = {
        "product_id": "prod-1",
        "promotion_type": "sale"
    }
    response = client.post("/api/v1/product-promotions", json=invalid_sale)
    assert response.status_code == 422
    assert "discount_percentage is required" in response.text
    
    # Test invalid bundle (missing product IDs)
    invalid_bundle = {
        "product_id": "prod-1",
        "promotion_type": "bundle"
    }
    response = client.post("/api/v1/product-promotions", json=invalid_bundle)
    assert response.status_code == 422
    assert "bundle_product_ids is required" in response.text
    
    # Test invalid clearance (missing price)
    invalid_clearance = {
        "product_id": "prod-1",
        "promotion_type": "clearance"
    }
    response = client.post("/api/v1/product-promotions", json=invalid_clearance)
    assert response.status_code == 422
    assert "clearance_price is required" in response.text


def test_schema_field_transformation():
    """Test schema field transformation and custom parsing."""
    
    # Create a schema with field transformations
    class ProductImportSchema(UnoSchema):
        """Schema for importing products with field transformations."""
        name: str
        price: Decimal
        sku: str
        category: str
        tags: List[str]
        dimensions: Optional[Dict[str, float]] = None
        
        @field_validator("sku")
        @classmethod
        def normalize_sku(cls, v: str) -> str:
            """Normalize SKU to uppercase with proper format."""
            if not v:
                raise ValueError("SKU cannot be empty")
            
            # Convert to proper format if possible
            parts = v.upper().split("-")
            if len(parts) == 2 and len(parts[0]) <= 3 and parts[1].isdigit():
                category_code = parts[0].ljust(3, "X")[:3]
                product_number = parts[1].zfill(5)[:5]
                return f"{category_code}-{product_number}"
            
            raise ValueError("SKU must be in format ABC-12345")
        
        @field_validator("tags")
        @classmethod
        def parse_tags(cls, v: List[str]) -> List[str]:
            """Parse and normalize tags."""
            if isinstance(v, str):
                # Split by comma if it's a string
                tags = [tag.strip() for tag in v.split(",")]
            else:
                # Ensure all tags are strings
                tags = [str(tag).strip() for tag in v]
            
            # Remove duplicates and empty tags
            tags = list(set(filter(None, tags)))
            
            # Validate tags
            for tag in tags:
                if not all(c.isalnum() or c == "-" for c in tag):
                    raise ValueError(f"Tag '{tag}' contains invalid characters")
            
            return tags
        
        @field_validator("dimensions")
        @classmethod
        def parse_dimensions(cls, v: Optional[Dict[str, float]]) -> Optional[Dict[str, float]]:
            """Parse and validate dimensions."""
            if not v:
                return None
            
            required_keys = {"length", "width", "height"}
            
            # Check for required keys
            if not all(key in v for key in required_keys):
                missing = required_keys - set(v.keys())
                raise ValueError(f"Missing dimension keys: {', '.join(missing)}")
            
            # Validate values
            for key in required_keys:
                if v[key] <= 0:
                    raise ValueError(f"{key.capitalize()} must be positive")
            
            # Add calculated volume
            v["volume"] = v["length"] * v["width"] * v["height"]
            
            return v
    
    # Test valid data
    valid_data = {
        "name": "Test Product",
        "price": "29.99",
        "sku": "abc-12345",  # Will be normalized to ABC-12345
        "category": "Electronics",
        "tags": ["test", "product", "electronics"],
        "dimensions": {
            "length": 10.0,
            "width": 5.0,
            "height": 2.0
        }
    }
    
    product = ProductImportSchema(**valid_data)
    assert product.sku == "ABC-12345"  # Normalized to uppercase
    assert set(product.tags) == {"test", "product", "electronics"}
    assert product.dimensions["volume"] == 100.0  # Added calculated field
    
    # Test SKU normalization with partial format
    partial_sku_data = valid_data.copy()
    partial_sku_data["sku"] = "ab-123"
    
    product = ProductImportSchema(**partial_sku_data)
    assert product.sku == "ABX-00123"  # Normalized format
    
    # Test tags as comma-separated string
    string_tags_data = valid_data.copy()
    string_tags_data["tags"] = "test, product, electronics"
    
    product = ProductImportSchema(**string_tags_data)
    assert set(product.tags) == {"test", "product", "electronics"}
    
    # Test invalid SKU
    invalid_sku_data = valid_data.copy()
    invalid_sku_data["sku"] = "invalid_sku"
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductImportSchema(**invalid_sku_data)
    
    assert "SKU must be in format" in str(excinfo.value)
    
    # Test invalid dimensions
    invalid_dimensions_data = valid_data.copy()
    invalid_dimensions_data["dimensions"] = {
        "length": 10.0,
        "width": -5.0,  # Negative width
        "height": 2.0
    }
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductImportSchema(**invalid_dimensions_data)
    
    assert "Width must be positive" in str(excinfo.value)