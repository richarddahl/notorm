"""
Statistical anomaly detectors.

This module provides statistical approaches to anomaly detection, including
Z-score, IQR, moving averages, and regression-based methods.
"""

import time
import logging
import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from uno.ai.anomaly_detection.engine import (
    AnomalyDetector,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)


class StatisticalDetector(AnomalyDetector):
    """
    Statistical anomaly detector using various statistical methods.

    This detector implements multiple statistical methods for anomaly detection:
    - Z-score: Detect anomalies based on standard deviations from the mean
    - IQR: Detect anomalies based on interquartile range
    - Moving Average: Detect anomalies based on deviation from moving average
    - Regression: Detect anomalies based on deviation from regression model
    """

    def __init__(
        self,
        anomaly_type: AnomalyType,
        strategy: DetectionStrategy,
        metric_name: str,
        training_window: int = 30,
        threshold: float = 2.0,
        min_data_points: int = 100,
        window_size: int = 24,  # For moving average
        seasonality: int = 24,  # For seasonal decomposition
        logger: logging.Logger | None = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the statistical detector.

        Args:
            anomaly_type: Type of anomaly to detect
            strategy: Detection strategy to use
            metric_name: Name of the metric to monitor
            training_window: Historical window for training in days
            threshold: Threshold for anomaly detection (standard deviations or IQR multiplier)
            min_data_points: Minimum data points required for detection
            window_size: Window size for moving average
            seasonality: Seasonality period for time series decomposition
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

        # Statistical parameters
        self.window_size = window_size
        self.seasonality = seasonality
        self.params = params or {}

        # Statistical state
        self.mean = None
        self.std = None
        self.q1 = None
        self.q3 = None
        self.iqr = None
        self.moving_averages = None
        self.regression_model = None
        self.time_index = None

        # Initialize strategy-specific parameters
        if strategy == DetectionStrategy.STATISTICAL_ZSCORE:
            self._initialize_zscore()
        elif strategy == DetectionStrategy.STATISTICAL_IQR:
            self._initialize_iqr()
        elif strategy == DetectionStrategy.STATISTICAL_MOVING_AVERAGE:
            self._initialize_moving_average()
        elif strategy == DetectionStrategy.STATISTICAL_REGRESSION:
            self._initialize_regression()

    def _initialize_zscore(self) -> None:
        """Initialize Z-score detector parameters."""
        # Default initialization is sufficient
        pass

    def _initialize_iqr(self) -> None:
        """Initialize IQR detector parameters."""
        # Default initialization is sufficient
        pass

    def _initialize_moving_average(self) -> None:
        """Initialize moving average detector parameters."""
        self.window_size = self.params.get("window_size", self.window_size)

    def _initialize_regression(self) -> None:
        """Initialize regression detector parameters."""
        self.seasonality = self.params.get("seasonality", self.seasonality)
        self.include_trend = self.params.get("include_trend", True)
        self.include_seasonal = self.params.get("include_seasonal", True)

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

        # Extract the metric values
        if self.metric_name in data.columns:
            values = data[self.metric_name].dropna().values
        else:
            # Assume single column dataframe
            values = data.iloc[:, 0].dropna().values

        if len(values) < self.min_data_points:
            self.logger.warning(
                f"Insufficient non-null data points for training: {len(values)} < {self.min_data_points}"
            )
            return False

        # Train based on strategy
        if self.strategy == DetectionStrategy.STATISTICAL_ZSCORE:
            success = self._train_zscore(values)
        elif self.strategy == DetectionStrategy.STATISTICAL_IQR:
            success = self._train_iqr(values)
        elif self.strategy == DetectionStrategy.STATISTICAL_MOVING_AVERAGE:
            success = self._train_moving_average(data)
        elif self.strategy == DetectionStrategy.STATISTICAL_REGRESSION:
            success = self._train_regression(data)
        else:
            self.logger.error(f"Unsupported strategy: {self.strategy}")
            return False

        if success:
            self.is_trained = True
            self.metrics["last_training_time"] = datetime.datetime.now().isoformat()
            self.logger.info(
                f"Trained {self.strategy} detector for {self.anomaly_type} on {self.metric_name}"
            )

        return success

    def _train_zscore(self, values: np.ndarray) -> bool:
        """
        Train Z-score detector on values.

        Args:
            values: Array of metric values

        Returns:
            True if training was successful
        """
        # Calculate mean and standard deviation
        self.mean = np.mean(values)
        self.std = np.std(values)

        if self.std == 0:
            self.logger.warning(
                "Standard deviation is zero, Z-score detector may not be effective"
            )
            # Use a small value to avoid division by zero
            self.std = 1e-6

        return True

    def _train_iqr(self, values: np.ndarray) -> bool:
        """
        Train IQR detector on values.

        Args:
            values: Array of metric values

        Returns:
            True if training was successful
        """
        # Calculate quartiles and IQR
        self.q1 = np.percentile(values, 25)
        self.q3 = np.percentile(values, 75)
        self.iqr = self.q3 - self.q1

        if self.iqr == 0:
            self.logger.warning("IQR is zero, IQR detector may not be effective")
            # Use a small value to avoid zero IQR
            self.iqr = 1e-6

        return True

    def _train_moving_average(self, data: pd.DataFrame) -> bool:
        """
        Train moving average detector on time series data.

        Args:
            data: DataFrame with timestamp index and metric values

        Returns:
            True if training was successful
        """
        # Ensure data is sorted by time
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning(
                "Data index is not DatetimeIndex, moving average may not be effective"
            )
            return False

        # Get the metric values
        if self.metric_name in data.columns:
            series = data[self.metric_name]
        else:
            # Assume single column dataframe
            series = data.iloc[:, 0]

        # Calculate moving averages and standard deviations for different windows
        self.moving_averages = {}

        # Use multiple window sizes for robustness
        window_sizes = [
            max(3, self.window_size // 4),  # Short-term
            max(5, self.window_size // 2),  # Medium-term
            self.window_size,  # Long-term
        ]

        for window in window_sizes:
            # Calculate the rolling mean and std
            rolling_mean = series.rolling(window=window, min_periods=3).mean()
            rolling_std = series.rolling(window=window, min_periods=3).std()

            # Handle zero std with a small constant
            rolling_std = rolling_std.replace(0, 1e-6)

            self.moving_averages[window] = {"mean": rolling_mean, "std": rolling_std}

        return True

    def _train_regression(self, data: pd.DataFrame) -> bool:
        """
        Train regression-based detector on time series data.

        Args:
            data: DataFrame with timestamp index and metric values

        Returns:
            True if training was successful
        """
        # Ensure data is sorted by time
        if not isinstance(data.index, pd.DatetimeIndex):
            self.logger.warning(
                "Data index is not DatetimeIndex, regression may not be effective"
            )
            return False

        # Get the metric values
        if self.metric_name in data.columns:
            series = data[self.metric_name]
        else:
            # Assume single column dataframe
            series = data.iloc[:, 0]

        # Create time features for regression
        try:
            # Convert index to numeric for regression
            self.time_index = np.arange(len(series))

            # Create a DataFrame with time features
            X = pd.DataFrame({"time": self.time_index})

            # Add trend features (polynomial)
            if self.include_trend:
                X["time_squared"] = X["time"] ** 2

            # Add seasonal features (sin/cos)
            if self.include_seasonal and self.seasonality > 0:
                for period in [
                    self.seasonality,
                    self.seasonality // 2,
                ]:  # Fundamental and harmonic
                    X[f"sin_{period}"] = np.sin(2 * np.pi * X["time"] / period)
                    X[f"cos_{period}"] = np.cos(2 * np.pi * X["time"] / period)

            # Add hour of day, day of week features if available in index
            if isinstance(data.index, pd.DatetimeIndex):
                X["hour"] = data.index.hour
                X["day_of_week"] = data.index.dayofweek

            # Add constant for intercept
            X = sm.add_constant(X)

            # Fit regression model
            self.regression_model = sm.OLS(series, X).fit()

            # Calculate residuals
            self.residuals = self.regression_model.resid
            self.residual_std = np.std(self.residuals)

            if self.residual_std == 0:
                self.residual_std = 1e-6  # Avoid division by zero

            return True

        except Exception as e:
            self.logger.error(f"Error training regression model: {e}")
            return False

    async def detect(self, data_point: Dict[str, Any]) -> Optional[AnomalyAlert]:
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
        if self.strategy == DetectionStrategy.STATISTICAL_ZSCORE:
            alert = self._detect_zscore(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.STATISTICAL_IQR:
            alert = self._detect_iqr(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.STATISTICAL_MOVING_AVERAGE:
            alert = self._detect_moving_average(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.STATISTICAL_REGRESSION:
            alert = self._detect_regression(value, timestamp, data_point)

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

    def _detect_zscore(
        self, value: float, timestamp: datetime.datetime, data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using Z-score.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        # Calculate Z-score
        z_score = (value - self.mean) / self.std

        # Check if it exceeds the threshold
        if abs(z_score) > self.threshold:
            # Determine severity based on z-score magnitude
            severity = self._get_severity(abs(z_score))

            # Create alert
            return AnomalyAlert(
                timestamp=timestamp,
                anomaly_type=self.anomaly_type,
                detection_strategy=self.strategy,
                severity=severity,
                entity_id=data_point.get("entity_id"),
                entity_type=data_point.get("entity_type"),
                metric_name=self.metric_name,
                metric_value=value,
                expected_range={
                    "lower": self.mean - self.threshold * self.std,
                    "upper": self.mean + self.threshold * self.std,
                },
                deviation_factor=abs(z_score),
                description=self._get_description(value, z_score),
                suggestion=self._get_suggestion(value, z_score),
                metadata={
                    "z_score": z_score,
                    "mean": self.mean,
                    "std": self.std,
                    "threshold": self.threshold,
                },
            )

        return None

    def _detect_iqr(
        self, value: float, timestamp: datetime.datetime, data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using IQR method.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        # Calculate IQR bounds
        lower_bound = self.q1 - self.threshold * self.iqr
        upper_bound = self.q3 + self.threshold * self.iqr

        # Check if value is outside the bounds
        if value < lower_bound or value > upper_bound:
            # Calculate the deviation factor
            deviation = 0
            if value < lower_bound:
                deviation = (lower_bound - value) / self.iqr
            else:
                deviation = (value - upper_bound) / self.iqr

            # Determine severity based on deviation
            severity = self._get_severity(deviation)

            # Create alert
            return AnomalyAlert(
                timestamp=timestamp,
                anomaly_type=self.anomaly_type,
                detection_strategy=self.strategy,
                severity=severity,
                entity_id=data_point.get("entity_id"),
                entity_type=data_point.get("entity_type"),
                metric_name=self.metric_name,
                metric_value=value,
                expected_range={"lower": lower_bound, "upper": upper_bound},
                deviation_factor=deviation,
                description=self._get_description_iqr(value, lower_bound, upper_bound),
                suggestion=self._get_suggestion_iqr(value, lower_bound, upper_bound),
                metadata={
                    "q1": self.q1,
                    "q3": self.q3,
                    "iqr": self.iqr,
                    "threshold": self.threshold,
                },
            )

        return None

    def _detect_moving_average(
        self, value: float, timestamp: datetime.datetime, data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using moving average method.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        # If we can't find a matching timestamp, we can't detect anomalies
        if not isinstance(self.training_data.index, pd.DatetimeIndex):
            return None

        # Get the most recent window data
        anomalies = []
        max_deviation = 0
        anomaly_window = None

        # Check against each window size
        for window, window_data in self.moving_averages.items():
            # Find the closest timestamp in the training data
            try:
                closest_idx = self.training_data.index.get_indexer(
                    [timestamp], method="nearest"
                )[0]
                if closest_idx < 0 or closest_idx >= len(window_data["mean"]):
                    continue  # No close match

                # Get the mean and std for this timestamp
                mean = window_data["mean"].iloc[closest_idx]
                std = window_data["std"].iloc[closest_idx]

                # Calculate z-score for this window
                if not np.isnan(mean) and not np.isnan(std):
                    z_score = (value - mean) / std

                    # Check if it exceeds the threshold
                    if abs(z_score) > self.threshold:
                        anomalies.append((window, z_score, mean, std))
                        if abs(z_score) > max_deviation:
                            max_deviation = abs(z_score)
                            anomaly_window = window

            except Exception as e:
                self.logger.warning(
                    f"Error detecting with moving average (window={window}): {e}"
                )

        # If we found anomalies in any window, create an alert
        if anomalies:
            # Find the anomaly with the highest deviation
            window, z_score, mean, std = next(
                (a for a in anomalies if a[0] == anomaly_window), anomalies[0]
            )

            # Determine severity based on z-score magnitude
            severity = self._get_severity(abs(z_score))

            # Create alert
            return AnomalyAlert(
                timestamp=timestamp,
                anomaly_type=self.anomaly_type,
                detection_strategy=self.strategy,
                severity=severity,
                entity_id=data_point.get("entity_id"),
                entity_type=data_point.get("entity_type"),
                metric_name=self.metric_name,
                metric_value=value,
                expected_range={
                    "lower": mean - self.threshold * std,
                    "upper": mean + self.threshold * std,
                },
                deviation_factor=abs(z_score),
                description=self._get_description_ma(value, z_score, window),
                suggestion=self._get_suggestion_ma(value, z_score, window),
                metadata={
                    "z_score": z_score,
                    "mean": mean,
                    "std": std,
                    "window": window,
                    "threshold": self.threshold,
                    "all_anomalies": anomalies,
                },
            )

        return None

    def _detect_regression(
        self, value: float, timestamp: datetime.datetime, data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using regression-based method.

        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point

        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        if not hasattr(self, "regression_model") or self.regression_model is None:
            return None

        try:
            # Create features for this data point
            features = {}

            # Use the next index after training data
            time_idx = len(self.time_index)
            features["time"] = time_idx

            # Add trend features
            if self.include_trend:
                features["time_squared"] = time_idx**2

            # Add seasonal features
            if self.include_seasonal and self.seasonality > 0:
                for period in [self.seasonality, self.seasonality // 2]:
                    features[f"sin_{period}"] = np.sin(2 * np.pi * time_idx / period)
                    features[f"cos_{period}"] = np.cos(2 * np.pi * time_idx / period)

            # Add hour of day, day of week features
            if isinstance(timestamp, datetime.datetime):
                features["hour"] = timestamp.hour
                features["day_of_week"] = timestamp.weekday()

            # Create feature vector for prediction
            X_pred = pd.DataFrame([features])

            # Add constant
            X_pred = sm.add_constant(X_pred)

            # Ensure columns match the training data
            for col in self.regression_model.model.exog_names:
                if col not in X_pred.columns:
                    X_pred[col] = 0

            # Keep only the columns used in the model
            X_pred = X_pred[self.regression_model.model.exog_names]

            # Predict the expected value
            predicted_value = self.regression_model.predict(X_pred)[0]

            # Calculate the residual
            residual = value - predicted_value

            # Calculate z-score of the residual
            z_score = residual / self.residual_std

            # Check if it exceeds the threshold
            if abs(z_score) > self.threshold:
                # Determine severity based on z-score magnitude
                severity = self._get_severity(abs(z_score))

                # Create alert
                return AnomalyAlert(
                    timestamp=timestamp,
                    anomaly_type=self.anomaly_type,
                    detection_strategy=self.strategy,
                    severity=severity,
                    entity_id=data_point.get("entity_id"),
                    entity_type=data_point.get("entity_type"),
                    metric_name=self.metric_name,
                    metric_value=value,
                    expected_range={
                        "lower": predicted_value - self.threshold * self.residual_std,
                        "upper": predicted_value + self.threshold * self.residual_std,
                    },
                    deviation_factor=abs(z_score),
                    description=self._get_description_regression(
                        value, predicted_value, z_score
                    ),
                    suggestion=self._get_suggestion_regression(
                        value, predicted_value, z_score
                    ),
                    metadata={
                        "z_score": z_score,
                        "predicted_value": predicted_value,
                        "residual": residual,
                        "residual_std": self.residual_std,
                        "threshold": self.threshold,
                    },
                )

        except Exception as e:
            self.logger.error(f"Error in regression-based detection: {e}")

        return None

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

    def _get_severity(self, deviation: float) -> AlertSeverity:
        """
        Determine alert severity based on deviation.

        Args:
            deviation: The deviation from normal (z-score or similar)

        Returns:
            Appropriate AlertSeverity level
        """
        if deviation >= 5:
            return AlertSeverity.EMERGENCY
        elif deviation >= 3:
            return AlertSeverity.CRITICAL
        elif deviation >= 2:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO

    def _get_description(self, value: float, z_score: float) -> str:
        """
        Generate a description for a Z-score anomaly.

        Args:
            value: The metric value
            z_score: The Z-score

        Returns:
            Description of the anomaly
        """
        direction = "above" if z_score > 0 else "below"
        return (
            f"Anomaly detected: {self.metric_name} value of {value:.2f} is {direction} "
            f"normal range (z-score: {z_score:.2f}, threshold: {self.threshold})"
        )

    def _get_suggestion(self, value: float, z_score: float) -> str:
        """
        Generate a suggestion for a Z-score anomaly.

        Args:
            value: The metric value
            z_score: The Z-score

        Returns:
            Suggestion for handling the anomaly
        """
        if self.anomaly_type in [
            AnomalyType.SYSTEM_CPU,
            AnomalyType.SYSTEM_MEMORY,
            AnomalyType.SYSTEM_DISK,
            AnomalyType.SYSTEM_NETWORK,
        ]:
            if z_score > 0:
                return "Check for resource consumption spikes and consider scaling resources if persistent"
            else:
                return "Verify system health; unusually low resource usage might indicate service issues"

        elif self.anomaly_type in [
            AnomalyType.SYSTEM_ERROR_RATE,
            AnomalyType.SYSTEM_LATENCY,
        ]:
            return "Investigate recent system changes or traffic patterns that might explain the anomaly"

        elif self.anomaly_type.value.startswith("user_"):
            return (
                "Review user activity logs and investigate potential security concerns"
            )

        elif self.anomaly_type.value.startswith("data_"):
            return "Investigate data quality and pipeline integrity"

        return "Investigate the root cause of this anomaly"

    def _get_description_iqr(
        self, value: float, lower_bound: float, upper_bound: float
    ) -> str:
        """
        Generate a description for an IQR anomaly.

        Args:
            value: The metric value
            lower_bound: The lower bound of the normal range
            upper_bound: The upper bound of the normal range

        Returns:
            Description of the anomaly
        """
        if value < lower_bound:
            return (
                f"Anomaly detected: {self.metric_name} value of {value:.2f} is below "
                f"normal range ({lower_bound:.2f} to {upper_bound:.2f})"
            )
        else:
            return (
                f"Anomaly detected: {self.metric_name} value of {value:.2f} is above "
                f"normal range ({lower_bound:.2f} to {upper_bound:.2f})"
            )

    def _get_suggestion_iqr(
        self, value: float, lower_bound: float, upper_bound: float
    ) -> str:
        """
        Generate a suggestion for an IQR anomaly.

        Args:
            value: The metric value
            lower_bound: The lower bound of the normal range
            upper_bound: The upper bound of the normal range

        Returns:
            Suggestion for handling the anomaly
        """
        return self._get_suggestion(
            value, (value - (upper_bound + lower_bound) / 2) / self.iqr
        )

    def _get_description_ma(self, value: float, z_score: float, window: int) -> str:
        """
        Generate a description for a moving average anomaly.

        Args:
            value: The metric value
            z_score: The Z-score
            window: The window size

        Returns:
            Description of the anomaly
        """
        direction = "above" if z_score > 0 else "below"
        return (
            f"Anomaly detected: {self.metric_name} value of {value:.2f} is {direction} "
            f"expected range based on {window}-point moving average "
            f"(z-score: {z_score:.2f}, threshold: {self.threshold})"
        )

    def _get_suggestion_ma(self, value: float, z_score: float, window: int) -> str:
        """
        Generate a suggestion for a moving average anomaly.

        Args:
            value: The metric value
            z_score: The Z-score
            window: The window size

        Returns:
            Suggestion for handling the anomaly
        """
        return self._get_suggestion(value, z_score)

    def _get_description_regression(
        self, value: float, predicted: float, z_score: float
    ) -> str:
        """
        Generate a description for a regression-based anomaly.

        Args:
            value: The metric value
            predicted: The predicted value
            z_score: The Z-score of the residual

        Returns:
            Description of the anomaly
        """
        direction = "above" if value > predicted else "below"
        return (
            f"Anomaly detected: {self.metric_name} value of {value:.2f} is {direction} "
            f"predicted value of {predicted:.2f} "
            f"(z-score: {z_score:.2f}, threshold: {self.threshold})"
        )

    def _get_suggestion_regression(
        self, value: float, predicted: float, z_score: float
    ) -> str:
        """
        Generate a suggestion for a regression-based anomaly.

        Args:
            value: The metric value
            predicted: The predicted value
            z_score: The Z-score of the residual

        Returns:
            Suggestion for handling the anomaly
        """
        return self._get_suggestion(value, z_score)
