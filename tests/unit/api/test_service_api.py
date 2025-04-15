"""
Tests for the API integration layer.

This module contains tests for the API integration layer, which connects
application services to HTTP endpoints.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from unittest.mock import MagicMock, AsyncMock

import pytest
from fastapi import FastAPI, APIRouter, Request, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.domain.model import Entity, AggregateRoot
from uno.domain.cqrs import CommandResult, QueryResult, CommandStatus, QueryStatus
from uno.domain.application_services import (
    ApplicationService,
    EntityService,
    AggregateService,
    ServiceContext,
    ServiceRegistry,
)
from uno.api.service_api import (
    EntityApi,
    AggregateApi,
    ServiceApiRegistry,
    create_dto_for_entity,
    create_response_model_for_entity,
    ContextProvider,
    get_context,
)
from uno.core.errors.base import ValidationError, AuthorizationError


# Test domain model


@dataclass
class TestEntity(Entity):
    """Test entity for API tests."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    name: str
    value: int = 0
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "value": self.value,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


@dataclass
class TestAggregate(AggregateRoot):
    """Test aggregate for API tests."""

    name: str
    items: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    __test__ = False  # Prevent pytest from collecting this class as a test

    def to_dict(self) -> Dict[str, Any]:
        """Convert aggregate to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "items": self.items,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Test DTOs


class TestEntityCreateDto(BaseModel):
    """DTO for creating a test entity."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    name: str
    value: int = 0


class TestEntityUpdateDto(BaseModel):
    """DTO for updating a test entity."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    name: Optional[str] = None
    value: Optional[int] = None


class TestEntityResponseDto(BaseModel):
    """Response DTO for a test entity."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    id: str
    name: str
    value: int
    created_at: str
    updated_at: Optional[str] = None


class TestAggregateCreateDto(BaseModel):
    """DTO for creating a test aggregate."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    name: str
    items: List[Dict[str, Any]] = []


class TestAggregateUpdateDto(BaseModel):
    """DTO for updating a test aggregate."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    name: Optional[str] = None


class TestAggregateResponseDto(BaseModel):
    """Response DTO for a test aggregate."""

    __test__ = False  # Prevent pytest from collecting this class as a test

    id: str
    name: str
    items: List[Dict[str, Any]]
    version: int
    created_at: str
    updated_at: Optional[str] = None


# Mock services


class MockEntityService(EntityService[TestEntity]):
    """Mock entity service for testing."""

    def __init__(self):
        """Initialize the mock service."""
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.get_by_id = AsyncMock()
        self.list = AsyncMock()
        self.paginated_list = AsyncMock()


class MockAggregateService(AggregateService[TestAggregate]):
    """Mock aggregate service for testing."""

    def __init__(self):
        """Initialize the mock service."""
        self.create = AsyncMock()
        self.update = AsyncMock()
        self.delete = AsyncMock()
        self.get_by_id = AsyncMock()
        self.list = AsyncMock()
        self.paginated_list = AsyncMock()
        self.custom_action = AsyncMock()


# Mock context provider


class MockContextProvider(ContextProvider):
    """Mock context provider for testing."""

    def __init__(
        self, user_id=None, tenant_id=None, is_authenticated=True, permissions=None
    ):
        """Initialize the mock context provider."""
        self.user_id = user_id or "test-user"
        self.tenant_id = tenant_id
        self.is_authenticated = is_authenticated
        self.permissions = permissions or ["entities:read", "entities:write"]

    async def __call__(self, request: Request) -> ServiceContext:
        """Create a service context."""
        return ServiceContext(
            user_id=self.user_id,
            tenant_id=self.tenant_id,
            is_authenticated=self.is_authenticated,
            permissions=self.permissions,
        )


# Test fixtures


@pytest.fixture
def mock_entity_service():
    """Create a mock entity service."""
    return MockEntityService()


@pytest.fixture
def mock_aggregate_service():
    """Create a mock aggregate service."""
    return MockAggregateService()


@pytest.fixture
def mock_context_provider():
    """Create a mock context provider."""
    return MockContextProvider()


@pytest.fixture
def mock_service_registry(mock_entity_service, mock_aggregate_service):
    """Create a mock service registry."""
    registry = MagicMock(spec=ServiceRegistry)
    registry.get.side_effect = lambda name: {
        "TestEntityService": mock_entity_service,
        "TestAggregateService": mock_aggregate_service,
    }.get(name)
    return registry


@pytest.fixture
def app():
    """Create a FastAPI app for testing."""
    return FastAPI()


@pytest.fixture
def router():
    """Create an API router for testing."""
    return APIRouter()


@pytest.fixture
def api_registry(router, mock_service_registry):
    """Create an API registry for testing."""
    return ServiceApiRegistry(router, mock_service_registry)


@pytest.fixture
def entity_api(mock_entity_service, router):
    """Create an entity API for testing."""
    return EntityApi(
        entity_type=TestEntity,
        service=mock_entity_service,
        router=router,
        prefix="/entities",
        tags=["Entities"],
        create_dto=TestEntityCreateDto,
        update_dto=TestEntityUpdateDto,
        response_model=TestEntityResponseDto,
    )


@pytest.fixture
def aggregate_api(mock_aggregate_service, router):
    """Create an aggregate API for testing."""
    return AggregateApi(
        aggregate_type=TestAggregate,
        service=mock_aggregate_service,
        router=router,
        prefix="/aggregates",
        tags=["Aggregates"],
        create_dto=TestAggregateCreateDto,
        update_dto=TestAggregateUpdateDto,
        response_model=TestAggregateResponseDto,
    )


@pytest.fixture
def client(app, router, mock_context_provider):
    """Create a test client."""
    # Register the mock context provider
    # We need to patch the module to replace the default context provider
    import uno.api.service_api

    original_provider = uno.api.service_api.default_context_provider
    uno.api.service_api.default_context_provider = mock_context_provider

    # Include the router
    app.include_router(router)

    # Create the test client
    client = TestClient(app)

    # Yield the client
    yield client

    # Restore the original context provider
    uno.api.service_api.default_context_provider = original_provider


# Entity API tests


def test_entity_api_create(entity_api, mock_entity_service, client):
    """Test creating an entity through the API."""
    # Mock the service response
    entity = TestEntity(id="test-1", name="Test Entity", value=42)
    mock_entity_service.create.return_value = CommandResult.success(
        command_id="cmd-1", command_type="CreateEntityCommand", output=entity
    )

    # Make the request
    response = client.post("/entities", json={"name": "Test Entity", "value": 42})

    # Check the response
    assert response.status_code == 200
    assert response.json() == {
        "id": "test-1",
        "name": "Test Entity",
        "value": 42,
        "created_at": entity.created_at.isoformat(),
        "updated_at": None,
    }

    # Check that the service was called
    mock_entity_service.create.assert_called_once()
    args, kwargs = mock_entity_service.create.call_args
    assert args[0] == {"name": "Test Entity", "value": 42}
    assert isinstance(args[1], ServiceContext)


def test_entity_api_get_by_id(entity_api, mock_entity_service, client):
    """Test getting an entity by ID through the API."""
    # Mock the service response
    entity = TestEntity(id="test-1", name="Test Entity", value=42)
    mock_entity_service.get_by_id.return_value = QueryResult.success(
        query_id="query-1", query_type="EntityByIdQuery", output=entity
    )

    # Make the request
    response = client.get("/entities/test-1")

    # Check the response
    assert response.status_code == 200
    assert response.json() == {
        "id": "test-1",
        "name": "Test Entity",
        "value": 42,
        "created_at": entity.created_at.isoformat(),
        "updated_at": None,
    }

    # Check that the service was called
    mock_entity_service.get_by_id.assert_called_once()
    args, kwargs = mock_entity_service.get_by_id.call_args
    assert args[0] == "test-1"
    assert isinstance(args[1], ServiceContext)


def test_entity_api_get_by_id_not_found(entity_api, mock_entity_service, client):
    """Test getting a non-existent entity by ID."""
    # Mock the service response
    mock_entity_service.get_by_id.return_value = QueryResult.success(
        query_id="query-1", query_type="EntityByIdQuery", output=None
    )

    # Make the request
    response = client.get("/entities/nonexistent")

    # Check the response
    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "TestEntity not found",
        "details": {},
    }


def test_entity_api_update(entity_api, mock_entity_service, client):
    """Test updating an entity through the API."""
    # Mock the service response
    entity = TestEntity(id="test-1", name="Updated Entity", value=43)
    mock_entity_service.update.return_value = CommandResult.success(
        command_id="cmd-1", command_type="UpdateEntityCommand", output=entity
    )

    # Make the request
    response = client.put(
        "/entities/test-1", json={"name": "Updated Entity", "value": 43}
    )

    # Check the response
    assert response.status_code == 200
    assert response.json() == {
        "id": "test-1",
        "name": "Updated Entity",
        "value": 43,
        "created_at": entity.created_at.isoformat(),
        "updated_at": None,
    }

    # Check that the service was called
    mock_entity_service.update.assert_called_once()
    args, kwargs = mock_entity_service.update.call_args
    assert args[0] == "test-1"
    assert args[1] == {"name": "Updated Entity", "value": 43}
    assert isinstance(args[2], ServiceContext)


def test_entity_api_delete(entity_api, mock_entity_service, client):
    """Test deleting an entity through the API."""
    # Mock the service response
    mock_entity_service.delete.return_value = CommandResult.success(
        command_id="cmd-1", command_type="DeleteEntityCommand", output=True
    )

    # Make the request
    response = client.delete("/entities/test-1")

    # Check the response
    assert response.status_code == 204
    assert response.content == b""

    # Check that the service was called
    mock_entity_service.delete.assert_called_once()
    args, kwargs = mock_entity_service.delete.call_args
    assert args[0] == "test-1"
    assert isinstance(args[1], ServiceContext)


def test_entity_api_list(entity_api, mock_entity_service, client):
    """Test listing entities through the API."""
    # Mock the service response
    entities = [
        TestEntity(id="test-1", name="Entity 1", value=10),
        TestEntity(id="test-2", name="Entity 2", value=20),
    ]
    mock_entity_service.list.return_value = QueryResult.success(
        query_id="query-1", query_type="EntityListQuery", output=entities
    )

    # Make the request
    response = client.get("/entities")

    # Check the response
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["id"] == "test-1"
    assert response.json()[1]["id"] == "test-2"

    # Check that the service was called
    mock_entity_service.list.assert_called_once()
    args, kwargs = mock_entity_service.list.call_args
    assert isinstance(args[0], ServiceContext)


# Aggregate API tests


def test_aggregate_api_create(aggregate_api, mock_aggregate_service, client):
    """Test creating an aggregate through the API."""
    # Mock the service response
    aggregate = TestAggregate(id="agg-1", name="Test Aggregate")
    mock_aggregate_service.create.return_value = CommandResult.success(
        command_id="cmd-1", command_type="CreateAggregateCommand", output=aggregate
    )

    # Make the request
    response = client.post("/aggregates", json={"name": "Test Aggregate", "items": []})

    # Check the response
    assert response.status_code == 200
    assert response.json() == {
        "id": "agg-1",
        "name": "Test Aggregate",
        "items": [],
        "version": 1,  # Default version for new aggregates
        "created_at": aggregate.created_at.isoformat(),
        "updated_at": None,
    }

    # Check that the service was called
    mock_aggregate_service.create.assert_called_once()
    args, kwargs = mock_aggregate_service.create.call_args
    assert args[0] == {"name": "Test Aggregate", "items": []}
    assert isinstance(args[1], ServiceContext)


def test_aggregate_api_update(aggregate_api, mock_aggregate_service, client):
    """Test updating an aggregate through the API."""
    # Mock the service response
    aggregate = TestAggregate(id="agg-1", name="Updated Aggregate")
    aggregate.version = 2  # Increment version after update
    mock_aggregate_service.update.return_value = CommandResult.success(
        command_id="cmd-1", command_type="UpdateAggregateCommand", output=aggregate
    )

    # Make the request with version parameter
    response = client.put(
        "/aggregates/agg-1?version=1", json={"name": "Updated Aggregate"}
    )

    # Check the response
    assert response.status_code == 200
    assert response.json() == {
        "id": "agg-1",
        "name": "Updated Aggregate",
        "items": [],
        "version": 2,
        "created_at": aggregate.created_at.isoformat(),
        "updated_at": None,
    }

    # Check that the service was called
    mock_aggregate_service.update.assert_called_once()
    args, kwargs = mock_aggregate_service.update.call_args
    assert args[0] == "agg-1"
    assert args[1] == 1  # Version
    assert args[2] == {"name": "Updated Aggregate"}
    assert isinstance(args[3], ServiceContext)


# Error handling tests


def test_api_validation_error(entity_api, mock_entity_service, client):
    """Test handling of validation errors."""
    # Mock the service to raise a validation error
    mock_entity_service.create.side_effect = ValidationError("Name is required")

    # Make the request
    response = client.post("/entities", json={"value": 42})  # Missing required name

    # Check the response
    assert response.status_code == 422
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "message": "Name is required",
        "details": {},
    }


def test_api_authorization_error(entity_api, mock_entity_service, client):
    """Test handling of authorization errors."""
    # Mock the service to raise an authorization error
    mock_entity_service.get_by_id.side_effect = AuthorizationError("Permission denied")

    # Make the request
    response = client.get("/entities/test-1")

    # Check the response
    assert response.status_code == 403
    assert response.json() == {
        "code": "FORBIDDEN",
        "message": "Permission denied",
        "details": {},
    }


def test_api_command_error(entity_api, mock_entity_service, client):
    """Test handling of command errors."""
    # Mock the service to return a command error
    mock_entity_service.create.return_value = CommandResult.failure(
        command_id="cmd-1",
        command_type="CreateEntityCommand",
        error="Invalid data",
        error_code="VALIDATION_ERROR",
    )

    # Make the request
    response = client.post(
        "/entities",
        json={"name": "Test Entity", "value": -1},  # Negative value not allowed
    )

    # Check the response
    assert response.status_code == 422
    assert response.json() == {
        "code": "VALIDATION_ERROR",
        "message": "Invalid data",
        "details": {},
    }


def test_api_query_error(entity_api, mock_entity_service, client):
    """Test handling of query errors."""
    # Mock the service to return a query error
    mock_entity_service.get_by_id.return_value = QueryResult.failure(
        query_id="query-1",
        query_type="EntityByIdQuery",
        error="Entity not found",
        error_code="ENTITY_NOT_FOUND",
    )

    # Make the request
    response = client.get("/entities/nonexistent")

    # Check the response
    assert response.status_code == 404
    assert response.json() == {
        "code": "NOT_FOUND",
        "message": "Entity not found",
        "details": {},
    }


# Service API registry tests


def test_service_api_registry_register_entity_api(
    api_registry, mock_service_registry, router
):
    """Test registering an entity API with the service API registry."""
    # Register an entity API
    api = api_registry.register_entity_api(
        entity_type=TestEntity,
        prefix="/entities",
        tags=["Entities"],
        service_name="TestEntityService",
        create_dto=TestEntityCreateDto,
        update_dto=TestEntityUpdateDto,
        response_model=TestEntityResponseDto,
    )

    # Check that the API was created
    assert api is not None
    assert isinstance(api, EntityApi)
    assert api.entity_type == TestEntity
    assert api.prefix == "/entities"
    assert api.tags == ["Entities"]

    # Check that the service was retrieved from the registry
    mock_service_registry.get.assert_called_with("TestEntityService")


def test_service_api_registry_register_aggregate_api(
    api_registry, mock_service_registry, router
):
    """Test registering an aggregate API with the service API registry."""
    # Register an aggregate API
    api = api_registry.register_aggregate_api(
        aggregate_type=TestAggregate,
        prefix="/aggregates",
        tags=["Aggregates"],
        service_name="TestAggregateService",
        create_dto=TestAggregateCreateDto,
        update_dto=TestAggregateUpdateDto,
        response_model=TestAggregateResponseDto,
    )

    # Check that the API was created
    assert api is not None
    assert isinstance(api, AggregateApi)
    assert api.entity_type == TestAggregate
    assert api.prefix == "/aggregates"
    assert api.tags == ["Aggregates"]

    # Check that the service was retrieved from the registry
    mock_service_registry.get.assert_called_with("TestAggregateService")


def test_service_api_registry_get_api(api_registry):
    """Test getting an API from the service API registry."""
    # Register an entity API
    api = api_registry.register_entity_api(
        entity_type=TestEntity,
        prefix="/entities",
        tags=["Entities"],
        service_name="TestEntityService",
    )

    # Get the API by name
    retrieved_api = api_registry.get_api("TestEntityApi")

    # Check that the API was retrieved
    assert retrieved_api is api

    # Check that getting a non-existent API raises an error
    with pytest.raises(KeyError):
        api_registry.get_api("NonexistentApi")


# DTO creation utility tests


def test_create_dto_for_entity():
    """Test creating a DTO for an entity."""
    # Create a DTO for TestEntity
    dto_class = create_dto_for_entity(
        entity_type=TestEntity,
        name="TestEntityDto",
        exclude=["id", "created_at", "updated_at"],
        optional=["value"],
    )

    # Check the DTO class
    assert dto_class.__name__ == "TestEntityDto"

    # Check the DTO fields
    assert "name" in dto_class.__annotations__
    assert "value" in dto_class.__annotations__
    assert "id" not in dto_class.__annotations__
    assert "created_at" not in dto_class.__annotations__
    assert "updated_at" not in dto_class.__annotations__

    # Check that name is required and value is optional
    dto = dto_class(name="Test")
    assert dto.name == "Test"
    assert dto.value is None

    # Check that the DTO can be serialized to JSON
    dto_json = dto.model_dump_json()
    data = json.loads(dto_json)
    assert data["name"] == "Test"
    assert data["value"] is None


def test_create_response_model_for_entity():
    """Test creating a response model for an entity."""
    # Create a response model for TestEntity
    response_model = create_response_model_for_entity(
        entity_type=TestEntity,
        name="TestEntityResponse",
        additional_fields={"extra_field": (str, None)},
    )

    # Check the response model class
    assert response_model.__name__ == "TestEntityResponse"

    # Check the response model fields
    assert "id" in response_model.__annotations__
    assert "name" in response_model.__annotations__
    assert "value" in response_model.__annotations__
    assert "created_at" in response_model.__annotations__
    assert "updated_at" in response_model.__annotations__
    assert "extra_field" in response_model.__annotations__
