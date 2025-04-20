"""
Core anomaly detection engine for Uno applications.

This module provides the central engine for anomaly detection, managing
detection strategies, alerting, and integration with monitoring systems.
"""

import asyncio
import datetime
import enum
import json
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set, Type, Union, cast

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from uno.core.errors.result import Result


class AnomalyType(str, enum.Enum):
    """Types of anomalies that can be detected."""

    # System-level anomalies
    SYSTEM_CPU = "system_cpu"
    SYSTEM_MEMORY = "system_memory"
    SYSTEM_DISK = "system_disk"
    SYSTEM_NETWORK = "system_network"
    SYSTEM_ERROR_RATE = "system_error_rate"
    SYSTEM_LATENCY = "system_latency"

    # User behavior anomalies
    USER_LOGIN_PATTERN = "user_login_pattern"
    USER_ACCESS_PATTERN = "user_access_pattern"
    USER_TRANSACTION_PATTERN = "user_transaction_pattern"
    USER_CONTENT_PATTERN = "user_content_pattern"

    # Data anomalies
    DATA_OUTLIER = "data_outlier"
    DATA_DRIFT = "data_drift"
    DATA_MISSING = "data_missing"
    DATA_INCONSISTENCY = "data_inconsistency"
    DATA_VOLUME = "data_volume"


class DetectionStrategy(str, enum.Enum):
    """Strategies for anomaly detection."""

    # Statistical approaches
    STATISTICAL_ZSCORE = "statistical_zscore"
    STATISTICAL_IQR = "statistical_iqr"
    STATISTICAL_MOVING_AVERAGE = "statistical_moving_average"
    STATISTICAL_REGRESSION = "statistical_regression"

    # Learning-based approaches
    LEARNING_ISOLATION_FOREST = "learning_isolation_forest"
    LEARNING_ONE_CLASS_SVM = "learning_one_class_svm"
    LEARNING_AUTOENCODER = "learning_autoencoder"
    LEARNING_DEEP_LSTM = "learning_deep_lstm"

    # Hybrid approaches
    HYBRID_ENSEMBLE = "hybrid_ensemble"
    HYBRID_ADAPTIVE = "hybrid_adaptive"


class AlertSeverity(str, enum.Enum):
    """Severity levels for anomaly alerts."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AnomalyAlert(BaseModel):
    """Model representing an anomaly alert."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.now)
    anomaly_type: AnomalyType
    detection_strategy: DetectionStrategy
    severity: AlertSeverity
    entity_id: str | None = None
    entity_type: str | None = None
    metric_name: str
    metric_value: float
    expected_range: Dict[str, float]
    deviation_factor: float
    description: str
    suggestion: str | None = None
    related_alerts: list[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def is_critical(self) -> bool:
        """Check if this is a critical alert."""
        return self.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage or API response."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "anomaly_type": self.anomaly_type.value,
            "detection_strategy": self.detection_strategy.value,
            "severity": self.severity.value,
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "expected_range": self.expected_range,
            "deviation_factor": self.deviation_factor,
            "description": self.description,
            "suggestion": self.suggestion,
            "related_alerts": self.related_alerts,
            "metadata": self.metadata,
            "is_critical": self.is_critical,
        }


class AnomalyDetector:
    """Base class for anomaly detectors."""

    def __init__(
        self,
        anomaly_type: AnomalyType,
        strategy: DetectionStrategy,
        metric_name: str,
        training_window: int = 30,  # days
        threshold: float = 2.0,  # standard deviations
        min_data_points: int = 100,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the anomaly detector.

        Args:
            anomaly_type: Type of anomaly to detect
            strategy: Detection strategy to use
            metric_name: Name of the metric to monitor
            training_window: Historical window for training in days
            threshold: Threshold for anomaly detection
            min_data_points: Minimum data points required for detection
            logger: Logger to use
        """
        self.anomaly_type = anomaly_type
        self.strategy = strategy
        self.metric_name = metric_name
        self.training_window = training_window
        self.threshold = threshold
        self.min_data_points = min_data_points
        self.logger = logger or logging.getLogger(__name__)

        # Internal state
        self.model: Any = None
        self.training_data: Optional[pd.DataFrame] = None
        self.is_trained = False

        # Metrics
        self.metrics = {
            "data_points_processed": 0,
            "anomalies_detected": 0,
            "last_training_time": None,
            "detection_time_ms": [],
        }

    async def train(self, data: pd.DataFrame) -> bool:
        """
        Train the detector on historical data.

        Args:
            data: Historical data for training

        Returns:
            True if training was successful, False otherwise
        """
        raise NotImplementedError("Subclasses must implement train method")

    async def detect(self, data_point: Dict[str, Any]) -> Optional[AnomalyAlert]:
        """
        Detect anomalies in a single data point.

        Args:
            data_point: The data point to check for anomalies

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        raise NotImplementedError("Subclasses must implement detect method")

    async def detect_batch(self, data: pd.DataFrame) -> list[AnomalyAlert]:
        """
        Detect anomalies in a batch of data points.

        Args:
            data: The data points to check for anomalies

        Returns:
            List of AnomalyAlert objects for detected anomalies
        """
        raise NotImplementedError("Subclasses must implement detect_batch method")

    def get_metrics(self) -> Dict[str, Any]:
        """Get detector metrics."""
        return {
            "anomaly_type": self.anomaly_type.value,
            "strategy": self.strategy.value,
            "metric_name": self.metric_name,
            "training_window": self.training_window,
            "threshold": self.threshold,
            "is_trained": self.is_trained,
            "data_points_processed": self.metrics["data_points_processed"],
            "anomalies_detected": self.metrics["anomalies_detected"],
            "last_training_time": self.metrics["last_training_time"],
            "avg_detection_time_ms": (
                np.mean(self.metrics["detection_time_ms"])
                if self.metrics["detection_time_ms"]
                else None
            ),
        }


class AnomalyDetectionEngine:
    """
    Engine for detecting anomalies in system metrics, user behavior, and data.

    This class provides a unified interface for anomaly detection using multiple
    detection strategies and alerting mechanisms.
    """

    def __init__(
        self,
        connection_string: str | None = None,
        alert_store_table: str = "anomaly_alerts",
        config_store_table: str = "anomaly_detector_config",
        enable_alerting: bool = True,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the anomaly detection engine.

        Args:
            connection_string: Database connection for alert storage
            alert_store_table: Table name for storing alerts
            config_store_table: Table name for storing detector configuration
            enable_alerting: Whether to enable alerting
            logger: Logger to use
        """
        self.connection_string = connection_string
        self.alert_store_table = alert_store_table
        self.config_store_table = config_store_table
        self.enable_alerting = enable_alerting
        self.logger = logger or logging.getLogger(__name__)

        # Initialize detectors registry
        self.detectors: Dict[str, AnomalyDetector] = {}

        # Alert handlers registry
        self.alert_handlers: list[callable] = []

        # State
        self.initialized = False
        self.pool = None

    async def initialize(self) -> None:
        """Initialize the detection engine and its resources."""
        if self.initialized:
            return

        if self.connection_string:
            import asyncpg

            # Initialize database connection pool
            self.pool = await asyncpg.create_pool(self.connection_string)

            # Create tables if they don't exist
            async with self.pool.acquire() as conn:
                # Create alerts table
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.alert_store_table} (
                        id TEXT PRIMARY KEY,
                        timestamp TIMESTAMP WITH TIME ZONE,
                        anomaly_type TEXT,
                        detection_strategy TEXT,
                        severity TEXT,
                        entity_id TEXT,
                        entity_type TEXT,
                        metric_name TEXT,
                        metric_value DOUBLE PRECISION,
                        expected_range JSONB,
                        deviation_factor DOUBLE PRECISION,
                        description TEXT,
                        suggestion TEXT,
                        related_alerts JSONB,
                        metadata JSONB,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create detector config table
                await conn.execute(
                    f"""
                    CREATE TABLE IF NOT EXISTS {self.config_store_table} (
                        id TEXT PRIMARY KEY,
                        anomaly_type TEXT,
                        strategy TEXT,
                        metric_name TEXT,
                        configuration JSONB,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    )
                """
                )

                # Create indexes
                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.alert_store_table}_timestamp 
                    ON {self.alert_store_table}(timestamp)
                """
                )

                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.alert_store_table}_anomaly_type 
                    ON {self.alert_store_table}(anomaly_type)
                """
                )

                await conn.execute(
                    f"""
                    CREATE INDEX IF NOT EXISTS idx_{self.alert_store_table}_severity 
                    ON {self.alert_store_table}(severity)
                """
                )

        # Load detector configurations
        if self.pool:
            await self._load_detector_configs()

        self.initialized = True

    async def close(self) -> None:
        """Close the engine and release its resources."""
        if self.pool:
            await self.pool.close()
            self.pool = None
        self.initialized = False

    @asynccontextmanager
    async def session(self):
        """Create a session for anomaly detection operations."""
        if not self.initialized:
            await self.initialize()

        try:
            yield self
        finally:
            pass  # No session-specific cleanup needed yet

    async def register_detector(
        self, detector: AnomalyDetector, save_config: bool = True
    ) -> str:
        """
        Register an anomaly detector with the engine.

        Args:
            detector: The detector to register
            save_config: Whether to save the detector configuration to the database

        Returns:
            Detector ID
        """
        if not self.initialized:
            await self.initialize()

        # Generate a detector ID
        detector_id = f"{detector.anomaly_type.value}_{detector.strategy.value}_{detector.metric_name}"

        # Register the detector
        self.detectors[detector_id] = detector

        # Save configuration to the database if requested
        if save_config and self.pool:
            config = {
                "training_window": detector.training_window,
                "threshold": detector.threshold,
                "min_data_points": detector.min_data_points,
                "params": getattr(detector, "params", {}),
            }

            async with self.pool.acquire() as conn:
                await conn.execute(
                    f"""
                    INSERT INTO {self.config_store_table}
                    (id, anomaly_type, strategy, metric_name, configuration, enabled)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (id) DO UPDATE
                    SET configuration = $5, updated_at = CURRENT_TIMESTAMP
                """,
                    detector_id,
                    detector.anomaly_type.value,
                    detector.strategy.value,
                    detector.metric_name,
                    json.dumps(config),
                    True,
                )

        self.logger.info(f"Registered detector: {detector_id}")
        return detector_id

    async def unregister_detector(self, detector_id: str) -> bool:
        """
        Unregister an anomaly detector.

        Args:
            detector_id: The ID of the detector to unregister

        Returns:
            True if the detector was unregistered, False otherwise
        """
        if detector_id in self.detectors:
            # Remove from registry
            del self.detectors[detector_id]

            # Disable in database if connected
            if self.pool:
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        UPDATE {self.config_store_table}
                        SET enabled = FALSE, updated_at = CURRENT_TIMESTAMP
                        WHERE id = $1
                    """,
                        detector_id,
                    )

            self.logger.info(f"Unregistered detector: {detector_id}")
            return True

        return False

    async def register_alert_handler(self, handler: callable) -> None:
        """
        Register a handler for anomaly alerts.

        Args:
            handler: Function to handle alerts, should accept an AnomalyAlert
        """
        self.alert_handlers.append(handler)

    async def process_data_point(
        self,
        data_point: Dict[str, Any],
        detector_types: Optional[list[AnomalyType]] = None,
    ) -> list[AnomalyAlert]:
        """
        Process a single data point through all relevant detectors.

        Args:
            data_point: The data point to process
            detector_types: Optional list of anomaly types to use

        Returns:
            List of detected anomaly alerts
        """
        if not self.initialized:
            await self.initialize()

        alerts = []
        tasks = []

        # Only use detectors of the specified types if provided
        filtered_detectors = {}
        if detector_types:
            for detector_id, detector in self.detectors.items():
                if detector.anomaly_type in detector_types:
                    filtered_detectors[detector_id] = detector
        else:
            filtered_detectors = self.detectors

        # Create detection tasks for each detector
        for detector_id, detector in filtered_detectors.items():
            if detector.metric_name in data_point:
                tasks.append(detector.detect(data_point))

        # Run detection tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error during anomaly detection: {result}")
                elif result is not None:
                    # We have an alert
                    alerts.append(result)
                    await self._handle_alert(result)

        return alerts

    async def process_batch(
        self, data: pd.DataFrame, detector_types: Optional[list[AnomalyType]] = None
    ) -> list[AnomalyAlert]:
        """
        Process a batch of data through all relevant detectors.

        Args:
            data: DataFrame with data points to process
            detector_types: Optional list of anomaly types to use

        Returns:
            List of detected anomaly alerts
        """
        if not self.initialized:
            await self.initialize()

        alerts = []
        tasks = []

        # Only use detectors of the specified types if provided
        filtered_detectors = {}
        if detector_types:
            for detector_id, detector in self.detectors.items():
                if detector.anomaly_type in detector_types:
                    filtered_detectors[detector_id] = detector
        else:
            filtered_detectors = self.detectors

        # Create detection tasks for each detector
        for detector_id, detector in filtered_detectors.items():
            if detector.metric_name in data.columns:
                tasks.append(detector.detect_batch(data))

        # Run detection tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error during batch anomaly detection: {result}")
                elif result:
                    # We have alerts
                    for alert in result:
                        alerts.append(alert)
                        await self._handle_alert(alert)

        return alerts

    async def train_detector(self, detector_id: str, data: pd.DataFrame) -> bool:
        """
        Train a specific detector with historical data.

        Args:
            detector_id: ID of the detector to train
            data: Historical data for training

        Returns:
            True if training was successful, False otherwise
        """
        if not self.initialized:
            await self.initialize()

        if detector_id not in self.detectors:
            self.logger.error(f"Detector not found: {detector_id}")
            return False

        detector = self.detectors[detector_id]
        return await detector.train(data)

    async def train_all_detectors(
        self, data: Dict[str, pd.DataFrame]
    ) -> Dict[str, bool]:
        """
        Train all detectors with historical data.

        Args:
            data: Dictionary mapping metric names to historical data

        Returns:
            Dictionary mapping detector IDs to training results
        """
        if not self.initialized:
            await self.initialize()

        results = {}
        tasks = []
        detector_ids = []

        # Create training tasks
        for detector_id, detector in self.detectors.items():
            if detector.metric_name in data:
                detector_ids.append(detector_id)
                tasks.append(detector.train(data[detector.metric_name]))

        # Run training tasks concurrently
        if tasks:
            training_results = await asyncio.gather(*tasks, return_exceptions=True)

            # Process results
            for i, result in enumerate(training_results):
                detector_id = detector_ids[i]
                if isinstance(result, Exception):
                    self.logger.error(
                        f"Error training detector {detector_id}: {result}"
                    )
                    results[detector_id] = False
                else:
                    results[detector_id] = result

        return results

    async def get_alerts(
        self,
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        anomaly_types: Optional[list[AnomalyType]] = None,
        severities: Optional[list[AlertSeverity]] = None,
        entity_id: str | None = None,
        entity_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnomalyAlert]:
        """
        Get anomaly alerts from the alert store.

        Args:
            start_time: Start time for alert retrieval
            end_time: End time for alert retrieval
            anomaly_types: Filter by anomaly types
            severities: Filter by severity levels
            entity_id: Filter by entity ID
            entity_type: Filter by entity type
            limit: Maximum number of alerts to retrieve
            offset: Offset for pagination

        Returns:
            List of AnomalyAlert objects
        """
        if not self.initialized:
            await self.initialize()

        if not self.pool:
            self.logger.warning("No database connection for retrieving alerts")
            return []

        # Build query
        query = f"SELECT * FROM {self.alert_store_table} WHERE 1=1"
        params = []
        param_index = 1

        # Add filters
        if start_time:
            query += f" AND timestamp >= ${param_index}"
            params.append(start_time)
            param_index += 1

        if end_time:
            query += f" AND timestamp <= ${param_index}"
            params.append(end_time)
            param_index += 1

        if anomaly_types:
            placeholders = ", ".join(
                [f"${param_index + i}" for i in range(len(anomaly_types))]
            )
            query += f" AND anomaly_type IN ({placeholders})"
            params.extend([at.value for at in anomaly_types])
            param_index += len(anomaly_types)

        if severities:
            placeholders = ", ".join(
                [f"${param_index + i}" for i in range(len(severities))]
            )
            query += f" AND severity IN ({placeholders})"
            params.extend([s.value for s in severities])
            param_index += len(severities)

        if entity_id:
            query += f" AND entity_id = ${param_index}"
            params.append(entity_id)
            param_index += 1

        if entity_type:
            query += f" AND entity_type = ${param_index}"
            params.append(entity_type)
            param_index += 1

        # Add ordering and pagination
        query += f" ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"

        # Execute query
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)

            # Convert to AnomalyAlert objects
            alerts = []
            for row in rows:
                alerts.append(
                    AnomalyAlert(
                        id=row["id"],
                        timestamp=row["timestamp"],
                        anomaly_type=AnomalyType(row["anomaly_type"]),
                        detection_strategy=DetectionStrategy(row["detection_strategy"]),
                        severity=AlertSeverity(row["severity"]),
                        entity_id=row["entity_id"],
                        entity_type=row["entity_type"],
                        metric_name=row["metric_name"],
                        metric_value=row["metric_value"],
                        expected_range=row["expected_range"],
                        deviation_factor=row["deviation_factor"],
                        description=row["description"],
                        suggestion=row["suggestion"],
                        related_alerts=row["related_alerts"],
                        metadata=row["metadata"],
                    )
                )

            return alerts

    async def get_detector_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get metrics for all registered detectors.

        Returns:
            Dictionary mapping detector IDs to their metrics
        """
        return {
            detector_id: detector.get_metrics()
            for detector_id, detector in self.detectors.items()
        }

    async def _handle_alert(self, alert: AnomalyAlert) -> None:
        """
        Handle an anomaly alert by storing it and notifying handlers.

        Args:
            alert: The anomaly alert to handle
        """
        # Store the alert if we have a database connection
        if self.pool:
            try:
                async with self.pool.acquire() as conn:
                    await conn.execute(
                        f"""
                        INSERT INTO {self.alert_store_table}
                        (id, timestamp, anomaly_type, detection_strategy, severity, 
                         entity_id, entity_type, metric_name, metric_value, expected_range,
                         deviation_factor, description, suggestion, related_alerts, metadata)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                    """,
                        alert.id,
                        alert.timestamp,
                        alert.anomaly_type.value,
                        alert.detection_strategy.value,
                        alert.severity.value,
                        alert.entity_id,
                        alert.entity_type,
                        alert.metric_name,
                        alert.metric_value,
                        json.dumps(alert.expected_range),
                        alert.deviation_factor,
                        alert.description,
                        alert.suggestion,
                        json.dumps(alert.related_alerts),
                        json.dumps(alert.metadata),
                    )
            except Exception as e:
                self.logger.error(f"Error storing alert: {e}")

        # Notify alert handlers if alerting is enabled
        if self.enable_alerting:
            for handler in self.alert_handlers:
                try:
                    await handler(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert handler: {e}")

    async def _load_detector_configs(self) -> None:
        """Load detector configurations from the database."""
        if not self.pool:
            return

        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    f"""
                    SELECT * FROM {self.config_store_table}
                    WHERE enabled = TRUE
                """
                )

                from uno.ai.anomaly_detection.detectors import (
                    StatisticalDetector,
                    LearningBasedDetector,
                    HybridDetector,
                )

                # Create detectors from configurations
                for row in rows:
                    anomaly_type = AnomalyType(row["anomaly_type"])
                    strategy = DetectionStrategy(row["strategy"])
                    metric_name = row["metric_name"]
                    config = row["configuration"]

                    # Create the appropriate detector
                    if strategy.value.startswith("statistical_"):
                        detector = StatisticalDetector(
                            anomaly_type=anomaly_type,
                            strategy=strategy,
                            metric_name=metric_name,
                            **config,
                        )
                    elif strategy.value.startswith("learning_"):
                        detector = LearningBasedDetector(
                            anomaly_type=anomaly_type,
                            strategy=strategy,
                            metric_name=metric_name,
                            **config,
                        )
                    elif strategy.value.startswith("hybrid_"):
                        detector = HybridDetector(
                            anomaly_type=anomaly_type,
                            strategy=strategy,
                            metric_name=metric_name,
                            **config,
                        )
                    else:
                        continue

                    # Register the detector without saving config
                    await self.register_detector(detector, save_config=False)

        except Exception as e:
            self.logger.error(f"Error loading detector configurations: {e}")
