"""Simple tests for the subscription classes."""

import unittest
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Set, List

from uno.realtime.subscriptions.subscription import (
    Subscription,
    SubscriptionType,
    SubscriptionStatus,
    create_resource_subscription,
    create_resource_type_subscription,
    create_topic_subscription,
    create_query_subscription
)
from uno.realtime.subscriptions.store import InMemorySubscriptionStore
from uno.realtime.subscriptions.manager import SubscriptionManager


class TestSubscription(unittest.TestCase):
    """Tests for the Subscription class."""
    
    def test_subscription_creation(self):
        """Test creating a Subscription."""
        subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.RESOURCE,
            resource_id="post123",
            resource_type="post"
        )
        
        self.assertEqual(subscription.user_id, "user1")
        self.assertEqual(subscription.type, SubscriptionType.RESOURCE)
        self.assertEqual(subscription.resource_id, "post123")
        self.assertEqual(subscription.resource_type, "post")
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE)
        self.assertIsNotNone(subscription.id)
    
    def test_subscription_validation(self):
        """Test subscription validation."""
        # Valid subscription
        subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.RESOURCE,
            resource_id="post123"
        )
        
        # Invalid subscription (missing required field)
        with self.assertRaises(ValueError):
            Subscription(
                user_id="user1",
                type=SubscriptionType.RESOURCE,
                resource_id=None
            )
    
    def test_subscription_serialization(self):
        """Test serializing and deserializing subscriptions."""
        subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.TOPIC,
            topic="announcements",
            labels={"important", "general"}
        )
        
        # Convert to dict
        data = subscription.to_dict()
        
        # Check dict values
        self.assertEqual(data["user_id"], "user1")
        self.assertEqual(data["type"], "TOPIC")
        self.assertEqual(data["topic"], "announcements")
        self.assertIn("important", data["labels"])
        self.assertIn("general", data["labels"])
        
        # Convert back to subscription
        new_subscription = Subscription.from_dict(data)
        
        # Check values after round-trip
        self.assertEqual(new_subscription.user_id, subscription.user_id)
        self.assertEqual(new_subscription.type, subscription.type)
        self.assertEqual(new_subscription.topic, subscription.topic)
        self.assertEqual(new_subscription.labels, subscription.labels)
    
    def test_subscription_status(self):
        """Test subscription status management."""
        subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.RESOURCE,
            resource_id="post123"
        )
        
        # Initially active
        self.assertEqual(subscription.status, SubscriptionStatus.ACTIVE)
        self.assertTrue(subscription.is_active())
        self.assertFalse(subscription.is_expired())
        
        # Update status
        subscription.update_status(SubscriptionStatus.PAUSED)
        self.assertEqual(subscription.status, SubscriptionStatus.PAUSED)
        self.assertFalse(subscription.is_active())
        
        # Set expiration
        future = datetime.now() + timedelta(days=1)
        subscription.update_status(SubscriptionStatus.ACTIVE)
        subscription.update_expiration(future)
        self.assertTrue(subscription.is_active())
        
        # Set past expiration
        past = datetime.now() - timedelta(days=1)
        subscription.update_expiration(past)
        self.assertFalse(subscription.is_active())
        self.assertTrue(subscription.is_expired())
    
    def test_subscription_matching(self):
        """Test subscription event matching."""
        # Resource subscription
        resource_subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.RESOURCE,
            resource_id="post123",
            resource_type="post"
        )
        
        # Topic subscription
        topic_subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.TOPIC,
            topic="announcements"
        )
        
        # Query subscription
        query_subscription = Subscription(
            user_id="user1",
            type=SubscriptionType.QUERY,
            query={"department": "engineering", "priority": "high"}
        )
        
        # Test resource subscription matching
        self.assertTrue(resource_subscription.matches_event({
            "resource_id": "post123",
            "resource_type": "post",
            "action": "update"
        }))
        
        self.assertFalse(resource_subscription.matches_event({
            "resource_id": "post456",
            "resource_type": "post",
            "action": "update"
        }))
        
        # Test topic subscription matching
        self.assertTrue(topic_subscription.matches_event({
            "topic": "announcements",
            "message": "New announcement"
        }))
        
        self.assertFalse(topic_subscription.matches_event({
            "topic": "events",
            "message": "New event"
        }))
        
        # Test query subscription matching
        self.assertTrue(query_subscription.matches_event({
            "department": "engineering",
            "priority": "high",
            "message": "Critical update"
        }))
        
        self.assertFalse(query_subscription.matches_event({
            "department": "engineering",
            "priority": "low",
            "message": "Minor update"
        }))
    
    def test_factory_functions(self):
        """Test subscription factory functions."""
        # Resource subscription
        resource_sub = create_resource_subscription(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        self.assertEqual(resource_sub.type, SubscriptionType.RESOURCE)
        self.assertEqual(resource_sub.resource_id, "post123")
        
        # Resource type subscription
        type_sub = create_resource_type_subscription(
            user_id="user1",
            resource_type="post"
        )
        
        self.assertEqual(type_sub.type, SubscriptionType.RESOURCE_TYPE)
        self.assertEqual(type_sub.resource_type, "post")
        
        # Topic subscription
        topic_sub = create_topic_subscription(
            user_id="user1",
            topic="announcements"
        )
        
        self.assertEqual(topic_sub.type, SubscriptionType.TOPIC)
        self.assertEqual(topic_sub.topic, "announcements")
        
        # Query subscription
        query_sub = create_query_subscription(
            user_id="user1",
            query={"department": "engineering"}
        )
        
        self.assertEqual(query_sub.type, SubscriptionType.QUERY)
        self.assertEqual(query_sub.query, {"department": "engineering"})


class TestInMemorySubscriptionStore(unittest.IsolatedAsyncioTestCase):
    """Tests for the InMemorySubscriptionStore class."""
    
    async def test_save_and_get(self):
        """Test saving and retrieving subscriptions."""
        store = InMemorySubscriptionStore()
        
        # Create a subscription
        subscription = create_resource_subscription(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        # Save it
        subscription_id = await store.save(subscription)
        
        # Retrieve it
        retrieved = await store.get(subscription_id)
        
        # Check it matches
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, subscription.id)
        self.assertEqual(retrieved.user_id, subscription.user_id)
        self.assertEqual(retrieved.resource_id, subscription.resource_id)
    
    async def test_get_for_user(self):
        """Test retrieving subscriptions for a user."""
        store = InMemorySubscriptionStore()
        
        # Create and save subscriptions for different users
        sub1 = create_resource_subscription(
            user_id="user1",
            resource_id="post123"
        )
        
        sub2 = create_topic_subscription(
            user_id="user1",
            topic="announcements"
        )
        
        sub3 = create_resource_subscription(
            user_id="user2",
            resource_id="post456"
        )
        
        await store.save(sub1)
        await store.save(sub2)
        await store.save(sub3)
        
        # Get subscriptions for user1
        user1_subscriptions = await store.get_for_user("user1")
        
        # Check results
        self.assertEqual(len(user1_subscriptions), 2)
        
        # Check by type
        topics = [sub for sub in user1_subscriptions if sub.type == SubscriptionType.TOPIC]
        self.assertEqual(len(topics), 1)
        self.assertEqual(topics[0].topic, "announcements")
        
        resources = [sub for sub in user1_subscriptions if sub.type == SubscriptionType.RESOURCE]
        self.assertEqual(len(resources), 1)
        self.assertEqual(resources[0].resource_id, "post123")
    
    async def test_get_by_type(self):
        """Test retrieving subscriptions by type."""
        store = InMemorySubscriptionStore()
        
        # Create and save different types of subscriptions
        resource_sub = create_resource_subscription(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        resource_type_sub = create_resource_type_subscription(
            user_id="user2",
            resource_type="post"
        )
        
        topic_sub = create_topic_subscription(
            user_id="user3",
            topic="posts"
        )
        
        await store.save(resource_sub)
        await store.save(resource_type_sub)
        await store.save(topic_sub)
        
        # Get by resource
        resource_subs = await store.get_by_resource("post123")
        self.assertEqual(len(resource_subs), 1)
        self.assertEqual(resource_subs[0].id, resource_sub.id)
        
        # Get by resource type
        resource_type_subs = await store.get_by_resource_type("post")
        self.assertEqual(len(resource_type_subs), 1)
        self.assertEqual(resource_type_subs[0].id, resource_type_sub.id)
        
        # Get by topic
        topic_subs = await store.get_by_topic("posts")
        self.assertEqual(len(topic_subs), 1)
        self.assertEqual(topic_subs[0].id, topic_sub.id)
    
    async def test_get_matching_event(self):
        """Test retrieving subscriptions matching an event."""
        store = InMemorySubscriptionStore()
        
        # Create and save different types of subscriptions
        resource_sub = create_resource_subscription(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        resource_type_sub = create_resource_type_subscription(
            user_id="user2",
            resource_type="post"
        )
        
        topic_sub = create_topic_subscription(
            user_id="user3",
            topic="posts"
        )
        
        query_sub = create_query_subscription(
            user_id="user4",
            query={"type": "post", "author": "user5"}
        )
        
        await store.save(resource_sub)
        await store.save(resource_type_sub)
        await store.save(topic_sub)
        await store.save(query_sub)
        
        # Create an event
        event = {
            "resource_id": "post123",
            "resource_type": "post",
            "topic": "posts",
            "type": "post",
            "author": "user5"
        }
        
        # Get matching subscriptions
        matching = await store.get_matching_event(event)
        
        # Should match all 4 subscriptions
        self.assertEqual(len(matching), 4)
        
        # Create a more specific event that won't match all
        event2 = {
            "resource_id": "post456",
            "resource_type": "post",
            "topic": "other",
            "type": "post",
            "author": "user5"
        }
        
        # Get matching subscriptions
        matching2 = await store.get_matching_event(event2)
        
        # Should match resource_type_sub and query_sub
        self.assertEqual(len(matching2), 2)


class TestSubscriptionManager(unittest.IsolatedAsyncioTestCase):
    """Tests for the SubscriptionManager class."""
    
    async def test_create_subscription(self):
        """Test creating a subscription through the manager."""
        manager = SubscriptionManager()
        
        # Create a subscription
        subscription = create_resource_subscription(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        # Save it
        subscription_id = await manager.create_subscription(subscription)
        
        # Retrieve it
        retrieved = await manager.get_subscription(subscription_id)
        
        # Check it matches
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, subscription.id)
        self.assertEqual(retrieved.user_id, subscription.user_id)
        self.assertEqual(retrieved.resource_id, subscription.resource_id)
    
    async def test_helper_methods(self):
        """Test subscription helper methods."""
        manager = SubscriptionManager()
        
        # Create subscriptions using helper methods
        resource_id = await manager.subscribe_to_resource(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        resource_type_id = await manager.subscribe_to_resource_type(
            user_id="user1",
            resource_type="comment"
        )
        
        topic_id = await manager.subscribe_to_topic(
            user_id="user1",
            topic="announcements"
        )
        
        query_id = await manager.subscribe_to_query(
            user_id="user1",
            query={"department": "engineering"}
        )
        
        # Get user subscriptions
        subscriptions = await manager.get_user_subscriptions("user1")
        
        # Check count
        self.assertEqual(len(subscriptions), 4)
        
        # Check types
        types = [sub.type for sub in subscriptions]
        self.assertIn(SubscriptionType.RESOURCE, types)
        self.assertIn(SubscriptionType.RESOURCE_TYPE, types)
        self.assertIn(SubscriptionType.TOPIC, types)
        self.assertIn(SubscriptionType.QUERY, types)
    
    async def test_update_subscription(self):
        """Test updating a subscription."""
        manager = SubscriptionManager()
        
        # Create a subscription
        subscription_id = await manager.subscribe_to_resource(
            user_id="user1",
            resource_id="post123"
        )
        
        # Update its status
        result = await manager.update_subscription_status(
            subscription_id,
            SubscriptionStatus.PAUSED
        )
        
        self.assertTrue(result)
        
        # Get the updated subscription
        subscription = await manager.get_subscription(subscription_id)
        
        # Check the status was updated
        self.assertEqual(subscription.status, SubscriptionStatus.PAUSED)
    
    async def test_process_event(self):
        """Test processing an event."""
        manager = SubscriptionManager()
        
        # Add an event handler to track calls
        events_processed = []
        
        async def event_handler(event_data: Dict[str, Any], matching_subscriptions: List[Subscription]) -> None:
            events_processed.append((event_data, matching_subscriptions))
        
        manager.add_event_handler(event_handler)
        
        # Create subscriptions
        await manager.subscribe_to_resource(
            user_id="user1",
            resource_id="post123",
            resource_type="post"
        )
        
        await manager.subscribe_to_topic(
            user_id="user2",
            topic="posts"
        )
        
        # Process an event
        event = {
            "resource_id": "post123",
            "resource_type": "post",
            "topic": "posts",
            "action": "update"
        }
        
        matching = await manager.process_event(event)
        
        # Check that the event was processed
        self.assertEqual(len(matching), 2)
        self.assertEqual(len(events_processed), 1)
        self.assertEqual(events_processed[0][0], event)
        self.assertEqual(len(events_processed[0][1]), 2)


if __name__ == "__main__":
    unittest.main()