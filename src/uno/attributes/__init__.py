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

# Models (for ORM)
from uno.attributes.models import AttributeModel, AttributeTypeModel

# Interfaces
from uno.attributes.interfaces import (
    AttributeRepositoryProtocol,
    AttributeTypeRepositoryProtocol,
    AttributeServiceProtocol,
    AttributeTypeServiceProtocol,
)

# Repositories
from uno.attributes.repositories import AttributeRepository, AttributeTypeRepository

# Services
from uno.attributes.services import AttributeService, AttributeTypeService

# API integration
from uno.attributes.api_integration import register_attribute_endpoints

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
    
    # ORM Models
    "AttributeModel",
    "AttributeTypeModel",
    
    # Interfaces
    "AttributeRepositoryProtocol",
    "AttributeTypeRepositoryProtocol",
    "AttributeServiceProtocol",
    "AttributeTypeServiceProtocol",
    
    # Implementation classes
    "AttributeRepository",
    "AttributeTypeRepository",
    "AttributeService",
    "AttributeTypeService",
    
    # API integration
    "register_attribute_endpoints",
    
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
