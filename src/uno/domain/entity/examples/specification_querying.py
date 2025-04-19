"""
Real-world examples of using specifications for querying domain entities.

This module demonstrates how to use specifications to implement domain-specific 
query logic in a way that is decoupled from the underlying persistence mechanism.
"""

import asyncio
import decimal
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import List, Optional, Set, Dict, Any
from uuid import UUID, uuid4

from pydantic import Field
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, Numeric
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

from uno.domain.entity.base import EntityBase
from uno.domain.entity.identity import Identity
from uno.domain.entity.specification.base import Specification, AttributeSpecification
from uno.domain.entity.specification.composite import AndSpecification, OrSpecification, NotSpecification
from uno.domain.entity.repository_memory import InMemoryRepository
from uno.domain.entity.repository_sqlalchemy import SQLAlchemyRepository, EntityMapper


# Domain Models
class OrderStatus(Enum):
    """Order status enum."""
    DRAFT = auto()
    PLACED = auto()
    PAID = auto()
    SHIPPED = auto()
    DELIVERED = auto()
    CANCELLED = auto()


class Category(EntityBase[UUID]):
    """Product category entity."""
    
    name: str
    description: Optional[str] = None


class Product(EntityBase[UUID]):
    """Product entity."""
    
    name: str
    description: Optional[str] = None
    price: decimal.Decimal
    category_id: UUID
    inventory_count: int = 0
    is_active: bool = True


class Customer(EntityBase[UUID]):
    """Customer entity."""
    
    name: str
    email: str
    is_vip: bool = False
    last_order_date: Optional[datetime] = None


class OrderItem(EntityBase[UUID]):
    """Order item entity."""
    
    order_id: UUID
    product_id: UUID
    quantity: int
    unit_price: decimal.Decimal
    
    @property
    def total_price(self) -> decimal.Decimal:
        """Calculate total price for this item."""
        return self.unit_price * self.quantity


class Order(EntityBase[UUID]):
    """Order entity."""
    
    customer_id: UUID
    order_date: datetime
    status: OrderStatus = OrderStatus.DRAFT
    items: List[OrderItem] = Field(default_factory=list)
    shipping_address: Optional[str] = None
    
    @property
    def total_amount(self) -> decimal.Decimal:
        """Calculate total amount for the order."""
        return sum(item.total_price for item in self.items)
    
    @property
    def item_count(self) -> int:
        """Get number of items in the order."""
        return sum(item.quantity for item in self.items)


# Specifications for Products
class ActiveProductSpecification(Specification[Product]):
    """Specification for active products."""
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is active."""
        return candidate.is_active


class ProductCategorySpecification(Specification[Product]):
    """Specification for products in a specific category."""
    
    def __init__(self, category_id: UUID):
        """Initialize with category ID."""
        self.category_id = category_id
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is in the specified category."""
        return candidate.category_id == self.category_id


class ProductPriceRangeSpecification(Specification[Product]):
    """Specification for products within a price range."""
    
    def __init__(self, min_price: decimal.Decimal, max_price: decimal.Decimal):
        """Initialize with price range."""
        self.min_price = min_price
        self.max_price = max_price
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product's price is within the range."""
        return self.min_price <= candidate.price <= self.max_price


class InStockProductSpecification(Specification[Product]):
    """Specification for products that are in stock."""
    
    def __init__(self, min_count: int = 1):
        """Initialize with minimum inventory count."""
        self.min_count = min_count
    
    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is in stock."""
        return candidate.inventory_count >= self.min_count


# Specifications for Orders
class OrderStatusSpecification(Specification[Order]):
    """Specification for orders with a specific status."""
    
    def __init__(self, status: OrderStatus):
        """Initialize with order status."""
        self.status = status
    
    def is_satisfied_by(self, candidate: Order) -> bool:
        """Check if the order has the specified status."""
        return candidate.status == self.status


class OrderDateRangeSpecification(Specification[Order]):
    """Specification for orders within a date range."""
    
    def __init__(self, start_date: datetime, end_date: datetime):
        """Initialize with date range."""
        self.start_date = start_date
        self.end_date = end_date
    
    def is_satisfied_by(self, candidate: Order) -> bool:
        """Check if the order date is within the range."""
        return self.start_date <= candidate.order_date <= self.end_date


class OrderValueSpecification(Specification[Order]):
    """Specification for orders with a minimum value."""
    
    def __init__(self, min_value: decimal.Decimal):
        """Initialize with minimum order value."""
        self.min_value = min_value
    
    def is_satisfied_by(self, candidate: Order) -> bool:
        """Check if the order value meets the minimum."""
        return candidate.total_amount >= self.min_value


# Specifications for Customers
class VipCustomerSpecification(Specification[Customer]):
    """Specification for VIP customers."""
    
    def is_satisfied_by(self, candidate: Customer) -> bool:
        """Check if the customer is a VIP."""
        return candidate.is_vip


class RecentCustomerSpecification(Specification[Customer]):
    """Specification for customers who have ordered recently."""
    
    def __init__(self, days: int = 30):
        """Initialize with number of days."""
        self.days = days
    
    def is_satisfied_by(self, candidate: Customer) -> bool:
        """Check if the customer has ordered recently."""
        if not candidate.last_order_date:
            return False
        
        cutoff = datetime.now() - timedelta(days=self.days)
        return candidate.last_order_date >= cutoff


# Mock database and repositories setup
async def setup_repositories():
    """Setup in-memory repositories with sample data."""
    # Create repositories
    category_repo = InMemoryRepository[Category, UUID](Category)
    product_repo = InMemoryRepository[Product, UUID](Product)
    customer_repo = InMemoryRepository[Customer, UUID](Customer)
    order_item_repo = InMemoryRepository[OrderItem, UUID](OrderItem)
    order_repo = InMemoryRepository[Order, UUID](Order)
    
    # Create sample data
    # Categories
    electronics = Category(
        id=uuid4(),
        name="Electronics",
        description="Electronic devices and accessories"
    )
    
    clothing = Category(
        id=uuid4(),
        name="Clothing",
        description="Apparel and accessories"
    )
    
    books = Category(
        id=uuid4(),
        name="Books",
        description="Books and publications"
    )
    
    await category_repo.add_many([electronics, clothing, books])
    
    # Products
    products = [
        Product(
            id=uuid4(),
            name="Smartphone",
            description="Latest smartphone with advanced features",
            price=decimal.Decimal("699.99"),
            category_id=electronics.id,
            inventory_count=15,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Laptop",
            description="Powerful laptop for professional use",
            price=decimal.Decimal("1299.99"),
            category_id=electronics.id,
            inventory_count=8,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Headphones",
            description="Noise-cancelling wireless headphones",
            price=decimal.Decimal("199.99"),
            category_id=electronics.id,
            inventory_count=25,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="T-Shirt",
            description="Comfortable cotton t-shirt",
            price=decimal.Decimal("19.99"),
            category_id=clothing.id,
            inventory_count=50,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Jeans",
            description="Classic blue jeans",
            price=decimal.Decimal("49.99"),
            category_id=clothing.id,
            inventory_count=30,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Winter Jacket",
            description="Warm winter jacket",
            price=decimal.Decimal("149.99"),
            category_id=clothing.id,
            inventory_count=0,  # Out of stock
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Novel",
            description="Bestselling novel",
            price=decimal.Decimal("12.99"),
            category_id=books.id,
            inventory_count=100,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Cookbook",
            description="Popular cookbook with recipes",
            price=decimal.Decimal("24.99"),
            category_id=books.id,
            inventory_count=40,
            is_active=True
        ),
        Product(
            id=uuid4(),
            name="Discontinued Item",
            description="This item is no longer available",
            price=decimal.Decimal("9.99"),
            category_id=books.id,
            inventory_count=5,
            is_active=False  # Inactive product
        )
    ]
    
    await product_repo.add_many(products)
    
    # Customers
    customers = [
        Customer(
            id=uuid4(),
            name="John Doe",
            email="john@example.com",
            is_vip=True,
            last_order_date=datetime.now() - timedelta(days=5)
        ),
        Customer(
            id=uuid4(),
            name="Jane Smith",
            email="jane@example.com",
            is_vip=False,
            last_order_date=datetime.now() - timedelta(days=20)
        ),
        Customer(
            id=uuid4(),
            name="Bob Johnson",
            email="bob@example.com",
            is_vip=False,
            last_order_date=datetime.now() - timedelta(days=60)
        ),
        Customer(
            id=uuid4(),
            name="Alice Brown",
            email="alice@example.com",
            is_vip=True,
            last_order_date=None  # New customer, no orders yet
        )
    ]
    
    await customer_repo.add_many(customers)
    
    # Orders and order items
    # John's recent order
    john_order = Order(
        id=uuid4(),
        customer_id=customers[0].id,
        order_date=datetime.now() - timedelta(days=5),
        status=OrderStatus.DELIVERED,
        shipping_address="123 Main St, Anytown, USA"
    )
    
    john_items = [
        OrderItem(
            id=uuid4(),
            order_id=john_order.id,
            product_id=products[0].id,  # Smartphone
            quantity=1,
            unit_price=products[0].price
        ),
        OrderItem(
            id=uuid4(),
            order_id=john_order.id,
            product_id=products[2].id,  # Headphones
            quantity=2,
            unit_price=products[2].price
        )
    ]
    
    john_order.items = john_items
    
    # Jane's recent order
    jane_order = Order(
        id=uuid4(),
        customer_id=customers[1].id,
        order_date=datetime.now() - timedelta(days=20),
        status=OrderStatus.SHIPPED,
        shipping_address="456 Oak Ave, Othertown, USA"
    )
    
    jane_items = [
        OrderItem(
            id=uuid4(),
            order_id=jane_order.id,
            product_id=products[3].id,  # T-Shirt
            quantity=3,
            unit_price=products[3].price
        ),
        OrderItem(
            id=uuid4(),
            order_id=jane_order.id,
            product_id=products[4].id,  # Jeans
            quantity=1,
            unit_price=products[4].price
        ),
        OrderItem(
            id=uuid4(),
            order_id=jane_order.id,
            product_id=products[6].id,  # Novel
            quantity=2,
            unit_price=products[6].price
        )
    ]
    
    jane_order.items = jane_items
    
    # Bob's older order
    bob_order = Order(
        id=uuid4(),
        customer_id=customers[2].id,
        order_date=datetime.now() - timedelta(days=60),
        status=OrderStatus.DELIVERED,
        shipping_address="789 Pine Rd, Somewhere, USA"
    )
    
    bob_items = [
        OrderItem(
            id=uuid4(),
            order_id=bob_order.id,
            product_id=products[1].id,  # Laptop
            quantity=1,
            unit_price=products[1].price
        ),
        OrderItem(
            id=uuid4(),
            order_id=bob_order.id,
            product_id=products[7].id,  # Cookbook
            quantity=1,
            unit_price=products[7].price
        )
    ]
    
    bob_order.items = bob_items
    
    # Add current draft order for John
    john_draft = Order(
        id=uuid4(),
        customer_id=customers[0].id,
        order_date=datetime.now(),
        status=OrderStatus.DRAFT,
        shipping_address="123 Main St, Anytown, USA"
    )
    
    draft_items = [
        OrderItem(
            id=uuid4(),
            order_id=john_draft.id,
            product_id=products[1].id,  # Laptop
            quantity=1,
            unit_price=products[1].price
        )
    ]
    
    john_draft.items = draft_items
    
    # Add items and orders to repositories
    await order_item_repo.add_many(john_items + jane_items + bob_items + draft_items)
    await order_repo.add_many([john_order, jane_order, bob_order, john_draft])
    
    # Update customer last order dates
    customers[0].last_order_date = john_order.order_date
    customers[1].last_order_date = jane_order.order_date
    customers[2].last_order_date = bob_order.order_date
    
    await customer_repo.update_many(customers[:3])
    
    return {
        "categories": category_repo,
        "products": product_repo,
        "customers": customer_repo,
        "order_items": order_item_repo,
        "orders": order_repo,
        "data": {
            "categories": [electronics, clothing, books],
            "products": products,
            "customers": customers,
            "orders": [john_order, jane_order, bob_order, john_draft]
        }
    }


async def run_product_queries(repos):
    """Run example product queries using specifications."""
    print("\n--- Product Queries ---")
    
    product_repo = repos["products"]
    categories = repos["data"]["categories"]
    
    # Find active products
    active_spec = ActiveProductSpecification()
    active_products = await product_repo.find(active_spec)
    print(f"Active products: {len(active_products)}")
    
    # Find electronics products
    electronics_spec = ProductCategorySpecification(categories[0].id)
    electronics_products = await product_repo.find(electronics_spec)
    print(f"Electronics products: {len(electronics_products)}")
    for product in electronics_products:
        print(f"  - {product.name}: ${product.price}")
    
    # Find products in a price range
    price_range_spec = ProductPriceRangeSpecification(
        decimal.Decimal("50"), decimal.Decimal("200")
    )
    mid_price_products = await product_repo.find(price_range_spec)
    print(f"\nProducts between $50 and $200: {len(mid_price_products)}")
    for product in mid_price_products:
        print(f"  - {product.name}: ${product.price}")
    
    # Find in-stock electronics in a specific price range
    combined_spec = (
        ActiveProductSpecification()
        .and_(ProductCategorySpecification(categories[0].id))
        .and_(ProductPriceRangeSpecification(
            decimal.Decimal("100"), decimal.Decimal("300")
        ))
        .and_(InStockProductSpecification())
    )
    
    target_products = await product_repo.find(combined_spec)
    print(f"\nActive, in-stock electronics between $100 and $300: {len(target_products)}")
    for product in target_products:
        print(f"  - {product.name}: ${product.price} (Inventory: {product.inventory_count})")
    
    # Find out-of-stock products
    out_of_stock_spec = InStockProductSpecification(1).not_()
    out_of_stock = await product_repo.find(out_of_stock_spec)
    print(f"\nOut of stock products: {len(out_of_stock)}")
    for product in out_of_stock:
        print(f"  - {product.name}")


async def run_order_queries(repos):
    """Run example order queries using specifications."""
    print("\n--- Order Queries ---")
    
    order_repo = repos["orders"]
    
    # Find orders by status
    draft_spec = OrderStatusSpecification(OrderStatus.DRAFT)
    draft_orders = await order_repo.find(draft_spec)
    print(f"Draft orders: {len(draft_orders)}")
    for order in draft_orders:
        print(f"  - Order {order.id}: Customer {order.customer_id} - Items: {order.item_count}")
    
    # Find recent orders
    one_month_ago = datetime.now() - timedelta(days=30)
    recent_spec = OrderDateRangeSpecification(one_month_ago, datetime.now())
    recent_orders = await order_repo.find(recent_spec)
    print(f"\nOrders in the last 30 days: {len(recent_orders)}")
    for order in recent_orders:
        print(f"  - Order {order.id}: {order.order_date.strftime('%Y-%m-%d')} - Status: {order.status.name}")
    
    # Find high-value orders
    high_value_spec = OrderValueSpecification(decimal.Decimal("1000"))
    high_value_orders = await order_repo.find(high_value_spec)
    print(f"\nHigh-value orders (>$1000): {len(high_value_orders)}")
    for order in high_value_orders:
        print(f"  - Order {order.id}: ${order.total_amount} - Items: {order.item_count}")
    
    # Find delivered orders with high value
    delivered_high_value_spec = (
        OrderStatusSpecification(OrderStatus.DELIVERED)
        .and_(OrderValueSpecification(decimal.Decimal("1000")))
    )
    delivered_high_value = await order_repo.find(delivered_high_value_spec)
    print(f"\nDelivered high-value orders: {len(delivered_high_value)}")
    for order in delivered_high_value:
        print(f"  - Order {order.id}: ${order.total_amount} - Date: {order.order_date.strftime('%Y-%m-%d')}")


async def run_customer_queries(repos):
    """Run example customer queries using specifications."""
    print("\n--- Customer Queries ---")
    
    customer_repo = repos["customers"]
    
    # Find VIP customers
    vip_spec = VipCustomerSpecification()
    vip_customers = await customer_repo.find(vip_spec)
    print(f"VIP customers: {len(vip_customers)}")
    for customer in vip_customers:
        print(f"  - {customer.name} ({customer.email})")
    
    # Find recent customers
    recent_spec = RecentCustomerSpecification(days=30)
    recent_customers = await customer_repo.find(recent_spec)
    print(f"\nCustomers with orders in the last 30 days: {len(recent_customers)}")
    for customer in recent_customers:
        print(f"  - {customer.name} ({customer.email}) - Last order: {customer.last_order_date.strftime('%Y-%m-%d')}")
    
    # Find VIP customers with recent orders
    vip_recent_spec = vip_spec.and_(recent_spec)
    vip_recent = await customer_repo.find(vip_recent_spec)
    print(f"\nVIP customers with recent orders: {len(vip_recent)}")
    for customer in vip_recent:
        print(f"  - {customer.name} ({customer.email}) - Last order: {customer.last_order_date.strftime('%Y-%m-%d')}")
    
    # Find customers without recent orders (potential churn)
    inactive_spec = recent_spec.not_()
    inactive_customers = await customer_repo.find(inactive_spec)
    print(f"\nCustomers without recent orders: {len(inactive_customers)}")
    for customer in inactive_customers:
        if customer.last_order_date:
            print(f"  - {customer.name} ({customer.email}) - Last order: {customer.last_order_date.strftime('%Y-%m-%d')}")
        else:
            print(f"  - {customer.name} ({customer.email}) - No orders yet")


async def main():
    """Run the domain querying examples."""
    # Setup repositories with sample data
    repos = await setup_repositories()
    
    # Run example queries
    await run_product_queries(repos)
    await run_order_queries(repos)
    await run_customer_queries(repos)


if __name__ == "__main__":
    asyncio.run(main())