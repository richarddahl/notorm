"""
Test for the basic event implementation.
"""

import sys
import os
import json
from datetime import datetime

# Add src to Python path
sys.path.insert(0, os.path.abspath('src'))

from uno.core.events.basic import BasicEvent


def test_basic_event():
    """Test the basic event implementation."""
    # Create a test event
    event = BasicEvent(
        name="Test Event",
        value=123,
        aggregate_id="test-123"
    )
    
    # Check properties
    assert event.event_type == "basicevent"
    assert event.name == "Test Event"
    assert event.value == 123
    assert event.aggregate_id == "test-123"
    assert event.event_id is not None
    assert isinstance(event.occurred_at, datetime)
    
    # Test serialization
    event_dict = event.to_dict()
    assert event_dict["name"] == "Test Event"
    assert event_dict["value"] == 123
    assert event_dict["aggregate_id"] == "test-123"
    
    # Test to_json and from_dict
    json_str = event.to_json()
    parsed_dict = json.loads(json_str)
    assert parsed_dict["name"] == "Test Event"
    
    # Create from dictionary
    new_event = BasicEvent.from_dict(event_dict)
    assert new_event.name == event.name
    assert new_event.value == event.value
    assert new_event.aggregate_id == event.aggregate_id
    
    print("All tests passed!")


if __name__ == "__main__":
    test_basic_event()