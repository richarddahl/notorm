# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Identity
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.tables import (
    Base,
    RelatedObject,
    ObjectType,
    BaseTable,
    str_26,
    str_255,
)
from uno.db.sql_emitters import (
    RecordVersionAuditSQL,
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)
from uno.auth.rls_sql_emitters import RLSSQL
from uno.fltr.tables import Query
# from uno.attr.graphs import attribute_type_edge_defs


class AttributeObjectValue(RelatedObject):
    display_name = "Attribute Object Value"
    display_name_plural = "Attribute Object Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    attribute_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute.id", ondelete="CASCADE"),
        index=True,
    )
    related_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
    )

    __tablename__ = "attribute__object_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between Attribute and RelatedObjects used as values",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute_object_value",
        "inherit_condition": id == RelatedObject.id,
    }


class AttributeTypeApplicability(RelatedObject):
    display_name = "Attribute Type Applicability"
    display_name_plural = "Attribute Type Applicabilities"
    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        index=True,
    )
    applicable_object_type_name: Mapped[str_255] = mapped_column(
        ForeignKey("uno.object_type.name", ondelete="CASCADE"),
        index=True,
    )

    __tablename__ = "attribute_type_applicability"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between AttributeType and ObjectType",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute_type_applicability",
        "inherit_condition": id == RelatedObject.id,
    }


class AttributeValue(RelatedObject):
    display_name = "Attribute Value"
    display_name_plural = "Attribute Values"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(doc="The value of the attribute")

    __tablename__ = "attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines values available for attributes, if not using an existing object types",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute_value",
        "inherit_condition": id == RelatedObject.id,
    }


class Attribute(RelatedObject):
    display_name = "Attribute"
    display_name_plural = "Attributes"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"),
        primary_key=True,
        doc="The unique identifier for the attribute",
    )
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
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
        secondaryjoin="RelatedObject.id == AttributeObjectValue.related_object_id",
        doc="The objects with this attribute",
        info={"edge": "HAS_ATTRIBUTE_VALUE"},
    )
    RelatedObject.attribute_values = relationship(
        "Attribute",
        back_populates="object_values",
        secondary=AttributeObjectValue.__table__,
        primaryjoin="RelatedObject.id == AttributeObjectValue.related_object_id",
        secondaryjoin="Attribute.id == AttributeObjectValue.attribute_id",
        doc="The attributes for the object",
        info={"edge": "HAS_ATTRIBUTE_VALUE"},
    )

    __tablename__ = "attribute"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Attributes define characteristics of objects",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute",
        "inherit_condition": id == RelatedObject.id,
    }


class AttributeType(RelatedObject):
    display_name = "Attribute Type"
    display_name_plural = "Attribute Types"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(unique=True)
    text: Mapped[str] = mapped_column()
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="SET NULL"),
        index=True,
        doc="The parent attribute type",
    )
    describes_id: Mapped[str_255] = mapped_column(
        ForeignKey("uno.object_type.name", ondelete="CASCADE"),
        index=True,
        doc="The object types that the attribute type describes.",
    )
    description_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        index=True,
        doc="The query that determines which object types are applicable to this attribute type.",
    )
    value_type_name: Mapped[str_255] = mapped_column(
        ForeignKey("uno.object_type.name", ondelete="CASCADE"),
        doc="The object types that are values for the attribute type",
    )
    value_type_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
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
        info={"edge": "HAS_CHILD"},
    )
    describes: Mapped[list[ObjectType]] = relationship(
        back_populates="described_by",
        primaryjoin=describes_id == ObjectType.name,
        secondary=AttributeTypeApplicability.__table__,
        secondaryjoin=AttributeTypeApplicability.attribute_type_id == id,
        doc="The object types that the attribute type describes.",
        info={"edge": "DESCRIBES"},
    )
    object_type_query: Mapped[Optional[Query]] = relationship(
        "Query",
        back_populates="attribute_type_applicability",
        primaryjoin=description_query_id == Query.id,
        doc="The query that determines which object types are applicable to this attribute type.",
        info={"edge": "DETERMINES_APPLICABILITY"},
    )
    value_types: Mapped[list[ObjectType]] = relationship(
        back_populates="attribute_values",
        primaryjoin=value_type_name == ObjectType.name,
        doc="The object types that are values for the attribute type",
        info={"edge": "IS_VALUE_TYPE_FOR"},
    )
    value_type_query: Mapped[Optional[Query]] = relationship(
        "Query",
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

    __tablename__ = "attribute_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of attribute that can be associated with an object",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute_type",
        "inherit_condition": id == RelatedObject.id,
    }


class AttachmentRelatedObject(RelatedObject):
    display_name = "Attachment RelatedObject"
    display_name_plural = "Attachment RelatedObjects"

    sql_emitters = []
    include_in_graph = False

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    attachment_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attachment.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    related_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    __tablename__ = "attachment__related_object"
    __table_args__ = {
        "schema": "uno",
        "comment": "Attachments to RelatedObjects",
    }
    __mapper_args__ = {
        "polymorphic_identity": "attachment__related_object",
        "inherit_condition": id == RelatedObject.id,
    }


class Attachment(RelatedObject):
    display_name = "Attachment"
    display_name_plural = "Attachments"

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"),
        primary_key=True,
    )
    name: Mapped[str_255] = mapped_column(unique=True, doc="Name of the file")
    file: Mapped[str_255] = mapped_column(doc="Path to the file")

    # Relationships
    __tablename__ = "attachment"
    __table_args__ = {
        "schema": "uno",
        "comment": "Files attached to db objects",
    }
    __mapper_args__ = {
        "polymorphic_identity": "attachment",
        "inherit_condition": id == RelatedObject.id,
    }
