# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
The attributes module provides a flexible system for defining and
attaching dynamic attributes to objects in the UNO framework.

The module allows for defining attribute types with specific constraints,
creating attribute instances, and associating attribute values with objects.
It integrates with the graph database to enable complex attribute-based queries.

Key components:
- AttributeType: Defines the structure and constraints of attributes (domain entity)
- Attribute: Represents a specific attribute associated with objects (domain entity)
- Repository Pattern: Follows domain-driven design for data access
- Domain Services: Encapsulates business logic for attributes
- API Integration: FastAPI endpoints for attribute operations
"""

# Domain entities (DDD)
from uno.attributes.entities import Attribute, AttributeType, MetaTypeRef, QueryRef

# Domain repositories (DDD)
from uno.attributes.domain_repositories import AttributeRepository, AttributeTypeRepository

# Domain services (DDD)
from uno.attributes.domain_services import AttributeService, AttributeTypeService

# Domain provider
from uno.attributes.domain_provider import get_attributes_provider, configure_attributes_services

# Domain endpoints
from uno.attributes.domain_endpoints import register_attribute_routers

# Error types
from uno.attributes.errors import (
    AttributeErrorCode,
    AttributeNotFoundError,
    AttributeTypeNotFoundError,
    AttributeInvalidDataError,
    AttributeTypeInvalidDataError,
    AttributeValueError,
    AttributeServiceError,
    AttributeTypeServiceError,
    register_attribute_errors,
)

# Register attribute error codes in the catalog
try:
    register_attribute_errors()
except Exception as e:
    import logging

    logger = logging.getLogger(__name__)
    logger.error(f"Failed to register attribute error codes: {e}")

__all__ = [
    # Domain Entities (DDD)
    "Attribute",
    "AttributeType",
    "MetaTypeRef",
    "QueryRef",
    
    # Domain Repositories (DDD)
    "AttributeRepository",
    "AttributeTypeRepository",
    
    # Domain Services (DDD)
    "AttributeService",
    "AttributeTypeService",
    
    # Dependency Injection
    "get_attributes_provider",
    "configure_attributes_services",
    
    # API Integration
    "register_attribute_routers",
    
    # Error types
    "AttributeErrorCode",
    "AttributeNotFoundError",
    "AttributeTypeNotFoundError",
    "AttributeInvalidDataError",
    "AttributeTypeInvalidDataError",
    "AttributeValueError",
    "AttributeServiceError",
    "AttributeTypeServiceError",
]
