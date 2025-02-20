# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.base import Base, str_26, str_255

from uno.db.tables import (
    Meta,
    MetaType,
)
from uno.db.sql_emitters import SQLEmitter
from uno.auth.rls_sql_emitters import RLSSQL
from uno.fltr.tables import Query

from uno.config import settings


class AttributeObjectValue(Base):
    __tablename__ = "attribute_objectvalue"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Association table between Attribute and RelatedObjects used as values",
        },
    )

    display_name: ClassVar[str] = "Attribute Object Value"
    display_name_plural: ClassVar[str] = "Attribute Object Values"
    include_in_graph = False

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    attribute_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attribute.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id", ondelete="CASCADE"),
        primary_key=True,
    )


class AttributeTypeMetaType(Base):
    __tablename__ = "attributetype_metatype"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Association table between AttributeType and MetaType",
        },
    )

    display_name: ClassVar[str] = "Attribute Type Applicability"
    display_name_plural: ClassVar[str] = "Attribute Type Applicabilities"
    include_in_graph = False

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
    )
    metatype_name: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        primary_key=True,
    )


class AttributeValue(Meta):
    __tablename__ = "attribute_value"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Defines values available for attributes, if not using an existing object types",
        },
    )

    display_name: ClassVar[str] = "Attribute Value"
    display_name_plural: ClassVar[str] = "Attribute Values"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(doc="The value of the attribute")

    __mapper_args__ = {
        "polymorphic_identity": "attribute_value",
        "inherit_condition": id == Meta.id,
    }


class Attribute(Meta):
    __tablename__ = "attribute"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Attributes define characteristics of objects",
        },
    )
    display_name: ClassVar[str] = "Attribute"
    display_name_plural: ClassVar[str] = "Attributes"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"),
        primary_key=True,
        doc="The unique identifier for the attribute",
    )
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attribute_type.id", ondelete="CASCADE"),
        index=True,
        doc="The type of attribute",
    )
    comment: Mapped[Optional[str]] = mapped_column(doc="A comment about the attribute")
    follow_up_required: Mapped[bool] = mapped_column(doc="Is follow up required?")

    # Relationships
    attribute_type: Mapped["AttributeType"] = relationship(
        foreign_keys=[attribute_type_id],
        back_populates="attributes",
        doc="The type of attribute",
        info={"edge": "HAS_ATTRIBUTE_TYPE"},
    )
    object_values: Mapped[Optional[list["Attribute"]]] = relationship(
        "Attribute",
        back_populates="attribute_values",
        secondary=AttributeObjectValue.__table__,
        primaryjoin="Attribute.id == AttributeObjectValue.attribute_id",
        secondaryjoin="Meta.id == AttributeObjectValue.meta_id",
        doc="The objects with this attribute",
        info={"edge": "HAS_ATTRIBUTE_VALUE"},
    )
    Meta.attribute_values = relationship(
        "Attribute",
        back_populates="object_values",
        secondary=AttributeObjectValue.__table__,
        primaryjoin="Meta.id == AttributeObjectValue.meta_id",
        secondaryjoin="Attribute.id == AttributeObjectValue.attribute_id",
        doc="The attributes for the object",
        info={"edge": "HAS_ATTRIBUTE_VALUE"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "attribute",
        "inherit_condition": id == Meta.id,
    }


class AttributeType(Meta):
    __tablename__ = "attribute_type"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Defines the type of attribute that can be associated with an object",
        },
    )
    display_name: ClassVar[str] = "Attribute Type"
    display_name_plural: ClassVar[str] = "Attribute Types"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(unique=True)
    text: Mapped[str] = mapped_column()
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attribute_type.id", ondelete="SET NULL"),
        index=True,
        doc="The parent attribute type",
    )
    describes_id: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
        doc="The object types that the attribute type describes.",
    )
    description_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        index=True,
        doc="The query that determines which object types are applicable to this attribute type.",
    )
    value_type_name: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        doc="The object types that are values for the attribute type",
    )
    value_type_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        doc="The query that determines which object types are used as values for the attribute type.",
    )
    required: Mapped[bool] = mapped_column(
        default=False, doc="Is the attribute required?"
    )
    multiple_allowed: Mapped[bool] = mapped_column(
        default=False, doc="Can the attribute have multiple values?"
    )
    comment_required: Mapped[bool] = mapped_column(
        default=False, doc="Is a comment required?"
    )
    initial_comment: Mapped[Optional[str]] = mapped_column(
        doc="The initial comment for attributes of this type"
    )

    # Relationships
    parent: Mapped["AttributeType"] = relationship(
        foreign_keys=[parent_id],
        remote_side=[id],
        back_populates="children",
        doc="The parent attribute type",
        info={"edge": "IS_PARENT_OF"},
    )
    children: Mapped[list["AttributeType"]] = relationship(
        foreign_keys=[id],
        back_populates="parent",
        doc="The child attribute types",
        info={"edge": "IS_CHILD_OF"},
    )
    describes: Mapped[list[MetaType]] = relationship(
        back_populates="described_by",
        primaryjoin=describes_id == MetaType.name,
        secondary=AttributeTypeMetaType.__table__,
        secondaryjoin=AttributeTypeMetaType.attribute_type_id == id,
        doc="The object types that the attribute type describes.",
        info={"edge": "DESCRIBES"},
    )
    metatype_query: Mapped[Optional[Query]] = relationship(
        Query,
        back_populates="attribute_type_applicability",
        primaryjoin=description_query_id == Query.id,
        doc="The query that determines which object types are applicable to this attribute type.",
        info={"edge": "DETERMINES_APPLICABILITY"},
    )
    value_types: Mapped[list[MetaType]] = relationship(
        back_populates="attribute_values",
        primaryjoin=value_type_name == MetaType.name,
        doc="The object types that are values for the attribute type",
        info={"edge": "IS_VALUE_TYPE_FOR"},
    )
    value_type_query: Mapped[Optional[Query]] = relationship(
        Query,
        back_populates="attribute_value_applicability",
        primaryjoin=value_type_query_id == Query.id,
        doc="The query that determines which object types are used as values for the attribute type.",
        info={"edge": "DETERMINES_VALUE_TYPE"},
    )
    attributes: Mapped[list[Attribute]] = relationship(
        back_populates="attribute_type",
        foreign_keys=[Attribute.attribute_type_id],
        remote_side=Attribute.attribute_type_id,
        doc="The attributes with this attribute type",
        info={"edge": "HAS_ATTRIBUTE"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "attribute_type",
        "inherit_condition": id == Meta.id,
    }


class AttachmentRelatedObject(Base):
    __tablename__ = "attachment_relatedobject"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Attachments to RelatedObjects",
    }
    display_name: ClassVar[str] = "Attachment Meta"
    display_name_plural: ClassVar[str] = "Attachment RelatedObjects"

    sql_emitters: ClassVar[list[SQLEmitter]] = []
    include_in_graph = False

    # Columns
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.attachment.id", ondelete="CASCADE"),
        primary_key=True,
    )
    meta_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Attachment(Meta):
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": settings.DB_SCHEMA,
        "comment": "Files attached to db objects",
    }

    display_name: ClassVar[str] = "Attachment"
    display_name_plural: ClassVar[str] = "Attachments"

    sql_emitters: ClassVar[list[SQLEmitter]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta.id"),
        primary_key=True,
    )
    name: Mapped[str_255] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str_255] = mapped_column(doc="Path to the file")

    # Relationships

    __mapper_args__ = {
        "polymorphic_identity": "attachment",
        "inherit_condition": id == Meta.id,
    }
