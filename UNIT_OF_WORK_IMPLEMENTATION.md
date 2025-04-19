# Unit of Work Pattern Implementation

This document describes the implementation of the Unit of Work pattern in the UNO framework, which is the final component of Phase 1 in the comprehensive architecture plan.

## Overview

The Unit of Work pattern maintains a list of objects affected by a business transaction and coordinates the writing out of changes and the resolution of concurrency problems. It provides transaction boundaries, ensures consistency across multiple repositories, and handles domain event publishing.

## Implementation Components

The implementation consists of the following components:

1. **AbstractUnitOfWork** (`uno.core.uow.base.AbstractUnitOfWork`):
   - Base implementation of the UnitOfWork protocol
   - Provides repository registration and retrieval
   - Collects and publishes domain events
   - Manages transaction lifecycle with async context manager support

2. **Concrete Implementations**:
   - **DatabaseUnitOfWork**: Works with database connections and transactions
   - **InMemoryUnitOfWork**: In-memory implementation for testing
   - **SqlAlchemyUnitOfWork**: Works with SQLAlchemy sessions

3. **Context Utilities**:
   - **transaction**: Async context manager for transaction boundaries
   - **unit_of_work**: Decorator for service methods to provide unit of work

## Core Components

### UnitOfWork Protocol

The `UnitOfWork` protocol in `uno.core.protocols` defines the interface for all unit of work implementations:

```python
class UnitOfWork(Protocol):
    """
    Protocol for the Unit of Work pattern.

    The Unit of Work maintains a list of objects affected by a business transaction
    and coordinates the writing out of changes and the resolution of concurrency problems.
    """

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
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Exit the Unit of Work context."""
        ...
```

### AbstractUnitOfWork

The `AbstractUnitOfWork` class provides a base implementation with common functionality:

```python
class AbstractUnitOfWork(UnitOfWork, ABC):
    """
    Abstract base class for Unit of Work implementations.
    
    The Unit of Work pattern maintains a list of objects affected by a business
    transaction and coordinates writing out changes while ensuring consistency.
    """
    
    def __init__(
        self,
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the Unit of Work."""
        self._event_bus = event_bus
        self._logger = logger or logging.getLogger(__name__)
        self._repositories: Dict[Type[Repository], Repository] = {}
        self._events: List[Event] = []
    
    def register_repository(self, repo_type: Type[RepoT], repo: RepoT) -> None:
        """Register a repository with this Unit of Work."""
        self._repositories[repo_type] = repo
    
    def get_repository(self, repo_type: Type[RepoT]) -> RepoT:
        """Get a repository by its type."""
        if repo_type not in self._repositories:
            raise KeyError(f"Repository not found: {repo_type.__name__}")
        return cast(RepoT, self._repositories[repo_type])
    
    def add_event(self, event: Event) -> None:
        """Add a domain event to be published after commit."""
        self._events.append(event)
    
    async def publish_events(self) -> None:
        """Publish all collected domain events."""
        # Implementation details...
    
    @abstractmethod
    async def begin(self) -> None:
        """Begin a new transaction."""
        pass
    
    @abstractmethod
    async def commit(self) -> None:
        """Commit the current transaction."""
        pass
    
    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the current transaction."""
        pass
    
    async def __aenter__(self) -> "AbstractUnitOfWork":
        """Enter the Unit of Work context."""
        await self.begin()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the Unit of Work context."""
        try:
            if exc_type:
                await self.rollback()
            else:
                await self.commit()
                await self.publish_events()
        except Exception as e:
            await self.rollback()
            raise
```

## Concrete Implementations

### DatabaseUnitOfWork

This implementation works with database connections and transactions:

```python
class DatabaseUnitOfWork(AbstractUnitOfWork):
    """
    Database implementation of the Unit of Work pattern.
    
    This implementation works with database connections and transactions,
    providing transaction boundaries and ensuring consistency across
    multiple repositories.
    """
    
    def __init__(
        self,
        connection_factory: ConnectionFactory,
        event_bus: Optional[AsyncEventBus] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """Initialize the database Unit of Work."""
        super().__init__(event_bus, logger)
        self._connection_factory = connection_factory
        self._connection = None
        self._transaction = None
    
    # Implementation of begin, commit, rollback, close methods...
```

### InMemoryUnitOfWork

This implementation is primarily for testing:

```python
class InMemoryUnitOfWork(AbstractUnitOfWork):
    """
    In-memory implementation of the Unit of Work pattern.
    
    This implementation is primarily for testing and does not provide
    actual transaction boundaries since in-memory repositories typically
    don't support transactions.
    """
    
    # Implementation of begin, commit, rollback methods...
```

### SqlAlchemyUnitOfWork

This implementation works with SQLAlchemy sessions:

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    """
    SQLAlchemy implementation of the Unit of Work pattern.
    
    This implementation works with SQLAlchemy sessions, providing transaction
    boundaries and ensuring consistency across multiple repositories.
    """
    
    # Implementation of begin, commit, rollback, close methods...
```

## Context Utilities

### Transaction Context Manager

The `transaction` context manager provides a convenient way to work with transactions:

```python
@asynccontextmanager
async def transaction(
    uow_factory: UnitOfWorkFactory,
    logger: Optional[logging.Logger] = None,
) -> AsyncIterator[AbstractUnitOfWork]:
    """
    Context manager for a transaction using a Unit of Work.
    
    Example:
        async with transaction(get_uow) as uow:
            # Operations within the transaction
            repo = uow.get_repository(UserRepository)
            user = await repo.get_by_id(user_id)
            user.update_email(new_email)
            await repo.update(user)
            # Transaction is automatically committed if no exception occurs
    """
    # Implementation details...
```

### Unit of Work Decorator

The `unit_of_work` decorator makes it easy to use a Unit of Work in service methods:

```python
def unit_of_work(
    uow_factory: UnitOfWorkFactory,
    logger: Optional[logging.Logger] = None,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """
    Decorator that provides a Unit of Work for a function.
    
    Example:
        @unit_of_work(get_uow)
        async def update_user_email(user_id: str, email: str, uow: UnitOfWork) -> None:
            repo = uow.get_repository(UserRepository)
            user = await repo.get_by_id(user_id)
            if user:
                user.update_email(email)
                await repo.update(user)
    """
    # Implementation details...
```

## Integration with Domain Events

One of the key features of the Unit of Work pattern is its integration with domain events. The `AbstractUnitOfWork` class collects events from repositories and publishes them after a successful commit:

```python
async def publish_events(self) -> None:
    """
    Publish all collected domain events.
    
    This is called automatically after a successful commit.
    """
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

## Usage Examples

### Basic Usage

```python
# Create a unit of work factory
def get_uow() -> AbstractUnitOfWork:
    return DatabaseUnitOfWork(
        connection_factory=get_connection_factory(),
        event_bus=event_bus,
    )

# Use the unit of work context manager
async def update_user(user_id: str, new_email: str) -> None:
    async with transaction(get_uow) as uow:
        user_repo = uow.get_repository(UserRepository)
        user = await user_repo.get_by_id(user_id)
        if user:
            user.update_email(new_email)
            await user_repo.update(user)
```

### With Service Method Decorator

```python
@unit_of_work(get_uow)
async def create_user(username: str, email: str, uow: UnitOfWork) -> User:
    user_repo = uow.get_repository(UserRepository)
    user = User(username=username, email=email)
    return await user_repo.add(user)
```

## Legacy Cleanup

As part of the implementation, the following legacy Unit of Work implementations were identified and will be deprecated in favor of the new implementation:

1. **infrastructure/repositories/unit_of_work.py**:
   - Contains `UnitOfWork`, `InMemoryUnitOfWork`, and `SQLAlchemyUnitOfWork` classes
   - Uses different event publishing mechanism and repository registration approach

2. **core/uow.py**:
   - Contains an older version of the Unit of Work pattern

These implementations will be kept for backward compatibility during the transition but will be marked with deprecation warnings. The new implementation provides several advantages:

- Better integration with the event system
- Stronger typing with repository registration by type
- Improved transaction handling with proper async context manager
- Consistent event collection and publishing
- Comprehensive test coverage

## Conclusion

The implementation of the Unit of Work pattern completes Phase 1 of the comprehensive architecture plan. It provides a unified approach to transaction management and ensures consistency across repositories while integrating with the event system for domain event publishing.

Next steps include:
1. Starting Phase 2 with Entity base classes implementation
2. Integrating the Unit of Work pattern with the repository layer
3. Adding additional Unit of Work implementations as needed (e.g., distributed transactions)