# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Meta module for Uno.

This module provides a foundational system for tracking types and records in the application.
It serves as a registry for tracking meta-information about objects in the system and
enables features like the knowledge graph, attributes, and values to work.

Key components:
- Domain Entities: Core business objects with behavior
  - MetaType: Represents types of objects in the system
  - MetaRecord: Represents instances of meta types
- Repository Pattern: Data access following domain-driven design
- Domain Services: Business logic for meta information
- API Integration: Register standardized API endpoints
"""

# Domain entities (DDD)
from uno.meta.entities import MetaType, MetaRecord

# Domain repositories (DDD)
from uno.meta.domain_repositories import (
    MetaTypeRepository,
    MetaRecordRepository,
)

# Domain services (DDD)
from uno.meta.domain_services import (
    MetaTypeService,
    MetaRecordService,
)

# Dependency provider
from uno.meta.domain_provider import (
    get_meta_provider,
    configure_meta_services,
)

# Domain endpoints
from uno.meta.domain_endpoints import register_meta_routers

__all__ = [
    # Domain Entities (DDD)
    "MetaType",
    "MetaRecord",
    
    # Domain Repositories (DDD)
    "MetaTypeRepository",
    "MetaRecordRepository",
    
    # Domain Services (DDD)
    "MetaTypeService",
    "MetaRecordService",
    
    # Dependency Injection
    "get_meta_provider",
    "configure_meta_services",
    
    # API Integration
    "register_meta_routers",
]
