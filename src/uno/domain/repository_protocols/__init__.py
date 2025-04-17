"""
Domain repository protocols package.

This package contains protocol interfaces for repositories.
"""

from .repository_protocol import RepositoryProtocol, UnitOfWorkProtocol

__all__ = [
    "RepositoryProtocol",
    "UnitOfWorkProtocol",
]
