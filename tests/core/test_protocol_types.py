"""
Tests for static type checking of core protocols.
"""
import pytest
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

from uno.core.protocols import (
    RepositoryProtocol,
    ServiceProtocol,
    EventProtocol,
    EventBusProtocol,
    EntityProtocol
)
from uno.core.errors import Result


# Sample entity implementation
class User:
    def __init__(self, id=None):
        self._id = id or str(uuid4())
        self._created_at = datetime.now()
        self._updated_at = self._created_at
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def __eq__(self, other):
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self):
        return hash(self.id)


# Sample repository implementation
class UserRepository:
    def __init__(self):
        self._users = {}
    
    async def get_by_id(self, id: str) -> Optional[User]:
        return self._users.get(id)
    
    async def find_all(self) -> List[User]:
        return list(self._users.values())
    
    async def save(self, entity: User) -> User:
        self._users[entity.id] = entity
        return entity
    
    async def delete(self, entity: User) -> None:
        if entity.id in self._users:
            del self._users[entity.id]
    
    async def delete_by_id(self, id: str) -> None:
        if id in self._users:
            del self._users[id]


# Sample service implementation
class UserService:
    def __init__(self, repository):
        self._repository = repository
    
    async def get_by_id(self, id: str) -> Result[Optional[User], Any]:
        try:
            user = await self._repository.get_by_id(id)
            return Result.success(user)
        except Exception as e:
            return Result.failure(str(e))
    
    async def get_all(self) -> Result[List[User], Any]:
        try:
            users = await self._repository.find_all()
            return Result.success(users)
        except Exception as e:
            return Result.failure(str(e))
    
    async def create(self, data: Dict[str, Any]) -> Result[User, Any]:
        try:
            user = User()
            user = await self._repository.save(user)
            return Result.success(user)
        except Exception as e:
            return Result.failure(str(e))
    
    async def update(self, id: str, data: Dict[str, Any]) -> Result[User, Any]:
        try:
            user = await self._repository.get_by_id(id)
            if not user:
                return Result.failure("User not found")
            user = await self._repository.save(user)
            return Result.success(user)
        except Exception as e:
            return Result.failure(str(e))
    
    async def delete(self, id: str) -> Result[None, Any]:
        try:
            await self._repository.delete_by_id(id)
            return Result.success(None)
        except Exception as e:
            return Result.failure(str(e))


# Sample event implementation
class UserCreatedEvent:
    def __init__(self, user_id: str):
        self._event_id = str(uuid4())
        self._occurred_at = datetime.now()
        self._user_id = user_id
    
    @property
    def event_id(self) -> str:
        return self._event_id
    
    @property
    def event_type(self) -> str:
        return "user.created"
    
    @property
    def occurred_at(self) -> datetime:
        return self._occurred_at
    
    @property
    def data(self) -> Dict[str, Any]:
        return {"user_id": self._user_id}
    
    @property
    def aggregate_id(self) -> Optional[str]:
        return self._user_id


# Sample event bus implementation
class InMemoryEventBus:
    def __init__(self):
        self._subscribers = {}
        self._published_events = []
    
    async def publish(self, event: EventProtocol) -> None:
        self._published_events.append(event)
        event_type = event.event_type
        if event_type in self._subscribers:
            for handler in self._subscribers[event_type]:
                await handler(event)
    
    async def subscribe(self, event_type: str, handler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
    
    async def unsubscribe(self, event_type: str, handler) -> None:
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)


# Type checking tests
def test_entity_protocol_compliance():
    """Test that User class implements EntityProtocol."""
    user = User()
    assert isinstance(user, EntityProtocol)


def test_repository_protocol_compliance():
    """Test that UserRepository class implements RepositoryProtocol."""
    repo = UserRepository()
    # Type checking will fail if the class doesn't implement the protocol
    # but we need runtime assertion as well
    assert isinstance(repo, RepositoryProtocol)


def test_service_protocol_compliance():
    """Test that UserService class implements ServiceProtocol."""
    repo = UserRepository()
    service = UserService(repo)
    assert isinstance(service, ServiceProtocol)


def test_event_protocol_compliance():
    """Test that UserCreatedEvent class implements EventProtocol."""
    event = UserCreatedEvent("123")
    assert isinstance(event, EventProtocol)


def test_event_bus_protocol_compliance():
    """Test that InMemoryEventBus class implements EventBusProtocol."""
    event_bus = InMemoryEventBus()
    assert isinstance(event_bus, EventBusProtocol)


@pytest.mark.asyncio
async def test_repository_operations():
    """Test basic repository operations."""
    repo = UserRepository()
    user = User()
    
    # Save
    saved_user = await repo.save(user)
    assert saved_user.id == user.id
    
    # Get by ID
    retrieved_user = await repo.get_by_id(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    
    # Find all
    all_users = await repo.find_all()
    assert len(all_users) == 1
    assert all_users[0].id == user.id
    
    # Delete
    await repo.delete(user)
    assert await repo.get_by_id(user.id) is None


@pytest.mark.asyncio
async def test_service_operations():
    """Test basic service operations."""
    repo = UserRepository()
    service = UserService(repo)
    
    # Create
    create_result = await service.create({})
    assert create_result.is_success
    assert create_result.value is not None
    
    user_id = create_result.value.id
    
    # Get by ID
    get_result = await service.get_by_id(user_id)
    assert get_result.is_success
    assert get_result.value is not None
    assert get_result.value.id == user_id
    
    # Get all
    all_result = await service.get_all()
    assert all_result.is_success
    assert len(all_result.value) == 1
    assert all_result.value[0].id == user_id
    
    # Delete
    delete_result = await service.delete(user_id)
    assert delete_result.is_success
    
    # Verify deletion
    get_after_delete = await service.get_by_id(user_id)
    assert get_after_delete.is_success
    assert get_after_delete.value is None


@pytest.mark.asyncio
async def test_event_bus_operations():
    """Test basic event bus operations."""
    event_bus = InMemoryEventBus()
    received_events = []
    
    # Define handler
    async def handle_user_created(event):
        received_events.append(event)
    
    # Subscribe
    await event_bus.subscribe("user.created", handle_user_created)
    
    # Publish
    event = UserCreatedEvent("123")
    await event_bus.publish(event)
    
    # Verify handler was called
    assert len(received_events) == 1
    assert received_events[0].event_id == event.event_id
    
    # Unsubscribe
    await event_bus.unsubscribe("user.created", handle_user_created)
    
    # Publish again
    await event_bus.publish(UserCreatedEvent("456"))
    
    # Verify handler was not called again
    assert len(received_events) == 1