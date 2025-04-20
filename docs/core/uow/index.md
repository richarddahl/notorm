# Unit of Work

The Unit of Work pattern is a crucial component of the Uno framework, providing transaction management, domain event coordination, and consistency across repositories.

## Overview

The Unit of Work pattern maintains a list of objects affected by a business transaction and coordinates the writing out of changes and the resolution of concurrency problems. In the Uno framework, it serves as the central point for transaction management and domain event publication.

## Key Features

- **Transaction Boundaries**: Provides clear transaction boundaries with async context manager support
- **Repository Coordination**: Manages multiple repositories within a single transaction
- **Domain Event Collection**: Collects domain events from repositories and entities
- **Event Publishing**: Publishes domain events after a successful transaction
- **Optimistic Concurrency**: Supports optimistic concurrency control
- **Async/Await Support**: Fully async implementation with modern Python patterns
- **Distributed Transactions**: Support for coordinating distributed transactions

## Basic Usage

```python
from uno.core.uow import UnitOfWork, get_unit_of_work
from uno.domain.repositories import UserRepository

async def create_user(name: str, email: str):
    # Get a Unit of Work
    async with get_unit_of_work() as uow:
        # Get a repository
        user_repo = uow.get_repository(UserRepository)
        
        # Create and save a user
        user = User.create(name, email)
        await user_repo.add(user)
        
        # Transaction is automatically committed if no exception occurs
        # Domain events are automatically published after commit
```

## With Domain Service

```python
from uno.domain.entity import DomainServiceWithUnitOfWork
from uno.core.errors.result import Result, Success, Failure

class UserService(DomainServiceWithUnitOfWork[User, UUID]):
    async def register_user(self, name: str, email: str) -> Result[User, str]:
        async with self.unit_of_work:
            # This code runs in a transaction
            user_repo = self.unit_of_work.get_repository(UserRepository)
            
            # Check if email is already taken
            existing_user = await user_repo.find_by_email(email)
            if existing_user:
                return Failure(f"Email {email} is already registered")
            
            # Create user
            user = User.create(name, email)
            user = await user_repo.add(user)
            
            return Success(user)
```

## Core Components

### UnitOfWork Protocol

The `UnitOfWork` protocol in `uno.core.protocols` defines the interface for all unit of work implementations:

```python
class UnitOfWork(Protocol):
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        ...

    @abstractmethod
    async def __aenter__(self) -> Self:
        """Enter the Unit of Work context."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        """Exit the Unit of Work context."""
        ...

    def get_repository(self, repo_type: Type[R]) -> R:
        """Get a repository by type."""
        ...

    def register_repository(self, repo_type: Type[R], repo: R) -> None:
        """Register a repository with this unit of work."""
        ...

    def add_event(self, event: Event) -> None:
        """Add a domain event to be published."""
        ...
```

### AbstractUnitOfWork

The `AbstractUnitOfWork` class provides a base implementation with common functionality:

```python
class AbstractUnitOfWork(UnitOfWork, ABC):
    def __init__(
        self,
        event_bus: Optional[EventBus] = None,
        logger: Optional[Logger] = None,
    ):
        self._event_bus = event_bus
        self._logger = logger or getLogger(__name__)
        self._repositories: Dict[Type[Repository], Repository] = {}
        self._events: list[Event] = []
    
    def register_repository(self, repo_type: Type[R], repo: R) -> None:
        """Register a repository with this Unit of Work."""
        self._repositories[repo_type] = repo
    
    def get_repository(self, repo_type: Type[R]) -> R:
        """Get a repository by its type."""
        if repo_type not in self._repositories:
            raise KeyError(f"Repository not found: {repo_type.__name__}")
        return cast(R, self._repositories[repo_type])
    
    def add_event(self, event: Event) -> None:
        """Add a domain event to be published after commit."""
        self._events.append(event)
    
    async def publish_events(self) -> None:
        """Publish all collected domain events."""
        # Implementation details...
```

## Implementations

### DatabaseUnitOfWork

The `DatabaseUnitOfWork` works with database connections and transactions:

```python
class DatabaseUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        connection_factory: ConnectionFactory,
        event_bus: Optional[EventBus] = None,
        logger: Optional[Logger] = None,
    ):
        super().__init__(event_bus, logger)
        self._connection_factory = connection_factory
        self._connection = None
        self._transaction = None
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        self._connection = await self._connection_factory.get_connection()
        self._transaction = await self._connection.begin()
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._transaction:
            await self._transaction.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._transaction:
            await self._transaction.rollback()
```

### SqlAlchemyUnitOfWork

The `SqlAlchemyUnitOfWork` works with SQLAlchemy sessions:

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(
        self,
        session_factory: Callable[[], AsyncSession],
        event_bus: Optional[EventBus] = None,
        logger: Optional[Logger] = None,
    ):
        super().__init__(event_bus, logger)
        self._session_factory = session_factory
        self._session = None
    
    async def begin(self) -> None:
        """Begin a new transaction."""
        self._session = self._session_factory()
        await self._session.begin()
    
    async def commit(self) -> None:
        """Commit the current transaction."""
        if self._session:
            await self._session.commit()
    
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        if self._session:
            await self._session.rollback()
```

## Distributed Unit of Work

For coordinating transactions across multiple systems, the `DistributedUnitOfWork` implements a two-phase commit protocol:

```python
from uno.core.uow.distributed import DistributedUnitOfWork, UnitOfWorkParticipant

# Create participants
db_participant = DatabaseParticipant(get_connection())
event_store_participant = EventStoreParticipant(get_event_store())

# Create distributed UoW
uow = DistributedUnitOfWork(
    participants=[db_participant, event_store_participant],
    event_bus=get_event_bus()
)

# Use the distributed UoW
async with uow:
    # Operations across multiple systems
    user_repo = uow.get_repository(UserRepository)
    user = await user_repo.get_by_id(user_id)
    user.update_email(new_email)
    await user_repo.update(user)
    
    # All participants will be committed or rolled back together
```

## Context Utilities

### transaction Context Manager

The `transaction` context manager provides a convenient way to work with transactions:

```python
from uno.core.uow.context import transaction

async def update_user(user_id: str, new_email: str):
    async with transaction(get_uow_factory()) as uow:
        # Operations within the transaction
        user_repo = uow.get_repository(UserRepository)
        user = await user_repo.get_by_id(user_id)
        user.update_email(new_email)
        await user_repo.update(user)
```

### unit_of_work Decorator

The `unit_of_work` decorator makes it easy to use a Unit of Work in service methods:

```python
from uno.core.uow.context import unit_of_work

@unit_of_work(get_uow_factory())
async def update_user_email(user_id: str, email: str, uow: UnitOfWork) -> None:
    repo = uow.get_repository(UserRepository)
    user = await repo.get_by_id(user_id)
    if user:
        user.update_email(email)
        await repo.update(user)
```

## Integration with Domain Events

One of the key features of the Unit of Work pattern is its integration with domain events. The `AbstractUnitOfWork` class collects events from repositories and entities and publishes them after a successful commit:

```python
async def publish_events(self) -> None:
    """Publish all collected domain events."""
    if not self._event_bus:
        self._logger.warning("No event bus configured, events will not be published")
        self._events.clear()
        return
    
    # Get all events to publish
    events = self.collect_new_events()
    
    # Publish each event
    self._logger.debug(f"Publishing {len(events)} events")
    for event in events:
        await self._event_bus.publish(event)
    
    # Clear the events after publishing
    self._events.clear()
```

## Best Practices

1. **Use Context Managers**: Always use the async context manager to ensure proper transaction handling.
2. **Register Repositories**: Register repositories with the Unit of Work to ensure they're part of the transaction.
3. **Collect Domain Events**: Use the Unit of Work to collect and publish domain events.
4. **Error Handling**: Let the Unit of Work handle transaction errors; it will automatically rollback on exceptions.
5. **Keep Transactions Short**: Minimize the amount of work done within a transaction.
6. **Use Domain Services with UoW**: Prefer `DomainServiceWithUnitOfWork` for automatic UoW integration.
7. **Consider Distributed UoW**: For operations spanning multiple systems, use the Distributed Unit of Work.

## Further Reading

- [Unit of Work Implementation](../../UNIT_OF_WORK_IMPLEMENTATION.md): Detailed implementation notes
- [Transaction Management](../database/transaction_management.md): Database transaction management
- [Domain Events](../events/index.md): Working with domain events
- [Domain Service Pattern](../../domain/service_pattern.md): Using UoW with domain services