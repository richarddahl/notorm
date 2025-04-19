"""
Compatibility module for service endpoint adapters.

DEPRECATED: This module is maintained for backward compatibility only.
Use the unified endpoint framework in `uno.api.endpoint` instead.
"""

import warnings

warnings.warn(
    "The uno.api.service_endpoint_adapter module is deprecated and will be removed in a future version. "
    "Use the unified endpoint framework in uno.api.endpoint instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import new implementation classes for backward compatibility
from uno.api.endpoint.base import BaseEndpoint, CommandEndpoint, QueryEndpoint
from uno.api.endpoint.cqrs import CommandHandler, QueryHandler