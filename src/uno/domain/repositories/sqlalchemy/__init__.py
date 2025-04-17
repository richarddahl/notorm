"""
SQLAlchemy repository implementations for the domain layer.

This package provides repository implementations that use SQLAlchemy as the ORM,
with full support for the specification pattern and async operations.
"""

from uno.domain.repositories.sqlalchemy.base import (
    SQLAlchemyRepository,
    SQLAlchemyUnitOfWork
)

# Import entity-specific repositories
from uno.domain.repositories.sqlalchemy.user import UserRepository
from uno.domain.repositories.sqlalchemy.product import ProductRepository
from uno.domain.repositories.sqlalchemy.order import OrderRepository