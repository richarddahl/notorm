"""
Example usage of the application service layer with CQRS.

This module demonstrates how application services coordinate the execution
of commands and queries, providing a higher-level API on top of CQRS.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4

from uno.domain.models import Entity, AggregateRoot
from uno.domain.cqrs import (
    Command,
    Query,
    CommandResult,
    QueryResult,
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
    PaginatedResult,
)
from uno.domain.application_services import (
    ApplicationService,
    EntityService,
    AggregateService,
    ServiceContext,
    ServiceRegistry,
    get_service_registry,
)
from uno.domain.repositories import Repository, InMemoryRepository
from uno.domain.unit_of_work import UnitOfWork, InMemoryUnitOfWork
from uno.core.errors.base import ValidationError, AuthorizationError


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


# Custom command handlers


class CheckoutOrderCommand(Command):
    """Command to checkout an order."""

    order_id: str


class CheckoutOrderCommandHandler(UpdateEntityCommandHandler):
    """Handler for the CheckoutOrderCommand."""

    async def _handle(self, command: CheckoutOrderCommand, uow: UnitOfWork) -> Order:
        """
        Handle the checkout order command.

        Args:
            command: The command to handle
            uow: The unit of work for transaction management

        Returns:
            The updated order
        """
        # Get the repository
        repository = uow.get_repository(self.entity_repository_type)

        # Get the order
        order = await repository.get_by_id(command.order_id)

        # Checkout the order
        order.checkout()

        # Save the updated order
        return await repository.update(order)


# Custom application services


class ProductService(EntityService[Product]):
    """Application service for product operations."""

    def validate_command(self, command: Command, context: ServiceContext) -> None:
        """
        Validate product commands.

        Args:
            command: The command to validate
            context: The service context

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(command, CreateEntityCommand):
            data = command.entity_data

            # Validate required fields
            if "name" not in data or not data["name"]:
                raise ValidationError("Product name is required")

            if "price" not in data:
                raise ValidationError("Product price is required")

            # Validate price
            if data["price"] < 0:
                raise ValidationError("Product price cannot be negative")

            # Validate SKU
            if "sku" not in data or not data["sku"]:
                raise ValidationError("Product SKU is required")

        elif isinstance(command, UpdateEntityCommand):
            data = command.entity_data

            # Validate price if present
            if "price" in data and data["price"] < 0:
                raise ValidationError("Product price cannot be negative")


class OrderService(AggregateService[Order]):
    """Application service for order operations."""

    def __init__(
        self,
        aggregate_type: Type[Order],
        product_service: ProductService,
        dispatcher: Optional[Dispatcher] = None,
        logger: Optional[logging.Logger] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
    ):
        """
        Initialize the order service.

        Args:
            aggregate_type: The type of aggregate this service manages
            product_service: Product service for validating products
            dispatcher: CQRS dispatcher for commands and queries
            logger: Optional logger instance
            read_permission: Permission required for read operations
            write_permission: Permission required for write operations
        """
        super().__init__(
            aggregate_type=aggregate_type,
            dispatcher=dispatcher,
            logger=logger,
            read_permission=read_permission,
            write_permission=write_permission,
        )
        self.product_service = product_service

    def validate_command(self, command: Command, context: ServiceContext) -> None:
        """
        Validate order commands.

        Args:
            command: The command to validate
            context: The service context

        Raises:
            ValidationError: If validation fails
        """
        if isinstance(command, CreateEntityCommand):
            data = command.entity_data

            # Validate required fields
            if "customer_id" not in data or not data["customer_id"]:
                raise ValidationError("Customer ID is required")

    async def checkout(self, order_id: str, context: ServiceContext) -> CommandResult:
        """
        Checkout an order.

        Args:
            order_id: Order ID
            context: Service context

        Returns:
            Command result with the updated order
        """
        command = CheckoutOrderCommand(order_id=order_id)
        return await self.execute_command(command, context)

    async def add_item(
        self, order_id: str, product_id: str, quantity: int, context: ServiceContext
    ) -> CommandResult:
        """
        Add an item to an order.

        Args:
            order_id: Order ID
            product_id: Product ID
            quantity: Item quantity
            context: Service context

        Returns:
            Command result with the updated order
        """
        # Get the order
        order_result = await self.get_by_id(order_id, context)
        if not order_result.is_success or not order_result.output:
            return CommandResult.failure(
                command_id=str(uuid4()),
                command_type="AddOrderItem",
                error=f"Order {order_id} not found",
                error_code="ENTITY_NOT_FOUND",
            )

        # Get the product
        product_result = await self.product_service.get_by_id(product_id, context)
        if not product_result.is_success or not product_result.output:
            return CommandResult.failure(
                command_id=str(uuid4()),
                command_type="AddOrderItem",
                error=f"Product {product_id} not found",
                error_code="ENTITY_NOT_FOUND",
            )

        order = order_result.output
        product = product_result.output

        # Check if product is in stock
        if not product.in_stock:
            return CommandResult.rejection(
                command_id=str(uuid4()),
                command_type="AddOrderItem",
                error=f"Product {product_id} is out of stock",
                error_code="PRODUCT_OUT_OF_STOCK",
            )

        # Create updated order data
        updated_order = Order(
            id=order.id,
            customer_id=order.customer_id,
            items=order.items.copy(),
            status=order.status,
            total=order.total,
            version=order.version,
        )

        # Add the item
        updated_order.add_item(product_id, quantity, product.price)

        # Update the order
        return await self.update(
            id=order_id,
            version=order.version,
            data=updated_order.to_dict(),
            context=context,
        )


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
        CreateEntityCommandHandler(Product, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        UpdateEntityCommandHandler(Product, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        DeleteEntityCommandHandler(Product, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        CreateEntityCommandHandler(Order, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        UpdateEntityCommandHandler(Order, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        DeleteEntityCommandHandler(Order, uow_factory, InMemoryRepository)
    )
    dispatcher.register_command_handler(
        CheckoutOrderCommandHandler(Order, uow_factory, InMemoryRepository)
    )

    # Register query handlers
    dispatcher.register_query_handler(
        EntityByIdQueryHandler(Product, product_repository)
    )
    dispatcher.register_query_handler(
        EntityListQueryHandler(Product, product_repository)
    )
    dispatcher.register_query_handler(EntityByIdQueryHandler(Order, order_repository))

    # Create service registry
    registry = get_service_registry()

    # Register services
    product_service = registry.register_entity_service(
        entity_type=Product,
        read_permission="products:read",
        write_permission="products:write",
    )

    order_service = OrderService(
        aggregate_type=Order,
        product_service=product_service,
        read_permission="orders:read",
        write_permission="orders:write",
    )
    registry.register("OrderService", order_service)

    return registry


async def run_example():
    """Run the example."""
    # Set up the example
    registry = await setup_example()

    # Get services
    product_service = registry.get("ProductService")
    order_service = registry.get("OrderService")

    # Create service context with permissions
    context = ServiceContext(
        user_id="user-1",
        is_authenticated=True,
        permissions=["products:read", "products:write", "orders:read", "orders:write"],
    )

    # Create products
    print("Creating products...")
    laptop_result = await product_service.create(
        {
            "id": "prod-1",
            "name": "Laptop",
            "description": "High-performance laptop",
            "price": 999.99,
            "sku": "LAP-001",
        },
        context,
    )

    phone_result = await product_service.create(
        {
            "id": "prod-2",
            "name": "Smartphone",
            "description": "Latest smartphone model",
            "price": 699.99,
            "sku": "PHN-001",
        },
        context,
    )

    # Create an order
    print("\nCreating order...")
    order_result = await order_service.create(
        {
            "id": "order-1",
            "customer_id": "cust-1",
            "items": [],
            "status": "pending",
            "total": 0.0,
        },
        context,
    )

    # Add items to the order
    print("\nAdding items to order...")
    add_laptop_result = await order_service.add_item("order-1", "prod-1", 1, context)

    add_phone_result = await order_service.add_item("order-1", "prod-2", 2, context)

    # Get the order
    print("\nGetting order...")
    get_order_result = await order_service.get_by_id("order-1", context)
    order = get_order_result.output
    print(f"Order total: ${order.total}")
    print(f"Order items: {len(order.items)}")

    # Checkout the order
    print("\nChecking out order...")
    checkout_result = await order_service.checkout("order-1", context)

    # Get the updated order
    print("\nGetting updated order...")
    get_updated_order_result = await order_service.get_by_id("order-1", context)
    updated_order = get_updated_order_result.output
    print(f"Order status: {updated_order.status}")

    # Try to access without permission
    print("\nTrying to access without permission...")
    restricted_context = ServiceContext(
        user_id="user-2",
        is_authenticated=True,
        permissions=["products:read"],  # No order permissions
    )

    try:
        await order_service.get_by_id("order-1", restricted_context)
    except AuthorizationError as e:
        print(f"Authorization failed: {str(e)}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_example())
