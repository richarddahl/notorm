"""
API integration for anomaly detection.

This module provides FastAPI integration for the anomaly detection system,
including endpoints for retrieving alerts, managing detectors, and visualizing anomalies.
"""

import datetime
from typing import Any, Dict, List, Optional, Set, Tuple, Union, cast

from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from uno.ai.anomaly_detection.engine import (
    AnomalyDetectionEngine,
    AnomalyType,
    DetectionStrategy,
    AnomalyAlert,
    AlertSeverity,
)


class DetectorConfigRequest(BaseModel):
    """Request model for creating or updating a detector."""
    
    anomaly_type: AnomalyType
    strategy: DetectionStrategy
    metric_name: str
    training_window: int = Field(default=30, description="Training window in days")
    threshold: float = Field(default=2.0, description="Anomaly detection threshold")
    min_data_points: int = Field(default=100, description="Minimum data points required for training")
    params: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")


class DataPointRequest(BaseModel):
    """Request model for processing a data point."""
    
    timestamp: Optional[datetime.datetime] = None
    metrics: Dict[str, float]
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class BatchDataRequest(BaseModel):
    """Request model for processing a batch of data points."""
    
    data_points: List[DataPointRequest]


class TrainRequest(BaseModel):
    """Request model for training detectors."""
    
    detector_ids: Optional[List[str]] = None
    historical_data: Optional[Dict[str, List[Dict[str, Any]]]] = None
    use_stored_data: bool = True
    days: int = Field(default=30, description="Days of historical data to use")


class AnomalyAlertResponse(BaseModel):
    """Response model for anomaly alerts."""
    
    id: str
    timestamp: datetime.datetime
    anomaly_type: str
    detection_strategy: str
    severity: str
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    metric_name: str
    metric_value: float
    expected_range: Dict[str, float]
    deviation_factor: float
    description: str
    suggestion: Optional[str] = None
    metadata: Dict[str, Any]
    is_critical: bool


def create_anomaly_detection_router(
    engine: AnomalyDetectionEngine,
    path_prefix: str = "/anomalies"
) -> APIRouter:
    """
    Create a FastAPI router for anomaly detection.
    
    Args:
        engine: The anomaly detection engine
        path_prefix: Prefix for API routes
        
    Returns:
        FastAPI router with anomaly detection endpoints
    """
    router = APIRouter(prefix=path_prefix, tags=["anomaly-detection"])
    
    @router.post("/detectors", response_model=Dict[str, str])
    async def create_detector(request: DetectorConfigRequest):
        """Create a new anomaly detector."""
        try:
            from uno.ai.anomaly_detection.detectors import (
                StatisticalDetector,
                LearningBasedDetector,
                HybridDetector
            )
            
            # Create the appropriate detector type
            if request.strategy.value.startswith("statistical_"):
                detector = StatisticalDetector(
                    anomaly_type=request.anomaly_type,
                    strategy=request.strategy,
                    metric_name=request.metric_name,
                    training_window=request.training_window,
                    threshold=request.threshold,
                    min_data_points=request.min_data_points,
                    params=request.params
                )
            elif request.strategy.value.startswith("learning_"):
                detector = LearningBasedDetector(
                    anomaly_type=request.anomaly_type,
                    strategy=request.strategy,
                    metric_name=request.metric_name,
                    training_window=request.training_window,
                    threshold=request.threshold,
                    min_data_points=request.min_data_points,
                    params=request.params
                )
            elif request.strategy.value.startswith("hybrid_"):
                detector = HybridDetector(
                    anomaly_type=request.anomaly_type,
                    strategy=request.strategy,
                    metric_name=request.metric_name,
                    training_window=request.training_window,
                    threshold=request.threshold,
                    min_data_points=request.min_data_points,
                    params=request.params
                )
            else:
                raise ValueError(f"Unsupported strategy: {request.strategy}")
            
            # Register the detector
            detector_id = await engine.register_detector(detector)
            
            return {"detector_id": detector_id}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create detector: {str(e)}")
    
    @router.delete("/detectors/{detector_id}", response_model=Dict[str, bool])
    async def delete_detector(detector_id: str):
        """Unregister an anomaly detector."""
        try:
            success = await engine.unregister_detector(detector_id)
            
            if not success:
                raise HTTPException(status_code=404, detail=f"Detector not found: {detector_id}")
            
            return {"success": success}
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete detector: {str(e)}")
    
    @router.get("/detectors", response_model=Dict[str, Dict[str, Any]])
    async def get_detectors():
        """Get metrics for all registered detectors."""
        try:
            return await engine.get_detector_metrics()
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get detectors: {str(e)}")
    
    @router.post("/data-point", response_model=List[AnomalyAlertResponse])
    async def process_data_point(request: DataPointRequest):
        """Process a single data point for anomaly detection."""
        try:
            # Convert request to data point
            data_point = {
                "timestamp": request.timestamp or datetime.datetime.now(),
                "entity_id": request.entity_id,
                "entity_type": request.entity_type,
                **(request.metadata or {})
            }
            
            # Add metrics
            data_point.update(request.metrics)
            
            # Process the data point
            alerts = await engine.process_data_point(data_point)
            
            # Convert to response format
            return [
                AnomalyAlertResponse(
                    id=alert.id,
                    timestamp=alert.timestamp,
                    anomaly_type=alert.anomaly_type.value,
                    detection_strategy=alert.detection_strategy.value,
                    severity=alert.severity.value,
                    entity_id=alert.entity_id,
                    entity_type=alert.entity_type,
                    metric_name=alert.metric_name,
                    metric_value=alert.metric_value,
                    expected_range=alert.expected_range,
                    deviation_factor=alert.deviation_factor,
                    description=alert.description,
                    suggestion=alert.suggestion,
                    metadata=alert.metadata,
                    is_critical=alert.is_critical
                )
                for alert in alerts
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process data point: {str(e)}")
    
    @router.post("/batch", response_model=List[AnomalyAlertResponse])
    async def process_batch(request: BatchDataRequest):
        """Process a batch of data points for anomaly detection."""
        try:
            all_alerts = []
            
            # Process each data point
            for point_request in request.data_points:
                # Convert request to data point
                data_point = {
                    "timestamp": point_request.timestamp or datetime.datetime.now(),
                    "entity_id": point_request.entity_id,
                    "entity_type": point_request.entity_type,
                    **(point_request.metadata or {})
                }
                
                # Add metrics
                data_point.update(point_request.metrics)
                
                # Process the data point
                alerts = await engine.process_data_point(data_point)
                all_alerts.extend(alerts)
            
            # Convert to response format
            return [
                AnomalyAlertResponse(
                    id=alert.id,
                    timestamp=alert.timestamp,
                    anomaly_type=alert.anomaly_type.value,
                    detection_strategy=alert.detection_strategy.value,
                    severity=alert.severity.value,
                    entity_id=alert.entity_id,
                    entity_type=alert.entity_type,
                    metric_name=alert.metric_name,
                    metric_value=alert.metric_value,
                    expected_range=alert.expected_range,
                    deviation_factor=alert.deviation_factor,
                    description=alert.description,
                    suggestion=alert.suggestion,
                    metadata=alert.metadata,
                    is_critical=alert.is_critical
                )
                for alert in all_alerts
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process batch: {str(e)}")
    
    @router.post("/train", response_model=Dict[str, bool])
    async def train_detectors(request: TrainRequest, background_tasks: BackgroundTasks):
        """Train detectors on historical data."""
        try:
            # This could be a long-running operation, so run in background
            background_tasks.add_task(
                _train_detectors_task,
                engine,
                request.detector_ids,
                request.historical_data,
                request.use_stored_data,
                request.days
            )
            
            return {"success": True, "message": "Training started in background"}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to start training: {str(e)}")
    
    @router.get("/alerts", response_model=List[AnomalyAlertResponse])
    async def get_alerts(
        start_time: Optional[datetime.datetime] = None,
        end_time: Optional[datetime.datetime] = None,
        anomaly_types: Optional[List[AnomalyType]] = Query(None),
        severities: Optional[List[AlertSeverity]] = Query(None),
        entity_id: Optional[str] = None,
        entity_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ):
        """Get anomaly alerts from the alert store."""
        try:
            alerts = await engine.get_alerts(
                start_time=start_time,
                end_time=end_time,
                anomaly_types=anomaly_types,
                severities=severities,
                entity_id=entity_id,
                entity_type=entity_type,
                limit=limit,
                offset=offset
            )
            
            # Convert to response format
            return [
                AnomalyAlertResponse(
                    id=alert.id,
                    timestamp=alert.timestamp,
                    anomaly_type=alert.anomaly_type.value,
                    detection_strategy=alert.detection_strategy.value,
                    severity=alert.severity.value,
                    entity_id=alert.entity_id,
                    entity_type=alert.entity_type,
                    metric_name=alert.metric_name,
                    metric_value=alert.metric_value,
                    expected_range=alert.expected_range,
                    deviation_factor=alert.deviation_factor,
                    description=alert.description,
                    suggestion=alert.suggestion,
                    metadata=alert.metadata,
                    is_critical=alert.is_critical
                )
                for alert in alerts
            ]
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")
    
    return router


async def _train_detectors_task(
    engine: AnomalyDetectionEngine,
    detector_ids: Optional[List[str]],
    historical_data: Optional[Dict[str, List[Dict[str, Any]]]],
    use_stored_data: bool,
    days: int
):
    """
    Background task to train detectors.
    
    Args:
        engine: The anomaly detection engine
        detector_ids: Optional list of detector IDs to train
        historical_data: Optional historical data for training
        use_stored_data: Whether to use stored data from the database
        days: Number of days of historical data to use
    """
    try:
        if historical_data:
            # Convert to pandas DataFrames
            import pandas as pd
            
            data_frames = {}
            for metric_name, data_points in historical_data.items():
                df = pd.DataFrame(data_points)
                if "timestamp" in df.columns:
                    df["timestamp"] = pd.to_datetime(df["timestamp"])
                    df.set_index("timestamp", inplace=True)
                data_frames[metric_name] = df
            
            # Train specific detectors
            if detector_ids:
                for detector_id in detector_ids:
                    if detector_id in engine.detectors:
                        detector = engine.detectors[detector_id]
                        metric_name = detector.metric_name
                        
                        if metric_name in data_frames:
                            await engine.train_detector(detector_id, data_frames[metric_name])
            else:
                # Train all detectors with available data
                await engine.train_all_detectors(data_frames)
        
        elif use_stored_data:
            # This would fetch data from the database or other sources
            # Implementation depends on how historical data is stored
            # For now, we'll just log that this would be implemented
            if engine.logger:
                engine.logger.info(f"Training detectors with {days} days of stored data")
    
    except Exception as e:
        if engine.logger:
            engine.logger.error(f"Error training detectors: {e}")


def integrate_anomaly_detection(
    app,
    connection_string: str,
    alert_store_table: str = "anomaly_alerts",
    config_store_table: str = "anomaly_detector_config",
    path_prefix: str = "/api/anomalies"
):
    """
    Integrate anomaly detection into a FastAPI application.
    
    Args:
        app: FastAPI application
        connection_string: Database connection string
        alert_store_table: Table name for storing alerts
        config_store_table: Table name for storing detector configurations
        path_prefix: Prefix for API routes
    """
    # Create anomaly detection engine
    engine = AnomalyDetectionEngine(
        connection_string=connection_string,
        alert_store_table=alert_store_table,
        config_store_table=config_store_table
    )
    
    # Create router
    router = create_anomaly_detection_router(
        engine=engine,
        path_prefix=path_prefix
    )
    
    # Add router to app
    app.include_router(router)
    
    # Initialize on startup
    @app.on_event("startup")
    async def startup():
        await engine.initialize()
    
    # Close on shutdown
    @app.on_event("shutdown")
    async def shutdown():
        await engine.close()
    
    return engine