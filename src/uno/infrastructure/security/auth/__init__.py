"""
Security authentication module.

DEPRECATED: This module is maintained for backward compatibility only.
Use the unified endpoint auth framework in `uno.api.endpoint.auth` instead.
"""

import warnings

warnings.warn(
    "The uno.infrastructure.security.auth module is deprecated and will be removed in a future version. "
    "Use the unified endpoint auth framework in uno.api.endpoint.auth instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import new implementation for backward compatibility
from uno.api.endpoint.auth import (
    AuthenticationBackend,
    AuthenticationError,
    AuthorizationError,
    JWTAuthBackend,
    Permission,
    Role,
    User,
    UserContext,
    get_user_context,
    requires_auth,
    setup_auth,
)