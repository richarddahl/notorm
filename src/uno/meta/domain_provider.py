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
    ServiceProvider,
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


def configure_meta_services(container):
    """Configure meta services in the DI container."""
    logger = logging.getLogger("uno.meta")

    # Register repositories
    container.register(
        MetaTypeRepository,
        lambda c: MetaTypeRepository(db_factory=c.resolve(DBManager)),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        MetaRecordRepository,
        lambda c: MetaRecordRepository(db_factory=c.resolve(DBManager)),
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


