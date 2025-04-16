"""
Dependency injection provider for the Attributes domain services.

This module integrates the attributes domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

import logging
from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.database.db_manager import DBManager
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
    logger = logging.getLogger("uno.attributes")
    
    # Register repositories with their dependencies
    provider.register(
        AttributeTypeRepository,
        lambda container: AttributeTypeRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        AttributeRepository,
        lambda container: AttributeRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register services with their repository dependencies
    provider.register(
        AttributeTypeService,
        lambda container: AttributeTypeService(
            repository=container.resolve(AttributeTypeRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        AttributeService,
        lambda container: AttributeService(
            repository=container.resolve(AttributeRepository),
            attribute_type_service=container.resolve(AttributeTypeService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


def configure_attributes_services(container):
    """
    Configure attributes services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_attributes_provider()
    provider.configure_container(container)