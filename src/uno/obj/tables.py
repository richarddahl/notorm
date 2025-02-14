# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import textwrap

from typing import List

from sqlalchemy import UniqueConstraint, ForeignKey, func, Identity
from sqlalchemy.orm import Mapped, mapped_column, relationship

from uno.db.base import Base, str_26, str_255
from uno.sql_emitters import AlterGrantSQL

from uno.auth.rls_sql_emitters import SuperuserRLSSQL

from uno.obj.sql_emitters import InsertPermissionSQL, InsertObjectTypeRecordSQL
from uno.obj.graphs import (
    object_type_node,
    object_type_edges,
    db_object_node,
    db_object_edges,
    attachment_node,
    attachment_edges,
)


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
    display_name = "Table Type"
    display_name_plural = "Table Types"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertPermissionSQL,
        AlterGrantSQL,
    ]

    graph_node = object_type_node
    graph_edges = object_type_edges

    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the object_type.",
    )
    schema_name: Mapped[str_255] = mapped_column(doc="SchemaDef of the table")
    table_name: Mapped[str_255] = mapped_column(doc="Name of the table")

    # relationships
    db_objects: Mapped[List["DBObject"]] = relationship(back_populates="object_type")
    described_attribute_types: Mapped[List["AttributeType"]] = relationship(
        back_populates="describes"
    )
    value_type_attribute_types: Mapped[List["AttributeType"]] = relationship(
        back_populates="value_types"
    )

    def __str__(self) -> str:
        return f"{self.schema_name}.{self.table_name}"


class DBObject(Base):
    """DB Objects are used for the pk of many objects in the database,
    allowing for a single point of reference for attributes, queries, workflows, and reports
    """

    __tablename__ = "db_object"
    __table_args__ = {
        "schema": "uno",
        "comment": textwrap.dedent(
            """
            DB Objects are used for the pk of many objects in the database,
            allowing for a single point of reference for attributes, queries, workflows, and reports
            """
        ),
    }
    display_name = "DB Object"
    display_name_plural = "DB Objects"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        AlterGrantSQL,
    ]

    graph_node = db_object_node
    graph_edges = db_object_edges

    # Columns
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        doc="Primary Key",
        index=True,
    )
    object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "HAS_OBJECT_TYPE"},
    )

    # relationships
    object_type: Mapped[ObjectType] = relationship(back_populates="db_objects")
    attributes: Mapped[List["Attribute"]] = relationship(
        back_populates="db_object", secondary="uno.attribute__object_value"
    )
    attachments: Mapped[List["Attachment"]] = relationship(
        back_populates="db_objects", secondary="uno.attribute__object_value"
    )

    def __str__(self) -> str:
        return f"{self.object_type_id}"


class Attachment(Base):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Files attached to db objects",
    }
    display_name = "Attachment"
    display_name_plural = "Attachments"

    sql_emitters = [InsertObjectTypeRecordSQL]

    graph_node = attachment_node
    graph_edges = attachment_edges

    # Columns
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        doc="Primary Key",
        index=True,
        server_default=func.generate_ulid(),
    )
    name: Mapped[str_255] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str_255] = mapped_column(doc="Path to the file")

    # Relationships


class AttachmentDBObject(Base):
    __tablename__ = "attachment__db_object"
    __table_args__ = {
        "schema": "uno",
        "comment": "Attachments to DBObjects",
    }
    display_name = "Attachment DBObject"
    display_name_plural = "Attachment DBObjects"

    sql_emitters = []

    # Columns
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attachment.id", ondelete="CASCADE"),
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
