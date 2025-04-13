"""
Tests for the Application Service Layer.

This module contains tests for the Application Service Layer,
which coordinates the execution of commands and queries.
"""

import asyncio
import unittest
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import uuid4
from pydantic import Field

import pytest

from uno.domain.model import Entity, AggregateRoot
from uno.domain.cqrs import Command, Query, CommandResult, QueryResult, Dispatcher, get_dispatcher
from uno.domain.command_handlers import (
    CreateEntityCommand, CreateEntityCommandHandler,
    UpdateEntityCommand, UpdateEntityCommandHandler,
    DeleteEntityCommand, DeleteEntityCommandHandler
)
from uno.domain.query_handlers import (
    EntityByIdQuery, EntityByIdQueryHandler,
    EntityListQuery, EntityListQueryHandler,
    PaginatedEntityQuery, PaginatedEntityQueryHandler,
    PaginatedResult
)
from uno.domain.application_services import (
    ApplicationService, EntityService, AggregateService,
    ServiceContext, ServiceRegistry, get_service_registry
)
from uno.domain.repositories import Repository, InMemoryRepository
from uno.domain.unit_of_work import UnitOfWork, InMemoryUnitOfWork
from uno.domain.exceptions import ValidationError, AuthorizationError


# Test domain model

class TestEntity(Entity[str]):
    """Test entity for application service tests."""
    
    name: str
    value: int = 0


class TestAggregate(AggregateRoot[str]):
    """Test aggregate for application service tests."""
    
    name: str
    items: List[Dict[str, Any]] = Field(default_factory=list)
    
    def add_item(self, item_id: str, name: str, value: int) -> None:
        """Add an item to the aggregate."""
        self.items.append({
            "id": item_id,
            "name": name,
            "value": value
        })
        self.updated_at = datetime.utcnow()
    
    def check_invariants(self) -> None:
        """Check that all invariants are satisfied."""
        if not self.name:
            raise ValueError("Name is required")


# Custom command for testing

class AddAggregateItemCommand(Command):
    """Command to add an item to an aggregate."""
    
    aggregate_id: str
    item_id: str
    name: str
    value: int


class AddAggregateItemCommandHandler(UpdateEntityCommandHandler):
    """Handler for the AddAggregateItemCommand."""
    
    def __init__(
        self,
        unit_of_work_factory,
        repository_type
    ):
        super().__init__(
            AddAggregateItemCommand,
            unit_of_work_factory,
            logger=None
        )
        self.repository_type = repository_type
    
    async def _handle(self, command: AddAggregateItemCommand, uow: UnitOfWork) -> TestAggregate:
        """Handle the command."""
        # Get the repository
        repository = uow.get_repository(self.repository_type)
        
        # Get the aggregate
        aggregate = await repository.get_by_id(command.aggregate_id)
        
        # Add the item
        aggregate.add_item(command.item_id, command.name, command.value)
        
        # Update the aggregate in the repository
        return await repository.update(aggregate)


# Custom application service

class TestEntityService(EntityService[TestEntity]):
    """Custom service for test entities."""
    
    def validate_command(self, command: Command, context: ServiceContext) -> None:
        """Validate commands."""
        super().validate_command(command, context)
        
        if isinstance(command, CreateEntityCommand):
            data = command.entity_data
            
            # Validate name
            if 'name' not in data or not data['name']:
                raise ValidationError("Name is required")
            
            # Validate value
            if 'value' in data and data['value'] < 0:
                raise ValidationError("Value cannot be negative")


class TestAggregateService(AggregateService[TestAggregate]):
    """Custom service for test aggregates."""
    
    async def add_item(
        self, 
        aggregate_id: str, 
        item_id: str, 
        name: str, 
        value: int, 
        context: ServiceContext
    ) -> CommandResult:
        """Add an item to an aggregate."""
        command = AddAggregateItemCommand(
            aggregate_id=aggregate_id,
            item_id=item_id,
            name=name,
            value=value
        )
        return await self.execute_command(command, context)


# Test fixtures

@pytest.fixture
def test_entity_repo():
    """Create a test entity repository."""
    return InMemoryRepository(TestEntity)


@pytest.fixture
def test_aggregate_repo():
    """Create a test aggregate repository."""
    return InMemoryRepository(TestAggregate)


@pytest.fixture
def unit_of_work(test_entity_repo, test_aggregate_repo):
    """Create a unit of work with registered repositories."""
    uow = InMemoryUnitOfWork()
    uow.register_repository(InMemoryRepository, test_entity_repo)
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
        TestEntity, unit_of_work_factory, InMemoryRepository
    )
    update_entity_handler = UpdateEntityCommandHandler(
        TestEntity, unit_of_work_factory, InMemoryRepository
    )
    delete_entity_handler = DeleteEntityCommandHandler(
        TestEntity, unit_of_work_factory, InMemoryRepository
    )
    create_aggregate_handler = CreateEntityCommandHandler(
        TestAggregate, unit_of_work_factory, InMemoryRepository
    )
    update_aggregate_handler = UpdateEntityCommandHandler(
        TestAggregate, unit_of_work_factory, InMemoryRepository
    )
    delete_aggregate_handler = DeleteEntityCommandHandler(
        TestAggregate, unit_of_work_factory, InMemoryRepository
    )
    add_aggregate_item_handler = AddAggregateItemCommandHandler(
        unit_of_work_factory, InMemoryRepository
    )
    
    # Register handlers
    dispatcher.register_command_handler(create_entity_handler)
    dispatcher.register_command_handler(update_entity_handler)
    dispatcher.register_command_handler(delete_entity_handler)
    dispatcher.register_command_handler(create_aggregate_handler)
    dispatcher.register_command_handler(update_aggregate_handler)
    dispatcher.register_command_handler(delete_aggregate_handler)
    dispatcher.register_command_handler(add_aggregate_item_handler)
    
    return {
        "create_entity": create_entity_handler,
        "update_entity": update_entity_handler,
        "delete_entity": delete_entity_handler,
        "create_aggregate": create_aggregate_handler,
        "update_aggregate": update_aggregate_handler,
        "delete_aggregate": delete_aggregate_handler,
        "add_aggregate_item": add_aggregate_item_handler
    }


@pytest.fixture
def query_handlers(test_entity_repo, test_aggregate_repo, dispatcher):
    """Create and register query handlers."""
    # Create handlers
    get_entity_by_id_handler = EntityByIdQueryHandler(
        TestEntity, test_entity_repo
    )
    list_entities_handler = EntityListQueryHandler(
        TestEntity, test_entity_repo
    )
    get_aggregate_by_id_handler = EntityByIdQueryHandler(
        TestAggregate, test_aggregate_repo
    )
    
    # Register handlers
    dispatcher.register_query_handler(get_entity_by_id_handler)
    dispatcher.register_query_handler(list_entities_handler)
    dispatcher.register_query_handler(get_aggregate_by_id_handler)
    
    return {
        "get_entity_by_id": get_entity_by_id_handler,
        "list_entities": list_entities_handler,
        "get_aggregate_by_id": get_aggregate_by_id_handler
    }


@pytest.fixture
def entity_service(dispatcher):
    """Create a test entity service."""
    return TestEntityService(
        entity_type=TestEntity,
        dispatcher=dispatcher,
        read_permission="entities:read",
        write_permission="entities:write"
    )


@pytest.fixture
def aggregate_service(dispatcher):
    """Create a test aggregate service."""
    return TestAggregateService(
        aggregate_type=TestAggregate,
        dispatcher=dispatcher,
        read_permission="aggregates:read",
        write_permission="aggregates:write"
    )


@pytest.fixture
def authenticated_context():
    """Create an authenticated service context with all permissions."""
    return ServiceContext(
        user_id="test-user",
        is_authenticated=True,
        permissions=["entities:read", "entities:write", "aggregates:read", "aggregates:write"]
    )


@pytest.fixture
def read_only_context():
    """Create an authenticated service context with read-only permissions."""
    return ServiceContext(
        user_id="read-only-user",
        is_authenticated=True,
        permissions=["entities:read", "aggregates:read"]
    )


@pytest.fixture
def anonymous_context():
    """Create an anonymous service context."""
    return ServiceContext.create_anonymous()


# Service context tests

def test_service_context_permissions():
    """Test service context permission checks."""
    # Create service context with permissions
    context = ServiceContext(
        user_id="test-user",
        is_authenticated=True,
        permissions=["products:read", "orders:write"]
    )
    
    # Check permissions
    assert context.has_permission("products:read") is True
    assert context.has_permission("orders:write") is True
    assert context.has_permission("users:read") is False
    
    # Test require_authentication
    context.require_authentication()  # Should not raise
    
    # Test require_permission
    context.require_permission("products:read")  # Should not raise
    
    # Test require_permission with missing permission
    with pytest.raises(AuthorizationError):
        context.require_permission("users:read")
    
    # Test anonymous context
    anonymous = ServiceContext.create_anonymous()
    assert anonymous.is_authenticated is False
    with pytest.raises(AuthorizationError):
        anonymous.require_authentication()
    
    # Test system context
    system = ServiceContext.create_system()
    assert system.is_authenticated is True
    assert system.has_permission("any:permission") is True  # Wildcard permission


# Entity service tests

@pytest.mark.asyncio
async def test_entity_service_create(entity_service, authenticated_context):
    """Test creating an entity through the service."""
    # Create a test entity
    result = await entity_service.create(
        {
            "id": "test-1",
            "name": "Test Entity",
            "value": 42
        },
        authenticated_context
    )
    
    # Check the result
    assert result.is_success
    assert result.output.id == "test-1"
    assert result.output.name == "Test Entity"
    assert result.output.value == 42


@pytest.mark.asyncio
async def test_entity_service_validation(entity_service, authenticated_context):
    """Test entity service validation."""
    # Create entity with missing name
    result = await entity_service.create(
        {
            "id": "test-2",
            "value": 42
        },
        authenticated_context
    )
    
    # Check the result
    assert result.is_failure
    assert result.status.name == "REJECTED"
    assert "Name is required" in result.error
    
    # Create entity with negative value
    result = await entity_service.create(
        {
            "id": "test-3",
            "name": "Invalid Entity",
            "value": -10
        },
        authenticated_context
    )
    
    # Check the result
    assert result.is_failure
    assert result.status.name == "REJECTED"
    assert "Value cannot be negative" in result.error


@pytest.mark.asyncio
async def test_entity_service_authorization(entity_service, read_only_context, anonymous_context):
    """Test entity service authorization."""
    # Create entity with read-only permissions
    result = await entity_service.create(
        {
            "id": "test-4",
            "name": "Unauthorized Entity",
            "value": 42
        },
        read_only_context
    )
    
    # Check the result
    assert result.is_failure
    assert result.status.name == "REJECTED"
    assert "Permission required: entities:write" in result.error
    
    # Get entity with read-only permissions
    entity_data = {
        "id": "test-5",
        "name": "Readable Entity",
        "value": 42
    }
    create_result = await entity_service.create(entity_data, authenticated_context)
    assert create_result.is_success
    
    # Read should succeed with read-only permissions
    read_result = await entity_service.get_by_id("test-5", read_only_context)
    assert read_result.is_success
    assert read_result.output.name == "Readable Entity"
    
    # Attempt to read with anonymous context
    anon_result = await entity_service.get_by_id("test-5", anonymous_context)
    assert anon_result.is_failure
    assert "Authentication required" in anon_result.error


@pytest.mark.asyncio
async def test_entity_service_update_delete(entity_service, authenticated_context):
    """Test updating and deleting entities through the service."""
    # Create a test entity
    create_result = await entity_service.create(
        {
            "id": "test-6",
            "name": "Original Entity",
            "value": 10
        },
        authenticated_context
    )
    assert create_result.is_success
    
    # Update the entity
    update_result = await entity_service.update(
        "test-6",
        {
            "name": "Updated Entity",
            "value": 20
        },
        authenticated_context
    )
    
    # Check the update result
    assert update_result.is_success
    assert update_result.output.name == "Updated Entity"
    assert update_result.output.value == 20
    
    # Delete the entity
    delete_result = await entity_service.delete("test-6", authenticated_context)
    
    # Check the delete result
    assert delete_result.is_success
    assert delete_result.output is True
    
    # Verify entity is deleted
    get_result = await entity_service.get_by_id("test-6", authenticated_context)
    assert get_result.output is None


@pytest.mark.asyncio
async def test_entity_service_list(entity_service, authenticated_context):
    """Test listing entities through the service."""
    # Create test entities
    for i in range(5):
        await entity_service.create(
            {
                "id": f"list-{i}",
                "name": f"Entity {i}",
                "value": i * 10
            },
            authenticated_context
        )
    
    # List all entities
    list_result = await entity_service.list(
        filters=None,
        order_by=["value"],
        context=authenticated_context
    )
    
    # Check the result
    assert list_result.is_success
    assert len(list_result.output) == 5
    assert list_result.output[0].value == 0
    assert list_result.output[4].value == 40
    
    # List with filtering
    filtered_result = await entity_service.list(
        filters={"value__gt": 15},
        context=authenticated_context
    )
    
    # Check the filtered result
    assert filtered_result.is_success
    assert len(filtered_result.output) == 3  # Entities with value > 15
    
    # Test paginated list
    paginated_result = await entity_service.paginated_list(
        page=1,
        page_size=2,
        order_by=["value"],
        context=authenticated_context
    )
    
    # Check the paginated result
    assert paginated_result.is_success
    assert paginated_result.output.page == 1
    assert paginated_result.output.page_size == 2
    assert paginated_result.output.total == 5
    assert len(paginated_result.output.items) == 2
    assert paginated_result.output.items[0].value == 0
    assert paginated_result.output.items[1].value == 10


# Aggregate service tests

@pytest.mark.asyncio
async def test_aggregate_service_create(aggregate_service, authenticated_context):
    """Test creating an aggregate through the service."""
    # Create a test aggregate
    result = await aggregate_service.create(
        {
            "id": "agg-1",
            "name": "Test Aggregate",
            "items": []
        },
        authenticated_context
    )
    
    # Check the result
    assert result.is_success
    assert result.output.id == "agg-1"
    assert result.output.name == "Test Aggregate"
    assert len(result.output.items) == 0


@pytest.mark.asyncio
async def test_aggregate_service_custom_method(aggregate_service, authenticated_context):
    """Test custom aggregate service method."""
    # Create a test aggregate
    create_result = await aggregate_service.create(
        {
            "id": "agg-2",
            "name": "Test Aggregate",
            "items": []
        },
        authenticated_context
    )
    assert create_result.is_success
    
    # Add an item using the custom method
    add_item_result = await aggregate_service.add_item(
        "agg-2",
        "item-1",
        "Test Item",
        10,
        authenticated_context
    )
    
    # Check the result
    assert add_item_result.is_success
    assert len(add_item_result.output.items) == 1
    assert add_item_result.output.items[0]["id"] == "item-1"
    assert add_item_result.output.items[0]["name"] == "Test Item"
    assert add_item_result.output.items[0]["value"] == 10


# Service registry tests

def test_service_registry():
    """Test the service registry."""
    # Create registry
    registry = ServiceRegistry()
    
    # Register and get services
    test_service = EntityService(TestEntity)
    registry.register("TestService", test_service)
    
    # Get the service
    retrieved_service = registry.get("TestService")
    assert retrieved_service is test_service
    
    # Register entity service
    entity_service = registry.register_entity_service(
        entity_type=TestEntity,
        read_permission="entities:read",
        write_permission="entities:write"
    )
    
    # Get the service by default name
    retrieved_entity_service = registry.get("TestEntityService")
    assert retrieved_entity_service is entity_service
    
    # Register aggregate service
    aggregate_service = registry.register_aggregate_service(
        aggregate_type=TestAggregate,
        name="CustomAggregateService",
        read_permission="aggregates:read",
        write_permission="aggregates:write"
    )
    
    # Get the service by custom name
    retrieved_aggregate_service = registry.get("CustomAggregateService")
    assert retrieved_aggregate_service is aggregate_service
    
    # Test getting non-existent service
    with pytest.raises(KeyError):
        registry.get("NonExistentService")


if __name__ == "__main__":
    pytest.main(["-v", __file__])