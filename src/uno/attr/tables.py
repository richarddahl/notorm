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

from uno.db.base import Base, RelatedObject, BaseFieldMixin, str_26, str_255
from uno.db.sql_emitters import RecordVersionAuditSQL

from uno.glbl.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)

from uno.auth.rls_sql_emitters import RLSSQL
from uno.fltr.tables import Query
from uno.glbl.tables import ObjectType

from uno.attr.graphs import attribute_type_edge_defs


class AttributeObjectValue(Base, BaseFieldMixin):
    __tablename__ = "attribute__object_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between Attribute and Object Value (Meta)",
        },
    )

    display_name = "Attribute Object Value"
    display_name_plural = "Attribute Object Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    attribute_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    related_object_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class AttributeTypeAppliesTo(Base, BaseFieldMixin):
    __tablename__ = "attribute_type__applies_to"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects to which an attribute is applied",
        },
    )

    display_name = "Attribute Type Applies To"
    display_name_plural = "Attribute Type Applies To"

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(Identity(), primary_key=True)
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    applicable_object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    determining_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
    )
    required: Mapped[bool] = mapped_column()

    # Relationships
    determining_query: Mapped[Optional[Query]] = relationship(
        Query,
        back_populates="attribute_type_applicability",
    )


class AttributeTypeAttributeValue(Base, BaseFieldMixin):
    __tablename__ = "attribute_type__attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between AttributeType and AttributeValue",
        },
    )

    display_name = "Attribute Type Attribute Value"
    display_name_plural = "Attribute Type Attribute Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    attribute_value_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_value.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )


class AttributeTypeValueType(Base, BaseFieldMixin):
    __tablename__ = "attribute_type__value_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects that provide the values for an attribute",
        },
    )

    display_name = "Attribute Type Value Type"
    display_name_plural = "Attribute Type Value Types"

    include_in_graph = False

    sql_emitters = []

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    value_object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    determining_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        info={"edge": "DETERMINES_VALUE_TYPE"},
    )

    determining_query: Mapped[Query] = relationship(
        "Query",
        back_populates="attribute_type__value_type",
    )

    # Relationships
    determining_query: Mapped[Optional[Query]] = relationship(
        Query,
        back_populates="attribute_value_applicability",
    )


class AttributeAttributeValue(Base, BaseFieldMixin):
    __tablename__ = "attribute__attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between Attribute and AttributeValue",
        },
    )

    display_name = "Attribute Attribute Value"
    display_name_plural = "Attribute Attribute Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    attribute_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"start_node": True},
    )
    attribute_value_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_value.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"end_node": True},
    )


class AttributeType(RelatedObject):
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

    display_name = "Attribute Type"
    display_name_plural = "Attribute Types"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    graph_edge_defs = attribute_type_edge_defs

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
        info={
            "edge": {"name": "IS_CHILD_OF", "accessor": "parent"},
        },
    )
    multiple_allowed: Mapped[bool] = mapped_column()
    comment_required: Mapped[bool] = mapped_column()
    initial_comment: Mapped[str] = mapped_column()

    # Relationships
    parent: Mapped["AttributeType"] = relationship(
        foreign_keys=[parent_id], remote_side=[id], back_populates="children"
    )
    children: Mapped[list["AttributeType"]] = relationship(
        foreign_keys=[id], back_populates="parent"
    )
    describes: Mapped[list["ObjectType"]] = relationship(
        back_populates="described_attribute_types",
        secondary=AttributeTypeAppliesTo.__table__,
        secondaryjoin="AttributeType.id == AttributeTypeAppliesTo.attribute_type_id",
        info={"edge": "DESCRIBES"},
    )
    ObjectType.described_attribute_types = relationship(
        "AttributeType",
        back_populates="describes",
        secondary=AttributeTypeAppliesTo.__table__,
        secondaryjoin="ObjectType.id == AttributeTypeAppliesTo.applicable_object_type_id",
    )
    value_types: Mapped[list["AttributeValue"]] = relationship(
        back_populates="attribute_types",
        secondary=AttributeTypeAttributeValue.__table__,
    )
    attributes: Mapped[list["Attribute"]] = relationship(
        back_populates="attribute_type"
    )


class Attribute(Base):
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

    display_name = "Attribute"
    display_name_plural = "Attributes"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "IS_OF_TYPE"},
    )
    comment: Mapped[Optional[str]] = mapped_column()
    follow_up_required: Mapped[bool] = mapped_column()

    # Relationships
    attribute_type: Mapped[AttributeType] = relationship(
        back_populates="attributes",
        foreign_keys=[attribute_type_id],
    )
    attribute_values: Mapped[Optional[list["AttributeValue"]]] = relationship(
        back_populates="attributes"
    )
    object_values: Mapped[Optional[list["RelatedObject"]]] = relationship(
        "RelatedObject",
        back_populates="attribute_values",
        secondary=AttributeObjectValue.__table__,
        primaryjoin="Attribute.id == AttributeObjectValue.attribute_id",
        secondaryjoin="RelatedObject.id == AttributeObjectValue.related_object_id",
    )
    RelatedObject.attribute_values = relationship(
        "Attribute",
        back_populates="object_values",
        secondary=AttributeObjectValue.__table__,
        primaryjoin="RelatedObject.id == AttributeObjectValue.related_object_id",
        secondaryjoin="Attribute.id == AttributeObjectValue.attribute_id",
    )


class AttributeValue(RelatedObject):
    __tablename__ = "attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the values available for attribute",
        },
    )
    __mapper_args__ = {
        "polymorphic_identity": "attribute_value",
        "inherit_condition": id == RelatedObject.id,
    }

    display_name = "Attribute Value"
    display_name_plural = "Attribute Values"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
    text: Mapped[str] = mapped_column()

    # Relationships
    attribute_types: Mapped[list[AttributeType]] = relationship(
        back_populates="value_types",
        secondary=AttributeTypeAttributeValue.__table__,
        primaryjoin="AttributeValue.id == AttributeTypeAttributeValue.attribute_value_id",
        secondaryjoin="AttributeType.id == AttributeTypeAttributeValue.attribute_type_id",
    )
    attributes: Mapped[list[Attribute]] = relationship(
        back_populates="attribute_values"
    )
