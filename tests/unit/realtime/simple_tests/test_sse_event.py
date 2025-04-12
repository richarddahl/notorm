"""Simple tests for the SSE Event class."""

import unittest
import json
from typing import Dict, Any

from uno.realtime.sse.event import Event, EventPriority, create_data_event, create_notification_event


class TestSSEEvent(unittest.TestCase):
    """Tests for the SSE Event class."""
    
    def test_event_creation(self):
        """Test creating an Event."""
        event = Event(data={"test": "data"})
        self.assertEqual(event.data, {"test": "data"})
        self.assertEqual(event.event, "message")  # Default type
        self.assertEqual(event.priority, EventPriority.NORMAL)
        self.assertIsNotNone(event.id)
    
    def test_event_sse_format(self):
        """Test converting an Event to SSE format."""
        event = Event(
            data={"test": "data"},
            id="test-id",
            event="test-event"
        )
        
        # Get the SSE format string
        sse_format = event.to_sse_format()
        
        # Verify essential parts
        self.assertIn(": timestamp=", sse_format)
        self.assertIn("id: test-id", sse_format)
        self.assertIn("event: test-event", sse_format)
        self.assertIn('data: {"test": "data"}', sse_format)
        
        # Should end with empty line
        self.assertTrue(sse_format.endswith("\n"))
    
    def test_create_data_event(self):
        """Test creating a data event."""
        event = create_data_event("users", {"id": 1, "name": "Test"})
        
        self.assertEqual(event.event, "data")
        self.assertEqual(event.data, {
            "resource": "users",
            "data": {"id": 1, "name": "Test"}
        })
    
    def test_create_notification_event(self):
        """Test creating a notification event."""
        event = create_notification_event(
            "Success", 
            "Operation completed", 
            "info",
            [{"label": "View", "action": "view"}]
        )
        
        self.assertEqual(event.event, "notification")
        self.assertEqual(event.data["title"], "Success")
        self.assertEqual(event.data["message"], "Operation completed")
        self.assertEqual(event.data["level"], "info")
        self.assertEqual(event.data["actions"], [{"label": "View", "action": "view"}])
        self.assertEqual(event.priority, EventPriority.HIGH)  # Default for notifications


if __name__ == "__main__":
    unittest.main()