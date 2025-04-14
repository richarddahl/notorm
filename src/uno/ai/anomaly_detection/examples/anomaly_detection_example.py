"""
Example usage of the anomaly detection system.

This script demonstrates how to use the anomaly detection system to
detect anomalies in system metrics, user behavior, and data quality.
"""

import asyncio
import datetime
import json
import logging
import os
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Depends, Query, HTTPException
import uvicorn

from uno.ai.anomaly_detection.engine import (
    AnomalyDetectionEngine,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)
from uno.ai.anomaly_detection.detectors import (
    StatisticalDetector,
    LearningBasedDetector,
    HybridDetector,
)
from uno.ai.anomaly_detection.integrations import (
    SystemMonitorIntegration,
    UserBehaviorIntegration, 
    DataQualityIntegration,
)
from uno.ai.anomaly_detection.api import integrate_anomaly_detection


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


async def alert_handler(alert: AnomalyAlert):
    """
    Example alert handler.
    
    Args:
        alert: The anomaly alert
    """
    print(f"\n{'='*80}")
    print(f"ANOMALY ALERT: {alert.severity.value.upper()}")
    print(f"Type: {alert.anomaly_type.value}")
    print(f"Metric: {alert.metric_name} = {alert.metric_value}")
    print(f"Entity: {alert.entity_type or 'unknown'}/{alert.entity_id or 'unknown'}")
    print(f"Timestamp: {alert.timestamp}")
    print(f"Description: {alert.description}")
    if alert.suggestion:
        print(f"Suggestion: {alert.suggestion}")
    print(f"Deviation Factor: {alert.deviation_factor:.2f}")
    print(f"Expected Range: {json.dumps(alert.expected_range)}")
    print(f"{'='*80}\n")


async def example_fastapi_integration():
    """Example of integrating anomaly detection with FastAPI."""
    # Create FastAPI app
    app = FastAPI(title="Anomaly Detection API", version="1.0.0")
    
    # Database connection (for production, use a real database)
    # In this example, we use in-memory storage
    connection_string = None
    
    # Integrate anomaly detection
    engine = integrate_anomaly_detection(
        app=app,
        connection_string=connection_string,
        path_prefix="/api/anomalies"
    )
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Start the server
    logger.info("Starting FastAPI server")
    uvicorn.run(app, host="127.0.0.1", port=8000)


async def example_statistical_detector():
    """Example of using a statistical detector."""
    logger.info("Starting statistical detector example")
    
    # Create an anomaly detection engine
    engine = AnomalyDetectionEngine()
    await engine.initialize()
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Create a statistical detector for CPU usage
    detector = StatisticalDetector(
        anomaly_type=AnomalyType.SYSTEM_CPU,
        strategy=DetectionStrategy.STATISTICAL_ZSCORE,
        metric_name="system_cpu_usage",
        threshold=2.0
    )
    
    # Register the detector
    detector_id = await engine.register_detector(detector)
    
    # Generate training data
    logger.info("Generating training data")
    timestamps = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(days=7),
        end=datetime.datetime.now(),
        freq="1h"
    )
    
    # Normal CPU usage: 20-40%
    values = 0.3 + 0.1 * np.random.randn(len(timestamps))
    values = np.clip(values, 0.1, 0.9)  # Ensure values are between 10% and 90%
    
    # Create DataFrame
    train_df = pd.DataFrame({
        "timestamp": timestamps,
        "system_cpu_usage": values
    })
    train_df.set_index("timestamp", inplace=True)
    
    # Train the detector
    logger.info(f"Training detector {detector_id}")
    await engine.train_detector(detector_id, train_df)
    
    # Generate test data with some anomalies
    logger.info("Generating test data with anomalies")
    normal_points = [
        {"system_cpu_usage": 0.35, "timestamp": datetime.datetime.now()},
        {"system_cpu_usage": 0.42, "timestamp": datetime.datetime.now()},
        {"system_cpu_usage": 0.28, "timestamp": datetime.datetime.now()},
    ]
    
    anomaly_points = [
        {"system_cpu_usage": 0.95, "timestamp": datetime.datetime.now()},  # High CPU spike
        {"system_cpu_usage": 0.05, "timestamp": datetime.datetime.now()},  # Unusually low CPU
    ]
    
    # Process normal points
    logger.info("Processing normal data points")
    for point in normal_points:
        alerts = await engine.process_data_point(point)
        if not alerts:
            logger.info(f"No anomalies detected for CPU usage: {point['system_cpu_usage']:.2f}")
    
    # Process anomaly points
    logger.info("Processing anomaly data points")
    for point in anomaly_points:
        alerts = await engine.process_data_point(point)
        if not alerts:
            logger.info(f"No anomalies detected for CPU usage: {point['system_cpu_usage']:.2f}")
    
    logger.info("Statistical detector example completed")


async def example_learning_based_detector():
    """Example of using a learning-based detector."""
    logger.info("Starting learning-based detector example")
    
    try:
        import sklearn
    except ImportError:
        logger.error("scikit-learn not available, learning-based detector example skipped")
        return
    
    # Create an anomaly detection engine
    engine = AnomalyDetectionEngine()
    await engine.initialize()
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Create a learning-based detector for transaction amounts
    detector = LearningBasedDetector(
        anomaly_type=AnomalyType.USER_TRANSACTION_PATTERN,
        strategy=DetectionStrategy.LEARNING_ISOLATION_FOREST,
        metric_name="transaction_amount",
        threshold=1.5,
        contamination=0.05
    )
    
    # Register the detector
    detector_id = await engine.register_detector(detector)
    
    # Generate training data
    logger.info("Generating training data")
    timestamps = pd.date_range(
        start=datetime.datetime.now() - datetime.timedelta(days=30),
        end=datetime.datetime.now(),
        freq="1h"
    )
    
    # Normal transaction pattern: mean=100, std=20
    values = 100 + 20 * np.random.randn(len(timestamps))
    values = np.abs(values)  # Ensure positive
    
    # Create DataFrame
    train_df = pd.DataFrame({
        "timestamp": timestamps,
        "transaction_amount": values,
        "hour": [ts.hour for ts in timestamps],
        "day_of_week": [ts.dayofweek for ts in timestamps]
    })
    train_df.set_index("timestamp", inplace=True)
    
    # Train the detector
    logger.info(f"Training detector {detector_id}")
    await engine.train_detector(detector_id, train_df)
    
    # Generate test data with some anomalies
    logger.info("Generating test data with anomalies")
    test_time = datetime.datetime.now()
    
    normal_points = [
        {
            "transaction_amount": 105.0,
            "timestamp": test_time,
            "hour": test_time.hour,
            "day_of_week": test_time.weekday()
        },
        {
            "transaction_amount": 87.5,
            "timestamp": test_time,
            "hour": test_time.hour,
            "day_of_week": test_time.weekday()
        },
        {
            "transaction_amount": 122.3,
            "timestamp": test_time,
            "hour": test_time.hour,
            "day_of_week": test_time.weekday()
        },
    ]
    
    anomaly_points = [
        {
            "transaction_amount": 1500.0,  # Unusually high transaction
            "timestamp": test_time,
            "hour": test_time.hour,
            "day_of_week": test_time.weekday()
        },
        {
            "transaction_amount": 0.5,  # Unusually low transaction
            "timestamp": test_time,
            "hour": test_time.hour,
            "day_of_week": test_time.weekday()
        },
    ]
    
    # Process normal points
    logger.info("Processing normal data points")
    for point in normal_points:
        alerts = await engine.process_data_point(point)
        if not alerts:
            logger.info(f"No anomalies detected for transaction amount: {point['transaction_amount']:.2f}")
    
    # Process anomaly points
    logger.info("Processing anomaly data points")
    for point in anomaly_points:
        alerts = await engine.process_data_point(point)
        if not alerts:
            logger.info(f"No anomalies detected for transaction amount: {point['transaction_amount']:.2f}")
    
    logger.info("Learning-based detector example completed")


async def example_system_monitoring():
    """Example of system monitoring integration."""
    logger.info("Starting system monitoring example")
    
    # Create an anomaly detection engine
    engine = AnomalyDetectionEngine()
    await engine.initialize()
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Create system monitoring integration
    monitor = SystemMonitorIntegration(
        engine=engine,
        metrics_source="prometheus",  # Placeholder, no actual Prometheus connection
        poll_interval=5,  # seconds
        alert_handlers=[alert_handler]
    )
    
    # Start monitoring
    await monitor.start()
    
    # Generate some synthetic training data
    logger.info("Generating synthetic training data")
    await monitor.train_detectors(days=7)
    
    # Run for a short time to collect metrics
    logger.info("Running system monitoring for 10 seconds")
    await asyncio.sleep(10)
    
    # Stop monitoring
    await monitor.stop()
    
    logger.info("System monitoring example completed")


async def example_user_behavior_monitoring():
    """Example of user behavior monitoring integration."""
    logger.info("Starting user behavior monitoring example")
    
    # Create an anomaly detection engine
    engine = AnomalyDetectionEngine()
    await engine.initialize()
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Create user behavior monitoring integration
    monitor = UserBehaviorIntegration(
        engine=engine,
        data_source="logs",  # Placeholder, no actual log parsing
        poll_interval=5,  # seconds
        alert_handlers=[alert_handler]
    )
    
    # Start monitoring
    await monitor.start()
    
    # Generate some synthetic training data
    logger.info("Generating synthetic training data")
    await monitor.train_detectors(days=7)
    
    # Run for a short time to collect metrics
    logger.info("Running user behavior monitoring for 10 seconds")
    await asyncio.sleep(10)
    
    # Stop monitoring
    await monitor.stop()
    
    logger.info("User behavior monitoring example completed")


async def example_data_quality_monitoring():
    """Example of data quality monitoring integration."""
    logger.info("Starting data quality monitoring example")
    
    # Create an anomaly detection engine
    engine = AnomalyDetectionEngine()
    await engine.initialize()
    
    # Register an alert handler
    await engine.register_alert_handler(alert_handler)
    
    # Create data quality monitoring integration
    monitor = DataQualityIntegration(
        engine=engine,
        data_source="database",  # Placeholder, no actual database connection
        tables=["users", "transactions", "products"],  # Example tables
        poll_interval=5,  # seconds
        alert_handlers=[alert_handler]
    )
    
    # Start monitoring
    await monitor.start()
    
    # Generate some synthetic training data
    logger.info("Generating synthetic training data")
    await monitor.train_detectors(days=7)
    
    # Run for a short time to collect metrics
    logger.info("Running data quality monitoring for 10 seconds")
    await asyncio.sleep(10)
    
    # Stop monitoring
    await monitor.stop()
    
    logger.info("Data quality monitoring example completed")


async def main():
    """Run the examples."""
    logger.info("Starting anomaly detection examples")
    
    # Run examples
    await example_statistical_detector()
    await example_learning_based_detector()
    await example_system_monitoring()
    await example_user_behavior_monitoring()
    await example_data_quality_monitoring()
    
    # For FastAPI example, uncomment this (it runs indefinitely)
    # await example_fastapi_integration()
    
    logger.info("All examples completed")


if __name__ == "__main__":
    asyncio.run(main())