# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Dict, Any, Type, Optional

from uno.messaging.domain_repositories import MessageRepository, MessageRepositoryProtocol
from uno.messaging.domain_services import MessageDomainService, MessageDomainServiceProtocol
from uno.messaging.schemas import MessageSchemaManager


def configure_messaging_services(container):
    """Configure dependency injection for messaging module using the DI container."""
    # Register repositories
    container.register(MessageRepositoryProtocol, lambda c: MessageRepository(), lifecycle="scoped")

    # Register services
    container.register(MessageDomainServiceProtocol, lambda c: MessageDomainService(), lifecycle="scoped")

    # Register schema managers
    container.register(MessageSchemaManager, lambda c: MessageSchemaManager(), lifecycle="singleton")