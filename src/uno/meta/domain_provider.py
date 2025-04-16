"""
Dependency injection provider for the Meta domain services.

This module integrates the meta domain services and repositories with
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
    logger = logging.getLogger("uno.meta")
    
    # Register repositories with their dependencies
    provider.register(
        MetaTypeRepository,
        lambda container: MetaTypeRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        MetaRecordRepository,
        lambda container: MetaRecordRepository(
            db_factory=container.resolve(DBManager),
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register MetaTypeService with its repository dependency
    provider.register(
        MetaTypeService,
        lambda container: MetaTypeService(
            repository=container.resolve(MetaTypeRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register MetaRecordService with its repository and MetaTypeService dependencies
    provider.register(
        MetaRecordService,
        lambda container: MetaRecordService(
            repository=container.resolve(MetaRecordRepository),
            meta_type_service=container.resolve(MetaTypeService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


def configure_meta_services(container):
    """
    Configure meta services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_meta_provider()
    provider.configure_container(container)