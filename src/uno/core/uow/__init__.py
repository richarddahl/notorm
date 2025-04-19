"""
Unit of Work pattern for the UNO framework.

This module provides a unified implementation of the Unit of Work pattern,
which manages transaction boundaries and ensures consistent changes across
multiple repositories.
"""

from uno.core.uow.base import AbstractUnitOfWork
from uno.core.uow.providers import (
    DatabaseUnitOfWork,
    InMemoryUnitOfWork,
    UnitOfWorkFactory,
)
from uno.core.uow.context import transaction, unit_of_work

__all__ = [
    'AbstractUnitOfWork',
    'DatabaseUnitOfWork',
    'InMemoryUnitOfWork',
    'UnitOfWorkFactory',
    'transaction',
    'unit_of_work',
]