"""
Minimal test for the event system components.
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

# Add src to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src')))

# Event test
def test_event_creation():
    """Test basic event creation."""
    from uno.core.events.event import Event
    
    class TestEvent(Event):
        data: str
        value: int
    
    event = TestEvent(data="test", value=123)
    
    assert event.event_type == "test_event"
    assert event.data == "test"
    assert event.value == 123
    assert event.occurred_at is not None
    
    # Test serialization
    event_dict = event.to_dict()
    assert event_dict["data"] == "test"
    assert event_dict["value"] == 123
    
    # Test with_metadata
    new_event = event.with_metadata(correlation_id="corr-123")
    assert new_event.correlation_id == "corr-123"
    assert new_event.data == event.data
    assert new_event.value == event.value

# Run test directly if file is executed
if __name__ == "__main__":
    test_event_creation()
    print("All tests passed!")