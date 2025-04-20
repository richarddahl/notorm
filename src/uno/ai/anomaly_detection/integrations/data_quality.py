"""
Data quality integration for anomaly detection.

This module provides integration between the anomaly detection system
and data quality monitoring, detecting anomalies in data patterns,
completeness, consistency, and volume.
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


class DataQualityIntegration:
    """
    Integration between data quality monitoring and anomaly detection.

    This class provides utilities for monitoring data quality metrics
    and detecting anomalies in data patterns, completeness, consistency,
    and volume.
    """

    def __init__(
        self,
        engine: AnomalyDetectionEngine,
        data_source: str = "database",  # database, kafka, etc.
        tables: list[str] | None = None,  # Tables/collections to monitor
        metrics_mapping: Optional[Dict[str, str]] = None,
        poll_interval: int = 3600,  # seconds (1 hour)
        alert_handlers: Optional[list[callable]] = None,
        logger: logging.Logger | None = None,
        db_connection: str | None = None,
    ):
        """
        Initialize the data quality integration.

        Args:
            engine: The anomaly detection engine
            data_source: Name of the data source
            tables: List of tables/collections to monitor
            metrics_mapping: Mapping of data quality metrics to metric names
            poll_interval: Interval for polling metrics (seconds)
            alert_handlers: Handlers for alerts
            logger: Logger to use
            db_connection: Database connection string (for database source)
        """
        self.engine = engine
        self.data_source = data_source
        self.tables = tables or []
        self.metrics_mapping = metrics_mapping or {}
        self.poll_interval = poll_interval
        self.alert_handlers = alert_handlers or []
        self.logger = logger or logging.getLogger(__name__)
        self.db_connection = db_connection

        # Default metric mappings if not provided
        if not self.metrics_mapping:
            self._set_default_mappings()

        # State
        self.running = False
        self.task = None
        self.start_time = None
        self.data_clients = {}

    def _set_default_mappings(self) -> None:
        """Set default metric mappings based on data source."""
        self.metrics_mapping = {
            "null_ratio": "data_null_ratio",
            "unique_ratio": "data_unique_ratio",
            "invalid_ratio": "data_invalid_ratio",
            "schema_compliance": "data_schema_compliance",
            "distribution_mean": "data_distribution_mean",
            "distribution_std": "data_distribution_std",
            "volume": "data_record_count",
            "freshness": "data_freshness_seconds",
        }

    async def initialize(self) -> None:
        """Initialize the integration and set up detectors."""
        # Create client for data source
        await self._create_data_client()

        # Discover tables if not provided
        if not self.tables:
            await self._discover_tables()

        # Register data quality detectors
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

    async def _discover_tables(self) -> None:
        """Discover tables/collections to monitor."""
        if self.data_source == "database":
            await self._discover_db_tables()

    async def _discover_db_tables(self) -> None:
        """Discover database tables to monitor."""
        if "database" not in self.data_clients:
            return

        pool = self.data_clients["database"]

        try:
            async with pool.acquire() as conn:
                # Query for tables in the database
                results = await conn.fetch(
                    """
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """
                )

                # Add tables to the list
                self.tables = [row["table_name"] for row in results]
                self.logger.info(f"Discovered {len(self.tables)} tables")

        except Exception as e:
            self.logger.error(f"Error discovering database tables: {e}")

    async def _register_detectors(self) -> None:
        """Register detectors for data quality metrics."""
        # For each table, register detectors for applicable metrics
        for table in self.tables:
            # Register data outlier detectors
            if "distribution_mean" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_OUTLIER,
                        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                        metric_name=f"{self.metrics_mapping['distribution_mean']}_{table}",
                    )
                )

            if "distribution_std" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_OUTLIER,
                        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                        metric_name=f"{self.metrics_mapping['distribution_std']}_{table}",
                    )
                )

            # Register data drift detectors
            if "schema_compliance" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_DRIFT,
                        strategy=DetectionStrategy.STATISTICAL_REGRESSION,
                        metric_name=f"{self.metrics_mapping['schema_compliance']}_{table}",
                    )
                )

            # Register data missing detectors
            if "null_ratio" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_MISSING,
                        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                        metric_name=f"{self.metrics_mapping['null_ratio']}_{table}",
                    )
                )

            # Register data inconsistency detectors
            if "invalid_ratio" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_INCONSISTENCY,
                        strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                        metric_name=f"{self.metrics_mapping['invalid_ratio']}_{table}",
                    )
                )

            if "unique_ratio" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_INCONSISTENCY,
                        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                        metric_name=f"{self.metrics_mapping['unique_ratio']}_{table}",
                    )
                )

            # Register data volume detectors
            if "volume" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_VOLUME,
                        strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                        metric_name=f"{self.metrics_mapping['volume']}_{table}",
                    )
                )

            # Register data freshness detector
            if "freshness" in self.metrics_mapping:
                await self.engine.register_detector(
                    await self._create_detector(
                        anomaly_type=AnomalyType.DATA_DRIFT,
                        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
                        metric_name=f"{self.metrics_mapping['freshness']}_{table}",
                    )
                )

    async def _create_detector(
        self, anomaly_type: AnomalyType, strategy: DetectionStrategy, metric_name: str
    ) -> Any:
        """
        Create a detector for a data quality metric.

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

        # Default to statistical for data quality
        return StatisticalDetector(
            anomaly_type=anomaly_type,
            strategy=DetectionStrategy.STATISTICAL_ZSCORE,
            metric_name=metric_name,
            logger=self.logger,
        )

    async def start(self) -> None:
        """Start the data quality monitoring integration."""
        if self.running:
            return

        self.running = True
        self.start_time = datetime.datetime.now()

        # Initialize the integration
        await self.initialize()

        # Start the monitoring task
        self.task = asyncio.create_task(self._monitoring_loop())

        self.logger.info("Data quality monitoring integration started")

    async def stop(self) -> None:
        """Stop the data quality monitoring integration."""
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

        self.logger.info("Data quality monitoring integration stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect data quality metrics
                quality_metrics = await self._collect_quality_metrics()

                if quality_metrics:
                    # Process metrics through the anomaly detection engine
                    for data_point in quality_metrics:
                        alerts = await self.engine.process_data_point(data_point)

                        # Handle alerts
                        for alert in alerts:
                            await self._handle_alert(alert)

            except Exception as e:
                self.logger.error(f"Error in data quality monitoring loop: {e}")

            # Wait for next poll
            await asyncio.sleep(self.poll_interval)

    async def _collect_quality_metrics(self) -> list[dict[str, Any]]:
        """
        Collect data quality metrics from the configured source.

        Returns:
            List of data quality metric data points
        """
        quality_metrics = []

        try:
            if self.data_source == "database":
                quality_metrics.extend(await self._collect_db_quality_metrics())
            elif self.data_source == "kafka":
                quality_metrics.extend(await self._collect_kafka_quality_metrics())

            # Add timestamp to data points
            timestamp = datetime.datetime.now()
            for data_point in quality_metrics:
                if "timestamp" not in data_point:
                    data_point["timestamp"] = timestamp

        except Exception as e:
            self.logger.error(f"Error collecting data quality metrics: {e}")

        return quality_metrics

    async def _collect_db_quality_metrics(self) -> list[dict[str, Any]]:
        """
        Collect data quality metrics from database.

        Returns:
            List of data quality metric data points
        """
        quality_metrics = []

        if "database" not in self.data_clients:
            return quality_metrics

        pool = self.data_clients["database"]

        try:
            async with pool.acquire() as conn:
                # For each table, collect quality metrics
                for table in self.tables:
                    # Collect record count
                    if "volume" in self.metrics_mapping:
                        try:
                            result = await conn.fetchval(
                                f"SELECT COUNT(*) FROM {table}"
                            )
                            quality_metrics.append(
                                {
                                    f"{self.metrics_mapping['volume']}_{table}": result,
                                    "entity_id": table,
                                    "entity_type": "table",
                                }
                            )
                        except Exception as e:
                            self.logger.error(
                                f"Error collecting record count for {table}: {e}"
                            )

                    # Collect null ratio for each column
                    if "null_ratio" in self.metrics_mapping:
                        try:
                            # Get column information
                            columns = await conn.fetch(
                                f"""
                                SELECT column_name FROM information_schema.columns 
                                WHERE table_name = '{table}' AND table_schema = 'public'
                            """
                            )

                            for column in columns:
                                column_name = column["column_name"]
                                # Calculate null ratio
                                total = await conn.fetchval(
                                    f"SELECT COUNT(*) FROM {table}"
                                )
                                nulls = await conn.fetchval(
                                    f"SELECT COUNT(*) FROM {table} WHERE {column_name} IS NULL"
                                )

                                if total > 0:
                                    null_ratio = nulls / total
                                    quality_metrics.append(
                                        {
                                            f"{self.metrics_mapping['null_ratio']}_{table}_{column_name}": null_ratio,
                                            "entity_id": f"{table}.{column_name}",
                                            "entity_type": "column",
                                        }
                                    )
                        except Exception as e:
                            self.logger.error(
                                f"Error collecting null ratio for {table}: {e}"
                            )

                    # Collect freshness (if table has timestamp column)
                    if "freshness" in self.metrics_mapping:
                        try:
                            # Check if table has timestamp columns
                            timestamp_columns = await conn.fetch(
                                f"""
                                SELECT column_name FROM information_schema.columns 
                                WHERE table_name = '{table}' AND table_schema = 'public' 
                                AND data_type IN ('timestamp', 'timestamp with time zone', 'date')
                            """
                            )

                            if timestamp_columns:
                                # Use the first timestamp column
                                ts_column = timestamp_columns[0]["column_name"]

                                # Calculate freshness in seconds
                                result = await conn.fetchval(
                                    f"""
                                    SELECT EXTRACT(EPOCH FROM (NOW() - MAX({ts_column})))
                                    FROM {table}
                                """
                                )

                                if result is not None:
                                    quality_metrics.append(
                                        {
                                            f"{self.metrics_mapping['freshness']}_{table}": float(
                                                result
                                            ),
                                            "entity_id": table,
                                            "entity_type": "table",
                                        }
                                    )
                        except Exception as e:
                            self.logger.error(
                                f"Error collecting freshness for {table}: {e}"
                            )

        except Exception as e:
            self.logger.error(f"Error collecting database quality metrics: {e}")

        return quality_metrics

    async def _collect_kafka_quality_metrics(self) -> list[dict[str, Any]]:
        """
        Collect data quality metrics from Kafka.

        Returns:
            List of data quality metric data points
        """
        quality_metrics = []

        if "kafka" not in self.data_clients:
            return quality_metrics

        try:
            # In a real implementation, you would analyze Kafka messages
            # This is a simplified placeholder implementation

            # Generate synthetic data for demonstration
            for topic in self.tables:  # In Kafka, topics are the "tables"
                # Message volume
                if "volume" in self.metrics_mapping:
                    quality_metrics.append(
                        {
                            f"{self.metrics_mapping['volume']}_{topic}": np.random.poisson(
                                1000
                            ),  # Average 1000 messages
                            "entity_id": topic,
                            "entity_type": "topic",
                        }
                    )

                # Schema compliance
                if "schema_compliance" in self.metrics_mapping:
                    quality_metrics.append(
                        {
                            f"{self.metrics_mapping['schema_compliance']}_{topic}": np.random.beta(
                                9, 1
                            ),  # High compliance
                            "entity_id": topic,
                            "entity_type": "topic",
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error collecting Kafka quality metrics: {e}")

        return quality_metrics

    async def _handle_alert(self, alert: AnomalyAlert) -> None:
        """
        Handle an anomaly alert.

        Args:
            alert: The anomaly alert
        """
        # Log the alert
        self.logger.warning(f"Data quality anomaly detected: {alert.description}")

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
            for metric_name, metric_data in historical_data.items():
                # Find detectors for this metric
                detector_ids = []
                for detector_id, detector in self.engine.detectors.items():
                    if detector.metric_name == metric_name:
                        detector_ids.append(detector_id)

                # Train each detector
                for detector_id in detector_ids:
                    self.logger.info(
                        f"Training detector {detector_id} on historical {metric_name} data"
                    )
                    await self.engine.train_detector(detector_id, metric_data)

            self.logger.info("Detector training completed")

        except Exception as e:
            self.logger.error(f"Error training detectors: {e}")

    async def _fetch_historical_data(self, days: int) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data quality metrics.

        Args:
            days: Number of days of historical data to fetch

        Returns:
            Dictionary mapping metric names to DataFrames of historical data
        """
        historical_data = {}

        try:
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=days)

            if self.data_source == "database":
                # If we have a database with historical metrics, we could fetch them
                # For now, we'll generate synthetic data
                historical_data = await self._generate_historical_metrics(
                    start_time, end_time
                )
            elif self.data_source == "kafka":
                # For Kafka, we'll also generate synthetic data
                historical_data = await self._generate_historical_metrics(
                    start_time, end_time
                )

        except Exception as e:
            self.logger.error(f"Error fetching historical data quality metrics: {e}")

        return historical_data

    async def _generate_historical_metrics(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Generate synthetic historical data quality metrics.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric names to DataFrames of historical data
        """
        historical_data = {}

        # For each table and metric, generate synthetic time series
        for table in self.tables:
            for metric_key, base_metric_name in self.metrics_mapping.items():
                metric_name = f"{base_metric_name}_{table}"

                # Create timestamps
                timestamps = pd.date_range(start=start_time, end=end_time, freq="1h")

                # Generate synthetic values based on metric type
                if metric_key == "null_ratio":
                    # Usually low, with occasional spikes
                    base = 0.05  # 5% nulls baseline
                    values = np.random.beta(1, 19, size=len(timestamps)) * 0.2 + base
                elif metric_key == "unique_ratio":
                    # Usually high, with occasional drops
                    base = 0.9  # 90% unique baseline
                    values = 1 - np.random.beta(1, 9, size=len(timestamps)) * 0.2
                elif metric_key == "invalid_ratio":
                    # Usually very low
                    base = 0.01  # 1% invalid baseline
                    values = np.random.beta(1, 99, size=len(timestamps)) * 0.05
                elif metric_key == "schema_compliance":
                    # Usually very high
                    base = 0.99  # 99% compliance baseline
                    values = 1 - np.random.beta(1, 99, size=len(timestamps)) * 0.05
                elif metric_key == "volume":
                    # Record counts with daily patterns
                    base = 1000  # Baseline record count
                    # Add day-of-week pattern
                    dow_pattern = np.array([1.0, 1.2, 1.1, 1.0, 0.9, 0.7, 0.6])
                    day_indices = np.array([t.dayofweek for t in timestamps])
                    day_factors = dow_pattern[day_indices]
                    # Add hour-of-day pattern
                    hod_pattern = 1 + 0.5 * np.sin(np.arange(24) * np.pi / 12)
                    hour_indices = np.array([t.hour for t in timestamps])
                    hour_factors = hod_pattern[hour_indices]
                    # Combine patterns with some noise
                    values = (
                        base
                        * day_factors
                        * hour_factors
                        * (1 + 0.1 * np.random.randn(len(timestamps)))
                    )
                elif metric_key == "freshness":
                    # Data freshness in seconds (lower is better)
                    base = 3600  # 1 hour baseline
                    values = np.random.exponential(base, size=len(timestamps))
                elif metric_key == "distribution_mean":
                    # Mean of a numeric column, with some trend and seasonality
                    base = 100  # Baseline mean
                    trend = np.linspace(0, 20, len(timestamps))  # Gradual increase
                    seasonality = 10 * np.sin(
                        np.arange(len(timestamps)) * 2 * np.pi / (24 * 7)
                    )  # Weekly pattern
                    values = (
                        base
                        + trend
                        + seasonality
                        + 5 * np.random.randn(len(timestamps))
                    )
                elif metric_key == "distribution_std":
                    # Standard deviation of a numeric column
                    base = 15  # Baseline std
                    values = base + 5 * np.random.randn(len(timestamps))
                    values = np.abs(values)  # Ensure positive
                else:
                    continue

                # Create DataFrame
                df = pd.DataFrame({"timestamp": timestamps, metric_name: values})
                df.set_index("timestamp", inplace=True)

                historical_data[metric_name] = df

        return historical_data
