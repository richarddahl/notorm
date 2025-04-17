"""
Tests for the enhanced product repository with specification pattern.

This module demonstrates testing the enhanced specification pattern
with a product repository implementation.
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import json
import uuid

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from uno.domain.models import Product, ProductCategory
from uno.domain.repositories.sqlalchemy.product import ProductRepository, ProductModel, EnhancedProductSpec
from uno.domain.specifications import specification_factory, enhance_specification_factory


# Test data
TEST_PRODUCTS = [
    {
        "id": "1",
        "name": "Gaming Laptop",
        "description": "High-performance gaming laptop",
        "price": 1299.99,
        "category": "Electronics",
        "sku": "LAPTOP001",
        "in_stock": True,
        "stock_quantity": 15,
        "tags": ["gaming", "laptop", "high-performance"],
        "metadata": {
            "supplier": {
                "id": "SUPP001",
                "name": "TechSupplier"
            },
            "on_sale": True,
            "discount": 10
        },
        "created_at": datetime.now(timezone.utc) - timedelta(days=10)
    },
    {
        "id": "2",
        "name": "Ergonomic Office Chair",
        "description": "Comfortable office chair",
        "price": 299.99,
        "category": "Furniture",
        "sku": "CHAIR001",
        "in_stock": True,
        "stock_quantity": 8,
        "tags": ["office", "ergonomic", "chair"],
        "metadata": {
            "supplier": {
                "id": "SUPP002",
                "name": "FurnitureSupplier"
            },
            "on_sale": False
        },
        "created_at": datetime.now(timezone.utc) - timedelta(days=60)
    },
    {
        "id": "3",
        "name": "Wireless Headphones",
        "description": "Noise-cancelling wireless headphones",
        "price": 199.99,
        "category": "Electronics",
        "sku": "AUDIO001",
        "in_stock": True,
        "stock_quantity": 25,
        "tags": ["audio", "wireless", "noise-cancelling"],
        "metadata": {
            "supplier": {
                "id": "SUPP001",
                "name": "TechSupplier"
            },
            "on_sale": True,
            "discount": 15
        },
        "created_at": datetime.now(timezone.utc) - timedelta(days=5)
    },
    {
        "id": "4",
        "name": "Coffee Table",
        "description": None,
        "price": 149.99,
        "category": "Furniture",
        "sku": "TABLE001",
        "in_stock": False,
        "stock_quantity": 0,
        "tags": ["table", "living-room"],
        "metadata": {
            "supplier": {
                "id": "SUPP002",
                "name": "FurnitureSupplier"
            },
            "on_sale": False
        },
        "created_at": datetime.now(timezone.utc) - timedelta(days=90)
    },
    {
        "id": "5",
        "name": "Gaming Mouse",
        "description": "Precision gaming mouse",
        "price": 79.99,
        "category": "Electronics",
        "sku": "MOUSE001",
        "in_stock": True,
        "stock_quantity": 5,
        "tags": ["gaming", "mouse", "precision"],
        "metadata": {
            "supplier": {
                "id": "SUPP001",
                "name": "TechSupplier"
            },
            "on_sale": False
        },
        "created_at": datetime.now(timezone.utc) - timedelta(days=15)
    }
]


@pytest.fixture
async def db_session():
    """Create a test database session with in-memory SQLite."""
    # Create async engine with in-memory SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(ProductModel.metadata.create_all)
    
    # Create session factory
    async_session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create session and insert test data
    async with async_session_factory() as session:
        for product_data in TEST_PRODUCTS:
            product_model = ProductModel(**product_data)
            session.add(product_model)
        
        await session.commit()
    
    # Return a session for testing
    async with async_session_factory() as session:
        yield session
    
    # Clean up
    async with engine.begin() as conn:
        await conn.run_sync(ProductModel.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
def session_factory(db_session):
    """Create a session factory for the repository."""
    async def _factory():
        return db_session
    
    return _factory


@pytest.fixture
async def product_repository(session_factory):
    """Create a product repository for testing."""
    return ProductRepository(session_factory)


class TestEnhancedProductRepository:
    """Test the enhanced product repository implementation."""
    
    @pytest.mark.asyncio
    async def test_find_by_category(self, product_repository):
        """Test finding products by category."""
        # Test with Electronics category
        products = await product_repository.find_by_category(ProductCategory.ELECTRONICS)
        assert len(products) == 3
        assert all(p.category == ProductCategory.ELECTRONICS.value for p in products)
        
        # Test with Furniture category
        products = await product_repository.find_by_category(ProductCategory.FURNITURE)
        assert len(products) == 2
        assert all(p.category == ProductCategory.FURNITURE.value for p in products)
    
    @pytest.mark.asyncio
    async def test_find_by_sku(self, product_repository):
        """Test finding a product by SKU."""
        product = await product_repository.find_by_sku("LAPTOP001")
        assert product is not None
        assert product.id == "1"
        assert product.name == "Gaming Laptop"
        
        # Test with non-existent SKU
        product = await product_repository.find_by_sku("NONEXISTENT")
        assert product is None
    
    @pytest.mark.asyncio
    async def test_find_in_stock(self, product_repository):
        """Test finding in-stock products."""
        products = await product_repository.find_in_stock()
        assert len(products) == 4
        assert all(p.in_stock for p in products)
    
    @pytest.mark.asyncio
    async def test_find_in_stock_by_category(self, product_repository):
        """Test finding in-stock products by category."""
        products = await product_repository.find_in_stock_by_category(ProductCategory.ELECTRONICS)
        assert len(products) == 3
        assert all(p.in_stock for p in products)
        assert all(p.category == ProductCategory.ELECTRONICS.value for p in products)
    
    @pytest.mark.asyncio
    async def test_find_by_price_range(self, product_repository):
        """Test finding products in a price range."""
        # Test inclusive range
        products = await product_repository.find_by_price_range(100, 200)
        assert len(products) == 2
        assert all(100 <= p.price <= 200 for p in products)
        
        # Test with no products in range
        products = await product_repository.find_by_price_range(5000, 6000)
        assert len(products) == 0
    
    @pytest.mark.asyncio
    async def test_find_by_name_pattern(self, product_repository):
        """Test finding products by name pattern."""
        # Case-insensitive search
        products = await product_repository.find_by_name_pattern("gaming")
        assert len(products) == 2
        assert any(p.name == "Gaming Laptop" for p in products)
        assert any(p.name == "Gaming Mouse" for p in products)
        
        # Case-sensitive search
        products = await product_repository.find_by_name_pattern("gaming", case_sensitive=True)
        assert len(products) == 0  # "Gaming" != "gaming"
    
    @pytest.mark.asyncio
    async def test_find_by_tags(self, product_repository):
        """Test finding products with specific tags."""
        products = await product_repository.find_by_tags(["gaming"])
        assert len(products) == 2
        assert all("gaming" in p.tags for p in products)
        
        products = await product_repository.find_by_tags(["ergonomic"])
        assert len(products) == 1
        assert products[0].name == "Ergonomic Office Chair"
    
    @pytest.mark.asyncio
    async def test_find_recently_added(self, product_repository):
        """Test finding recently added products."""
        # Products added in the last 7 days
        products = await product_repository.find_recently_added(days=7)
        assert len(products) == 1
        assert products[0].name == "Wireless Headphones"
        
        # Products added in the last 30 days
        products = await product_repository.find_recently_added(days=30)
        assert len(products) == 3
    
    @pytest.mark.asyncio
    async def test_find_with_specific_metadata(self, product_repository):
        """Test finding products with specific metadata."""
        products = await product_repository.find_with_specific_metadata("SUPP001")
        assert len(products) == 3
        assert all(p.metadata["supplier"]["id"] == "SUPP001" for p in products)
    
    @pytest.mark.asyncio
    async def test_find_products_on_sale(self, product_repository):
        """Test finding products that are on sale."""
        products = await product_repository.find_products_on_sale()
        assert len(products) == 2
        assert all(p.metadata["on_sale"] is True for p in products)
    
    @pytest.mark.asyncio
    async def test_find_low_stock(self, product_repository):
        """Test finding products with low stock."""
        # Products with stock <= 5
        products = await product_repository.find_low_stock(threshold=5)
        assert len(products) == 1
        assert products[0].name == "Gaming Mouse"
        assert products[0].stock_quantity == 5
        
        # Products with stock <= 10
        products = await product_repository.find_low_stock(threshold=10)
        assert len(products) == 2
    
    @pytest.mark.asyncio
    async def test_find_products_not_in_categories(self, product_repository):
        """Test finding products not in certain categories."""
        products = await product_repository.find_products_not_in_categories([ProductCategory.FURNITURE])
        assert len(products) == 3
        assert all(p.category != ProductCategory.FURNITURE.value for p in products)
    
    @pytest.mark.asyncio
    async def test_find_products_without_description(self, product_repository):
        """Test finding products without a description."""
        products = await product_repository.find_products_without_description()
        assert len(products) == 1
        assert products[0].name == "Coffee Table"
        assert products[0].description is None
    
    @pytest.mark.asyncio
    async def test_find_products_with_text_in_description(self, product_repository):
        """Test finding products with specific text in their description."""
        products = await product_repository.find_products_with_text_in_description("noise")
        assert len(products) == 1
        assert products[0].name == "Wireless Headphones"
        assert "noise" in products[0].description.lower()
    
    @pytest.mark.asyncio
    async def test_search_products(self, product_repository):
        """Test the combined search products functionality."""
        # Search with multiple criteria
        products = await product_repository.search_products(
            keywords="gaming",
            category=ProductCategory.ELECTRONICS,
            min_price=50,
            max_price=100,
            in_stock_only=True,
            tags=["precision"]
        )
        assert len(products) == 1
        assert products[0].name == "Gaming Mouse"
        
        # Search with just keywords
        products = await product_repository.search_products(keywords="chair")
        assert len(products) == 1
        assert products[0].name == "Ergonomic Office Chair"
        
        # Search with just category and price range
        products = await product_repository.search_products(
            category=ProductCategory.ELECTRONICS,
            min_price=100,
            max_price=1000
        )
        assert len(products) == 1
        assert products[0].name == "Wireless Headphones"
    
    @pytest.mark.asyncio
    async def test_raw_specification_usage(self, product_repository):
        """Test using the specification pattern directly."""
        # Create a complex specification manually
        spec = (EnhancedProductSpec.contains("name", "gaming")
                .and_(EnhancedProductSpec.gt("price", 100))
                .and_(EnhancedProductSpec.is_not_null("description")))
        
        # Find products using the specification
        products = await product_repository.find(spec)
        assert len(products) == 1
        assert products[0].name == "Gaming Laptop"
        
        # Even more complex specification
        spec = (EnhancedProductSpec.in_list("category", ["Electronics", "Furniture"])
                .and_(EnhancedProductSpec.range("price", 150, 300))
                .and_(EnhancedProductSpec.eq("in_stock", True)))
        
        products = await product_repository.find(spec)
        assert len(products) == 1
        assert products[0].name == "Ergonomic Office Chair"