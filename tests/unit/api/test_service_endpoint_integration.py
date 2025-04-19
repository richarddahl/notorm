"""
Tests for domain service integration with API endpoints.

This module contains tests for the newer unified endpoint framework.
"""

import pytest
from datetime import datetime, UTC
from typing import Dict, Optional, Any, List
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.core.errors.result import Result, Success, Failure
from uno.domain.entity.service import ApplicationService, CrudService, DomainService
from uno.domain.entity.uow import UnitOfWork
from uno.api.endpoint import BaseEndpoint, CommandEndpoint, QueryEndpoint, CrudEndpoint


# Mock models for testing
class TestInput(BaseModel):
    name: str
    value: int


class TestOutput(BaseModel):
    id: str
    name: str
    value: int
    created_at: datetime


# Mock UnitOfWork for testing
class MockUnitOfWork(UnitOfWork):
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def commit(self):
        pass
        
    async def rollback(self):
        pass
    
    @property
    def repositories(self) -> List[Any]:
        return []


# Mock domain service for testing
class TestDomainService(DomainService):
    def __init__(self, uow=None):
        self.uow = uow or MockUnitOfWork()
    
    async def execute(self, input_data: TestInput) -> Result[TestOutput]:
        # Success case
        if input_data.value >= 0:
            return Success(TestOutput(
                id="test-id",
                name=input_data.name,
                value=input_data.value,
                created_at=datetime.now(UTC)
            ))
        # Failure case
        else:
            return Failure(
                message="Value cannot be negative",
                error_code="INVALID_VALUE"
            )


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    return app


def test_command_endpoint_success(test_app):
    """Test that a command endpoint handles success cases correctly."""
    # Create service
    service = TestDomainService()
    
    # Create endpoint
    endpoint = CommandEndpoint(
        service=service,
        command_model=TestInput,
        response_model=TestOutput,
        path="/test",
        method="post"
    )
    
    # Register with app
    endpoint.register(test_app)
    
    # Create test client
    client = TestClient(test_app)
    
    # Test successful request
    response = client.post("/test", json={"name": "test", "value": 42})
    assert response.status_code == 201  # Created status code
    data = response.json()
    assert data["name"] == "test"
    assert data["value"] == 42
    assert "id" in data
    assert "created_at" in data


def test_command_endpoint_failure(test_app):
    """Test that a command endpoint handles failure cases correctly."""
    # Create service
    service = TestDomainService()
    
    # Create endpoint
    endpoint = CommandEndpoint(
        service=service,
        command_model=TestInput,
        response_model=TestOutput,
        path="/test",
        method="post"
    )
    
    # Register with app
    endpoint.register(test_app)
    
    # Create test client
    client = TestClient(test_app)
    
    # Test error case
    response = client.post("/test", json={"name": "test", "value": -1})
    assert response.status_code == 400
    data = response.json()
    assert "message" in data
    assert "Value cannot be negative" in data["message"]
    assert "code" in data
    assert data["code"] == "INVALID_VALUE"


def test_crud_endpoint(test_app):
    """Test that a CRUD endpoint works correctly."""
    # Create mock CRUD service
    service = MagicMock(spec=CrudService)
    service.create = AsyncMock(return_value=Success(TestOutput(
        id="test-id",
        name="test",
        value=42,
        created_at=datetime.now(UTC)
    )))
    service.get_by_id = AsyncMock(return_value=Success(TestOutput(
        id="test-id",
        name="test",
        value=42,
        created_at=datetime.now(UTC)
    )))
    service.get_all = AsyncMock(return_value=Success([
        TestOutput(
            id="test-id",
            name="test",
            value=42,
            created_at=datetime.now(UTC)
        )
    ]))
    service.update = AsyncMock(return_value=Success(TestOutput(
        id="test-id",
        name="updated",
        value=43,
        created_at=datetime.now(UTC)
    )))
    service.delete = AsyncMock(return_value=Success(None))
    
    # Create endpoint
    endpoint = CrudEndpoint(
        service=service,
        create_model=TestInput,
        response_model=TestOutput,
        path="/tests"
    )
    
    # Register with app
    endpoint.register(test_app)
    
    # Create test client
    client = TestClient(test_app)
    
    # Test create
    response = client.post("/tests", json={"name": "test", "value": 42})
    assert response.status_code == 201
    
    # Test get by ID
    response = client.get("/tests/test-id")
    assert response.status_code == 200
    
    # Test list
    response = client.get("/tests")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # Test update
    response = client.put("/tests/test-id", json={"name": "updated", "value": 43})
    assert response.status_code == 200
    
    # Test delete
    response = client.delete("/tests/test-id")
    assert response.status_code == 204