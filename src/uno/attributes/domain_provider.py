"""
Dependency injection provider for the Attributes domain services.

This module integrates the attributes domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from uno.attributes.entities import (
    Attribute,
    AttributeType,
)
from uno.attributes.domain_repositories import (
    AttributeRepository,
    AttributeTypeRepository,
)
from uno.attributes.domain_services import (
    AttributeService,
    AttributeTypeService,
)


@lru_cache(maxsize=1)
def get_attributes_provider() -> UnoServiceProvider:
    """
    Get the Attributes module service provider.
    
    Returns:
        A configured service provider for the Attributes module
    """
    provider = UnoServiceProvider("attributes")
    
    # Register repositories
    provider.register(AttributeRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(AttributeTypeRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services
    provider.register(AttributeService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(AttributeTypeService, lifecycle=ServiceLifecycle.SCOPED)
    
    return provider


def configure_attributes_services(container):
    """
    Configure attributes services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_attributes_provider()
    provider.configure_container(container)


def create_attribute_service_factory(
    attribute_repo: Optional[AttributeRepository] = None,
    attribute_type_service: Optional[AttributeTypeService] = None
):
    """
    Create a factory function for AttributeService.
    
    This function creates a factory that can be used with the dependency
    injection system to create AttributeService instances with specific
    dependencies.
    
    Args:
        attribute_repo: Optional repository for attributes
        attribute_type_service: Optional service for attribute types
        
    Returns:
        A factory function for creating AttributeService instances
    """
    def create_service():
        return AttributeService(
            repository=attribute_repo,
            attribute_type_service=attribute_type_service
        )
    
    return create_service