"""
DEPRECATED: This module has been replaced by the new database provider.

Please use uno.infrastructure.database.provider instead.

This file will be removed in a future version.
"""

import warnings

warnings.warn(
    "The uno.infrastructure.database.db module is deprecated and will be removed "
    "in a future version. Use uno.infrastructure.database.provider instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from uno.infrastructure.database.provider import DatabaseProvider as UnoDB
from uno.infrastructure.database.provider import create_database_provider