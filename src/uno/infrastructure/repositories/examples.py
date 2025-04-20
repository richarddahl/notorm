"""
Examples of using the repository pattern in practice.

This module demonstrates how to use the repository pattern in various scenarios,
serving as a reference for developers implementing repositories in their code.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.future import select
from sqlalchemy.orm import relationship

from uno.core.errors.result import Result
from uno.domain.core import Entity, AggregateRoot
from uno.domain.specifications import Specification, AndSpecification
from uno.infrastructure.repositories.di import get_repository, get_unit_of_work

# Only modern repository and unit of work APIs are demonstrated below. All legacy references have been removed.


# Domain model examples
@dataclass
class ProductEntity(Entity):
    """Example product entity."""

    id: int
    name: str
    price: float
    category: str
    sku: str

    # Method to get entity ID (required for repositories)
    def get_id(self) -> int:
        return self.id


@dataclass
class OrderItemEntity(Entity):
    """Example order item entity."""

    id: int
    product_id: int
    quantity: int
    price: float

    def get_id(self) -> int:
        return self.id


@dataclass
class OrderEntity(AggregateRoot):
    """Example order aggregate root."""

    id: int
    customer_id: int
    status: str
    created_at: str
    items: list[OrderItemEntity] = field(default_factory=list)
    version: int = 1

    def get_id(self) -> int:
        return self.id

    def add_item(self, item: OrderItemEntity) -> None:
        """Add an order item to this order."""
        self.items.append(item)
        self.record_event(
            OrderItemAddedEvent(
                order_id=self.id,
                item_id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
            )
        )

    def get_child_entities(self) -> list[Entity]:
        """Get all child entities of this aggregate."""
        return self.items

    def apply_changes(self) -> None:
        """Apply any pending changes to this aggregate."""
        # In a real implementation, this would handle any business rules
        # and increment the version if changes were made
        self.version += 1


# Domain events
@dataclass
class OrderItemAddedEvent:
    """Event emitted when an order item is added."""

    order_id: int
    item_id: int
    product_id: int
    quantity: int


# Specifications
class ProductByPriceRangeSpecification(Specification[ProductEntity]):
    """Specification for products within a price range."""

    def __init__(self, min_price: float, max_price: float):
        self.min_price = min_price
        self.max_price = max_price

    def is_satisfied_by(self, candidate: ProductEntity) -> bool:
        """Check if the product's price is within the specified range."""
        return self.min_price <= candidate.price <= self.max_price


class ProductByCategorySpecification(Specification[ProductEntity]):
    """Specification for products in a specific category."""

    def __init__(self, category: str):
        self.category = category

    def is_satisfied_by(self, candidate: ProductEntity) -> bool:
        """Check if the product is in the specified category."""
        return candidate.category == self.category


# Specification translator (for SQL implementation)
class ProductSpecificationTranslator:
    """Translates product specifications into SQL filter conditions."""

    def translate(self, spec: Specification[ProductEntity]) -> dict[str, Any]:
        """Translate a specification into a filter dictionary."""
        if isinstance(spec, ProductByPriceRangeSpecification):
            return {"price__gte": spec.min_price, "price__lte": spec.max_price}
        elif isinstance(spec, ProductByCategorySpecification):
            return {"category": spec.category}
        elif isinstance(spec, AndSpecification):
            # Combine filters from both specifications
            left_filters = self.translate(spec.left)
            right_filters = self.translate(spec.right)
            return {**left_filters, **right_filters}
        else:
            raise ValueError(f"Unsupported specification type: {type(spec)}")


# Example SQLAlchemy models
Base = declarative_base()


class ProductModel(Base):
    """SQLAlchemy model for products."""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)  # Stored as cents
    category = Column(String, nullable=False)
    sku = Column(String, nullable=False, unique=True)

    def to_entity(self) -> ProductEntity:
        """Convert to domain entity."""
        return ProductEntity(
            id=self.id,
            name=self.name,
            price=self.price / 100.0,  # Convert cents to dollars
            category=self.category,
            sku=self.sku,
        )


# Example of using repositories
async def product_repository_example(session: AsyncSession) -> None:
    """Example of using product repository."""
    # Create a repository for the ProductEntity
    product_repo = await get_repository(
        entity_type=ProductEntity,
        session=session,
        model_class=ProductModel,
        include_specification=True,
        include_batch=True,
    )

    # Add a new product
    new_product = ProductEntity(
        id=0,  # Will be assigned by database
        name="Example Product",
        price=99.99,
        category="Electronics",
        sku="EP-12345",
    )

    saved_product = await product_repo.add(new_product)
    print(f"Added product: {saved_product.name} (ID: {saved_product.id})")

    # Get a product by ID
    product = await product_repo.get(saved_product.id)
    if product:
        print(f"Retrieved product: {product.name}")

    # Use specifications to find products
    price_spec = ProductByPriceRangeSpecification(50.0, 150.0)
    category_spec = ProductByCategorySpecification("Electronics")
    combined_spec = price_spec.and_specification(category_spec)

    # Find products matching the specification
    matching_products = await product_repo.find(combined_spec)
    print(f"Found {len(matching_products)} products matching the specification")

    # Batch operations
    products_to_add = [
        ProductEntity(
            id=0, name="Product 1", price=19.99, category="Books", sku="BK-001"
        ),
        ProductEntity(
            id=0, name="Product 2", price=29.99, category="Books", sku="BK-002"
        ),
        ProductEntity(
            id=0, name="Product 3", price=39.99, category="Books", sku="BK-003"
        ),
    ]

    added_products = await product_repo.add_many(products_to_add)
    print(f"Added {len(added_products)} products in batch")

    # Delete a product
    await product_repo.delete(saved_product)
    print(f"Deleted product with ID: {saved_product.id}")


async def order_repository_example(session: AsyncSession) -> None:
    """Example of using order repository (aggregate root)."""
    # Create a repository for OrderEntity (an aggregate root)
    order_repo = await get_repository(
        entity_type=OrderEntity,
        session=session,
        model_class=None,  # Would be an actual model in real code
        include_events=True,  # Always enable events for aggregates
        in_memory=True,  # Using in-memory for this example
    )

    # Create a new order
    order = OrderEntity(
        id=1, customer_id=1001, status="pending", created_at="2023-01-01T12:00:00Z"
    )

    # Add items to the order
    order.add_item(OrderItemEntity(id=1, product_id=101, quantity=2, price=19.99))
    order.add_item(OrderItemEntity(id=2, product_id=102, quantity=1, price=29.99))

    # Save the order (this will collect events)
    saved_order = await order_repo.save(order)
    print(f"Saved order: {saved_order.id} with {len(saved_order.items)} items")

    # Collect the events that were recorded
    events = order_repo.collect_events()
    print(f"Collected {len(events)} events from the order")

    # In a real application, these events would be published to an event bus
    for event in events:
        print(f"Event: {event.__class__.__name__}")


async def unit_of_work_example(session: AsyncSession) -> None:
    """Example of using the Unit of Work pattern."""
    # Get a unit of work
    uow = await get_unit_of_work(session=session)

    # Use the unit of work with multiple repositories
    async with uow:
        # Get repositories within the unit of work context
        product_repo = await get_repository(
            entity_type=ProductEntity, session=session, model_class=ProductModel
        )

        order_repo = await get_repository(
            entity_type=OrderEntity,
            session=session,
            model_class=None,  # Would be an actual model in real code
            in_memory=True,  # Using in-memory for this example
        )

        # Transactional operations
        try:
            # Add a product
            product = await product_repo.add(
                ProductEntity(
                    id=0,
                    name="Test Product",
                    price=49.99,
                    category="Test",
                    sku="TST-001",
                )
            )

            # Create an order with the product
            order = OrderEntity(
                id=999,
                customer_id=2001,
                status="new",
                created_at="2023-01-01T12:00:00Z",
            )
            order.add_item(
                OrderItemEntity(
                    id=1, product_id=product.id, quantity=1, price=product.price
                )
            )
            await order_repo.add(order)

            # Commit the transaction (both operations succeed or fail together)
            await uow.commit()
            print("Transaction committed successfully")

        except Exception as e:
            # Rollback on error
            await uow.rollback()
            print(f"Transaction rolled back: {str(e)}")

    # After exiting the context manager, the transaction is complete


# FastAPI dependency example
async def get_product_repository(
    session: AsyncSession,
) -> Repository[ProductEntity, int]:
    """
    FastAPI dependency for getting a product repository.

    Example usage in FastAPI:

    @app.get("/products/{product_id}")
    async def get_product(
        product_id: int,
        product_repo: Repository[ProductEntity, int] = Depends(get_product_repository)
    ):
        product = await product_repo.get(product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    """
    return await get_repository(
        entity_type=ProductEntity,
        session=session,
        model_class=ProductModel,
        include_specification=True,
    )
