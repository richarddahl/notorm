"""
DEPRECATED: This module has been replaced by the new database provider.

Please use uno.infrastructure.database.provider.ConnectionPool instead.

This file will be removed in a future version.
"""

import warnings

warnings.warn(
    "The uno.infrastructure.database.enhanced_connection_pool module is deprecated and will be removed "
    "in a future version. Use uno.infrastructure.database.provider.ConnectionPool instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export from new location for backward compatibility
from uno.infrastructure.database.provider import ConnectionPool as EnhancedConnectionPool