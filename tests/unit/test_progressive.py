"""Tests for progressive enhancement.

This module tests the progressive enhancement functionality, including
connectivity detection, capability detection, and feature enhancement.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from uno.offline.progressive.detector import (
    ConnectivityDetector,
    CapabilityDetector,
    ConnectivityStatus
)
from uno.offline.progressive.config import (
    ProgressiveConfig,
    FeatureConfig,
    FeatureLevel
)
from uno.offline.progressive.strategies import (
    DefaultStrategy,
    BatteryAwareStrategy,
    BandwidthAwareStrategy,
    StorageAwareStrategy
)
from uno.offline.progressive.enhancer import ProgressiveEnhancer


class TestConnectivityDetector:
    """Tests for the ConnectivityDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a connectivity detector."""
        detector = ConnectivityDetector(check_interval=0.1)
        # Patch the _check_connectivity method to avoid actual network calls
        detector._check_connectivity = AsyncMock()
        return detector
    
    @pytest.mark.asyncio
    async def test_initialization(self, detector):
        """Test that the detector initializes correctly."""
        assert detector.status == ConnectivityStatus.OFFLINE
        assert detector.check_interval == 0.1
        assert len(detector.endpoints) > 0
        assert detector.timeout > 0
    
    @pytest.mark.asyncio
    async def test_start_stop(self, detector):
        """Test starting and stopping the detector."""
        await detector.start()
        assert detector._running is True
        assert detector._task is not None
        
        await detector.stop()
        assert detector._running is False
        assert detector._task is None
    
    @pytest.mark.asyncio
    async def test_check_now(self, detector):
        """Test checking connectivity immediately."""
        # Mock the _check_connectivity method to update the status
        async def check_mock():
            detector._status = ConnectivityStatus.GOOD
        detector._check_connectivity = check_mock
        
        status = await detector.check_now()
        assert status == ConnectivityStatus.GOOD
        assert detector.status == ConnectivityStatus.GOOD
    
    @pytest.mark.asyncio
    async def test_listeners(self, detector):
        """Test connectivity change listeners."""
        listener = MagicMock()
        detector.add_listener(listener)
        
        # Simulate a connectivity change
        detector._status = ConnectivityStatus.OFFLINE
        detector._notify_listeners()
        
        # Check that the listener was called
        listener.assert_called_once_with(ConnectivityStatus.OFFLINE)
        
        # Remove the listener
        detector.remove_listener(listener)
        
        # Reset the mock and simulate another change
        listener.reset_mock()
        detector._status = ConnectivityStatus.GOOD
        detector._notify_listeners()
        
        # Check that the listener was not called
        listener.assert_not_called()


class TestCapabilityDetector:
    """Tests for the CapabilityDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a capability detector."""
        return CapabilityDetector()
    
    @pytest.mark.asyncio
    async def test_detect_all(self, detector):
        """Test detecting all capabilities."""
        capabilities = await detector.detect_all()
        
        # Check that all capabilities are present
        assert "storage_quota" in capabilities
        assert "network_type" in capabilities
        assert "device_memory" in capabilities
        assert "cpu_cores" in capabilities
        assert "battery_status" in capabilities
        
        # Check that all capabilities have sensible values
        assert isinstance(capabilities["storage_quota"], int)
        assert isinstance(capabilities["network_type"], str)
        assert isinstance(capabilities["device_memory"], float)
        assert isinstance(capabilities["cpu_cores"], int)
        assert isinstance(capabilities["battery_status"], dict)


class TestEnhancementStrategies:
    """Tests for enhancement strategies."""
    
    @pytest.fixture
    def feature_config(self):
        """Create a test feature configuration."""
        return FeatureConfig(
            name="test-feature",
            default_level="good",
            levels={
                "offline": FeatureLevel(
                    enabled=True,
                    config={"mode": "offline"}
                ),
                "poor": FeatureLevel(
                    enabled=True,
                    config={"mode": "poor"}
                ),
                "good": FeatureLevel(
                    enabled=True,
                    config={"mode": "good"}
                ),
                "excellent": FeatureLevel(
                    enabled=True,
                    config={"mode": "excellent"}
                )
            }
        )
    
    def test_default_strategy(self, feature_config):
        """Test the default enhancement strategy."""
        strategy = DefaultStrategy()
        
        # Test with different connectivity statuses
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.OFFLINE,
            {}
        )
        assert level == "offline"
        
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.GOOD,
            {}
        )
        assert level == "good"
        
        # Test with capabilities
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.EXCELLENT,
            {"device_memory": 1.0}
        )
        assert level == "good"  # Should degrade to good due to low memory
        
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.EXCELLENT,
            {"device_memory": 4.0}
        )
        assert level == "excellent"  # Should stay at excellent with enough memory
    
    def test_battery_aware_strategy(self, feature_config):
        """Test the battery-aware enhancement strategy."""
        strategy = BatteryAwareStrategy()
        
        # Test with low battery
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.EXCELLENT,
            {
                "device_memory": 4.0,
                "battery_status": {
                    "charging": False,
                    "level": 0.1  # 10% battery
                }
            }
        )
        assert level == "good"  # Should degrade to good due to low battery
        
        # Test with charging battery
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.EXCELLENT,
            {
                "device_memory": 4.0,
                "battery_status": {
                    "charging": True,
                    "level": 0.1  # 10% battery, but charging
                }
            }
        )
        assert level == "excellent"  # Should stay at excellent when charging
    
    def test_bandwidth_aware_strategy(self, feature_config):
        """Test the bandwidth-aware enhancement strategy."""
        strategy = BandwidthAwareStrategy()
        
        # Test with cellular network
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.EXCELLENT,
            {
                "device_memory": 4.0,
                "network_type": "cellular"
            }
        )
        assert level == "poor"  # Should degrade to poor on cellular
        
        # Test with slow-2g network
        level = strategy.determine_level(
            feature_config,
            ConnectivityStatus.GOOD,
            {
                "device_memory": 4.0,
                "network_type": "slow-2g"
            }
        )
        assert level == "offline"  # Should degrade to offline on slow-2g


class TestProgressiveEnhancer:
    """Tests for the ProgressiveEnhancer class."""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration."""
        config = ProgressiveConfig()
        
        # Add a test feature
        test_feature = FeatureConfig(
            name="test-feature",
            default_level="good",
            levels={
                "offline": FeatureLevel(
                    enabled=True,
                    config={"mode": "offline"}
                ),
                "poor": FeatureLevel(
                    enabled=True,
                    config={"mode": "poor"}
                ),
                "good": FeatureLevel(
                    enabled=True,
                    config={"mode": "good"}
                ),
                "excellent": FeatureLevel(
                    enabled=True,
                    config={"mode": "excellent"}
                )
            }
        )
        config.add_feature(test_feature)
        
        return config
    
    @pytest.fixture
    def mock_connectivity_detector(self):
        """Create a mock connectivity detector."""
        detector = MagicMock()
        detector.status = ConnectivityStatus.GOOD
        detector.start = AsyncMock()
        detector.stop = AsyncMock()
        detector.add_listener = MagicMock()
        return detector
    
    @pytest.fixture
    def mock_capability_detector(self):
        """Create a mock capability detector."""
        detector = MagicMock()
        detector.detect_all = AsyncMock(return_value={
            "device_memory": 4.0,
            "network_type": "wifi",
            "storage_quota": 1024 * 1024 * 100
        })
        return detector
    
    @pytest.fixture
    def enhancer(self, config, mock_connectivity_detector, mock_capability_detector):
        """Create a progressive enhancer with mocks."""
        enhancer = ProgressiveEnhancer(
            config=config,
            connectivity_detector=mock_connectivity_detector,
            capability_detector=mock_capability_detector
        )
        enhancer._update_feature = AsyncMock()
        return enhancer
    
    @pytest.mark.asyncio
    async def test_initialization(self, enhancer, config, mock_connectivity_detector):
        """Test that the enhancer initializes correctly."""
        assert enhancer.config is config
        assert isinstance(enhancer.strategy, DefaultStrategy)
        assert enhancer.connectivity_detector is mock_connectivity_detector
        assert enhancer._running is False
        
        # Check that a listener was added to the connectivity detector
        mock_connectivity_detector.add_listener.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_stop(self, enhancer, mock_connectivity_detector, mock_capability_detector):
        """Test starting and stopping the enhancer."""
        await enhancer.start()
        
        # Check that monitoring was started
        mock_connectivity_detector.start.assert_called_once()
        mock_capability_detector.detect_all.assert_called_once()
        assert enhancer._running is True
        
        # Check that features were initialized
        enhancer._update_feature.assert_called()
        
        # Reset the mock for testing stop
        enhancer._update_feature.reset_mock()
        
        await enhancer.stop()
        
        # Check that monitoring was stopped
        mock_connectivity_detector.stop.assert_called_once()
        assert enhancer._running is False
    
    @pytest.mark.asyncio
    async def test_feature_enhancers(self, enhancer):
        """Test registering and using feature enhancers."""
        # Set up a test enhancer function
        test_enhancer = MagicMock()
        
        # Register the enhancer
        enhancer.register_feature_enhancer("test-feature", test_enhancer)
        
        # Check that the enhancer was registered
        assert "test-feature" in enhancer._feature_enhancers
        assert enhancer._feature_enhancers["test-feature"] is test_enhancer
        
        # Simulate a feature update
        enhancer._feature_status["test-feature"] = {
            "level": "good",
            "config": {"mode": "good"},
            "enabled": True
        }
        
        # Manually call the enhancer
        test_enhancer.reset_mock()
        enhancer._on_connectivity_change(ConnectivityStatus.EXCELLENT)
        
        # Check that the enhancer was called
        assert enhancer._update_feature.called
        
        # Unregister the enhancer
        enhancer.unregister_feature_enhancer("test-feature")
        
        # Check that the enhancer was unregistered
        assert "test-feature" not in enhancer._feature_enhancers