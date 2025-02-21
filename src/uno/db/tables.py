# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from __future__ import annotations

import datetime

from typing import Optional, ClassVar

from sqlalchemy import ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column, declared_attr

from uno.db.base import Base, str_26, str_63, str_255
from uno.db.sql.sql_emitter import SQLEmitter
from uno.db.sql.table_sql_emitters import (
    InsertPermission,
    InsertMetaTypeRecord,
    InsertMetaRecordTrigger,
    RecordVersionAudit,
    CreateHistoryTable,
    InsertHistoryTableRecord,
    RecordAuditFunction,
)
from uno.config import settings


class RecordVersionAuditMixin:
    """Mixin for recording version history of a record"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [RecordVersionAudit]


class HistoryTableAuditMixin:
    """Mixin for recording history of a table"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        CreateHistoryTable,
        InsertHistoryTableRecord,
    ]


class RecordAuditMixin:
    """Mixin for auditing actions on records

    Documents both the timestamps of when and user ids  of who created,
    modified, and deleted a record

    """

    sql_emitters: ClassVar[list[SQLEmitter]] = [RecordAuditFunction]

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

    @declared_attr
    def created_by_id(cls) -> Mapped[str_26]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )

    modified_at: Mapped[datetime.datetime] = mapped_column(
        doc="Time the record was last modified",
    )

    @declared_attr
    def modified_by_id(cls) -> Mapped[str_26]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )

    deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(
        doc="Time the record was deleted",
    )

    @declared_attr
    def deleted_by_id(cls) -> Mapped[Optional[str_26]]:
        return mapped_column(
            ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
            index=True,
        )


class MetaObjectMixin:
    """Mixin for MetaRecord Objects"""

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        InsertMetaRecordTrigger,
    ]


class MetaType(Base):
    """MetaRecord Types identify polymorphic types in the database for sublcasses of MetaRecord"""

    __tablename__ = "meta_type"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "MetaRecord Types identify polymorphic types in the database for sublcasses of MetaRecord",
    }

    display_name: ClassVar[str] = "Meta Type"
    display_name_plural: ClassVar[str] = "Meta Types"

    sql_emitters: ClassVar[list[SQLEmitter]] = [
        InsertMetaTypeRecord,
        InsertPermission,
    ]

    name: Mapped[str_63] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="Name of the table",
    )

    def __str__(self) -> str:
        return self.name


class MetaRecord(Base):
    """
    Base class for objects that are generically related to other objects.

    MetaRecord Objects are used for the pk of many objects in the database,
    allowing for a single point of reference for attributes, queries, workflows, and reports
    """

    __tablename__ = "meta"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": """
            MetaRecord Objects are polymorphic objects that are used for the pk of many objects in the database,
            allowing for a single point of reference for attributes, queries, workflows, and reports
            """,
    }
    display_name: ClassVar[str] = "Meta Record"
    display_name_plural: ClassVar[str] = "Meta Records"

    sql_emitters: ClassVar[list[SQLEmitter]] = [InsertMetaTypeRecord]

    # Columns

    id: Mapped[str_26] = mapped_column(primary_key=True)
    meta_type_name: Mapped[str_63] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
        doc="The meta_type_name of the related object",
    )

    __mapper_args__ = {
        "polymorphic_identity": "meta",
        "polymorphic_on": "meta_type_name",
    }

    def __str__(self) -> str:
        return f"{self.meta_type_name}"
