"""
Tests for the Unit of Work pattern implementation.

This module contains tests for the Unit of Work pattern implementation,
including the abstract base class, concrete implementations, and context utilities.
"""

import asyncio
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Optional, Dict, List, Any

from uno.core.events import AsyncEventBus, Event
from uno.core.protocols import Repository, UnitOfWork
from uno.core.uow import (
    AbstractUnitOfWork,
    DatabaseUnitOfWork,
    InMemoryUnitOfWork,
    transaction,
    unit_of_work,
)


# Test event class
class TestEvent(Event):
    """Test event for Unit of Work tests."""
    entity_id: str
    action: str


# Test repository class
class TestRepository:
    """Test repository for Unit of Work tests."""
    
    def __init__(self):
        self.data = {}
        self.events = []
    
    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """Get an entity by ID."""
        return self.data.get(id)
    
    async def add(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Add an entity to the repository."""
        entity_id = entity.get('id')
        if not entity_id:
            raise ValueError("Entity must have an ID")
        
        self.data[entity_id] = entity
        self.events.append(TestEvent(entity_id=entity_id, action="added"))
        return entity
    
    async def update(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Update an entity in the repository."""
        entity_id = entity.get('id')
        if not entity_id or entity_id not in self.data:
            raise ValueError("Entity must have an ID and exist in the repository")
        
        self.data[entity_id] = entity
        self.events.append(TestEvent(entity_id=entity_id, action="updated"))
        return entity
    
    def collect_events(self) -> List[Event]:
        """Collect events from the repository."""
        events = list(self.events)
        self.events.clear()
        return events


# Mock connection class
class MockConnection:
    """Mock database connection for Unit of Work tests."""
    
    def __init__(self):
        self.transaction = AsyncMock()
        self.close = AsyncMock()
    
    async def transaction(self):
        """Create a new transaction."""
        return self.transaction


# Test InMemoryUnitOfWork
@pytest.mark.asyncio
async def test_in_memory_unit_of_work():
    """Test the InMemoryUnitOfWork implementation."""
    # Create event bus and repository
    event_bus = AsyncMock(spec=AsyncEventBus)
    repo = TestRepository()
    
    # Create unit of work
    uow = InMemoryUnitOfWork(event_bus=event_bus)
    uow.register_repository(TestRepository, repo)
    
    # Test context manager
    async with uow:
        # Get repository
        repo_from_uow = uow.get_repository(TestRepository)
        assert repo_from_uow is repo
        
        # Add entity
        entity = {'id': '1', 'name': 'Test Entity'}
        await repo_from_uow.add(entity)
        
        # Update entity
        entity['name'] = 'Updated Entity'
        await repo_from_uow.update(entity)
    
    # Check that events were published
    assert event_bus.publish.call_count == 2
    
    # Check that the entity was saved
    saved_entity = await repo.get_by_id('1')
    assert saved_entity == {'id': '1', 'name': 'Updated Entity'}


# Test DatabaseUnitOfWork
@pytest.mark.asyncio
async def test_database_unit_of_work():
    """Test the DatabaseUnitOfWork implementation."""
    # Create event bus and repository
    event_bus = AsyncMock(spec=AsyncEventBus)
    repo = TestRepository()
    
    # Create mock connection
    connection = MockConnection()
    connection_factory = AsyncMock(return_value=connection)
    
    # Create unit of work
    uow = DatabaseUnitOfWork(
        connection_factory=connection_factory,
        event_bus=event_bus
    )
    uow.register_repository(TestRepository, repo)
    
    # Test context manager with successful transaction
    async with uow:
        # Verify connection and transaction are created
        connection_factory.assert_called_once()
        connection.transaction.assert_called_once()
        
        # Get repository
        repo_from_uow = uow.get_repository(TestRepository)
        assert repo_from_uow is repo
        
        # Add entity
        entity = {'id': '1', 'name': 'Test Entity'}
        await repo_from_uow.add(entity)
    
    # Verify transaction was committed and events published
    connection.transaction.commit.assert_called_once()
    assert event_bus.publish.call_count == 1
    
    # Test context manager with failed transaction
    connection.transaction.reset_mock()
    connection_factory.reset_mock()
    event_bus.publish.reset_mock()
    
    try:
        async with uow:
            # Add entity
            await repo.add({'id': '2', 'name': 'Test Entity 2'})
            
            # Raise exception
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Verify transaction was rolled back and no events published
    connection.transaction.rollback.assert_called_once()
    event_bus.publish.assert_not_called()


# Test transaction context manager
@pytest.mark.asyncio
async def test_transaction_context_manager():
    """Test the transaction context manager."""
    # Create event bus and repository
    event_bus = AsyncMock(spec=AsyncEventBus)
    repo = TestRepository()
    
    # Create unit of work factory
    uow = InMemoryUnitOfWork(event_bus=event_bus)
    uow.register_repository(TestRepository, repo)
    uow_factory = AsyncMock(return_value=uow)
    
    # Test successful transaction
    async with transaction(uow_factory):
        # Get repository
        repo_from_uow = uow.get_repository(TestRepository)
        
        # Add entity
        entity = {'id': '1', 'name': 'Test Entity'}
        await repo_from_uow.add(entity)
    
    # Verify events were published
    assert event_bus.publish.call_count == 1
    
    # Test failed transaction
    event_bus.publish.reset_mock()
    
    try:
        async with transaction(uow_factory):
            # Add entity
            await repo.add({'id': '2', 'name': 'Test Entity 2'})
            
            # Raise exception
            raise ValueError("Test exception")
    except ValueError:
        pass
    
    # Verify no events were published
    event_bus.publish.assert_not_called()


# Test unit_of_work decorator
@pytest.mark.asyncio
async def test_unit_of_work_decorator():
    """Test the unit_of_work decorator."""
    # Create event bus and repository
    event_bus = AsyncMock(spec=AsyncEventBus)
    repo = TestRepository()
    
    # Create unit of work factory
    uow = InMemoryUnitOfWork(event_bus=event_bus)
    uow.register_repository(TestRepository, repo)
    uow_factory = AsyncMock(return_value=uow)
    
    # Define test service function
    @unit_of_work(uow_factory)
    async def create_entity(name: str, uow: UnitOfWork) -> Dict[str, Any]:
        repo = uow.get_repository(TestRepository)
        entity = {'id': '1', 'name': name}
        return await repo.add(entity)
    
    # Test service function
    result = await create_entity("Test Entity")
    
    # Verify result and events
    assert result == {'id': '1', 'name': 'Test Entity'}
    assert event_bus.publish.call_count == 1
    
    # Define test service function that doesn't need UoW
    @unit_of_work(uow_factory)
    async def get_entity(entity_id: str) -> Optional[Dict[str, Any]]:
        return await repo.get_by_id(entity_id)
    
    # Test service function
    result = await get_entity("1")
    
    # Verify result
    assert result == {'id': '1', 'name': 'Test Entity'}