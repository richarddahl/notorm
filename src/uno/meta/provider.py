"""
Dependency injection provider for the Meta domain.

This module registers all repositories and services for the Meta domain with the DI container.
Use this as the canonical place for all DI registrations in uno.meta.
"""

import logging
from uno.dependencies.modern_provider import ServiceLifecycle
from uno.meta.domain_repositories import (
    MetaTypeRepository,
    MetaRecordRepository,
)
from uno.meta.domain_services import (
    MetaTypeService,
    MetaRecordService,
)

def configure_meta_services(container):
    """Configure meta services in the DI container."""
    logger = logging.getLogger("uno.meta")

    # Register repositories
    container.register(
        MetaTypeRepository,
        lambda c: MetaTypeRepository(),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        MetaRecordRepository,
        lambda c: MetaRecordRepository(),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # Register services
    container.register(
        MetaTypeService,
        lambda c: MetaTypeService(repository=c.resolve(MetaTypeRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        MetaRecordService,
        lambda c: MetaRecordService(
            repository=c.resolve(MetaRecordRepository),
            meta_type_service=c.resolve(MetaTypeService),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
