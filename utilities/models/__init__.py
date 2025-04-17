"""Generic ORM abstractions and mixins for client domain models."""
from .base import Base
from .mixins import IDMixin, AuditMixin

__all__ = ["Base", "IDMixin", "AuditMixin"]