# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
from typing import Optional

from sqlalchemy import ForeignKey, FetchedValue, text
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declared_attr,
    relationship,
)


from uno.db.base import str_26

from uno.config import settings


class GeneralBaseMixin:

    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to Meta Base",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates that the record is currently active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates that the record has been soft deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that created the record",
        info={
            "edge": "CREATED_BY",
            "reverse_node_label": "Meta",
            "reverse_edge": "OBJECTS_CREATED",
        },
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        nullable=False,
        server_default=FetchedValue(),
        doc="Timestamp when the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that last modified the record",
        info={
            "edge": "MODIFIED_BY",
            "reverse_node_label": "Meta",
            "reverse_edge": "OBJECTS_MODIFIED",
        },
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        nullable=True,
        server_default=FetchedValue(),
        doc="Timestamp when the record was soft deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="User that deleted the record",
        info={
            "edge": "DELETED_BY",
            "reverse_node_label": "Meta",
            "reverse_edge": "OBJECTS_DELETED",
        },
    )

    # Relationships
    @declared_attr
    def created_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.created_by_id],
            doc="User that created the record",
        )

    @declared_attr
    def modified_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.modified_by_id],
            doc="User that last modified the record",
        )

    @declared_attr
    def deleted_by(cls) -> Mapped["UserBase"]:
        return relationship(
            foreign_keys=[cls.deleted_by_id],
            doc="User that deleted the record",
        )


class BaseMixin(GeneralBaseMixin):
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Group to which the record belongs",
        info={
            "edge": "TENANT",
            "reverse_edge": "TENANTS",
        },
    )
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey("group.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Group to which the record belongs",
        info={
            "edge": "GROUP",
            "reverse_edge": "GROUPS",
        },
    )

    # Relationships
    @declared_attr
    def tenant(cls) -> Mapped["TenantBase"]:
        return relationship(
            foreign_keys=[cls.tenant_id],
            doc="Tenant to which the record belongs",
        )

    @declared_attr
    def group(cls) -> Mapped["GroupBase"]:
        return relationship(
            foreign_keys=[cls.group_id],
            doc="Group to which the record belongs",
        )
