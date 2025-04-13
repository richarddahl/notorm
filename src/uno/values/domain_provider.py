"""
Dependency injection provider for the Values domain services.

This module integrates the values domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from uno.values.entities import (
    Attachment,
    BooleanValue,
    DateTimeValue,
    DateValue,
    DecimalValue,
    IntegerValue,
    TextValue,
    TimeValue,
)
from uno.values.repositories import (
    AttachmentRepository,
    BooleanValueRepository,
    DateTimeValueRepository,
    DateValueRepository,
    DecimalValueRepository,
    IntegerValueRepository,
    TextValueRepository,
    TimeValueRepository,
)
from uno.values.domain_services import (
    AttachmentService,
    BooleanValueService,
    DateTimeValueService,
    DateValueService,
    DecimalValueService,
    IntegerValueService,
    TextValueService,
    TimeValueService,
)


@lru_cache(maxsize=1)
def get_values_provider() -> UnoServiceProvider:
    """
    Get the Values module service provider.
    
    Returns:
        A configured service provider for the Values module
    """
    provider = UnoServiceProvider("values")
    
    # Register repositories
    provider.register(AttachmentRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(BooleanValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DateTimeValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DateValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DecimalValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(IntegerValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TextValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TimeValueRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services
    provider.register(AttachmentService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(BooleanValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DateTimeValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DateValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(DecimalValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(IntegerValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TextValueService, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(TimeValueService, lifecycle=ServiceLifecycle.SCOPED)
    
    return provider


def configure_values_services(container):
    """
    Configure values services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_values_provider()
    provider.configure_container(container)