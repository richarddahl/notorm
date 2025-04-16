# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Unit tests for schema manager integration with domain entities.

These tests demonstrate how the SchemaManagerService works with domain entities
in the Domain-Driven Design approach.
"""

import pytest
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4

from uno.schema.services import SchemaManagerService
from uno.schema.schema import UnoSchema, UnoSchemaConfig


# Sample domain entities for testing
class Address:
    """Value object representing an address."""
    
    def __init__(self, street: str, city: str, state: str, zip_code: str):
        self.street = street
        self.city = city
        self.state = state
        self.zip_code = zip_code
        
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code
        }


class Customer:
    """Domain entity representing a customer."""
    
    def __init__(
        self, 
        id: UUID,
        name: str,
        email: str,
        address: Optional[Address] = None,
        phone: Optional[str] = None,
        active: bool = True,
        created_at: Optional[str] = None,
        updated_at: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.address = address
        self.phone = phone
        self.active = active
        self.created_at = created_at
        self.updated_at = updated_at
        self.events = []  # Domain events list
        
    @classmethod
    def create(cls, name: str, email: str, **kwargs) -> "Customer":
        """Factory method to create a new customer."""
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            **kwargs
        )
        
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        result = {
            "id": str(self.id),
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "active": self.active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        
        if self.address:
            result["address"] = self.address.to_dict()
            
        return result


class TestSchemaManagerDomainIntegration:
    """Tests for integrating SchemaManagerService with domain entities."""
    
    def test_create_dto_from_model(self):
        """Test creating DTOs from domain entities."""
        # Create schema manager
        schema_manager = SchemaManagerService()
        
        # Create DTOs from Customer entity
        customer_dto = schema_manager.create_dto_from_model(
            model_type=Customer,
            dto_name="CustomerDTO",
            exclude_fields={"events"}
        )
        
        # Check DTO structure
        assert hasattr(customer_dto, "model_fields")
        assert "id" in customer_dto.model_fields
        assert "name" in customer_dto.model_fields
        assert "email" in customer_dto.model_fields
        assert "address" in customer_dto.model_fields
        assert "phone" in customer_dto.model_fields
        assert "active" in customer_dto.model_fields
        assert "created_at" in customer_dto.model_fields
        assert "updated_at" in customer_dto.model_fields
        assert "events" not in customer_dto.model_fields
        
        # Create a DTO with all optional fields for updates
        update_dto = schema_manager.create_dto_from_model(
            model_type=Customer,
            dto_name="CustomerUpdateDTO",
            exclude_fields={"id", "events", "created_at", "updated_at"},
            make_optional=True
        )
        
        # Check update DTO structure
        assert hasattr(update_dto, "model_fields")
        assert "id" not in update_dto.model_fields
        assert "name" in update_dto.model_fields
        assert "email" in update_dto.model_fields
        assert "address" in update_dto.model_fields
        assert "phone" in update_dto.model_fields
        assert "active" in update_dto.model_fields
        assert "created_at" not in update_dto.model_fields
        assert "updated_at" not in update_dto.model_fields
        assert "events" not in update_dto.model_fields
        
        # All fields should be optional in the update DTO
        for field_name, field in update_dto.model_fields.items():
            from typing import get_origin, Union, Optional
            assert get_origin(field.annotation) == Union
        
    def test_create_api_schemas(self):
        """Test creating a complete set of API schemas for a domain entity."""
        # Create schema manager
        schema_manager = SchemaManagerService()
        
        # Generate API schemas
        schemas = schema_manager.create_api_schemas(Customer)
        
        # Check all expected schemas were created
        assert "detail" in schemas
        assert "create" in schemas
        assert "update" in schemas
        assert "list" in schemas
        
        # Check the detail schema
        detail_schema = schemas["detail"]
        assert "id" in detail_schema.model_fields
        assert "name" in detail_schema.model_fields
        assert "email" in detail_schema.model_fields
        assert "address" in detail_schema.model_fields
        assert "active" in detail_schema.model_fields
        
        # Check the create schema
        create_schema = schemas["create"]
        assert "id" not in create_schema.model_fields  # ID is excluded for creation
        assert "name" in create_schema.model_fields
        assert "email" in create_schema.model_fields
        assert "created_at" not in create_schema.model_fields
        
        # Check the update schema (all fields optional)
        update_schema = schemas["update"]
        assert "id" not in update_schema.model_fields
        assert "name" in update_schema.model_fields
        
        # All fields in update schema should be optional
        for field_name, field in update_schema.model_fields.items():
            from typing import get_origin, Union, Optional
            assert get_origin(field.annotation) == Union
            
        # Check the list schema
        list_schema = schemas["list"]
        assert "items" in list_schema.model_fields
        assert "total" in list_schema.model_fields
        assert "page" in list_schema.model_fields
        assert "page_size" in list_schema.model_fields
        
    def test_pydantic_conversion(self):
        """Test using the generated schemas with actual domain entities."""
        # Create a domain entity
        address = Address("123 Main St", "Anytown", "CA", "12345")
        customer = Customer.create(
            name="Jane Smith",
            email="jane@example.com",
            address=address,
            phone="555-123-4567"
        )
        
        # Create schema manager and generate schemas
        schema_manager = SchemaManagerService()
        schemas = schema_manager.create_api_schemas(Customer)
        
        # Convert domain entity to detail DTO
        customer_dict = customer.to_dict()
        detail_dto = schemas["detail"](**customer_dict)
        
        # Check conversion
        assert detail_dto.id == str(customer.id)
        assert detail_dto.name == customer.name
        assert detail_dto.email == customer.email
        assert detail_dto.phone == customer.phone
        
        # The address is represented as a dict in the DTO
        assert isinstance(detail_dto.address, dict)
        assert detail_dto.address["street"] == customer.address.street
        assert detail_dto.address["city"] == customer.address.city
        
        # Create an update DTO with partial data
        update_data = {
            "name": "Jane Smith-Jones",
            "phone": "555-987-6543"
        }
        update_dto = schemas["update"](**update_data)
        
        # Check update DTO
        assert update_dto.name == "Jane Smith-Jones"
        assert update_dto.phone == "555-987-6543"
        # Fields not specified should have default values
        assert update_dto.email is None
        assert update_dto.address is None
        
        # Check serialization to dict
        dto_dict = detail_dto.model_dump()
        assert dto_dict["id"] == str(customer.id)
        assert dto_dict["name"] == customer.name
        assert dto_dict["email"] == customer.email
        assert dto_dict["phone"] == customer.phone