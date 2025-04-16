# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
API integration for the attributes module.

This module provides a convenient way to register attribute and attribute type endpoints
with a FastAPI application using both legacy service-based and modern domain-driven
approaches.
"""

from typing import Dict, List, Any, Optional, Union
from fastapi import FastAPI, Depends, Security, APIRouter

# Legacy service-based approach
from uno.attributes.services import AttributeService, AttributeTypeService
from uno.attributes.endpoints import create_attribute_endpoints, create_attribute_type_endpoints

# Domain-driven approach
from uno.api.endpoint_factory import UnoEndpointFactory
from uno.api.repository_adapter import RepositoryAdapter
from uno.attributes.domain_repositories import AttributeTypeRepository, AttributeRepository
from uno.attributes.entities import AttributeType, Attribute
from uno.attributes.schemas import AttributeTypeSchemaManager, AttributeSchemaManager
from uno.attributes.domain_services import AttributeTypeService as AttributeTypeDomainService
from uno.attributes.domain_services import AttributeService as AttributeDomainService


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
    Register all attribute and attribute type endpoints with a FastAPI router using the legacy approach.
    
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


def register_domain_attribute_endpoints(
    app_or_router: Union[FastAPI, APIRouter],
    path_prefix: str = "/api/v1",
    dependencies: List[Any] = None,
    include_auth: bool = True,
    attribute_type_repository: Optional[AttributeTypeRepository] = None,
    attribute_repository: Optional[AttributeRepository] = None,
) -> Dict[str, List[Any]]:
    """
    Register attribute endpoints with the FastAPI app or router using domain-driven design.
    
    This function creates RESTful API endpoints for the Attributes module, including
    CRUD operations for attribute types and attributes following DDD principles.
    
    Args:
        app_or_router: The FastAPI application or router to register the endpoints with
        path_prefix: Prefix for all endpoint URLs
        dependencies: List of dependencies to apply to all endpoints
        include_auth: Whether to include authentication dependencies
        attribute_type_repository: Repository for attribute types
        attribute_repository: Repository for attributes
        
    Returns:
        A dictionary containing the registered endpoints
        
    Raises:
        ValueError: If app_or_router is neither a FastAPI app nor an APIRouter
    """
    # Determine if app_or_router is a FastAPI app or an APIRouter
    is_app = isinstance(app_or_router, FastAPI)
    is_router = isinstance(app_or_router, APIRouter)
    
    if not (is_app or is_router):
        raise ValueError("app_or_router must be either a FastAPI app or an APIRouter")
    
    # Set up endpoint factory
    endpoint_factory = UnoEndpointFactory()
    
    # Create schema managers
    attribute_type_schema_manager = AttributeTypeSchemaManager()
    attribute_schema_manager = AttributeSchemaManager()
    
    # Create repositories if not provided
    if attribute_type_repository is None:
        attribute_type_repository = AttributeTypeRepository()
    
    if attribute_repository is None:
        attribute_repository = AttributeRepository()
    
    # Create default dependencies if none provided
    if dependencies is None:
        dependencies = []
        
        # Add authentication dependencies if requested
        if include_auth:
            # This would typically check for auth providers and add appropriate dependencies
            pass
    
    # Create endpoint target
    target = app_or_router
    
    # Create attribute type endpoints
    attribute_type_endpoints = endpoint_factory.create_endpoints(
        app=target if is_app else None,
        router=target if is_router else None,
        repository=attribute_type_repository,
        entity_type=AttributeType,
        schema_manager=attribute_type_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/attribute-types",
        endpoint_tags=["Attribute Types"],
        dependencies=dependencies,
    )
    
    # Create attribute endpoints
    attribute_endpoints = endpoint_factory.create_endpoints(
        app=target if is_app else None,
        router=target if is_router else None,
        repository=attribute_repository,
        entity_type=Attribute,
        schema_manager=attribute_schema_manager,
        endpoints=["Create", "View", "List", "Update", "Delete"],
        path_prefix=f"{path_prefix}/attributes",
        endpoint_tags=["Attributes"],
        dependencies=dependencies,
    )
    
    # Add custom relationship endpoints
    if is_app:
        app = target
        # Example of a custom relationship endpoint
        @app.get(
            f"{path_prefix}/attributes/{'{attribute_id}'}/values",
            tags=["Attributes"],
            summary="Get values for an attribute",
            dependencies=dependencies,
        )
        async def get_attribute_values(attribute_id: str):
            """Get all values associated with an attribute."""
            # Implementation would get the attribute and return its values
            attribute = await attribute_repository.get_by_id(attribute_id)
            if attribute is None:
                return []
            
            # In a real implementation, this would fetch the actual value objects
            return attribute.value_ids
    
    # Bundle and return all endpoints
    return {
        "attribute_type_endpoints": attribute_type_endpoints,
        "attribute_endpoints": attribute_endpoints,
    }