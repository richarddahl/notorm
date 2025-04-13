# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Dependency injection provider for the values module.

This module registers the values services and repositories with the
dependency injection container.
"""

import logging
import inject

from uno.dependencies.interfaces import ServiceProvider
from uno.database.db_manager import DBManager
from uno.values.interfaces import ValueServiceProtocol
from uno.values.repositories import (
    BooleanValueRepository,
    TextValueRepository,
    IntegerValueRepository,
    DecimalValueRepository,
    DateValueRepository,
    DateTimeValueRepository,
    TimeValueRepository,
    AttachmentRepository,
)
from uno.values.services import ValueService


class ValuesServiceProvider(ServiceProvider):
    """Service provider for the values module."""
    
    def register_services(self, binder):
        """Register values services with the dependency injection container."""
        logger = logging.getLogger(__name__)
        
        # Get db_manager from container
        db_manager = inject.instance(DBManager)
        
        # Create repositories
        boolean_repository = BooleanValueRepository(db_manager)
        text_repository = TextValueRepository(db_manager)
        integer_repository = IntegerValueRepository(db_manager)
        decimal_repository = DecimalValueRepository(db_manager)
        date_repository = DateValueRepository(db_manager)
        datetime_repository = DateTimeValueRepository(db_manager)
        time_repository = TimeValueRepository(db_manager)
        attachment_repository = AttachmentRepository(db_manager)
        
        # Create value service
        value_service = ValueService(
            boolean_repository=boolean_repository,
            text_repository=text_repository,
            integer_repository=integer_repository,
            decimal_repository=decimal_repository,
            date_repository=date_repository,
            datetime_repository=datetime_repository,
            time_repository=time_repository,
            attachment_repository=attachment_repository,
            db_manager=db_manager,
            logger=logger,
        )
        
        # Bind interfaces to implementations
        binder.bind(ValueServiceProtocol, value_service)
        
        logger.info("Registered values services")