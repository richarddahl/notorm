"""Tests for the offline synchronization engine.

This module tests the synchronization engine implementation, including
the network adapters, conflict resolution, and change tracking.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from uno.offline.store.store import OfflineStore
from uno.offline.sync.options import SyncOptions
from uno.offline.sync.engine import SynchronizationEngine
from uno.offline.sync.adapter import NetworkAdapter
from uno.offline.sync.errors import (
    SyncError,
    NetworkError,
    ConflictError,
    SyncCancelledError
)
from uno.offline.sync.conflict import (
    ServerWinsResolver,
    ClientWinsResolver,
    TimestampBasedResolver
)
from uno.offline.sync.tracker import ChangeTracker


class MockNetworkAdapter(NetworkAdapter):
    """Mock network adapter for testing."""
    
    def __init__(self, online=True):
        super().__init__()
        self.online = online
        self.fetch_changes_called = False
        self.send_change_called = False
        self.fetch_changes_params = []
        self.send_change_params = []
        self.server_timestamp = "2023-01-01T00:00:00Z"
        
        # Mock data to return
        self.remote_changes = {}
        self.conflict_on_send = False
        self.server_versions = {}
    
    async def fetch_changes(self, collection, query_params=None):
        """Fetch changes from the server."""
        self.fetch_changes_called = True
        self.fetch_changes_params.append((collection, query_params))
        
        if not self.online:
            raise NetworkError("Offline")
        
        changes = self.remote_changes.get(collection, [])
        for change in changes:
            yield change
    
    async def send_change(self, collection, data):
        """Send a change to the server."""
        self.send_change_called = True
        self.send_change_params.append((collection, data))
        
        if not self.online:
            raise NetworkError("Offline")
        
        if self.conflict_on_send:
            server_version = self.server_versions.get(data.get("id"))
            if server_version:
                raise ConflictError(
                    "Conflict",
                    data,
                    server_version
                )
        
        # Return a copy of the data with a server timestamp
        result = data.copy()
        result["server_processed"] = True
        return result
    
    async def is_online(self):
        """Check if the server is reachable."""
        return self.online
    
    def get_server_timestamp(self):
        """Get the server's timestamp."""
        return self.server_timestamp


class TestSyncOptions:
    """Tests for the SyncOptions class."""
    
    def test_basic_options(self):
        """Test basic options configuration."""
        options = SyncOptions(
            collections=["users", "products"],
            strategy="two-way",
            network_adapter=MockNetworkAdapter(),
            conflict_strategy="server-wins"
        )
        
        assert options.collections == ["users", "products"]
        assert options.strategy == "two-way"
        assert isinstance(options.network_adapter, MockNetworkAdapter)
        assert options.conflict_strategy == "server-wins"
    
    def test_invalid_strategy(self):
        """Test that invalid strategies raise an error."""
        with pytest.raises(ValueError):
            SyncOptions(
                collections=["users"],
                strategy="invalid-strategy",
                network_adapter=MockNetworkAdapter()
            )
    
    def test_resolver_instance(self):
        """Test using a resolver instance."""
        resolver = ServerWinsResolver()
        options = SyncOptions(
            collections=["users"],
            strategy="two-way",
            network_adapter=MockNetworkAdapter(),
            conflict_strategy=resolver
        )
        
        assert options.conflict_strategy is resolver


@pytest.fixture
def mock_store():
    """Create a mock offline store."""
    store = AsyncMock(spec=OfflineStore)
    store.get.return_value = None
    store.put.return_value = None
    store.get_metadata.return_value = None
    store.set_metadata.return_value = None
    store.delete_metadata.return_value = None
    
    # Sync version of get_metadata for the ChangeTracker
    store.get_metadata_sync = MagicMock(return_value=None)
    
    return store


@pytest.fixture
def mock_adapter():
    """Create a mock network adapter."""
    return MockNetworkAdapter()


@pytest.fixture
def sync_engine(mock_store, mock_adapter):
    """Create a synchronization engine with mocks."""
    options = SyncOptions(
        collections=["users", "products"],
        strategy="two-way",
        network_adapter=mock_adapter,
        conflict_strategy="server-wins"
    )
    
    return SynchronizationEngine(mock_store, options)


class TestSynchronizationEngine:
    """Tests for the SynchronizationEngine class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, sync_engine):
        """Test that the engine initializes correctly."""
        assert sync_engine.store is not None
        assert sync_engine.options is not None
        assert sync_engine.network_adapter is not None
        assert isinstance(sync_engine.conflict_resolver, ServerWinsResolver)
        assert sync_engine._running is False
        assert sync_engine._cancel_requested is False
    
    @pytest.mark.asyncio
    async def test_offline_error(self, sync_engine):
        """Test that being offline raises an error."""
        sync_engine.network_adapter.online = False
        
        with pytest.raises(NetworkError):
            await sync_engine.sync()
    
    @pytest.mark.asyncio
    async def test_empty_sync(self, sync_engine, mock_store):
        """Test synchronizing with no changes."""
        mock_store.get_metadata.return_value = "2023-01-01T00:00:00Z"
        
        result = await sync_engine.sync()
        
        assert result["uploaded"] == 0
        assert result["downloaded"] == 0
        assert result["conflicts"] == 0
        assert len(result["errors"]) == 0
        assert sync_engine.network_adapter.fetch_changes_called is True
    
    @pytest.mark.asyncio
    async def test_pull_changes(self, sync_engine, mock_store, mock_adapter):
        """Test pulling changes from the server."""
        # Set up mock data
        mock_adapter.remote_changes = {
            "users": [
                {"id": "user1", "name": "User 1", "updated_at": "2023-01-01T00:00:01Z"},
                {"id": "user2", "name": "User 2", "updated_at": "2023-01-01T00:00:02Z"}
            ]
        }
        
        # Run sync
        result = await sync_engine.sync()
        
        # Verify results
        assert result["downloaded"] == 2
        assert result["uploaded"] == 0
        assert mock_store.put.call_count == 2
    
    @pytest.mark.asyncio
    async def test_push_changes(self, sync_engine, mock_store, mock_adapter):
        """Test pushing changes to the server."""
        # Set up tracking changes
        mock_store.get_metadata.side_effect = lambda key: "user1,user2" if "sync:changes:users" in key else None
        
        # Set up mock data
        mock_store.get.side_effect = lambda collection, id: {
            "id": id,
            "name": f"User {id}",
            "updated_at": "2023-01-01T00:00:01Z"
        } if collection == "users" and id in ["user1", "user2"] else None
        
        # Run sync
        result = await sync_engine.sync()
        
        # Verify results
        assert result["uploaded"] == 2
        assert result["downloaded"] == 0
        assert mock_adapter.send_change_called is True
        assert len(mock_adapter.send_change_params) == 2
    
    @pytest.mark.asyncio
    async def test_conflict_resolution(self, sync_engine, mock_store, mock_adapter):
        """Test conflict resolution."""
        # Set up tracking changes
        mock_store.get_metadata.side_effect = lambda key: "user1" if "sync:changes:users" in key else None
        
        # Set up mock data
        mock_store.get.side_effect = lambda collection, id: {
            "id": id,
            "name": "Local User",
            "updated_at": "2023-01-01T00:00:02Z"
        } if collection == "users" and id == "user1" else None
        
        # Set up conflict
        mock_adapter.conflict_on_send = True
        mock_adapter.server_versions = {
            "user1": {
                "id": "user1",
                "name": "Server User",
                "updated_at": "2023-01-01T00:00:01Z"
            }
        }
        
        # Set up spy on conflict resolver
        with patch.object(ServerWinsResolver, 'resolve', wraps=sync_engine.conflict_resolver.resolve) as spy:
            # Run sync
            result = await sync_engine.sync()
            
            # Verify results
            assert result["conflicts"] == 1
            assert spy.called is True
            # Server version should win with ServerWinsResolver
            mock_store.put.assert_called_with("users", mock_adapter.server_versions["user1"])
    
    @pytest.mark.asyncio
    async def test_cancellation(self, sync_engine, mock_store, mock_adapter):
        """Test cancellation of synchronization."""
        # Set up a lot of changes to sync
        mock_adapter.remote_changes = {
            "users": [{"id": f"user{i}", "name": f"User {i}"} for i in range(100)]
        }
        
        # Add a delay to fetch_changes to simulate a long operation
        original_fetch = mock_adapter.fetch_changes
        
        async def delayed_fetch(*args, **kwargs):
            async for item in original_fetch(*args, **kwargs):
                await asyncio.sleep(0.01)  # Small delay
                yield item
        
        mock_adapter.fetch_changes = delayed_fetch
        
        # Start sync in a task
        sync_task = asyncio.create_task(sync_engine.sync())
        
        # Wait a bit and then cancel
        await asyncio.sleep(0.05)
        sync_engine.cancel()
        
        # Check for cancellation
        with pytest.raises(SyncCancelledError):
            await sync_task
        
        # Verify the engine state
        assert sync_engine._running is False
        assert sync_engine._cancel_requested is True


class TestChangeTracker:
    """Tests for the ChangeTracker class."""
    
    @pytest.fixture
    def tracker(self, mock_store):
        """Create a change tracker with a mock store."""
        return ChangeTracker(mock_store)
    
    @pytest.mark.asyncio
    async def test_track_change(self, tracker, mock_store):
        """Test tracking a change."""
        # Initial state: no changes
        mock_store.get_metadata.return_value = None
        
        # Track a change
        await tracker.track_change("users", "user1")
        
        # Should save to metadata
        mock_store.set_metadata.assert_called_with("sync:changes:users", "user1")
        
        # Track another change
        mock_store.get_metadata.return_value = "user1"
        await tracker.track_change("users", "user2")
        
        # Should save both changes
        mock_store.set_metadata.assert_called_with("sync:changes:users", "user1,user2")
    
    @pytest.mark.asyncio
    async def test_mark_synchronized(self, tracker, mock_store):
        """Test marking a change as synchronized."""
        # Initial state: two changes
        mock_store.get_metadata.return_value = "user1,user2"
        
        # Mark one as synchronized
        await tracker.mark_synchronized("users", "user1")
        
        # Should save the remaining change
        mock_store.set_metadata.assert_called_with("sync:changes:users", "user2")
        
        # Mark the last one as synchronized
        mock_store.get_metadata.return_value = "user2"
        await tracker.mark_synchronized("users", "user2")
        
        # Should delete the metadata since there are no more changes
        mock_store.delete_metadata.assert_called_with("sync:changes:users")
    
    @pytest.mark.asyncio
    async def test_get_local_changes(self, tracker, mock_store):
        """Test getting local changes."""
        # Initial state: two changes
        mock_store.get_metadata.return_value = "user1,user2"
        
        # Set up mock data
        user1 = {"id": "user1", "name": "User 1"}
        user2 = {"id": "user2", "name": "User 2"}
        
        mock_store.get.side_effect = lambda collection, id: {
            "users": {
                "user1": user1,
                "user2": user2
            }
        }.get(collection, {}).get(id)
        
        # Get local changes
        changes = await tracker.get_local_changes("users")
        
        # Should return both records
        assert len(changes) == 2
        assert user1 in changes
        assert user2 in changes
        
        # Test with a missing record (should be removed from tracking)
        mock_store.get_metadata.return_value = "user1,user3"
        mock_store.get.side_effect = lambda collection, id: {
            "users": {
                "user1": user1
            }
        }.get(collection, {}).get(id)
        
        changes = await tracker.get_local_changes("users")
        
        # Should return only one record and mark the missing one as synchronized
        assert len(changes) == 1
        assert changes[0] == user1
        mock_store.set_metadata.assert_called_with("sync:changes:users", "user1")
    
    def test_has_unsynchronized_changes(self, tracker, mock_store):
        """Test checking for unsynchronized changes."""
        # Set up mock data
        mock_store.get_metadata_sync.return_value = "user1,user2"
        
        # Check for changes
        assert tracker.has_unsynchronized_changes("users", "user1") is True
        assert tracker.has_unsynchronized_changes("users", "user3") is False
        
        # Test with invalid data
        mock_store.get_metadata_sync.return_value = None
        assert tracker.has_unsynchronized_changes("users", "user1") is False