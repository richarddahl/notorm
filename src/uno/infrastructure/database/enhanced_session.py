"""
DEPRECATED: This module has been replaced by the new database provider.

Please use uno.infrastructure.database.provider.DatabaseProvider.async_session instead.

This file will be removed in a future version.
"""

import warnings

warnings.warn(
    "The uno.infrastructure.database.enhanced_session module is deprecated and will be removed "
    "in a future version. Use uno.infrastructure.database.provider.DatabaseProvider.async_session instead.",
    DeprecationWarning,
    stacklevel=2,
)

# No re-export since the new provider uses context managers for sessions