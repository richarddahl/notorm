# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import BaseModel
from sqlalchemy import ForeignKey, FetchedValue
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
    declared_attr,
)
from sqlalchemy.sql import text

from uno.model import str_26
from uno.mixins import ObjectMixin, ModelMixin


class RecordAuditObjectMixin(BaseModel):
    created_by_id: Optional[str] = None
    created_by: Optional["User"] = None
    modified_by_id: Optional[str] = None
    modified_by: Optional["User"] = None
    deleted_by_id: Optional[str] = None
    deleted_by: Optional["User"] = None


class RecordAuditModelMixin:

    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that created the record",
        info={
            "edge": "CREATED_BY",
            "reverse_node_label": "MetaRecord",
            "reverse_edge": "CREATED_OBJECTS",
        },
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey("user.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
        server_default=FetchedValue(),
        doc="User that last modified the record",
        info={
            "edge": "MODIFIED_BY",
            "reverse_node_label": "MetaRecord",
            "reverse_edge": "MODIFIED_OBJECTS",
        },
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("user.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="User that deleted the record",
        info={
            "edge": "DELETED_BY",
            "reverse_node_label": "MetaRecord",
            "reverse_edge": "DELETED_OBJECTS",
        },
    )

    # Relationships
    @declared_attr
    def created_by(cls) -> Mapped["UserModel"]:
        return relationship(
            foreign_keys=[cls.created_by_id],
            doc="User that created the record",
        )

    @declared_attr
    def modified_by(cls) -> Mapped["UserModel"]:
        return relationship(
            foreign_keys=[cls.modified_by_id],
            doc="User that last modified the record",
        )

    @declared_attr
    def deleted_by(cls) -> Mapped["UserModel"]:
        return relationship(
            foreign_keys=[cls.deleted_by_id],
            doc="User that deleted the record",
        )


class GroupObjectMixin(BaseModel):
    group_id: str
    group: Optional["Group"] = None


class GroupModelMixin:
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey("group.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Group to which the record belongs",
        info={
            "edge": "GROUP",
            "reverse_edge": "GROUP_OBJECTS",
        },
    )

    # Relationships
    @declared_attr
    def group(cls) -> Mapped["GroupModel"]:
        return relationship(
            foreign_keys=[cls.group_id],
            doc="Group to which the record belongs",
        )


class TenantObjectMixin(BaseModel):
    tenant_id: str
    tenant: Optional["Tenant"] = None


class TenantModelMixin:
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey("tenant.id", ondelete="RESTRICT"),
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Tenant to which the record belongs",
        info={
            "edge": "TENANT",
            "reverse_edge": "TENANT_OBJECTS",
        },
    )

    # Relationships
    @declared_attr
    def tenant(cls) -> Mapped["TenantModel"]:
        return relationship(
            foreign_keys=[cls.tenant_id],
            doc="Tenant to which the record belongs",
        )


class DefaultModelMixin(
    RecordAuditModelMixin, TenantModelMixin, GroupModelMixin, ModelMixin
):
    pass


class DefaultObjectMixin(
    RecordAuditObjectMixin, TenantObjectMixin, GroupObjectMixin, ObjectMixin
):
    pass
