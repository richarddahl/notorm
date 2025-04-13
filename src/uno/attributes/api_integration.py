# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API integration for the attributes module.

This module provides a convenient way to register attribute and attribute type endpoints
with a FastAPI application.
"""

from fastapi import APIRouter
from typing import List, Optional

from uno.attributes.services import AttributeService, AttributeTypeService
from uno.attributes.endpoints import create_attribute_endpoints, create_attribute_type_endpoints


def register_attribute_endpoints(
    router: APIRouter,
    attribute_service: AttributeService,
    attribute_type_service: AttributeTypeService,
    attribute_prefix: str = "/attributes",
    attribute_type_prefix: str = "/attribute-types",
    attribute_tags: List[str] = ["Attributes"],
    attribute_type_tags: List[str] = ["Attribute Types"]
):
    """
    Register all attribute and attribute type endpoints with a FastAPI router.
    
    Args:
        router: FastAPI router
        attribute_service: Attribute service instance
        attribute_type_service: Attribute type service instance
        attribute_prefix: API route prefix for attributes
        attribute_type_prefix: API route prefix for attribute types
        attribute_tags: API tags for attribute endpoints
        attribute_type_tags: API tags for attribute type endpoints
    """
    # Create attribute endpoints
    create_attribute_endpoints(
        router=router,
        attribute_service=attribute_service,
        prefix=attribute_prefix,
        tags=attribute_tags
    )
    
    # Create attribute type endpoints
    create_attribute_type_endpoints(
        router=router,
        attribute_type_service=attribute_type_service,
        prefix=attribute_type_prefix,
        tags=attribute_type_tags
    )
    
    return router