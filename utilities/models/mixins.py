"""
Mixins for common ORM model behavior: audit timestamps and identifiers.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID


class IDMixin:
    """
    Adds a UUID primary key column named `id`.
    """
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)


class AuditMixin:
    """
    Adds `created_at` and `updated_at` timestamp columns.
    """
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )