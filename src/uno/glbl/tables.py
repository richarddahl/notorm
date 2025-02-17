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

from uno.glbl.sql_emitters import InsertPermissionSQL, InsertObjectTypeRecordSQL
from uno.glbl.graphs import (
    object_type_edge_defs,
    related_object_edge_defs,
    attachment_edge_defs,
)
from uno.db.mixins import BaseFieldMixin, RelatedObjectPKMixin


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
        },
    )
    display_name = "Table Type"
    display_name_plural = "Table Types"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertPermissionSQL,
        AlterGrantSQL,
    ]

    graph_edge_defs = object_type_edge_defs

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
    related_objects: Mapped[List["RelatedObject"]] = relationship(
        back_populates="object_type"
    )
    described_attribute_types: Mapped[List["AttributeType"]] = relationship(
        back_populates="describes",
        secondary="uno.attribute_type__object_type",
        secondaryjoin="AttributeType.parent_id == ObjectType.id",
    )
    value_type_attribute_types: Mapped[List["AttributeType"]] = relationship(
        back_populates="value_types"
    )

    def __str__(self) -> str:
        return f"{self.schema_name}.{self.table_name}"


class Attachment(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Files attached to db objects",
    }
    display_name = "Attachment"
    display_name_plural = "Attachments"

    sql_emitters = [InsertObjectTypeRecordSQL]

    graph_edge_defs = attachment_edge_defs

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


class AttachmentRelatedObject(Base, RelatedObjectPKMixin):
    __tablename__ = "attachment__related_object"
    __table_args__ = {
        "schema": "uno",
        "comment": "Attachments to RelatedObjects",
    }
    display_name = "Attachment RelatedObject"
    display_name_plural = "Attachment RelatedObjects"

    sql_emitters = []
    include_in_graph = False

    # Columns
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attachment.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "WAS_ATTACHED_TO"},
    )
    related_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        nullable=False,
        info={"edge": "HAS_ATTACHMENT"},
    )
