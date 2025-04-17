"""
Testing infrastructure for CQRS and Read Model.

This module provides testing utilities for CQRS and Read Model components,
enabling comprehensive testing of commands, queries, projections, and more.
"""

import asyncio
import inspect
import logging
from datetime import datetime, UTC
from typing import (
    Any, Dict, Generic, List, Optional, Set, Tuple, Type, TypeVar, Union, Callable,
    cast, get_type_hints
)
from unittest.mock import MagicMock, AsyncMock, patch

from uno.core.cqrs import (
    Command, CommandHandler, Query, QueryHandler, CommandResult, QueryResult,
    MessageBus, CommandBus, QueryBus, Mediator
)
from uno.domain.events import DomainEvent, EventDispatcher
from uno.domain.event_store import EventStore, PostgresEventStore
from uno.read_model.read_model import ReadModel, ReadModelRepository
from uno.read_model.projector import Projection, Projector
from uno.core.uow import UnitOfWork, AbstractUnitOfWork
from uno.core.di import Container

# Type variables
T = TypeVar('T')
TCommand = TypeVar('TCommand', bound=Command)
TQuery = TypeVar('TQuery', bound=Query)
TReadModel = TypeVar('TReadModel', bound=ReadModel)
TEvent = TypeVar('TEvent', bound=DomainEvent)
TResult = TypeVar('TResult')


class CommandTestHarness(Generic[TCommand, TResult]):
    """
    Test harness for command handlers.
    
    This harness helps test command handlers by capturing events,
    tracking errors, and providing utilities for assertions.
    """
    
    def __init__(
        self,
        handler: CommandHandler[TCommand, TResult],
        unit_of_work: Optional[AbstractUnitOfWork] = None
    ):
        """
        Initialize the command test harness.
        
        Args:
            handler: The command handler to test
            unit_of_work: Optional unit of work for the handler
        """
        self.handler = handler
        self.unit_of_work = unit_of_work
        self.published_events: List[DomainEvent] = []
        self.errors: List[Exception] = []
        
        # Set up event capture
        if hasattr(handler, "add_event"):
            self._original_add_event = handler.add_event
            handler.add_event = self._capture_event
    
    async def execute(self, command: TCommand) -> TResult:
        """
        Execute a command and capture events and errors.
        
        Args:
            command: The command to execute
            
        Returns:
            The command result
        """
        try:
            # Execute command with or without unit of work
            if self.unit_of_work and hasattr(self.handler, "_handle"):
                return await self.handler._handle(command, self.unit_of_work)
            else:
                return await self.handler.handle(command)
        except Exception as e:
            self.errors.append(e)
            raise
    
    def _capture_event(self, event: DomainEvent) -> None:
        """
        Capture an event published by the handler.
        
        Args:
            event: The domain event
        """
        self.published_events.append(event)
        
        # Call original method if available
        if hasattr(self, "_original_add_event"):
            self._original_add_event(event)
    
    def assert_events_published(self, count: int) -> None:
        """
        Assert that a certain number of events were published.
        
        Args:
            count: The expected number of events
        """
        assert len(self.published_events) == count, \
            f"Expected {count} events, got {len(self.published_events)}"
    
    def assert_event_published(self, event_type: Type[DomainEvent]) -> None:
        """
        Assert that an event of a specific type was published.
        
        Args:
            event_type: The expected event type
        """
        for event in self.published_events:
            if isinstance(event, event_type):
                return
        
        assert False, f"Expected event of type {event_type.__name__}"
    
    def assert_no_errors(self) -> None:
        """Assert that no errors occurred during command execution."""
        assert len(self.errors) == 0, f"Expected no errors, got {len(self.errors)}"
    
    def get_events_of_type(self, event_type: Type[DomainEvent]) -> List[DomainEvent]:
        """
        Get all events of a specific type.
        
        Args:
            event_type: The event type to filter by
            
        Returns:
            List of matching events
        """
        return [event for event in self.published_events if isinstance(event, event_type)]


class QueryTestHarness(Generic[TQuery, TResult]):
    """
    Test harness for query handlers.
    
    This harness helps test query handlers by tracking results,
    errors, and providing utilities for assertions.
    """
    
    def __init__(self, handler: QueryHandler[TQuery, TResult]):
        """
        Initialize the query test harness.
        
        Args:
            handler: The query handler to test
        """
        self.handler = handler
        self.results: List[TResult] = []
        self.errors: List[Exception] = []
    
    async def execute(self, query: TQuery) -> TResult:
        """
        Execute a query and track results and errors.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        try:
            result = await self.handler.handle(query)
            self.results.append(result)
            return result
        except Exception as e:
            self.errors.append(e)
            raise
    
    def assert_results_count(self, count: int) -> None:
        """
        Assert that a certain number of queries were executed successfully.
        
        Args:
            count: The expected number of results
        """
        assert len(self.results) == count, \
            f"Expected {count} results, got {len(self.results)}"
    
    def assert_no_errors(self) -> None:
        """Assert that no errors occurred during query execution."""
        assert len(self.errors) == 0, f"Expected no errors, got {len(self.errors)}"
    
    def get_latest_result(self) -> Optional[TResult]:
        """
        Get the latest query result.
        
        Returns:
            The latest result or None if no queries were executed
        """
        if not self.results:
            return None
        return self.results[-1]


class EventStoreTestHarness:
    """
    Test harness for event store.
    
    This harness helps test event store implementations by tracking
    events, providing utilities for assertions, and mocking dependencies.
    """
    
    def __init__(
        self,
        event_store: EventStore,
        dispatcher: Optional[EventDispatcher] = None
    ):
        """
        Initialize the event store test harness.
        
        Args:
            event_store: The event store to test
            dispatcher: Optional event dispatcher
        """
        self.event_store = event_store
        self.dispatcher = dispatcher
        self.stored_events: List[DomainEvent] = []
        self.dispatched_events: List[DomainEvent] = []
        
        # Mock append to track events
        if hasattr(event_store, "append"):
            self._original_append = event_store.append
            event_store.append = self._track_append
        
        # Mock dispatcher if provided
        if dispatcher:
            self._original_dispatch = dispatcher.dispatch
            dispatcher.dispatch = self._track_dispatch
    
    async def _track_append(self, event: DomainEvent) -> None:
        """
        Track an event being appended to the store.
        
        Args:
            event: The domain event
        """
        self.stored_events.append(event)
        
        # Call original method
        if hasattr(self, "_original_append"):
            await self._original_append(event)
    
    async def _track_dispatch(self, event: DomainEvent) -> None:
        """
        Track an event being dispatched.
        
        Args:
            event: The domain event
        """
        self.dispatched_events.append(event)
        
        # Call original method
        if hasattr(self, "_original_dispatch"):
            await self._original_dispatch(event)
    
    def assert_events_stored(self, count: int) -> None:
        """
        Assert that a certain number of events were stored.
        
        Args:
            count: The expected number of events
        """
        assert len(self.stored_events) == count, \
            f"Expected {count} stored events, got {len(self.stored_events)}"
    
    def assert_events_dispatched(self, count: int) -> None:
        """
        Assert that a certain number of events were dispatched.
        
        Args:
            count: The expected number of events
        """
        assert len(self.dispatched_events) == count, \
            f"Expected {count} dispatched events, got {len(self.dispatched_events)}"
    
    def assert_event_stored(self, event_type: Type[DomainEvent]) -> None:
        """
        Assert that an event of a specific type was stored.
        
        Args:
            event_type: The expected event type
        """
        for event in self.stored_events:
            if isinstance(event, event_type):
                return
        
        assert False, f"Expected stored event of type {event_type.__name__}"
    
    def assert_event_dispatched(self, event_type: Type[DomainEvent]) -> None:
        """
        Assert that an event of a specific type was dispatched.
        
        Args:
            event_type: The expected event type
        """
        for event in self.dispatched_events:
            if isinstance(event, event_type):
                return
        
        assert False, f"Expected dispatched event of type {event_type.__name__}"


class EventSourcedAggregateTest(Generic[T]):
    """
    Test harness for event-sourced aggregates.
    
    This harness helps test event-sourced aggregates by tracking
    events, providing utilities for assertions, and simulating
    event application.
    """
    
    def __init__(self, aggregate_type: Type[T]):
        """
        Initialize the aggregate test harness.
        
        Args:
            aggregate_type: The aggregate type to test
        """
        self.aggregate_type = aggregate_type
        self.events: List[DomainEvent] = []
    
    def create_aggregate(self, **kwargs) -> T:
        """
        Create a new aggregate instance.
        
        Args:
            **kwargs: Arguments for aggregate constructor
            
        Returns:
            A new aggregate instance
        """
        return self.aggregate_type(**kwargs)
    
    def apply_events(self, aggregate: T, events: List[DomainEvent]) -> T:
        """
        Apply events to an aggregate.
        
        Args:
            aggregate: The aggregate to apply events to
            events: The events to apply
            
        Returns:
            The updated aggregate
        """
        # Track events
        self.events.extend(events)
        
        # Apply events
        if hasattr(aggregate, "apply"):
            for event in events:
                aggregate.apply(event)
        
        return aggregate
    
    def assert_events_count(self, count: int) -> None:
        """
        Assert that a certain number of events were applied.
        
        Args:
            count: The expected number of events
        """
        assert len(self.events) == count, \
            f"Expected {count} events, got {len(self.events)}"
    
    def assert_event_applied(self, event_type: Type[DomainEvent]) -> None:
        """
        Assert that an event of a specific type was applied.
        
        Args:
            event_type: The expected event type
        """
        for event in self.events:
            if isinstance(event, event_type):
                return
        
        assert False, f"Expected event of type {event_type.__name__}"


class ProjectionTest(Generic[TReadModel, TEvent]):
    """
    Test harness for projections.
    
    This harness helps test projections by tracking read models,
    providing utilities for assertions, and simulating event
    application.
    """
    
    def __init__(
        self,
        projection: Projection[TReadModel, TEvent],
        repository: Optional[ReadModelRepository[TReadModel]] = None
    ):
        """
        Initialize the projection test harness.
        
        Args:
            projection: The projection to test
            repository: Optional repository for storing read models
        """
        self.projection = projection
        self.repository = repository
        self.read_models: List[TReadModel] = []
        self.events: List[TEvent] = []
    
    async def apply_event(self, event: TEvent) -> Optional[TReadModel]:
        """
        Apply an event to the projection.
        
        Args:
            event: The event to apply
            
        Returns:
            The updated read model, if any
        """
        # Track event
        self.events.append(event)
        
        # Apply event
        read_model = await self.projection.apply(event)
        
        # Track read model
        if read_model:
            self.read_models.append(read_model)
            
            # Save to repository if available
            if self.repository:
                await self.repository.save(read_model)
        
        return read_model
    
    async def apply_events(self, events: List[TEvent]) -> List[TReadModel]:
        """
        Apply multiple events to the projection.
        
        Args:
            events: The events to apply
            
        Returns:
            The resulting read models
        """
        # Track events
        self.events.extend(events)
        
        # Apply events
        results = []
        for event in events:
            read_model = await self.projection.apply(event)
            if read_model:
                self.read_models.append(read_model)
                results.append(read_model)
                
                # Save to repository if available
                if self.repository:
                    await self.repository.save(read_model)
        
        return results
    
    def assert_read_models_count(self, count: int) -> None:
        """
        Assert that a certain number of read models were created.
        
        Args:
            count: The expected number of read models
        """
        assert len(self.read_models) == count, \
            f"Expected {count} read models, got {len(self.read_models)}"
    
    def assert_events_count(self, count: int) -> None:
        """
        Assert that a certain number of events were applied.
        
        Args:
            count: The expected number of events
        """
        assert len(self.events) == count, \
            f"Expected {count} events, got {len(self.events)}"
    
    def get_latest_read_model(self) -> Optional[TReadModel]:
        """
        Get the latest read model.
        
        Returns:
            The latest read model or None if no read models were created
        """
        if not self.read_models:
            return None
        return self.read_models[-1]


class MockEventStore(EventStore):
    """
    Mock implementation of event store for testing.
    
    This implementation stores events in memory and provides
    utilities for assertions and verification.
    """
    
    def __init__(self, dispatcher: Optional[EventDispatcher] = None):
        """
        Initialize the mock event store.
        
        Args:
            dispatcher: Optional event dispatcher
        """
        self.events: Dict[str, List[DomainEvent]] = {}
        self.all_events: List[DomainEvent] = []
        self.dispatcher = dispatcher
    
    async def append(self, event: DomainEvent) -> None:
        """
        Append an event to the store.
        
        Args:
            event: The domain event
        """
        # Extract aggregate ID
        aggregate_id = getattr(event, "aggregate_id", None)
        if not aggregate_id:
            raise ValueError("Event must have aggregate_id attribute")
        
        # Store event
        if aggregate_id not in self.events:
            self.events[aggregate_id] = []
        
        self.events[aggregate_id].append(event)
        self.all_events.append(event)
        
        # Dispatch event if dispatcher is available
        if self.dispatcher:
            await self.dispatcher.dispatch(event)
    
    async def get_events(
        self,
        aggregate_id: str,
        aggregate_type: Optional[str] = None,
        since_version: Optional[int] = None
    ) -> List[DomainEvent]:
        """
        Get events for an aggregate.
        
        Args:
            aggregate_id: ID of the aggregate
            aggregate_type: Optional type of the aggregate
            since_version: Optional version to start from
            
        Returns:
            List of domain events
        """
        # Get events for aggregate
        events = self.events.get(aggregate_id, [])
        
        # Filter by aggregate type if specified
        if aggregate_type:
            events = [e for e in events if getattr(e, "aggregate_type", None) == aggregate_type]
        
        # Filter by version if specified
        if since_version is not None:
            events = [e for e in events if getattr(e, "version", 0) > since_version]
        
        return events


class MockReadModelRepository(ReadModelRepository[TReadModel]):
    """
    Mock implementation of read model repository for testing.
    
    This implementation stores read models in memory and provides
    utilities for assertions and verification.
    """
    
    def __init__(self, model_type: Type[TReadModel]):
        """
        Initialize the mock repository.
        
        Args:
            model_type: The type of read model
        """
        super().__init__(model_type)
        self.models: Dict[str, TReadModel] = {}
    
    async def get(self, id: str) -> Optional[TReadModel]:
        """
        Get a read model by ID.
        
        Args:
            id: The read model ID
            
        Returns:
            The read model if found, None otherwise
        """
        return self.models.get(id)
    
    async def find(self, query: Dict[str, Any]) -> List[TReadModel]:
        """
        Find read models matching criteria.
        
        Args:
            query: The query criteria
            
        Returns:
            List of matching read models
        """
        results = []
        
        for model in self.models.values():
            # Simple property matching
            matches = True
            for key, value in query.items():
                if not hasattr(model, key) or getattr(model, key) != value:
                    matches = False
                    break
            
            if matches:
                results.append(model)
        
        return results
    
    async def save(self, model: TReadModel) -> TReadModel:
        """
        Save a read model.
        
        Args:
            model: The read model to save
            
        Returns:
            The saved read model
        """
        self.models[model.id] = model
        return model
    
    async def delete(self, id: str) -> bool:
        """
        Delete a read model.
        
        Args:
            id: The read model ID
            
        Returns:
            True if deleted, False otherwise
        """
        if id in self.models:
            del self.models[id]
            return True
        return False
    
    def assert_model_count(self, count: int) -> None:
        """
        Assert that the repository contains a certain number of models.
        
        Args:
            count: The expected number of models
        """
        assert len(self.models) == count, \
            f"Expected {count} models, got {len(self.models)}"
    
    def assert_model_exists(self, id: str) -> None:
        """
        Assert that a model with the given ID exists.
        
        Args:
            id: The model ID
        """
        assert id in self.models, f"Expected model with ID {id}"
    
    def assert_model_matches(self, id: str, **attrs) -> None:
        """
        Assert that a model with the given ID has specific attributes.
        
        Args:
            id: The model ID
            **attrs: Expected attribute values
        """
        assert id in self.models, f"Expected model with ID {id}"
        
        model = self.models[id]
        for key, value in attrs.items():
            assert hasattr(model, key), f"Model does not have attribute {key}"
            assert getattr(model, key) == value, \
                f"Expected {key}={value}, got {getattr(model, key)}"


class MockUnitOfWork(AbstractUnitOfWork):
    """
    Mock implementation of unit of work for testing.
    
    This implementation simulates a unit of work with transaction
    support, providing utilities for verification.
    """
    
    def __init__(self, repositories: Optional[Dict[str, Any]] = None):
        """
        Initialize the mock unit of work.
        
        Args:
            repositories: Optional dictionary of repositories
        """
        self.repositories = repositories or {}
        self.committed = False
        self.rolled_back = False
        self.active = False
    
    async def __aenter__(self) -> 'MockUnitOfWork':
        """Enter the context manager (start transaction)."""
        self.active = True
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the context manager (end transaction)."""
        if exc_type:
            await self.rollback()
        else:
            await self.commit()
        
        self.active = False
    
    async def commit(self) -> None:
        """Commit the transaction."""
        self.committed = True
    
    async def rollback(self) -> None:
        """Roll back the transaction."""
        self.rolled_back = True
    
    def assert_committed(self) -> None:
        """Assert that the transaction was committed."""
        assert self.committed, "Expected transaction to be committed"
    
    def assert_rolled_back(self) -> None:
        """Assert that the transaction was rolled back."""
        assert self.rolled_back, "Expected transaction to be rolled back"


class MockCQRSMediator(Mediator):
    """
    Mock implementation of CQRS mediator for testing.
    
    This implementation simulates a mediator with command and query
    handling, providing utilities for verification.
    """
    
    def __init__(self):
        """Initialize the mock mediator."""
        self.command_handlers: Dict[Type[Command], Callable] = {}
        self.query_handlers: Dict[Type[Query], Callable] = {}
        self.executed_commands: List[Command] = []
        self.executed_queries: List[Query] = []
    
    def register_command_handler(
        self,
        command_type: Type[Command],
        handler: Callable[[Command], Any]
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_type: The type of command
            handler: The handler function
        """
        self.command_handlers[command_type] = handler
    
    def register_query_handler(
        self,
        query_type: Type[Query],
        handler: Callable[[Query], Any]
    ) -> None:
        """
        Register a query handler.
        
        Args:
            query_type: The type of query
            handler: The handler function
        """
        self.query_handlers[query_type] = handler
    
    async def execute_command(self, command: Command) -> Any:
        """
        Execute a command.
        
        Args:
            command: The command to execute
            
        Returns:
            The command result
        """
        # Track command
        self.executed_commands.append(command)
        
        # Find handler
        handler = None
        for cmd_type, cmd_handler in self.command_handlers.items():
            if isinstance(command, cmd_type):
                handler = cmd_handler
                break
        
        if not handler:
            raise ValueError(f"No handler registered for command {command.__class__.__name__}")
        
        # Execute handler
        result = handler(command)
        if asyncio.iscoroutine(result):
            return await result
        return result
    
    async def execute_query(self, query: Query) -> Any:
        """
        Execute a query.
        
        Args:
            query: The query to execute
            
        Returns:
            The query result
        """
        # Track query
        self.executed_queries.append(query)
        
        # Find handler
        handler = None
        for qry_type, qry_handler in self.query_handlers.items():
            if isinstance(query, qry_type):
                handler = qry_handler
                break
        
        if not handler:
            raise ValueError(f"No handler registered for query {query.__class__.__name__}")
        
        # Execute handler
        result = handler(query)
        if asyncio.iscoroutine(result):
            return await result
        return result
    
    def assert_command_executed(self, command_type: Type[Command]) -> None:
        """
        Assert that a command of a specific type was executed.
        
        Args:
            command_type: The expected command type
        """
        for command in self.executed_commands:
            if isinstance(command, command_type):
                return
        
        assert False, f"Expected command of type {command_type.__name__}"
    
    def assert_query_executed(self, query_type: Type[Query]) -> None:
        """
        Assert that a query of a specific type was executed.
        
        Args:
            query_type: The expected query type
        """
        for query in self.executed_queries:
            if isinstance(query, query_type):
                return
        
        assert False, f"Expected query of type {query_type.__name__}"
    
    def get_commands_of_type(self, command_type: Type[Command]) -> List[Command]:
        """
        Get all executed commands of a specific type.
        
        Args:
            command_type: The command type to filter by
            
        Returns:
            List of matching commands
        """
        return [cmd for cmd in self.executed_commands if isinstance(cmd, command_type)]
    
    def get_queries_of_type(self, query_type: Type[Query]) -> List[Query]:
        """
        Get all executed queries of a specific type.
        
        Args:
            query_type: The query type to filter by
            
        Returns:
            List of matching queries
        """
        return [qry for qry in self.executed_queries if isinstance(qry, query_type)]


class CQRSTestContainer:
    """
    Test container for CQRS tests.
    
    This container provides mock implementations of CQRS components
    for testing, with utilities for setup and verification.
    """
    
    def __init__(self):
        """Initialize the test container."""
        self.event_dispatcher = EventDispatcher()
        self.event_store = MockEventStore(self.event_dispatcher)
        self.mediator = MockCQRSMediator()
        self.repositories: Dict[str, Any] = {}
        self.unit_of_work = MockUnitOfWork(self.repositories)
    
    def register_mock_repository(self, name: str, repository: Any) -> None:
        """
        Register a mock repository.
        
        Args:
            name: The repository name
            repository: The repository instance
        """
        self.repositories[name] = repository
        
        # Update unit of work repositories
        self.unit_of_work.repositories = self.repositories
    
    def get_read_model_repository(
        self,
        name: str,
        model_type: Type[TReadModel]
    ) -> MockReadModelRepository[TReadModel]:
        """
        Get or create a mock read model repository.
        
        Args:
            name: The repository name
            model_type: The read model type
            
        Returns:
            A mock read model repository
        """
        if name not in self.repositories:
            repository = MockReadModelRepository(model_type)
            self.register_mock_repository(name, repository)
        
        return self.repositories[name]
    
    def register_command_handler(
        self,
        command_type: Type[Command],
        handler: CommandHandler
    ) -> None:
        """
        Register a command handler.
        
        Args:
            command_type: The command type
            handler: The handler instance
        """
        self.mediator.register_command_handler(
            command_type,
            handler.handle
        )
    
    def register_query_handler(
        self,
        query_type: Type[Query],
        handler: QueryHandler
    ) -> None:
        """
        Register a query handler.
        
        Args:
            query_type: The query type
            handler: The handler instance
        """
        self.mediator.register_query_handler(
            query_type,
            handler.handle
        )
    
    def register_event_handler(
        self,
        event_type: Type[DomainEvent],
        handler: Callable[[DomainEvent], Any]
    ) -> None:
        """
        Register an event handler.
        
        Args:
            event_type: The event type
            handler: The handler function
        """
        self.event_dispatcher.subscribe(event_type.__name__, handler)
    
    def clear_all(self) -> None:
        """Clear all mock data and handlers."""
        # Clear event store
        self.event_store.events.clear()
        self.event_store.all_events.clear()
        
        # Clear mediator
        self.mediator.command_handlers.clear()
        self.mediator.query_handlers.clear()
        self.mediator.executed_commands.clear()
        self.mediator.executed_queries.clear()
        
        # Clear repositories
        for repository in self.repositories.values():
            if hasattr(repository, "models"):
                repository.models.clear()
        
        # Reset unit of work
        self.unit_of_work.committed = False
        self.unit_of_work.rolled_back = False
        self.unit_of_work.active = False
        
        # Clear event dispatcher
        self.event_dispatcher.handlers.clear()


# Helper functions

def create_test_container() -> CQRSTestContainer:
    """
    Create a test container for CQRS tests.
    
    Returns:
        A new test container
    """
    return CQRSTestContainer()


def configure_test_container(container: Container) -> CQRSTestContainer:
    """
    Configure a dependency injection container for testing.
    
    Args:
        container: The DI container to configure
        
    Returns:
        A test container for verification
    """
    # Create test container
    test_container = create_test_container()
    
    # Register mocks in DI container
    container.register(EventDispatcher, lambda: test_container.event_dispatcher)
    container.register(EventStore, lambda: test_container.event_store)
    container.register(Mediator, lambda: test_container.mediator)
    container.register(AbstractUnitOfWork, lambda: test_container.unit_of_work)
    
    # Return test container for verification
    return test_container


def restore_container(container: Container) -> None:
    """
    Restore a dependency injection container after testing.
    
    Args:
        container: The DI container to restore
    """
    # Clear all registrations
    container.clear()
    
    # Reinitialize container (container-specific code)
    pass