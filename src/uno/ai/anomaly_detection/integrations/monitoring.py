"""
System monitoring integration for anomaly detection.

This module provides integration between the anomaly detection system
and system monitoring data sources such as metrics, logs, and traces.
"""

import asyncio
import datetime
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import pandas as pd

from uno.ai.anomaly_detection.engine import (
    AnomalyDetectionEngine,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)


class SystemMonitorIntegration:
    """
    Integration between system monitoring and anomaly detection.

    This class provides utilities for monitoring system metrics
    and detecting anomalies in system behavior.
    """

    def __init__(
        self,
        engine: AnomalyDetectionEngine,
        metrics_source: str = "prometheus",  # prometheus, datadog, cloudwatch, etc.
        poll_interval: int = 60,  # seconds
        metrics_mapping: Optional[Dict[str, str]] = None,
        alert_handlers: Optional[list[callable]] = None,
        logger: logging.Logger | None = None,
    ):
        """
        Initialize the system monitor integration.

        Args:
            engine: The anomaly detection engine
            metrics_source: Name of the metrics source
            poll_interval: Interval for polling metrics (seconds)
            metrics_mapping: Mapping of system metrics to metric names
            alert_handlers: Handlers for alerts
            logger: Logger to use
        """
        self.engine = engine
        self.metrics_source = metrics_source
        self.poll_interval = poll_interval
        self.metrics_mapping = metrics_mapping or {}
        self.alert_handlers = alert_handlers or []
        self.logger = logger or logging.getLogger(__name__)

        # Default metric mappings if not provided
        if not self.metrics_mapping:
            self._set_default_mappings()

        # State
        self.running = False
        self.task = None
        self.start_time = None
        self.metrics_clients = {}

    def _set_default_mappings(self) -> None:
        """Set default metric mappings based on metrics source."""
        if self.metrics_source == "prometheus":
            self.metrics_mapping = {
                "cpu_usage": "system_cpu_usage_ratio",
                "memory_usage": "system_memory_usage_bytes",
                "disk_usage": "system_disk_usage_ratio",
                "network_traffic": "system_network_traffic_bytes",
                "error_rate": "system_error_rate_per_minute",
                "latency": "system_request_latency_seconds",
            }
        elif self.metrics_source == "datadog":
            self.metrics_mapping = {
                "cpu_usage": "system.cpu.user",
                "memory_usage": "system.mem.used",
                "disk_usage": "system.disk.in_use",
                "network_traffic": "system.net.bytes_sent",
                "error_rate": "app.errors.count",
                "latency": "app.request.latency",
            }
        elif self.metrics_source == "cloudwatch":
            self.metrics_mapping = {
                "cpu_usage": "CPUUtilization",
                "memory_usage": "MemoryUtilization",
                "disk_usage": "DiskUtilization",
                "network_traffic": "NetworkIn",
                "error_rate": "ErrorCount",
                "latency": "Latency",
            }

    async def initialize(self) -> None:
        """Initialize the integration and set up detectors."""
        # Create client for metrics source
        await self._create_metrics_client()

        # Register system metric detectors
        await self._register_detectors()

    async def _create_metrics_client(self) -> None:
        """Create client for the metrics source."""
        if self.metrics_source == "prometheus":
            try:
                # Check if prometheus client is available
                import importlib.util

                if importlib.util.find_spec("prometheus_client"):
                    from prometheus_client import REGISTRY, Counter, Gauge, Histogram

                    self.metrics_clients["prometheus"] = REGISTRY
                    self.logger.info("Prometheus client initialized")
            except ImportError:
                self.logger.warning("Prometheus client not available")

        elif self.metrics_source == "datadog":
            try:
                # Check if datadog client is available
                import importlib.util

                if importlib.util.find_spec("datadog"):
                    import datadog

                    self.metrics_clients["datadog"] = datadog
                    self.logger.info("Datadog client initialized")
            except ImportError:
                self.logger.warning("Datadog client not available")

        elif self.metrics_source == "cloudwatch":
            try:
                # Check if boto3 client is available
                import importlib.util

                if importlib.util.find_spec("boto3"):
                    import boto3

                    self.metrics_clients["cloudwatch"] = boto3.client("cloudwatch")
                    self.logger.info("CloudWatch client initialized")
            except ImportError:
                self.logger.warning("Boto3 client not available")

    async def _register_detectors(self) -> None:
        """Register detectors for system metrics."""
        # Register CPU detector
        if "cpu_usage" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_CPU,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.metrics_mapping["cpu_usage"],
                )
            )

        # Register memory detector
        if "memory_usage" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_MEMORY,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.metrics_mapping["memory_usage"],
                )
            )

        # Register disk detector
        if "disk_usage" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_DISK,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.metrics_mapping["disk_usage"],
                )
            )

        # Register network detector
        if "network_traffic" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_NETWORK,
                    strategy=DetectionStrategy.STATISTICAL_MOVING_AVERAGE,
                    metric_name=self.metrics_mapping["network_traffic"],
                )
            )

        # Register error rate detector
        if "error_rate" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_ERROR_RATE,
                    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
                    metric_name=self.metrics_mapping["error_rate"],
                )
            )

        # Register latency detector
        if "latency" in self.metrics_mapping:
            await self.engine.register_detector(
                await self._create_detector(
                    anomaly_type=AnomalyType.SYSTEM_LATENCY,
                    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    metric_name=self.metrics_mapping["latency"],
                )
            )

    async def _create_detector(
        self, anomaly_type: AnomalyType, strategy: DetectionStrategy, metric_name: str
    ) -> Any:
        """
        Create a detector for a system metric.

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

        # Default to statistical
        return StatisticalDetector(
            anomaly_type=anomaly_type,
            strategy=DetectionStrategy.STATISTICAL_ZSCORE,
            metric_name=metric_name,
            logger=self.logger,
        )

    async def start(self) -> None:
        """Start the monitoring integration."""
        if self.running:
            return

        self.running = True
        self.start_time = datetime.datetime.now()

        # Initialize the integration
        await self.initialize()

        # Start the monitoring task
        self.task = asyncio.create_task(self._monitoring_loop())

        self.logger.info("System monitoring integration started")

    async def stop(self) -> None:
        """Stop the monitoring integration."""
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

        self.logger.info("System monitoring integration stopped")

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()

                if metrics:
                    # Process metrics through the anomaly detection engine
                    for data_point in metrics:
                        alerts = await self.engine.process_data_point(data_point)

                        # Handle alerts
                        for alert in alerts:
                            await self._handle_alert(alert)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")

            # Wait for next poll
            await asyncio.sleep(self.poll_interval)

    async def _collect_metrics(self) -> list[dict[str, Any]]:
        """
        Collect metrics from the configured source.

        Returns:
            List of metric data points
        """
        metrics = []

        try:
            if self.metrics_source == "prometheus":
                metrics.extend(await self._collect_prometheus_metrics())
            elif self.metrics_source == "datadog":
                metrics.extend(await self._collect_datadog_metrics())
            elif self.metrics_source == "cloudwatch":
                metrics.extend(await self._collect_cloudwatch_metrics())

            # Add timestamp to metrics
            timestamp = datetime.datetime.now()
            for metric in metrics:
                if "timestamp" not in metric:
                    metric["timestamp"] = timestamp

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")

        return metrics

    async def _collect_prometheus_metrics(self) -> list[dict[str, Any]]:
        """
        Collect metrics from Prometheus.

        Returns:
            List of metric data points
        """
        metrics = []

        if "prometheus" not in self.metrics_clients:
            return metrics

        try:
            # In a real implementation, you would use the Prometheus HTTP API
            # or parse metrics from the /metrics endpoint
            # This is a simplified placeholder implementation

            # Example: Create a dummy metric data point
            for metric_key, metric_name in self.metrics_mapping.items():
                if metric_key == "cpu_usage":
                    metrics.append(
                        {
                            metric_name: 0.35,  # 35% CPU usage
                            "entity_id": "system",
                            "entity_type": "instance",
                        }
                    )
                elif metric_key == "memory_usage":
                    metrics.append(
                        {
                            metric_name: 2.5 * 1024 * 1024 * 1024,  # 2.5GB memory usage
                            "entity_id": "system",
                            "entity_type": "instance",
                        }
                    )
                elif metric_key == "disk_usage":
                    metrics.append(
                        {
                            metric_name: 0.65,  # 65% disk usage
                            "entity_id": "system",
                            "entity_type": "instance",
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error collecting Prometheus metrics: {e}")

        return metrics

    async def _collect_datadog_metrics(self) -> list[dict[str, Any]]:
        """
        Collect metrics from Datadog.

        Returns:
            List of metric data points
        """
        metrics = []

        if "datadog" not in self.metrics_clients:
            return metrics

        try:
            # In a real implementation, you would use the Datadog API
            # to fetch metrics
            # This is a simplified placeholder implementation

            # Example: Create dummy metric data points
            for metric_key, metric_name in self.metrics_mapping.items():
                if metric_key == "error_rate":
                    metrics.append(
                        {
                            metric_name: 0.02,  # 2% error rate
                            "entity_id": "app",
                            "entity_type": "service",
                        }
                    )
                elif metric_key == "latency":
                    metrics.append(
                        {
                            metric_name: 0.12,  # 120ms latency
                            "entity_id": "app",
                            "entity_type": "service",
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error collecting Datadog metrics: {e}")

        return metrics

    async def _collect_cloudwatch_metrics(self) -> list[dict[str, Any]]:
        """
        Collect metrics from CloudWatch.

        Returns:
            List of metric data points
        """
        metrics = []

        if "cloudwatch" not in self.metrics_clients:
            return metrics

        try:
            # In a real implementation, you would use the CloudWatch API
            # to fetch metrics
            # This is a simplified placeholder implementation

            # Example: Create dummy metric data points
            for metric_key, metric_name in self.metrics_mapping.items():
                if metric_key == "network_traffic":
                    metrics.append(
                        {
                            metric_name: 1.2 * 1024 * 1024,  # 1.2MB network traffic
                            "entity_id": "system",
                            "entity_type": "instance",
                        }
                    )

        except Exception as e:
            self.logger.error(f"Error collecting CloudWatch metrics: {e}")

        return metrics

    async def _handle_alert(self, alert: AnomalyAlert) -> None:
        """
        Handle an anomaly alert.

        Args:
            alert: The anomaly alert
        """
        # Log the alert
        self.logger.warning(f"System anomaly detected: {alert.description}")

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
                if metric_key in self.metrics_mapping:
                    metric_name = self.metrics_mapping[metric_key]

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

    async def _fetch_historical_data(self, days: int) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical metric data.

        Args:
            days: Number of days of historical data to fetch

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        historical_data = {}

        try:
            end_time = datetime.datetime.now()
            start_time = end_time - datetime.timedelta(days=days)

            if self.metrics_source == "prometheus":
                historical_data = await self._fetch_prometheus_historical(
                    start_time, end_time
                )
            elif self.metrics_source == "datadog":
                historical_data = await self._fetch_datadog_historical(
                    start_time, end_time
                )
            elif self.metrics_source == "cloudwatch":
                historical_data = await self._fetch_cloudwatch_historical(
                    start_time, end_time
                )

        except Exception as e:
            self.logger.error(f"Error fetching historical data: {e}")

        return historical_data

    async def _fetch_prometheus_historical(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data from Prometheus.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        historical_data = {}

        # In a real implementation, you would use the Prometheus HTTP API
        # to fetch historical data for each metric
        # This is a simplified placeholder implementation

        # Generate synthetic data for each metric
        for metric_key in self.metrics_mapping:
            # Create synthetic time series
            timestamps = pd.date_range(start=start_time, end=end_time, freq="5min")

            if metric_key == "cpu_usage":
                values = 0.3 + 0.2 * np.random.random(
                    size=len(timestamps)
                )  # 30-50% CPU usage
            elif metric_key == "memory_usage":
                values = (
                    (2.0 + 1.0 * np.random.random(size=len(timestamps)))
                    * 1024
                    * 1024
                    * 1024
                )  # 2-3GB
            elif metric_key == "disk_usage":
                values = 0.6 + 0.1 * np.random.random(
                    size=len(timestamps)
                )  # 60-70% disk usage
            elif metric_key == "network_traffic":
                values = (
                    (1.0 + 0.5 * np.random.random(size=len(timestamps))) * 1024 * 1024
                )  # 1-1.5MB
            elif metric_key == "error_rate":
                values = 0.01 + 0.02 * np.random.random(
                    size=len(timestamps)
                )  # 1-3% error rate
            elif metric_key == "latency":
                values = 0.1 + 0.1 * np.random.random(
                    size=len(timestamps)
                )  # 100-200ms latency
            else:
                continue

            # Create DataFrame
            df = pd.DataFrame(
                {"timestamp": timestamps, self.metrics_mapping[metric_key]: values}
            )
            df.set_index("timestamp", inplace=True)

            historical_data[metric_key] = df

        return historical_data

    async def _fetch_datadog_historical(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data from Datadog.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        # In a real implementation, you would use the Datadog API
        # This implementation delegates to the Prometheus one for simplicity
        return await self._fetch_prometheus_historical(start_time, end_time)

    async def _fetch_cloudwatch_historical(
        self, start_time: datetime.datetime, end_time: datetime.datetime
    ) -> Dict[str, pd.DataFrame]:
        """
        Fetch historical data from CloudWatch.

        Args:
            start_time: Start time for historical data
            end_time: End time for historical data

        Returns:
            Dictionary mapping metric keys to DataFrames of historical data
        """
        # In a real implementation, you would use the CloudWatch API
        # This implementation delegates to the Prometheus one for simplicity
        return await self._fetch_prometheus_historical(start_time, end_time)
