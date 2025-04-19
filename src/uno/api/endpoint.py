"""
Legacy endpoint classes for the UNO API.

DEPRECATED: This module is deprecated and will be removed in a future version.
Use the unified endpoint framework in `uno.api.endpoint` instead.
"""

import warnings
from typing import Any, Dict, List, Optional, TypeVar, Union

from fastapi import FastAPI, APIRouter, Depends

# Display deprecation warning
warnings.warn(
    "The uno.api.endpoint module is deprecated and will be removed in a future version. "
    "Use the unified endpoint framework in uno.api.endpoint instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from the new location for backward compatibility
from uno.api.endpoint.compatibility import (
    LegacyUnoEndpoint as UnoEndpoint,
    LegacyEndpointAdapter,
    LegacyServiceEndpointAdapter,
    LegacyEntityEndpointAdapter,
    create_legacy_endpoint,
)

# Legacy endpoint classes
class CreateEndpoint(UnoEndpoint):
    """
    Legacy endpoint for creating resources.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(self, **kwargs):
        """Initialize a legacy create endpoint."""
        warnings.warn(
            "CreateEndpoint is deprecated. Use CrudEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)


class ViewEndpoint(UnoEndpoint):
    """
    Legacy endpoint for viewing resources.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(self, **kwargs):
        """Initialize a legacy view endpoint."""
        warnings.warn(
            "ViewEndpoint is deprecated. Use CrudEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)


class ListEndpoint(UnoEndpoint):
    """
    Legacy endpoint for listing resources.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(self, **kwargs):
        """Initialize a legacy list endpoint."""
        warnings.warn(
            "ListEndpoint is deprecated. Use CrudEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)


class UpdateEndpoint(UnoEndpoint):
    """
    Legacy endpoint for updating resources.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(self, **kwargs):
        """Initialize a legacy update endpoint."""
        warnings.warn(
            "UpdateEndpoint is deprecated. Use CrudEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)


class DeleteEndpoint(UnoEndpoint):
    """
    Legacy endpoint for deleting resources.
    
    DEPRECATED: Use CrudEndpoint from uno.api.endpoint.base instead.
    """
    
    def __init__(self, **kwargs):
        """Initialize a legacy delete endpoint."""
        warnings.warn(
            "DeleteEndpoint is deprecated. Use CrudEndpoint from uno.api.endpoint.base instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**kwargs)