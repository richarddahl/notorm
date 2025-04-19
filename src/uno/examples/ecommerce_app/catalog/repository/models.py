"""
Database models for the catalog context.

This module defines the SQLAlchemy models that represent the database schema
for the catalog context. These models are separate from the domain entities.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    Text,
    DateTime,
    ForeignKey,
    Table,
    JSON,
    Enum,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime, UTC

from uno.domain.base.model import BaseModel

# Base model class
Base = declarative_base()

# Association table for products and categories
product_category_association = Table(
    "catalog_product_category",
    Base.metadata,
    Column("product_id", String(36), ForeignKey("catalog_products.id")),
    Column("category_id", String(36), ForeignKey("catalog_categories.id")),
)


class ProductModel(BaseModel, Base):
    """SQLAlchemy model for products."""

    __tablename__ = "catalog_products"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    sku = Column(String(100), nullable=False, unique=True)
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String(3), default="USD")
    status = Column(String(20), default="draft")

    # Inventory
    inventory_quantity = Column(Integer, default=0)
    inventory_reserved = Column(Integer, default=0)
    inventory_backorderable = Column(Boolean, default=False)
    inventory_restock_threshold = Column(Integer)

    # Physical attributes
    weight_value = Column(Float)
    weight_unit = Column(String(5))

    dimensions_length = Column(Float)
    dimensions_width = Column(Float)
    dimensions_height = Column(Float)
    dimensions_unit = Column(String(5))

    # Attributes and metadata
    attributes = Column(JSON, default={})
    tags = Column(JSON, default=[])
    seo_title = Column(String(255))
    seo_description = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Version for optimistic concurrency
    version = Column(Integer, default=1)

    # Relationships
    variants = relationship(
        "ProductVariantModel", back_populates="product", cascade="all, delete-orphan"
    )
    images = relationship(
        "ProductImageModel", back_populates="product", cascade="all, delete-orphan"
    )
    categories = relationship(
        "CategoryModel",
        secondary=product_category_association,
        back_populates="products",
    )


class ProductVariantModel(BaseModel, Base):
    """SQLAlchemy model for product variants."""

    __tablename__ = "catalog_product_variants"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), ForeignKey("catalog_products.id"), nullable=False)
    sku = Column(String(100), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    price_amount = Column(Float, nullable=False)
    price_currency = Column(String(3), default="USD")

    # Inventory
    inventory_quantity = Column(Integer, default=0)
    inventory_reserved = Column(Integer, default=0)
    inventory_backorderable = Column(Boolean, default=False)
    inventory_restock_threshold = Column(Integer)

    # Attributes
    attributes = Column(JSON, default={})
    is_active = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Relationships
    product = relationship("ProductModel", back_populates="variants")


class ProductImageModel(BaseModel, Base):
    """SQLAlchemy model for product images."""

    __tablename__ = "catalog_product_images"

    id = Column(String(36), primary_key=True)
    product_id = Column(String(36), ForeignKey("catalog_products.id"), nullable=False)
    url = Column(String(255), nullable=False)
    alt_text = Column(String(255))
    sort_order = Column(Integer, default=0)
    is_primary = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Relationships
    product = relationship("ProductModel", back_populates="images")


class CategoryModel(BaseModel, Base):
    """SQLAlchemy model for categories."""

    __tablename__ = "catalog_categories"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    parent_id = Column(String(36), ForeignKey("catalog_categories.id"))
    image_url = Column(String(255))
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(datetime.UTC), onupdate=lambda: datetime.now(datetime.UTC))

    # Relationships
    children = relationship(
        "CategoryModel", backref=relationship("CategoryModel", remote_side=[id])
    )
    products = relationship(
        "ProductModel",
        secondary=product_category_association,
        back_populates="categories",
    )
