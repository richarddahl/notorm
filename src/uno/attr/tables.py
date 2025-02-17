# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.base import Base, RelatedObjectBase, str_26, str_255
from uno.db.mixins import BaseFieldMixin
from uno.db.sql_emitters import RecordVersionAuditSQL

from uno.glbl.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)

from uno.auth.rls_sql_emitters import RLSSQL
from uno.fltr.tables import Query

from uno.attr.graphs import attribute_type_edge_defs


class AttributeType(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "attribute_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of attribute that can be associated with an object",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute_type"}

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
    )
    multiple_allowed: Mapped[bool] = mapped_column()
    comment_required: Mapped[bool] = mapped_column()
    initial_comment: Mapped[str] = mapped_column()

    # Relationships
    parent: Mapped["AttributeType"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["AttributeType"]] = relationship(back_populates="parent")
    describes: Mapped[list["AttributeTypeAppliesTo"]] = relationship(
        back_populates="attribute_type"
    )
    value_types: Mapped[list["AttributeTypeValueType"]] = relationship(
        back_populates="attribute_type"
    )


class AttributeTypeAppliesTo(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "attribute_type__applies_to"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects to which an attribute is applied",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute_type__applies_to"}

    display_name = "Attribute Type Applies To"
    display_name_plural = "Attribute Type Applies To"

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
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
        "Query",
        back_populates="attribute_type__applies_to",
    )


class AttributeTypeValueType(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "attribute_type__value_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects that provide the values for an attribute",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute_type__value_type"}

    display_name = "Attribute Type Value Type"
    display_name_plural = "Attribute Type Value Types"

    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id"), primary_key=True
    )
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

    # Relationships
    determining_query: Mapped[Query] = relationship(
        "Query",
        back_populates="attribute_type__value_type",
    )


class Attribute(Base):
    __tablename__ = "attribute"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Attributes define characteristics of objects",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute"}

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
    attribute_type: Mapped[AttributeType] = relationship(back_populates="attributes")
    attribute_values: Mapped[Optional[list["AttributeValue"]]] = relationship(
        back_populates="attributes"
    )
    object_values: Mapped[Optional[list["RelatedObject"]]] = relationship(
        back_populates="attributes"
    )


class AttributeValue(RelatedObjectBase, BaseFieldMixin):
    __tablename__ = "attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the values available for attribute",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute_value"}

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
    attributes: Mapped[list[Attribute]] = relationship(
        back_populates="attribute_values"
    )


class AttributeAttributeValue(Base, BaseFieldMixin):
    __tablename__ = "attribute__attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between Attribute and AttributeValue",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute__attribute_value"}

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

    # Relationships
    # attribute: Mapped[Attribute] = relationship(
    #    back_populates="attribute_attribute_values",
    # )
    # attribute_value: Mapped[AttributeValue] = relationship(
    #    back_populates="attribute_attribute_values",
    # )


class AttributeObjectValue(Base, BaseFieldMixin):
    __tablename__ = "attribute__object_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Association table between Attribute and Object Value (Meta)",
        },
    )
    __mapper_args__ = {"polymorphic_identity": "attribute__object_value"}

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
        primary_key=True,
        index=True,
        info={"start_node": True},
    )
    # object_value_id: Mapped[str_26] = mapped_column(
    #    ForeignKey("uno.related_object.id", ondelete="CASCADE"),
    #    primary_key=True,
    #    index=True,
    #    info={"end_node": True},
    # )

    # Relationships
    # attribute: Mapped[Attribute] = relationship(
    #    back_populates="attribute_object_values",
    # )
    # object_value: Mapped[RelatedObject] = relationship(
    #    back_populates="attribute_object_values",
    # )
