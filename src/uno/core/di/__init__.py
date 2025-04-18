"""
Dependency Injection Module

This module provides a unified dependency injection system for the UNO framework.
It defines protocols and implementations for dependency resolution, container management,
and lifetime scopes.
"""

from uno.core.di.protocols import (
    ProviderProtocol,
    ContainerProtocol,
    ScopeProtocol,
    ServiceLifetime,
    FactoryProtocol
)
from uno.core.di.container import Container
from uno.core.di.provider import Provider
from uno.core.di.scope import Scope

__all__ = [
    # Protocols
    'ProviderProtocol',
    'ContainerProtocol',
    'ScopeProtocol',
    'FactoryProtocol',
    'ServiceLifetime',
    
    # Implementations
    'Container',
    'Provider',
    'Scope',
]