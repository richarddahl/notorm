"""
Learning-based anomaly detectors.

This module provides machine learning approaches to anomaly detection, including
isolation forest, one-class SVM, autoencoders, and LSTM-based methods.
"""

import time
import logging
import datetime
import importlib.util
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import numpy as np
import pandas as pd

from uno.ai.anomaly_detection.engine import (
    AnomalyDetector,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)


class LearningBasedDetector(AnomalyDetector):
    """
    Learning-based anomaly detector using various machine learning methods.
    
    This detector implements multiple ML methods for anomaly detection:
    - Isolation Forest: Detect anomalies using isolation forest algorithm
    - One-Class SVM: Detect anomalies using one-class SVM
    - Autoencoder: Detect anomalies using neural network autoencoder
    - LSTM: Detect anomalies in time series using LSTM networks
    """
    
    def __init__(
        self,
        anomaly_type: AnomalyType,
        strategy: DetectionStrategy,
        metric_name: str,
        training_window: int = 30,
        threshold: float = 2.0,
        min_data_points: int = 100,
        contamination: float = 0.05,  # Expected proportion of anomalies
        sequence_length: int = 10,    # For sequence models like LSTM
        time_features: bool = True,   # Include time-based features
        feature_columns: Optional[List[str]] = None,  # Additional feature columns
        context_columns: Optional[List[str]] = None,  # Context columns for prediction
        model_path: Optional[str] = None,  # Path to save/load models
        logger: Optional[logging.Logger] = None,
        params: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the learning-based detector.
        
        Args:
            anomaly_type: Type of anomaly to detect
            strategy: Detection strategy to use
            metric_name: Name of the metric to monitor
            training_window: Historical window for training in days
            threshold: Threshold for anomaly detection
            min_data_points: Minimum data points required for detection
            contamination: Expected proportion of anomalies in the dataset
            sequence_length: Length of sequences for LSTM models
            time_features: Whether to include time-based features
            feature_columns: Additional feature columns to use
            context_columns: Context columns to use for prediction
            model_path: Path to save/load models
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
            logger=logger
        )
        
        # ML parameters
        self.contamination = contamination
        self.sequence_length = sequence_length
        self.time_features = time_features
        self.feature_columns = feature_columns or []
        self.context_columns = context_columns or []
        self.model_path = model_path
        self.params = params or {}
        
        # State
        self.model = None
        self.scaler = None
        self.preprocessor = None
        self.feature_names = None
        self.threshold_value = None
        
        # Lazy imports
        self._sklearn_available = self._check_sklearn()
        self._tensorflow_available = self._check_tensorflow()
        
        # Initialize strategy-specific parameters
        if strategy == DetectionStrategy.LEARNING_ISOLATION_FOREST:
            self._initialize_isolation_forest()
        elif strategy == DetectionStrategy.LEARNING_ONE_CLASS_SVM:
            self._initialize_one_class_svm()
        elif strategy == DetectionStrategy.LEARNING_AUTOENCODER:
            self._initialize_autoencoder()
        elif strategy == DetectionStrategy.LEARNING_DEEP_LSTM:
            self._initialize_lstm()
    
    def _check_sklearn(self) -> bool:
        """Check if scikit-learn is available."""
        return importlib.util.find_spec("sklearn") is not None
    
    def _check_tensorflow(self) -> bool:
        """Check if TensorFlow is available."""
        return importlib.util.find_spec("tensorflow") is not None
    
    def _initialize_isolation_forest(self) -> None:
        """Initialize isolation forest detector parameters."""
        if not self._sklearn_available:
            self.logger.warning("scikit-learn not available, isolation forest cannot be used")
            return
        
        # Update parameters from configuration
        self.contamination = self.params.get("contamination", self.contamination)
        self.n_estimators = self.params.get("n_estimators", 100)
        self.max_samples = self.params.get("max_samples", "auto")
        self.random_state = self.params.get("random_state", 42)
    
    def _initialize_one_class_svm(self) -> None:
        """Initialize one-class SVM detector parameters."""
        if not self._sklearn_available:
            self.logger.warning("scikit-learn not available, one-class SVM cannot be used")
            return
        
        # Update parameters from configuration
        self.kernel = self.params.get("kernel", "rbf")
        self.nu = self.params.get("nu", 0.05)
        self.gamma = self.params.get("gamma", "scale")
    
    def _initialize_autoencoder(self) -> None:
        """Initialize autoencoder detector parameters."""
        if not self._tensorflow_available:
            self.logger.warning("TensorFlow not available, autoencoder cannot be used")
            return
        
        # Update parameters from configuration
        self.encoding_dim = self.params.get("encoding_dim", 8)
        self.epochs = self.params.get("epochs", 50)
        self.batch_size = self.params.get("batch_size", 32)
        self.activation = self.params.get("activation", "relu")
        self.learning_rate = self.params.get("learning_rate", 0.001)
    
    def _initialize_lstm(self) -> None:
        """Initialize LSTM detector parameters."""
        if not self._tensorflow_available:
            self.logger.warning("TensorFlow not available, LSTM cannot be used")
            return
        
        # Update parameters from configuration
        self.sequence_length = self.params.get("sequence_length", self.sequence_length)
        self.lstm_units = self.params.get("lstm_units", 64)
        self.dropout_rate = self.params.get("dropout_rate", 0.2)
        self.epochs = self.params.get("epochs", 50)
        self.batch_size = self.params.get("batch_size", 32)
        self.learning_rate = self.params.get("learning_rate", 0.001)
    
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
        
        # Use the appropriate training method based on strategy
        if self.strategy == DetectionStrategy.LEARNING_ISOLATION_FOREST:
            success = await self._train_isolation_forest(data)
        elif self.strategy == DetectionStrategy.LEARNING_ONE_CLASS_SVM:
            success = await self._train_one_class_svm(data)
        elif self.strategy == DetectionStrategy.LEARNING_AUTOENCODER:
            success = await self._train_autoencoder(data)
        elif self.strategy == DetectionStrategy.LEARNING_DEEP_LSTM:
            success = await self._train_lstm(data)
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
    
    async def _train_isolation_forest(self, data: pd.DataFrame) -> bool:
        """
        Train isolation forest detector on data.
        
        Args:
            data: DataFrame with timestamp index and metric values
            
        Returns:
            True if training was successful
        """
        if not self._sklearn_available:
            self.logger.error("scikit-learn not available, isolation forest cannot be used")
            return False
        
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler
            
            # Prepare features
            X, _, feature_names = self._prepare_features(data)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Create and train the model
            self.model = IsolationForest(
                n_estimators=self.n_estimators,
                max_samples=self.max_samples,
                contamination=self.contamination,
                random_state=self.random_state
            )
            
            self.model.fit(X_scaled)
            
            # Calculate decision function on training data to determine threshold
            scores = -self.model.decision_function(X_scaled)
            
            # Set threshold based on quantile
            self.threshold_value = np.quantile(scores, 1 - self.contamination)
            
            # Store feature names
            self.feature_names = feature_names
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training isolation forest: {e}")
            return False
    
    async def _train_one_class_svm(self, data: pd.DataFrame) -> bool:
        """
        Train one-class SVM detector on data.
        
        Args:
            data: DataFrame with timestamp index and metric values
            
        Returns:
            True if training was successful
        """
        if not self._sklearn_available:
            self.logger.error("scikit-learn not available, one-class SVM cannot be used")
            return False
        
        try:
            from sklearn.svm import OneClassSVM
            from sklearn.preprocessing import StandardScaler
            
            # Prepare features
            X, _, feature_names = self._prepare_features(data)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Create and train the model
            self.model = OneClassSVM(
                kernel=self.kernel,
                nu=self.nu,
                gamma=self.gamma
            )
            
            self.model.fit(X_scaled)
            
            # Calculate decision function on training data to determine threshold
            scores = -self.model.decision_function(X_scaled)
            
            # Set threshold based on quantile
            self.threshold_value = np.quantile(scores, 1 - self.contamination)
            
            # Store feature names
            self.feature_names = feature_names
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training one-class SVM: {e}")
            return False
    
    async def _train_autoencoder(self, data: pd.DataFrame) -> bool:
        """
        Train autoencoder detector on data.
        
        Args:
            data: DataFrame with timestamp index and metric values
            
        Returns:
            True if training was successful
        """
        if not self._tensorflow_available:
            self.logger.error("TensorFlow not available, autoencoder cannot be used")
            return False
        
        try:
            import tensorflow as tf
            from sklearn.preprocessing import StandardScaler
            
            # Prepare features
            X, _, feature_names = self._prepare_features(data)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Get input dimension
            input_dim = X_scaled.shape[1]
            
            # Build the autoencoder model
            input_layer = tf.keras.layers.Input(shape=(input_dim,))
            
            # Encoder
            encoded = tf.keras.layers.Dense(
                int(input_dim * 0.75), activation=self.activation
            )(input_layer)
            encoded = tf.keras.layers.Dense(
                self.encoding_dim, activation=self.activation
            )(encoded)
            
            # Decoder
            decoded = tf.keras.layers.Dense(
                int(input_dim * 0.75), activation=self.activation
            )(encoded)
            decoded = tf.keras.layers.Dense(
                input_dim, activation='linear'
            )(decoded)
            
            # Full autoencoder
            self.model = tf.keras.models.Model(inputs=input_layer, outputs=decoded)
            
            # Compile the model
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                loss='mse'
            )
            
            # Train the model
            self.model.fit(
                X_scaled, X_scaled,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.1,
                verbose=0,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        patience=5, restore_best_weights=True
                    )
                ]
            )
            
            # Calculate reconstruction error on training data
            predictions = self.model.predict(X_scaled)
            mse = np.mean(np.power(X_scaled - predictions, 2), axis=1)
            
            # Set threshold based on quantile
            self.threshold_value = np.quantile(mse, 1 - self.contamination)
            
            # Store feature names
            self.feature_names = feature_names
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training autoencoder: {e}")
            return False
    
    async def _train_lstm(self, data: pd.DataFrame) -> bool:
        """
        Train LSTM detector on time series data.
        
        Args:
            data: DataFrame with timestamp index and metric values
            
        Returns:
            True if training was successful
        """
        if not self._tensorflow_available:
            self.logger.error("TensorFlow not available, LSTM cannot be used")
            return False
        
        try:
            import tensorflow as tf
            from sklearn.preprocessing import StandardScaler
            
            # Ensure data is sorted by time
            if not isinstance(data.index, pd.DatetimeIndex):
                self.logger.warning("Data index is not DatetimeIndex, time features may not be accurate")
                
                # If there's a timestamp column, use it
                if 'timestamp' in data.columns:
                    data = data.sort_values('timestamp')
                
            # Prepare features
            X, _, feature_names = self._prepare_features(data)
            
            # Scale features
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            
            # Create sequences for LSTM
            X_seq, y_seq = self._create_sequences(X_scaled, self.sequence_length)
            
            if len(X_seq) < self.min_data_points / 2:
                self.logger.warning(
                    f"Insufficient sequences for training: {len(X_seq)} < {self.min_data_points / 2}"
                )
                return False
            
            # Build the LSTM model
            input_dim = X_seq.shape[2]
            
            # Model architecture
            self.model = tf.keras.models.Sequential([
                tf.keras.layers.LSTM(
                    self.lstm_units, activation='tanh',
                    return_sequences=True, input_shape=(self.sequence_length, input_dim)
                ),
                tf.keras.layers.Dropout(self.dropout_rate),
                tf.keras.layers.LSTM(self.lstm_units // 2, activation='tanh'),
                tf.keras.layers.Dropout(self.dropout_rate),
                tf.keras.layers.Dense(input_dim)
            ])
            
            # Compile the model
            self.model.compile(
                optimizer=tf.keras.optimizers.Adam(learning_rate=self.learning_rate),
                loss='mse'
            )
            
            # Train the model
            self.model.fit(
                X_seq, y_seq,
                epochs=self.epochs,
                batch_size=self.batch_size,
                validation_split=0.1,
                verbose=0,
                callbacks=[
                    tf.keras.callbacks.EarlyStopping(
                        patience=5, restore_best_weights=True
                    )
                ]
            )
            
            # Calculate prediction error on training data
            predictions = self.model.predict(X_seq)
            mse = np.mean(np.power(y_seq - predictions, 2), axis=1)
            
            # Set threshold based on quantile
            self.threshold_value = np.quantile(mse, 1 - self.contamination)
            
            # Store feature names
            self.feature_names = feature_names
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error training LSTM: {e}")
            return False
    
    def _prepare_features(
        self,
        data: pd.DataFrame
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare features for model training or prediction.
        
        Args:
            data: DataFrame with timestamp index and metric values
            
        Returns:
            Tuple of (features array, target array, feature names)
        """
        # Copy data to avoid modifying the original
        df = data.copy()
        
        # Extract target variable
        if self.metric_name in df.columns:
            y = df[self.metric_name].values
        else:
            # Assume it's the first column
            y = df.iloc[:, 0].values
        
        # Create feature set
        feature_cols = [self.metric_name]
        
        # Add time-based features if requested
        if self.time_features and isinstance(df.index, pd.DatetimeIndex):
            # Add hour, day of week, day of month, month features
            df['hour'] = df.index.hour
            df['day_of_week'] = df.index.dayofweek
            df['day_of_month'] = df.index.day
            df['month'] = df.index.month
            
            # Add to feature columns
            feature_cols.extend(['hour', 'day_of_week', 'day_of_month', 'month'])
        
        # Add additional feature columns if available
        for col in self.feature_columns:
            if col in df.columns and col != self.metric_name:
                feature_cols.append(col)
        
        # For multivariate time series, include context columns
        for col in self.context_columns:
            if col in df.columns and col != self.metric_name:
                feature_cols.append(col)
        
        # Ensure all feature columns are present
        feature_cols = [col for col in feature_cols if col in df.columns]
        
        # Create feature matrix
        X = df[feature_cols].values
        
        return X, y, feature_cols
    
    def _create_sequences(
        self,
        data: np.ndarray,
        seq_length: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create sequences from data for LSTM training.
        
        Args:
            data: Feature array
            seq_length: Sequence length
            
        Returns:
            Tuple of (input sequences, output values)
        """
        X = []
        y = []
        
        for i in range(len(data) - seq_length):
            X.append(data[i:i + seq_length])
            y.append(data[i + seq_length])
        
        return np.array(X), np.array(y)
    
    async def detect(self, data_point: Dict[str, Any]) -> Optional[AnomalyAlert]:
        """
        Detect anomalies in a single data point.
        
        Args:
            data_point: The data point to check for anomalies
            
        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        if not self.is_trained or self.model is None:
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
        timestamp = data_point.get('timestamp', datetime.datetime.now())
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.datetime.fromisoformat(timestamp)
            except ValueError:
                timestamp = datetime.datetime.now()
        
        # Detect based on strategy
        alert = None
        if self.strategy == DetectionStrategy.LEARNING_ISOLATION_FOREST:
            alert = await self._detect_isolation_forest(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.LEARNING_ONE_CLASS_SVM:
            alert = await self._detect_one_class_svm(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.LEARNING_AUTOENCODER:
            alert = await self._detect_autoencoder(value, timestamp, data_point)
        elif self.strategy == DetectionStrategy.LEARNING_DEEP_LSTM:
            alert = await self._detect_lstm(value, timestamp, data_point)
        
        # Update metrics
        end_time = time.time()
        self.metrics["detection_time_ms"].append((end_time - start_time) * 1000)
        self.metrics["data_points_processed"] += 1
        if alert:
            self.metrics["anomalies_detected"] += 1
        
        # Keep only the last 1000 detection times
        if len(self.metrics["detection_time_ms"]) > 1000:
            self.metrics["detection_time_ms"] = self.metrics["detection_time_ms"][-1000:]
        
        return alert
    
    async def _detect_isolation_forest(
        self,
        value: float,
        timestamp: datetime.datetime,
        data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using isolation forest.
        
        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point
            
        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        try:
            # Create a feature vector
            X = self._create_feature_vector(data_point, timestamp)
            
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Calculate anomaly score
            score = -self.model.decision_function(X_scaled)[0]
            
            # Check if it exceeds the threshold
            if score > self.threshold_value:
                # Calculate deviation factor (how many times over threshold)
                deviation_factor = score / self.threshold_value
                
                # Determine severity based on deviation
                severity = self._get_severity(deviation_factor)
                
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
                        "threshold": self.threshold_value
                    },
                    deviation_factor=deviation_factor,
                    description=self._get_description_if(value, score),
                    suggestion=self._get_suggestion_if(value, score),
                    metadata={
                        "anomaly_score": score,
                        "threshold": self.threshold_value
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in isolation forest detection: {e}")
        
        return None
    
    async def _detect_one_class_svm(
        self,
        value: float,
        timestamp: datetime.datetime,
        data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using one-class SVM.
        
        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point
            
        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        try:
            # Create a feature vector
            X = self._create_feature_vector(data_point, timestamp)
            
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Calculate anomaly score
            score = -self.model.decision_function(X_scaled)[0]
            
            # Check if it exceeds the threshold
            if score > self.threshold_value:
                # Calculate deviation factor (how many times over threshold)
                deviation_factor = score / self.threshold_value
                
                # Determine severity based on deviation
                severity = self._get_severity(deviation_factor)
                
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
                        "threshold": self.threshold_value
                    },
                    deviation_factor=deviation_factor,
                    description=self._get_description_svm(value, score),
                    suggestion=self._get_suggestion_svm(value, score),
                    metadata={
                        "anomaly_score": score,
                        "threshold": self.threshold_value
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in one-class SVM detection: {e}")
        
        return None
    
    async def _detect_autoencoder(
        self,
        value: float,
        timestamp: datetime.datetime,
        data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using autoencoder.
        
        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point
            
        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        try:
            # Create a feature vector
            X = self._create_feature_vector(data_point, timestamp)
            
            # Scale the features
            X_scaled = self.scaler.transform(X)
            
            # Calculate reconstruction error
            prediction = self.model.predict(X_scaled)
            mse = np.mean(np.power(X_scaled - prediction, 2))
            
            # Check if it exceeds the threshold
            if mse > self.threshold_value:
                # Calculate deviation factor (how many times over threshold)
                deviation_factor = mse / self.threshold_value
                
                # Determine severity based on deviation
                severity = self._get_severity(deviation_factor)
                
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
                        "threshold": self.threshold_value
                    },
                    deviation_factor=deviation_factor,
                    description=self._get_description_ae(value, mse),
                    suggestion=self._get_suggestion_ae(value, mse),
                    metadata={
                        "reconstruction_error": float(mse),
                        "threshold": self.threshold_value
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in autoencoder detection: {e}")
        
        return None
    
    async def _detect_lstm(
        self,
        value: float,
        timestamp: datetime.datetime,
        data_point: Dict[str, Any]
    ) -> Optional[AnomalyAlert]:
        """
        Detect anomalies using LSTM.
        
        Args:
            value: The metric value
            timestamp: The timestamp of the data point
            data_point: The complete data point
            
        Returns:
            An AnomalyAlert if an anomaly is detected, None otherwise
        """
        try:
            # For LSTM, we need the previous sequence to make a prediction
            # First, check if we have enough recent training data
            if not hasattr(self, 'training_data') or self.training_data is None:
                self.logger.warning("No training data available for LSTM sequence")
                return None
            
            # Get the most recent sequence from training data
            recent_data = self.training_data.copy()
            
            # Prepare features for the most recent data
            X_recent, _, _ = self._prepare_features(recent_data)
            X_recent_scaled = self.scaler.transform(X_recent)
            
            # Get the last sequence
            if len(X_recent_scaled) < self.sequence_length:
                self.logger.warning(
                    f"Insufficient data for LSTM sequence: {len(X_recent_scaled)} < {self.sequence_length}"
                )
                return None
            
            last_sequence = X_recent_scaled[-self.sequence_length:]
            last_sequence = np.reshape(last_sequence, (1, self.sequence_length, X_recent_scaled.shape[1]))
            
            # Create a feature vector for the current point
            X = self._create_feature_vector(data_point, timestamp)
            X_scaled = self.scaler.transform(X)
            
            # Make a prediction
            prediction = self.model.predict(last_sequence)
            
            # Calculate prediction error
            mse = np.mean(np.power(X_scaled - prediction, 2))
            
            # Check if it exceeds the threshold
            if mse > self.threshold_value:
                # Calculate deviation factor (how many times over threshold)
                deviation_factor = mse / self.threshold_value
                
                # Determine severity based on deviation
                severity = self._get_severity(deviation_factor)
                
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
                        "threshold": self.threshold_value
                    },
                    deviation_factor=deviation_factor,
                    description=self._get_description_lstm(value, mse),
                    suggestion=self._get_suggestion_lstm(value, mse),
                    metadata={
                        "prediction_error": float(mse),
                        "threshold": self.threshold_value,
                        "predicted_value": float(prediction[0][0]) if prediction.size > 0 else None
                    }
                )
        
        except Exception as e:
            self.logger.error(f"Error in LSTM detection: {e}")
        
        return None
    
    def _create_feature_vector(
        self,
        data_point: Dict[str, Any],
        timestamp: datetime.datetime
    ) -> np.ndarray:
        """
        Create a feature vector for detection.
        
        Args:
            data_point: The data point
            timestamp: The timestamp
            
        Returns:
            Feature vector as numpy array
        """
        # Create feature dictionary
        features = {}
        
        # Add the metric value
        features[self.metric_name] = data_point[self.metric_name]
        
        # Add time-based features if used
        if self.time_features:
            features['hour'] = timestamp.hour
            features['day_of_week'] = timestamp.weekday()
            features['day_of_month'] = timestamp.day
            features['month'] = timestamp.month
        
        # Add other feature columns if available
        for col in self.feature_columns:
            if col in data_point and col != self.metric_name:
                features[col] = data_point[col]
        
        # Add context columns if available
        for col in self.context_columns:
            if col in data_point and col != self.metric_name:
                features[col] = data_point[col]
        
        # Create a DataFrame to ensure correct column order
        df = pd.DataFrame([features])
        
        # Ensure all feature columns used in training are present
        if self.feature_names:
            for col in self.feature_names:
                if col not in df.columns:
                    df[col] = 0  # Use a default value for missing features
            
            # Select only the columns used in training
            df = df[self.feature_names]
        
        return df.values
    
    async def detect_batch(self, data: pd.DataFrame) -> List[AnomalyAlert]:
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
        timestamp_col = 'timestamp'
        if timestamp_col not in data.columns and isinstance(data.index, pd.DatetimeIndex):
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
            deviation: The deviation from normal (ratio to threshold)
            
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
    
    def _get_description_if(self, value: float, score: float) -> str:
        """
        Generate a description for an isolation forest anomaly.
        
        Args:
            value: The metric value
            score: The anomaly score
            
        Returns:
            Description of the anomaly
        """
        return (f"Anomaly detected: {self.metric_name} value of {value:.2f} is anomalous "
                f"(isolation forest anomaly score: {score:.4f}, threshold: {self.threshold_value:.4f})")
    
    def _get_suggestion_if(self, value: float, score: float) -> str:
        """
        Generate a suggestion for an isolation forest anomaly.
        
        Args:
            value: The metric value
            score: The anomaly score
            
        Returns:
            Suggestion for handling the anomaly
        """
        suggestion = "Investigate the context of this anomaly and look for other metrics that might be correlated"
        
        if self.anomaly_type in [AnomalyType.SYSTEM_CPU, AnomalyType.SYSTEM_MEMORY, 
                               AnomalyType.SYSTEM_DISK, AnomalyType.SYSTEM_NETWORK]:
            suggestion += ". Check system resources and recent deployments or configuration changes."
        
        elif self.anomaly_type in [AnomalyType.SYSTEM_ERROR_RATE, AnomalyType.SYSTEM_LATENCY]:
            suggestion += ". Review application logs and monitor related performance metrics."
        
        elif self.anomaly_type.value.startswith("user_"):
            suggestion += ". Review user activity patterns and security logs."
        
        elif self.anomaly_type.value.startswith("data_"):
            suggestion += ". Check data pipelines and validate data quality."
        
        return suggestion
    
    def _get_description_svm(self, value: float, score: float) -> str:
        """
        Generate a description for a one-class SVM anomaly.
        
        Args:
            value: The metric value
            score: The anomaly score
            
        Returns:
            Description of the anomaly
        """
        return (f"Anomaly detected: {self.metric_name} value of {value:.2f} is outside normal boundaries "
                f"(SVM anomaly score: {score:.4f}, threshold: {self.threshold_value:.4f})")
    
    def _get_suggestion_svm(self, value: float, score: float) -> str:
        """
        Generate a suggestion for a one-class SVM anomaly.
        
        Args:
            value: The metric value
            score: The anomaly score
            
        Returns:
            Suggestion for handling the anomaly
        """
        return self._get_suggestion_if(value, score)
    
    def _get_description_ae(self, value: float, error: float) -> str:
        """
        Generate a description for an autoencoder anomaly.
        
        Args:
            value: The metric value
            error: The reconstruction error
            
        Returns:
            Description of the anomaly
        """
        return (f"Anomaly detected: {self.metric_name} value of {value:.2f} is difficult to reconstruct "
                f"(reconstruction error: {error:.4f}, threshold: {self.threshold_value:.4f})")
    
    def _get_suggestion_ae(self, value: float, error: float) -> str:
        """
        Generate a suggestion for an autoencoder anomaly.
        
        Args:
            value: The metric value
            error: The reconstruction error
            
        Returns:
            Suggestion for handling the anomaly
        """
        return self._get_suggestion_if(value, error / self.threshold_value)
    
    def _get_description_lstm(self, value: float, error: float) -> str:
        """
        Generate a description for an LSTM anomaly.
        
        Args:
            value: The metric value
            error: The prediction error
            
        Returns:
            Description of the anomaly
        """
        return (f"Anomaly detected: {self.metric_name} value of {value:.2f} deviates from expected sequence pattern "
                f"(prediction error: {error:.4f}, threshold: {self.threshold_value:.4f})")
    
    def _get_suggestion_lstm(self, value: float, error: float) -> str:
        """
        Generate a suggestion for an LSTM anomaly.
        
        Args:
            value: The metric value
            error: The prediction error
            
        Returns:
            Suggestion for handling the anomaly
        """
        suggestion = "Investigate recent trends and pattern changes in this metric"
        
        if self.anomaly_type in [AnomalyType.SYSTEM_CPU, AnomalyType.SYSTEM_MEMORY, 
                               AnomalyType.SYSTEM_DISK, AnomalyType.SYSTEM_NETWORK]:
            suggestion += ". Check for unusual usage patterns and workload changes."
        
        elif self.anomaly_type in [AnomalyType.SYSTEM_ERROR_RATE, AnomalyType.SYSTEM_LATENCY]:
            suggestion += ". Review application stability and performance metrics over the past few hours."
        
        elif self.anomaly_type.value.startswith("user_"):
            suggestion += ". Examine user behavior patterns for potential account compromise or unusual activity."
        
        elif self.anomaly_type.value.startswith("data_"):
            suggestion += ". Check for changes in data sources or processing that might affect data patterns."
        
        return suggestion