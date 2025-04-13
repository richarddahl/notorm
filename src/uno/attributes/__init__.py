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
- AttributeType: Defines the structure and constraints of attributes
- Attribute: Represents a specific attribute associated with objects
- API Integration: FastAPI endpoints for attribute operations
"""

from uno.attributes.models import AttributeModel, AttributeTypeModel
from uno.attributes.objs import Attribute, AttributeType
from uno.attributes.interfaces import AttributeRepositoryProtocol, AttributeTypeRepositoryProtocol, AttributeServiceProtocol, AttributeTypeServiceProtocol
from uno.attributes.repositories import AttributeRepository, AttributeTypeRepository
from uno.attributes.services import AttributeService, AttributeTypeService
from uno.attributes.api_integration import register_attribute_endpoints

__all__ = [
    # Core models and objects
    "Attribute",
    "AttributeType",
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
]