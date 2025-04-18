# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Data Transfer Object (DTO) module for the Uno framework.

This module provides base classes and utilities for creating and managing DTOs
that facilitate data transfer between different layers of the application, including
validation, serialization, and API documentation.
"""

from uno.core.base.dto import BaseDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO
from .manager import DTOManager, get_dto_manager

__all__ = [
    "BaseDTO",
    "DTOConfig",
    "PaginatedListDTO",
    "WithMetadataDTO",
    "DTOManager",
    "get_dto_manager",
]
