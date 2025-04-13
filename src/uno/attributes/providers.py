# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Dependency injection provider for the attributes module.

This module registers the attributes services and repositories with the
dependency injection container.
"""

import logging
import inject

from uno.dependencies.interfaces import ServiceProvider
from uno.database.db_manager import DBManager
from uno.attributes.interfaces import (
    AttributeRepositoryProtocol,
    AttributeTypeRepositoryProtocol,
    AttributeServiceProtocol,
    AttributeTypeServiceProtocol,
)
from uno.attributes.repositories import (
    AttributeRepository,
    AttributeTypeRepository,
)
from uno.attributes.services import (
    AttributeService,
    AttributeTypeService,
)


class AttributesServiceProvider(ServiceProvider):
    """Service provider for the attributes module."""
    
    def register_services(self, binder):
        """Register attributes services with the dependency injection container."""
        logger = logging.getLogger(__name__)
        
        # Get db_manager from container
        db_manager = inject.instance(DBManager)
        
        # Create repositories
        attribute_repository = AttributeRepository(db_manager)
        attribute_type_repository = AttributeTypeRepository(db_manager)
        
        # Create services
        attribute_service = AttributeService(
            attribute_repository=attribute_repository,
            attribute_type_repository=attribute_type_repository,
            db_manager=db_manager,
            logger=logger,
        )
        
        attribute_type_service = AttributeTypeService(
            attribute_type_repository=attribute_type_repository,
            db_manager=db_manager,
            logger=logger,
        )
        
        # Bind interfaces to implementations
        binder.bind(AttributeRepositoryProtocol, attribute_repository)
        binder.bind(AttributeTypeRepositoryProtocol, attribute_type_repository)
        binder.bind(AttributeServiceProtocol, attribute_service)
        binder.bind(AttributeTypeServiceProtocol, attribute_type_service)
        
        logger.info("Registered attributes services")