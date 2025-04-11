"""
Unit tests for vector search dependency injection.

These tests ensure that the vector search components are properly
integrated with the dependency injection system.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

from uno.dependencies import (
    ServiceProvider, 
    get_service_provider,
    VectorConfigServiceProtocol,
    VectorSearchServiceProtocol,
    VectorUpdateServiceProtocol,
    BatchVectorUpdateServiceProtocol,
    RAGServiceProtocol
)
from uno.dependencies.vector_provider import (
    VectorConfigService,
    VectorSearchProvider,
    get_vector_search_service,
    get_rag_service
)
from uno.dependencies.interfaces import UnoConfigProtocol
from uno.domain.event_dispatcher import EventDispatcher


class MockConfig(UnoConfigProtocol):
    """Mock configuration for testing."""
    
    def __init__(self, values=None):
        self._values = values or {
            "VECTOR_DIMENSIONS": 768,
            "VECTOR_INDEX_TYPE": "hnsw",
            "VECTOR_BATCH_SIZE": 50,
            "VECTOR_UPDATE_INTERVAL": 0.5,
            "VECTOR_AUTO_START": False,
            "VECTOR_ENTITIES": {
                "test": {
                    "fields": ["title", "content"],
                    "dimensions": 384,
                    "index_type": "ivfflat"
                }
            }
        }
    
    def get_value(self, key, default=None):
        """Get configuration value by key."""
        return self._values.get(key, default)
    
    def all(self):
        """Get all configuration values."""
        return dict(self._values)


@pytest.fixture
def mock_service_provider():
    """Create a service provider with mocked components for testing."""
    provider = ServiceProvider()
    provider._initialized = True
    provider._logger = logging.getLogger("test")
    
    # Register a mock config
    mock_config = MockConfig()
    provider.register_service(UnoConfigProtocol, mock_config)
    
    return provider


@pytest.fixture
def vector_config_service(mock_service_provider):
    """Create a VectorConfigService for testing."""
    config = mock_service_provider.get_config()
    return VectorConfigService(config)


def test_vector_config_service_initialization(vector_config_service):
    """Test that the VectorConfigService initializes correctly from config."""
    # Check default values
    assert vector_config_service._default_dimensions == 768
    assert vector_config_service._default_index_type == "hnsw"
    
    # Check entity-specific values
    assert "test" in vector_config_service._entity_configs
    assert vector_config_service.get_dimensions("test") == 384
    assert vector_config_service.get_index_type("test") == "ivfflat"
    assert vector_config_service.get_vectorizable_fields("test") == ["title", "content"]
    assert vector_config_service.is_vectorizable("test")
    
    # Test default fallbacks
    assert vector_config_service.get_dimensions() == 768
    assert vector_config_service.get_index_type() == "hnsw"
    assert vector_config_service.get_vectorizable_fields("nonexistent") == []
    assert not vector_config_service.is_vectorizable("nonexistent")


def test_register_vectorizable_entity(vector_config_service):
    """Test registering a new vectorizable entity."""
    # Register new entity
    vector_config_service.register_vectorizable_entity(
        entity_type="document",
        fields=["title", "body", "summary"],
        dimensions=1536,
        index_type="hnsw"
    )
    
    # Check it was registered correctly
    assert "document" in vector_config_service._entity_configs
    assert vector_config_service.get_dimensions("document") == 1536
    assert vector_config_service.get_index_type("document") == "hnsw"
    assert vector_config_service.get_vectorizable_fields("document") == ["title", "body", "summary"]
    assert vector_config_service.is_vectorizable("document")


def test_vector_search_provider_registration(mock_service_provider):
    """Test the vector search provider registration process."""
    # Create a vector search provider
    provider = VectorSearchProvider()
    provider._initialized = True
    provider._logger = logging.getLogger("test")
    
    # Mock methods to avoid circular dependencies in testing
    provider.get_config = MagicMock(return_value=MockConfig())
    provider.get_service = MagicMock(side_effect=ValueError("Service not found"))
    provider.register_service = MagicMock()
    
    # Register services
    provider.register()
    
    # Check that services were registered
    assert provider.register_service.call_count >= 5  # Config, handlers, update services
    
    # Check the first call was to register VectorConfigService
    first_call = provider.register_service.call_args_list[0]
    assert first_call[0][0] == VectorConfigServiceProtocol


@patch("uno.dependencies.vector_provider._vector_search_factory")
@patch("uno.dependencies.vector_provider._rag_service_factory")
def test_get_vector_services(mock_rag_factory, mock_search_factory, mock_service_provider):
    """Test the vector service getter functions."""
    # Set up mocks
    mock_search_service = MagicMock()
    mock_search_factory.return_value = mock_search_service
    
    mock_rag_service = MagicMock()
    mock_rag_factory.return_value = mock_rag_service
    
    # Get services
    search_service = get_vector_search_service("test", "test_table")
    rag_service = get_rag_service(search_service)
    
    # Check results
    assert search_service == mock_search_service
    assert rag_service == mock_rag_service
    
    # Check factory calls
    mock_search_factory.assert_called_once_with("test", "test_table", None)
    mock_rag_factory.assert_called_once_with(mock_search_service)