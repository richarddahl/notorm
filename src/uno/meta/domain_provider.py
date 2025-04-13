"""
Dependency injection provider for the Meta domain services.

This module integrates the meta domain services and repositories with
the dependency injection system, making them available throughout the application.
"""

from functools import lru_cache
from typing import Dict, Any, Optional, Type

from uno.dependencies.modern_provider import (
    UnoServiceProvider,
    ServiceLifecycle,
)
from uno.meta.entities import (
    MetaType,
    MetaRecord,
)
from uno.meta.domain_repositories import (
    MetaTypeRepository,
    MetaRecordRepository,
)
from uno.meta.domain_services import (
    MetaTypeService,
    MetaRecordService,
)


@lru_cache(maxsize=1)
def get_meta_provider() -> UnoServiceProvider:
    """
    Get the Meta module service provider.
    
    Returns:
        A configured service provider for the Meta module
    """
    provider = UnoServiceProvider("meta")
    
    # Register repositories
    provider.register(MetaTypeRepository, lifecycle=ServiceLifecycle.SCOPED)
    provider.register(MetaRecordRepository, lifecycle=ServiceLifecycle.SCOPED)
    
    # Register services with dependencies
    provider.register(MetaTypeService, lifecycle=ServiceLifecycle.SCOPED)
    
    # For MetaRecordService, configure it to use MetaTypeService
    def create_meta_record_service():
        meta_type_service = provider.get_service(MetaTypeService)
        repository = provider.get_service(MetaRecordRepository)
        return MetaRecordService(repository=repository, meta_type_service=meta_type_service)
    
    provider.register_factory(MetaRecordService, create_meta_record_service, lifecycle=ServiceLifecycle.SCOPED)
    
    return provider


def configure_meta_services(container):
    """
    Configure meta services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_meta_provider()
    provider.configure_container(container)