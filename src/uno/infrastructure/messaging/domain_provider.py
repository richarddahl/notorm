# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any, Type, Optional
import inject

from uno.messaging.domain_repositories import MessageRepository, MessageRepositoryProtocol
from uno.messaging.domain_services import MessageDomainService, MessageDomainServiceProtocol
from uno.messaging.schemas import MessageSchemaManager


def configure_messaging_dependencies(binder: inject.Binder) -> None:
    """Configure dependency injection for messaging module.
    
    Args:
        binder: The inject binder to configure
    """
    # Bind repositories
    binder.bind_to_provider(MessageRepositoryProtocol, MessageRepository)
    
    # Bind services
    binder.bind_to_provider(MessageDomainServiceProtocol, MessageDomainService)
    
    # Bind schema managers
    binder.bind(MessageSchemaManager, MessageSchemaManager())


def get_messaging_di_config() -> Dict[Type, Any]:
    """Get dependency injection configuration for messaging module.
    
    Returns:
        Dictionary mapping interface types to implementation types
    """
    return {
        MessageRepositoryProtocol: MessageRepository,
        MessageDomainServiceProtocol: MessageDomainService,
        MessageSchemaManager: MessageSchemaManager(),
    }