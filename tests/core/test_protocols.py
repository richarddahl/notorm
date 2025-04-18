"""
Tests for the core protocol implementations.
"""
import pytest
from typing import Protocol, runtime_checkable


@runtime_checkable
class TestRepositoryProtocol(Protocol):
    """A simple repository protocol for testing."""
    async def get_by_id(self, id): ...
    async def find_all(self): ...
    async def save(self, entity): ...


@runtime_checkable
class TestServiceProtocol(Protocol):
    """A simple service protocol for testing."""
    async def get_by_id(self, id): ...
    async def get_all(self): ...
    async def create(self, data): ...
    async def update(self, id, data): ...


class SampleRepository:
    """A sample repository implementation for testing protocol compliance."""
    async def get_by_id(self, id):
        """Get entity by ID."""
        return {"id": id}
    
    async def find_all(self):
        """Find all entities."""
        return []
    
    async def save(self, entity):
        """Save entity."""
        return entity


class SampleService:
    """A sample service implementation for testing protocol compliance."""
    async def get_by_id(self, id):
        """Get entity by ID."""
        return {"success": True, "value": {"id": id}}
    
    async def get_all(self):
        """Get all entities."""
        return {"success": True, "value": []}
    
    async def create(self, data):
        """Create entity."""
        return {"success": True, "value": {"id": "new-id", **data}}
    
    async def update(self, id, data):
        """Update entity."""
        return {"success": True, "value": {"id": id, **data}}


def test_repository_protocol_compliance():
    """Test if SampleRepository complies with TestRepositoryProtocol."""
    repo = SampleRepository()
    assert isinstance(repo, TestRepositoryProtocol)


def test_service_protocol_compliance():
    """Test if SampleService complies with TestServiceProtocol."""
    service = SampleService()
    assert isinstance(service, TestServiceProtocol)