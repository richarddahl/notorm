"""
Domain Service API Integration Example.

This module demonstrates how to use the domain service endpoint factory to create API endpoints
that integrate with domain services, showing the complete flow from domain model to API.
"""

import logging
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any, Annotated
from uuid import uuid4

from fastapi import FastAPI, APIRouter, Depends, Query
from pydantic import BaseModel, Field, EmailStr

from uno.core.errors.result import Result, Success, Failure
from uno.core.events import UnoEvent, event_handler
from uno.domain.core import Entity, AggregateRoot
from uno.core.base.respository import Repository
from uno.domain.unit_of_work import UnitOfWork
from uno.domain.unified_services import (
    DomainService,
    ReadOnlyDomainService,
    EntityService,
    DomainServiceFactory,
    initialize_service_factory,
)
from uno.api.service_endpoint_adapter import DomainServiceAdapter, EntityServiceAdapter
from uno.api.service_endpoint_factory import (
    DomainServiceEndpointFactory,
    get_domain_service_endpoint_factory,
)


# ======================================================================
# Domain Model
# ======================================================================


class User(Entity):
    """User entity in the domain model."""

    def __init__(
        self,
        id: Optional[str] = None,
        email: str = "",
        username: str = "",
        full_name: Optional[str] = None,
        is_active: bool = True,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        **kwargs,
    ):
        """Initialize User entity."""
        self.id = id or str(uuid4())
        self.email = email
        self.username = username
        self.full_name = full_name
        self.is_active = is_active
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or self.created_at

        # Domain events collection for this entity
        self.events: List[UnoEvent] = []

    def update(self) -> None:
        """Update timestamp when the entity is modified."""
        self.updated_at = datetime.now(UTC)

    def deactivate(self) -> None:
        """Deactivate the user."""
        if not self.is_active:
            return

        self.is_active = False
        self.update()

        # Record an event
        self.events.append(
            UserDeactivatedEvent(
                aggregate_id=self.id, aggregate_type="User", username=self.username
            )
        )

    def get_events(self) -> List[UnoEvent]:
        """Get and clear events."""
        events = self.events.copy()
        self.events.clear()
        return events


class Order(AggregateRoot):
    """Order aggregate root in the domain model."""

    def __init__(
        self,
        id: Optional[str] = None,
        user_id: Optional[str] = None,
        items: Optional[List[Dict[str, Any]]] = None,
        status: str = "new",
        total_amount: float = 0.0,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: int = 1,
        **kwargs,
    ):
        """Initialize Order aggregate."""
        self.id = id or str(uuid4())
        self.user_id = user_id
        self.items = items or []
        self.status = status
        self.total_amount = total_amount
        self.created_at = created_at or datetime.now(UTC)
        self.updated_at = updated_at or self.created_at
        self.version = version

        # Domain events collection
        self.events: List[UnoEvent] = []

    def update(self) -> None:
        """Update timestamp and version when the aggregate is modified."""
        self.updated_at = datetime.now(UTC)
        self.version += 1

    def add_item(self, product_id: str, quantity: int, price: float) -> None:
        """Add an item to the order."""
        # Add the new item
        self.items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "price": price,
                "item_total": quantity * price,
            }
        )

        # Recalculate total
        self.recalculate_total()

        # Update timestamp and version
        self.update()

        # Record an event
        self.events.append(
            OrderItemAddedEvent(
                aggregate_id=self.id,
                aggregate_type="Order",
                product_id=product_id,
                quantity=quantity,
            )
        )

    def recalculate_total(self) -> None:
        """Recalculate the order total."""
        self.total_amount = sum(item.get("item_total", 0) for item in self.items)

    def place(self) -> None:
        """Place the order."""
        if self.status != "new":
            raise ValueError(f"Cannot place order with status {self.status}")

        if not self.items:
            raise ValueError("Cannot place an empty order")

        self.status = "placed"
        self.update()

        # Record an event
        self.events.append(
            OrderPlacedEvent(
                aggregate_id=self.id,
                aggregate_type="Order",
                user_id=self.user_id,
                total_amount=self.total_amount,
            )
        )

    def apply_changes(self) -> None:
        """Apply changes to ensure invariants and increment version."""
        self.recalculate_total()
        self.update()

    def get_events(self) -> List[UnoEvent]:
        """Get accumulated events."""
        return self.events.copy()

    def clear_events(self) -> List[UnoEvent]:
        """Get and clear events."""
        events = self.events.copy()
        self.events.clear()
        return events


# ======================================================================
# Domain Events
# ======================================================================


class UserDeactivatedEvent(UnoEvent):
    """Event raised when a user is deactivated."""

    username: str


class OrderItemAddedEvent(UnoEvent):
    """Event raised when an item is added to an order."""

    product_id: str
    quantity: int


class OrderPlacedEvent(UnoEvent):
    """Event raised when an order is placed."""

    user_id: str
    total_amount: float


# ======================================================================
# Repositories
# ======================================================================


class InMemoryUserRepository(Repository[User]):
    """In-memory implementation of the user repository."""

    def __init__(self):
        """Initialize repository with empty storage."""
        self.users: Dict[str, User] = {}

    async def get(self, id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(id)

    async def add(self, entity: User) -> User:
        """Add a new user."""
        self.users[entity.id] = entity
        return entity

    async def update(self, entity: User) -> User:
        """Update an existing user."""
        self.users[entity.id] = entity
        return entity

    async def remove(self, entity: User) -> None:
        """Remove a user."""
        if entity.id in self.users:
            del self.users[entity.id]

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[User]:
        """List users with optional filtering and pagination."""
        result = list(self.users.values())

        # Apply filters
        if filters:
            for key, value in filters.items():
                result = [u for u in result if getattr(u, key, None) == value]

        # Apply pagination
        if offset is not None:
            result = result[offset:]

        if limit is not None:
            result = result[:limit]

        return result

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count users with optional filtering."""
        if not filters:
            return len(self.users)

        count = 0
        for user in self.users.values():
            matches = True
            for key, value in filters.items():
                if getattr(user, key, None) != value:
                    matches = False
                    break
            if matches:
                count += 1

        return count

    def collect_events(self) -> List[UnoEvent]:
        """Collect domain events from entities."""
        events = []
        for user in self.users.values():
            if hasattr(user, "get_events") and callable(user.get_events):
                events.extend(user.get_events())
        return events


class InMemoryOrderRepository(Repository[Order]):
    """In-memory implementation of the order repository."""

    def __init__(self):
        """Initialize repository with empty storage."""
        self.orders: Dict[str, Order] = {}

    async def get(self, id: str) -> Optional[Order]:
        """Get an order by ID."""
        return self.orders.get(id)

    async def add(self, entity: Order) -> Order:
        """Add a new order."""
        self.orders[entity.id] = entity
        return entity

    async def update(self, entity: Order) -> Order:
        """Update an existing order."""
        self.orders[entity.id] = entity
        return entity

    async def remove(self, entity: Order) -> None:
        """Remove an order."""
        if entity.id in self.orders:
            del self.orders[entity.id]

    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order_by: Optional[List[str]] = None,
    ) -> List[Order]:
        """List orders with optional filtering and pagination."""
        result = list(self.orders.values())

        # Apply filters
        if filters:
            for key, value in filters.items():
                result = [o for o in result if getattr(o, key, None) == value]

        # Apply pagination
        if offset is not None:
            result = result[offset:]

        if limit is not None:
            result = result[:limit]

        return result

    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count orders with optional filtering."""
        if not filters:
            return len(self.orders)

        count = 0
        for order in self.orders.values():
            matches = True
            for key, value in filters.items():
                if getattr(order, key, None) != value:
                    matches = False
                    break
            if matches:
                count += 1

        return count

    def collect_events(self) -> List[UnoEvent]:
        """Collect domain events from aggregates."""
        events = []
        for order in self.orders.values():
            if hasattr(order, "get_events") and callable(order.get_events):
                events.extend(order.get_events())
        return events


# ======================================================================
# Unit of Work
# ======================================================================


class InMemoryUnitOfWork(UnitOfWork):
    """In-memory implementation of the unit of work."""

    def __init__(
        self,
        user_repository: InMemoryUserRepository,
        order_repository: InMemoryOrderRepository,
    ):
        """Initialize with repositories."""
        self.users = user_repository
        self.orders = order_repository
        self._committed = False

    @property
    def repositories(self) -> List[Repository]:
        """Get all repositories managed by this unit of work."""
        return [self.users, self.orders]

    async def __aenter__(self) -> "InMemoryUnitOfWork":
        """Enter the context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager."""
        if exc_type is not None:
            # An exception occurred, so we don't commit
            return

        if not self._committed:
            # No explicit commit was called, so we rollback
            pass

    async def commit(self) -> None:
        """Commit the transaction."""
        self._committed = True

    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass


class UnitOfWorkFactory:
    """Factory for creating units of work."""

    def __init__(
        self,
        user_repository: InMemoryUserRepository,
        order_repository: InMemoryOrderRepository,
    ):
        """Initialize with repositories."""
        self.user_repository = user_repository
        self.order_repository = order_repository

    def create_uow(self) -> InMemoryUnitOfWork:
        """Create a new unit of work."""
        return InMemoryUnitOfWork(self.user_repository, self.order_repository)


# ======================================================================
# Domain Services
# ======================================================================

# --- Input/Output Models ---


class CreateUserInput(BaseModel):
    """Input model for user creation."""

    email: EmailStr
    username: str
    full_name: Optional[str] = None

    class Config:
        frozen = True


class UserOutput(BaseModel):
    """Output model for user responses."""

    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserList(BaseModel):
    """Model for paginated user list response."""

    items: List[UserOutput]
    total: int
    page: int
    page_size: int


class SearchUsersInput(BaseModel):
    """Input model for user search."""

    username_contains: Optional[str] = None
    email_contains: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        frozen = True


class DeactivateUserInput(BaseModel):
    """Input model for user deactivation."""

    user_id: str

    class Config:
        frozen = True


class CreateOrderInput(BaseModel):
    """Input model for order creation."""

    user_id: str
    items: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        frozen = True


class OrderItemInput(BaseModel):
    """Input model for adding an item to an order."""

    order_id: str
    product_id: str
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    class Config:
        frozen = True


class PlaceOrderInput(BaseModel):
    """Input model for placing an order."""

    order_id: str

    class Config:
        frozen = True


class OrderOutput(BaseModel):
    """Output model for order responses."""

    id: str
    user_id: str
    items: List[Dict[str, Any]]
    status: str
    total_amount: float
    created_at: datetime
    updated_at: datetime
    version: int


# --- Domain Services ---


class CreateUserService(DomainService[CreateUserInput, UserOutput, InMemoryUnitOfWork]):
    """Service for creating new users."""

    async def _execute_internal(
        self, input_data: CreateUserInput
    ) -> Result[UserOutput]:
        """Create a new user."""
        # Check if username already exists
        existing_users = await self.uow.users.list({"username": input_data.username})
        if existing_users:
            return Failure("Username already exists", error_code="DUPLICATE_USERNAME")

        # Check if email already exists
        existing_users = await self.uow.users.list({"email": input_data.email})
        if existing_users:
            return Failure("Email already exists", error_code="DUPLICATE_EMAIL")

        # Create user entity
        user = User(
            email=input_data.email,
            username=input_data.username,
            full_name=input_data.full_name,
        )

        # Save to repository
        await self.uow.users.add(user)

        # Convert to output model and return
        return Success(
            UserOutput(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )


class SearchUsersService(
    ReadOnlyDomainService[SearchUsersInput, UserList, InMemoryUnitOfWork]
):
    """Service for searching users."""

    async def _execute_internal(self, input_data: SearchUsersInput) -> Result[UserList]:
        """Search for users based on criteria."""
        # Build filters
        filters = {}

        if input_data.is_active is not None:
            filters["is_active"] = input_data.is_active

        # Execute query - for a real implementation, this would be more sophisticated
        users = await self.uow.users.list(filters)

        # Apply additional filters that aren't directly supported by the repository
        if input_data.username_contains:
            users = [
                u
                for u in users
                if input_data.username_contains.lower() in u.username.lower()
            ]

        if input_data.email_contains:
            users = [
                u for u in users if input_data.email_contains.lower() in u.email.lower()
            ]

        # Get total count
        total = len(users)

        # Convert to output models
        user_outputs = [
            UserOutput(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
            for user in users
        ]

        # Return paginated result
        return Success(
            UserList(
                items=user_outputs,
                total=total,
                page=1,  # Fixed for this example
                page_size=len(user_outputs),
            )
        )


class DeactivateUserService(
    DomainService[DeactivateUserInput, UserOutput, InMemoryUnitOfWork]
):
    """Service for deactivating users."""

    async def _execute_internal(
        self, input_data: DeactivateUserInput
    ) -> Result[UserOutput]:
        """Deactivate a user."""
        # Get the user
        user = await self.uow.users.get(input_data.user_id)
        if not user:
            return Failure(
                f"User with ID {input_data.user_id} not found",
                error_code="USER_NOT_FOUND",
            )

        # Deactivate the user
        user.deactivate()

        # Update in repository
        await self.uow.users.update(user)

        # Convert to output model and return
        return Success(
            UserOutput(
                id=user.id,
                email=user.email,
                username=user.username,
                full_name=user.full_name,
                is_active=user.is_active,
                created_at=user.created_at,
                updated_at=user.updated_at,
            )
        )


class CreateOrderService(
    DomainService[CreateOrderInput, OrderOutput, InMemoryUnitOfWork]
):
    """Service for creating new orders."""

    async def _execute_internal(
        self, input_data: CreateOrderInput
    ) -> Result[OrderOutput]:
        """Create a new order."""
        # Check if user exists
        user = await self.uow.users.get(input_data.user_id)
        if not user:
            return Failure(
                f"User with ID {input_data.user_id} not found",
                error_code="USER_NOT_FOUND",
            )

        # Create order aggregate
        order = Order(user_id=input_data.user_id, items=input_data.items)

        # Apply initial changes (calculate totals, etc.)
        order.apply_changes()

        # Save to repository
        await self.uow.orders.add(order)

        # Convert to output model and return
        return Success(
            OrderOutput(
                id=order.id,
                user_id=order.user_id,
                items=order.items,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                updated_at=order.updated_at,
                version=order.version,
            )
        )


class AddOrderItemService(
    DomainService[OrderItemInput, OrderOutput, InMemoryUnitOfWork]
):
    """Service for adding items to an order."""

    async def _execute_internal(
        self, input_data: OrderItemInput
    ) -> Result[OrderOutput]:
        """Add an item to an order."""
        # Get the order
        order = await self.uow.orders.get(input_data.order_id)
        if not order:
            return Failure(
                f"Order with ID {input_data.order_id} not found",
                error_code="ORDER_NOT_FOUND",
            )

        # Check if order can be modified
        if order.status != "new":
            return Failure(
                f"Cannot modify order with status {order.status}",
                error_code="INVALID_ORDER_STATUS",
            )

        # Add the item
        order.add_item(
            product_id=input_data.product_id,
            quantity=input_data.quantity,
            price=input_data.price,
        )

        # Update in repository
        await self.uow.orders.update(order)

        # Convert to output model and return
        return Success(
            OrderOutput(
                id=order.id,
                user_id=order.user_id,
                items=order.items,
                status=order.status,
                total_amount=order.total_amount,
                created_at=order.created_at,
                updated_at=order.updated_at,
                version=order.version,
            )
        )


class PlaceOrderService(
    DomainService[PlaceOrderInput, OrderOutput, InMemoryUnitOfWork]
):
    """Service for placing orders."""

    async def _execute_internal(
        self, input_data: PlaceOrderInput
    ) -> Result[OrderOutput]:
        """Place an order."""
        # Get the order
        order = await self.uow.orders.get(input_data.order_id)
        if not order:
            return Failure(
                f"Order with ID {input_data.order_id} not found",
                error_code="ORDER_NOT_FOUND",
            )

        try:
            # Place the order
            order.place()

            # Update in repository
            await self.uow.orders.update(order)

            # Convert to output model and return
            return Success(
                OrderOutput(
                    id=order.id,
                    user_id=order.user_id,
                    items=order.items,
                    status=order.status,
                    total_amount=order.total_amount,
                    created_at=order.created_at,
                    updated_at=order.updated_at,
                    version=order.version,
                )
            )
        except ValueError as e:
            return Failure(str(e), error_code="INVALID_ORDER_STATE")


# ======================================================================
# Event Handlers
# ======================================================================


@event_handler(UserDeactivatedEvent)
async def handle_user_deactivated(event: UserDeactivatedEvent) -> None:
    """Handle user deactivated events."""
    print(
        f"User {event.username} has been deactivated (aggregate ID: {event.aggregate_id})"
    )


@event_handler(OrderPlacedEvent)
async def handle_order_placed(event: OrderPlacedEvent) -> None:
    """Handle order placed events."""
    print(
        f"Order {event.aggregate_id} has been placed by user {event.user_id} "
        f"with total amount {event.total_amount}"
    )


# ======================================================================
# API Integration
# ======================================================================

# --- API Models ---

# Note: For this example, we're reusing our domain DTOs for the API.
# In a real application, you might want separate API DTOs with different validations.

# --- API Endpoints Setup ---


def setup_domain_endpoints(app: FastAPI) -> None:
    """Set up domain service endpoints for the application."""
    # Create router for domain endpoints
    router = APIRouter(prefix="/api/v1", tags=["Domain"])

    # Get endpoint factory
    endpoint_factory = get_domain_service_endpoint_factory()

    # Create user endpoints
    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=CreateUserService,
        path="/users",
        method="POST",
        summary="Create User",
        description="Create a new user in the system",
        response_model=UserOutput,
        status_code=201,
    )

    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=SearchUsersService,
        path="/users/search",
        method="POST",
        summary="Search Users",
        description="Search for users based on criteria",
        response_model=UserList,
    )

    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=DeactivateUserService,
        path="/users/deactivate",
        method="POST",
        summary="Deactivate User",
        description="Deactivate a user account",
        response_model=UserOutput,
    )

    # Create order endpoints
    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=CreateOrderService,
        path="/orders",
        method="POST",
        summary="Create Order",
        description="Create a new order",
        response_model=OrderOutput,
        status_code=201,
    )

    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=AddOrderItemService,
        path="/orders/add-item",
        method="POST",
        summary="Add Order Item",
        description="Add an item to an existing order",
        response_model=OrderOutput,
    )

    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=PlaceOrderService,
        path="/orders/place",
        method="POST",
        summary="Place Order",
        description="Place an existing order",
        response_model=OrderOutput,
    )

    # Create entity service CRUD endpoints for User
    endpoint_factory.create_entity_service_endpoints(
        router=router,
        entity_type=User,
        path_prefix="/users",
        tags=["Users"],
        input_model=UserOutput,  # Using output model as input for CRUD operations
        output_model=UserOutput,
    )

    # Create entity service CRUD endpoints for Order
    endpoint_factory.create_entity_service_endpoints(
        router=router,
        entity_type=Order,
        path_prefix="/orders",
        tags=["Orders"],
        input_model=OrderOutput,  # Using output model as input for CRUD operations
        output_model=OrderOutput,
    )

    # Register the router with the application
    app.include_router(router)


# ======================================================================
# Application Setup
# ======================================================================


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Create repositories
    user_repository = InMemoryUserRepository()
    order_repository = InMemoryOrderRepository()

    # Create unit of work factory
    uow_factory = UnitOfWorkFactory(user_repository, order_repository)

    # Initialize service factory
    initialize_service_factory(uow_factory)

    # Register entity types with service factory
    service_factory = get_service_factory()
    service_factory.register_entity_type(User, user_repository)
    service_factory.register_entity_type(Order, order_repository)

    # Create FastAPI app
    app = FastAPI(
        title="Domain Service API Example",
        description="Example showing domain services integration with API endpoints",
        version="1.0.0",
    )

    # Set up domain endpoints
    setup_domain_endpoints(app)

    return app


# Create the application
app = create_app()


# ======================================================================
# Run the application (for development)
# ======================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("service_endpoint_example:app", host="0.0.0.0", port=8000, reload=True)
