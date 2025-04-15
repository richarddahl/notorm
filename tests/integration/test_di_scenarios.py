# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Integration tests for dependency injection scenarios.

These tests verify the behavior of the dependency injection system in various
real-world integration scenarios, focusing on the interplay between 
different components of the uno framework.
"""

import pytest
import asyncio
import logging
from typing import Dict, List, Any, Optional, Protocol, Type, AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from uno.dependencies.scoped_container import (
    ServiceCollection, ServiceResolver, ServiceScope,
    initialize_container, get_container, get_service,
    create_scope, create_async_scope
)
from uno.dependencies.interfaces import (
    UnoConfigProtocol, UnoRepositoryProtocol, 
    UnoDatabaseProviderProtocol, UnoDBManagerProtocol,
    UnoServiceProtocol, DomainRepositoryProtocol,
    DomainServiceProtocol, EventBusProtocol
)
from uno.dependencies.database import (
    get_db_session, get_raw_connection, get_repository,
    get_db_manager, get_sql_emitter_factory
)
from uno.core.errors import UnoError
from uno.core.errors.base import ValidationError


# Mock services for testing
class MockConfig:
    """Mock configuration service."""
    
    def __init__(self, config_data: Optional[Dict[str, Any]] = None):
        self.config_data = config_data or {
            "db_host": "localhost",
            "db_port": 5432,
            "db_name": "test_db",
            "app_name": "test_app",
            "log_level": "info"
        }
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key."""
        return self.config_data.get(key, default)
    
    def all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config_data.copy()


class MockDatabaseSession:
    """Mock database session for testing."""
    
    def __init__(self, session_id: str = None):
        self.session_id = session_id or str(uuid4())
        self.closed = False
        self.committed = False
        self.rolled_back = False
        self.queries = []
    
    async def commit(self) -> None:
        """Commit the session."""
        self.committed = True
    
    async def rollback(self) -> None:
        """Rollback the session."""
        self.rolled_back = True
    
    async def close(self) -> None:
        """Close the session."""
        self.closed = True
    
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Execute a query."""
        self.queries.append((query, params))
        
        # Return mock results based on the query
        if "SELECT" in query.upper():
            return [{"id": 1, "name": "test"}]
        return []


class MockDatabaseProvider:
    """Mock database provider for testing."""
    
    def __init__(self, config: UnoConfigProtocol):
        self.config = config
        self.sessions = []
        self.connections = []
        self.connection_params = {
            "host": config.get_value("db_host", "localhost"),
            "port": config.get_value("db_port", 5432),
            "database": config.get_value("db_name", "test_db")
        }
    
    @asynccontextmanager
    async def async_session(self) -> AsyncIterator[MockDatabaseSession]:
        """Get an async session context manager."""
        session = MockDatabaseSession()
        self.sessions.append(session)
        try:
            yield session
        finally:
            await session.close()
    
    @asynccontextmanager
    async def async_connection(self) -> AsyncIterator[Any]:
        """Get an async connection context manager."""
        connection = {"id": str(uuid4()), "params": self.connection_params}
        self.connections.append(connection)
        try:
            yield connection
        finally:
            # Closing connection
            connection["closed"] = True
    
    async def health_check(self) -> bool:
        """Check database health."""
        return True
    
    async def close(self) -> None:
        """Close all connections."""
        for session in self.sessions:
            if not session.closed:
                await session.close()
        
        for connection in self.connections:
            connection["closed"] = True


class MockEntity:
    """Mock entity for testing repositories."""
    
    def __init__(self, id: str, name: str, **kwargs):
        self.id = id
        self.name = name
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockRepository:
    """Mock repository for testing."""
    
    def __init__(self, db_provider: UnoDatabaseProviderProtocol):
        self.db_provider = db_provider
        self.entities = {}
    
    async def get(self, id: str) -> Optional[MockEntity]:
        """Get an entity by ID."""
        return self.entities.get(id)
    
    async def list(self, 
                 filters: Optional[Dict[str, Any]] = None, 
                 order_by: Optional[List[str]] = None,
                 limit: Optional[int] = None,
                 offset: Optional[int] = None) -> List[MockEntity]:
        """List entities with filtering, ordering, and pagination."""
        entities = list(self.entities.values())
        
        # Apply filters if provided
        if filters:
            filtered = []
            for entity in entities:
                match = True
                for key, value in filters.items():
                    if not hasattr(entity, key) or getattr(entity, key) != value:
                        match = False
                        break
                if match:
                    filtered.append(entity)
            entities = filtered
        
        # Apply ordering if provided
        if order_by:
            for field in reversed(order_by):
                descending = field.startswith("-")
                field_name = field[1:] if descending else field
                entities.sort(key=lambda e: getattr(e, field_name, None), reverse=descending)
        
        # Apply pagination if provided
        if offset is not None:
            entities = entities[offset:]
        if limit is not None:
            entities = entities[:limit]
        
        return entities
    
    async def create(self, data: Dict[str, Any]) -> MockEntity:
        """Create a new entity."""
        if "id" not in data:
            data["id"] = str(uuid4())
        
        entity = MockEntity(**data)
        self.entities[entity.id] = entity
        return entity
    
    async def update(self, id: str, data: Dict[str, Any]) -> Optional[MockEntity]:
        """Update an existing entity."""
        if id not in self.entities:
            return None
        
        entity = self.entities[id]
        for key, value in data.items():
            setattr(entity, key, value)
        
        return entity
    
    async def delete(self, id: str) -> bool:
        """Delete an entity by ID."""
        if id not in self.entities:
            return False
        
        del self.entities[id]
        return True
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count entities matching the given filters."""
        entities = await self.list(filters=filters)
        return len(entities)


class MockService:
    """Mock service for testing."""
    
    def __init__(self, repository: UnoRepositoryProtocol, config: UnoConfigProtocol):
        self.repository = repository
        self.config = config
    
    async def execute(self, action: str, data: Dict[str, Any]) -> Any:
        """Execute a service operation."""
        if action == "get":
            return await self.repository.get(data.get("id"))
        elif action == "create":
            return await self.repository.create(data)
        elif action == "update":
            return await self.repository.update(data.get("id"), data)
        elif action == "delete":
            return await self.repository.delete(data.get("id"))
        elif action == "list":
            return await self.repository.list(
                filters=data.get("filters"),
                order_by=data.get("order_by"),
                limit=data.get("limit"),
                offset=data.get("offset")
            )
        elif action == "count":
            return await self.repository.count(filters=data.get("filters"))
        elif action == "get_config":
            return self.config.get_value(data.get("key"))
        else:
            raise ValueError(f"Unknown action: {action}")


class MockEventBus:
    """Mock event bus for testing."""
    
    def __init__(self):
        self.subscribers = {}
        self.published_events = []
    
    async def publish(self, event: Any) -> None:
        """Publish an event to subscribers."""
        self.published_events.append(event)
        
        # Get event type
        event_type = type(event)
        
        # Notify subscribers
        handlers = []
        
        # Type-specific handlers
        if event_type in self.subscribers:
            handlers.extend(self.subscribers[event_type])
        
        # General handlers
        if "all" in self.subscribers:
            handlers.extend(self.subscribers["all"])
        
        # Call handlers
        for handler in handlers:
            await handler(event)
    
    async def publish_all(self, events: List[Any]) -> None:
        """Publish multiple events."""
        for event in events:
            await self.publish(event)
    
    def subscribe(self, event_type: Type[Any], handler: Any) -> None:
        """Subscribe to a specific event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        
        self.subscribers[event_type].append(handler)
    
    def subscribe_all(self, handler: Any) -> None:
        """Subscribe to all events."""
        if "all" not in self.subscribers:
            self.subscribers["all"] = []
        
        self.subscribers["all"].append(handler)
    
    def unsubscribe(self, event_type: Type[Any], handler: Any) -> None:
        """Unsubscribe from a specific event type."""
        if event_type in self.subscribers:
            if handler in self.subscribers[event_type]:
                self.subscribers[event_type].remove(handler)
    
    def unsubscribe_all(self, handler: Any) -> None:
        """Unsubscribe from all events."""
        if "all" in self.subscribers:
            if handler in self.subscribers["all"]:
                self.subscribers["all"].remove(handler)


# Mock domain models and events
class UserCreatedEvent:
    """Event fired when a user is created."""
    
    def __init__(self, user_id: str, username: str):
        self.user_id = user_id
        self.username = username
        self.timestamp = asyncio.get_event_loop().time()


class UserUpdatedEvent:
    """Event fired when a user is updated."""
    
    def __init__(self, user_id: str, changes: Dict[str, Any]):
        self.user_id = user_id
        self.changes = changes
        self.timestamp = asyncio.get_event_loop().time()


class User:
    """Mock user entity."""
    
    def __init__(self, id: str, username: str, email: str, **kwargs):
        self.id = id
        self.username = username
        self.email = email
        self.is_active = kwargs.get("is_active", True)
        self.created_at = kwargs.get("created_at", asyncio.get_event_loop().time())
        self.updated_at = kwargs.get("updated_at", self.created_at)
        self.metadata = kwargs.get("metadata", {})
    
    def update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user attributes."""
        changes = {}
        for key, value in data.items():
            if hasattr(self, key) and getattr(self, key) != value:
                changes[key] = value
                setattr(self, key, value)
        
        if changes:
            self.updated_at = asyncio.get_event_loop().time()
        
        return changes


class UserRepository:
    """Repository for users."""
    
    def __init__(self, db_provider: UnoDatabaseProviderProtocol, event_bus: EventBusProtocol):
        self.db_provider = db_provider
        self.event_bus = event_bus
        self.users = {}
    
    async def get(self, id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(id)
    
    async def list(self, 
                 filters: Optional[Dict[str, Any]] = None, 
                 order_by: Optional[List[str]] = None,
                 limit: Optional[int] = None,
                 offset: Optional[int] = None) -> List[User]:
        """List users with filtering, ordering, and pagination."""
        users = list(self.users.values())
        
        # Apply filters if provided
        if filters:
            filtered = []
            for user in users:
                match = True
                for key, value in filters.items():
                    if not hasattr(user, key) or getattr(user, key) != value:
                        match = False
                        break
                if match:
                    filtered.append(user)
            users = filtered
        
        # Apply ordering if provided
        if order_by:
            for field in reversed(order_by):
                descending = field.startswith("-")
                field_name = field[1:] if descending else field
                users.sort(key=lambda u: getattr(u, field_name, None), reverse=descending)
        
        # Apply pagination if provided
        if offset is not None:
            users = users[offset:]
        if limit is not None:
            users = users[:limit]
        
        return users
    
    async def add(self, user: User) -> User:
        """Add a new user."""
        self.users[user.id] = user
        
        # Publish event
        await self.event_bus.publish(UserCreatedEvent(user.id, user.username))
        
        return user
    
    async def update(self, user: User) -> User:
        """Update an existing user."""
        if user.id not in self.users:
            raise ValueError(f"User with ID {user.id} not found")
        
        self.users[user.id] = user
        return user
    
    async def remove(self, user: User) -> None:
        """Remove a user."""
        if user.id in self.users:
            del self.users[user.id]
    
    async def remove_by_id(self, id: str) -> bool:
        """Remove a user by ID."""
        if id not in self.users:
            return False
        
        del self.users[id]
        return True
    
    async def exists(self, id: str) -> bool:
        """Check if a user exists."""
        return id in self.users
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count users matching filters."""
        users = await self.list(filters=filters)
        return len(users)


class UserService:
    """Service for user operations."""
    
    def __init__(self, repository: UserRepository, event_bus: EventBusProtocol):
        self.repository = repository
        self.event_bus = event_bus
    
    async def get_by_id(self, id: str) -> Optional[User]:
        """Get a user by ID."""
        return await self.repository.get(id)
    
    async def list(self, 
                 filters: Optional[Dict[str, Any]] = None, 
                 order_by: Optional[List[str]] = None,
                 limit: Optional[int] = None,
                 offset: Optional[int] = None) -> List[User]:
        """List users with filtering, ordering, and pagination."""
        return await self.repository.list(
            filters=filters,
            order_by=order_by,
            limit=limit,
            offset=offset
        )
    
    async def create_user(self, data: Dict[str, Any]) -> User:
        """Create a new user."""
        # Validate required fields
        required_fields = ["username", "email"]
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Create user
        user = User(
            id=data.get("id", str(uuid4())),
            username=data["username"],
            email=data["email"],
            is_active=data.get("is_active", True),
            created_at=asyncio.get_event_loop().time(),
            updated_at=asyncio.get_event_loop().time(),
            metadata=data.get("metadata", {})
        )
        
        # Add to repository
        await self.repository.add(user)
        
        return user
    
    async def update_user(self, id: str, data: Dict[str, Any]) -> Optional[User]:
        """Update an existing user."""
        # Get user
        user = await self.repository.get(id)
        if not user:
            return None
        
        # Update user
        changes = user.update(data)
        
        # Save changes
        await self.repository.update(user)
        
        # Publish event if there were changes
        if changes:
            await self.event_bus.publish(UserUpdatedEvent(user.id, changes))
        
        return user
    
    async def delete_user(self, id: str) -> bool:
        """Delete a user."""
        # Check if user exists
        if not await self.repository.exists(id):
            return False
        
        # Remove user
        return await self.repository.remove_by_id(id)
    
    async def save(self, user: User) -> Optional[User]:
        """Save a user (create or update)."""
        if await self.repository.exists(user.id):
            await self.repository.update(user)
        else:
            await self.repository.add(user)
        
        return user
    
    async def delete(self, user: User) -> bool:
        """Delete a user."""
        await self.repository.remove(user)
        return True


# Test fixtures
@pytest.fixture
def event_handler():
    """Create an event handler for testing."""
    events = []
    
    async def handler(event):
        events.append(event)
    
    handler.events = events
    return handler


@pytest.fixture
def configured_container():
    """Create a configured container for integration testing."""
    # Create a service collection
    collection = ServiceCollection()
    
    # Register configuration
    collection.add_singleton(UnoConfigProtocol, MockConfig)
    
    # Register database services
    collection.add_scoped(UnoDatabaseProviderProtocol, MockDatabaseProvider)
    
    # Register repositories
    collection.add_scoped(UnoRepositoryProtocol, MockRepository)
    collection.add_scoped(UserRepository)
    
    # Register event bus
    collection.add_singleton(EventBusProtocol, MockEventBus)
    
    # Register services
    collection.add_scoped(UnoServiceProtocol, MockService)
    collection.add_scoped(UserService)
    
    # Register domain interfaces
    collection.add_scoped(DomainRepositoryProtocol, UserRepository)
    collection.add_scoped(DomainServiceProtocol, UserService)
    
    # Initialize global container
    initialize_container(collection, logging.getLogger("test"))
    
    # Return the collection for reference
    return collection


# Integration tests
@pytest.mark.integration
class TestDIIntegrationScenarios:
    """Integration tests for dependency injection scenarios."""
    
    @pytest.mark.asyncio
    async def test_repository_service_integration(self, configured_container, event_handler):
        """Test integration between repositories and services."""
        # Get the event bus and register our handler
        event_bus = get_service(EventBusProtocol)
        event_bus.subscribe(UserCreatedEvent, event_handler)
        event_bus.subscribe(UserUpdatedEvent, event_handler)
        
        # Create a scope for this test
        async with create_async_scope("test_scope") as scope:
            # Get the user service
            user_service = scope.resolve(UserService)
            
            # Create a new user
            user = await user_service.create_user({
                "username": "testuser",
                "email": "test@example.com"
            })
            
            # Verify user was created
            assert user.id is not None
            assert user.username == "testuser"
            assert user.email == "test@example.com"
            
            # Update the user
            updated_user = await user_service.update_user(user.id, {
                "username": "updated_user"
            })
            
            # Verify user was updated
            assert updated_user is not None
            assert updated_user.username == "updated_user"
            
            # Delete the user
            deleted = await user_service.delete_user(user.id)
            
            # Verify user was deleted
            assert deleted is True
        
        # Verify events were fired
        assert len(event_handler.events) == 2
        assert isinstance(event_handler.events[0], UserCreatedEvent)
        assert isinstance(event_handler.events[1], UserUpdatedEvent)
        assert event_handler.events[0].user_id == user.id
        assert event_handler.events[1].user_id == user.id
        assert event_handler.events[1].changes == {"username": "updated_user"}
    
    @pytest.mark.asyncio
    async def test_database_session_integration(self, configured_container):
        """Test integration with database sessions."""
        # Create a scope for this test
        async with create_async_scope("test_scope") as scope:
            # Get the repository
            repository = scope.resolve(UnoRepositoryProtocol)
            
            # Create some entities
            entity1 = await repository.create({"name": "Entity 1"})
            entity2 = await repository.create({"name": "Entity 2"})
            
            # Get the database provider directly
            db_provider = scope.resolve(UnoDatabaseProviderProtocol)
            
            # Verify provider has sessions
            assert len(db_provider.sessions) > 0
            
            # Use the database helper function
            async with get_db_session() as session:
                # Verify session is a mock session
                assert isinstance(session, MockDatabaseSession)
                
                # Execute a query
                await session.execute("SELECT * FROM entities")
                
                # Verify query was recorded
                assert len(session.queries) > 0
                assert session.queries[0][0] == "SELECT * FROM entities"
        
        # After scope exit, session should be closed
        for session in db_provider.sessions:
            assert session.closed
    
    @pytest.mark.asyncio
    async def test_repository_factory_integration(self, configured_container):
        """Test integration with repository factories."""
        # Create a scope for this test
        async with create_async_scope("test_scope") as scope:
            # Get the repository using the helper function
            repository = await get_repository(UnoRepositoryProtocol)
            
            # Create an entity
            entity = await repository.create({"name": "Test Entity"})
            
            # Verify entity was created
            assert entity.id is not None
            assert entity.name == "Test Entity"
    
    @pytest.mark.asyncio
    async def test_error_handling_integration(self, configured_container):
        """Test error handling across the integration points."""
        # Create a scope for this test
        async with create_async_scope("test_scope") as scope:
            # Get the user service
            user_service = scope.resolve(UserService)
            
            # Attempt to create a user with missing required fields
            with pytest.raises(ValidationError) as excinfo:
                await user_service.create_user({
                    "username": "testuser"
                    # Missing email
                })
            
            assert "Missing required field: email" in str(excinfo.value)
            
            # Attempt to update a non-existent user
            non_existent_id = str(uuid4())
            result = await user_service.update_user(non_existent_id, {
                "username": "updated_user"
            })
            
            # Should return None for non-existent user
            assert result is None
            
            # Create a user
            user = await user_service.create_user({
                "username": "testuser",
                "email": "test@example.com"
            })
            
            # Attempt to create a circular reference
            with pytest.raises(ValueError):
                await user_service.update_user(user.id, {
                    "circular_ref": user  # This should cause a circular reference error
                })
    
    @pytest.mark.asyncio
    async def test_lifecycle_integration(self, configured_container):
        """Test service lifecycle across integration points."""
        # Get the event bus
        event_bus = get_service(EventBusProtocol)
        
        # Track event counts
        initial_event_count = len(event_bus.published_events)
        
        # Create multiple scopes
        async with create_async_scope("scope1") as scope1:
            # Get services in scope 1
            user_service1 = scope1.resolve(UserService)
            repository1 = scope1.resolve(UserRepository)
            
            # Create a user in scope 1
            user1 = await user_service1.create_user({
                "username": "user1",
                "email": "user1@example.com"
            })
            
            # Create another scope
            async with create_async_scope("scope2") as scope2:
                # Get services in scope 2
                user_service2 = scope2.resolve(UserService)
                repository2 = scope2.resolve(UserRepository)
                
                # Services should be different instances (scoped)
                assert user_service1 is not user_service2
                assert repository1 is not repository2
                
                # But they should share data (same backing store)
                user1_in_scope2 = await user_service2.get_by_id(user1.id)
                assert user1_in_scope2 is not None
                assert user1_in_scope2.username == user1.username
                
                # Create a user in scope 2
                user2 = await user_service2.create_user({
                    "username": "user2",
                    "email": "user2@example.com"
                })
                
                # Verify event bus fired events (singleton across scopes)
                assert len(event_bus.published_events) == initial_event_count + 2
            
            # After scope 2 exits, we should still be able to access scope 1 services
            assert await user_service1.exists(user1.id)
            
            # And we should be able to see users created in scope 2
            user2_in_scope1 = await user_service1.get_by_id(user2.id)
            assert user2_in_scope1 is not None
            assert user2_in_scope1.username == "user2"
        
        # After all scopes exit, the global event bus should still have the events
        assert len(event_bus.published_events) == initial_event_count + 2
    
    def test_error_messages_for_dependency_resolution(self, configured_container):
        """Test error messages for dependency resolution failures."""
        async def async_test():
            # Reset the container
            import uno.dependencies.scoped_container as container_module
            container_module._container = None
            
            # Create a minimal container with no registrations
            services = ServiceCollection()
            initialize_container(services, logging.getLogger("test"))
            
            # Create a handler that will capture log messages
            log_messages = []
            
            class CaptureHandler(logging.Handler):
                def emit(self, record):
                    log_messages.append(record.getMessage())
            
            logger = logging.getLogger("test")
            logger.addHandler(CaptureHandler())
            logger.setLevel(logging.ERROR)
            
            # Try to get service that doesn't exist
            try:
                get_service(UnoConfigProtocol)
                assert False, "Should have raised KeyError"
            except KeyError as e:
                # Verify error message
                assert "No registration found for" in str(e)
                assert "UnoConfigProtocol" in str(e)
            
            # Verify error was logged
            assert any("No registration found for" in msg for msg in log_messages)
            
            # Try to create a service with missing dependencies
            services.add_singleton(UserService)  # Missing required dependencies
            
            try:
                get_service(UserService)
                assert False, "Should have raised Exception"
            except Exception as e:
                # Verify error mentions missing parameters or dependencies
                error_msg = str(e)
                assert "missing" in error_msg.lower() or "required" in error_msg.lower()
            
            # Verify error was logged
            assert len(log_messages) >= 2
        
        # Run the async test
        asyncio.run(async_test())