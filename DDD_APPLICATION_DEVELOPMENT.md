# Domain-Driven Design Application Development Guide for Uno Framework

This document provides a comprehensive guide for implementing DDD-based applications using the uno framework, along with the improvements made to create a cohesive domain model implementation.

## Domain Model Implementation

I've identified and resolved inconsistencies in the domain model implementation across the codebase, with multiple competing implementations in `core.py`, `models/base.py`, and `model.py`. To resolve this, I've:

1. Created a unified implementation in `core.py` that combines the best aspects of each approach
2. Moved common value objects to a dedicated `value_objects.py` module
3. Updated all domain models to use the new unified implementation 
4. Removed redundant implementations to ensure consistency

### Key Improvements Made

1. **Unified Domain Model Classes**
   - Consolidated all domain model base classes into a single implementation in `core.py`
   - Created consistent inheritance and behavior patterns
   - Used modern Python typing features for better type safety
   - Implemented Pydantic validation properly

2. **Standardized Value Objects**
   - Implemented immutable value objects with proper validation
   - Added a generic `PrimitiveValueObject` for simple value types 
   - Used proper equality and hash implementations
   - Created common value objects (Email, Money, Address) in a dedicated module

3. **Improved Entity Implementation**
   - Created a clear separation between entities and aggregate roots
   - Implemented proper identity-based equality
   - Added consistent event tracking
   - Used proper encapsulation with private attributes

4. **Enhanced Aggregate Root**
   - Added version field for optimistic concurrency control
   - Implemented proper child entity management
   - Provided consistent invariant checking

5. **Files Removed**
   - `src/uno/domain/models/base.py` - redundant entity/value object implementations
   - `src/uno/domain/model.py` - duplicative domain model implementation

### Core Domain Model Classes

The unified domain model in `core.py` now provides these key components:

#### 1. Value Objects

```python
class ValueObject(BaseModel):
    """
    Base class for value objects.

    Value objects:
    - Are immutable objects defined by their attributes
    - Have no identity
    - Are equatable by their attributes
    - Cannot be changed after creation
    """

    model_config = ConfigDict(frozen=True)

    @model_validator(mode='after')
    def validate_value_object(self) -> 'ValueObject':
        """Validate the value object after initialization."""
        self.validate()
        return self
    
    def validate(self) -> None:
        """
        Validate the value object.
        
        Override this method to implement specific validation logic.
        """
        pass

    def __eq__(self, other: Any) -> bool:
        """Value objects are equal if they have the same type and attributes."""
        if not isinstance(other, self.__class__):
            return False
        return self.model_dump() == other.model_dump()

    def __hash__(self) -> int:
        """Hash based on all attributes."""
        return hash(tuple(sorted(self.model_dump().items())))
```

#### 2. Primitive Value Objects

```python
class PrimitiveValueObject(ValueObject, Generic[V]):
    """
    Value object that wraps a primitive value.
    
    Use this for domain values that need validation or semantic meaning
    beyond what a primitive type provides, e.g., EmailAddress, Money.
    """
    
    value: V
    
    def __str__(self) -> str:
        """String representation of the primitive value."""
        return str(self.value)
    
    @classmethod
    def create(cls, value: V) -> 'PrimitiveValueObject[V]':
        """Create a new primitive value object."""
        return cls(value=value)
```

#### 3. Entities

```python
class Entity(BaseModel, Generic[T_ID]):
    """
    Base class for domain entities.

    Entities:
    - Have a distinct identity that persists through state changes
    - Are equatable by their identity, not their attributes
    - May change over time
    - Can register domain events
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    id: T_ID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = None
    
    # Domain events - excluded from serialization
    _events: List[DomainEvent] = Field(default_factory=list, exclude=True)

    def __eq__(self, other: Any) -> bool:
        """Entities are equal if they have the same type and ID."""
        if not isinstance(other, self.__class__):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on the entity's ID."""
        return hash(self.id)

    @model_validator(mode="before")
    def set_updated_at(cls, values):
        """Update the updated_at field whenever the entity is modified."""
        if isinstance(values, dict) and values.get("id") and values.get("created_at"):
            values["updated_at"] = datetime.now(UTC)
        return values

    def add_event(self, event: DomainEvent) -> None:
        """Add a domain event to this entity."""
        self._events.append(event)

    def clear_events(self) -> List[DomainEvent]:
        """Clear and return all domain events."""
        events = list(self._events)
        self._events.clear()
        return events
    
    def get_events(self) -> List[DomainEvent]:
        """Get all domain events without clearing them."""
        return list(self._events)
```

#### 4. Aggregate Roots

```python
class AggregateRoot(Entity[T_ID]):
    """
    Base class for aggregate roots.

    Aggregate Roots:
    - Are entities that are the root of an aggregate
    - Maintain consistency boundaries
    - Manage lifecycle of child entities
    - Enforce invariants across the aggregate
    - Coordinate domain events for the aggregate
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Version for optimistic concurrency control
    version: int = Field(default=1)
    
    # Child entities - excluded from serialization
    _child_entities: Set[Entity] = Field(default_factory=set, exclude=True)

    def check_invariants(self) -> None:
        """
        Check that the aggregate invariants are maintained.
        
        Override this method to implement specific invariant checks.
        """
        pass

    def apply_changes(self) -> None:
        """
        Apply any pending changes and ensure consistency.
        
        This method should be called before saving the aggregate to ensure
        that it is in a valid state and to update metadata.
        """
        self.check_invariants()
        self.updated_at = datetime.now(UTC)
        self.version += 1

    def add_child_entity(self, entity: Entity) -> None:
        """Register a child entity with this aggregate root."""
        self._child_entities.add(entity)
        
    def remove_child_entity(self, entity: Entity) -> None:
        """Remove a child entity from this aggregate root."""
        self._child_entities.discard(entity)

    def get_child_entities(self) -> Set[Entity]:
        """Get all child entities of this aggregate root."""
        return self._child_entities.copy()
```

#### 5. Domain Events

```python
class DomainEvent(BaseModel):
    """
    Base class for domain events.

    Domain events represent something significant that occurred within the domain.
    They are immutable records of what happened, used to communicate between
    different parts of the application.
    """

    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = Field(default="domain_event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: Optional[str] = None
    aggregate_type: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to a dictionary."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DomainEvent":
        """Create an event from a dictionary."""
        return cls(**data)
```

### Common Value Objects

I've also created a dedicated `value_objects.py` module for common value objects:

```python
class Email(PrimitiveValueObject[str]):
    """Email address value object."""
    
    def validate(self) -> None:
        """Validate email address."""
        if not self.value:
            raise ValueError("Email cannot be empty")
        if "@" not in self.value:
            raise ValueError("Email must contain @")
        if "." not in self.value.split("@")[1]:
            raise ValueError("Email must have a valid domain")
    
    @field_validator('value')
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Normalize email to lowercase."""
        return v.lower() if isinstance(v, str) else v


class Money(ValueObject):
    """Money value object."""
    
    amount: float
    currency: str = "USD"
    
    def validate(self) -> None:
        """Validate money."""
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.currency not in {"USD", "EUR", "GBP", "JPY", "CNY", "CAD", "AUD"}:
            raise ValueError(f"Unsupported currency: {self.currency}")
    
    def add(self, other: 'Money') -> 'Money':
        """Add money."""
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(amount=self.amount + other.amount, currency=self.currency)
    
    def subtract(self, other: 'Money') -> 'Money':
        """Subtract money."""
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        result = self.amount - other.amount
        if result < 0:
            raise ValueError("Result cannot be negative")
        return Money(amount=result, currency=self.currency)


class Address(ValueObject):
    """Address value object."""
    
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    
    def validate(self) -> None:
        """Validate address."""
        if not self.street:
            raise ValueError("Street cannot be empty")
        if not self.city:
            raise ValueError("City cannot be empty")
        if not self.zip_code:
            raise ValueError("Zip code cannot be empty")
```

## Key Design Decisions

### 1. Pydantic Integration

The new implementation fully leverages Pydantic v2 for:
- Validation through model validators
- Type safety with proper generics
- Immutability of value objects
- Serialization/deserialization

### 2. Modern Python Features

- Uses UTC timezone through the `datetime.UTC` constant for Python 3.11+
- Leverages proper type hints with generics
- Uses property decorators and field validation

### 3. Encapsulation Improvements

- Private attributes for events and child entities using underscore prefix
- Clear separation between public API and internal state
- Consistent methods for managing entity lifecycle

### 4. Value Object Design

- True immutability through Pydantic's frozen config
- Consistent validation through a validation hook
- Proper equality and hash implementations

### 5. Entity Design

- Clear separation between entity and aggregate root
- Proper identity-based equality
- Automatic timestamp updating
- Consistent event tracking

## Updated Model Import Structure

The domain models package structure has been updated:

```python
# From uno.domain.models/__init__.py
from uno.domain.core import (
    DomainEvent,
    ValueObject,
    PrimitiveValueObject,
    Entity,
    AggregateRoot,
)

from uno.domain.value_objects import (
    Email,
    Money,
    Address,
)

from uno.domain.models.user import (
    User,
    UserRole,
)

from uno.domain.models.product import (
    Product,
    ProductCategory,
)

from uno.domain.models.order import (
    Order,
    OrderStatus,
    OrderItem,
)
```

## Example Usage

Here's how to use the new unified domain model:

### 1. Define Domain Events

```python
class OrderCreatedEvent(DomainEvent):
    """Event fired when a new order is created."""
    
    order_id: str
    customer_id: str
    
    model_config = ConfigDict(
        frozen=True,
        json_schema_extra={
            "event_type": "order.created"
        }
    )
```

### 2. Create Entity Models

```python
class Product(Entity):
    """Product entity."""
    
    name: str
    description: str
    price: Money
    sku: str
    
    def update_price(self, new_price: Money) -> None:
        """Update the product price."""
        old_price = self.price
        self.price = new_price
        self.add_event(ProductPriceChangedEvent(
            product_id=str(self.id),
            old_price=old_price.to_dict(),
            new_price=new_price.to_dict()
        ))
```

### 3. Create Aggregate Roots

```python
class User(AggregateRoot):
    """User aggregate root."""
    
    username: str
    email: Email
    addresses: List[Address] = Field(default_factory=list)
    
    def add_address(self, address: Address) -> None:
        """Add an address to the user."""
        self.addresses.append(address)
        self.updated_at = datetime.now(UTC)
    
    def check_invariants(self) -> None:
        """Check user invariants."""
        if not self.username:
            raise ValueError("Username is required")
        if not self.email:
            raise ValueError("Email is required")
```

## Repository Pattern Implementation

The repository pattern has been standardized to align with the unified domain model. The new implementation provides a consistent interface for data access across different storage mechanisms.

### Key Components

#### 1. Repository Base Class

```python
class Repository(Generic[T], ABC):
    """
    Abstract base repository for domain entities.
    
    This class provides a standardized interface for repository operations,
    abstracting the persistence details from the domain layer.
    """
    
    def __init__(self, entity_type: Type[T], logger: Optional[logging.Logger] = None):
        """Initialize the repository."""
        self.entity_type = entity_type
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    async def get(self, id: Any) -> Optional[T]:
        """Get an entity by ID."""
        pass
    
    async def get_by_id(self, id: Any) -> Result[T]:
        """Get an entity by ID with result object."""
        try:
            entity = await self.get(id)
            if entity is None:
                return Failure(f"Entity with ID {id} not found")
            return Success(entity)
        except Exception as e:
            return Failure(str(e))
    
    @abstractmethod
    async def find(self, specification: Specification[T]) -> List[T]:
        """Find entities matching a specification."""
        pass
    
    @abstractmethod
    async def add(self, entity: T) -> T:
        """Add a new entity."""
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass
    
    @abstractmethod
    async def remove(self, entity: T) -> None:
        """Remove an entity."""
        pass
```

#### 2. Aggregate Repository

```python
class AggregateRepository(Repository[A], Generic[A]):
    """
    Repository for aggregate roots.
    
    This repository extends the base repository with methods for working with
    aggregate roots, including event collection and lifecycle management.
    """
    
    def __init__(self, aggregate_type: Type[A], logger: Optional[logging.Logger] = None):
        """Initialize the aggregate repository."""
        super().__init__(aggregate_type, logger)
        self._pending_events: List[DomainEvent] = []
    
    async def save(self, aggregate: A) -> A:
        """
        Save an aggregate (create or update).
        
        This method applies changes to the aggregate, collects events,
        and persists the aggregate to the repository.
        """
        # Apply changes to ensure invariants and increment version
        aggregate.apply_changes()
        
        # Collect events
        self._collect_events(aggregate)
        
        # Determine if this is a create or update
        exists = await self.exists(aggregate.id)
        
        # Save the aggregate
        if exists:
            return await self.update(aggregate)
        else:
            return await self.add(aggregate)
    
    def collect_events(self) -> List[DomainEvent]:
        """
        Collect all pending domain events.
        
        Returns:
            List of pending domain events
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events
```

#### 3. SQLAlchemy Implementations

```python
class SQLAlchemyRepository(Repository[T], Generic[T, M]):
    """
    SQLAlchemy implementation of the repository pattern.
    
    This repository uses SQLAlchemy for data access, with support for both
    ORM and Core approaches.
    """
    
    def __init__(
        self,
        entity_type: Type[T],
        session: AsyncSession,
        model_class: Type[M],
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the SQLAlchemy repository."""
        super().__init__(entity_type, logger)
        self.session = session
        self.model_class = model_class
```

#### 4. In-Memory Implementations

```python
class InMemoryRepository(Repository[T], Generic[T]):
    """
    In-memory implementation of the repository pattern.
    
    This repository stores entities in memory, making it useful for testing.
    """
    
    def __init__(self, entity_type: Type[T], logger: Optional[logging.Logger] = None):
        """Initialize the in-memory repository."""
        super().__init__(entity_type, logger)
        self.entities: Dict[Any, T] = {}
```

### Specification Pattern Integration

The repository pattern integrates with the specification pattern for complex querying:

```python
class ProductSpecification:
    """Specifications for product entities."""
    
    @staticmethod
    def in_stock() -> Specification[Product]:
        """Create a specification for in-stock products."""
        return AttributeSpecification("in_stock", True)
    
    @staticmethod
    def price_between(min_price: float, max_price: float) -> Specification[Product]:
        """Create a specification for products in a price range."""
        return PredicateSpecification(
            lambda product: min_price <= product.price.amount <= max_price,
            f"price_between_{min_price}_{max_price}"
        )

# Find products using a specification
spec = ProductSpecification.in_stock().and_(
    ProductSpecification.price_between(10.0, 50.0)
)
in_stock_affordable_products = await product_repository.find(spec)
```

### Specification Translators

The `SpecificationTranslator` converts domain specifications to database queries:

```python
from uno.domain.specification_translators import SQLAlchemySpecificationTranslator

# Create a translator
translator = SQLAlchemySpecificationTranslator(ProductModel)

# Translate a specification to a SQLAlchemy query
query = translator.translate(spec)

# Execute the query
result = await session.execute(query)
models = result.scalars().all()
```

### Unit of Work Integration

Repositories work with the Unit of Work pattern to ensure transactional consistency:

```python
from uno.domain.unit_of_work_standardized import SQLAlchemyUnitOfWork

async with SQLAlchemyUnitOfWork(session) as uow:
    # Get repositories
    product_repo = uow.get_repository(Product)
    order_repo = uow.get_repository(Order)
    
    # Make changes
    product = await product_repo.get_by_id("123")
    order = Order(
        customer_id="456",
        items=[OrderItem(product_id=product.id, quantity=2, price=product.price)]
    )
    
    await order_repo.add(order)
    
    # Commit the transaction
    await uow.commit()
    
    # Collect and publish events
    events = order_repo.collect_events()
    for event in events:
        await event_bus.publish(event)
```

### Repository Factory

The `RepositoryFactory` simplifies the creation of repositories:

```python
from uno.domain.repository_factory import repository_factory

# Register models
repository_factory.register_model(Product, ProductModel)
repository_factory.register_model(Order, OrderModel)

# Set up the database connection
repository_factory.create_from_connection_string(
    "postgresql+asyncpg://user:password@localhost/dbname"
)

# Create repositories
product_repo = repository_factory.create_repository(Product)
order_repo = repository_factory.create_repository(Order)
```

### Files Created/Updated

1. `src/uno/domain/repository_standardized.py` - Standardized repository implementation
2. `src/uno/domain/unit_of_work_standardized.py` - Standardized unit of work
3. `src/uno/domain/repository_factory.py` - Factory for creating repositories
4. `src/uno/domain/specification_translators.py` - Updated specification translators
5. `docs/domain/repository_pattern.md` - Documentation for the repository pattern

## Unified Event System

I've implemented a unified event system that combines the best aspects of the previously separate event implementations in `uno.core.events` and `uno.domain.events`. The new system provides a consistent approach to handling domain events across the framework.

### Key Improvements Made

1. **Consolidated Event System Implementation**
   - Created a unified implementation in `uno.core.unified_events.py`
   - Simplified API while maintaining advanced capabilities
   - Consistent behavior across synchronous and asynchronous contexts
   - Comprehensive type safety throughout

2. **Enhanced Event Capabilities**
   - Priority-based event handling to control execution order
   - Topic-based event routing for targeted subscriptions
   - Improved event persistence with standardized EventStore interface
   - Support for event tracing using correlation and causation IDs

3. **Multiple Handler Types**
   - Class-based handlers with `EventHandler` base class
   - Function-based handlers with `@event_handler` decorator
   - Subscriber pattern with `EventSubscriber` base class
   - Automatic handler discovery via scanner utilities

4. **Improved Error Handling**
   - Comprehensive error context for debugging
   - Isolated handler execution to prevent cascading failures
   - Integration with the Result pattern for error management

5. **Streamlined Event Publishing**
   - Synchronous publishing for critical events
   - Asynchronous publishing for non-blocking operations
   - Batch publishing for event collections
   - Centralized event bus with dependency injection support

### Core Components

#### Domain Events

```python
from uno.core.unified_events import DomainEvent

class OrderCreatedEvent(DomainEvent):
    """Event raised when a new order is created."""
    
    order_id: str
    user_id: str
    items: List[Dict[str, Any]]
    total_amount: float
```

#### Event Handlers

```python
# Class-based handler
from uno.core.unified_events import EventHandler

class OrderEventHandler(EventHandler[OrderCreatedEvent]):
    def __init__(self):
        super().__init__(OrderCreatedEvent)
        
    async def handle(self, event: OrderCreatedEvent) -> None:
        # Handle the event...
        print(f"Processing order {event.order_id}")

# Function-based handler
from uno.core.unified_events import event_handler, EventPriority

@event_handler(OrderCreatedEvent, priority=EventPriority.HIGH)
async def send_order_confirmation(event: OrderCreatedEvent) -> None:
    # Handle the event...
    print(f"Sending confirmation for order {event.order_id}")
```

#### Event Subscribers

```python
from uno.core.unified_events import EventSubscriber, event_handler

class AnalyticsSubscriber(EventSubscriber):
    def __init__(self, event_bus):
        self.events = []
        super().__init__(event_bus)
    
    @event_handler(OrderCreatedEvent)
    async def track_order_created(self, event: OrderCreatedEvent) -> None:
        self.events.append({
            "type": "order_created",
            "order_id": event.order_id,
            "amount": event.total_amount
        })
```

#### Event Publishing

```python
from uno.core.unified_events import publish_event, publish_event_sync, collect_event, publish_collected_events_async

# Async publishing (non-blocking)
publish_event(OrderCreatedEvent(order_id="123", user_id="456", items=[], total_amount=99.99))

# Sync publishing (blocking)
publish_event_sync(OrderShippedEvent(order_id="123", user_id="456", tracking_number="TRACK123"))

# Batch publishing
collect_event(OrderCreatedEvent(...))
collect_event(PaymentProcessedEvent(...))
await publish_collected_events_async()
```

### Integration with Repositories and Domain Model

```python
class OrderRepository(AggregateRepository[Order]):
    async def save(self, order: Order) -> Order:
        # Apply changes and update version
        order.apply_changes()
        
        # Get domain events
        events = order.clear_events()
        
        # Save to database
        result = await super().save(order)
        
        # Publish events
        for event in events:
            publish_event(event)
            
        return result
```

### Example Usage

A complete example demonstrating the unified event system is available at:
`src/uno/core/examples/unified_events_example.py`

### Documentation and Migration

Comprehensive documentation has been created:

1. `docs/architecture/event_system.md` - Detailed documentation of the unified event system
2. `docs/architecture/event_system_migration.md` - Guide for migrating from previous event implementations

### Files Created/Updated

1. `src/uno/core/unified_events.py` - The new unified event system implementation
2. `src/uno/core/examples/unified_events_example.py` - Example usage of the unified event system
3. `tests/unit/core/test_unified_events.py` - Comprehensive test suite for the unified event system

## Domain Services Implementation

I've implemented a unified domain service pattern that provides a standardized approach to implementing domain services that work with the domain model and event system. The new implementation ensures a consistent API for domain operations, with proper transaction boundaries, error handling, and event management.

### Key Improvements Made

1. **Standardized Service Classes**
   - Created a clear hierarchy of domain service classes with consistent interfaces
   - Implemented transactional boundary management
   - Added proper error handling with the Result pattern
   - Integrated with the unified event system
   - Provided consistent validation hooks

2. **Multiple Service Types**
   - `DomainService` - Base class for services that require transactions
   - `ReadOnlyDomainService` - For query services that don't modify state
   - `EntityService` - For standard CRUD operations on entities
   - `AggregateService` - For operations on aggregate roots with concurrency control

3. **Service Factory**
   - Implemented a factory for creating services with proper dependencies
   - Added registration for entity types and repositories
   - Provided a global factory instance with initialization helpers
   - Enabled dependency injection for services

4. **Integration Features**
   - Transaction management through Unit of Work pattern
   - Event collection and publishing
   - Error handling with the Result pattern
   - Validation hooks for input data
   - Concurrency control for aggregate operations

### Core Components

#### Base Domain Service

```python
class DomainService(Generic[InputT, OutputT, UowT], ABC):
    """
    Base class for domain services that require transactions.
    
    Domain services encapsulate operations that don't naturally belong to
    entities or value objects. They are typically stateless and operate on
    multiple domain objects, providing a clear boundary for business logic.
    """
    
    def __init__(
        self, 
        uow: UowT, 
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize domain service."""
        self.uow = uow
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the domain service operation within a transaction.
        
        This method provides transactional boundaries and error handling
        for the domain operation.
        """
        try:
            # Validate input
            validation_result = self.validate(input_data)
            if validation_result and validation_result.is_failure:
                return validation_result
            
            # Start transaction
            async with self.uow:
                # Execute the domain operation
                result = await self._execute_internal(input_data)
                
                # If successful, commit transaction
                if result.is_success:
                    # Collect events from repositories if they implement collect_events
                    events: List[DomainEvent] = []
                    for repo in self.uow.repositories:
                        if hasattr(repo, "collect_events") and callable(repo.collect_events):
                            events.extend(repo.collect_events())
                    
                    # Collect events from result if it contains events
                    if hasattr(result, "events") and result.events:
                        events.extend(result.events)
                    
                    # Commit the transaction
                    await self.uow.commit()
                    
                    # Publish events after successful commit
                    for event in events:
                        collect_event(event)
                
                return result
                
        except UnoError as e:
            # Known domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))
            
        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(f"Unexpected error in {self.__class__.__name__}: {str(e)}", exc_info=True)
            return Failure(str(e))
    
    def validate(self, input_data: InputT) -> Optional[Result[OutputT]]:
        """
        Validate the input data before execution.
        
        Override this method to implement input validation logic.
        Return None if validation passes, or a Failure result if validation fails.
        """
        return None
    
    @abstractmethod
    async def _execute_internal(self, input_data: InputT) -> Result[OutputT]:
        """
        Internal implementation of the domain service operation.
        
        This method should be implemented by derived classes to provide
        the specific domain logic.
        """
        pass
```

#### Read-Only Domain Service

```python
class ReadOnlyDomainService(Generic[InputT, OutputT, UowT], ABC):
    """
    Base class for read-only domain services.
    
    Read-only domain services perform operations that don't modify domain state,
    such as complex queries or calculations. They don't require transaction
    management but still operate within the domain model.
    """
    
    def __init__(
        self, 
        uow: UowT,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize read-only domain service."""
        self.uow = uow
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def execute(self, input_data: InputT) -> Result[OutputT]:
        """
        Execute the read-only domain service operation.
        """
        try:
            # Validate input
            validation_result = self.validate(input_data)
            if validation_result and validation_result.is_failure:
                return validation_result
                
            # Execute the query operation - no transaction needed
            return await self._execute_internal(input_data)
            
        except UnoError as e:
            # Known domain errors are returned as failures
            self.logger.warning(f"Domain error in {self.__class__.__name__}: {str(e)}")
            return Failure(str(e), error_code=getattr(e, "error_code", None))
            
        except Exception as e:
            # Unexpected errors are logged and returned as failures
            self.logger.error(f"Unexpected error in {self.__class__.__name__}: {str(e)}", exc_info=True)
            return Failure(str(e))
```

#### Entity Service

```python
class EntityService(Generic[E]):
    """
    Service for working with domain entities.
    
    This service provides standard CRUD operations for domain entities,
    using a repository for data access and supporting domain events.
    """
    
    def __init__(
        self, 
        entity_type: Type[E],
        repository: Repository[E],
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the entity service."""
        self.entity_type = entity_type
        self.repository = repository
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def get_by_id(self, id: Any) -> Result[Optional[E]]:
        """Get an entity by ID."""
        try:
            entity = await self.repository.get(id)
            return Success(entity)
        except Exception as e:
            return Failure(str(e))
    
    async def create(self, data: Dict[str, Any]) -> Result[E]:
        """Create a new entity."""
        try:
            # Create entity instance
            entity = self.entity_type(**data)
            
            # Save to repository
            saved_entity = await self.repository.add(entity)
            
            # Publish events
            if hasattr(saved_entity, "get_events"):
                events = saved_entity.get_events()
                for event in events:
                    publish_event(event)
            
            return Success(saved_entity)
        except Exception as e:
            return Failure(str(e))
```

#### Aggregate Service

```python
class AggregateService(Generic[A]):
    """
    Service for working with aggregate roots.
    
    This service provides operations for aggregate roots, ensuring
    proper event handling and transaction boundaries.
    """
    
    def __init__(
        self, 
        aggregate_type: Type[A],
        repository: Repository[A],
        unit_of_work: UnitOfWork,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the aggregate service."""
        self.aggregate_type = aggregate_type
        self.repository = repository
        self.unit_of_work = unit_of_work
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def update(self, id: Any, version: int, data: Dict[str, Any]) -> Result[A]:
        """
        Update an existing aggregate with optimistic concurrency.
        """
        try:
            async with self.unit_of_work:
                # Get existing aggregate
                aggregate = await self.repository.get(id)
                if not aggregate:
                    return Failure(f"Aggregate with ID {id} not found")
                
                # Check version for optimistic concurrency
                if hasattr(aggregate, "version") and aggregate.version != version:
                    return Failure(f"Concurrency conflict: expected version {version}, found {aggregate.version}")
                
                # Update fields
                for key, value in data.items():
                    if hasattr(aggregate, key):
                        setattr(aggregate, key, value)
                
                # Apply changes to ensure invariants and increment version
                aggregate.apply_changes()
                
                # Save to repository
                updated_aggregate = await self.repository.update(aggregate)
                
                # Collect events
                events = []
                if hasattr(updated_aggregate, "clear_events"):
                    events = updated_aggregate.clear_events()
                
                # Commit transaction
                await self.unit_of_work.commit()
                
                # Publish events after successful commit
                for event in events:
                    publish_event(event)
                
                return Success(updated_aggregate)
                
        except Exception as e:
            return Failure(str(e))
```

#### Domain Service Factory

```python
class DomainServiceFactory:
    """
    Factory for creating domain services.
    
    This factory creates and configures domain services with appropriate
    dependencies, such as repositories, units of work, and event bus.
    """
    
    def __init__(
        self,
        unit_of_work_factory: Any,
        event_bus: Optional[EventBus] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize domain service factory."""
        self.unit_of_work_factory = unit_of_work_factory
        self.event_bus = event_bus or get_event_bus()
        self.logger = logger or logging.getLogger(__name__)
        self._registered_entity_types: Dict[Type[Entity], Repository] = {}
    
    def register_entity_type(self, entity_type: Type[Entity], repository: Repository) -> None:
        """Register an entity type with its repository."""
        self._registered_entity_types[entity_type] = repository
    
    def create_domain_service(self, service_class: Type[DomainService], **kwargs: Any) -> DomainService:
        """Create a domain service instance."""
        # Create a unit of work
        uow = self.unit_of_work_factory.create_uow()
        
        # Create the service with dependencies
        service = service_class(uow=uow, event_bus=self.event_bus, **kwargs)
        
        return service
    
    def create_entity_service(self, entity_type: Type[E], **kwargs: Any) -> EntityService[E]:
        """Create an entity service for a specific entity type."""
        # Get the repository for this entity type
        if entity_type not in self._registered_entity_types:
            raise ValueError(f"No repository registered for entity type {entity_type.__name__}")
        
        repository = self._registered_entity_types[entity_type]
        
        # Create the service
        service = EntityService(
            entity_type=entity_type,
            repository=repository,
            event_bus=self.event_bus,
            **kwargs
        )
        
        return service
```

### Example Usage

#### Creating a Domain Service

```python
from uno.core.errors.result import Result, Success, Failure
from uno.domain.unified_services import DomainService
from uno.domain.repository import Repository
from uno.domain.unit_of_work import UnitOfWork

# Input/Output models
class CreateOrderInput(BaseModel):
    customer_id: str
    items: List[Dict[str, Any]]
    shipping_address: Dict[str, Any]

class OrderOutput(BaseModel):
    id: str
    status: str
    total: float
    created_at: datetime

# Domain service
class CreateOrderService(DomainService[CreateOrderInput, OrderOutput, UnitOfWork]):
    def __init__(
        self, 
        uow: UnitOfWork,
        order_repository: Repository[Order],
        product_repository: Repository[Product]
    ):
        super().__init__(uow)
        self.order_repository = order_repository
        self.product_repository = product_repository
    
    async def _execute_internal(self, input_data: CreateOrderInput) -> Result[OrderOutput]:
        # Validate items and check inventory
        items = []
        total = 0.0
        
        for item_data in input_data.items:
            product_id = item_data["product_id"]
            quantity = item_data["quantity"]
            
            # Get product
            product = await self.product_repository.get(product_id)
            if not product:
                return Failure(f"Product with ID {product_id} not found")
            
            # Check inventory
            if product.stock < quantity:
                return Failure(f"Insufficient stock for product {product.name}")
            
            # Update inventory
            product.stock -= quantity
            await self.product_repository.update(product)
            
            # Add to items
            items.append(OrderItem(
                product_id=product_id,
                product_name=product.name,
                quantity=quantity,
                price=product.price.amount
            ))
            
            # Update total
            total += product.price.amount * quantity
        
        # Create order
        order = Order(
            id=uuid.uuid4(),
            customer_id=input_data.customer_id,
            items=items,
            shipping_address=Address(**input_data.shipping_address),
            status="created",
            total=total
        )
        
        # Add to repository
        saved_order = await self.order_repository.add(order)
        
        # Return output
        return Success(OrderOutput(
            id=str(saved_order.id),
            status=saved_order.status,
            total=saved_order.total,
            created_at=saved_order.created_at
        ))
```

#### Using the Service Factory

```python
from uno.domain.unified_services import initialize_service_factory, get_service_factory

# Initialize service factory
initialize_service_factory(unit_of_work_factory)

# Register entity types
service_factory = get_service_factory()
service_factory.register_entity_type(Product, product_repository)
service_factory.register_entity_type(Order, order_repository)

# Create services
create_order_service = service_factory.create_domain_service(
    CreateOrderService,
    order_repository=order_repository,
    product_repository=product_repository
)

product_service = service_factory.create_entity_service(Product)
```

#### Using the Services

```python
# Execute a domain service
result = await create_order_service.execute(CreateOrderInput(
    customer_id="customer-123",
    items=[
        {"product_id": "product-456", "quantity": 2},
        {"product_id": "product-789", "quantity": 1}
    ],
    shipping_address={
        "street": "123 Main St",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "12345"
    }
))

# Check result
if result.is_success:
    print(f"Order created: {result.value.id}")
else:
    print(f"Failed to create order: {result.error}")

# Use entity service
product_result = await product_service.get_by_id("product-456")
if product_result.is_success and product_result.value:
    print(f"Product: {product_result.value.name}, Stock: {product_result.value.stock}")
```

### Documentation and Tests

Comprehensive documentation has been created:

1. `docs/domain/unified_services.md` - Detailed documentation of the domain service pattern
2. `tests/unit/domain/test_unified_services.py` - Test suite for the domain service implementation

### Files Created/Updated

1. `src/uno/domain/unified_services.py` - The unified domain service pattern implementation
2. `docs/domain/unified_services.md` - Documentation for the domain service pattern
3. `tests/unit/domain/test_unified_services.py` - Test suite for the unified domain services

## Code Duplications and Cleanup Needs

During the implementation of our unified domain-driven design components, I've identified several redundancies and code duplications that should be addressed:

### 1. Multiple Domain Event Implementations

There are multiple implementations of `DomainEvent` and `UnoDomainEvent` across the codebase:
- `src/uno/core/domain.py`
- `src/uno/core/protocols.py`
- `src/uno/core/unified_events.py` (canonical version)
- `src/uno/core/protocols/__init__.py`
- `src/uno/domain/core.py`
- `src/uno/domain/models.py`

**Resolution Strategy:**
- Keep the implementation in `src/uno/core/unified_events.py` as the canonical version
- Create aliases in other modules that import from the canonical implementation
- Add deprecation warnings to alternate implementations
- Update all imports to use the canonical version
- Eventually remove duplicate implementations when code is fully migrated

### 2. Overlapping Repository Implementations

There are several repository implementations that overlap in functionality:
- Legacy repositories in various modules
- Standardized repositories in `src/uno/domain/repository.py`
- SQL-specific repositories in different files

**Resolution Strategy:**
- Complete the migration to the standardized repository pattern
- Create adapters for legacy repositories to implement the new interface
- Add deprecation warnings to legacy implementations
- Document migration paths for legacy code

### 3. Inconsistent Service Interfaces

Before our unification work, services were implemented with inconsistent interfaces:
- Some used exceptions for error handling, others used the Result pattern
- Some had transaction management, others left it to the caller
- Naming conventions and method signatures varied

**Resolution Strategy:**
- Continue migration to the unified domain service pattern
- Create adapter facades over legacy services where needed
- Add deprecation warnings to legacy implementations
- Document clear migration paths

### 4. Deprecated Modules to Remove

Based on our analysis, the following modules should be deprecated and eventually removed:
- `src/uno/domain/service.py` - Replaced by unified domain services
- `src/uno/domain/events.py` - Replaced by unified event system
- `src/uno/domain/models/base.py` - Replaced by unified domain model
- Duplicate protocol definitions across different modules

## Domain Service API Integration

I've implemented a standardized approach for integrating domain services with API endpoints, creating a bridge between domain-driven design and the API layer. This completes the full stack from domain model to REST API endpoints.

### Key Improvements Made

1. **Domain Service Adapters**
   - Created adapters for domain services to work with API endpoints
   - Implemented model conversion between domain and API models
   - Added consistent error handling and HTTP status code mapping
   - Provided support for both entity services and domain services

2. **Endpoint Factory**
   - Implemented a factory for creating standardized FastAPI endpoints
   - Added support for the common HTTP methods (GET, POST, PUT, DELETE)
   - Enabled proper OpenAPI documentation generation
   - Created simplified CRUD endpoint creation for entity services

3. **Complete Integration**
   - Connected the domain model, services, repositories, and events with API endpoints
   - Ensured proper separation of concerns throughout the stack
   - Maintained consistent error handling and validation
   - Provided proper dependency injection support

### Core Components

#### 1. Domain Service Adapter

The `DomainServiceAdapter` bridges domain services with API endpoints:

```python
class DomainServiceAdapter(Generic[InputT, OutputT]):
    """
    Adapter to bridge domain services with API endpoints.
    
    This class wraps a domain service, providing methods with signatures
    compatible with the API endpoint system while using domain-driven practices underneath.
    """
    
    def __init__(
        self,
        service: DomainServiceProtocol,
        input_model: Optional[Type[InputT]] = None,
        output_model: Optional[Type[OutputT]] = None,
        error_handler: Optional[Callable[[Result], None]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the service adapter."""
        # Initialize adapter with dependencies
        
    async def execute(self, input_data: Union[Dict[str, Any], BaseModel]) -> Any:
        """
        Execute the domain service operation.
        
        Args:
            input_data: The input data for the operation
            
        Returns:
            The operation result
            
        Raises:
            HTTPException: If the operation fails
        """
        # Convert input to domain model
        # Execute domain service
        # Handle errors
        # Return result
```

#### 2. Entity Service Adapter

The `EntityServiceAdapter` provides CRUD operations for entity services:

```python
class EntityServiceAdapter(Generic[T]):
    """
    Adapter to bridge entity services with API endpoints.
    
    This class wraps an EntityService to provide CRUD operations for API endpoints.
    """
    
    def __init__(
        self,
        service: EntityService[T],
        entity_type: Type[T],
        input_model: Optional[Type[BaseModel]] = None,
        output_model: Optional[Type[BaseModel]] = None,
        error_handler: Optional[Callable[[Result], None]] = None,
        logger: Optional[logging.Logger] = None
    ):
        """Initialize the entity service adapter."""
        # Initialize adapter with dependencies
        
    async def get(self, id: str, **kwargs) -> Any:
        """Get an entity by ID."""
        # ...
    
    async def filter(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 50,
        **kwargs
    ) -> Union[List[T], Dict[str, Any]]:
        """Filter entities based on criteria."""
        # ...
    
    async def save(
        self, 
        data: Union[Dict[str, Any], BaseModel], 
        **kwargs
    ) -> T:
        """Create or update an entity."""
        # ...
    
    async def delete_(self, id: str, **kwargs) -> bool:
        """Delete an entity."""
        # ...
```

#### 3. Service Endpoint Factory

The `DomainServiceEndpointFactory` creates FastAPI endpoints from domain services:

```python
class DomainServiceEndpointFactory:
    """
    Factory for creating FastAPI endpoints from domain services.
    
    This class provides methods to create endpoints from different types of domain services,
    ensuring a consistent API interface for domain-driven design patterns.
    """
    
    def __init__(
        self,
        service_factory: Optional[DomainServiceFactory] = None,
        error_handler: Optional[Callable[[Result], None]] = None
    ):
        """Initialize the endpoint factory."""
        # Initialize factory with dependencies
        
    def create_entity_service_endpoints(
        self,
        app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        entity_type: Type[T] = None,
        path_prefix: Optional[str] = None,
        tags: Optional[List[str]] = None,
        # ... additional parameters
    ) -> Dict[str, UnoEndpoint]:
        """
        Create endpoints for an entity service.
        
        This method creates standardized CRUD endpoints for an entity type:
        - POST {prefix} - Create
        - GET {prefix}/{id} - View
        - GET {prefix} - List
        - PUT {prefix}/{id} - Update
        - DELETE {prefix}/{id} - Delete
        """
        # ...
    
    def create_domain_service_endpoint(
        self,
        app: Optional[FastAPI] = None,
        router: Optional[APIRouter] = None,
        service_class: Type[DomainService],
        path: str,
        method: str = "POST",
        # ... additional parameters
    ):
        """
        Create an endpoint for a domain service.
        
        This method creates a custom endpoint for a domain service operation.
        """
        # ...
```

### Example Usage

A complete example is available at `src/uno/api/service_endpoint_example.py`. Here's a brief usage example:

```python
# Set up domain endpoints
def setup_domain_endpoints(app: FastAPI) -> None:
    # Create router for domain endpoints
    router = APIRouter(prefix="/api/v1", tags=["Domain"])
    
    # Get endpoint factory
    endpoint_factory = get_domain_service_endpoint_factory()
    
    # Create a domain service endpoint
    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=CreateUserService,
        path="/users",
        method="POST",
        summary="Create User",
        description="Create a new user in the system",
        response_model=UserOutput,
        status_code=201
    )
    
    # Create CRUD endpoints for an entity
    endpoint_factory.create_entity_service_endpoints(
        router=router,
        entity_type=User,
        path_prefix="/users",
        tags=["Users"],
        input_model=UserOutput,
        output_model=UserOutput
    )
    
    # Register the router with the application
    app.include_router(router)
```

### Documentation

Comprehensive documentation has been created:

1. `docs/api/domain-service-integration.md` - Detailed documentation of the domain service integration with API endpoints
2. `tests/unit/api/test_service_endpoint_integration.py` - Test suite for the service endpoint integration

### Files Created/Updated

1. `src/uno/api/service_endpoint_adapter.py` - Adapters for domain services
2. `src/uno/api/service_endpoint_factory.py` - Factory for creating API endpoints
3. `src/uno/api/service_endpoint_example.py` - Complete example implementation
4. `docs/api/domain-service-integration.md` - Documentation for the domain service integration
5. `tests/unit/api/test_service_endpoint_integration.py` - Tests for the integration

## Code Cleanup and Redundancy Resolution

After identifying code redundancies and inconsistencies in our DDD implementation, I've taken steps to address them:

### 1. Domain Event Consolidation

I've consolidated the multiple `DomainEvent`/`UnoDomainEvent` implementations:
- Added imports from the canonical implementation in `uno.core.unified_events`
- Added deprecation warnings to redundant implementations
- Updated documentation to point to the canonical implementation
- Created adapters for backward compatibility

### 2. Repository Pattern Standardization

I've standardized the repository pattern implementation:
- Added deprecation warnings to legacy repository implementations
- Created adapter classes for integrating legacy repositories with the standardized pattern
- Created a registry system for module-specific repository implementations

### 3. Service Pattern Standardization

I've standardized the service pattern implementation:
- Added deprecation warnings to legacy service implementations
- Created adapter classes for integrating legacy services with the unified pattern
- Created a registry system for module-specific service implementations

### 4. Migration Guide

I've created a comprehensive migration guide:
- `docs/domain/migration_to_unified_ddd.md` - Guide for migrating to the unified DDD approach
- Includes examples and best practices for new code
- Provides adapter patterns for gradual migration

### 5. Deprecation Warnings

I've added deprecation warnings to all redundant implementations:
- `uno.core.domain.UnoDomainEvent`
- `uno.core.protocols.UnoDomainEvent`
- `uno.domain.core.UnoDomainEvent`
- `uno.domain.models.UnoDomainEvent`
- `uno.domain.service`
- `uno.domain.services`
- `uno.dependencies.repository.UnoRepository`
- `uno.infrastructure.database.repository`

## Next Steps

### 2. Create Example Applications

Build example applications that demonstrate how to use the unified domain-driven design components to build real-world applications, from domain model to API endpoints.

### 3. Documentation and Migration Guides

Create comprehensive documentation and migration guides to help developers transition to the new patterns, including:
- Examples of common patterns and uses
- Clear migration paths from legacy code
- Best practices for using the new components

### 4. Cross-Module Integration

Enhance integration with other modules in the framework:
- Attribute system integration
- Values system integration
- Query system integration
- Reporting system integration
- Workflow system integration

By implementing these changes, the uno framework will provide a solid foundation for building domain-driven applications, ensuring consistency and following modern Python best practices.