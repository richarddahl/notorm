"""
Generic Feature Factory for Domain-Driven sub-packages.

This module provides a uniform API to load repository, service, and endpoint
modules for a given feature name, eliminating per-feature boilerplate.
"""

import importlib
from types import ModuleType
from typing import Any, Optional


def _import_module(feature: str, suffix: str) -> Optional[ModuleType]:
    """
    Dynamically import a module by feature name and suffix.
    Returns None if import fails.
    """
    module_name = f"uno.{feature}.{suffix}"
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None


class FeatureFactory:
    """
    Factory for loading DDD layers of a named feature.
    """
    def __init__(self, feature: str):
        self.feature = feature
        # Dynamically import modules
        self.repositories = _import_module(feature, "domain_repositories")
        self.services = _import_module(feature, "domain_services")
        self.endpoints = _import_module(feature, "domain_endpoints")

    def get_repositories(self) -> ModuleType:
        """Return the feature's domain_repositories module."""
        if self.repositories is None:
            raise ModuleNotFoundError(
                f"domain_repositories not found for feature '{self.feature}'"
            )
        return self.repositories

    def get_services(self) -> ModuleType:
        """Return the feature's domain_services module."""
        if self.services is None:
            raise ModuleNotFoundError(
                f"domain_services not found for feature '{self.feature}'"
            )
        return self.services

    def get_router(self) -> Any:
        """
        Return the feature's API router:
        - If module has attribute 'router', return it.
        - If module defines 'get_router()', call and return it.
        """
        if self.endpoints is None:
            raise ModuleNotFoundError(
                f"domain_endpoints not found for feature '{self.feature}'"
            )
        mod = self.endpoints
        # Direct router
        if hasattr(mod, "router"):
            return getattr(mod, "router")
        # Factory function
        factory = getattr(mod, "get_router", None)
        if callable(factory):
            return factory()
        raise AttributeError(
            f"No 'router' or 'get_router' in {mod.__name__}"  # noqa: E501
        )
    
    def get_routers(self) -> list[Any]:  # requires Python 3.9+
        """
        Collect all FastAPI APIRouter instances from the feature's endpoints module.
        """
        if self.endpoints is None:
            raise ModuleNotFoundError(
                f"domain_endpoints not found for feature '{self.feature}'"
            )
        mod = self.endpoints
        routers: list[Any] = []
        # Allow get_router() to contribute
        try:
            primary = self.get_router()
            routers.append(primary)
        except (ModuleNotFoundError, AttributeError):
            pass
        # Discover any APIRouter instances defined at module level
        try:
            from fastapi import APIRouter
        except ImportError:
            return routers
        for attr in dir(mod):
            val = getattr(mod, attr)
            if isinstance(val, APIRouter):
                routers.append(val)
        # Deduplicate
        unique: list[Any] = []
        for r in routers:
            if r not in unique:
                unique.append(r)
        return unique