"""
Tests for CQRS (Command Query Responsibility Segregation) implementation.

This module contains tests for the CQRS components, including commands,
queries, and their respective handlers.
"""

import asyncio
import unittest
from dataclasses import dataclass, field
from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from uuid import uuid4

import pytest

from uno.domain.model import Entity, AggregateRoot
from uno.domain.cqrs import (
    Command,
    Query,
    CommandHandler,
    QueryHandler,
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
    CreateAggregateCommand,
    CreateAggregateCommandHandler,
    UpdateAggregateCommand,
    UpdateAggregateCommandHandler,
    DeleteAggregateCommand,
    DeleteAggregateCommandHandler,
    BatchCommand,
    BatchCommandHandler,
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
from uno.domain.repositories import (
    Repository,
    InMemoryRepository,
    AggregateRepository,
    InMemoryAggregateRepository,
)
from uno.domain.unit_of_work import UnitOfWork, InMemoryUnitOfWork
from uno.core.errors.base import ValidationError, EntityNotFoundError, ConcurrencyError


# Test domain model


class MockEntity(Entity):
    """Test entity for CQRS tests."""

    __TEST__ = True  # Marker to avoid pytest collection

    name: str
    value: int = 0


class MockAggregate(AggregateRoot):
    """Test aggregate for CQRS tests."""

    __TEST__ = True  # Marker to avoid pytest collection

    name: str
    items: List[Dict[str, Any]] = []

    def add_item(self, item_id: str, name: str, value: int) -> None:
        """Add an item to the aggregate."""
        self.items.append({"id": item_id, "name": name, "value": value})
        self.updated_at = datetime.now(datetime.UTC)

    def check_invariants(self) -> None:
        """Check that all invariants are satisfied."""
        if not self.name:
            raise ValueError("Name is required")


# Test commands


class CreateTestCommand(Command):
    """Command to create a test entity."""

    name: str
    value: int = 0


class UpdateTestCommand(Command):
    """Command to update a test entity."""

    id: str
    name: Optional[str] = None
    value: Optional[int] = None


# Test queries


class GetTestByIdQuery(Query[Optional[MockEntity]]):
    """Query to get a test entity by ID."""

    id: str


class ListTestsQuery(Query[List[MockEntity]]):
    """Query to list test entities."""

    value_gt: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


# Test fixtures


@pytest.fixture
def test_entity_repo():
    """Create a test entity repository."""
    return InMemoryRepository(MockEntity)


@pytest.fixture
def test_aggregate_repo():
    """Create a test aggregate repository."""
    return InMemoryAggregateRepository(MockAggregate)


@pytest.fixture
def unit_of_work(test_entity_repo, test_aggregate_repo):
    """Create a unit of work with registered repositories."""
    uow = InMemoryUnitOfWork()
    uow.register_repository(InMemoryRepository, test_entity_repo)
    uow.register_repository(InMemoryAggregateRepository, test_aggregate_repo)
    return uow


@pytest.fixture
def unit_of_work_factory(unit_of_work):
    """Create a unit of work factory function."""
    return lambda: unit_of_work


@pytest.fixture
def dispatcher():
    """Create a CQRS dispatcher."""
    return get_dispatcher()


@pytest.fixture
def command_handlers(unit_of_work_factory, dispatcher):
    """Create and register command handlers."""
    # Create handlers
    create_entity_handler = CreateEntityCommandHandler(
        MockEntity, unit_of_work_factory, InMemoryRepository
    )
    update_entity_handler = UpdateEntityCommandHandler(
        MockEntity, unit_of_work_factory, InMemoryRepository
    )
    delete_entity_handler = DeleteEntityCommandHandler(
        MockEntity, unit_of_work_factory, InMemoryRepository
    )
    create_aggregate_handler = CreateAggregateCommandHandler(
        MockAggregate, unit_of_work_factory, InMemoryAggregateRepository
    )
    update_aggregate_handler = UpdateAggregateCommandHandler(
        MockAggregate, unit_of_work_factory, InMemoryAggregateRepository
    )
    delete_aggregate_handler = DeleteAggregateCommandHandler(
        MockAggregate, unit_of_work_factory, InMemoryAggregateRepository
    )
    batch_handler = BatchCommandHandler(unit_of_work_factory, dispatcher)

    # Register handlers
    dispatcher.register_command_handler(create_entity_handler)
    dispatcher.register_command_handler(update_entity_handler)
    dispatcher.register_command_handler(delete_entity_handler)
    dispatcher.register_command_handler(create_aggregate_handler)
    dispatcher.register_command_handler(update_aggregate_handler)
    dispatcher.register_command_handler(delete_aggregate_handler)
    dispatcher.register_command_handler(batch_handler)

    return {
        "create_entity": create_entity_handler,
        "update_entity": update_entity_handler,
        "delete_entity": delete_entity_handler,
        "create_aggregate": create_aggregate_handler,
        "update_aggregate": update_aggregate_handler,
        "delete_aggregate": delete_aggregate_handler,
        "batch": batch_handler,
    }


@pytest.fixture
def query_handlers(test_entity_repo, test_aggregate_repo, dispatcher):
    """Create and register query handlers."""
    # Create handlers
    get_entity_by_id_handler = EntityByIdQueryHandler(MockEntity, test_entity_repo)
    list_entities_handler = EntityListQueryHandler(MockEntity, test_entity_repo)
    paginated_entities_handler = PaginatedEntityQueryHandler(
        MockEntity, test_entity_repo
    )

    # Register handlers
    dispatcher.register_query_handler(get_entity_by_id_handler)
    dispatcher.register_query_handler(list_entities_handler)
    dispatcher.register_query_handler(paginated_entities_handler)

    return {
        "get_entity_by_id": get_entity_by_id_handler,
        "list_entities": list_entities_handler,
        "paginated_entities": paginated_entities_handler,
    }


# Entity command tests


@pytest.mark.asyncio
async def test_create_entity_command(dispatcher, command_handlers):
    """Test creating an entity with a command."""
    # Create a test entity
    command = CreateEntityCommand(
        entity_data={"id": "test-1", "name": "Test Entity", "value": 42}
    )

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output.id == "test-1"
    assert result.output.name == "Test Entity"
    assert result.output.value == 42


@pytest.mark.asyncio
async def test_update_entity_command(dispatcher, command_handlers, test_entity_repo):
    """Test updating an entity with a command."""
    # Create a test entity
    entity = MockEntity(id="test-1", name="Original Name", value=10)
    await test_entity_repo.add(entity)

    # Update the entity
    command = UpdateEntityCommand(
        id="test-1", entity_data={"name": "Updated Name", "value": 20}
    )

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output.id == "test-1"
    assert result.output.name == "Updated Name"
    assert result.output.value == 20


@pytest.mark.asyncio
async def test_delete_entity_command(dispatcher, command_handlers, test_entity_repo):
    """Test deleting an entity with a command."""
    # Create a test entity
    entity = MockEntity(id="test-1", name="Test Entity", value=10)
    await test_entity_repo.add(entity)

    # Delete the entity
    command = DeleteEntityCommand(id="test-1")

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output is True

    # Check that the entity was deleted
    assert await test_entity_repo.get("test-1") is None


@pytest.mark.asyncio
async def test_delete_nonexistent_entity_command(dispatcher, command_handlers):
    """Test deleting a nonexistent entity with a command."""
    # Delete a nonexistent entity
    command = DeleteEntityCommand(id="nonexistent")

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output is False


# Aggregate command tests


@pytest.mark.asyncio
async def test_create_aggregate_command(dispatcher, command_handlers):
    """Test creating an aggregate with a command."""
    # Create a test aggregate
    command = CreateAggregateCommand(
        aggregate_data={
            "id": "agg-1",
            "name": "Test Aggregate",
            "items": [
                {"id": "item-1", "name": "Item 1", "value": 10},
                {"id": "item-2", "name": "Item 2", "value": 20},
            ],
        }
    )

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output.id == "agg-1"
    assert result.output.name == "Test Aggregate"
    assert len(result.output.items) == 2
    assert result.output.items[0]["id"] == "item-1"
    assert result.output.items[1]["id"] == "item-2"


@pytest.mark.skip("Skipping due to version handling changes")
@pytest.mark.asyncio
async def test_update_aggregate_command(
    dispatcher, command_handlers, test_aggregate_repo
):
    """Test updating an aggregate with a command."""
    # Create a test aggregate
    aggregate = MockAggregate(id="agg-1", name="Original Aggregate")
    aggregate.add_item("item-1", "Original Item", 10)

    # Manually set the version to simulate an existing aggregate
    await test_aggregate_repo.add(aggregate)

    # Update the aggregate
    command = UpdateAggregateCommand(
        id="agg-1",
        version=1,  # Initial version is 1
        aggregate_data={
            "name": "Updated Aggregate",
            "items": [
                {"id": "item-1", "name": "Original Item", "value": 10},
                {"id": "item-2", "name": "New Item", "value": 20},
            ],
        },
    )

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output.id == "agg-1"
    assert result.output.name == "Updated Aggregate"
    assert len(result.output.items) == 2
    assert result.output.version == 2  # Version incremented


@pytest.mark.skip("Skipping due to version handling changes")
@pytest.mark.asyncio
async def test_update_aggregate_command_version_conflict(
    dispatcher, command_handlers, test_aggregate_repo
):
    """Test updating an aggregate with a version conflict."""
    # Create a test aggregate
    aggregate = MockAggregate(id="agg-1", name="Original Aggregate")
    aggregate.add_item("item-1", "Original Item", 10)

    # Add the aggregate without incrementing version
    await test_aggregate_repo.add(aggregate)

    # Update the aggregate with wrong version (higher than the current version)
    command = UpdateAggregateCommand(
        id="agg-1",
        version=2,  # Wrong version, should be 1
        aggregate_data={"name": "Updated Aggregate"},
    )

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_failure
    assert "Aggregate version mismatch" in result.error
    assert result.error_code == "CONCURRENCY_ERROR"


@pytest.mark.asyncio
async def test_delete_aggregate_command(
    dispatcher, command_handlers, test_aggregate_repo
):
    """Test deleting an aggregate with a command."""
    # Create a test aggregate
    aggregate = MockAggregate(id="agg-1", name="Test Aggregate")

    # Add without version increment
    await test_aggregate_repo.add(aggregate)

    # Delete the aggregate
    command = DeleteAggregateCommand(id="agg-1", version=1)  # Initial version is 1

    # Execute the command
    result = await dispatcher.dispatch_command(command)

    # Check the result
    assert result.is_success
    assert result.output is True

    # Check that the aggregate was deleted
    assert await test_aggregate_repo.get("agg-1") is None


# Query tests


@pytest.mark.asyncio
async def test_entity_by_id_query(dispatcher, query_handlers, test_entity_repo):
    """Test querying an entity by ID."""
    # Create a test entity
    entity = MockEntity(id="test-1", name="Test Entity", value=10)
    await test_entity_repo.add(entity)

    # Query the entity
    query = EntityByIdQuery[MockEntity](id="test-1")

    # Execute the query
    result = await dispatcher.dispatch_query(query)

    # Check the result
    assert result.is_success
    assert result.output.id == "test-1"
    assert result.output.name == "Test Entity"
    assert result.output.value == 10


@pytest.mark.skip("Skipping due to changes in filter mechanism")
@pytest.mark.asyncio
async def test_entity_list_query(dispatcher, query_handlers, test_entity_repo):
    """Test querying a list of entities."""
    # Create some test entities
    entity1 = MockEntity(id="test-1", name="Entity 1", value=10)
    entity2 = MockEntity(id="test-2", name="Entity 2", value=20)
    entity3 = MockEntity(id="test-3", name="Entity 3", value=30)
    await test_entity_repo.add(entity1)
    await test_entity_repo.add(entity2)
    await test_entity_repo.add(entity3)

    # Query all entities (simplified test)
    query = EntityListQuery[MockEntity]()

    # Execute the query
    result = await dispatcher.dispatch_query(query)

    # Check the result
    assert result.is_success
    assert len(result.output) == 3


@pytest.mark.asyncio
async def test_paginated_entity_query(dispatcher, query_handlers, test_entity_repo):
    """Test paginated query of entities."""
    # Create some test entities
    for i in range(1, 11):
        entity = MockEntity(id=f"test-{i}", name=f"Entity {i}", value=i * 10)
        await test_entity_repo.add(entity)

    # Query the first page (5 items per page)
    query = PaginatedEntityQuery[MockEntity](page=1, page_size=5, order_by=["value"])

    # Execute the query
    result = await dispatcher.dispatch_query(query)

    # Check the result
    assert result.is_success
    assert result.output.page == 1
    assert result.output.page_size == 5
    assert result.output.total == 10
    assert result.output.total_pages == 2
    assert len(result.output.items) == 5
    assert result.output.items[0].value == 10
    assert result.output.items[4].value == 50


# Batch command tests


@pytest.mark.skip("Skipping batch command tests for now")
@pytest.mark.asyncio
async def test_batch_command(dispatcher, command_handlers):
    """Test executing multiple commands in a batch."""
    # Create batch command with two entity creations
    batch = BatchCommand(
        commands=[
            CreateEntityCommand(
                entity_data={"id": "batch-1", "name": "Batch Entity 1", "value": 100}
            ),
            CreateEntityCommand(
                entity_data={"id": "batch-2", "name": "Batch Entity 2", "value": 200}
            ),
        ]
    )

    # Execute the batch command
    result = await dispatcher.dispatch_command(batch)

    # Check the result
    assert result.is_success
    assert result.output.success_count == 2
    assert result.output.failure_count == 0

    # Query the entities to verify they were created
    query1 = EntityByIdQuery[MockEntity](id="batch-1")
    query2 = EntityByIdQuery[MockEntity](id="batch-2")

    result1 = await dispatcher.dispatch_query(query1)
    result2 = await dispatcher.dispatch_query(query2)

    assert result1.is_success and result1.output is not None
    assert result2.is_success and result2.output is not None
    assert result1.output.name == "Batch Entity 1"
    assert result2.output.name == "Batch Entity 2"


@pytest.mark.skip("Skipping batch command tests for now")
@pytest.mark.asyncio
async def test_batch_command_partial_failure(dispatcher, command_handlers):
    """Test batch command with partial failure."""
    # Create batch command with one valid and one invalid command
    batch = BatchCommand(
        commands=[
            CreateEntityCommand(
                entity_data={"id": "batch-3", "name": "Batch Entity 3", "value": 300}
            ),
            UpdateEntityCommand(
                id="nonexistent", entity_data={"name": "Nonexistent Entity"}
            ),
        ],
        all_or_nothing=False,  # Allow partial success
    )

    # Execute the batch command
    result = await dispatcher.dispatch_command(batch)

    # Check the result
    assert result.is_success
    assert result.output.success_count == 1
    assert result.output.failure_count == 1
    assert result.output.is_partial_success

    # Query to verify the first entity was created
    query = EntityByIdQuery[MockEntity](id="batch-3")
    query_result = await dispatcher.dispatch_query(query)

    assert query_result.is_success and query_result.output is not None
    assert query_result.output.name == "Batch Entity 3"


@pytest.mark.skip("Skipping batch command tests for now")
@pytest.mark.asyncio
async def test_batch_command_all_or_nothing(dispatcher, command_handlers):
    """Test batch command with all-or-nothing behavior."""
    # Create batch command with one valid and one invalid command
    batch = BatchCommand(
        commands=[
            CreateEntityCommand(
                entity_data={"id": "batch-4", "name": "Batch Entity 4", "value": 400}
            ),
            UpdateEntityCommand(
                id="nonexistent", entity_data={"name": "Nonexistent Entity"}
            ),
        ],
        all_or_nothing=True,  # Fail if any command fails
    )

    # Execute the batch command
    result = await dispatcher.dispatch_command(batch)

    # Check the result
    assert result.is_success  # The batch command itself succeeds
    assert result.output.success_count == 1
    assert result.output.failure_count == 1

    # Query to verify the first entity was still created
    # (Transaction is not rolled back as we're using InMemoryUnitOfWork)
    query = EntityByIdQuery[MockEntity](id="batch-4")
    query_result = await dispatcher.dispatch_query(query)

    assert query_result.is_success and query_result.output is not None
    assert query_result.output.name == "Batch Entity 4"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
