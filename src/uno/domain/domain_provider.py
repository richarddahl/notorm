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


@lru_cache(maxsize=1)
def get_values_provider() -> UnoServiceProvider:
    """
    Get the Values module service provider.
    
    Returns:
        A configured service provider for the Values module
    """
    provider = UnoServiceProvider("values")
    logger = logging.getLogger("uno.values")
    
    # Register dependencies
    
    # Register repositories with their dependencies
    provider.register(
        AttachmentRepository,
        lambda container: AttachmentRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        BooleanValueRepository,
        lambda container: BooleanValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DateTimeValueRepository,
        lambda container: DateTimeValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DateValueRepository,
        lambda container: DateValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DecimalValueRepository,
        lambda container: DecimalValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        IntegerValueRepository,
        lambda container: IntegerValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        TextValueRepository,
        lambda container: TextValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        TimeValueRepository,
        lambda container: TimeValueRepository(
            db_manager=container.resolve(DBManager),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    # Register services with their repository dependencies
    provider.register(
        AttachmentService,
        lambda container: AttachmentService(
            repository=container.resolve(AttachmentRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        BooleanValueService,
        lambda container: BooleanValueService(
            repository=container.resolve(BooleanValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DateTimeValueService,
        lambda container: DateTimeValueService(
            repository=container.resolve(DateTimeValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DateValueService,
        lambda container: DateValueService(
            repository=container.resolve(DateValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        DecimalValueService,
        lambda container: DecimalValueService(
            repository=container.resolve(DecimalValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        IntegerValueService,
        lambda container: IntegerValueService(
            repository=container.resolve(IntegerValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        TextValueService,
        lambda container: TextValueService(
            repository=container.resolve(TextValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    provider.register(
        TimeValueService,
        lambda container: TimeValueService(
            repository=container.resolve(TimeValueRepository),
            logger=logger,
        ),
        lifecycle=ServiceLifecycle.SCOPED,
    )
    
    return provider


def configure_values_services(container):
    """
    Configure values services in the dependency container.
    
    Args:
        container: The dependency container to configure
    """
    provider = get_values_provider()
    provider.configure_container(container)