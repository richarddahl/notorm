"""
Tests for the dependency injection testing utilities.

This module demonstrates how to use the testing utilities
to mock dependencies in tests.
"""

import pytest
from unittest.mock import MagicMock
import inject

from uno.dependencies.testing import (
    TestingContainer,
    MockRepository,
    MockConfig,
    MockService,
    TestSession,
    configure_test_container
)
from uno.dependencies.interfaces import (
    UnoRepositoryProtocol,
    UnoConfigProtocol,
    UnoServiceProtocol,
    UnoSessionProviderProtocol
)


class TestTestingContainer:
    """Tests for the TestingContainer class."""
    
    def setup_method(self):
        """Set up before each test."""
        # Clean up any existing injector configuration
        inject.clear()
        
    def teardown_method(self):
        """Clean up after each test."""
        # Clean up any remaining injector configuration
        inject.clear()
    
    def test_bind_and_configure(self):
        """Test binding and configuring a container."""
        # Create a container and bind a test value
        container = TestingContainer()
        mock_repo = MagicMock(spec=UnoRepositoryProtocol)
        container.bind(UnoRepositoryProtocol, mock_repo)
        
        # Configure the container
        container.configure()
        
        # Verify the binding is registered
        assert inject.instance(UnoRepositoryProtocol) is mock_repo
        
        # Clean up
        container.restore()
    
    def test_container_saves_configuration(self):
        """Test that TestingContainer correctly handles configuration."""
        # Setup initial configuration
        initial_repo = MagicMock(spec=UnoRepositoryProtocol)
        inject.clear_and_configure(lambda binder: binder.bind(UnoRepositoryProtocol, initial_repo))
        
        # Create a test container 
        container = TestingContainer()
        
        # Configure with a different repo
        test_repo = MagicMock(spec=UnoRepositoryProtocol)
        container.bind(UnoRepositoryProtocol, test_repo)
        container.configure()
        
        # Verify test binding is active
        assert inject.instance(UnoRepositoryProtocol) is test_repo
        
        # Clean up
        inject.clear()


class TestMockFactories:
    """Tests for the mock factory classes."""
    
    def test_mock_repository(self):
        """Test creating a mock repository."""
        repo = MockRepository.create()
        
        # Verify the repository is properly mocked
        assert isinstance(repo, MagicMock)
        assert hasattr(repo, 'get')
        assert hasattr(repo, 'list')
        assert hasattr(repo, 'create')
        assert hasattr(repo, 'update')
        assert hasattr(repo, 'delete')
    
    @pytest.mark.asyncio
    async def test_repository_with_items(self):
        """Test creating a repository with predefined items."""
        items = [
            MagicMock(id='1', name='Item 1'),
            MagicMock(id='2', name='Item 2')
        ]
        
        repo = MockRepository.with_items(items)
        
        # Verify list returns all items
        result = await repo.list()
        assert result == items
        
        # Verify get returns matching item
        item = await repo.get('1')
        assert item is items[0]
        
        # Verify get returns None for non-existent item
        item = await repo.get('999')
        assert item is None
    
    def test_mock_config(self):
        """Test creating a mock configuration."""
        values = {'foo': 'bar', 'baz': 123}
        config = MockConfig.create(values)
        
        # Verify get_value returns the configured values
        assert config.get_value('foo') == 'bar'
        assert config.get_value('baz') == 123
        assert config.get_value('not_found', 'default') == 'default'
        
        # Verify all returns all values
        assert config.all() == values
    
    @pytest.mark.asyncio
    async def test_mock_service(self):
        """Test creating a mock service."""
        service = MockService.create('test_result')
        
        # Verify execute returns the configured value
        result = await service.execute()
        assert result == 'test_result'


@pytest.fixture
def test_container():
    """Fixture for a test container."""
    container = configure_test_container()
    yield container
    container.restore()


class TestConfigureTestContainer:
    """Tests for the configure_test_container function."""
    
    def test_default_configuration(self, test_container):
        """Test the default configuration."""
        # Verify default mocks are configured
        assert isinstance(inject.instance(UnoRepositoryProtocol), MagicMock)
        assert isinstance(inject.instance(UnoConfigProtocol), MagicMock)
        assert isinstance(inject.instance(UnoSessionProviderProtocol), MagicMock)
    
    def test_custom_configuration(self):
        """Test custom configuration."""
        custom_repo = MagicMock(spec=UnoRepositoryProtocol)
        custom_service = MagicMock(spec=UnoServiceProtocol)
        
        container = configure_test_container({
            UnoRepositoryProtocol: custom_repo,
            UnoServiceProtocol: custom_service
        })
        
        # Verify custom mocks are configured
        assert inject.instance(UnoRepositoryProtocol) is custom_repo
        assert inject.instance(UnoServiceProtocol) is custom_service
        
        container.restore()


# Example of a class that uses dependency injection
class ItemService:
    """Example service that uses dependency injection."""
    
    @inject.autoparams()
    def __init__(self, repository: UnoRepositoryProtocol, config: UnoConfigProtocol):
        """Initialize with injected dependencies."""
        self.repository = repository
        self.config = config
    
    async def get_items(self, limit=None):
        """Get items with an optional limit."""
        default_limit = self.config.get_value('DEFAULT_LIMIT', 100)
        limit = limit or default_limit
        return await self.repository.list(limit=limit)


class TestItemService:
    """Tests for the example ItemService class."""
    
    @pytest.mark.asyncio
    async def test_get_items_with_mock_dependencies(self, test_container):
        """Test getting items with mock dependencies."""
        # Configure mock repository to return specific items
        items = [MagicMock(id='1', name='Test Item')]
        repo = MockRepository.with_items(items)
        config = MockConfig.create({'DEFAULT_LIMIT': 10})
        
        # Override default mocks
        inject.clear_and_configure(lambda binder: [
            binder.bind(UnoRepositoryProtocol, repo),
            binder.bind(UnoConfigProtocol, config)
        ])
        
        # Create service (dependencies will be injected)
        service = ItemService()
        
        # Test with default limit from config
        result = await service.get_items()
        assert result == items
        
        # Verify repository was called with the right limit
        repo.list.assert_called_with(limit=10)
        
        # Test with explicit limit
        await service.get_items(limit=5)
        repo.list.assert_called_with(limit=5)