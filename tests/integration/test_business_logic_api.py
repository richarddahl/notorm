"""
Integration tests for business logic objects with API endpoints.

This module tests the integration between UnoObj business logic
and FastAPI endpoints, ensuring proper validation and behavior.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, timedelta
import json
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient

from uno.obj import UnoObj
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column
from uno.schema import UnoSchemaConfig
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.database.db import FilterParam


# ===== PRODUCT DOMAIN MODELS =====

class ProductModel(UnoModel):
    """Database model for products."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class Product(UnoObj[ProductModel]):
    """Product business object with domain-specific validation."""
    
    # Schema configurations
    schema_configs = {
        "view_schema": UnoSchemaConfig(),
        "edit_schema": UnoSchemaConfig(exclude_fields={"created_at", "updated_at"}),
        "list_schema": UnoSchemaConfig(include_fields={
            "id", "name", "price", "category", "inventory_count", "is_active"
        })
    }
    
    # Domain validation
    def validate(self, schema_name: str) -> ValidationContext:
        """Domain-specific validation for products."""
        # Call parent validation first
        context = super().validate(schema_name)
        
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
            import re
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
        
        return context
    
    # Business methods
    async def reserve_inventory(self, quantity: int) -> bool:
        """Reserve inventory for an order."""
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


# ===== API ENDPOINTS FOR TESTING =====

# Create FastAPI app
app = FastAPI()

# Mock database
product_db = {}

# Mock Product.get and Product.filter for tests
@patch.object(Product, 'get')
async def mock_get_product(id):
    if id in product_db:
        return product_db[id]
    raise UnoError(f"Product not found: {id}", ErrorCode.RESOURCE_NOT_FOUND)

@patch.object(Product, 'filter')
async def mock_filter_products(filters=None):
    results = list(product_db.values())
    if filters and hasattr(filters, 'get'):
        # Apply filters based on category
        category = filters.get('category')
        if category:
            results = [p for p in results if p.category == category]
    return results

# Patch the UnoObj.save method to update the mock DB
@patch.object(Product, 'save')
async def mock_save_product(self):
    product_db[self.id] = self
    return self

# Define a dependency for product operations
async def get_product_service():
    class ProductService:
        async def get_product(self, product_id: str):
            try:
                return await mock_get_product(product_id)
            except UnoError as e:
                if e.error_code == ErrorCode.RESOURCE_NOT_FOUND:
                    raise HTTPException(status_code=404, detail=str(e))
                raise HTTPException(status_code=500, detail=str(e))
        
        async def create_product(self, product_data: dict):
            # Generate an ID for new product
            import uuid
            product_id = str(uuid.uuid4())
            
            # Create product with the generated ID
            product_data['id'] = product_id
            product = Product(**product_data)
            
            # Validate product
            validation_context = product.validate("edit_schema")
            if validation_context.has_errors():
                raise ValidationError(
                    "Validation failed for product",
                    ErrorCode.VALIDATION_ERROR,
                    validation_errors=validation_context.errors
                )
            
            # Save product
            await mock_save_product(product)
            return product
        
        async def update_product(self, product_id: str, product_data: dict):
            # Get the existing product
            product = await self.get_product(product_id)
            
            # Update product attributes
            for key, value in product_data.items():
                setattr(product, key, value)
            
            # Validate product
            validation_context = product.validate("edit_schema")
            if validation_context.has_errors():
                raise ValidationError(
                    "Validation failed for product",
                    ErrorCode.VALIDATION_ERROR,
                    validation_errors=validation_context.errors
                )
            
            # Save product
            await mock_save_product(product)
            return product
        
        async def list_products(self, category: str = None):
            filters = None
            if category:
                filters = FilterParam(category=category)
            return await mock_filter_products(filters)
        
        async def reserve_inventory(self, product_id: str, quantity: int):
            product = await self.get_product(product_id)
            return await product.reserve_inventory(quantity)
    
    return ProductService()

# Define API routes
@app.post("/products")
async def create_product(
    product_data: dict,
    product_service = Depends(get_product_service)
):
    try:
        product = await product_service.create_product(product_data)
        return {"status": "success", "data": product.dict()}
    except ValidationError as e:
        return {"status": "error", "message": str(e), "errors": e.validation_errors}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/products/{product_id}")
async def get_product(
    product_id: str,
    product_service = Depends(get_product_service)
):
    try:
        product = await product_service.get_product(product_id)
        return {"status": "success", "data": product.dict()}
    except HTTPException as e:
        return {"status": "error", "message": e.detail, "code": e.status_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.put("/products/{product_id}")
async def update_product(
    product_id: str,
    product_data: dict,
    product_service = Depends(get_product_service)
):
    try:
        product = await product_service.update_product(product_id, product_data)
        return {"status": "success", "data": product.dict()}
    except ValidationError as e:
        return {"status": "error", "message": str(e), "errors": e.validation_errors}
    except HTTPException as e:
        return {"status": "error", "message": e.detail, "code": e.status_code}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/products")
async def list_products(
    category: str = None,
    product_service = Depends(get_product_service)
):
    try:
        products = await product_service.list_products(category)
        return {"status": "success", "data": [p.dict() for p in products]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/products/{product_id}/reserve")
async def reserve_inventory(
    product_id: str,
    data: dict,
    product_service = Depends(get_product_service)
):
    try:
        quantity = data.get("quantity", 0)
        if quantity <= 0:
            return {"status": "error", "message": "Quantity must be greater than zero"}
        
        success = await product_service.reserve_inventory(product_id, quantity)
        return {"status": "success", "reserved": success}
    except ValidationError as e:
        return {"status": "error", "message": str(e), "errors": e.validation_errors}
    except HTTPException as e:
        return {"status": "error", "message": e.detail, "code": e.status_code}
    except UnoError as e:
        return {"status": "error", "message": str(e), "code": e.error_code}
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ===== INTEGRATION TESTS =====

@pytest.fixture
def test_client():
    # Create test client
    client = TestClient(app)
    
    # Reset product database before each test
    product_db.clear()
    
    # Seed database with test products
    test_products = [
        Product(
            id="prod-1",
            name="Test Product 1",
            description="Test description 1",
            price=Decimal("19.99"),
            sku="ABC-12345",
            category="Electronics",
            inventory_count=100,
            is_active=True
        ),
        Product(
            id="prod-2",
            name="Test Product 2",
            description="Test description 2",
            price=Decimal("29.99"),
            sku="DEF-67890",
            category="Clothing",
            inventory_count=50,
            is_active=True
        ),
        Product(
            id="prod-3",
            name="Test Product 3",
            description="Test description 3",
            price=Decimal("9.99"),
            sku="GHI-24680",
            category="Books",
            inventory_count=200,
            is_active=False
        )
    ]
    
    for product in test_products:
        product_db[product.id] = product
    
    return client


def test_get_product(test_client):
    """Test getting a product."""
    # Get existing product
    response = test_client.get("/products/prod-1")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "Test Product 1"
    assert data["data"]["price"] == "19.99"
    
    # Get non-existent product
    response = test_client.get("/products/non-existent")
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_create_product(test_client):
    """Test creating a product."""
    # Create valid product
    valid_product = {
        "name": "New Product",
        "description": "New product description",
        "price": "39.99",
        "sku": "JKL-13579",
        "category": "Electronics",
        "inventory_count": 75,
        "is_active": True
    }
    
    response = test_client.post("/products", json=valid_product)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["name"] == "New Product"
    assert data["data"]["price"] == "39.99"
    
    # Create invalid product (negative price)
    invalid_product = {
        "name": "Invalid Product",
        "description": "Invalid product description",
        "price": "-9.99",
        "sku": "MNO-24680",
        "category": "Electronics",
        "inventory_count": 50,
        "is_active": True
    }
    
    response = test_client.post("/products", json=invalid_product)
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert any("price" in error["field"] for error in data["errors"])
    
    # Create invalid product (invalid SKU format)
    invalid_product = {
        "name": "Invalid Product",
        "description": "Invalid product description",
        "price": "29.99",
        "sku": "invalid-sku",
        "category": "Electronics",
        "inventory_count": 50,
        "is_active": True
    }
    
    response = test_client.post("/products", json=invalid_product)
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert any("sku" in error["field"] for error in data["errors"])
    
    # Create invalid product (invalid category)
    invalid_product = {
        "name": "Invalid Product",
        "description": "Invalid product description",
        "price": "29.99",
        "sku": "PQR-13579",
        "category": "Invalid Category",
        "inventory_count": 50,
        "is_active": True
    }
    
    response = test_client.post("/products", json=invalid_product)
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert any("category" in error["field"] for error in data["errors"])


def test_update_product(test_client):
    """Test updating a product."""
    # Update existing product
    update_data = {
        "price": "49.99",
        "inventory_count": 150
    }
    
    response = test_client.put("/products/prod-1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["data"]["price"] == "49.99"
    assert data["data"]["inventory_count"] == 150
    
    # Update with invalid data
    invalid_update = {
        "price": "-20.00"
    }
    
    response = test_client.put("/products/prod-1", json=invalid_update)
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "errors" in data
    assert any("price" in error["field"] for error in data["errors"])
    
    # Update non-existent product
    response = test_client.put("/products/non-existent", json=update_data)
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "not found" in data["message"]


def test_list_products(test_client):
    """Test listing products."""
    # List all products
    response = test_client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 3
    
    # List products by category
    response = test_client.get("/products?category=Electronics")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["category"] == "Electronics"
    
    response = test_client.get("/products?category=Clothing")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["data"]) == 1
    assert data["data"][0]["category"] == "Clothing"


def test_reserve_inventory(test_client):
    """Test reserving product inventory."""
    # Reserve valid quantity
    response = test_client.post("/products/prod-1/reserve", json={"quantity": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["reserved"] is True
    
    # Check that inventory was updated
    response = test_client.get("/products/prod-1")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["inventory_count"] == 90  # 100 - 10
    
    # Reserve more than available
    response = test_client.post("/products/prod-1/reserve", json={"quantity": 100})
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "Insufficient inventory" in data["message"]
    
    # Reserve zero or negative quantity
    response = test_client.post("/products/prod-1/reserve", json={"quantity": 0})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert "Quantity must be greater than zero" in data["message"]
    
    # Reserve from non-existent product
    response = test_client.post("/products/non-existent/reserve", json={"quantity": 10})
    assert response.status_code == 200  # Status is 200 because we handle the error
    data = response.json()
    assert data["status"] == "error"
    assert "not found" in data["message"]


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])