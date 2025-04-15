"""
Tests for complex schema validation scenarios.

This module tests advanced schema validation capabilities including:
- Interdependent field validation
- Conditional validation rules
- Complex type transformations
- Nested object validation
- Array and dictionary validation
- Custom validators
- Extensible validation rules
"""

import pytest
import json
from datetime import datetime, date, time, timedelta
from decimal import Decimal
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Set, Tuple, Literal, ClassVar

from pydantic import BaseModel, Field, field_validator, model_validator, computed_field
from pydantic import ValidationError as PydanticValidationError

from uno.schema import UnoSchema, UnoSchemaConfig, UnoSchemaManager
from uno.schema.schema import (
    create_schema_class, 
    create_list_schema, 
    extract_fields_from_schema
)
from uno.core.errors import ValidationContext, UnoError, ErrorCode
from uno.core.errors.validation import ValidationError
from uno.model import UnoModel, PostgresTypes
from sqlalchemy.orm import Mapped, mapped_column


# ===== TEST MODELS =====

class ProductCategory(str, Enum):
    """Product category enumeration for testing."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BOOKS = "books"
    HOME = "home"
    TOYS = "toys"


class PriceRange(BaseModel):
    """Nested model for price range."""
    min_price: Decimal
    max_price: Decimal
    currency: str = "USD"
    
    @model_validator(mode='after')
    def validate_price_range(self):
        """Validate min_price is less than max_price."""
        if self.min_price > self.max_price:
            raise ValueError("min_price must be less than or equal to max_price")
        return self


class ProductDimensions(BaseModel):
    """Nested model for product dimensions."""
    length: float
    width: float
    height: float
    unit: Literal["cm", "in"] = "cm"
    
    @property
    def volume(self) -> float:
        """Calculate the volume of the product."""
        return self.length * self.width * self.height


class ProductImage(BaseModel):
    """Nested model for product images."""
    url: str
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_primary: bool = False


class ProductReview(BaseModel):
    """Nested model for product reviews."""
    user_id: str
    rating: int
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v):
        """Validate rating is between 1 and 5."""
        if v < 1 or v > 5:
            raise ValueError("Rating must be between 1 and 5")
        return v


class ProductStatus(str, Enum):
    """Product status enumeration."""
    DRAFT = "draft"
    PUBLISHED = "published"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"


class ProductInventoryModel(UnoModel):
    """Database model for product inventory."""
    
    __tablename__ = "product_inventory"
    
    product_id: Mapped[str] = mapped_column(nullable=False)
    warehouse_id: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False, default=0)
    reserved: Mapped[int] = mapped_column(nullable=False, default=0)
    reorder_point: Mapped[int] = mapped_column(nullable=True)
    reorder_quantity: Mapped[int] = mapped_column(nullable=True)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)


class ProductModel(UnoModel):
    """Database model for products."""
    
    __tablename__ = "products"
    
    name: Mapped[PostgresTypes.String255] = mapped_column(nullable=False)
    description: Mapped[str] = mapped_column(nullable=True)
    sku: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, unique=True)
    price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=False)
    cost: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=True)
    category: Mapped[PostgresTypes.String100] = mapped_column(nullable=False)
    weight: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=True)
    dimensions: Mapped[str] = mapped_column(nullable=True)
    tags: Mapped[str] = mapped_column(nullable=True)
    manufacturer: Mapped[PostgresTypes.String255] = mapped_column(nullable=True)
    status: Mapped[PostgresTypes.String50] = mapped_column(nullable=False, default="draft")
    inventory_count: Mapped[int] = mapped_column(nullable=False, default=0)
    min_order_quantity: Mapped[int] = mapped_column(nullable=True)
    max_order_quantity: Mapped[int] = mapped_column(nullable=True)
    is_taxable: Mapped[bool] = mapped_column(nullable=False, default=True)
    tax_code: Mapped[PostgresTypes.String50] = mapped_column(nullable=True)
    barcode: Mapped[PostgresTypes.String100] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(nullable=False, default=datetime.now, onupdate=datetime.now)
    published_at: Mapped[datetime] = mapped_column(nullable=True)
    sale_start_date: Mapped[date] = mapped_column(nullable=True)
    sale_end_date: Mapped[date] = mapped_column(nullable=True)
    sale_price: Mapped[PostgresTypes.Decimal10_2] = mapped_column(nullable=True)


# ===== TEST SCHEMAS =====

class ProductBaseSchema(UnoSchema):
    """Base schema for product validation."""
    
    name: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    sku: str = Field(..., pattern=r"^[A-Z]{3}-\d{5}$")  # Format: ABC-12345
    price: Decimal = Field(..., gt=0)
    cost: Optional[Decimal] = Field(None, ge=0)
    category: ProductCategory
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[ProductDimensions] = None
    tags: Optional[List[str]] = Field(None, max_items=10)
    manufacturer: Optional[str] = None
    status: ProductStatus = ProductStatus.DRAFT
    inventory_count: int = Field(0, ge=0)
    min_order_quantity: Optional[int] = Field(None, ge=1)
    max_order_quantity: Optional[int] = Field(None, ge=1)
    is_taxable: bool = True
    tax_code: Optional[str] = None
    barcode: Optional[str] = None
    images: Optional[List[ProductImage]] = None
    reviews: Optional[List[ProductReview]] = None
    price_range: Optional[PriceRange] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    sale_start_date: Optional[date] = None
    sale_end_date: Optional[date] = None
    sale_price: Optional[Decimal] = Field(None, gt=0)
    available_colors: Optional[Set[str]] = None
    available_sizes: Optional[List[str]] = None
    warehouse_inventory: Optional[Dict[str, int]] = None

    @model_validator(mode='after')
    def validate_order_quantities(self):
        """Validate min_order_quantity is less than max_order_quantity if both are set."""
        min_qty = self.min_order_quantity
        max_qty = self.max_order_quantity
        
        if min_qty is not None and max_qty is not None and min_qty > max_qty:
            raise ValueError("min_order_quantity must be less than or equal to max_order_quantity")
        
        return self
    
    @model_validator(mode='after')
    def validate_sale_dates(self):
        """Validate sale_start_date is before sale_end_date if both are set."""
        start_date = self.sale_start_date
        end_date = self.sale_end_date
        
        if start_date is not None and end_date is not None and start_date > end_date:
            raise ValueError("sale_start_date must be before sale_end_date")
        
        return self
    
    @model_validator(mode='after')
    def validate_sale_price(self):
        """Validate sale_price is less than regular price if set."""
        if self.sale_price is not None and self.price is not None:
            if self.sale_price >= self.price:
                raise ValueError("sale_price must be less than regular price")
        
        return self
    
    @model_validator(mode='after')
    def validate_cost_price(self):
        """Validate cost is less than price if both are set."""
        if self.cost is not None and self.price is not None:
            if self.cost > self.price:
                # This is a warning rather than an error
                self._cost_warning = "Cost is greater than price"
        
        return self
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        """Validate tags: no duplicates, no empty strings."""
        if v is not None:
            # Remove duplicates
            v = list(set(v))
            
            # Remove empty strings
            v = [tag for tag in v if tag.strip()]
            
            # Validate tag format
            for tag in v:
                if not tag.isalnum() and not all(c.isalnum() or c == '-' for c in tag):
                    raise ValueError(f"Tag '{tag}' contains invalid characters")
        
        return v
    
    @computed_field
    @property
    def is_on_sale(self) -> bool:
        """Determine if the product is currently on sale."""
        if self.sale_price is None:
            return False
        
        today = date.today()
        
        if self.sale_start_date and today < self.sale_start_date:
            return False
        
        if self.sale_end_date and today > self.sale_end_date:
            return False
        
        return True
    
    @computed_field
    @property
    def current_price(self) -> Decimal:
        """Get the current price, considering sales."""
        if self.is_on_sale and self.sale_price is not None:
            return self.sale_price
        return self.price
    
    @computed_field
    @property
    def margin(self) -> Optional[Decimal]:
        """Calculate the profit margin if cost is available."""
        if self.cost is None or self.price is None or self.cost == 0:
            return None
        
        margin = (self.price - self.cost) / self.price
        return round(margin * 100, 2)  # Return as percentage with 2 decimal places
    
    @computed_field
    @property
    def available_inventory(self) -> int:
        """Calculate the available inventory."""
        # In a real application, this would subtract reserved inventory
        return max(0, self.inventory_count)


class ProductCreateSchema(ProductBaseSchema):
    """Schema for creating products."""
    
    class Config:
        """Schema configuration for create operations."""
        extra = "forbid"  # No extra fields allowed


class ProductUpdateSchema(ProductBaseSchema):
    """Schema for updating products."""
    
    # All fields are optional for updates
    name: Optional[str] = Field(None, min_length=3, max_length=255)
    sku: Optional[str] = Field(None, pattern=r"^[A-Z]{3}-\d{5}$")
    price: Optional[Decimal] = Field(None, gt=0)
    category: Optional[ProductCategory] = None
    
    class Config:
        """Schema configuration for update operations."""
        extra = "forbid"  # No extra fields allowed


class ProductViewSchema(ProductBaseSchema):
    """Schema for viewing products."""
    
    id: str  # ID is required for view schema
    
    class Config:
        """Schema configuration for view operations."""
        extra = "ignore"  # Ignore extra fields


class ProductListSchema(UnoSchema):
    """Schema for listing products."""
    
    id: str
    name: str
    price: Decimal
    category: ProductCategory
    inventory_count: int
    status: ProductStatus
    is_on_sale: bool
    current_price: Decimal


# ===== TEST FIXTURES =====

@pytest.fixture
def valid_product_data():
    """Fixture for valid product data."""
    return {
        "id": "prod-123",
        "name": "Test Product",
        "description": "A test product for schema validation",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "cost": Decimal("15.00"),
        "category": "electronics",
        "weight": 1.5,
        "dimensions": {
            "length": 10.0,
            "width": 5.0,
            "height": 2.0,
            "unit": "cm"
        },
        "tags": ["test", "product", "electronics"],
        "manufacturer": "Test Company",
        "status": "published",
        "inventory_count": 100,
        "min_order_quantity": 1,
        "max_order_quantity": 10,
        "is_taxable": True,
        "tax_code": "TX-001",
        "barcode": "123456789012",
        "images": [
            {
                "url": "https://example.com/image1.jpg",
                "alt_text": "Main product image",
                "is_primary": True
            },
            {
                "url": "https://example.com/image2.jpg",
                "alt_text": "Secondary product image"
            }
        ],
        "reviews": [
            {
                "user_id": "user-1",
                "rating": 5,
                "comment": "Great product!"
            },
            {
                "user_id": "user-2",
                "rating": 4,
                "comment": "Good product, but a bit expensive"
            }
        ],
        "price_range": {
            "min_price": Decimal("29.99"),
            "max_price": Decimal("39.99"),
            "currency": "USD"
        },
        "metadata": {
            "featured": True,
            "seo_keywords": "test, product, electronics"
        },
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "published_at": datetime.now(),
        "sale_start_date": date.today(),
        "sale_end_date": date.today() + timedelta(days=30),
        "sale_price": Decimal("24.99"),
        "available_colors": ["red", "blue", "green"],
        "available_sizes": ["S", "M", "L", "XL"],
        "warehouse_inventory": {
            "warehouse-1": 50,
            "warehouse-2": 50
        }
    }


@pytest.fixture
def product_schema_manager():
    """Fixture for product schema manager."""
    # Create a schema manager with our test schemas
    manager = UnoSchemaManager()
    
    # Register schemas
    manager.register_schema("create_schema", ProductCreateSchema)
    manager.register_schema("update_schema", ProductUpdateSchema)
    manager.register_schema("view_schema", ProductViewSchema)
    manager.register_schema("list_schema", ProductListSchema)
    
    return manager


# ===== TESTS FOR COMPLEX VALIDATION SCENARIOS =====

def test_nested_object_validation(valid_product_data):
    """Test validation of nested objects."""
    # Valid nested object
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert isinstance(product.dimensions, ProductDimensions)
    assert product.dimensions.volume == 10.0 * 5.0 * 2.0
    
    # Invalid nested object (min_price > max_price)
    invalid_data = valid_product_data.copy()
    invalid_data["price_range"]["min_price"] = Decimal("50.00")
    invalid_data["price_range"]["max_price"] = Decimal("40.00")
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "min_price must be less than or equal to max_price" in str(excinfo.value)
    
    # Missing required field in nested object
    invalid_data = valid_product_data.copy()
    invalid_data["dimensions"] = {"width": 5.0, "height": 2.0, "unit": "cm"}  # Missing length
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "dimensions -> length" in str(excinfo.value)


def test_collection_validation(valid_product_data):
    """Test validation of collections (lists, sets, dictionaries)."""
    # Valid collections
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert len(product.tags) == 3
    assert len(product.images) == 2
    assert len(product.reviews) == 2
    assert len(product.available_colors) == 3
    assert len(product.available_sizes) == 4
    assert len(product.warehouse_inventory) == 2
    
    # Test list with too many items
    invalid_data = valid_product_data.copy()
    invalid_data["tags"] = ["tag" + str(i) for i in range(15)]  # 15 tags (max is 10)
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "tags" in str(excinfo.value)
    assert "maximum" in str(excinfo.value)
    
    # Test list with invalid items
    invalid_data = valid_product_data.copy()
    invalid_data["reviews"] = [
        {"user_id": "user-1", "rating": 6, "comment": "Invalid rating"}  # Rating > 5
    ]
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "reviews -> 0 -> rating" in str(excinfo.value)
    assert "Rating must be between 1 and 5" in str(excinfo.value)
    
    # Test tag validation (no duplicates, no empty strings, valid characters)
    invalid_data = valid_product_data.copy()
    invalid_data["tags"] = ["test", "test", "", "invalid tag!"]
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "tags" in str(excinfo.value)
    assert "invalid characters" in str(excinfo.value)


def test_interdependent_field_validation(valid_product_data):
    """Test validation involving multiple fields."""
    # Valid interdependent fields
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert product.min_order_quantity < product.max_order_quantity
    assert product.sale_start_date < product.sale_end_date
    assert product.sale_price < product.price
    
    # Invalid min/max order quantity
    invalid_data = valid_product_data.copy()
    invalid_data["min_order_quantity"] = 20
    invalid_data["max_order_quantity"] = 10
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "min_order_quantity must be less than or equal to max_order_quantity" in str(excinfo.value)
    
    # Invalid sale dates
    invalid_data = valid_product_data.copy()
    invalid_data["sale_start_date"] = date.today() + timedelta(days=10)
    invalid_data["sale_end_date"] = date.today()
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "sale_start_date must be before sale_end_date" in str(excinfo.value)
    
    # Invalid sale price
    invalid_data = valid_product_data.copy()
    invalid_data["sale_price"] = Decimal("39.99")  # Greater than regular price
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "sale_price must be less than regular price" in str(excinfo.value)


def test_computed_fields_validation(valid_product_data):
    """Test validation of computed fields."""
    # Create a product
    product = ProductViewSchema(**valid_product_data)
    
    # Test is_on_sale
    assert product.is_on_sale is True
    
    # Test current_price
    assert product.current_price == Decimal("24.99")
    
    # Test margin
    assert product.margin is not None
    assert product.margin == Decimal("49.98")  # (29.99 - 15.00) / 29.99 * 100
    
    # Test available_inventory
    assert product.available_inventory == 100
    
    # Test with different sale dates
    past_sale = valid_product_data.copy()
    past_sale["sale_start_date"] = date.today() - timedelta(days=30)
    past_sale["sale_end_date"] = date.today() - timedelta(days=1)
    
    past_product = ProductViewSchema(**past_sale)
    assert past_product.is_on_sale is False
    assert past_product.current_price == Decimal("29.99")  # Regular price
    
    # Test with no cost defined
    no_cost = valid_product_data.copy()
    no_cost["cost"] = None
    
    no_cost_product = ProductViewSchema(**no_cost)
    assert no_cost_product.margin is None


def test_enum_validation(valid_product_data):
    """Test validation of enum fields."""
    # Valid enum values
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert product.category == ProductCategory.ELECTRONICS
    assert product.status == ProductStatus.PUBLISHED
    
    # Invalid category
    invalid_data = valid_product_data.copy()
    invalid_data["category"] = "invalid-category"
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "category" in str(excinfo.value)
    
    # Invalid status
    invalid_data = valid_product_data.copy()
    invalid_data["status"] = "invalid-status"
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "status" in str(excinfo.value)


def test_literal_validation(valid_product_data):
    """Test validation of literal fields."""
    # Valid literal values
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert product.dimensions.unit == "cm"
    
    # Invalid unit
    invalid_data = valid_product_data.copy()
    invalid_data["dimensions"]["unit"] = "m"  # Not in ["cm", "in"]
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "dimensions -> unit" in str(excinfo.value)


def test_pattern_validation(valid_product_data):
    """Test validation of pattern fields."""
    # Valid pattern
    valid_data = valid_product_data.copy()
    product = ProductViewSchema(**valid_data)
    assert product.sku == "TST-12345"
    
    # Invalid SKU format
    invalid_data = valid_product_data.copy()
    invalid_data["sku"] = "INVALID-SKU"
    
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductViewSchema(**invalid_data)
    
    assert "sku" in str(excinfo.value)
    assert "pattern" in str(excinfo.value)


def test_conditional_validation():
    """Test conditional validation rules."""
    # Test conditional validation based on status
    data = {
        "id": "prod-123",
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics",
        "status": "published",  # Published status requires published_at
        "published_at": None  # Missing published_at
    }
    
    # Create a custom validator for this test
    class ConditionalSchema(ProductViewSchema):
        @model_validator(mode='after')
        def validate_published_status(self):
            """Validate that published products have a published_at date."""
            if self.status == ProductStatus.PUBLISHED and not self.published_at:
                raise ValueError("published_at is required for published products")
            return self
    
    # Test validation failure
    with pytest.raises(PydanticValidationError) as excinfo:
        ConditionalSchema(**data)
    
    assert "published_at is required for published products" in str(excinfo.value)
    
    # Fix the data and test again
    data["published_at"] = datetime.now()
    product = ConditionalSchema(**data)
    assert product.status == ProductStatus.PUBLISHED
    assert product.published_at is not None


def test_schema_with_extra_fields():
    """Test schema behavior with extra fields."""
    # Data with extra fields
    data = {
        "id": "prod-123",
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics",
        "extra_field_1": "extra value 1",
        "extra_field_2": "extra value 2"
    }
    
    # Test create schema - should reject extra fields
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductCreateSchema(**data)
    
    assert "extra fields" in str(excinfo.value)
    
    # Test update schema - should reject extra fields
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductUpdateSchema(**data)
    
    assert "extra fields" in str(excinfo.value)
    
    # Test view schema - should ignore extra fields
    product = ProductViewSchema(**data)
    assert product.name == "Test Product"
    assert not hasattr(product, "extra_field_1")


def test_schema_with_missing_fields():
    """Test schema behavior with missing required fields."""
    # Data with missing required fields
    data = {
        "id": "prod-123",
        "name": "Test Product",
        # Missing sku
        # Missing price
        "category": "electronics"
    }
    
    # Test create schema - should reject missing required fields
    with pytest.raises(PydanticValidationError) as excinfo:
        ProductCreateSchema(**data)
    
    assert "sku" in str(excinfo.value)
    assert "price" in str(excinfo.value)
    
    # Test update schema - should accept missing fields (all are optional)
    product = ProductUpdateSchema(**data)
    assert product.name == "Test Product"
    assert product.sku is None
    assert product.price is None
    
    # Test with completely empty data
    empty_data = {}
    
    # Create schema should fail
    with pytest.raises(PydanticValidationError):
        ProductCreateSchema(**empty_data)
    
    # Update schema should succeed (all fields are optional)
    product = ProductUpdateSchema(**empty_data)
    assert product.name is None
    assert product.price is None


def test_schema_inheritance():
    """Test schema inheritance and validation."""
    # Create a schema that inherits from ProductBaseSchema
    class SpecialProductSchema(ProductBaseSchema):
        """Special product schema with additional fields."""
        
        special_feature: str
        is_limited_edition: bool = False
        limited_quantity: Optional[int] = None
        
        @model_validator(mode='after')
        def validate_limited_edition(self):
            """Validate limited edition products have a quantity."""
            if self.is_limited_edition and self.limited_quantity is None:
                raise ValueError("limited_quantity is required for limited edition products")
            return self
    
    # Valid data
    data = {
        "name": "Special Product",
        "sku": "SPL-12345",
        "price": Decimal("99.99"),
        "category": "electronics",
        "special_feature": "Unique feature",
        "is_limited_edition": True,
        "limited_quantity": 100
    }
    
    # Test valid data
    product = SpecialProductSchema(**data)
    assert product.name == "Special Product"
    assert product.special_feature == "Unique feature"
    assert product.is_limited_edition is True
    assert product.limited_quantity == 100
    
    # Test invalid data (missing limited_quantity)
    invalid_data = data.copy()
    invalid_data["limited_quantity"] = None
    
    with pytest.raises(PydanticValidationError) as excinfo:
        SpecialProductSchema(**invalid_data)
    
    assert "limited_quantity is required for limited edition products" in str(excinfo.value)


def test_schema_manager_integration(product_schema_manager, valid_product_data):
    """Test integration with UnoSchemaManager."""
    # Get schemas from manager
    create_schema = product_schema_manager.get_schema("create_schema")
    update_schema = product_schema_manager.get_schema("update_schema")
    view_schema = product_schema_manager.get_schema("view_schema")
    list_schema = product_schema_manager.get_schema("list_schema")
    
    # Make sure schemas were registered and retrieved correctly
    assert create_schema == ProductCreateSchema
    assert update_schema == ProductUpdateSchema
    assert view_schema == ProductViewSchema
    assert list_schema == ProductListSchema
    
    # Test creating with create schema
    create_data = valid_product_data.copy()
    del create_data["id"]  # ID not needed for create
    
    product = create_schema(**create_data)
    assert product.name == "Test Product"
    
    # Test creating view schema
    view_data = valid_product_data.copy()
    product = view_schema(**view_data)
    assert product.id == "prod-123"
    
    # Test list schema with minimal data
    list_data = {
        "id": "prod-123",
        "name": "Test Product",
        "price": Decimal("29.99"),
        "category": "electronics",
        "inventory_count": 100,
        "status": "published",
        "is_on_sale": True,
        "current_price": Decimal("24.99")
    }
    
    product = list_schema(**list_data)
    assert product.id == "prod-123"
    assert product.name == "Test Product"
    assert product.current_price == Decimal("24.99")


def test_create_list_schema():
    """Test creation of list schemas."""
    # Create a list schema from ProductViewSchema
    list_schema = create_list_schema(ProductViewSchema)
    
    # Check that it's a valid Pydantic model class
    assert issubclass(list_schema, BaseModel)
    
    # Check that it contains a list field
    assert hasattr(list_schema, "root")
    assert list_schema.__annotations__["root"] == List[ProductViewSchema]
    
    # Test instance with a list of products
    products = [
        ProductViewSchema(**{
            "id": f"prod-{i}",
            "name": f"Product {i}",
            "sku": f"TST-{i:05d}",
            "price": Decimal("10.99"),
            "category": "electronics",
            "status": "published"
        })
        for i in range(1, 4)
    ]
    
    product_list = list_schema(root=products)
    assert len(product_list.root) == 3
    assert product_list.root[0].id == "prod-1"
    assert product_list.root[1].name == "Product 2"
    assert product_list.root[2].sku == "TST-00003"


def test_extract_fields_from_schema():
    """Test extracting fields from a schema."""
    # Extract fields from ProductViewSchema
    fields = extract_fields_from_schema(ProductViewSchema)
    
    # Check that fields were extracted correctly
    assert "name" in fields
    assert "price" in fields
    assert "category" in fields
    assert "dimensions" in fields
    
    # Check field properties
    assert fields["name"].annotation == str
    assert fields["price"].annotation == Decimal
    assert "min_length" in fields["name"].json_schema_extra
    assert "gt" in fields["price"].json_schema_extra


def test_validation_error_handling():
    """Test handling of validation errors."""
    # Data with multiple validation errors
    invalid_data = {
        "id": "prod-123",
        "name": "Te",  # Too short
        "sku": "invalid-sku",  # Invalid format
        "price": Decimal("-10.99"),  # Negative price
        "category": "invalid-category",  # Invalid category
        "min_order_quantity": 10,
        "max_order_quantity": 5  # min > max
    }
    
    # Get validation errors
    try:
        ProductViewSchema(**invalid_data)
        assert False, "Validation should have failed"
    except PydanticValidationError as e:
        errors = e.errors()
        
        # Check that all expected errors were caught
        error_fields = [error["loc"][0] for error in errors]
        assert "name" in error_fields
        assert "sku" in error_fields
        assert "price" in error_fields
        assert "category" in error_fields
        
        # Also check for the model validator error
        model_errors = [error for error in errors if len(error["loc"]) == 0]
        assert len(model_errors) > 0, "Model validator error not found"
        assert any("min_order_quantity" in error["msg"] for error in model_errors)


def test_schema_with_default_values():
    """Test schemas with default values."""
    # Minimal data, let defaults take effect
    data = {
        "id": "prod-123",
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics"
    }
    
    # Create product with defaults
    product = ProductViewSchema(**data)
    
    # Check default values
    assert product.status == ProductStatus.DRAFT
    assert product.inventory_count == 0
    assert product.is_taxable is True
    assert product.tags is None


def test_schema_serialization():
    """Test schema serialization to JSON."""
    # Create a product
    product = ProductViewSchema(**{
        "id": "prod-123",
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics",
        "dimensions": {
            "length": 10.0,
            "width": 5.0,
            "height": 2.0,
            "unit": "cm"
        },
        "sale_price": Decimal("24.99"),
        "sale_start_date": date.today(),
        "sale_end_date": date.today() + timedelta(days=30)
    })
    
    # Serialize to JSON
    json_data = json.loads(product.model_dump_json())
    
    # Check serialized data
    assert json_data["id"] == "prod-123"
    assert json_data["name"] == "Test Product"
    assert json_data["sku"] == "TST-12345"
    assert json_data["price"] == "29.99"
    assert json_data["category"] == "electronics"
    assert json_data["dimensions"]["length"] == 10.0
    assert json_data["is_on_sale"] is True
    assert json_data["current_price"] == "24.99"
    
    # Check that dates were serialized correctly
    assert json_data["sale_start_date"] == date.today().isoformat()
    assert json_data["sale_end_date"] == (date.today() + timedelta(days=30)).isoformat()


def test_model_to_schema_conversion():
    """Test conversion from UnoModel to schema."""
    # Create a product model instance
    model = ProductModel()
    model.id = "prod-123"
    model.name = "Test Product"
    model.sku = "TST-12345"
    model.price = Decimal("29.99")
    model.category = "electronics"
    model.status = "published"
    model.inventory_count = 100
    model.created_at = datetime.now()
    model.updated_at = datetime.now()
    
    # Convert model to view schema
    product = ProductViewSchema.model_validate(model.__dict__)
    
    # Check converted data
    assert product.id == "prod-123"
    assert product.name == "Test Product"
    assert product.sku == "TST-12345"
    assert product.price == Decimal("29.99")
    assert product.category == ProductCategory.ELECTRONICS
    assert product.status == ProductStatus.PUBLISHED
    assert product.inventory_count == 100


def test_schema_to_model_conversion():
    """Test conversion from schema to UnoModel."""
    # Create a product schema instance
    schema = ProductCreateSchema(
        name="Test Product",
        sku="TST-12345",
        price=Decimal("29.99"),
        category=ProductCategory.ELECTRONICS,
        status=ProductStatus.DRAFT,
        inventory_count=100
    )
    
    # Convert schema to model
    model_data = schema.model_dump()
    model = ProductModel()
    
    # Set model attributes from schema
    for key, value in model_data.items():
        if hasattr(model, key):
            setattr(model, key, value)
    
    # Check converted data
    assert model.name == "Test Product"
    assert model.sku == "TST-12345"
    assert model.price == Decimal("29.99")
    assert model.category == "electronics"  # Enum converted to string
    assert model.status == "draft"  # Enum converted to string
    assert model.inventory_count == 100


# ===== ADVANCED VALIDATION TESTS =====

def test_custom_validation_context():
    """Test custom validation context with UnoError integration."""
    # Create a function to validate with custom context
    def validate_with_context(data):
        context = ValidationContext()
        
        # Validate name
        if "name" not in data or not data["name"]:
            context.add_error(
                field="name",
                message="Name is required",
                error_code="MISSING_NAME"
            )
        elif len(data["name"]) < 3:
            context.add_error(
                field="name",
                message="Name must be at least 3 characters",
                error_code="NAME_TOO_SHORT"
            )
        
        # Validate price
        if "price" not in data:
            context.add_error(
                field="price",
                message="Price is required",
                error_code="MISSING_PRICE"
            )
        elif data["price"] <= 0:
            context.add_error(
                field="price",
                message="Price must be greater than 0",
                error_code="INVALID_PRICE",
                details={"provided_price": data["price"]}
            )
        
        # Validate SKU
        if "sku" in data and data["sku"]:
            sku_pattern = r"^[A-Z]{3}-\d{5}$"
            if not re.match(sku_pattern, data["sku"]):
                context.add_error(
                    field="sku",
                    message="SKU must follow pattern ABC-12345",
                    error_code="INVALID_SKU_FORMAT"
                )
        
        return context
    
    # Test valid data
    valid_data = {
        "name": "Test Product",
        "price": Decimal("29.99"),
        "sku": "TST-12345"
    }
    
    context = validate_with_context(valid_data)
    assert not context.has_errors()
    
    # Test invalid data
    invalid_data = {
        "name": "Te",
        "price": Decimal("-10.99"),
        "sku": "invalid-sku"
    }
    
    context = validate_with_context(invalid_data)
    assert context.has_errors()
    assert len(context.errors) == 3
    
    # Check error details
    name_error = next(e for e in context.errors if e["field"] == "name")
    price_error = next(e for e in context.errors if e["field"] == "price")
    sku_error = next(e for e in context.errors if e["field"] == "sku")
    
    assert name_error["message"] == "Name must be at least 3 characters"
    assert name_error["error_code"] == "NAME_TOO_SHORT"
    
    assert price_error["message"] == "Price must be greater than 0"
    assert price_error["error_code"] == "INVALID_PRICE"
    assert price_error["details"]["provided_price"] == Decimal("-10.99")
    
    assert sku_error["message"] == "SKU must follow pattern ABC-12345"
    assert sku_error["error_code"] == "INVALID_SKU_FORMAT"
    
    # Convert validation context to UnoError
    try:
        if context.has_errors():
            raise ValidationError(
                message="Validation failed",
                error_code=ErrorCode.VALIDATION_ERROR,
                validation_errors=context.errors
            )
        
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert str(e) == "Validation failed"
        assert e.error_code == ErrorCode.VALIDATION_ERROR
        assert len(e.validation_errors) == 3


def test_advanced_schema_configuration():
    """Test advanced schema configuration options."""
    # Define a schema config with complex options
    config = UnoSchemaConfig(
        schema_class=ProductBaseSchema,
        include_fields={"id", "name", "price", "category", "status", "inventory_count"},
        exclude_fields={"created_at", "updated_at"}
    )
    
    # Create schema class with config
    schema_class = create_schema_class("AdvancedSchema", config)
    
    # Check schema class structure
    assert issubclass(schema_class, ProductBaseSchema)
    assert "id" in schema_class.__annotations__
    assert "name" in schema_class.__annotations__
    assert "price" in schema_class.__annotations__
    assert "category" in schema_class.__annotations__
    assert "status" in schema_class.__annotations__
    assert "inventory_count" in schema_class.__annotations__
    
    # Excluded fields should not be present
    assert "created_at" not in schema_class.__annotations__
    assert "updated_at" not in schema_class.__annotations__
    
    # Fields not in the include list should not be present
    assert "description" not in schema_class.__annotations__
    assert "sku" not in schema_class.__annotations__
    
    # Test instance with valid data
    instance = schema_class(
        id="prod-123",
        name="Test Product",
        price=Decimal("29.99"),
        category=ProductCategory.ELECTRONICS,
        status=ProductStatus.PUBLISHED,
        inventory_count=100
    )
    
    assert instance.id == "prod-123"
    assert instance.name == "Test Product"
    assert instance.price == Decimal("29.99")


def test_error_handling_with_uno_error():
    """Test integrating schema validation with UnoError system."""
    # Function to validate and convert Pydantic errors to UnoError
    def validate_schema(data):
        try:
            # Try to validate with Pydantic
            return ProductCreateSchema(**data)
        except PydanticValidationError as e:
            # Convert Pydantic errors to ValidationContext
            context = ValidationContext()
            
            for error in e.errors():
                field = ".".join(str(loc) for loc in error["loc"]) if error["loc"] else None
                message = error["msg"]
                type_error = error["type"]
                
                # Map Pydantic error types to UnoError codes
                if type_error == "value_error.missing":
                    error_code = "MISSING_FIELD"
                elif type_error.startswith("type_error"):
                    error_code = "TYPE_ERROR"
                elif type_error.startswith("value_error.number"):
                    error_code = "NUMBER_ERROR"
                elif type_error.startswith("value_error.str"):
                    error_code = "STRING_ERROR"
                elif type_error.startswith("enum"):
                    error_code = "ENUM_ERROR"
                else:
                    error_code = "VALIDATION_ERROR"
                
                context.add_error(
                    field=field,
                    message=message,
                    error_code=error_code,
                    details={"pydantic_error_type": type_error}
                )
            
            # Raise ValidationError
            raise ValidationError(
                message="Schema validation failed",
                error_code=ErrorCode.VALIDATION_ERROR,
                validation_errors=context.errors
            )
    
    # Test valid data
    valid_data = {
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics"
    }
    
    product = validate_schema(valid_data)
    assert product.name == "Test Product"
    
    # Test invalid data
    invalid_data = {
        "name": "Te",  # Too short
        "sku": "invalid-sku",  # Invalid format
        "price": Decimal("-10.99"),  # Negative price
        "category": "invalid-category"  # Invalid category
    }
    
    try:
        validate_schema(invalid_data)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        # Check that errors were properly converted
        assert e.error_code == ErrorCode.VALIDATION_ERROR
        assert len(e.validation_errors) > 0
        
        # Check for specific validation errors
        field_errors = {error["field"]: error for error in e.validation_errors if error["field"]}
        
        assert "name" in field_errors
        assert field_errors["name"]["error_code"] == "STRING_ERROR"
        
        assert "sku" in field_errors
        assert field_errors["sku"]["error_code"] == "STRING_ERROR"
        
        assert "price" in field_errors
        assert field_errors["price"]["error_code"] == "NUMBER_ERROR"
        
        assert "category" in field_errors
        assert field_errors["category"]["error_code"] == "ENUM_ERROR"


def test_schema_validation_with_custom_error_formatter():
    """Test schema validation with custom error formatting."""
    
    # Create a custom error formatter
    class CustomErrorFormatter:
        """Custom error formatter for schema validation errors."""
        
        @staticmethod
        def format_validation_error(error_list):
            """Format Pydantic validation errors into a structured response."""
            formatted_errors = []
            
            for error in error_list:
                field_path = " -> ".join(str(loc) for loc in error["loc"]) if error["loc"] else "schema"
                error_type = error["type"]
                message = error["msg"]
                
                formatted_error = {
                    "field": field_path,
                    "error_type": error_type,
                    "message": message,
                    "user_message": f"Error in field '{field_path}': {message}"
                }
                
                # Add additional context based on error type
                if error_type == "value_error.missing":
                    formatted_error["severity"] = "critical"
                    formatted_error["suggestion"] = f"Please provide a value for '{field_path}'"
                elif error_type.startswith("type_error"):
                    formatted_error["severity"] = "error"
                    formatted_error["suggestion"] = "Please provide a value of the correct type"
                elif "greater_than" in error_type or "less_than" in error_type:
                    formatted_error["severity"] = "error"
                    formatted_error["suggestion"] = "Please provide a value within the allowed range"
                elif "string" in error_type:
                    formatted_error["severity"] = "warning"
                    formatted_error["suggestion"] = "Please check the format of this text field"
                else:
                    formatted_error["severity"] = "error"
                    formatted_error["suggestion"] = "Please check this field and try again"
                
                formatted_errors.append(formatted_error)
            
            return {
                "error_count": len(formatted_errors),
                "errors": formatted_errors,
                "has_critical": any(e["severity"] == "critical" for e in formatted_errors),
                "summary": f"Validation failed with {len(formatted_errors)} errors"
            }
    
    # Function to validate with custom error formatting
    def validate_with_formatting(data, schema_class):
        try:
            instance = schema_class(**data)
            return {"valid": True, "data": instance.model_dump(), "errors": None}
        except PydanticValidationError as e:
            return {
                "valid": False,
                "data": None,
                "errors": CustomErrorFormatter.format_validation_error(e.errors())
            }
    
    # Test valid data
    valid_data = {
        "id": "prod-123",
        "name": "Test Product",
        "sku": "TST-12345",
        "price": Decimal("29.99"),
        "category": "electronics",
        "status": "published"
    }
    
    result = validate_with_formatting(valid_data, ProductViewSchema)
    assert result["valid"] is True
    assert result["data"]["name"] == "Test Product"
    assert result["errors"] is None
    
    # Test invalid data with multiple errors
    invalid_data = {
        "id": "prod-123",
        "name": "Te",  # Too short
        "sku": "invalid-sku",  # Invalid format
        "price": Decimal("-10.99"),  # Negative price
        "category": "invalid-category",  # Invalid category
        "min_order_quantity": 10,
        "max_order_quantity": 5  # min > max
    }
    
    result = validate_with_formatting(invalid_data, ProductViewSchema)
    assert result["valid"] is False
    assert result["data"] is None
    assert result["errors"] is not None
    
    # Check error format
    errors = result["errors"]
    assert errors["error_count"] >= 5
    assert "has_critical" in errors
    assert "summary" in errors
    assert "errors" in errors
    
    # Check individual errors
    error_messages = [e["message"] for e in errors["errors"]]
    assert any("at least 3" in msg for msg in error_messages)  # Name too short
    assert any("pattern" in msg for msg in error_messages)  # Invalid SKU
    assert any("greater than" in msg for msg in error_messages)  # Negative price
    assert any("enum" in msg or "valid" in msg for msg in error_messages)  # Invalid category
    assert any("min_order_quantity" in msg for msg in error_messages)  # min > max
    
    # Check that suggestions are included
    assert all("suggestion" in e for e in errors["errors"])
    assert all("severity" in e for e in errors["errors"])
    assert all("user_message" in e for e in errors["errors"])


def test_recursive_schema_validation():
    """Test validation of recursive schemas."""
    
    # Define recursive schemas (e.g., for category hierarchies or comment threads)
    class CategorySchema(UnoSchema):
        """Schema for categories with recursive structure."""
        id: str
        name: str
        description: Optional[str] = None
        parent_id: Optional[str] = None
        subcategories: Optional[List['CategorySchema']] = None
        
        @model_validator(mode='after')
        def validate_hierarchy(self):
            """Validate that a category doesn't reference itself as parent."""
            if self.parent_id == self.id:
                raise ValueError("Category cannot be its own parent")
            
            # Check for circular references in subcategories
            if self.subcategories:
                category_ids = {self.id}
                
                def check_circular_refs(category, id_set):
                    if category.parent_id in id_set:
                        raise ValueError(f"Circular reference detected: {category.id} -> {category.parent_id}")
                    
                    if category.subcategories:
                        for subcat in category.subcategories:
                            # Add current category ID
                            new_id_set = id_set.copy()
                            new_id_set.add(category.id)
                            check_circular_refs(subcat, new_id_set)
                
                for subcat in self.subcategories:
                    check_circular_refs(subcat, category_ids)
            
            return self
    
    # Create test data
    valid_category = {
        "id": "cat-1",
        "name": "Electronics",
        "subcategories": [
            {
                "id": "cat-2",
                "name": "Computers",
                "parent_id": "cat-1",
                "subcategories": [
                    {
                        "id": "cat-3",
                        "name": "Laptops",
                        "parent_id": "cat-2"
                    },
                    {
                        "id": "cat-4",
                        "name": "Desktops",
                        "parent_id": "cat-2"
                    }
                ]
            },
            {
                "id": "cat-5",
                "name": "Smartphones",
                "parent_id": "cat-1"
            }
        ]
    }
    
    # Test valid hierarchy
    category = CategorySchema(**valid_category)
    assert category.id == "cat-1"
    assert category.name == "Electronics"
    assert len(category.subcategories) == 2
    assert category.subcategories[0].subcategories[0].name == "Laptops"
    
    # Test self-reference
    invalid_category = valid_category.copy()
    invalid_category["parent_id"] = "cat-1"  # Self-reference
    
    with pytest.raises(PydanticValidationError) as excinfo:
        CategorySchema(**invalid_category)
    
    assert "Category cannot be its own parent" in str(excinfo.value)
    
    # Test circular reference
    invalid_category = valid_category.copy()
    # Create circular reference: cat-1 -> cat-2 -> cat-3 -> cat-1
    invalid_category["subcategories"][0]["subcategories"][0]["subcategories"] = [
        {
            "id": "cat-6",
            "name": "Circular Ref",
            "parent_id": "cat-3",
            "subcategories": [
                {
                    "id": "cat-7",
                    "name": "Deep Circular Ref",
                    "parent_id": "cat-6",
                    "subcategories": [
                        {
                            "id": "cat-1",  # Circular reference back to the root
                            "name": "Electronics",
                            "parent_id": "cat-7"
                        }
                    ]
                }
            ]
        }
    ]
    
    with pytest.raises(PydanticValidationError) as excinfo:
        CategorySchema(**invalid_category)
    
    assert "Circular reference detected" in str(excinfo.value)


def test_schema_validation_with_contextual_rules():
    """Test schema validation with context-dependent rules."""
    
    class OrderContextSchema(UnoSchema):
        """Order schema with context-dependent validation."""
        customer_id: str
        items: List[dict]
        shipping_address: dict
        billing_address: Optional[dict] = None
        payment_method: str
        shipping_method: str
        total_amount: Decimal
        currency: str = "USD"
        context: Dict[str, Any] = {}  # Contextual information
        
        @model_validator(mode='after')
        def validate_with_context(self):
            """Apply validation rules based on context."""
            # Get context variables
            country = self.shipping_address.get("country", "")
            is_international = country != "US"
            is_high_value = self.total_amount > Decimal("1000")
            payment_type = self.payment_method.split("_")[0] if "_" in self.payment_method else self.payment_method
            
            # Store context for future use
            self.context["is_international"] = is_international
            self.context["is_high_value"] = is_high_value
            self.context["payment_type"] = payment_type
            
            # Validation rule: International high-value orders require additional verification
            if is_international and is_high_value:
                self.context["requires_verification"] = True
                
                # Billing address is required for high-value international orders
                if not self.billing_address:
                    raise ValueError("Billing address is required for high-value international orders")
            else:
                self.context["requires_verification"] = False
            
            # Validation rule: Cash payment not allowed for international shipping
            if is_international and payment_type == "cash":
                raise ValueError("Cash payment is not accepted for international shipping")
            
            # Validation rule: Certain payment methods require billing address
            card_payment_types = ["credit", "debit"]
            if payment_type in card_payment_types and not self.billing_address:
                raise ValueError(f"{payment_type.capitalize()} card payments require billing address")
            
            # Validation rule: Express shipping required for perishable items
            has_perishable = any(item.get("is_perishable", False) for item in self.items)
            self.context["has_perishable"] = has_perishable
            
            if has_perishable and self.shipping_method != "express":
                raise ValueError("Express shipping is required for orders with perishable items")
            
            return self
    
    # Test valid order
    valid_order = {
        "customer_id": "cust-123",
        "items": [
            {"id": "item-1", "name": "Standard Item", "price": "29.99", "quantity": 2}
        ],
        "shipping_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "country": "US",
            "postal_code": "12345"
        },
        "payment_method": "credit_card",
        "billing_address": {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "country": "US",
            "postal_code": "12345"
        },
        "shipping_method": "standard",
        "total_amount": Decimal("59.98")
    }
    
    order = OrderContextSchema(**valid_order)
    assert order.context["is_international"] is False
    assert order.context["is_high_value"] is False
    assert order.context["payment_type"] == "credit"
    assert order.context["requires_verification"] is False
    assert order.context["has_perishable"] is False
    
    # Test international high-value order without billing address
    invalid_order = valid_order.copy()
    invalid_order["shipping_address"]["country"] = "UK"
    invalid_order["total_amount"] = Decimal("1500.00")
    invalid_order["billing_address"] = None
    
    with pytest.raises(PydanticValidationError) as excinfo:
        OrderContextSchema(**invalid_order)
    
    assert "Billing address is required for high-value international orders" in str(excinfo.value)
    
    # Test international order with cash payment
    invalid_order = valid_order.copy()
    invalid_order["shipping_address"]["country"] = "UK"
    invalid_order["payment_method"] = "cash"
    
    with pytest.raises(PydanticValidationError) as excinfo:
        OrderContextSchema(**invalid_order)
    
    assert "Cash payment is not accepted for international shipping" in str(excinfo.value)
    
    # Test credit card payment without billing address
    invalid_order = valid_order.copy()
    invalid_order["billing_address"] = None
    
    with pytest.raises(PydanticValidationError) as excinfo:
        OrderContextSchema(**invalid_order)
    
    assert "Credit card payments require billing address" in str(excinfo.value)
    
    # Test perishable items without express shipping
    invalid_order = valid_order.copy()
    invalid_order["items"].append({
        "id": "item-2", 
        "name": "Perishable Item", 
        "price": "49.99", 
        "quantity": 1, 
        "is_perishable": True
    })
    
    with pytest.raises(PydanticValidationError) as excinfo:
        OrderContextSchema(**invalid_order)
    
    assert "Express shipping is required for orders with perishable items" in str(excinfo.value)
    
    # Test valid order with all special conditions met
    special_order = invalid_order.copy()
    special_order["shipping_method"] = "express"
    
    order = OrderContextSchema(**special_order)
    assert order.context["has_perishable"] is True