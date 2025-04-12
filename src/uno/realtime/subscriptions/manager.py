"""Subscription manager implementation.

This module provides the central subscription manager for managing subscriptions.
"""

import asyncio
import logging
from typing import (
    Dict, List, Any, Optional, Set, Callable, Coroutine, 
    Union, TypeVar, Generic, Protocol, Awaitable
)
from datetime import datetime, timedelta

from uno.realtime.subscriptions.subscription import (
    Subscription,
    SubscriptionType,
    SubscriptionStatus,
    create_resource_subscription,
    create_resource_type_subscription,
    create_topic_subscription,
    create_query_subscription
)
from uno.realtime.subscriptions.store import (
    SubscriptionStore,
    InMemorySubscriptionStoreWithCleanup
)
from uno.realtime.subscriptions.errors import (
    SubscriptionError,
    SubscriptionErrorCode,
    ValidationError,
    PermissionError,
    StoreError
)


# Type for subscription handler
SubscriptionHandler = Callable[[Subscription], Awaitable[bool]]

# Type for subscription filter
SubscriptionFilter = Callable[[Subscription], Awaitable[bool]]

# Type for event handler
EventHandler = Callable[[Dict[str, Any], List[Subscription]], Awaitable[None]]


class SubscriptionManager:
    """Central manager for subscriptions.
    
    The SubscriptionManager is responsible for:
    - Creating and storing subscriptions
    - Managing subscription lifecycle
    - Finding subscriptions for events
    - Processing events with matched subscriptions
    """
    
    def __init__(
        self,
        store: Optional[SubscriptionStore] = None,
        max_subscriptions_per_user: int = 100,
        enable_authorization: bool = True
    ):
        """Initialize the subscription manager.
        
        Args:
            store: The subscription store to use.
            max_subscriptions_per_user: Maximum number of subscriptions per user.
            enable_authorization: Whether to enable authorization checks.
        """
        # Initialize logger first so it's available to all methods
        self._logger = logging.getLogger(__name__)
        
        self._store = store or InMemorySubscriptionStoreWithCleanup()
        self._max_subscriptions_per_user = max_subscriptions_per_user
        self._enable_authorization = enable_authorization
        
        # Subscription hooks
        self._pre_subscription_hooks: List[SubscriptionFilter] = []
        self._post_subscription_hooks: List[SubscriptionHandler] = []
        
        # Event hooks
        self._event_handlers: List[EventHandler] = []
        
        # Authorization handlers
        self._authorization_handlers: Dict[SubscriptionType, Callable] = {}
    
    @property
    def store(self) -> SubscriptionStore:
        """Get the subscription store."""
        return self._store
    
    def add_pre_subscription_hook(self, hook: SubscriptionFilter) -> None:
        """Add a hook to run before creating a subscription.
        
        Pre-subscription hooks can filter subscriptions before creation.
        If any hook returns False, the subscription will not be created.
        
        Args:
            hook: The hook function to add.
        """
        self._pre_subscription_hooks.append(hook)
    
    def add_post_subscription_hook(self, hook: SubscriptionHandler) -> None:
        """Add a hook to run after creating a subscription.
        
        Post-subscription hooks are called after successful creation.
        
        Args:
            hook: The hook function to add.
        """
        self._post_subscription_hooks.append(hook)
    
    def add_event_handler(self, handler: EventHandler) -> None:
        """Add a handler for events with matched subscriptions.
        
        Event handlers are called when an event matches subscriptions.
        
        Args:
            handler: The handler function to add.
        """
        self._event_handlers.append(handler)
    
    def register_authorization_handler(
        self, 
        subscription_type: SubscriptionType, 
        handler: Callable
    ) -> None:
        """Register an authorization handler for a subscription type.
        
        Args:
            subscription_type: The subscription type.
            handler: The authorization handler function.
        """
        self._authorization_handlers[subscription_type] = handler
    
    async def create_subscription(self, subscription: Subscription) -> str:
        """Create a new subscription.
        
        Args:
            subscription: The subscription to create.
            
        Returns:
            The ID of the created subscription.
            
        Raises:
            ValidationError: If the subscription is invalid.
            PermissionError: If the user is not authorized to create the subscription.
            SubscriptionError: If subscription creation fails.
        """
        # Validate subscription
        try:
            subscription._validate_type_specific_fields()
        except ValueError as e:
            raise ValidationError(
                SubscriptionErrorCode.INVALID_SUBSCRIPTION,
                str(e)
            )
        
        # Check subscription limit
        user_subscriptions = await self._store.get_for_user(
            subscription.user_id, active_only=True
        )
        if len(user_subscriptions) >= self._max_subscriptions_per_user:
            raise SubscriptionError(
                SubscriptionErrorCode.SUBSCRIPTION_LIMIT_REACHED,
                f"User has reached the maximum of {self._max_subscriptions_per_user} subscriptions"
            )
        
        # Check authorization if enabled
        if self._enable_authorization:
            await self._check_authorization(subscription)
        
        # Run pre-subscription hooks
        for hook in self._pre_subscription_hooks:
            try:
                allow = await hook(subscription)
                if not allow:
                    raise SubscriptionError(
                        SubscriptionErrorCode.INVALID_SUBSCRIPTION,
                        "Subscription rejected by pre-subscription hook"
                    )
            except Exception as e:
                self._logger.error(f"Error in pre-subscription hook: {e}")
                # Continue with other hooks
        
        # Store the subscription
        try:
            subscription_id = await self._store.save(subscription)
        except Exception as e:
            raise StoreError(
                SubscriptionErrorCode.STORE_ERROR,
                f"Failed to save subscription: {str(e)}"
            )
        
        # Run post-subscription hooks
        for hook in self._post_subscription_hooks:
            try:
                await hook(subscription)
            except Exception as e:
                self._logger.error(f"Error in post-subscription hook: {e}")
                # Continue with other hooks
        
        return subscription_id
    
    async def _check_authorization(self, subscription: Subscription) -> None:
        """Check if a user is authorized to create a subscription.
        
        Args:
            subscription: The subscription to check.
            
        Raises:
            PermissionError: If the user is not authorized.
        """
        # Skip if no handler for this type
        if subscription.type not in self._authorization_handlers:
            return
        
        handler = self._authorization_handlers[subscription.type]
        
        try:
            authorized = await handler(subscription)
            if not authorized:
                raise PermissionError(
                    SubscriptionErrorCode.PERMISSION_DENIED,
                    f"User {subscription.user_id} is not authorized to create this subscription"
                )
        except Exception as e:
            if isinstance(e, PermissionError):
                raise
            
            raise PermissionError(
                SubscriptionErrorCode.PERMISSION_DENIED,
                f"Authorization check failed: {str(e)}"
            )
    
    async def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID.
        
        Args:
            subscription_id: The ID of the subscription.
            
        Returns:
            The subscription if found, None otherwise.
        """
        return await self._store.get(subscription_id)
    
    async def update_subscription(self, subscription: Subscription) -> bool:
        """Update an existing subscription.
        
        Args:
            subscription: The updated subscription.
            
        Returns:
            True if the subscription was updated, False if not found.
            
        Raises:
            ValidationError: If the subscription is invalid.
            PermissionError: If the user is not authorized to update the subscription.
            StoreError: If the update fails.
        """
        # Validate subscription
        try:
            subscription._validate_type_specific_fields()
        except ValueError as e:
            raise ValidationError(
                SubscriptionErrorCode.INVALID_SUBSCRIPTION,
                str(e)
            )
        
        # Get existing subscription
        existing = await self._store.get(subscription.id)
        if not existing:
            return False
        
        # Check authorization if enabled and user_id changed
        if self._enable_authorization and existing.user_id != subscription.user_id:
            await self._check_authorization(subscription)
        
        # Update the subscription
        try:
            result = await self._store.update(subscription)
        except Exception as e:
            raise StoreError(
                SubscriptionErrorCode.STORE_ERROR,
                f"Failed to update subscription: {str(e)}"
            )
        
        return result
    
    async def delete_subscription(self, subscription_id: str) -> bool:
        """Delete a subscription.
        
        Args:
            subscription_id: The ID of the subscription to delete.
            
        Returns:
            True if the subscription was deleted, False if not found.
            
        Raises:
            StoreError: If the deletion fails.
        """
        try:
            return await self._store.delete(subscription_id)
        except Exception as e:
            raise StoreError(
                SubscriptionErrorCode.STORE_ERROR,
                f"Failed to delete subscription: {str(e)}"
            )
    
    async def get_user_subscriptions(
        self, 
        user_id: str, 
        active_only: bool = True,
        types: Optional[List[SubscriptionType]] = None
    ) -> List[Subscription]:
        """Get subscriptions for a specific user.
        
        Args:
            user_id: The ID of the user.
            active_only: Whether to include only active subscriptions.
            types: Optional list of subscription types to filter by.
            
        Returns:
            List of subscriptions for the user.
        """
        return await self._store.get_for_user(user_id, active_only, types)
    
    async def update_subscription_status(
        self, 
        subscription_id: str, 
        status: SubscriptionStatus
    ) -> bool:
        """Update the status of a subscription.
        
        Args:
            subscription_id: The ID of the subscription.
            status: The new status.
            
        Returns:
            True if the subscription was updated, False if not found.
            
        Raises:
            StoreError: If the update fails.
        """
        subscription = await self._store.get(subscription_id)
        if not subscription:
            return False
        
        subscription.update_status(status)
        
        try:
            return await self._store.update(subscription)
        except Exception as e:
            raise StoreError(
                SubscriptionErrorCode.STORE_ERROR,
                f"Failed to update subscription status: {str(e)}"
            )
    
    async def update_subscription_expiration(
        self, 
        subscription_id: str, 
        expires_at: Optional[datetime]
    ) -> bool:
        """Update the expiration of a subscription.
        
        Args:
            subscription_id: The ID of the subscription.
            expires_at: The new expiration date, or None for no expiration.
            
        Returns:
            True if the subscription was updated, False if not found.
            
        Raises:
            StoreError: If the update fails.
        """
        subscription = await self._store.get(subscription_id)
        if not subscription:
            return False
        
        subscription.update_expiration(expires_at)
        
        try:
            return await self._store.update(subscription)
        except Exception as e:
            raise StoreError(
                SubscriptionErrorCode.STORE_ERROR,
                f"Failed to update subscription expiration: {str(e)}"
            )
    
    async def process_event(self, event_data: Dict[str, Any]) -> List[Subscription]:
        """Process an event and match it with subscriptions.
        
        Args:
            event_data: The event data.
            
        Returns:
            List of subscriptions that match the event.
            
        Raises:
            SubscriptionError: If event processing fails.
        """
        try:
            # Get matching subscriptions
            matching_subscriptions = await self._store.get_matching_event(event_data)
            
            # Run event handlers
            for handler in self._event_handlers:
                try:
                    await handler(event_data, matching_subscriptions)
                except Exception as e:
                    self._logger.error(f"Error in event handler: {e}")
                    # Continue with other handlers
            
            return matching_subscriptions
        except Exception as e:
            raise SubscriptionError(
                SubscriptionErrorCode.OPERATION_FAILED,
                f"Failed to process event: {str(e)}"
            )
    
    # Convenience methods for creating common subscription types
    
    async def subscribe_to_resource(
        self,
        user_id: str,
        resource_id: str,
        resource_type: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        labels: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a subscription to a specific resource.
        
        Args:
            user_id: The ID of the subscribing user.
            resource_id: The ID of the resource.
            resource_type: Optional type of the resource.
            expires_at: Optional expiration date.
            labels: Optional set of labels.
            metadata: Optional metadata.
            
        Returns:
            The ID of the created subscription.
        """
        subscription = create_resource_subscription(
            user_id=user_id,
            resource_id=resource_id,
            resource_type=resource_type,
            expires_at=expires_at,
            labels=labels,
            metadata=metadata
        )
        
        return await self.create_subscription(subscription)
    
    async def subscribe_to_resource_type(
        self,
        user_id: str,
        resource_type: str,
        expires_at: Optional[datetime] = None,
        labels: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a subscription to a resource type.
        
        Args:
            user_id: The ID of the subscribing user.
            resource_type: The type of resources to subscribe to.
            expires_at: Optional expiration date.
            labels: Optional set of labels.
            metadata: Optional metadata.
            
        Returns:
            The ID of the created subscription.
        """
        subscription = create_resource_type_subscription(
            user_id=user_id,
            resource_type=resource_type,
            expires_at=expires_at,
            labels=labels,
            metadata=metadata
        )
        
        return await self.create_subscription(subscription)
    
    async def subscribe_to_topic(
        self,
        user_id: str,
        topic: str,
        expires_at: Optional[datetime] = None,
        labels: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        payload_filter: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a subscription to a topic.
        
        Args:
            user_id: The ID of the subscribing user.
            topic: The topic to subscribe to.
            expires_at: Optional expiration date.
            labels: Optional set of labels.
            metadata: Optional metadata.
            payload_filter: Optional filter for event payloads.
            
        Returns:
            The ID of the created subscription.
        """
        subscription = create_topic_subscription(
            user_id=user_id,
            topic=topic,
            expires_at=expires_at,
            labels=labels,
            metadata=metadata,
            payload_filter=payload_filter
        )
        
        return await self.create_subscription(subscription)
    
    async def subscribe_to_query(
        self,
        user_id: str,
        query: Dict[str, Any],
        expires_at: Optional[datetime] = None,
        labels: Optional[Set[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Create a subscription to query results.
        
        Args:
            user_id: The ID of the subscribing user.
            query: The query parameters.
            expires_at: Optional expiration date.
            labels: Optional set of labels.
            metadata: Optional metadata.
            
        Returns:
            The ID of the created subscription.
        """
        subscription = create_query_subscription(
            user_id=user_id,
            query=query,
            expires_at=expires_at,
            labels=labels,
            metadata=metadata
        )
        
        return await self.create_subscription(subscription)


# Integration with notifications, WebSocket, and SSE

class NotificationEventHandler:
    """Event handler that sends notifications for matched subscriptions."""
    
    def __init__(self, notification_hub):
        """Initialize with a notification hub.
        
        Args:
            notification_hub: The notification hub instance.
        """
        from uno.realtime.notifications import NotificationHub
        self._notification_hub = notification_hub
    
    async def handle_event(
        self, 
        event_data: Dict[str, Any], 
        matching_subscriptions: List[Subscription]
    ) -> None:
        """Handle an event by sending notifications to subscribers.
        
        Args:
            event_data: The event data.
            matching_subscriptions: The subscriptions that match the event.
        """
        from uno.realtime.notifications import (
            Notification, 
            NotificationPriority, 
            NotificationType
        )
        
        # Skip if no matching subscriptions
        if not matching_subscriptions:
            return
        
        # Extract notification data from event
        title = event_data.get("title", "Event Notification")
        message = event_data.get("message", "You have a new notification")
        priority = event_data.get("priority", NotificationPriority.NORMAL)
        
        # Group subscribers by topic/resource for batch notifications
        subscribers_by_topic: Dict[str, List[str]] = {}
        
        for subscription in matching_subscriptions:
            # Skip inactive subscriptions
            if not subscription.is_active():
                continue
            
            # Determine the topic (or use resource info)
            topic = None
            if subscription.type == SubscriptionType.TOPIC and subscription.topic:
                topic = subscription.topic
            elif subscription.type == SubscriptionType.RESOURCE and subscription.resource_id:
                topic = f"resource:{subscription.resource_id}"
            elif subscription.type == SubscriptionType.RESOURCE_TYPE and subscription.resource_type:
                topic = f"resource_type:{subscription.resource_type}"
            else:
                topic = "general"
            
            # Add to subscribers map
            if topic not in subscribers_by_topic:
                subscribers_by_topic[topic] = []
            
            subscribers_by_topic[topic].append(subscription.user_id)
        
        # Send notifications for each topic group
        for topic, user_ids in subscribers_by_topic.items():
            # Skip empty groups
            if not user_ids:
                continue
            
            # Create actions if applicable
            actions = []
            resource_id = event_data.get("resource_id")
            resource_type = event_data.get("resource_type")
            
            if resource_id and resource_type:
                actions.append({
                    "label": "View",
                    "action": "view_resource",
                    "data": {
                        "resource_id": resource_id,
                        "resource_type": resource_type
                    }
                })
            
            # Determine notification type
            if topic.startswith("resource:"):
                notification_type = NotificationType.UPDATE
            elif topic.startswith("resource_type:"):
                notification_type = NotificationType.NEW_CONTENT
            else:
                notification_type = NotificationType.SYSTEM
            
            # Send notification to this group
            try:
                await self._notification_hub.notify_resource(
                    title=title,
                    message=message,
                    recipients=user_ids,
                    resource_type=resource_type or "event",
                    resource_id=resource_id or topic,
                    type_=notification_type,
                    priority=priority,
                    actions=actions
                )
            except Exception as e:
                # Log error but continue with other notifications
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to send notification for topic {topic}: {e}")


class WebSocketEventHandler:
    """Event handler that sends WebSocket messages for matched subscriptions."""
    
    def __init__(self, websocket_manager):
        """Initialize with a WebSocket manager.
        
        Args:
            websocket_manager: The WebSocket manager instance.
        """
        from uno.realtime.websocket import WebSocketManager
        self._websocket_manager = websocket_manager
    
    async def handle_event(
        self, 
        event_data: Dict[str, Any], 
        matching_subscriptions: List[Subscription]
    ) -> None:
        """Handle an event by sending WebSocket messages to subscribers.
        
        Args:
            event_data: The event data.
            matching_subscriptions: The subscriptions that match the event.
        """
        from uno.realtime.websocket.message import MessageType, Message
        
        # Skip if no matching subscriptions
        if not matching_subscriptions:
            return
        
        # Extract user IDs from matching subscriptions
        user_ids = [sub.user_id for sub in matching_subscriptions if sub.is_active()]
        
        # Skip if no active subscribers
        if not user_ids:
            return
        
        # Create WebSocket message
        message = Message(
            type=MessageType.DATA,
            payload={
                "event": event_data,
                "subscription_matched": True
            }
        )
        
        # Broadcast to matching users
        await self._websocket_manager.broadcast_to_users(message, user_ids)


class SSEEventHandler:
    """Event handler that sends SSE events for matched subscriptions."""
    
    def __init__(self, sse_manager):
        """Initialize with an SSE manager.
        
        Args:
            sse_manager: The SSE manager instance.
        """
        from uno.realtime.sse import SSEManager
        self._sse_manager = sse_manager
    
    async def handle_event(
        self, 
        event_data: Dict[str, Any], 
        matching_subscriptions: List[Subscription]
    ) -> None:
        """Handle an event by sending SSE events to subscribers.
        
        Args:
            event_data: The event data.
            matching_subscriptions: The subscriptions that match the event.
        """
        from uno.realtime.sse.event import create_data_event, EventPriority
        
        # Skip if no matching subscriptions
        if not matching_subscriptions:
            return
        
        # Extract user IDs from matching subscriptions
        user_ids = [sub.user_id for sub in matching_subscriptions if sub.is_active()]
        
        # Skip if no active subscribers
        if not user_ids:
            return
        
        # Determine resource information
        resource_type = event_data.get("resource_type", "event")
        resource_id = event_data.get("resource_id", None)
        
        # Construct resource identifier
        if resource_id:
            resource = f"{resource_type}:{resource_id}"
        else:
            resource = resource_type
        
        # Determine priority
        priority = EventPriority.NORMAL
        if "priority" in event_data:
            priority_value = event_data["priority"]
            if priority_value == "high":
                priority = EventPriority.HIGH
            elif priority_value == "low":
                priority = EventPriority.LOW
        
        # Broadcast to matching users
        await self._sse_manager.broadcast_data(
            resource=resource,
            data=event_data,
            user_ids=user_ids,
            priority=priority
        )