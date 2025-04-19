# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

# Domain entities
from uno.messaging.entities import Message, MessageUser

# Domain repositories
from uno.messaging.domain_repositories import (
    MessageRepositoryProtocol,
    MessageRepository
)

# Domain services
from uno.messaging.domain_services import (
    MessageDomainServiceProtocol,
    MessageDomainService
)

# DTOs
from uno.messaging.dtos import (
    # Message DTOs
    MessageBaseDto, MessageCreateDto, MessageUpdateDto, MessageViewDto,
    MessageFilterParams, MessageListDto,
    
    # Message User DTOs
    MessageUserBaseDto, MessageUserViewDto
)

# Schema managers
from uno.messaging.schemas import MessageSchemaManager

# API integration
from uno.messaging.api_integration import register_messaging_endpoints
from uno.messaging.domain_endpoints import register_message_endpoints

# Domain provider

    configure_messaging_dependencies,
    get_messaging_di_config
)

# SQL Configuration
from uno.messaging.sqlconfigs import (
    MessageModelSQLConfig,
    MessageUserSQLConfig
)

__all__ = [
    # Entities
    'Message', 'MessageUser',
    
    # Repositories
    'MessageRepositoryProtocol', 'MessageRepository',
    
    # Services
    'MessageDomainServiceProtocol', 'MessageDomainService',
    
    # DTOs
    'MessageBaseDto', 'MessageCreateDto', 'MessageUpdateDto', 'MessageViewDto',
    'MessageFilterParams', 'MessageListDto',
    'MessageUserBaseDto', 'MessageUserViewDto',
    
    # Schema managers
    'MessageSchemaManager',
    
    # API integration
    'register_messaging_endpoints', 'register_message_endpoints',
    
    # Domain provider
    'configure_messaging_dependencies', 'get_messaging_di_config',
    
    # SQL Configuration
    'MessageModelSQLConfig', 'MessageUserSQLConfig'
]