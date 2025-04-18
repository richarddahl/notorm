"""
Dependency Injection System (Legacy)

This module is a transitional layer for migrating from the legacy dependency injection system
to the new system in uno.core.di. It re-exports the new system's components while providing
backward compatibility.

DEPRECATION WARNING: This entire module is deprecated and will be removed in a future
version. Use uno.core.di directly instead.
"""

import warnings

warnings.warn(
    "The uno.dependencies module is deprecated and will be removed in a future version. "
    "Use uno.core.di directly instead.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from the new DI system
from uno.core.di import (
    # Protocols
    ProviderProtocol,
    ContainerProtocol,
    ScopeProtocol,
    FactoryProtocol,
    ServiceLifetime,
    
    # Implementations
    Container,
    Provider,
    Scope,
)

# These imports are kept for backward compatibility during migration
# and should not be used in new code
from uno.core.di.protocols import ProviderProtocol as UnoServiceProviderProtocol
from uno.core.di.protocols import ContainerProtocol as DependencyContainerProtocol

# Legacy imports kept for backward compatibility - these will be removed in a future version
from uno.core.di.fastapi import Inject as inject_dependency
from uno.core.di.fastapi import cleanup_request_scope

__all__ = [
    # New system
    'ProviderProtocol',
    'ContainerProtocol',
    'ScopeProtocol',
    'FactoryProtocol',
    'ServiceLifetime',
    'Container',
    'Provider',
    'Scope',
    
    # Backward compatibility
    'UnoServiceProviderProtocol',
    'DependencyContainerProtocol',
    'inject_dependency',
    'cleanup_request_scope',
]