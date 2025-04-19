"""
Tests for unified domain services implementation.

This module tests the standardized domain service pattern implementation,
ensuring proper integration with the unified event system, domain model,
and repository pattern.
"""

import asyncio
import logging
import uuid
from datetime import datetime, UTC
from typing import Dict, Any, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel

from uno.core.errors.result import Result
from uno.core.events import (
    UnoEvent,
    EventBus,
    initialize_events,
    reset_events,
    collect_event,
    get_event_bus,
)
from uno.domain.core import Entity, AggregateRoot, DomainException
from uno.core.base.respository import (
    Repository,
    InMemoryRepository,
    InMemoryAggregateRepository,
)
from uno.domain.specifications import Specification, AttributeSpecification
from uno.domain.unit_of_work import UnitOfWork, InMemoryUnitOfWork
from uno.domain.unified_services import (
    DomainService,
    ReadOnlyDomainService,
    EntityService,
    AggregateService,
    DomainServiceFactory,
)


# Test Models
class TestEvent(UnoEvent):
    """Test event for testing event handling."""

    data: str


class TestEntity(Entity):
    """Test entity for testing entity services."""

    name: str
    description: Optional[str] = None


class TestAggregate(AggregateRoot):
    """Test aggregate for testing aggregate services."""

    name: str
    items: List[str] = []

    def add_item(self, item: str) -> None:
        """Add an item to the aggregate."""
        self.items.append(item)
        self.add_event(
            TestEvent(
                event_type="item_added",
                aggregate_id=str(self.id),
                aggregate_type=self.__class__.__name__,
                data=item,
            )
        )


# Test Input/Output Models
class CreateEntityInput(BaseModel):
    """Input model for creating entities."""

    name: str
    description: Optional[str] = None


class EntityOutput(BaseModel):
    """Output model for entity operations."""

    id: str
    name: str
    description: Optional[str] = None


# Test Repository
class TestEntityRepository(InMemoryRepository[TestEntity]):
    """Repository for test entities."""

    def __init__(self):
        super().__init__(TestEntity)


class TestAggregateRepository(InMemoryAggregateRepository[TestAggregate]):
    """Repository for test aggregates."""

    def __init__(self):
        super().__init__(TestAggregate)


# Test Unit of Work
class TestUnitOfWork(InMemoryUnitOfWork):
    """Unit of work for testing."""

    def __init__(self, repositories: Optional[List[Repository]] = None):
        super().__init__()
        self.repositories = repositories or []


# Test Domain Service
class CreateEntityService(DomainService[CreateEntityInput, EntityOutput, UnitOfWork]):
    """Service for creating entities."""

    def __init__(self, uow: UnitOfWork, entity_repository: TestEntityRepository):
        super().__init__(uow)
        self.entity_repository = entity_repository

    async def _execute_internal(
        self, input_data: CreateEntityInput
    ) -> Result[EntityOutput]:
        """Create a new entity."""
        # Create entity
        entity = TestEntity(
            id=uuid.uuid4(), name=input_data.name, description=input_data.description
        )

        # Add entity to repository
        saved_entity = await self.entity_repository.add(entity)

        # Create and collect event
        event = TestEvent(
            event_type="entity_created",
            aggregate_id=str(saved_entity.id),
            aggregate_type="TestEntity",
            data=saved_entity.name,
        )
        collect_event(event)

        # Return success
        return Result.success(
            EntityOutput(
                id=str(saved_entity.id),
                name=saved_entity.name,
                description=saved_entity.description,
            )
        )


# Test Read-Only Domain Service
class GetEntityService(ReadOnlyDomainService[str, EntityOutput, UnitOfWork]):
    """Service for retrieving entities."""

    def __init__(self, uow: UnitOfWork, entity_repository: TestEntityRepository):
        super().__init__(uow)
        self.entity_repository = entity_repository

    async def _execute_internal(self, input_data: str) -> Result[EntityOutput]:
        """Get an entity by ID."""
        # Get entity
        entity = await self.entity_repository.get(input_data)

        # Check if entity exists
        if entity is None:
            return Result.failure(f"Entity with ID {input_data} not found")

        # Return success
        return Result.success(
            EntityOutput(
                id=str(entity.id), name=entity.name, description=entity.description
            )
        )


@pytest.fixture(autouse=True)
def setup_events():
    """Set up and tear down events for each test."""
    initialize_events(in_memory_event_store=True)
    yield
    reset_events()


@pytest.fixture
def entity_repository():
    """Create a test entity repository."""
    return TestEntityRepository()


@pytest.fixture
def aggregate_repository():
    """Create a test aggregate repository."""
    return TestAggregateRepository()


@pytest.fixture
def unit_of_work_factory(entity_repository, aggregate_repository):
    """Create a factory for test unit of work."""

    def create_uow():
        uow = TestUnitOfWork([entity_repository, aggregate_repository])
        uow.register_repository(TestEntityRepository, entity_repository)
        uow.register_repository(TestAggregateRepository, aggregate_repository)
        return uow

    return MagicMock(create_uow=create_uow)


@pytest.fixture
def service_factory(unit_of_work_factory):
    """Create a test service factory."""
    factory = DomainServiceFactory(unit_of_work_factory)
    factory.register_entity_type(TestEntity, TestEntityRepository())
    factory.register_entity_type(TestAggregate, TestAggregateRepository())
    return factory


class TestDomainService:
    """Tests for the domain service base class."""

    async def test_domain_service_execution(self, entity_repository):
        """Test domain service execution with transaction."""
        # Arrange
        input_data = CreateEntityInput(name="Test Entity")
        uow = TestUnitOfWork([entity_repository])
        service = CreateEntityService(uow, entity_repository)

        # Act
        result = await service.execute(input_data)

        # Assert
        assert result.is_success
        assert result.value.name == "Test Entity"
        assert await entity_repository.count() == 1

        # Check that transaction was committed
        assert uow.committed

    async def test_domain_service_validation_failure(self, entity_repository):
        """Test domain service with validation failure."""
        # Arrange
        input_data = CreateEntityInput(name="Invalid")
        uow = TestUnitOfWork([entity_repository])
        service = CreateEntityService(uow, entity_repository)

        # Add validation that rejects "Invalid" names
        service.validate = lambda data: (
            Result.failure("Invalid name") if data.name == "Invalid" else None
        )

        # Act
        result = await service.execute(input_data)

        # Assert
        assert result.is_failure
        assert result.error == "Invalid name"
        assert await entity_repository.count() == 0

        # Check that transaction was not committed
        assert not uow.committed

    async def test_domain_service_error_handling(self, entity_repository):
        """Test domain service error handling."""
        # Arrange
        input_data = CreateEntityInput(name="Test Entity")
        uow = TestUnitOfWork([entity_repository])
        service = CreateEntityService(uow, entity_repository)

        # Mock repository to raise exception
        entity_repository.add = AsyncMock(side_effect=ValueError("Test error"))

        # Act
        result = await service.execute(input_data)

        # Assert
        assert result.is_failure
        assert "Test error" in result.error

        # Check that transaction was rolled back
        assert not uow.committed
        assert uow.rolled_back

    async def test_domain_service_event_collection(self, entity_repository):
        """Test domain service event collection and publishing."""
        # Arrange
        input_data = CreateEntityInput(name="Test Entity")
        event_bus = EventBus()
        event_handler = AsyncMock()
        event_bus.subscribe(TestEvent, event_handler)

        uow = TestUnitOfWork([entity_repository])
        uow.event_bus = event_bus
        service = CreateEntityService(uow, entity_repository)

        # Act
        result = await service.execute(input_data)

        # Assert
        assert result.is_success

        # Check that event was published
        await asyncio.sleep(0.1)  # Wait for async event publishing
        event_handler.assert_called_once()
        call_args = event_handler.call_args[0][0]
        assert isinstance(call_args, TestEvent)
        assert call_args.event_type == "entity_created"
        assert call_args.data == "Test Entity"


class TestReadOnlyDomainService:
    """Tests for the read-only domain service base class."""

    async def test_read_only_service_execution(self, entity_repository):
        """Test read-only domain service execution."""
        # Arrange
        entity_id = str(uuid.uuid4())
        entity = TestEntity(id=entity_id, name="Test Entity")
        await entity_repository.add(entity)

        uow = TestUnitOfWork([entity_repository])
        service = GetEntityService(uow, entity_repository)

        # Act
        result = await service.execute(entity_id)

        # Assert
        assert result.is_success
        assert result.value.name == "Test Entity"
        assert result.value.id == entity_id

    async def test_read_only_service_not_found(self, entity_repository):
        """Test read-only domain service with entity not found."""
        # Arrange
        entity_id = str(uuid.uuid4())
        uow = TestUnitOfWork([entity_repository])
        service = GetEntityService(uow, entity_repository)

        # Act
        result = await service.execute(entity_id)

        # Assert
        assert result.is_failure
        assert f"Entity with ID {entity_id} not found" in result.error


class TestEntityService:
    """Tests for the entity service class."""

    async def test_entity_service_get_by_id(self, entity_repository):
        """Test entity service get by ID."""
        # Arrange
        entity_id = str(uuid.uuid4())
        entity = TestEntity(id=entity_id, name="Test Entity")
        await entity_repository.add(entity)

        service = EntityService(entity_type=TestEntity, repository=entity_repository)

        # Act
        result = await service.get_by_id(entity_id)

        # Assert
        assert result.is_success
        assert result.value.id == entity_id
        assert result.value.name == "Test Entity"

    async def test_entity_service_find(self, entity_repository):
        """Test entity service find operation."""
        # Arrange
        entity1 = TestEntity(id=uuid.uuid4(), name="Entity 1")
        entity2 = TestEntity(id=uuid.uuid4(), name="Entity 2")
        await entity_repository.add(entity1)
        await entity_repository.add(entity2)

        service = EntityService(entity_type=TestEntity, repository=entity_repository)

        # Act
        result = await service.find({"name": "Entity 1"})

        # Assert
        assert result.is_success
        assert len(result.value) == 1
        assert result.value[0].name == "Entity 1"

    async def test_entity_service_create(self, entity_repository):
        """Test entity service create operation."""
        # Arrange
        service = EntityService(entity_type=TestEntity, repository=entity_repository)

        # Act
        result = await service.create(
            {"name": "New Entity", "description": "Created by service"}
        )

        # Assert
        assert result.is_success
        assert result.value.name == "New Entity"
        assert result.value.description == "Created by service"

        # Check entity was added to repository
        entities = await entity_repository.list({})
        assert len(entities) == 1
        assert entities[0].name == "New Entity"

    async def test_entity_service_update(self, entity_repository):
        """Test entity service update operation."""
        # Arrange
        entity_id = uuid.uuid4()
        entity = TestEntity(id=entity_id, name="Original Name")
        await entity_repository.add(entity)

        service = EntityService(entity_type=TestEntity, repository=entity_repository)

        # Act
        result = await service.update(
            entity_id, {"name": "Updated Name", "description": "Added description"}
        )

        # Assert
        assert result.is_success
        assert result.value.name == "Updated Name"
        assert result.value.description == "Added description"

        # Check entity was updated in repository
        updated_entity = await entity_repository.get(entity_id)
        assert updated_entity is not None
        assert updated_entity.name == "Updated Name"
        assert updated_entity.description == "Added description"

    async def test_entity_service_delete(self, entity_repository):
        """Test entity service delete operation."""
        # Arrange
        entity_id = uuid.uuid4()
        entity = TestEntity(id=entity_id, name="Entity to Delete")
        await entity_repository.add(entity)

        service = EntityService(entity_type=TestEntity, repository=entity_repository)

        # Act
        result = await service.delete(entity_id)

        # Assert
        assert result.is_success
        assert result.value is True

        # Check entity was removed from repository
        deleted_entity = await entity_repository.get(entity_id)
        assert deleted_entity is None


class TestAggregateService:
    """Tests for the aggregate service class."""

    async def test_aggregate_service_create(self, aggregate_repository):
        """Test aggregate service create operation."""
        # Arrange
        uow = TestUnitOfWork([aggregate_repository])
        service = AggregateService(
            aggregate_type=TestAggregate,
            repository=aggregate_repository,
            unit_of_work=uow,
        )

        # Act
        result = await service.create(
            {"name": "Test Aggregate", "items": ["Item 1", "Item 2"]}
        )

        # Assert
        assert result.is_success
        assert result.value.name == "Test Aggregate"
        assert result.value.items == ["Item 1", "Item 2"]
        assert result.value.version == 1

        # Check aggregate was added to repository
        aggregates = await aggregate_repository.list({})
        assert len(aggregates) == 1
        assert aggregates[0].name == "Test Aggregate"

        # Check transaction was committed
        assert uow.committed

    async def test_aggregate_service_update_with_concurrency(
        self, aggregate_repository
    ):
        """Test aggregate service update with concurrency control."""
        # Arrange
        aggregate_id = uuid.uuid4()
        aggregate = TestAggregate(id=aggregate_id, name="Original Name")
        await aggregate_repository.add(aggregate)

        uow = TestUnitOfWork([aggregate_repository])
        service = AggregateService(
            aggregate_type=TestAggregate,
            repository=aggregate_repository,
            unit_of_work=uow,
        )

        # Act - with correct version
        result = await service.update(aggregate_id, 1, {"name": "Updated Name"})

        # Assert
        assert result.is_success
        assert result.value.name == "Updated Name"
        assert result.value.version == 2

        # Check aggregate was updated in repository
        updated_aggregate = await aggregate_repository.get(aggregate_id)
        assert updated_aggregate is not None
        assert updated_aggregate.name == "Updated Name"
        assert updated_aggregate.version == 2

        # Act - with incorrect version
        result2 = await service.update(aggregate_id, 1, {"name": "This Should Fail"})

        # Assert
        assert result2.is_failure
        assert "Concurrency conflict" in result2.error

        # Check aggregate was not updated again
        aggregate_after_failed_update = await aggregate_repository.get(aggregate_id)
        assert aggregate_after_failed_update is not None
        assert aggregate_after_failed_update.name == "Updated Name"
        assert aggregate_after_failed_update.version == 2

    async def test_aggregate_service_events(self, aggregate_repository):
        """Test aggregate service event collection and publishing."""
        # Arrange
        event_bus = EventBus()
        event_handler = AsyncMock()
        event_bus.subscribe(TestEvent, event_handler)

        uow = TestUnitOfWork([aggregate_repository])
        uow.event_bus = event_bus

        service = AggregateService(
            aggregate_type=TestAggregate,
            repository=aggregate_repository,
            unit_of_work=uow,
        )

        # Create aggregate
        aggregate = TestAggregate(id=uuid.uuid4(), name="Event Test")
        aggregate.add_item("New Item")  # This adds an event

        # Act
        result = await service.update(aggregate.id, 1, {"name": "Updated Name"})

        # Assert
        assert result.is_success

        # Check that events were published
        await asyncio.sleep(0.1)  # Wait for async event publishing
        event_handler.assert_called_once()
        call_args = event_handler.call_args[0][0]
        assert isinstance(call_args, TestEvent)
        assert call_args.event_type == "item_added"
        assert call_args.data == "New Item"


class TestDomainServiceFactory:
    """Tests for the domain service factory."""

    async def test_create_domain_service(
        self, service_factory, unit_of_work_factory, entity_repository
    ):
        """Test creating a domain service."""
        # Arrange
        # Create a domain service class
        service = service_factory.create_domain_service(
            CreateEntityService, entity_repository=entity_repository
        )

        # Act
        result = await service.execute(CreateEntityInput(name="Factory Test"))

        # Assert
        assert result.is_success
        assert result.value.name == "Factory Test"

    async def test_create_read_only_service(
        self, service_factory, unit_of_work_factory, entity_repository
    ):
        """Test creating a read-only domain service."""
        # Arrange
        # Add an entity to the repository
        entity_id = str(uuid.uuid4())
        entity = TestEntity(id=entity_id, name="Read Test")
        await entity_repository.add(entity)

        # Create a read-only service
        service = service_factory.create_read_only_service(
            GetEntityService, entity_repository=entity_repository
        )

        # Act
        result = await service.execute(entity_id)

        # Assert
        assert result.is_success
        assert result.value.name == "Read Test"

    async def test_create_entity_service(self, service_factory):
        """Test creating an entity service from the factory."""
        # Arrange & Act
        service = service_factory.create_entity_service(TestEntity)

        # Assert
        assert isinstance(service, EntityService)
        assert service.entity_type == TestEntity

    async def test_create_aggregate_service(self, service_factory):
        """Test creating an aggregate service from the factory."""
        # Arrange & Act
        service = service_factory.create_aggregate_service(TestAggregate)

        # Assert
        assert isinstance(service, AggregateService)
        assert service.aggregate_type == TestAggregate
