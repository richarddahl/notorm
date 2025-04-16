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
"""

# Domain entities (DDD)
from uno.meta.entities import MetaType, MetaRecord

# Models
from uno.meta.models import MetaTypeModel, MetaRecordModel

# Services
from uno.meta.services import MetaTypeService, MetaRecordService

# Repositories 
from uno.meta.repositories import MetaTypeRepository, MetaRecordRepository

# Domain services and repositories
from uno.meta.domain_services import (
    MetaTypeDomainService,
    MetaRecordDomainService,
)
from uno.meta.domain_repositories import (
    MetaTypeDomainRepository,
    MetaRecordDomainRepository,
)

__all__ = [
    # Domain Entities (DDD)
    "MetaType",
    "MetaRecord",
    
    # Models
    "MetaTypeModel",
    "MetaRecordModel",
    
    # Services
    "MetaTypeService",
    "MetaRecordService",
    
    # Repositories
    "MetaTypeRepository",
    "MetaRecordRepository",
    
    # Domain services and repositories
    "MetaTypeDomainService",
    "MetaRecordDomainService",
    "MetaTypeDomainRepository",
    "MetaRecordDomainRepository",
]
