"""
Unit of Work pattern for the UNO framework.

This module provides a unified implementation of the Unit of Work pattern,
which manages transaction boundaries and ensures consistent changes across
multiple repositories. It includes support for distributed transactions
using a two-phase commit protocol.
"""

from uno.core.uow.base import AbstractUnitOfWork
from uno.core.uow.providers import (
    DatabaseUnitOfWork,
    InMemoryUnitOfWork,
    UnitOfWorkFactory,
)
from uno.core.uow.context import transaction, unit_of_work
from uno.core.uow.distributed import (
    DistributedUnitOfWork,
    TransactionParticipant,
    UnitOfWorkParticipant,
    EventStoreParticipant,
    TwoPhaseStatus,
)

__all__ = [
    'AbstractUnitOfWork',
    'DatabaseUnitOfWork',
    'InMemoryUnitOfWork',
    'UnitOfWorkFactory',
    'transaction',
    'unit_of_work',
    'DistributedUnitOfWork',
    'TransactionParticipant',
    'UnitOfWorkParticipant',
    'EventStoreParticipant',
    'TwoPhaseStatus',
]