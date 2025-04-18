# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

"""
Domain repositories package.

This package contains domain-specific repository definitions and interfaces.
"""

from uno.domain.repositories.repository_adapter import (
    RepositoryAdapter,
)

__all__ = [
    "RepositoryAdapter",
]