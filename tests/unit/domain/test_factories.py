"""
Tests for the domain factories module.
"""

# Python 3.13 compatibility workaround for dataclasses
import sys
if sys.version_info[:2] >= (3, 13):
    # For Python 3.13+, we patch the abc module's update_abstractmethods function
    # to avoid the dictionary keys changed during iteration error
    import abc
    
    _original_update_abstractmethods = abc.update_abstractmethods
    
    def _patched_update_abstractmethods(cls):
        """
        A patched version of abc.update_abstractmethods that handles dictionary modification safely.
        
        This is a workaround for a Python 3.13 issue with dataclasses where the original
        implementation can cause a "dictionary keys changed during iteration" error.
        """
        try:
            return _original_update_abstractmethods(cls)
        except RuntimeError as e:
            if "dictionary keys changed during iteration" in str(e):
                # Just return cls without modifying abstract methods
                # This is safe for our use case with dataclasses
                return cls
            # Re-raise any other RuntimeError
            raise
    
    # Apply the patch
    abc.update_abstractmethods = _patched_update_abstractmethods

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Set, Optional

from uno.domain.models import Entity, AggregateRoot, ValueObject, DomainEvent
from uno.domain.factories import (
    EntityFactory, AggregateFactory, ValueObjectFactory,
    create_entity_factory, create_aggregate_factory, create_value_factory,
    FactoryRegistry
)


# Test models
class UserCreatedEvent(DomainEvent):
    user_id: str
    username: str


class Address(ValueObject):
    street: str
    city: str
    state: str
    postal_code: str
    country: str = "US"
    
    def validate(self) -> None:
        if not self.street or not self.city:
            raise ValueError("Street and city are required")


class Email(ValueObject):
    value: str
    
    def validate(self) -> None:
        if not self.value or "@" not in self.value:
            raise ValueError("Invalid email format")


class User(Entity):
    username: str
    email: Optional[str] = None
    is_active: bool = True


class OrderItem(Entity):
    product_id: str
    quantity: int
    unit_price: float


class Order(AggregateRoot):
    customer_id: str
    status: str = "pending"
    
    def check_invariants(self) -> None:
        # An order must have at least one item
        if not any(isinstance(entity, OrderItem) for entity in self.get_child_entities()):
            raise ValueError("An order must have at least one item")


# Create factory classes
AddressFactory = create_value_factory(Address)
EmailFactory = create_value_factory(Email)
UserFactory = create_entity_factory(User)
OrderItemFactory = create_entity_factory(OrderItem)
OrderFactory = create_aggregate_factory(Order)


class TestEntityFactory:
    """Tests for the EntityFactory class."""
    
    def test_create_entity(self):
        """Test creating an entity with the factory."""
        user = UserFactory.create(username="testuser")
        
        assert isinstance(user, User)
        assert user.id is not None
        assert user.username == "testuser"
        assert user.is_active is True
        assert user.created_at is not None
        assert user.updated_at is None
    
    def test_create_with_explicit_id(self):
        """Test creating an entity with an explicit ID."""
        user_id = str(uuid4())
        user = UserFactory.create(id=user_id, username="testuser")
        
        assert user.id == user_id
    
    def test_create_with_events(self):
        """Test creating an entity with registered events."""
        event = UserCreatedEvent(user_id="123", username="testuser")
        user = UserFactory.create_with_events([event], username="testuser")
        
        assert isinstance(user, User)
        assert len(user.clear_events()) == 1
        assert user.clear_events() == []  # Events should be cleared
    
    def test_reconstitute(self):
        """Test reconstituting an entity from a dictionary."""
        user_id = str(uuid4())
        created_at = datetime.now(timezone.utc)
        data = {
            "id": user_id,
            "username": "testuser",
            "is_active": False,
            "created_at": created_at,
            "updated_at": None
        }
        
        user = UserFactory.reconstitute(data)
        
        assert isinstance(user, User)
        assert user.id == user_id
        assert user.username == "testuser"
        assert user.is_active is False
        assert user.created_at == created_at
        assert user.updated_at is None


class TestAggregateFactory:
    """Tests for the AggregateFactory class."""
    
    def test_create_aggregate(self):
        """Test creating an aggregate with the factory."""
        order = OrderFactory.create(customer_id="cust-123")
        
        assert isinstance(order, Order)
        assert order.id is not None
        assert order.customer_id == "cust-123"
        assert order.status == "pending"
        assert order.created_at is not None
        assert order.updated_at is None
        assert order.version == 1
    
    def test_create_with_children(self):
        """Test creating an aggregate with child entities."""
        # Create child entities
        item1 = OrderItemFactory.create(product_id="prod-1", quantity=2, unit_price=29.99)
        item2 = OrderItemFactory.create(product_id="prod-2", quantity=1, unit_price=49.99)
        
        # Create order with items
        order = OrderFactory.create_with_children(
            [item1, item2],
            customer_id="cust-123"
        )
        
        assert isinstance(order, Order)
        assert len(order.get_child_entities()) == 2
        assert item1 in order.get_child_entities()
        assert item2 in order.get_child_entities()
    
    def test_check_invariants(self):
        """Test that invariants are checked when creating with children."""
        # This should pass because we're providing items
        item = OrderItemFactory.create(product_id="prod-1", quantity=2, unit_price=29.99)
        order = OrderFactory.create_with_children([item], customer_id="cust-123")
        assert isinstance(order, Order)
        
        # This should fail because an order needs at least one item
        with pytest.raises(ValueError, match="An order must have at least one item"):
            OrderFactory.create_with_children([], customer_id="cust-123")


class TestValueObjectFactory:
    """Tests for the ValueObjectFactory class."""
    
    def test_create_value_object(self):
        """Test creating a value object with the factory."""
        address = AddressFactory.create(
            street="123 Main St",
            city="Anytown",
            state="CA",
            postal_code="12345"
        )
        
        assert isinstance(address, Address)
        assert address.street == "123 Main St"
        assert address.city == "Anytown"
        assert address.state == "CA"
        assert address.postal_code == "12345"
        assert address.country == "US"  # Default value
    
    def test_validation(self):
        """Test that validation is performed when creating value objects."""
        # This should pass
        email = EmailFactory.create(value="user@example.com")
        assert isinstance(email, Email)
        assert email.value == "user@example.com"
        
        # This should fail validation
        with pytest.raises(ValueError, match="Invalid email format"):
            EmailFactory.create(value="invalid-email")
    
    def test_create_from_dict(self):
        """Test creating a value object from a dictionary."""
        data = {
            "street": "123 Main St",
            "city": "Anytown",
            "state": "CA",
            "postal_code": "12345",
            "country": "CA"  # Override default
        }
        
        address = AddressFactory.create_from_dict(data)
        
        assert isinstance(address, Address)
        assert address.street == "123 Main St"
        assert address.city == "Anytown"
        assert address.state == "CA"
        assert address.postal_code == "12345"
        assert address.country == "CA"


class TestFactoryRegistry:
    """Tests for the FactoryRegistry class."""
    
    def test_register_and_get_factories(self):
        """Test registering and retrieving factories."""
        registry = FactoryRegistry()
        
        # Register factories
        registry.register_entity_factory(User, UserFactory)
        registry.register_entity_factory(Order, OrderFactory)
        registry.register_value_factory(Address, AddressFactory)
        
        # Get factories
        user_factory = registry.get_entity_factory(User)
        order_factory = registry.get_entity_factory(Order)
        address_factory = registry.get_value_factory(Address)
        
        assert user_factory is UserFactory
        assert order_factory is OrderFactory
        assert address_factory is AddressFactory
    
    def test_unregistered_factory(self):
        """Test getting an unregistered factory."""
        registry = FactoryRegistry()
        
        with pytest.raises(KeyError, match="No factory registered for"):
            registry.get_entity_factory(User)
        
        with pytest.raises(KeyError, match="No factory registered for"):
            registry.get_value_factory(Address)
    
    def test_create_entity_with_registry(self):
        """Test creating an entity using the registry."""
        registry = FactoryRegistry()
        registry.register_entity_factory(User, UserFactory)
        
        # Get factory and create entity
        user_factory = registry.get_entity_factory(User)
        user = user_factory.create(username="testuser")
        
        assert isinstance(user, User)
        assert user.username == "testuser"