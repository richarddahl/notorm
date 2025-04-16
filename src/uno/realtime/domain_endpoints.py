"""
Domain endpoints for the Realtime module.

This module defines FastAPI endpoints for the Realtime module.
"""

from typing import Dict, List, Optional, Any, Union, Annotated
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator

from uno.core.result import Result
from uno.dependencies.service import inject_dependency
from uno.realtime.domain_services import (
    NotificationServiceProtocol,
    SubscriptionServiceProtocol,
    ConnectionServiceProtocol,
    WebSocketServiceProtocol,
    SSEServiceProtocol,
    RealtimeService
)
from uno.realtime.domain_provider import (
    get_notification_service,
    get_subscription_service,
    get_connection_service,
    get_websocket_service,
    get_sse_service,
    get_realtime_service
)
from uno.realtime.entities import (
    NotificationId,
    SubscriptionId,
    ConnectionId,
    UserId,
    NotificationType,
    NotificationPriority,
    NotificationStatus,
    SubscriptionType,
    SubscriptionStatus,
    EventPriority
)


# DTOs
class NotificationDTO(BaseModel):
    """DTO for notifications."""
    
    id: str = Field(..., description="Notification ID")
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    type: str = Field(..., description="Notification type")
    priority: str = Field(..., description="Notification priority")
    status: str = Field(..., description="Notification status")
    recipients: List[str] = Field(..., description="Recipient user IDs")
    sender_id: Optional[str] = Field(None, description="Sender user ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    delivered_at: Optional[datetime] = Field(None, description="Delivery timestamp")
    read_by: List[str] = Field(default_factory=list, description="Users who read the notification")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Available actions")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CreateNotificationDTO(BaseModel):
    """DTO for creating notifications."""
    
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message")
    recipients: List[str] = Field(..., description="Recipient user IDs")
    type: str = Field("system", description="Notification type")
    priority: str = Field("normal", description="Notification priority")
    sender_id: Optional[str] = Field(None, description="Sender user ID")
    resource_type: Optional[str] = Field(None, description="Resource type")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    actions: List[Dict[str, Any]] = Field(default_factory=list, description="Available actions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class SubscriptionDTO(BaseModel):
    """DTO for subscriptions."""
    
    id: str = Field(..., description="Subscription ID")
    user_id: str = Field(..., description="User ID")
    type: str = Field(..., description="Subscription type")
    status: str = Field(..., description="Subscription status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    resource_id: Optional[str] = Field(None, description="Resource ID")
    resource_type: Optional[str] = Field(None, description="Resource type")
    topic: Optional[str] = Field(None, description="Topic name")
    query: Optional[Dict[str, Any]] = Field(None, description="Query parameters")
    labels: List[str] = Field(default_factory=list, description="Subscription labels")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class CreateResourceSubscriptionDTO(BaseModel):
    """DTO for creating resource subscriptions."""
    
    user_id: str = Field(..., description="User ID")
    resource_id: str = Field(..., description="Resource ID")
    resource_type: Optional[str] = Field(None, description="Resource type")
    labels: Optional[List[str]] = Field(None, description="Subscription labels")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")


class CreateTopicSubscriptionDTO(BaseModel):
    """DTO for creating topic subscriptions."""
    
    user_id: str = Field(..., description="User ID")
    topic: str = Field(..., description="Topic name")
    labels: Optional[List[str]] = Field(None, description="Subscription labels")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    expires_at: Optional[datetime] = Field(None, description="Expiration timestamp")
    payload_filter: Optional[Dict[str, Any]] = Field(None, description="Payload filter")


class UpdateSubscriptionStatusDTO(BaseModel):
    """DTO for updating subscription status."""
    
    status: str = Field(..., description="New subscription status")


class EventDTO(BaseModel):
    """DTO for SSE events."""
    
    id: str = Field(..., description="Event ID")
    event: str = Field(..., description="Event name")
    data: str = Field(..., description="Event data")
    priority: str = Field("normal", description="Event priority")
    retry: Optional[int] = Field(None, description="Retry interval in milliseconds")
    comment: Optional[str] = Field(None, description="Event comment")


class CreateEventDTO(BaseModel):
    """DTO for creating SSE events."""
    
    event: str = Field(..., description="Event name")
    data: str = Field(..., description="Event data")
    priority: str = Field("normal", description="Event priority")
    retry: Optional[int] = Field(None, description="Retry interval in milliseconds")
    comment: Optional[str] = Field(None, description="Event comment")


class BroadcastEventDTO(BaseModel):
    """DTO for broadcasting SSE events."""
    
    event: str = Field(..., description="Event name")
    data: str = Field(..., description="Event data")
    priority: str = Field("normal", description="Event priority")
    recipients: Optional[List[str]] = Field(None, description="Recipient connection IDs")
    exclude: Optional[List[str]] = Field(None, description="Connection IDs to exclude")


# Endpoints
def create_realtime_router() -> APIRouter:
    """
    Create FastAPI router for realtime endpoints.
    
    Returns:
        FastAPI router
    """
    router = APIRouter(
        prefix="/api/realtime",
        tags=["realtime"],
        responses={401: {"description": "Unauthorized"}},
    )
    
    # Notification endpoints
    @router.post(
        "/notifications",
        response_model=NotificationDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create notification",
        description="Create a new notification for one or more users"
    )
    async def create_notification(
        request: CreateNotificationDTO,
        notification_service: NotificationServiceProtocol = Depends(get_notification_service),
        websocket_service: WebSocketServiceProtocol = Depends(get_websocket_service)
    ) -> NotificationDTO:
        """Create a new notification."""
        try:
            # Convert DTOs to domain objects
            recipients = [UserId(user_id) for user_id in request.recipients]
            sender_id = UserId(request.sender_id) if request.sender_id else None
            
            # Create notification
            notification_result = await notification_service.create_notification(
                title=request.title,
                message=request.message,
                recipients=recipients,
                type_=NotificationType(request.type),
                priority=NotificationPriority(request.priority),
                sender_id=sender_id,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                actions=request.actions,
                metadata=request.metadata,
                expires_at=request.expires_at
            )
            
            if notification_result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=notification_result.error
                )
            
            notification = notification_result.value
            
            # Send notification via WebSocket to connected recipients
            await websocket_service.send_notification(notification)
            
            # Mark as delivered since we tried to deliver it
            await notification_service.mark_as_delivered(notification.id)
            
            # Convert to DTO
            return NotificationDTO(
                id=notification.id.value,
                title=notification.title,
                message=notification.message,
                type=notification.type.value,
                priority=notification.priority.value,
                status=notification.status.value,
                recipients=[r.value for r in notification.recipients],
                sender_id=notification.sender_id.value if notification.sender_id else None,
                created_at=notification.created_at,
                delivered_at=notification.delivered_at,
                read_by=[r.value for r in notification.read_by],
                actions=notification.actions,
                resource_type=notification.resource_type,
                resource_id=notification.resource_id,
                metadata=notification.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/notifications",
        response_model=List[NotificationDTO],
        summary="Get user notifications",
        description="Get notifications for a specific user"
    )
    async def get_user_notifications(
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        notification_service: NotificationServiceProtocol = Depends(get_notification_service)
    ) -> List[NotificationDTO]:
        """Get notifications for a specific user."""
        try:
            # Get notifications
            status_enum = NotificationStatus(status) if status else None
            result = await notification_service.get_user_notifications(
                UserId(user_id),
                status=status_enum,
                page=page,
                page_size=page_size
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            # Convert to DTOs
            return [
                NotificationDTO(
                    id=notification.id.value,
                    title=notification.title,
                    message=notification.message,
                    type=notification.type.value,
                    priority=notification.priority.value,
                    status=notification.status.value,
                    recipients=[r.value for r in notification.recipients],
                    sender_id=notification.sender_id.value if notification.sender_id else None,
                    created_at=notification.created_at,
                    delivered_at=notification.delivered_at,
                    read_by=[r.value for r in notification.read_by],
                    actions=notification.actions,
                    resource_type=notification.resource_type,
                    resource_id=notification.resource_id,
                    metadata=notification.metadata
                )
                for notification in result.value
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/notifications/{notification_id}",
        response_model=NotificationDTO,
        summary="Get notification",
        description="Get a specific notification by ID"
    )
    async def get_notification(
        notification_id: str,
        notification_service: NotificationServiceProtocol = Depends(get_notification_service)
    ) -> NotificationDTO:
        """Get a specific notification by ID."""
        try:
            # Get notification
            result = await notification_service.get_notification(NotificationId(notification_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            notification = result.value
            
            # Convert to DTO
            return NotificationDTO(
                id=notification.id.value,
                title=notification.title,
                message=notification.message,
                type=notification.type.value,
                priority=notification.priority.value,
                status=notification.status.value,
                recipients=[r.value for r in notification.recipients],
                sender_id=notification.sender_id.value if notification.sender_id else None,
                created_at=notification.created_at,
                delivered_at=notification.delivered_at,
                read_by=[r.value for r in notification.read_by],
                actions=notification.actions,
                resource_type=notification.resource_type,
                resource_id=notification.resource_id,
                metadata=notification.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/notifications/{notification_id}/mark-read",
        response_model=NotificationDTO,
        summary="Mark notification as read",
        description="Mark a notification as read by a specific user"
    )
    async def mark_notification_as_read(
        notification_id: str,
        user_id: str,
        notification_service: NotificationServiceProtocol = Depends(get_notification_service)
    ) -> NotificationDTO:
        """Mark a notification as read by a specific user."""
        try:
            # Mark as read
            result = await notification_service.mark_as_read(
                NotificationId(notification_id),
                UserId(user_id)
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            notification = result.value
            
            # Convert to DTO
            return NotificationDTO(
                id=notification.id.value,
                title=notification.title,
                message=notification.message,
                type=notification.type.value,
                priority=notification.priority.value,
                status=notification.status.value,
                recipients=[r.value for r in notification.recipients],
                sender_id=notification.sender_id.value if notification.sender_id else None,
                created_at=notification.created_at,
                delivered_at=notification.delivered_at,
                read_by=[r.value for r in notification.read_by],
                actions=notification.actions,
                resource_type=notification.resource_type,
                resource_id=notification.resource_id,
                metadata=notification.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/notifications/unread-count/{user_id}",
        response_model=int,
        summary="Get unread count",
        description="Get the count of unread notifications for a user"
    )
    async def get_unread_count(
        user_id: str,
        notification_service: NotificationServiceProtocol = Depends(get_notification_service)
    ) -> int:
        """Get the count of unread notifications for a user."""
        try:
            # Get unread count
            result = await notification_service.get_unread_count(UserId(user_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            return result.value
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Subscription endpoints
    @router.post(
        "/subscriptions/resource",
        response_model=SubscriptionDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create resource subscription",
        description="Create a new subscription to a specific resource"
    )
    async def create_resource_subscription(
        request: CreateResourceSubscriptionDTO,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> SubscriptionDTO:
        """Create a new subscription to a specific resource."""
        try:
            # Convert to domain values
            user_id = UserId(request.user_id)
            labels = set(request.labels) if request.labels else set()
            
            # Create subscription
            result = await subscription_service.create_resource_subscription(
                user_id=user_id,
                resource_id=request.resource_id,
                resource_type=request.resource_type,
                labels=labels,
                metadata=request.metadata,
                expires_at=request.expires_at
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            subscription = result.value
            
            # Convert to DTO
            return SubscriptionDTO(
                id=subscription.id.value,
                user_id=subscription.user_id.value,
                type=subscription.type.value,
                status=subscription.status.value,
                created_at=subscription.created_at,
                updated_at=subscription.updated_at,
                expires_at=subscription.expires_at,
                resource_id=subscription.resource_id,
                resource_type=subscription.resource_type,
                topic=subscription.topic,
                query=subscription.query,
                labels=list(subscription.labels),
                metadata=subscription.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.post(
        "/subscriptions/topic",
        response_model=SubscriptionDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create topic subscription",
        description="Create a new subscription to a topic"
    )
    async def create_topic_subscription(
        request: CreateTopicSubscriptionDTO,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> SubscriptionDTO:
        """Create a new subscription to a topic."""
        try:
            # Convert to domain values
            user_id = UserId(request.user_id)
            labels = set(request.labels) if request.labels else set()
            
            # Create subscription
            result = await subscription_service.create_topic_subscription(
                user_id=user_id,
                topic=request.topic,
                labels=labels,
                metadata=request.metadata,
                expires_at=request.expires_at,
                payload_filter=request.payload_filter
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            subscription = result.value
            
            # Convert to DTO
            return SubscriptionDTO(
                id=subscription.id.value,
                user_id=subscription.user_id.value,
                type=subscription.type.value,
                status=subscription.status.value,
                created_at=subscription.created_at,
                updated_at=subscription.updated_at,
                expires_at=subscription.expires_at,
                resource_id=subscription.resource_id,
                resource_type=subscription.resource_type,
                topic=subscription.topic,
                query=subscription.query,
                labels=list(subscription.labels),
                metadata=subscription.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/subscriptions",
        response_model=List[SubscriptionDTO],
        summary="Get user subscriptions",
        description="Get subscriptions for a specific user"
    )
    async def get_user_subscriptions(
        user_id: str,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> List[SubscriptionDTO]:
        """Get subscriptions for a specific user."""
        try:
            # Get subscriptions
            status_enum = SubscriptionStatus(status) if status else None
            result = await subscription_service.get_user_subscriptions(
                UserId(user_id),
                status=status_enum,
                page=page,
                page_size=page_size
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            # Convert to DTOs
            return [
                SubscriptionDTO(
                    id=subscription.id.value,
                    user_id=subscription.user_id.value,
                    type=subscription.type.value,
                    status=subscription.status.value,
                    created_at=subscription.created_at,
                    updated_at=subscription.updated_at,
                    expires_at=subscription.expires_at,
                    resource_id=subscription.resource_id,
                    resource_type=subscription.resource_type,
                    topic=subscription.topic,
                    query=subscription.query,
                    labels=list(subscription.labels),
                    metadata=subscription.metadata
                )
                for subscription in result.value
            ]
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.get(
        "/subscriptions/{subscription_id}",
        response_model=SubscriptionDTO,
        summary="Get subscription",
        description="Get a specific subscription by ID"
    )
    async def get_subscription(
        subscription_id: str,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> SubscriptionDTO:
        """Get a specific subscription by ID."""
        try:
            # Get subscription
            result = await subscription_service.get_subscription(SubscriptionId(subscription_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            subscription = result.value
            
            # Convert to DTO
            return SubscriptionDTO(
                id=subscription.id.value,
                user_id=subscription.user_id.value,
                type=subscription.type.value,
                status=subscription.status.value,
                created_at=subscription.created_at,
                updated_at=subscription.updated_at,
                expires_at=subscription.expires_at,
                resource_id=subscription.resource_id,
                resource_type=subscription.resource_type,
                topic=subscription.topic,
                query=subscription.query,
                labels=list(subscription.labels),
                metadata=subscription.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.patch(
        "/subscriptions/{subscription_id}/status",
        response_model=SubscriptionDTO,
        summary="Update subscription status",
        description="Update the status of a subscription"
    )
    async def update_subscription_status(
        subscription_id: str,
        request: UpdateSubscriptionStatusDTO,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> SubscriptionDTO:
        """Update the status of a subscription."""
        try:
            # Update status
            result = await subscription_service.update_subscription_status(
                SubscriptionId(subscription_id),
                SubscriptionStatus(request.status)
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
            
            subscription = result.value
            
            # Convert to DTO
            return SubscriptionDTO(
                id=subscription.id.value,
                user_id=subscription.user_id.value,
                type=subscription.type.value,
                status=subscription.status.value,
                created_at=subscription.created_at,
                updated_at=subscription.updated_at,
                expires_at=subscription.expires_at,
                resource_id=subscription.resource_id,
                resource_type=subscription.resource_type,
                topic=subscription.topic,
                query=subscription.query,
                labels=list(subscription.labels),
                metadata=subscription.metadata
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    @router.delete(
        "/subscriptions/{subscription_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary="Delete subscription",
        description="Delete a subscription"
    )
    async def delete_subscription(
        subscription_id: str,
        subscription_service: SubscriptionServiceProtocol = Depends(get_subscription_service)
    ) -> None:
        """Delete a subscription."""
        try:
            # Delete subscription
            result = await subscription_service.delete_subscription(SubscriptionId(subscription_id))
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=result.error
                )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # SSE endpoint
    @router.get(
        "/events",
        summary="SSE events stream",
        description="Get a Server-Sent Events (SSE) stream"
    )
    async def event_stream(
        request: Request,
        connection_service: ConnectionServiceProtocol = Depends(get_connection_service),
        sse_service: SSEServiceProtocol = Depends(get_sse_service)
    ):
        """Get a Server-Sent Events (SSE) stream."""
        try:
            # Create a connection
            connection_result = await connection_service.create_connection(
                client_info={
                    "ip": request.client.host,
                    "user_agent": request.headers.get("user-agent"),
                    "connection_type": "sse"
                }
            )
            
            if connection_result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=connection_result.error
                )
            
            connection = connection_result.value
            
            # Update connection state
            await connection_service.update_connection_state(connection.id, "connected")
            
            # Get event stream
            stream_result = await sse_service.get_event_stream(connection.id)
            
            if stream_result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=stream_result.error
                )
            
            event_stream = stream_result.value
            
            # Define the event generator function
            async def generate_events():
                try:
                    async for event in event_stream:
                        yield event.to_sse_format()
                except Exception as e:
                    print(f"Error in event stream: {str(e)}")
                finally:
                    # Close connection when stream ends
                    await connection_service.close_connection(connection.id)
            
            # Return streaming response
            return StreamingResponse(
                generate_events(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"
                }
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Event creation endpoint
    @router.post(
        "/events",
        response_model=EventDTO,
        status_code=status.HTTP_201_CREATED,
        summary="Create event",
        description="Create a new SSE event"
    )
    async def create_event(
        request: CreateEventDTO,
        sse_service: SSEServiceProtocol = Depends(get_sse_service)
    ) -> EventDTO:
        """Create a new SSE event."""
        try:
            # Create event
            result = await sse_service.create_event(
                event_type=request.event,
                data=request.data,
                priority=EventPriority(request.priority)
            )
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            event = result.value
            
            # Convert to DTO
            return EventDTO(
                id=event.id,
                event=event.event,
                data=event.data,
                priority=event.priority.value,
                retry=event.retry,
                comment=event.comment
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # Broadcast event endpoint
    @router.post(
        "/events/broadcast",
        response_model=int,
        summary="Broadcast event",
        description="Broadcast an SSE event to multiple connections"
    )
    async def broadcast_event(
        request: BroadcastEventDTO,
        sse_service: SSEServiceProtocol = Depends(get_sse_service)
    ) -> int:
        """Broadcast an SSE event to multiple connections."""
        try:
            # Create event
            event_result = await sse_service.create_event(
                event_type=request.event,
                data=request.data,
                priority=EventPriority(request.priority)
            )
            
            if event_result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=event_result.error
                )
            
            event = event_result.value
            
            # Convert connection IDs
            recipients = [ConnectionId(conn_id) for conn_id in (request.recipients or [])]
            exclude = [ConnectionId(conn_id) for conn_id in (request.exclude or [])]
            
            # Broadcast event
            result = await sse_service.broadcast_event(event, recipients, exclude)
            
            if result.is_failure():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.error
                )
            
            # Return number of connections the event was sent to
            return result.value
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e)
            )
    
    # WebSocket endpoint
    @router.websocket("/ws")
    async def websocket_endpoint(
        websocket: WebSocket,
        connection_service: ConnectionServiceProtocol = Depends(get_connection_service),
        websocket_service: WebSocketServiceProtocol = Depends(get_websocket_service)
    ):
        """WebSocket endpoint for real-time communication."""
        connection_id = None
        try:
            # Accept connection
            await websocket.accept()
            
            # Create a connection
            connection_result = await connection_service.create_connection(
                client_info={
                    "ip": websocket.client.host,
                    "user_agent": websocket.headers.get("user-agent"),
                    "connection_type": "websocket"
                }
            )
            
            if connection_result.is_failure():
                await websocket.close(code=1011, reason=connection_result.error)
                return
            
            connection = connection_result.value
            connection_id = connection.id
            
            # Register WebSocket with service
            websocket_service.register_socket(connection.id, websocket)
            
            # Update connection state
            await connection_service.update_connection_state(connection.id, "connected")
            
            # Send connection ID to client
            await websocket.send_json({
                "type": "connection",
                "connection_id": connection.id.value
            })
            
            # Listen for messages
            while True:
                message = await websocket.receive()
                
                if "text" in message:
                    # Handle text message
                    await websocket_service.handle_message(connection.id, message["text"])
                elif "bytes" in message:
                    # Handle binary message
                    await websocket_service.handle_message(connection.id, message["bytes"], binary=True)
        except WebSocketDisconnect:
            # Client disconnected
            pass
        except Exception as e:
            # Error occurred
            if websocket.client_state == WebSocket.CONNECTED:
                await websocket.close(code=1011, reason=str(e))
        finally:
            # Clean up on disconnect
            if connection_id:
                # Update connection state
                await connection_service.update_connection_state(connection_id, "disconnected")
                
                # Unregister WebSocket
                websocket_service.unregister_socket(connection_id)
                
                # Close connection
                await connection_service.close_connection(connection_id)
    
    return router