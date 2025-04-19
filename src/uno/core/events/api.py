"""
REST API for the event subscription management system.

This module provides FastAPI endpoints for interacting with the event subscription
management system, allowing for CRUD operations on subscriptions and monitoring.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel

from uno.core.protocols.event import EventBusProtocol
from uno.core.errors import Error, NotFoundError
from uno.core.events.subscription import (
    SubscriptionManager, 
    SubscriptionConfig, 
    SubscriptionInfo,
    EventTypeInfo,
    SubscriptionMetrics
)


# Input and response models
class SubscriptionCreateRequest(BaseModel):
    """Input model for creating a subscription."""
    
    event_type: str
    handler_name: str
    handler_module: str
    handler_function: Optional[str] = None
    description: str = ""
    is_active: bool = True
    is_async: bool = True
    max_retries: int = 3
    retry_delay_ms: int = 1000
    timeout_ms: int = 30000  # 30 seconds
    filter_expression: Optional[str] = None
    batch_size: int = 1
    batch_interval_ms: int = 0
    requires_permissions: List[str] = []
    alert_on_failure: bool = False
    alert_threshold: float = 0.8


class SubscriptionUpdateRequest(BaseModel):
    """Input model for updating a subscription."""
    
    event_type: Optional[str] = None
    handler_name: Optional[str] = None
    handler_module: Optional[str] = None
    handler_function: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_async: Optional[bool] = None
    max_retries: Optional[int] = None
    retry_delay_ms: Optional[int] = None
    timeout_ms: Optional[int] = None
    filter_expression: Optional[str] = None
    batch_size: Optional[int] = None
    batch_interval_ms: Optional[int] = None
    requires_permissions: Optional[List[str]] = None
    alert_on_failure: Optional[bool] = None
    alert_threshold: Optional[float] = None


class SubscriptionResponse(BaseModel):
    """API response model for a subscription."""
    
    subscription_id: str
    event_type: str
    handler_name: str
    handler_module: str
    handler_function: Optional[str] = None
    description: str
    is_active: bool
    is_async: bool
    created_at: datetime
    updated_at: datetime
    max_retries: int
    retry_delay_ms: int
    timeout_ms: int
    filter_expression: Optional[str] = None
    batch_size: int
    batch_interval_ms: int
    requires_permissions: List[str]
    alert_on_failure: bool
    alert_threshold: float
    metrics: Dict[str, Any]


class SubscriptionListResponse(BaseModel):
    """API response model for a list of subscriptions."""
    
    items: List[SubscriptionResponse]
    total: int


class EventTypeResponse(BaseModel):
    """API response model for an event type."""
    
    name: str
    description: str
    schema: Dict[str, Any]
    example: Optional[Dict[str, Any]] = None
    deprecated: bool
    domain: Optional[str] = None


class EventTypeListResponse(BaseModel):
    """API response model for a list of event types."""
    
    items: List[EventTypeResponse]
    total: int


class MetricsResponse(BaseModel):
    """API response model for metrics."""
    
    total_subscriptions: int
    active_subscriptions: int
    event_types_count: int
    handlers_count: int
    invocations: Dict[str, Any]
    avg_processing_time_ms: float
    by_event_type: List[Dict[str, Any]]
    by_handler: List[Dict[str, Any]]


def create_subscription_router(subscription_manager: SubscriptionManager) -> APIRouter:
    """
    Create a FastAPI router for event subscription management.
    
    Args:
        subscription_manager: The subscription manager to use
        
    Returns:
        A FastAPI router with event subscription endpoints
    """
    router = APIRouter(prefix="/events", tags=["events"])
    
    # Helper function to convert subscription model to response
    def subscription_to_response(subscription: SubscriptionInfo) -> SubscriptionResponse:
        metrics_dict = {
            "invocation_count": subscription.metrics.invocation_count,
            "success_count": subscription.metrics.success_count,
            "failure_count": subscription.metrics.failure_count,
            "last_invoked_at": subscription.metrics.last_invoked_at,
            "avg_processing_time_ms": subscription.metrics.avg_processing_time_ms,
            "p95_processing_time_ms": subscription.metrics.p95_processing_time_ms,
            "p99_processing_time_ms": subscription.metrics.p99_processing_time_ms,
            "min_processing_time_ms": subscription.metrics.min_processing_time_ms,
            "max_processing_time_ms": subscription.metrics.max_processing_time_ms
        }
        
        # Calculate success rate
        if subscription.metrics.invocation_count > 0:
            metrics_dict["success_rate"] = subscription.metrics.success_count / subscription.metrics.invocation_count
        else:
            metrics_dict["success_rate"] = 1.0
            
        return SubscriptionResponse(
            subscription_id=subscription.subscription_id,
            event_type=subscription.event_type,
            handler_name=subscription.handler_name,
            handler_module=subscription.handler_module,
            handler_function=subscription.handler_function,
            description=subscription.description,
            is_active=subscription.is_active,
            is_async=subscription.is_async,
            created_at=subscription.created_at,
            updated_at=subscription.updated_at,
            max_retries=subscription.max_retries,
            retry_delay_ms=subscription.retry_delay_ms,
            timeout_ms=subscription.timeout_ms,
            filter_expression=subscription.filter_expression,
            batch_size=subscription.batch_size,
            batch_interval_ms=subscription.batch_interval_ms,
            requires_permissions=subscription.requires_permissions,
            alert_on_failure=subscription.alert_on_failure,
            alert_threshold=subscription.alert_threshold,
            metrics=metrics_dict
        )
    
    # Helper function to handle errors
    def handle_error(result):
        if isinstance(result, Error):
            if isinstance(result.error, NotFoundError):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(result.error))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(result.error))
        return result
    
    @router.get("/subscriptions", response_model=SubscriptionListResponse)
    async def get_subscriptions(
        event_type: Optional[str] = Query(None, description="Filter subscriptions by event type"),
        active_only: bool = Query(False, description="Only return active subscriptions")
    ):
        """Get all subscriptions."""
        subscriptions = await subscription_manager.repository.get_subscriptions(event_type)
        
        if active_only:
            subscriptions = [sub for sub in subscriptions if sub.is_active]
        
        response_items = [subscription_to_response(sub) for sub in subscriptions]
        
        return SubscriptionListResponse(
            items=response_items,
            total=len(response_items)
        )
    
    @router.get("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
    async def get_subscription(subscription_id: str = Path(..., description="ID of the subscription")):
        """Get a subscription by ID."""
        result = await subscription_manager.repository.get_subscription(subscription_id)
        subscription = handle_error(result)
        
        return subscription_to_response(subscription)
    
    @router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
    async def create_subscription(subscription: SubscriptionCreateRequest):
        """Create a new subscription."""
        config = SubscriptionConfig(**subscription.model_dump())
        result = await subscription_manager.create_subscription(config)
        new_subscription = handle_error(result)
        
        return subscription_to_response(new_subscription)
    
    @router.patch("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
    async def update_subscription(
        update: SubscriptionUpdateRequest,
        subscription_id: str = Path(..., description="ID of the subscription")
    ):
        """Update a subscription."""
        # Convert to SubscriptionConfig, only including set fields
        config_data = {k: v for k, v in update.model_dump().items() if v is not None}
        config = SubscriptionConfig(subscription_id=subscription_id, **config_data)
        
        result = await subscription_manager.update_subscription(subscription_id, config)
        updated_subscription = handle_error(result)
        
        return subscription_to_response(updated_subscription)
    
    @router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_subscription(subscription_id: str = Path(..., description="ID of the subscription")):
        """Delete a subscription."""
        result = await subscription_manager.delete_subscription(subscription_id)
        handle_error(result)
        
        return None
    
    @router.get("/types", response_model=EventTypeListResponse)
    async def get_event_types():
        """Get all registered event types."""
        event_types = await subscription_manager.repository.get_event_types()
        
        return EventTypeListResponse(
            items=event_types,
            total=len(event_types)
        )
    
    @router.get("/types/{name}", response_model=EventTypeResponse)
    async def get_event_type(name: str = Path(..., description="Name of the event type")):
        """Get an event type by name."""
        result = await subscription_manager.repository.get_event_type(name)
        event_type = handle_error(result)
        
        return event_type
    
    @router.post("/types", response_model=EventTypeResponse, status_code=status.HTTP_201_CREATED)
    async def register_event_type(event_type: EventTypeInfo):
        """Register a new event type."""
        registered = await subscription_manager.repository.register_event_type(event_type)
        
        return registered
    
    @router.get("/metrics", response_model=MetricsResponse)
    async def get_metrics():
        """Get overall metrics for event subscriptions."""
        metrics = await subscription_manager.get_metrics()
        
        return metrics
    
    return router