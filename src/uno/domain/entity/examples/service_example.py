"""
Example demonstrating the use of the Service pattern with domain entities.

This example shows how to:
1. Create domain services for business logic
2. Use the application service layer for orchestration
3. Combine services with repositories and specifications
4. Use the Result pattern for error handling
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from uno.core.errors.result import Result
from uno.core.uow.base import AbstractUnitOfWork
from uno.core.uow.memory import InMemoryUnitOfWork

from uno.domain.entity.base import EntityBase
from uno.domain.entity.repository_memory import InMemoryRepository
from uno.domain.entity.specification.base import Specification, AttributeSpecification
from uno.domain.entity.service import (
    DomainService,
    DomainServiceWithUnitOfWork,
    ApplicationService,
    CrudService,
    ServiceFactory,
)


# Define domain entities
class Product(EntityBase[uuid.UUID]):
    """Example product entity."""

    name: str
    description: str
    price: float
    category: str
    inventory_count: int = 0
    is_active: bool = True


class Order(EntityBase[uuid.UUID]):
    """Example order entity."""

    customer_id: uuid.UUID
    products: list[uuid.UUID]
    total_amount: float
    status: str = "pending"
    order_date: datetime = datetime.now()


# Define domain specifications
class ActiveProductSpecification(Specification[Product]):
    """Specification for active products."""

    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is active."""
        return candidate.is_active


class InStockProductSpecification(Specification[Product]):
    """Specification for products that are in stock."""

    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is in stock."""
        return candidate.inventory_count > 0


class CategoryProductSpecification(Specification[Product]):
    """Specification for products in a specific category."""

    def __init__(self, category: str):
        """Initialize with category."""
        self.category = category

    def is_satisfied_by(self, candidate: Product) -> bool:
        """Check if the product is in the specified category."""
        return candidate.category == self.category


# Define domain services
class ProductService(DomainService[Product, uuid.UUID]):
    """Domain service for product-related business logic."""

    async def get_available_products(self) -> Result[list[Product], str]:
        """
        Get all products that are active and in stock.

        Returns:
            Success with available products or Failure if an error occurs
        """
        specification = ActiveProductSpecification().and_(InStockProductSpecification())
        return await self.find(specification)

    async def get_products_by_category(
        self, category: str
    ) -> Result[list[Product], str]:
        """
        Get all products in a specific category.

        Args:
            category: Product category

        Returns:
            Success with products in the category or Failure if an error occurs
        """
        specification = CategoryProductSpecification(category)
        return await self.find(specification)

    async def update_inventory(
        self, product_id: uuid.UUID, quantity: int
    ) -> Result[Product, str]:
        """
        Update the inventory count for a product.

        Args:
            product_id: Product ID
            quantity: New inventory quantity

        Returns:
            Success with updated product or Failure if an error occurs
        """
        result = await self.get_by_id(product_id)
        if not result.is_success():
            return result

        product = result.value
        product.inventory_count = quantity

        try:
            updated = await self.repository.update(product)
            return Success(updated)
        except Exception as e:
            self.logger.error(f"Error updating product inventory: {e}", exc_info=True)
            return Failure(f"Error updating product inventory: {str(e)}")


class OrderService(DomainServiceWithUnitOfWork[Order, uuid.UUID]):
    """Domain service for order-related business logic."""

    async def create_order(
        self, customer_id: uuid.UUID, product_ids: list[uuid.UUID]
    ) -> Result[Order, str]:
        """
        Create a new order for a customer.

        Args:
            customer_id: Customer ID
            product_ids: List of product IDs

        Returns:
            Success with created order or Failure if an error occurs
        """
        async with self.with_uow("create_order"):
            await self._ensure_repository()

            # Get product repository from unit of work
            product_repo = self.unit_of_work.get_repository(Product)

            # Validate products
            products = []
            for product_id in product_ids:
                product = await product_repo.get(product_id)
                if product is None:
                    return Failure(f"Product with ID {product_id} not found")
                if not product.is_active:
                    return Failure(f"Product '{product.name}' is not active")
                if product.inventory_count <= 0:
                    return Failure(f"Product '{product.name}' is out of stock")
                products.append(product)

            # Calculate total amount
            total_amount = sum(product.price for product in products)

            # Create new order
            order = Order(
                id=uuid.uuid4(),
                customer_id=customer_id,
                products=product_ids,
                total_amount=total_amount,
                status="pending",
                order_date=datetime.now(),
            )

            # Save order
            try:
                created_order = await self.repository.add(order)

                # Update product inventory
                for product in products:
                    product.inventory_count -= 1
                    await product_repo.update(product)

                return Success(created_order)
            except Exception as e:
                self.logger.error(f"Error creating order: {e}", exc_info=True)
                return Failure(f"Error creating order: {str(e)}")

    async def get_orders_by_customer(
        self, customer_id: uuid.UUID
    ) -> Result[list[Order], str]:
        """
        Get all orders for a specific customer.

        Args:
            customer_id: Customer ID

        Returns:
            Success with customer orders or Failure if an error occurs
        """
        await self._ensure_repository()

        try:
            orders = await self.repository.find(
                AttributeSpecification("customer_id", customer_id)
            )
            return Success(orders)
        except Exception as e:
            self.logger.error(f"Error getting customer orders: {e}", exc_info=True)
            return Failure(f"Error getting customer orders: {str(e)}")

    async def update_order_status(
        self, order_id: uuid.UUID, status: str
    ) -> Result[Order, str]:
        """
        Update the status of an order.

        Args:
            order_id: Order ID
            status: New order status

        Returns:
            Success with updated order or Failure if an error occurs
        """
        async with self.with_uow("update_order_status"):
            await self._ensure_repository()

            # Get the order
            order = await self.repository.get(order_id)
            if order is None:
                return Failure(f"Order with ID {order_id} not found")

            # Update status
            order.status = status

            # Save changes
            try:
                updated_order = await self.repository.update(order)
                return Success(updated_order)
            except Exception as e:
                self.logger.error(f"Error updating order status: {e}", exc_info=True)
                return Failure(f"Error updating order status: {str(e)}")


# Define application service
class OrderingApplicationService(ApplicationService[Any, str]):
    """Application service for coordinating ordering operations."""

    def __init__(self, product_service: ProductService, order_service: OrderService):
        """
        Initialize the application service.

        Args:
            product_service: Domain service for products
            order_service: Domain service for orders
        """
        super().__init__()
        self.product_service = product_service
        self.order_service = order_service

    async def place_order(
        self, customer_id: uuid.UUID, product_ids: list[uuid.UUID]
    ) -> Result[Dict[str, Any], str]:
        """
        Place an order for a customer.

        This method coordinates the entire order placement process:
        1. Validate products
        2. Create order
        3. Update inventory
        4. Return order details

        Args:
            customer_id: Customer ID
            product_ids: List of product IDs

        Returns:
            Success with order details or Failure if an error occurs
        """
        self.log_request(
            "place_order", {"customer_id": customer_id, "product_ids": product_ids}
        )

        # Create the order
        order_result = await self.order_service.create_order(customer_id, product_ids)
        if not order_result.is_success():
            self.logger.warning(f"Order creation failed: {order_result.error}")
            return Failure(order_result.error)

        order = order_result.value

        # Get product details for the response
        products = []
        for product_id in product_ids:
            product_result = await self.product_service.get_by_id(product_id)
            if product_result.is_success():
                products.append(
                    {
                        "id": str(product_result.value.id),
                        "name": product_result.value.name,
                        "price": product_result.value.price,
                    }
                )

        # Prepare the response
        response = {
            "order_id": str(order.id),
            "customer_id": str(order.customer_id),
            "products": products,
            "total_amount": order.total_amount,
            "status": order.status,
            "order_date": order.order_date.isoformat(),
        }

        self.log_response("place_order", Success(response))
        return Success(response)

    async def get_available_products_by_category(
        self, category: str
    ) -> Result[list[dict[str, Any]], str]:
        """
        Get all available products in a specific category.

        Args:
            category: Product category

        Returns:
            Success with available products or Failure if an error occurs
        """
        self.log_request("get_available_products_by_category", {"category": category})

        # Get products by category
        category_result = await self.product_service.get_products_by_category(category)
        if not category_result.is_success():
            self.logger.warning(f"Category query failed: {category_result.error}")
            return Failure(category_result.error)

        category_products = category_result.value

        # Filter for available products
        specification = ActiveProductSpecification().and_(InStockProductSpecification())
        available_products = [
            {
                "id": str(p.id),
                "name": p.name,
                "description": p.description,
                "price": p.price,
                "inventory_count": p.inventory_count,
            }
            for p in category_products
            if specification.is_satisfied_by(p)
        ]

        self.log_response(
            "get_available_products_by_category", Success(available_products)
        )
        return Success(available_products)


async def run_example():
    """Run the service example."""
    print("\n--- Service Pattern Example ---")

    # Create repositories
    product_repo = InMemoryRepository[Product, uuid.UUID](Product)
    order_repo = InMemoryRepository[Order, uuid.UUID](Order)

    # Create unit of work
    uow = InMemoryUnitOfWork()
    uow.register_repository(Product, product_repo)
    uow.register_repository(Order, order_repo)

    # Create domain services
    product_service = ProductService(Product, product_repo)
    order_service = OrderService(Order, uow)

    # Create application service
    app_service = OrderingApplicationService(product_service, order_service)

    # Create sample products
    products = [
        Product(
            id=uuid.uuid4(),
            name="Smartphone",
            description="Latest smartphone with advanced features",
            price=699.99,
            category="Electronics",
            inventory_count=10,
            is_active=True,
        ),
        Product(
            id=uuid.uuid4(),
            name="Laptop",
            description="Powerful laptop for professional use",
            price=1299.99,
            category="Electronics",
            inventory_count=5,
            is_active=True,
        ),
        Product(
            id=uuid.uuid4(),
            name="Headphones",
            description="Noise-cancelling wireless headphones",
            price=199.99,
            category="Electronics",
            inventory_count=0,  # Out of stock
            is_active=True,
        ),
        Product(
            id=uuid.uuid4(),
            name="T-Shirt",
            description="Comfortable cotton t-shirt",
            price=24.99,
            category="Clothing",
            inventory_count=50,
            is_active=True,
        ),
        Product(
            id=uuid.uuid4(),
            name="Discontinued Item",
            description="This item is no longer available",
            price=9.99,
            category="Electronics",
            inventory_count=3,
            is_active=False,  # Inactive
        ),
    ]

    # Add products to repository
    await product_repo.add_many(products)
    print(f"Added {len(products)} products to repository")

    # Get available products
    result = await product_service.get_available_products()
    if result.is_success():
        print(f"\nAvailable products: {len(result.value)}")
        for product in result.value:
            print(
                f"  - {product.name} (${product.price:.2f}, {product.inventory_count} in stock)"
            )

    # Get products by category
    result = await product_service.get_products_by_category("Electronics")
    if result.is_success():
        print(f"\nElectronics products: {len(result.value)}")
        for product in result.value:
            status = "Active" if product.is_active else "Inactive"
            stock = (
                f"{product.inventory_count} in stock"
                if product.inventory_count > 0
                else "Out of stock"
            )
            print(f"  - {product.name} (${product.price:.2f}, {status}, {stock})")

    # Create a customer ID
    customer_id = uuid.uuid4()

    # Place an order (using application service)
    product_ids = [products[0].id, products[1].id]  # Smartphone and Laptop
    result = await app_service.place_order(customer_id, product_ids)

    if result.is_success():
        print(f"\nOrder placed successfully: {result.value['order_id']}")
        print(f"  Customer: {result.value['customer_id']}")
        print(f"  Total amount: ${result.value['total_amount']:.2f}")
        print(f"  Products:")
        for product in result.value["products"]:
            print(f"    - {product['name']} (${product['price']:.2f})")
    else:
        print(f"\nFailed to place order: {result.error}")

    # Get customer orders
    result = await order_service.get_orders_by_customer(customer_id)
    if result.is_success():
        print(f"\nCustomer orders: {len(result.value)}")
        for order in result.value:
            print(f"  - Order {order.id}")
            print(f"    Status: {order.status}")
            print(f"    Total: ${order.total_amount:.2f}")
            print(f"    Date: {order.order_date}")

    # Try to order an out-of-stock product
    product_ids = [products[2].id]  # Headphones (out of stock)
    result = await app_service.place_order(customer_id, product_ids)

    if not result.is_success():
        print(f"\nExpected order failure: {result.error}")

    # Try to order an inactive product
    product_ids = [products[4].id]  # Discontinued item
    result = await app_service.place_order(customer_id, product_ids)

    if not result.is_success():
        print(f"\nExpected order failure: {result.error}")

    # Update order status
    if (
        order_result := await order_service.get_orders_by_customer(customer_id)
    ).is_success():
        orders = order_result.value
        if orders:
            update_result = await order_service.update_order_status(
                orders[0].id, "shipped"
            )
            if update_result.is_success():
                print(f"\nOrder status updated to: {update_result.value.status}")

    # Check inventory after order
    result = await product_service.get_by_id(products[0].id)  # Smartphone
    if result.is_success():
        print(
            f"\nUpdated inventory for {result.value.name}: {result.value.inventory_count}"
        )

    result = await product_service.get_by_id(products[1].id)  # Laptop
    if result.is_success():
        print(
            f"Updated inventory for {result.value.name}: {result.value.inventory_count}"
        )

    # Use the service factory
    print("\n--- Service Factory Example ---")

    def create_product_repo(entity_type: Type) -> InMemoryRepository:
        return InMemoryRepository(entity_type)

    factory = ServiceFactory(Product, repository_factory=create_product_repo)

    # Create domain service using factory
    domain_service = factory.create_domain_service()

    # Create CRUD service using factory
    crud_service = factory.create_crud_service(domain_service)

    # Create a new product using CRUD service
    new_product = Product(
        id=uuid.uuid4(),
        name="Tablet",
        description="10-inch tablet with high-resolution display",
        price=349.99,
        category="Electronics",
        inventory_count=15,
        is_active=True,
    )

    result = await crud_service.create(new_product)
    if result.is_success():
        print(f"Created new product: {result.value.name} (ID: {result.value.id})")

    # List all products using CRUD service
    result = await crud_service.list(filters={"category": "Electronics"})
    if result.is_success():
        print(f"\nAll electronics products: {len(result.value)}")
        for product in result.value:
            print(f"  - {product.name} (${product.price:.2f})")


if __name__ == "__main__":
    asyncio.run(run_example())
