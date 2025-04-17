"""Test basic imports."""

import pytest

def test_import_unified_events():
    """Test importing unified_events module."""
    from uno.core.unified_events import DomainEvent, EventBus
    
    assert DomainEvent is not None
    assert EventBus is not None

def test_import_unified_services():
    """Test importing unified_services module."""
    from uno.domain.unified_services import DomainService, EntityService
    
    assert DomainService is not None
    assert EntityService is not None