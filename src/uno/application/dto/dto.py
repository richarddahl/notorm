# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Application-specific DTO definitions for the Uno framework.

This module provides DTO classes for the application layer, building on the
base DTO classes from the core module.
"""

# Re-export items from the core base DTO module
from uno.core.base.dto import (
    BaseDTO,
    DTOConfig,
    PaginatedListDTO,
    WithMetadataDTO,
)

# Provide backward compatibility type alias for UnoDTO
# Ideally, all code should be migrated to use BaseDTO instead
UnoDTO = BaseDTO