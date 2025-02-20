# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime

from typing import Optional, ClassVar

from sqlalchemy import ForeignKey, text, func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    declared_attr,
    relationship,
)

from uno.db.base import Base, str_26, str_63, str_255
from uno.db.sql_emitters import (
    SQLEmitter,
    InsertPermissionSQL,
    InsertMetaObjectTriggerSQL,
    RecordVersionAuditSQL,
    CreateHistoryTableSQL,
    InsertHistoryTableRecordSQL,
)
from uno.config import settings


class RecordVersionAuditMixin:
    """Mixin for recording version history of a record"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [RecordVersionAuditSQL]


class HistoryTableAuditMixin:
    """Mixin for recording history of a table"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        CreateHistoryTableSQL,
        InsertHistoryTableRecordSQL,
    ]


class RecordUserAuditMixin:
    sql_emitters: ClassVar[list[SQLEmitter]] = []


class MetaObjectMixin:
    """Mixin for Meta Objects"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        InsertMetaObjectTriggerSQL,
    ]


class MetaType(Base):
    """Meta Types identify polymorphic types in the database for sublcasses of Meta"""

    __tablename__ = "meta_type"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Meta Types identify polymorphic types in the database for sublcasses of Meta",
        },
    )

    display_name: ClassVar[str] = "Table Type"
    display_name_plural: ClassVar[str] = "Table Types"

    sql_emitters: ClassVar[list[SQLEmitter]] = [InsertPermissionSQL]

    name: Mapped[str_63] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="Name of the table",
    )

    # Relationships
    described_by: Mapped[list["AttributeType"]] = relationship(
        back_populates="describes",
        primaryjoin="AttributeType.metatype_name== MetaType.name",
        doc="The attribute types that describe the object type",
        info={"edge": "IS_DESCRIBED_BY"},
    )
    attribute_values: Mapped[list["AttributeType"]] = relationship(
        back_populates="value_types",
        primaryjoin="AttributeType.value_type_name == MetaType.name",
        doc="The attribute types that are values for the object type",
        info={"edge": "HAS_VALUE_TYPE"},
    )
    permissions: Mapped[list["Permission"]] = relationship(
        back_populates="meta_type",
        doc="The permissions for the object type",
        info={"edge": "HAS_PERMISSION"},
    )

    def __str__(self) -> str:
        return self.name


class Meta(Base):
    """
    Base class for objects that are generically related to other objects.

    Meta Objects are used for the pk of many objects in the database,
    allowing for a single point of reference for attributes, queries, workflows, and reports
    """

    __tablename__ = "meta"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": """
            Meta Objects are polymorphic objects that are used for the pk of many objects in the database,
            allowing for a single point of reference for attributes, queries, workflows, and reports
            """,
    }
    display_name: ClassVar[str] = "Meta Object"
    display_name_plural: ClassVar[str] = "Meta Objects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    # Columns
    id: Mapped[str_26] = mapped_column(primary_key=True)
    metatype_name: Mapped[str_63] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
        doc="The metatype_name of the related object",
    )
    is_active: Mapped[bool] = mapped_column(
        server_default=text("true"),
        doc="Indicates if the record is active",
    )
    is_deleted: Mapped[bool] = mapped_column(
        server_default=text("false"),
        doc="Indicates if the record has been deleted",
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was created",
    )
    created_by_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
    )
    modified_by_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )

    # Relationships
    @declared_attr
    def created_by(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=[cls.created_by_id],
            doc="The user that owns the related object",
            info={"edge": "WAS_CREATED_BY"},
        )

    @declared_attr
    def modified_by(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=[cls.modified_by_id],
            doc="The user that last modified the related object",
            info={"edge": "WAS_MODIFIED_BY"},
        )

    @declared_attr
    def deleted_by(cls) -> Mapped["User"]:
        return relationship(
            "User",
            foreign_keys=[cls.deleted_by_id],
            doc="The user that deleted the related object",
            info={"edge": "WAS_DELETED_BY"},
        )

    __mapper_args__ = {
        "polymorphic_identity": "meta",
        "polymorphic_on": "metatype_name",
    }

    def __str__(self) -> str:
        return f"{self.metatype_name}"
