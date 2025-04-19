"""
Dependency injection provider for the Values domain services.

This module integrates the values domain services and repositories with
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
from uno.values.domain_repositories import (
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



def configure_values_services(container):
    """Configure values services in the DI container."""
    logger = logging.getLogger("uno.values")

    # Register repositories
    container.register(
        AttachmentRepository,
        lambda c: AttachmentRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        BooleanValueRepository,
        lambda c: BooleanValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DateTimeValueRepository,
        lambda c: DateTimeValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DateValueRepository,
        lambda c: DateValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DecimalValueRepository,
        lambda c: DecimalValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        IntegerValueRepository,
        lambda c: IntegerValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        TextValueRepository,
        lambda c: TextValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        TimeValueRepository,
        lambda c: TimeValueRepository(db_manager=c.resolve(DBManager), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )

    # Register services
    container.register(
        AttachmentService,
        lambda c: AttachmentService(repository=c.resolve(AttachmentRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        BooleanValueService,
        lambda c: BooleanValueService(repository=c.resolve(BooleanValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DateTimeValueService,
        lambda c: DateTimeValueService(repository=c.resolve(DateTimeValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DateValueService,
        lambda c: DateValueService(repository=c.resolve(DateValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        DecimalValueService,
        lambda c: DecimalValueService(repository=c.resolve(DecimalValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        IntegerValueService,
        lambda c: IntegerValueService(repository=c.resolve(IntegerValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        TextValueService,
        lambda c: TextValueService(repository=c.resolve(TextValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    container.register(
        TimeValueService,
        lambda c: TimeValueService(repository=c.resolve(TimeValueRepository), logger=logger),
        lifecycle=ServiceLifecycle.SCOPED,
    )


