"""
User behavior integration for anomaly detection.

This module provides integration between the anomaly detection system
and user behavior data sources such as login events, page views, and actions.
"""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import pandas as pd
import numpy as np

from uno.ai.anomaly_detection.engine import (
    AnomalyDetectionEngine,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)


class UserBehaviorIntegration:
    """
    Integration between user behavior monitoring and anomaly detection.

    This class provides utilities for monitoring user behavior metrics
    and detecting anomalies in user activity patterns.
    """

    def __init__(
        self,
        engine: AnomalyDetectionEngine,
        data_source: str = "database",  # database, kafka, logs, etc.
        poll_interval: int = 300,  # seconds (5 minutes)
        user_metrics_mapping: Optional[dict[str, str]] = None,
        alert_handlers: Optional[list[callable]] = None,
        logger: logging.Logger | None = None,
        db_connection: str | None = None,
    ):
        """
        Initialize the user behavior integration.

        Args:
            engine: The anomaly detection engine
            data_source: Name of the data source
            poll_interval: Interval for polling metrics (seconds)
            user_metrics_mapping: Mapping of user metrics to metric names
            alert_handlers: Handlers for alerts
            logger: Logger to use
            db_connection: Database connection string (for database source)
        """
        self.engine = engine
        self.data_source = data_source
        self.poll_interval = poll_interval
        self.user_metrics_mapping = user_metrics_mapping or {}
        self.alert_handlers = alert_handlers or []
        self.logger = logger or logging.getLogger(__name__)
        self.db_connection = db_connection

        # Default metric mappings if not provided
        if not self.user_metrics_mapping:
            self._set_default_mappings()

        # State
        self.running = False
        self.task = None
        self.start_time = None
        self.data_clients = {}

    def _set_default_mappings(self) -> None:
        """Set default metric mappings based on data source."""
        self.user_metrics_mapping = {
            "login_frequency": "user_login_frequency_per_day",
            "login_times": "user_login_hour_of_day",
            "login_locations": "user_login_location_code",
            "access_patterns": "user_access_pattern_hash",
            "transaction_amounts": "user_transaction_amount",
            "transaction_frequency": "user_transaction_frequency_per_day",
            "content_types": "user_content_interaction_type",
            "session_duration": "user_session_duration_minutes",
        }

    async def initialize(self) -> None:
        """Initialize the integration and set up detectors."""
        # Create client for data source
        await self._create_data_client()

        # Register user behavior detectors
        await self._register_detectors()

    async def _create_data_client(self) -> None:
        """Create client for the data source."""
        if self.data_source == "database":
            try:
                # Check if asyncpg is available
                import importlib.util

                if importlib.util.find_spec("asyncpg"):
                    import asyncpg

                    if self.db_connection:
                        pool = await asyncpg.create_pool(self.db_connection)
                        self.data_clients["database"] = pool
                        self.logger.info("Database client initialized")
                    else:
                        self.logger.warning("No database connection string provided")
            except ImportError:
                self.logger.warning("Asyncpg not available")

        elif self.data_source == "kafka":
            try:
                # Check if aiokafka is available
                import importlib.util

                if importlib.util.find_spec("aiokafka"):
                    import aiokafka

                    # In a real implementation, you would configure the Kafka consumer
                    self.data_clients["kafka"] = True
                    self.logger.info("Kafka client initialized")
            except ImportError:
                self.logger.warning("Aiokafka not available")

        elif self.data_source == "logs":
            # In a real implementation, you would set up log parsing
            self.data_clients["logs"] = True
            self.logger.info("Log client initialized")

    async def _register_detectors(self) -> None:
        """Register detectors for user behavior metrics."""
        # Register login pattern detector
        if "login_frequency" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_LOGIN_PATTERN,
                    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    metric_name=self.user_metrics_mapping["login_frequency"],
                )
            )

        if "login_times" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_LOGIN_PATTERN,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.user_metrics_mapping["login_times"],
                )
            )

        if "login_locations" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_LOGIN_PATTERN,
                    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    metric_name=self.user_metrics_mapping["login_locations"],
                )
            )

        # Register access pattern detector
        if "access_patterns" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_ACCESS_PATTERN,
                    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    metric_name=self.user_metrics_mapping["access_patterns"],
                )
            )

        # Register transaction pattern detector
        if "transaction_amounts" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_TRANSACTION_PATTERN,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.user_metrics_mapping["transaction_amounts"],
                )
            )

        if "transaction_frequency" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_TRANSACTION_PATTERN,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.user_metrics_mapping["transaction_frequency"],
                )
            )

        # Register content pattern detector
        if "content_types" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_CONTENT_PATTERN,
                    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    metric_name=self.user_metrics_mapping["content_types"],
                )
            )

        if "session_duration" in self.user_metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.USER_ACCESS_PATTERN,
                    strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                    metric_name=self.user_metrics_mapping["session_duration"],
                )
            )

    async def _create_detector(
        self, anomaly_type: AnomalyType, strategy: DetectionStrategy, metric_name: str
    ) -> Any:
        """
        Create a detector for a user behavior metric.

        Args:
            anomaly_type: Type of anomaly to detect
            strategy: Detection strategy to use
            metric_name: Name of the metric to monitor

        Returns:
            Detector instance
        """
        from uno.ai.anomaly_detection.detectors import (
            StatisticalDetector,
            LearningBasedDetector,
            HybridDetector,
        )

        if strategy.value.startswith("statistical_"):
            return StatisticalDetector(
                anomaly_type=anomaly_type,
                strategy=strategy,
                metric_name=metric_name,
                logger=self.logger,
            )
        elif strategy.value.startswith("learning_"):
            return LearningBasedDetector(
                anomaly_type=anomaly_type,
                strategy=strategy,
                metric_name=metric_name,
                logger=self.logger,
            )
        elif strategy.value.startswith("hybrid_"):
            return HybridDetector(
                anomaly_type=anomaly_type,
                strategy=strategy,
                metric_name=metric_name,
                logger=self.logger,
            )

        # Default to learning-based for user behavior
        return LearningBasedDetector(
            anomaly_type=anomaly_type,
            strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
            metric_name=metric_name,
            logger=self.logger,
        )

    async def start(self) -> None:
        """Start the user behavior monitoring integration."""
        if self.running:
            return

        self.running = True
        self.start_time = datetime.datetime.now()

        # Initialize the integration
        await self.initialize()

        # Start the monitoring task
        self.task = asyncio.create_task(self._monitoring_loop())

        self.logger.info("User behavior monitoring integration started")

    async def stop(self) -> None:
        """Stop the user behavior monitoring integration."""
        if not self.running:
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None

        # Close data clients
        if "database" in self.data_clients:
            await self.data_clients["database"].close()

        self.logger.info("User behavior monitoring integration stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect user behavior data
                user_data = await self._collect_user_data()

                if user_data:
                    # Process user data through the anomaly detection engine
                    for data_point in user_data:
                        alerts = await self.engine.process_data_point(data_point)

                        # Handle alerts
                        for alert in alerts:
                            await self._handle_alert(alert)

            except Exception as e:
                self.logger.error(f"Error in user behavior monitoring loop: {e}")

            # Wait for next poll
            await asyncio.sleep(self.poll_interval)

    async def _collect_user_data(self) -> list[dict[str, Any]]:
        """
        Collect user behavior data from the configured source.

        Returns:
            List of user behavior data points
        """
        user_data = []

        try:
            if self.data_source == "database":
                user_data.extend(await self._collect_db_user_data())
            elif self.data_source == "kafka":
                user_data.extend(await self._collect_kafka_user_data())
            elif self.data_source == "logs":
                user_data.extend(await self._collect_log_user_data())

            # Add timestamp to data points
            timestamp = datetime.datetime.now()
            for data_point in user_data:
                if "timestamp" not in data_point:
                    data_point["timestamp"] = timestamp

        except Exception as e:
            self.logger.error(f"Error collecting user behavior data: {e}")

        return user_data

    async def _collect_db_user_data(self) -> list[dict[str, Any]]:
        """
        Collect user behavior data from database.

        Returns:
            List of user behavior data points
        """
        user_data = []

        if "database" not in self.data_clients:
            return user_data

        pool = self.data_clients["database"]

        try:
            async with pool.acquire() as conn:
                # In a real implementation, you would query the database
                # for user behavior data
                # This is a simplified placeholder implementation

                # Example: Query login frequency
                if "login_frequency" in self.user_metrics_mapping:
                    # In a real implementation, this would be a real SQL query
                    # results = await conn.fetch("SELECT user_id, COUNT(*) as login_count FROM user_logins WHERE timestamp > NOW() - INTERVAL '1 day' GROUP BY user_id")

                    # Generate synthetic data for demonstration
                    for i in range(5):
                        user_data.append(
                            {
                                self.user_metrics_mapping[
                                    "login_frequency"
                                ]: np.random.poisson(
                                    3
                                ),  # Average 3 logins per day
                                "entity_id": f"user_{i}",
                                "entity_type": "user",
                            }
                        )

                # Example: Query transaction amounts
                if "transaction_amounts" in self.user_metrics_mapping:
                    # In a real implementation, this would be a real SQL query
                    # results = await conn.fetch("SELECT user_id, amount FROM user_transactions WHERE timestamp > NOW() - INTERVAL '1 day'")

                    # Generate synthetic data for demonstration
                    for i in range(5):
                        for _ in range(
                            np.random.poisson(2)
                        ):  # Average 2 transactions per user
                            user_data.append(
                                {
                                    self.user_metrics_mapping[
                                        "transaction_amounts"
                                    ]: np.random.exponential(
                                        100
                                    ),  # Average $100 transactions
                                    "entity_id": f"user_{i}",
                                    "entity_type": "user",
                                }
                            )

        except Exception as e:
            self.logger.error(f"Error collecting user behavior data from database: {e}")

        return user_data

    async def _collect_kafka_user_data(self) -> list[dict[str, Any]]:
        """
        Collect user behavior data from Kafka.

        Returns:
            List of user behavior data points
        """
        user_data = []

        if "kafka" not in self.data_clients:
            return user_data

        try:
            # In a real implementation, you would consume messages from Kafka
            # This is a simplified placeholder implementation

            # Generate synthetic data for demonstration
            for i in range(3):
                user_data.append(
                    {
                        self.user_metrics_mapping["access_patterns"]: hash(
                            f"pattern_{np.random.randint(1, 10)}"
                        ),
                        "entity_id": f"user_{np.random.randint(1, 20)}",
                        "entity_type": "user",
                    }
                )

        except Exception as e:
            self.logger.error(f"Error collecting user behavior data from Kafka: {e}")

        return user_data

    async def _collect_log_user_data(self) -> list[dict[str, Any]]:
        """
        Collect user behavior data from logs.

        Returns:
            List of user behavior data points
        """
        user_data = []

        if "logs" not in self.data_clients:
            return user_data

        try:
            # In a real implementation, you would parse logs
            # This is a simplified placeholder implementation

            # Generate synthetic data for demonstration
            if "session_duration" in self.user_metrics_mapping:
                for i in range(4):
                    user_data.append(
                        {
                            self.user_metrics_mapping[
                                "session_duration"
                            ]: np.random.exponential(
                                15
                            ),  # Average 15 minutes
                            "entity_id": f"user_{np.random.randint(1, 20)}",
                            "entity_type": "user",
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error collecting user behavior data from logs: {e}")

        return user_data

    async def _handle_alert(self, alert: AnomalyAlert) -> None:
        """
        Handle an anomaly alert.

        Args:
            alert: The anomaly alert
        """
        # Log the alert
        self.logger.warning(f"User behavior anomaly detected: {alert.description}")

        # Call registered alert handlers
        for handler in self.alert_handlers:
            try:
                await handler(alert)
            except Exception as e:
                self.logger.error(f"Error in alert handler: {e}")

    async def train_detectors(self, days: int = 30) -> None:
        """
        Train detectors on historical data.

        Args:
            days: Number of days of historical data to use
        """
        try:
            # Fetch historical data
            historical_data = await self._fetch_historical_data(days)

            if not historical_data:
                self.logger.warning("No historical data available for training")
                return

            # Train detectors
            for metric_key, metric_data in historical_data.items():
                if metric_key in self.user_metrics_mapping:
                    metric_name = self.user_metrics_mapping[metric_key]

                    # Find detectors for this metric
                    detector_ids = []
                    for detector_id, detector in self.engine.detectors.items():
                        if detector.metric_name == metric_name:
                            detector_ids.append(detector_id)

                    # Train each detector
                    for detector_id in detector_ids:
                        self.logger.info(
                            f"Training detector {detector_id} on historical {metric_key} data"
                        )
                        await self.engine.train_detector(detector_id, metric_data)

            self.logger.info("Detector training completed")

        except Exception as e:
            self.logger.error(f"Error training detectors: {e}")

    async def _fetch_historical_data(self, days: int) -> dict[str, pd.DataFrame]:
        """
        Fetch historical user behavior data.

        Args:
            days: Number of days of historical data to fetch

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        historical_data = {}

        try:
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=days)

            if self.data_source == "database":
                historical_data = await self._fetch_db_historical(start_time, end_time)
            elif self.data_source == "kafka":
                # For Kafka, we might not have historical data, so we'll generate synthetic data
                historical_data = self._generate_synthetic_historical(
                    start_time, end_time
                )
            elif self.data_source == "logs":
                # For logs, we might parse historical log files
                historical_data = self._generate_synthetic_historical(
                    start_time, end_time
                )

        except Exception as e:
            self.logger.error(f"Error fetching historical user behavior data: {e}")

        return historical_data

    async def _fetch_db_historical(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> dict[str, pd.DataFrame]:
        """
        Fetch historical data from database.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        historical_data = {}

        if "database" not in self.data_clients:
            return historical_data

        pool = self.data_clients["database"]

        try:
            async with pool.acquire() as conn:
                # In a real implementation, you would query the database
                # for historical user behavior data
                # This is a simplified placeholder implementation

                # For now, we'll generate synthetic data
                historical_data = self._generate_synthetic_historical(
                    start_time, end_time
                )

        except Exception as e:
            self.logger.error(
                f"Error fetching historical user behavior data from database: {e}"
            )

        return historical_data

    def _generate_synthetic_historical(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> dict[str, pd.DataFrame]:
        """
        Generate synthetic historical data for user behavior.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        historical_data = {}

        # Generate synthetic data for each metric
        for metric_key in self.user_metrics_mapping:
            # Create synthetic time series
            timestamps = pd.date_range(start=start_time, end=end_time, freq="1h")

            if metric_key == "login_frequency":
                # Daily login frequency per user
                values = np.random.poisson(
                    3, size=len(timestamps)
                )  # Average 3 logins per day
            elif metric_key == "login_times":
                # Hour of day (0-23)
                values = np.random.normal(12, 4, size=len(timestamps)).astype(int) % 24
            elif metric_key == "login_locations":
                # Location codes (e.g., country codes)
                locations = [1, 2, 3, 4, 5]  # Sample location codes
                values = np.random.choice(locations, size=len(timestamps))
            elif metric_key == "access_patterns":
                # Hash values of access patterns
                patterns = [hash(f"pattern_{i}") for i in range(1, 6)]
                values = np.random.choice(patterns, size=len(timestamps))
            elif metric_key == "transaction_amounts":
                # Transaction amounts
                values = np.random.exponential(
                    100, size=len(timestamps)
                )  # Average $100
            elif metric_key == "transaction_frequency":
                # Daily transaction frequency per user
                values = np.random.poisson(
                    2, size=len(timestamps)
                )  # Average 2 transactions per day
            elif metric_key == "content_types":
                # Content type IDs
                content_types = [1, 2, 3, 4, 5]  # Sample content type IDs
                values = np.random.choice(content_types, size=len(timestamps))
            elif metric_key == "session_duration":
                # Session duration in minutes
                values = np.random.exponential(
                    15, size=len(timestamps)
                )  # Average 15 minutes
            else:
                continue

            # Create DataFrame
            df = pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "user_id": np.random.choice(
                        [f"user_{i}" for i in range(1, 21)], size=len(timestamps)
                    ),
                    self.user_metrics_mapping[metric_key]: values,
                }
            )
            df.set_index("timestamp", inplace=True)

            historical_data[metric_key] = df

        return historical_data
