# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import List

from sqlalchemy import UniqueConstraint, ForeignKey, func, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.base import Base, str_26, str_255
from uno.db.sql_emitters import AlterGrantSQL

from uno.auth.rls_sql_emitters import SuperuserRLSSQL

from uno.objs.sql_emitters import InsertPermissionSQL, InsertObjectTypeRecordSQL


class ObjectType(Base):
    """Table Types identify the tables in the database, similar to contenttypes in Django"""

    __tablename__ = "object_type"
    __table_args__ = (
        UniqueConstraint(
            "schema_name",
            "table_name",
            name="uq_objecttype_schema_table_name",
        ),
        {
            "schema": "uno",
            "comment": "Table Types identify the tables in the database, similar to contenttypes in Django",
            "info": {"rls_policy": "superuser"},
        },
    )
    verbose_name = "Table Type"
    verbose_name_plural = "Table Types"

    sql_emitters = [
        InsertPermissionSQL,
        AlterGrantSQL,
        # SuperuserRLSSQL,
    ]

    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        index=True,
        doc="Primary Key",
        server_default=func.generate_ulid(),
    )
    schema_name: Mapped[str_255] = mapped_column(doc="Schema of the table")
    table_name: Mapped[str_255] = mapped_column(doc="Name of the table")

    # relationships
    db_objects: Mapped[List["DBObject"]] = relationship(back_populates="object_type")

    def __str__(self) -> str:
        return f"{self.schema_name}.{self.table_name}"


class DBObject(Base):
    """Related Objects are used for the pk of many objects in the database,
    allowing for a single point of reference for attributes, queries, workflows, and reports
    """

    __tablename__ = "db_object"
    __table_args__ = {
        "schema": "uno",
        "comment": textwrap.dedent(
            """
            Related Objects are used for the pk of many objects in the database,
            allowing for a single point of reference for attributes, queries, workflows, and reports
            """
        ),
    }
    sql_emitters = [
        AlterGrantSQL,
    ]
    verbose_name = "Related Object"
    verbose_name_plural = "Related Objects"

    # Columns
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        doc="Primary Key",
        index=True,
    )
    object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "HAS_OBJECT_TYPE"},
    )

    # relationships
    object_type: Mapped[ObjectType] = relationship(back_populates="db_objects")

    def __str__(self) -> str:
        return f"{self.object_type_id}"


class Attachment(Base):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Files attached to db objects",
    }
    verbose_name = "Attachment"
    verbose_name_plural = "Attachments"

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the vertex.",
    )
    name: Mapped[str_255] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str_255] = mapped_column(doc="Path to the file")

    # Relationships


class MessageDBObject(Base):
    __tablename__ = "message__dbobject"
    __table_args__ = {
        "schema": "uno",
        "comment": "Attachments to DBObjects",
    }
    verbose_name = "Message DBObject"
    verbose_name_plural = "Message DBObjects"

    sql_emitters = []

    # Columns
    message_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.message.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_ATTACHED_TO"},
    )
    db_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.db_object.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "HAS_ATTACHMENT"},
    )
