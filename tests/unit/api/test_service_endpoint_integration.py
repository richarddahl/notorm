"""
Tests for domain service integration with API endpoints.
"""

import pytest
from datetime import datetime, UTC
from typing import Dict, Optional, Any, List
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient
from pydantic import BaseModel

from uno.core.errors.result import Result, Success, Failure
from uno.domain.unified_services import DomainService
from uno.domain.unit_of_work import UnitOfWork
from uno.api.service_endpoint_adapter import DomainServiceAdapter
from uno.api.service_endpoint_factory import DomainServiceEndpointFactory


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
class TestDomainService(DomainService[TestInput, TestOutput, MockUnitOfWork]):
    async def _execute_internal(self, input_data: TestInput) -> Result[TestOutput]:
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


# Mock service factory that returns our test service with a mock UoW
class MockServiceFactory:
    def create_domain_service(self, service_class, **kwargs):
        uow = MockUnitOfWork()
        return service_class(uow=uow)


@pytest.fixture
def test_app():
    """Create a test FastAPI application."""
    app = FastAPI()
    return app


@pytest.fixture
def endpoint_factory():
    """Create endpoint factory with mock service factory."""
    service_factory = MockServiceFactory()
    return DomainServiceEndpointFactory(service_factory=service_factory)


def test_service_adapter_success():
    """Test that service adapter handles success cases correctly."""
    # Create mock service
    service = AsyncMock()
    service.execute = AsyncMock(return_value=Success({"id": "test-id", "name": "test"}))
    
    # Create adapter
    adapter = DomainServiceAdapter(service=service)
    
    # Call execute (run in an event loop)
    import asyncio
    result = asyncio.run(adapter.execute({"name": "test", "value": 123}))
    
    # Verify result
    assert result == {"id": "test-id", "name": "test"}
    service.execute.assert_called_once()


def test_service_adapter_failure():
    """Test that service adapter handles failure cases correctly."""
    # Create mock service
    service = AsyncMock()
    service.execute = AsyncMock(return_value=Failure("Test error", error_code="TEST_ERROR"))
    
    # Create adapter
    adapter = DomainServiceAdapter(service=service)
    
    # Call execute (run in an event loop)
    import asyncio
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as excinfo:
        asyncio.run(adapter.execute({"name": "test", "value": -1}))
    
    # Verify error details
    assert excinfo.value.status_code == 400
    assert "TEST_ERROR" in str(excinfo.value.detail)


def test_create_domain_service_endpoint(test_app, endpoint_factory):
    """Test creating an endpoint for a domain service."""
    router = APIRouter()
    
    # Create an endpoint
    endpoint_factory.create_domain_service_endpoint(
        router=router,
        service_class=TestDomainService,
        path="/test",
        method="POST",
        response_model=TestOutput,
    )
    
    # Add router to app
    test_app.include_router(router)
    
    # Create test client
    client = TestClient(test_app)
    
    # Test successful request
    response = client.post("/test", json={"name": "test", "value": 42})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test"
    assert data["value"] == 42
    assert "id" in data
    assert "created_at" in data
    
    # Test error case
    response = client.post("/test", json={"name": "test", "value": -1})
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "INVALID_VALUE"
    assert "Value cannot be negative" in data["message"]