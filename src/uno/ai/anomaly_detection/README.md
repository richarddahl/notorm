# Anomaly Detection System

The uno Anomaly Detection System provides comprehensive tools for detecting anomalies in system metrics, user behavior, and data quality. This module enables proactive monitoring and alerting for potential issues in your applications.

## Features

- **Multiple Detection Strategies**: Statistical, machine learning-based, and hybrid approaches
- **Different Anomaly Types**: System metrics, user behavior, and data quality
- **Integrations**: Monitoring systems, metrics collection, and alerting
- **Visualization**: Anomaly dashboards and time series analysis
- **API Integration**: RESTful API for detection and management

## Key Components

### Core Engine

The `AnomalyDetectionEngine` provides the central functionality for detecting anomalies, managing detectors, and handling alerts:

```python
from uno.ai.anomaly_detection.engine import AnomalyDetectionEngine

# Create engine with database storage for alerts
engine = AnomalyDetectionEngine(
    connection_string="postgresql://user:pass@localhost/dbname",
    alert_store_table="anomaly_alerts"
)

# Initialize the engine
await engine.initialize()

# Process data points
alerts = await engine.process_data_point({
    "cpu_usage": 0.95,
    "timestamp": datetime.datetime.now(),
    "entity_id": "server-01",
    "entity_type": "instance"
})
```

### Detection Strategies

#### Statistical Detectors

Statistical approaches for anomaly detection, including Z-score, IQR, moving average, and regression-based methods:

```python
from uno.ai.anomaly_detection.detectors import StatisticalDetector
from uno.ai.anomaly_detection.engine import AnomalyType, DetectionStrategy

# Create a Z-score detector for CPU usage
detector = StatisticalDetector(
    anomaly_type=AnomalyType.SYSTEM_CPU,
    strategy=DetectionStrategy.STATISTICAL_ZSCORE,
    metric_name="cpu_usage",
    threshold=3.0  # 3 standard deviations
)

# Register with the engine
detector_id = await engine.register_detector(detector)
```

#### Learning-Based Detectors

Machine learning approaches for anomaly detection, including isolation forest, one-class SVM, autoencoder, and LSTM-based methods:

```python
from uno.ai.anomaly_detection.detectors import LearningBasedDetector

# Create an isolation forest detector for transaction patterns
detector = LearningBasedDetector(
    anomaly_type=AnomalyType.USER_TRANSACTION_PATTERN,
    strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
    metric_name="transaction_amount",
    contamination=0.05  # Expected proportion of anomalies
)

# Register with the engine
detector_id = await engine.register_detector(detector)
```

#### Hybrid Detectors

Hybrid approaches combining multiple detection strategies for more robust anomaly detection:

```python
from uno.ai.anomaly_detection.detectors import HybridDetector

# Create an ensemble detector for data quality
detector = HybridDetector(
    anomaly_type=AnomalyType.DATA_QUALITY,
    strategy=DetectionStrategy.HYBRID_ENSEMBLE,
    metric_name="data_quality_score",
    ensemble_threshold=0.7  # Minimum score to trigger an alert
)

# Register with the engine
detector_id = await engine.register_detector(detector)
```

### Integrations

#### System Monitoring

Monitor system metrics like CPU, memory, disk, network, error rates, and latency:

```python
from uno.ai.anomaly_detection.integrations import SystemMonitorIntegration

# Create system monitoring integration
monitor = SystemMonitorIntegration(
    engine=engine,
    metrics_source="prometheus",
    poll_interval=60  # seconds
)

# Start monitoring
await monitor.start()

# Train detectors on historical data
await monitor.train_detectors(days=30)
```

#### User Behavior Monitoring

Monitor user behavior patterns including login activity, access patterns, and transaction behavior:

```python
from uno.ai.anomaly_detection.integrations import UserBehaviorIntegration

# Create user behavior monitoring integration
monitor = UserBehaviorIntegration(
    engine=engine,
    data_source="database",
    poll_interval=300,  # seconds
    db_connection="postgresql://user:pass@localhost/dbname"
)

# Start monitoring
await monitor.start()
```

#### Data Quality Monitoring

Monitor data quality metrics including completeness, consistency, validity, and volume:

```python
from uno.ai.anomaly_detection.integrations import DataQualityIntegration

# Create data quality monitoring integration
monitor = DataQualityIntegration(
    engine=engine,
    data_source="database",
    tables=["users", "transactions", "products"],
    poll_interval=3600,  # seconds
    db_connection="postgresql://user:pass@localhost/dbname"
)

# Start monitoring
await monitor.start()
```

### API Integration

Integrate anomaly detection with FastAPI applications:

```python
from fastapi import FastAPI
from uno.ai.anomaly_detection.api import integrate_anomaly_detection

# Create FastAPI app
app = FastAPI()

# Integrate anomaly detection
engine = integrate_anomaly_detection(
    app=app,
    connection_string="postgresql://user:pass@localhost/dbname",
    path_prefix="/api/anomalies"
)

# Start the app
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
```

## Handling Alerts

Register alert handlers to respond to detected anomalies:

```python
async def alert_handler(alert):
    print(f"Anomaly detected: {alert.description}")
    
    # Send notification
    if alert.is_critical:
        await send_critical_notification(alert)
    
    # Log to monitoring system
    await log_to_monitoring_system(alert)

# Register alert handler with the engine
await engine.register_alert_handler(alert_handler)
```

## Training Detectors

Train detectors on historical data:

```python
# Create training data
import pandas as pd
import numpy as np

# Generate time series data
timestamps = pd.date_range(
    start=datetime.datetime.now() - datetime.timedelta(days=30),
    end=datetime.datetime.now(),
    freq="1h"
)

# CPU usage time series
values = 0.4 + 0.2 * np.sin(np.arange(len(timestamps)) * np.pi / 12) + 0.1 * np.random.randn(len(timestamps))

# Create DataFrame
train_df = pd.DataFrame({
    "timestamp": timestamps,
    "cpu_usage": values
})
train_df.set_index("timestamp", inplace=True)

# Train detector
await engine.train_detector("statistical_zscore_cpu_usage", train_df)
```

## Example Usage

See the [examples](examples/anomaly_detection_example.py) directory for complete examples of using the anomaly detection system.

## Best Practices

1. **Start with Statistical Detectors**: For most metrics, start with simple statistical detectors before trying more complex approaches.

2. **Use Historical Data**: Always train detectors on representative historical data to capture normal patterns.

3. **Tune Thresholds Carefully**: Set appropriate thresholds to balance sensitivity and false alarms.

4. **Combine Detection Strategies**: Use hybrid detectors for critical systems to reduce false positives.

5. **Implement Proper Alert Handling**: Ensure alerts are properly categorized, routed, and resolved.

6. **Regular Retraining**: Periodically retrain detectors as system behavior evolves.

7. **Monitor Detector Performance**: Track false positive and false negative rates to improve detectors over time.

## Requirements

- Python 3.9+
- asyncio
- numpy
- pandas
- scikit-learn (optional, for learning-based detectors)
- tensorflow (optional, for deep learning detectors)
- fastapi (optional, for API integration)
- asyncpg (optional, for database storage)

## Customization

The anomaly detection system is designed to be extensible. You can:

1. Create custom detectors by extending the base detector classes
2. Implement custom integrations for specific data sources
3. Add custom alert handlers for specific notification systems
4. Extend the API with additional endpoints for specific use cases