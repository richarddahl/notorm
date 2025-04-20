"""
Hybrid anomaly detectors.

This module provides hybrid approaches to anomaly detection, combining
statistical and machine learning methods for more robust detection.
"""

import time
import logging
import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

import numpy as np
import pandas as pd

from uno.ai.anomaly_detection.engine import (
    AnomalyDetector,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)
from uno.ai.anomaly_detection.detectors.statistical import StatisticalDetector
from uno.ai.anomaly_detection.detectors.learning_based import LearningBasedDetector


class HybridDetector(AnomalyDetector):
    """
    Hybrid anomaly detector combining multiple detection methods.

    This detector implements hybrid approaches to anomaly detection:
    - Ensemble: Combine results from multiple detectors
    - Adaptive: Dynamically select the best detector for each situation
    """

    def __init__(
        self,
        anomaly_type: AnomalyType,
        strategy: DetectionStrategy,
        metric_name: str,
        training_window: int = 30,
        threshold: float = 2.0,
        min_data_points: int = 100,
        ensemble_weights: Optional[dict[str, float]] = None,
        ensemble_threshold: float = 0.6,  # Minimum combined score for anomaly detection
        logger: logging.Logger | None = None,
        params: dict[str, Any] | None = None,
    ):
        """
        Initialize the hybrid detector.

        Args:
            anomaly_type: Type of anomaly to detect
            strategy: Detection strategy to use
            metric_name: Name of the metric to monitor
            training_window: Historical window for training in days
            threshold: Threshold for anomaly detection
            min_data_points: Minimum data points required for detection
            ensemble_weights: Weights for ensemble detectors
            ensemble_threshold: Minimum combined score for anomaly detection
            logger: Logger to use
            params: Additional parameters for the detector
        """
        super().__init__(
            anomaly_type=anomaly_type,
            strategy=strategy,
            metric_name=metric_name,
            training_window=training_window,
            threshold=threshold,
            min_data_points=min_data_points,
            logger=logger,
        )

        # Hybrid parameters
        self.ensemble_weights = ensemble_weights or {}
        self.ensemble_threshold = ensemble_threshold
        self.params = params or {}

        # Sub-detectors
        self.detectors: dict[str, AnomalyDetector] = {}

        # Performance tracking for adaptive strategy
        self.detector_performance: dict[str, dict[str, Any]] = {}

        # Initialize strategy-specific parameters
        if strategy == DetectionStrategy.HYBRID_ENSEMBLE:
            self._initialize_ensemble()
        elif strategy == DetectionStrategy.HYBRID_ADAPTIVE:
            self._initialize_adaptive()

    def _initialize_ensemble(self) -> None:
        """Initialize ensemble detector."""
        # Create sub-detectors for ensemble
        detector_configs = self.params.get("detectors", [])

        # If no detector configs provided, use default set
        if not detector_configs:
            detector_configs = [
                {
                    "type": "statistical",
                    "strategy": DetectionStrategy.STATISTICAL_ZSCORE,
                    "weight": 0.3,
                },
                {
                    "type": "statistical",
                    "strategy": DetectionStrategy.STATISTICAL_IQR,
                    "weight": 0.2,
                },
                {
                    "type": "learning",
                    "strategy": DetectionStrategy.LEARNING_ISOLATION_FOREST,
                    "weight": 0.5,
                },
            ]

        # Create each detector
        for config in detector_configs:
            detector_type = config.get("type", "statistical")
            detector_strategy = config.get("strategy")
            weight = config.get("weight", 1.0)

            if not detector_strategy:
                continue

            # Create detector
            if detector_type == "statistical":
                detector = StatisticalDetector(
                    anomaly_type=self.anomaly_type,
                    strategy=DetectionStrategy(detector_strategy),
                    metric_name=self.metric_name,
                    training_window=self.training_window,
                    threshold=self.threshold,
                    min_data_points=self.min_data_points,
                    logger=self.logger,
                    params=config.get("params", {}),
                )
            elif detector_type == "learning":
                detector = LearningBasedDetector(
                    anomaly_type=self.anomaly_type,
                    strategy=DetectionStrategy(detector_strategy),
                    metric_name=self.metric_name,
                    training_window=self.training_window,
                    threshold=self.threshold,
                    min_data_points=self.min_data_points,
                    logger=self.logger,
                    params=config.get("params", {}),
                )
            else:
                self.logger.warning(f"Unknown detector type: {detector_type}")
                continue

            # Add to detectors
            detector_id = f"{detector_type}_{detector_strategy}"
            self.detectors[detector_id] = detector

            # Set weight
            self.ensemble_weights[detector_id] = weight

        # Normalize weights
        total_weight = sum(self.ensemble_weights.values())
        if total_weight > 0:
            for detector_id in self.ensemble_weights:
                self.ensemble_weights[detector_id] /= total_weight

    def _initialize_adaptive(self) -> None:
        """Initialize adaptive detector."""
        # Create sub-detectors for adaptive strategy
        self._initialize_ensemble()  # Use the same detectors as ensemble

        # Initialize performance tracking
        for detector_id in self.detectors:
            self.detector_performance[detector_id] = {
                "true_positives": 0,
                "false_positives": 0,
                "true_negatives": 0,
                "false_negatives": 0,
                "precision": 0.0,
                "recall": 0.0,
                "f1_score": 0.0,
                "last_update": datetime.datetime.now().isoformat(),
            }

    async def train(self, data: pd.DataFrame) -> bool:
        """
        Train the detector on historical data.

        Args:
            data: Historical data for training with timestamp index and metric value column

        Returns:
            True if training was successful, False otherwise
        """
        start_time = time.time()

        if len(data) < self.min_data_points:
            self.logger.warning(
                f"Insufficient data points for training: {len(data)} < {self.min_data_points}"
            )
            return False

        # Store training data
        self.training_data = data.copy()

        # Train all sub-detectors
        success = True
        for detector_id, detector in self.detectors.items():
            self.logger.info(f"Training sub-detector: {detector_id}")
            sub_success = await detector.train(data)
            if not sub_success:
                self.logger.warning(f"Failed to train sub-detector: {detector_id}")
                success = False

        if success:
            self.is_trained = True
            self.metrics["last_training_time"] = datetime.datetime.now().isoformat()
            self.logger.info(
                f"Trained {self.strategy} detector for {self.anomaly_type} on {self.metric_name}"
            )

        return success

    async def detect(self, data_point: dict[str, Any]) -> Optional[AnomalyAlert]:
        """
        Detect anomalies in a single data point.

        Args:
            data_point: The data point to check for anomalies

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        if not self.is_trained:
            self.logger.warning("Detector not trained, cannot detect anomalies")
            return None

        start_time = time.time()

        # Extract the metric value
        if self.metric_name not in data_point:
            self.logger.warning(f"Metric {self.metric_name} not found in data point")
            return None

        value = data_point[self.metric_name]
        if value is None:
            return None

        # Get the timestamp if available
        timestamp = data_point.get("timestamp", datetime.datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.datetime.now()

        # Detect based on strategy
        alert = None
        if self.strategy == DetectionStrategy.HYBRID_ENSEMBLE:
            alert = await self._detect_ensemble(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.HYBRID_ADAPTIVE:
            alert = await self._detect_adaptive(value, timestamp, data_point)

        # Update metrics
        end_time = time.time()
        self.metrics["detection_time_ms"].append((end_time - start_time) * 1000)
        self.metrics["data_points_processed"] += 1
        if alert:
            self.metrics["anomalies_detected"] += 1

        # Keep only the last 1000 detection times
        if len(self.metrics["detection_time_ms"]) > 1000:
            self.metrics["detection_time_ms"] = self.metrics["detection_time_ms"][
                -1000:
            ]

        return alert

    async def _detect_ensemble(
        self, value: float, timestamp: datetime.datetime, data_point: dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using ensemble of detectors.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        # Run all sub-detectors
        detector_results = {}
        alerts = {}

        for detector_id, detector in self.detectors.items():
            try:
                alert = await detector.detect(data_point)

                if alert:
                    detector_results[detector_id] = alert.deviation_factor
                    alerts[detector_id] = alert
                else:
                    detector_results[detector_id] = 0.0
            except Exception as e:
                self.logger.error(f"Error in sub-detector {detector_id}: {e}")
                detector_results[detector_id] = 0.0

        # Calculate weighted score
        weighted_score = 0.0
        for detector_id, score in detector_results.items():
            weight = self.ensemble_weights.get(detector_id, 1.0 / len(self.detectors))
            weighted_score += score * weight

        # Check if weighted score exceeds threshold
        if weighted_score >= self.ensemble_threshold:
            # Determine the maximum severity from individual alerts
            max_severity = AlertSeverity.INFO
            max_deviation = weighted_score
            description_parts = []
            suggestion_parts = []

            for detector_id, alert in alerts.items():
                if alert.severity.value > max_severity.value:
                    max_severity = alert.severity

                description_parts.append(f"- {detector_id}: {alert.description}")

                if alert.suggestion:
                    suggestion_parts.append(alert.suggestion)

            # Create a combined description and suggestion
            description = (
                f"Ensemble anomaly detected: {self.metric_name} value of {value:.2f}\n"
            )
            description += "\n".join(description_parts)

            # Get unique suggestions
            unique_suggestions = list(set(suggestion_parts))
            suggestion = "\n".join(unique_suggestions) if unique_suggestions else None

            # Create the alert
            return AnomalyAlert(
                timestamp=timestamp,
                anomaly_type=self.anomaly_type,
                detection_strategy=self.strategy,
                severity=max_severity,
                entity_id=data_point.get("entity_id"),
                entity_type=data_point.get("entity_type"),
                metric_name=self.metric_name,
                metric_value=value,
                expected_range={"threshold": self.ensemble_threshold},
                deviation_factor=max_deviation,
                description=description,
                suggestion=suggestion,
                metadata={
                    "detector_results": detector_results,
                    "weighted_score": weighted_score,
                    "threshold": self.ensemble_threshold,
                    "weights": self.ensemble_weights,
                },
            )

        return None

    async def _detect_adaptive(
        self, value: float, timestamp: datetime.datetime, data_point: dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using adaptive selection of detectors.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        # Calculate performance-based weights
        adaptive_weights = self._calculate_adaptive_weights()

        # Store original weights
        original_weights = self.ensemble_weights.copy()

        # Update weights with adaptive weights
        for detector_id, weight in adaptive_weights.items():
            self.ensemble_weights[detector_id] = weight

        # Use ensemble detection with adaptive weights
        alert = await self._detect_ensemble(value, timestamp, data_point)

        # Restore original weights
        self.ensemble_weights = original_weights

        # Update the metadata if an alert was generated
        if alert:
            alert.metadata["adaptive_weights"] = adaptive_weights

        return alert

    def _calculate_adaptive_weights(self) -> dict[str, float]:
        """
        Calculate adaptive weights based on detector performance.

        Returns:
            Dictionary of detector ID to weight
        """
        weights = {}

        # Calculate F1 scores
        f1_scores = {}
        total_f1 = 0.0

        for detector_id, perf in self.detector_performance.items():
            # Calculate precision and recall
            precision = perf["true_positives"] / (
                perf["true_positives"] + perf["false_positives"] + 1e-10
            )
            recall = perf["true_positives"] / (
                perf["true_positives"] + perf["false_negatives"] + 1e-10
            )

            # Calculate F1 score
            f1 = 2 * precision * recall / (precision + recall + 1e-10)

            # Store F1 score
            f1_scores[detector_id] = f1
            total_f1 += f1

        # If we have no performance data, use original weights
        if total_f1 <= 0:
            return self.ensemble_weights.copy()

        # Calculate weights based on F1 scores
        for detector_id, f1 in f1_scores.items():
            weights[detector_id] = f1 / total_f1

        return weights

    def update_detector_performance(
        self,
        detector_id: str,
        true_positive: int = 0,
        false_positive: int = 0,
        true_negative: int = 0,
        false_negative: int = 0,
    ) -> None:
        """
        Update performance metrics for a detector.

        Args:
            detector_id: ID of the detector to update
            true_positive: Number of true positives to add
            false_positive: Number of false positives to add
            true_negative: Number of true negatives to add
            false_negative: Number of false negatives to add
        """
        if detector_id not in self.detector_performance:
            return

        perf = self.detector_performance[detector_id]

        # Update counts
        perf["true_positives"] += true_positive
        perf["false_positives"] += false_positive
        perf["true_negatives"] += true_negative
        perf["false_negatives"] += false_negative

        # Calculate precision and recall
        precision = perf["true_positives"] / (
            perf["true_positives"] + perf["false_positives"] + 1e-10
        )
        recall = perf["true_positives"] / (
            perf["true_positives"] + perf["false_negatives"] + 1e-10
        )

        # Calculate F1 score
        f1 = 2 * precision * recall / (precision + recall + 1e-10)

        # Update metrics
        perf["precision"] = precision
        perf["recall"] = recall
        perf["f1_score"] = f1
        perf["last_update"] = datetime.datetime.now().isoformat()

    async def detect_batch(self, data: pd.DataFrame) -> list[AnomalyAlert]:
        """
        Detect anomalies in a batch of data points.

        Args:
            data: DataFrame with data points to check for anomalies

        Returns:
            List of AnomalyAlert objects for detected anomalies
        """
        if not self.is_trained:
            self.logger.warning("Detector not trained, cannot detect anomalies")
            return []

        if self.metric_name not in data.columns:
            self.logger.warning(f"Metric {self.metric_name} not found in data")
            return []

        # Prepare timestamp column if available
        timestamp_col = "timestamp"
        if timestamp_col not in data.columns and isinstance(
            data.index, pd.DatetimeIndex
        ):
            data = data.copy()
            data[timestamp_col] = data.index

        # Process each row
        alerts = []
        for _, row in data.iterrows():
            # Convert row to dictionary
            data_point = row.to_dict()

            # Detect anomalies
            alert = await self.detect(data_point)
            if alert:
                alerts.append(alert)

        return alerts
