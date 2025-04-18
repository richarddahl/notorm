# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Base classes for the core layer of the Uno framework.

This module provides base classes, interfaces, and utilities for the core layer.
"""

from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO
from uno.core.base.repository import (
    BaseRepository,
    SpecificationRepository,
    BatchRepository,
    StreamingRepository,
    CompleteRepository,
    RepositoryProtocol,
    SpecificationRepositoryProtocol,
    BatchRepositoryProtocol,
    StreamingRepositoryProtocol,
    FilterProtocol,
    FilterType,
)
from uno.core.base.service import (
    BaseService,
    BaseQueryService,
    ServiceProtocol,
    CrudServiceProtocol,
    QueryServiceProtocol,
)
from uno.core.base.error import BaseError

__all__ = [
    # DTO classes
    "BaseDTO",
    "DTOConfig",
    "PaginatedListDTO",
    "WithMetadataDTO",
    
    # Repository classes and protocols
    "BaseRepository",
    "SpecificationRepository",
    "BatchRepository",
    "StreamingRepository",
    "CompleteRepository",
    "RepositoryProtocol",
    "SpecificationRepositoryProtocol",
    "BatchRepositoryProtocol",
    "StreamingRepositoryProtocol",
    "FilterProtocol",
    "FilterType",
    
    # Service classes and protocols
    "BaseService",
    "BaseQueryService",
    "ServiceProtocol",
    "CrudServiceProtocol",
    "QueryServiceProtocol",
    
    # Error classes
    "BaseError",
]