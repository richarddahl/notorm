# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
DEPRECATED: This module has been replaced by uno.dto.

To align with Domain-Driven Design principles, UnoSchema has been renamed to UnoDTO.
Please import from uno.dto instead of uno.schema.schema.

Example:
    from uno.dto import UnoDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO
"""

from uno.dto import UnoDTO, DTOConfig, PaginatedListDTO, WithMetadataDTO

# For backward compatibility
UnoSchema = UnoDTO
UnoSchemaConfig = DTOConfig
PaginatedList = PaginatedListDTO
WithMetadata = WithMetadataDTO