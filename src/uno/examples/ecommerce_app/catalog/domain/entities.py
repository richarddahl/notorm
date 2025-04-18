"""
Domain entities for the catalog context.

This module defines the core domain entities for the catalog bounded context,
including products, categories, and related entities.
"""

from typing import List, Dict, Optional, Set, Any
from datetime import datetime, UTC
from decimal import Decimal
import uuid

from pydantic import Field

from uno.domain.core import Entity, AggregateRoot
from uno.core.events import UnoEvent

from uno.examples.ecommerce_app.shared.value_objects import Money
from uno.examples.ecommerce_app.catalog.domain.value_objects import (
    ProductStatus,
    Dimensions,
    Weight,
    Inventory,
)
from uno.examples.ecommerce_app.catalog.domain.events import (
    ProductCreatedEvent,
    ProductUpdatedEvent,
    ProductPriceChangedEvent,
    ProductInventoryUpdatedEvent,
)


class Category(Entity):
    """Category entity for organizing products."""

    name: str
    slug: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

    def update(self) -> None:
        """Update entity timestamp when modified."""
        self.updated_at = datetime.now(UTC)


class ProductImage(Entity):
    """Product image entity."""

    product_id: str
    url: str
    alt_text: Optional[str] = None
    sort_order: int = 0
    is_primary: bool = False

    def update(self) -> None:
        """Update entity timestamp when modified."""
        self.updated_at = datetime.now(UTC)


class ProductVariant(Entity):
    """Product variant entity for products with multiple options."""

    product_id: str
    sku: str
    name: str
    price: Money
    inventory: Inventory = Field(default_factory=lambda: Inventory(quantity=0))
    attributes: Dict[str, str] = Field(default_factory=dict)
    is_active: bool = True

    def update(self) -> None:
        """Update entity timestamp when modified."""
        self.updated_at = datetime.now(UTC)

    def update_inventory(self, new_inventory: Inventory) -> None:
        """Update the inventory for this variant."""
        self.inventory = new_inventory
        self.update()

    def update_price(self, new_price: Money) -> None:
        """Update the price for this variant."""
        self.price = new_price
        self.update()


class Product(AggregateRoot):
    """
    Product aggregate root entity.

    This is the main entity in the catalog context, representing a product
    with its variants, images, and categories.
    """

    name: str
    slug: str
    description: Optional[str] = None
    sku: str
    price: Money
    status: ProductStatus = ProductStatus.DRAFT
    inventory: Inventory = Field(default_factory=lambda: Inventory(quantity=0))

    # Physical attributes
    weight: Optional[Weight] = None
    dimensions: Optional[Dimensions] = None

    # Relationships (references/IDs)
    category_ids: List[str] = Field(default_factory=list)

    # Attributes and metadata
    attributes: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    seo_title: Optional[str] = None
    seo_description: Optional[str] = None

    # Excluded from serialization
    variants: List[ProductVariant] = Field(default_factory=list, exclude=True)
    images: List[ProductImage] = Field(default_factory=list, exclude=True)

    def __init__(self, **data):
        """Initialize a product entity."""
        super().__init__(**data)
        # Register creation event
        self.register_event(
            ProductCreatedEvent(
                aggregate_id=str(self.id),
                aggregate_type="Product",
                name=self.name,
                sku=self.sku,
                price=self.price.amount,
                currency=self.price.currency,
            )
        )

    def update(self) -> None:
        """Update entity timestamp when modified."""
        self.updated_at = datetime.now(UTC)
        self.version += 1  # Increment version for optimistic concurrency

    def update_inventory(self, new_inventory: Inventory) -> None:
        """
        Update the product's inventory.

        Args:
            new_inventory: New inventory values
        """
        old_quantity = self.inventory.quantity
        self.inventory = new_inventory
        self.update()

        # Register inventory update event
        self.register_event(
            ProductInventoryUpdatedEvent(
                aggregate_id=str(self.id),
                aggregate_type="Product",
                old_quantity=old_quantity,
                new_quantity=new_inventory.quantity,
            )
        )

    def update_price(self, new_price: Money) -> None:
        """
        Update the product's price.

        Args:
            new_price: New price value
        """
        old_price = self.price
        self.price = new_price
        self.update()

        # Register price change event
        self.register_event(
            ProductPriceChangedEvent(
                aggregate_id=str(self.id),
                aggregate_type="Product",
                old_price=old_price.amount,
                new_price=new_price.amount,
                currency=new_price.currency,
            )
        )

    def add_variant(self, variant: ProductVariant) -> None:
        """
        Add a variant to the product.

        Args:
            variant: Product variant to add
        """
        # Ensure the variant is linked to this product
        variant.product_id = str(self.id)

        # Add the variant and update
        self.variants.append(variant)
        self.update()

    def add_image(self, image: ProductImage) -> None:
        """
        Add an image to the product.

        Args:
            image: Product image to add
        """
        # Ensure the image is linked to this product
        image.product_id = str(self.id)

        # If this is the first image, make it primary
        if not self.images:
            image.is_primary = True

        # Add the image and update
        self.images.append(image)
        self.update()

    def add_to_category(self, category_id: str) -> None:
        """
        Add the product to a category.

        Args:
            category_id: ID of the category to add
        """
        if category_id not in self.category_ids:
            self.category_ids.append(category_id)
            self.update()

    def remove_from_category(self, category_id: str) -> None:
        """
        Remove the product from a category.

        Args:
            category_id: ID of the category to remove
        """
        if category_id in self.category_ids:
            self.category_ids.remove(category_id)
            self.update()

    def activate(self) -> None:
        """Activate the product (make it available for purchase)."""
        if self.status != ProductStatus.ACTIVE:
            self.status = ProductStatus.ACTIVE
            self.update()

            # Register product updated event
            self.register_event(
                ProductUpdatedEvent(
                    aggregate_id=str(self.id),
                    aggregate_type="Product",
                    name=self.name,
                    status=self.status,
                )
            )

    def deactivate(self) -> None:
        """Deactivate the product (make it unavailable for purchase)."""
        if self.status != ProductStatus.INACTIVE:
            self.status = ProductStatus.INACTIVE
            self.update()

            # Register product updated event
            self.register_event(
                ProductUpdatedEvent(
                    aggregate_id=str(self.id),
                    aggregate_type="Product",
                    name=self.name,
                    status=self.status,
                )
            )

    def check_invariants(self) -> None:
        """
        Check domain invariants before saving.

        Raises:
            ValueError: If any invariant is violated
        """
        # Products must have a name
        if not self.name:
            raise ValueError("Product must have a name")

        # Products must have a SKU
        if not self.sku:
            raise ValueError("Product must have a SKU")

        # Products must have a valid price
        if self.price.amount < 0:
            raise ValueError("Product price cannot be negative")

        # Variants must belong to this product
        for variant in self.variants:
            if variant.product_id != str(self.id):
                raise ValueError(f"Variant {variant.id} belongs to another product")

        # Images must belong to this product
        for image in self.images:
            if image.product_id != str(self.id):
                raise ValueError(f"Image {image.id} belongs to another product")
