"""
Example usage of the API integration layer with CQRS and application services.

This module demonstrates how to connect FastAPI endpoints to application services,
creating a complete API for a domain model.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Type
from uuid import uuid4

import uvicorn
from fastapi import (
    FastAPI,
    APIRouter,
    Request,
    Response,
    Depends,
    HTTPException,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

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
from uno.api.service_api import (
    EntityApi,
    AggregateApi,
    ServiceApiRegistry,
    create_dto_for_entity,
    create_response_model_for_entity,
    ContextProvider,
    get_context,
)


# Domain model


@dataclass(kw_only=True)
class Product(Entity):
    """Product entity."""

    name: str
    description: str
    price: float
    sku: str
    in_stock: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to a dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "sku": self.sku,
            "in_stock": self.in_stock,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass(kw_only=True)
class Order(AggregateRoot):
    """Order aggregate root."""

    customer_id: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "pending"
    total: float = 0.0

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

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate to a dictionary."""
        return {
            "id": self.id,
            "customer_id": self.customer_id,
            "items": self.items,
            "status": self.status,
            "total": self.total,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# DTOs and response models


class ProductCreateDto(BaseModel):
    """DTO for creating a product."""

    name: str
    description: str
    price: float
    sku: str
    in_stock: bool = True


class ProductUpdateDto(BaseModel):
    """DTO for updating a product."""

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sku: Optional[str] = None
    in_stock: Optional[bool] = None


class ProductResponseDto(BaseModel):
    """Response DTO for a product."""

    id: str
    name: str
    description: str
    price: float
    sku: str
    in_stock: bool
    created_at: str
    updated_at: Optional[str] = None


class OrderItemDto(BaseModel):
    """DTO for an order item."""

    product_id: str
    quantity: int
    price: float
    subtotal: float


class OrderCreateDto(BaseModel):
    """DTO for creating an order."""

    customer_id: str
    items: List[OrderItemDto] = []


class OrderUpdateDto(BaseModel):
    """DTO for updating an order."""

    customer_id: Optional[str] = None
    status: Optional[str] = None


class OrderResponseDto(BaseModel):
    """Response DTO for an order."""

    id: str
    customer_id: str
    items: List[Dict[str, Any]]
    status: str
    total: float
    version: int
    created_at: str
    updated_at: Optional[str] = None


# Custom command for checkout


class CheckoutOrderCommand(Command):
    """Command to checkout an order."""

    order_id: str


class CheckoutOrderCommandHandler(UpdateEntityCommandHandler):
    """Handler for the CheckoutOrderCommand."""

    async def _handle(self, command: CheckoutOrderCommand, uow: UnitOfWork) -> Order:
        """Handle the command."""
        # Get the repository
        repository = uow.get_repository(self.entity_repository_type)

        # Get the order
        order = await repository.get_by_id(command.order_id)

        # Checkout the order
        order.checkout()

        # Update the order in the repository
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
        dispatcher=None,
        logger=None,
        read_permission=None,
        write_permission=None,
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


# Custom API endpoints


class OrderApi(AggregateApi[Order]):
    """API endpoints for order operations."""

    def __init__(
        self,
        aggregate_type: Type[Order],
        service: OrderService,
        router: APIRouter,
        prefix: str,
        tags: List[str],
        create_dto=None,
        update_dto=None,
        response_model=None,
        logger=None,
    ):
        """Initialize the order API."""
        super().__init__(
            aggregate_type=aggregate_type,
            service=service,
            router=router,
            prefix=prefix,
            tags=tags,
            create_dto=create_dto,
            update_dto=update_dto,
            response_model=response_model,
            logger=logger,
        )

        # Register additional routes
        self._register_checkout_route()

    def _register_checkout_route(self) -> None:
        """Register the checkout route."""

        @self.router.post(
            f"{self.prefix}/{{order_id}}/checkout",
            response_model=self.response_model,
            tags=self.tags,
        )
        async def checkout_order(
            order_id: str,
            context: ServiceContext = Depends(get_context),
        ):
            try:
                # Execute the checkout operation
                result = await self.service.checkout(order_id, context)

                # Handle the result
                return self._handle_result(result)
            except Exception as e:
                return self._handle_exception(e)


# Custom context provider


class ExampleContextProvider(ContextProvider):
    """Custom context provider for example."""

    def _get_user_id(self, request: Request) -> Optional[str]:
        """Get user ID from request header."""
        return request.headers.get("X-User-ID", "anonymous")

    def _get_tenant_id(self, request: Request) -> Optional[str]:
        """Get tenant ID from request header."""
        return request.headers.get("X-Tenant-ID")

    def _get_permissions(self, request: Request) -> List[str]:
        """Get permissions from request header."""
        # In a real app, these would be derived from the user's role
        # or from a token's claims
        return ["products:read", "products:write", "orders:read", "orders:write"]


# Setup and example app


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
    product_service = ProductService(
        entity_type=Product,
        read_permission="products:read",
        write_permission="products:write",
    )
    registry.register("ProductService", product_service)

    order_service = OrderService(
        aggregate_type=Order,
        product_service=product_service,
        read_permission="orders:read",
        write_permission="orders:write",
    )
    registry.register("OrderService", order_service)

    # Create FastAPI app
    app = FastAPI(title="Uno Example API")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create API router
    router = APIRouter()

    # Register custom context provider
    global default_context_provider
    from uno.api.service_api import default_context_provider

    default_context_provider = ExampleContextProvider()

    # Create API registry
    api_registry = ServiceApiRegistry(router, registry)

    # Register APIs
    api_registry.register_entity_api(
        entity_type=Product,
        prefix="/products",
        tags=["Products"],
        service_name="ProductService",
        create_dto=ProductCreateDto,
        update_dto=ProductUpdateDto,
        response_model=ProductResponseDto,
    )

    # Register custom order API
    order_api = OrderApi(
        aggregate_type=Order,
        service=order_service,
        router=router,
        prefix="/orders",
        tags=["Orders"],
        create_dto=OrderCreateDto,
        update_dto=OrderUpdateDto,
        response_model=OrderResponseDto,
    )

    # Include router in app
    app.include_router(router, prefix="/api/v1")

    return app


def run_api():
    """Run the example API."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Create and run the app
    app = asyncio.run(setup_example())
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run_api()
