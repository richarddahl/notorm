"""Subscription storage system.

This module provides storage for subscriptions with query and retrieval capabilities.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set, Tuple, AsyncIterator
from datetime import datetime, timedelta

from uno.realtime.subscriptions.subscription import (
    Subscription, 
    SubscriptionType,
    SubscriptionStatus
)
from uno.realtime.subscriptions.errors import (
    StoreError, 
    SubscriptionErrorCode
)


class SubscriptionStore(ABC):
    """Abstract base class for subscription stores.
    
    This class defines the interface for subscription storage implementations.
    Concrete implementations can store subscriptions in memory, database, etc.
    """
    
    @abstractmethod
    async def save(self, subscription: Subscription) -> str:
        """Save a subscription to the store.
        
        Args:
            subscription: The subscription to save.
            
        Returns:
            The ID of the saved subscription.
            
        Raises:
            StoreError: If the subscription cannot be saved.
        """
        pass
    
    @abstractmethod
    async def get(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID.
        
        Args:
            subscription_id: The ID of the subscription.
            
        Returns:
            The subscription if found, None otherwise.
        """
        pass
    
    @abstractmethod
    async def update(self, subscription: Subscription) -> bool:
        """Update an existing subscription.
        
        Args:
            subscription: The updated subscription.
            
        Returns:
            True if the subscription was updated, False if not found.
            
        Raises:
            StoreError: If the subscription cannot be updated.
        """
        pass
    
    @abstractmethod
    async def delete(self, subscription_id: str) -> bool:
        """Delete a subscription.
        
        Args:
            subscription_id: The ID of the subscription to delete.
            
        Returns:
            True if the subscription was deleted, False if not found.
        """
        pass
    
    @abstractmethod
    async def get_for_user(
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
        pass
    
    @abstractmethod
    async def get_by_resource(
        self, 
        resource_id: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific resource.
        
        Args:
            resource_id: The ID of the resource.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the resource.
        """
        pass
    
    @abstractmethod
    async def get_by_resource_type(
        self, 
        resource_type: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific resource type.
        
        Args:
            resource_type: The type of resource.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the resource type.
        """
        pass
    
    @abstractmethod
    async def get_by_topic(
        self, 
        topic: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific topic.
        
        Args:
            topic: The topic name.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the topic.
        """
        pass
    
    @abstractmethod
    async def get_matching_event(
        self, 
        event_data: Dict[str, Any],
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions that match an event.
        
        Args:
            event_data: The event data.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions that match the event.
        """
        pass
    
    @abstractmethod
    async def cleanup_expired(self) -> int:
        """Clean up expired subscriptions.
        
        Returns:
            The number of subscriptions cleaned up.
        """
        pass


class InMemorySubscriptionStore(SubscriptionStore):
    """In-memory implementation of SubscriptionStore.
    
    This implementation stores subscriptions in memory and is suitable for
    development, testing, or small applications with no persistence requirements.
    """
    
    def __init__(self):
        """Initialize the in-memory subscription store."""
        self._subscriptions: Dict[str, Subscription] = {}
        self._user_subscriptions: Dict[str, Set[str]] = {}
        self._resource_subscriptions: Dict[str, Set[str]] = {}
        self._resource_type_subscriptions: Dict[str, Set[str]] = {}
        self._topic_subscriptions: Dict[str, Set[str]] = {}
        self._logger = logging.getLogger(__name__)
    
    async def save(self, subscription: Subscription) -> str:
        """Save a subscription to the store.
        
        Args:
            subscription: The subscription to save.
            
        Returns:
            The ID of the saved subscription.
        """
        # Store the subscription
        self._subscriptions[subscription.id] = subscription
        
        # Update user-to-subscriptions mapping
        if subscription.user_id not in self._user_subscriptions:
            self._user_subscriptions[subscription.user_id] = set()
        self._user_subscriptions[subscription.user_id].add(subscription.id)
        
        # Update type-specific mappings
        if subscription.type == SubscriptionType.RESOURCE and subscription.resource_id:
            if subscription.resource_id not in self._resource_subscriptions:
                self._resource_subscriptions[subscription.resource_id] = set()
            self._resource_subscriptions[subscription.resource_id].add(subscription.id)
        
        elif subscription.type == SubscriptionType.RESOURCE_TYPE and subscription.resource_type:
            if subscription.resource_type not in self._resource_type_subscriptions:
                self._resource_type_subscriptions[subscription.resource_type] = set()
            self._resource_type_subscriptions[subscription.resource_type].add(subscription.id)
        
        elif subscription.type == SubscriptionType.TOPIC and subscription.topic:
            if subscription.topic not in self._topic_subscriptions:
                self._topic_subscriptions[subscription.topic] = set()
            self._topic_subscriptions[subscription.topic].add(subscription.id)
        
        return subscription.id
    
    async def get(self, subscription_id: str) -> Optional[Subscription]:
        """Get a subscription by ID.
        
        Args:
            subscription_id: The ID of the subscription.
            
        Returns:
            The subscription if found, None otherwise.
        """
        return self._subscriptions.get(subscription_id)
    
    async def update(self, subscription: Subscription) -> bool:
        """Update an existing subscription.
        
        Args:
            subscription: The updated subscription.
            
        Returns:
            True if the subscription was updated, False if not found.
        """
        if subscription.id not in self._subscriptions:
            return False
        
        # Get the old subscription to check if type-specific mappings need updating
        old_subscription = self._subscriptions[subscription.id]
        
        # Update type-specific mappings if needed
        if old_subscription.type != subscription.type:
            # Remove from old type mapping
            self._remove_from_type_mapping(old_subscription)
            
            # Add to new type mapping
            self._add_to_type_mapping(subscription)
        elif old_subscription.type == subscription.type:
            # Update within the same type if relevant fields changed
            if old_subscription.type == SubscriptionType.RESOURCE and old_subscription.resource_id != subscription.resource_id:
                self._remove_from_type_mapping(old_subscription)
                self._add_to_type_mapping(subscription)
            elif old_subscription.type == SubscriptionType.RESOURCE_TYPE and old_subscription.resource_type != subscription.resource_type:
                self._remove_from_type_mapping(old_subscription)
                self._add_to_type_mapping(subscription)
            elif old_subscription.type == SubscriptionType.TOPIC and old_subscription.topic != subscription.topic:
                self._remove_from_type_mapping(old_subscription)
                self._add_to_type_mapping(subscription)
        
        # Update the subscription
        self._subscriptions[subscription.id] = subscription
        
        # Update user mapping if needed
        if old_subscription.user_id != subscription.user_id:
            # Remove from old user
            if old_subscription.user_id in self._user_subscriptions:
                self._user_subscriptions[old_subscription.user_id].discard(subscription.id)
            
            # Add to new user
            if subscription.user_id not in self._user_subscriptions:
                self._user_subscriptions[subscription.user_id] = set()
            self._user_subscriptions[subscription.user_id].add(subscription.id)
        
        return True
    
    def _remove_from_type_mapping(self, subscription: Subscription) -> None:
        """Remove a subscription from its type-specific mapping.
        
        Args:
            subscription: The subscription to remove.
        """
        if subscription.type == SubscriptionType.RESOURCE and subscription.resource_id:
            if subscription.resource_id in self._resource_subscriptions:
                self._resource_subscriptions[subscription.resource_id].discard(subscription.id)
        
        elif subscription.type == SubscriptionType.RESOURCE_TYPE and subscription.resource_type:
            if subscription.resource_type in self._resource_type_subscriptions:
                self._resource_type_subscriptions[subscription.resource_type].discard(subscription.id)
        
        elif subscription.type == SubscriptionType.TOPIC and subscription.topic:
            if subscription.topic in self._topic_subscriptions:
                self._topic_subscriptions[subscription.topic].discard(subscription.id)
    
    def _add_to_type_mapping(self, subscription: Subscription) -> None:
        """Add a subscription to its type-specific mapping.
        
        Args:
            subscription: The subscription to add.
        """
        if subscription.type == SubscriptionType.RESOURCE and subscription.resource_id:
            if subscription.resource_id not in self._resource_subscriptions:
                self._resource_subscriptions[subscription.resource_id] = set()
            self._resource_subscriptions[subscription.resource_id].add(subscription.id)
        
        elif subscription.type == SubscriptionType.RESOURCE_TYPE and subscription.resource_type:
            if subscription.resource_type not in self._resource_type_subscriptions:
                self._resource_type_subscriptions[subscription.resource_type] = set()
            self._resource_type_subscriptions[subscription.resource_type].add(subscription.id)
        
        elif subscription.type == SubscriptionType.TOPIC and subscription.topic:
            if subscription.topic not in self._topic_subscriptions:
                self._topic_subscriptions[subscription.topic] = set()
            self._topic_subscriptions[subscription.topic].add(subscription.id)
    
    async def delete(self, subscription_id: str) -> bool:
        """Delete a subscription.
        
        Args:
            subscription_id: The ID of the subscription to delete.
            
        Returns:
            True if the subscription was deleted, False if not found.
        """
        if subscription_id not in self._subscriptions:
            return False
        
        # Get the subscription
        subscription = self._subscriptions[subscription_id]
        
        # Remove from user mapping
        if subscription.user_id in self._user_subscriptions:
            self._user_subscriptions[subscription.user_id].discard(subscription_id)
        
        # Remove from type-specific mappings
        self._remove_from_type_mapping(subscription)
        
        # Remove the subscription
        del self._subscriptions[subscription_id]
        
        return True
    
    async def get_for_user(
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
        if user_id not in self._user_subscriptions:
            return []
        
        # Get all subscription IDs for the user
        subscription_ids = self._user_subscriptions[user_id]
        
        # Get the subscriptions
        subscriptions = []
        for subscription_id in subscription_ids:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                
                # Filter by active status if requested
                if active_only and not subscription.is_active():
                    continue
                
                # Filter by types if specified
                if types and subscription.type not in types:
                    continue
                
                subscriptions.append(subscription)
        
        return subscriptions
    
    async def get_by_resource(
        self, 
        resource_id: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific resource.
        
        Args:
            resource_id: The ID of the resource.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the resource.
        """
        if resource_id not in self._resource_subscriptions:
            return []
        
        # Get all subscription IDs for the resource
        subscription_ids = self._resource_subscriptions[resource_id]
        
        # Get the subscriptions
        subscriptions = []
        for subscription_id in subscription_ids:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                
                # Filter by active status if requested
                if active_only and not subscription.is_active():
                    continue
                
                subscriptions.append(subscription)
        
        return subscriptions
    
    async def get_by_resource_type(
        self, 
        resource_type: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific resource type.
        
        Args:
            resource_type: The type of resource.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the resource type.
        """
        if resource_type not in self._resource_type_subscriptions:
            return []
        
        # Get all subscription IDs for the resource type
        subscription_ids = self._resource_type_subscriptions[resource_type]
        
        # Get the subscriptions
        subscriptions = []
        for subscription_id in subscription_ids:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                
                # Filter by active status if requested
                if active_only and not subscription.is_active():
                    continue
                
                subscriptions.append(subscription)
        
        return subscriptions
    
    async def get_by_topic(
        self, 
        topic: str,
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions for a specific topic.
        
        Args:
            topic: The topic name.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions for the topic.
        """
        if topic not in self._topic_subscriptions:
            return []
        
        # Get all subscription IDs for the topic
        subscription_ids = self._topic_subscriptions[topic]
        
        # Get the subscriptions
        subscriptions = []
        for subscription_id in subscription_ids:
            if subscription_id in self._subscriptions:
                subscription = self._subscriptions[subscription_id]
                
                # Filter by active status if requested
                if active_only and not subscription.is_active():
                    continue
                
                subscriptions.append(subscription)
        
        return subscriptions
    
    async def get_matching_event(
        self, 
        event_data: Dict[str, Any],
        active_only: bool = True
    ) -> List[Subscription]:
        """Get subscriptions that match an event.
        
        Args:
            event_data: The event data.
            active_only: Whether to include only active subscriptions.
            
        Returns:
            List of subscriptions that match the event.
        """
        matching_subscriptions = []
        
        # Check resource-specific subscriptions
        resource_id = event_data.get("resource_id")
        if resource_id and resource_id in self._resource_subscriptions:
            for subscription_id in self._resource_subscriptions[resource_id]:
                if subscription_id in self._subscriptions:
                    subscription = self._subscriptions[subscription_id]
                    
                    # Filter by active status if requested
                    if active_only and not subscription.is_active():
                        continue
                    
                    # Check if the subscription matches the event
                    if subscription.matches_event(event_data):
                        matching_subscriptions.append(subscription)
        
        # Check resource type subscriptions
        resource_type = event_data.get("resource_type")
        if resource_type and resource_type in self._resource_type_subscriptions:
            for subscription_id in self._resource_type_subscriptions[resource_type]:
                if subscription_id in self._subscriptions:
                    subscription = self._subscriptions[subscription_id]
                    
                    # Skip if already added
                    if subscription in matching_subscriptions:
                        continue
                    
                    # Filter by active status if requested
                    if active_only and not subscription.is_active():
                        continue
                    
                    # Check if the subscription matches the event
                    if subscription.matches_event(event_data):
                        matching_subscriptions.append(subscription)
        
        # Check topic subscriptions
        topic = event_data.get("topic")
        if topic and topic in self._topic_subscriptions:
            for subscription_id in self._topic_subscriptions[topic]:
                if subscription_id in self._subscriptions:
                    subscription = self._subscriptions[subscription_id]
                    
                    # Skip if already added
                    if subscription in matching_subscriptions:
                        continue
                    
                    # Filter by active status if requested
                    if active_only and not subscription.is_active():
                        continue
                    
                    # Check if the subscription matches the event
                    if subscription.matches_event(event_data):
                        matching_subscriptions.append(subscription)
        
        # Check query subscriptions
        # For query subscriptions, we need to check all of them
        # This is potentially expensive, but in-memory store is meant for small datasets
        for subscription in self._subscriptions.values():
            # Skip if already added
            if subscription in matching_subscriptions:
                continue
            
            # Only check query subscriptions
            if subscription.type != SubscriptionType.QUERY:
                continue
            
            # Filter by active status if requested
            if active_only and not subscription.is_active():
                continue
            
            # Check if the subscription matches the event
            if subscription.matches_event(event_data):
                matching_subscriptions.append(subscription)
        
        return matching_subscriptions
    
    async def cleanup_expired(self) -> int:
        """Clean up expired subscriptions.
        
        Returns:
            The number of subscriptions cleaned up.
        """
        now = datetime.now()
        expired_ids = []
        
        # Find expired subscriptions
        for subscription_id, subscription in self._subscriptions.items():
            if subscription.is_expired():
                expired_ids.append(subscription_id)
            elif subscription.expires_at and subscription.expires_at < now:
                # Mark as expired
                subscription.update_status(SubscriptionStatus.EXPIRED)
                expired_ids.append(subscription_id)
        
        # Delete expired subscriptions
        count = 0
        for subscription_id in expired_ids:
            if await self.delete(subscription_id):
                count += 1
        
        return count


class PeriodicCleanupMixin:
    """Mixin for adding periodic cleanup to subscription stores."""
    
    def __init__(
        self, 
        cleanup_interval: int = 3600,  # Default: 1 hour
        max_age_days: int = 30,        # Default: 30 days
        *args, 
        **kwargs
    ):
        """Initialize the periodic cleanup mixin.
        
        Args:
            cleanup_interval: Cleanup interval in seconds.
            max_age_days: Maximum age of subscriptions in days.
        """
        super().__init__(*args, **kwargs)
        self.cleanup_interval = cleanup_interval
        self.max_age_days = max_age_days
        self._cleanup_task = None
        self._logger = logging.getLogger(__name__)
    
    async def start_cleanup_task(self) -> None:
        """Start the periodic cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._periodic_cleanup())  # type: ignore
    
    async def stop_cleanup_task(self) -> None:
        """Stop the periodic cleanup task."""
        if self._cleanup_task is not None:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _periodic_cleanup(self) -> None:
        """Run the periodic cleanup task."""
        try:
            while True:
                await asyncio.sleep(self.cleanup_interval)
                try:
                    # Use the concrete implementation's method
                    if hasattr(self, 'cleanup_expired'):
                        count = await self.cleanup_expired()  # type: ignore
                        if count > 0:
                            self._logger.info(f"Cleaned up {count} expired subscriptions")
                        
                        count = await self._cleanup_old_subscriptions()  # type: ignore
                        if count > 0:
                            self._logger.info(f"Cleaned up {count} old subscriptions")
                except Exception as e:
                    self._logger.error(f"Error during subscription cleanup: {e}")
        except asyncio.CancelledError:
            # Task was canceled, exit gracefully
            pass
        except Exception as e:
            self._logger.error(f"Unexpected error in subscription cleanup task: {e}")
    
    async def _cleanup_old_subscriptions(self, cutoff_date: Optional[datetime] = None) -> int:
        """Clean up subscriptions older than the cutoff date.
        
        Args:
            cutoff_date: The cutoff date for subscription age, defaults to max_age_days ago.
            
        Returns:
            The number of subscriptions cleaned up.
        """
        if cutoff_date is None:
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # This method should be implemented by the concrete class
        # Default implementation does nothing
        return 0  # pragma: no cover


class InMemorySubscriptionStoreWithCleanup(PeriodicCleanupMixin, InMemorySubscriptionStore):
    """In-memory subscription store with periodic cleanup."""
    
    async def _cleanup_old_subscriptions(self, cutoff_date: Optional[datetime] = None) -> int:
        """Clean up subscriptions older than the cutoff date.
        
        Args:
            cutoff_date: The cutoff date for subscription age, defaults to max_age_days ago.
            
        Returns:
            The number of subscriptions cleaned up.
        """
        if cutoff_date is None:
            cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        
        # Find old inactive subscriptions
        old_subscription_ids = []
        for subscription_id, subscription in self._subscriptions.items():
            if (subscription.status != SubscriptionStatus.ACTIVE and
                subscription.updated_at < cutoff_date):
                old_subscription_ids.append(subscription_id)
        
        # Delete old subscriptions
        count = 0
        for subscription_id in old_subscription_ids:
            if await self.delete(subscription_id):
                count += 1
        
        return count