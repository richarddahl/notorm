"""
Example usage of the CQRS pattern in the Uno framework.

This module demonstrates how to use the CQRS pattern with a simple domain model.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from uno.domain.models import Entity, AggregateRoot, ValueObject
from uno.domain.cqrs import (
    Command,
    Query,
    CommandHandler,
    QueryHandler,
    Dispatcher,
    get_dispatcher,
)
from uno.domain.command_handlers import (
    CreateEntityCommand,
    CreateEntityCommandHandler,
    UpdateEntityCommand,
    UpdateEntityCommandHandler,
    DeleteEntityCommand,
    DeleteEntityCommandHandler,
)
from uno.domain.query_handlers import (
    EntityByIdQuery,
    EntityByIdQueryHandler,
    EntityListQuery,
    EntityListQueryHandler,
    PaginatedEntityQuery,
    PaginatedEntityQueryHandler,
)
from uno.domain.repositories import Repository, InMemoryRepository
from uno.domain.unit_of_work import UnitOfWork, InMemoryUnitOfWork
from uno.domain.validation import ValidationResult, DataValidator


# Sample domain model


@dataclass
class Product(Entity):
    """Product entity."""

    name: str
    description: str
    price: float
    sku: str
    in_stock: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


@dataclass
class Order(AggregateRoot):
    """Order aggregate root."""

    customer_id: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    total: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        """Add an item to the order."""
        self.items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "price": price,
                "subtotal": quantity * price,
            }
        )
        self.update_total()

    def remove_item(self, product_id: str) -> None:
        """Remove an item from the order."""
        self.items = [item for item in self.items if item["product_id"] != product_id]
        self.update_total()

    def update_total(self) -> None:
        """Update the order total."""
        self.total = sum(item["subtotal"] for item in self.items)
        self.updated_at = datetime.utcnow()

    def checkout(self) -> None:
        """Checkout the order."""
        if not self.items:
            raise ValueError("Cannot checkout an empty order")
        self.status = "placed"
        self.updated_at = datetime.utcnow()

    def check_invariants(self) -> None:
        """Check that all order invariants are satisfied."""
        if not self.customer_id:
            raise ValueError("Customer ID is required")
        if self.total < 0:
            raise ValueError("Order total cannot be negative")


# Sample commands


class CreateProductCommand(Command):
    """Command to create a new product."""

    name: str
    description: str
    price: float
    sku: str
    in_stock: bool = True


class UpdateProductCommand(Command):
    """Command to update an existing product."""

    id: str
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    in_stock: Optional[bool] = None


class DeleteProductCommand(Command):
    """Command to delete a product."""

    id: str


class CreateOrderCommand(Command):
    """Command to create a new order."""

    customer_id: str
    items: List[Dict[str, Any]]


class AddOrderItemCommand(Command):
    """Command to add an item to an order."""

    order_id: str
    product_id: str
    quantity: int
    price: float


class RemoveOrderItemCommand(Command):
    """Command to remove an item from an order."""

    order_id: str
    product_id: str


class CheckoutOrderCommand(Command):
    """Command to checkout an order."""

    order_id: str


# Sample queries


class GetProductByIdQuery(Query[Optional[Product]]):
    """Query to get a product by ID."""

    id: str


class ListProductsQuery(Query[List[Product]]):
    """Query to list products."""

    in_stock: Optional[bool] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class GetOrderByIdQuery(Query[Optional[Order]]):
    """Query to get an order by ID."""

    id: str


class ListOrdersByCustomerQuery(Query[List[Order]]):
    """Query to list orders for a customer."""

    customer_id: str
    status: Optional[str] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


# Sample command handlers


class CreateProductCommandHandler(CommandHandler[CreateProductCommand, Product]):
    """Handler for the CreateProductCommand."""

    def __init__(self, unit_of_work_factory, product_repository_type):
        super().__init__(CreateProductCommand, unit_of_work_factory)
        self.product_repository_type = product_repository_type

    def validate(self, command: CreateProductCommand) -> None:
        """Validate the create product command."""
        if not command.name:
            raise ValueError("Product name is required")
        if command.price < 0:
            raise ValueError("Product price cannot be negative")
        if not command.sku:
            raise ValueError("Product SKU is required")

    async def _handle(self, command: CreateProductCommand, uow: UnitOfWork) -> Product:
        """Handle the create product command."""
        # Get the repository
        repository = uow.get_repository(self.product_repository_type)

        # Create the product
        product = Product(
            id=str(uuid4()),
            name=command.name,
            description=command.description,
            price=command.price,
            sku=command.sku,
            in_stock=command.in_stock,
        )

        # Add the product to the repository
        return await repository.add(product)


class UpdateProductCommandHandler(CommandHandler[UpdateProductCommand, Product]):
    """Handler for the UpdateProductCommand."""

    def __init__(self, unit_of_work_factory, product_repository_type):
        super().__init__(UpdateProductCommand, unit_of_work_factory)
        self.product_repository_type = product_repository_type

    def validate(self, command: UpdateProductCommand) -> None:
        """Validate the update product command."""
        if command.price is not None and command.price < 0:
            raise ValueError("Product price cannot be negative")

    async def _handle(self, command: UpdateProductCommand, uow: UnitOfWork) -> Product:
        """Handle the update product command."""
        # Get the repository
        repository = uow.get_repository(self.product_repository_type)

        # Get the product
        product = await repository.get_by_id(command.id)

        # Update the product
        if command.name is not None:
            product.name = command.name
        if command.description is not None:
            product.description = command.description
        if command.price is not None:
            product.price = command.price
        if command.sku is not None:
            product.sku = command.sku
        if command.in_stock is not None:
            product.in_stock = command.in_stock

        # Update the timestamp
        product.updated_at = datetime.utcnow()

        # Update the product in the repository
        return await repository.update(product)


# Sample query handlers


class GetProductByIdQueryHandler(QueryHandler[GetProductByIdQuery, Optional[Product]]):
    """Handler for the GetProductByIdQuery."""

    def __init__(self, query_type, product_repository):
        super().__init__(query_type)
        self.product_repository = product_repository

    async def _handle(self, query: GetProductByIdQuery) -> Optional[Product]:
        """Handle the get product by ID query."""
        return await self.product_repository.get(query.id)


class ListProductsQueryHandler(QueryHandler[ListProductsQuery, List[Product]]):
    """Handler for the ListProductsQuery."""

    def __init__(self, query_type, product_repository):
        super().__init__(query_type)
        self.product_repository = product_repository

    async def _handle(self, query: ListProductsQuery) -> List[Product]:
        """Handle the list products query."""
        # Build filters
        filters = {}
        if query.in_stock is not None:
            filters["in_stock"] = query.in_stock

        # Execute query
        products = await self.product_repository.list(
            filters=filters, limit=query.limit, offset=query.offset
        )

        # Filter by price range if specified
        if query.min_price is not None or query.max_price is not None:
            filtered_products = []
            for product in products:
                if (query.min_price is None or product.price >= query.min_price) and (
                    query.max_price is None or product.price <= query.max_price
                ):
                    filtered_products.append(product)
            return filtered_products

        return products


# Example setup and usage


async def setup_example():
    """Set up the example."""
    # Create repositories
    product_repository = InMemoryRepository(Product)
    order_repository = InMemoryRepository(Order)

    # Create unit of work factory
    uow = InMemoryUnitOfWork()
    uow.register_repository(InMemoryRepository, product_repository)
    uow_factory = lambda: uow

    # Get the dispatcher
    dispatcher = get_dispatcher()

    # Register command handlers
    dispatcher.register_command_handler(
        CreateProductCommandHandler(uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        UpdateProductCommandHandler(uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        CreateEntityCommandHandler(Order, uow_factory, InMemoryRepository)
    )

    # Register query handlers
    dispatcher.register_query_handler(
        GetProductByIdQueryHandler(GetProductByIdQuery, product_repository)
    )
    dispatcher.register_query_handler(
        ListProductsQueryHandler(ListProductsQuery, product_repository)
    )
    dispatcher.register_query_handler(EntityByIdQueryHandler(Order, order_repository))

    return dispatcher, product_repository, order_repository


async def run_example():
    """Run the example."""
    dispatcher, product_repository, order_repository = await setup_example()

    # Create some products
    create_product1_result = await dispatcher.dispatch_command(
        CreateProductCommand(
            name="Laptop",
            description="High-performance laptop",
            price=999.99,
            sku="LAP-001",
        )
    )

    create_product2_result = await dispatcher.dispatch_command(
        CreateProductCommand(
            name="Smartphone",
            description="Latest smartphone model",
            price=699.99,
            sku="PHN-001",
        )
    )

    # Get a product by ID
    get_product_result = await dispatcher.dispatch_query(
        GetProductByIdQuery(id=create_product1_result.output.id)
    )
    print(f"Retrieved product: {get_product_result.output.name}")

    # List products
    list_products_result = await dispatcher.dispatch_query(
        ListProductsQuery(min_price=500.0)
    )
    print(f"Found {len(list_products_result.output)} products over $500")

    # Update a product
    update_product_result = await dispatcher.dispatch_command(
        UpdateProductCommand(
            id=create_product1_result.output.id, price=899.99, in_stock=False
        )
    )
    print(f"Updated product price: ${update_product_result.output.price}")

    # Create an order
    create_order_result = await dispatcher.dispatch_command(
        CreateEntityCommand(
            entity_data={
                "customer_id": "cust-001",
                "items": [
                    {
                        "product_id": create_product2_result.output.id,
                        "quantity": 2,
                        "price": 699.99,
                        "subtotal": 1399.98,
                    }
                ],
                "status": "pending",
                "total": 1399.98,
            }
        )
    )

    # Get the order
    get_order_result = await dispatcher.dispatch_query(
        EntityByIdQuery[Order](id=create_order_result.output.id)
    )
    print(f"Order total: ${get_order_result.output.total}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_example())
