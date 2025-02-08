# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Column,
    Table,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import VARCHAR

from uno.db.base import Base, str_26, str_255
from uno.db.mixins import BaseFieldMixin, RelatedObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL
from uno.objs.tables import ObjectType, DBObject
from uno.objs.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)
from uno.auth.rls_sql_emitters import RLSSQL
from uno.fltrs.tables import Query

from uno.attrs.enums import AttributePurpose, AttributeDataType


class AttributeType(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "attribute_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of attribute that can be associated with an object",
        },
    )
    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    name: Mapped[str_255] = mapped_column(unique=True)
    text: Mapped[str] = mapped_column()
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="SET NULL"),
        info={"edge": "IS_CHILD_OF"},
    )
    multiple_allowed: Mapped[bool] = mapped_column()
    comment_required: Mapped[bool] = mapped_column()
    initial_comment: Mapped[str] = mapped_column()

    # Relationships
    obj: Mapped[DBObject] = relationship(back_populates="attribute_types")
    parent: Mapped["AttributeType"] = relationship(
        remote_side=[id], back_populates="children"
    )
    children: Mapped[list["AttributeType"]] = relationship(
        "AttributeType", back_populates="parent"
    )
    applies_to: Mapped[list["AttributeTypeAppliesTo"]] = relationship(
        "AttributeTypeAppliesTo", back_populates="attribute_type"
    )
    value_type: Mapped[list["AttributeTypeValueType"]] = relationship(
        "AttributeTypeValueType", back_populates="attribute_type"
    )


class AttributeTypeAppliesTo(Base, BaseFieldMixin):
    __tablename__ = "attribute_type__applies_to"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects to which an attribute is applied",
        },
    )

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "APPLIES_TO"},
    )
    applicable_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "IS_DESCRIBED_BY"},
    )
    determining_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        info={"edge": "DETERMINES_APPLICABILITY"},
    )
    required: Mapped[bool] = mapped_column()

    # Relationships
    determining_query: Mapped[Optional[Query]] = relationship(
        "Query",
        back_populates="attribute_type__applies_to",
    )


class AttributeTypeValueType(Base, BaseFieldMixin):
    __tablename__ = "attribute_type__value_type"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the type of database objects that provide the values for an attribute",
        },
    )

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "IS_DESCRIBED_BY"},
    )
    value_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        info={"edge": "IS_VALUE_FOR"},
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


class AttributeValue(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "attribute_value"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Defines the values available for attribute",
        },
    )
    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    text: Mapped[str] = mapped_column()

    # Relationships
    obj: Mapped[DBObject] = relationship(back_populates="attribute_values")


class Attribute(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "attribute"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "Attributes define characteristics of objects",
        },
    )
    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.attribute_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "IS_OF_TYPE"},
    )
    comment: Mapped[Optional[str]] = mapped_column()
    follow_up_required: Mapped[bool] = mapped_column()

    # Relationships
    obj: Mapped[DBObject] = relationship(back_populates="attribute_values")
    attribute_type: Mapped[AttributeType] = relationship(back_populates="attributes")
    attribute_values: Mapped[Optional[list[AttributeValue]]] = relationship(
        back_populates="attributes"
    )
    object_values: Mapped[Optional[list[DBObject]]] = relationship(
        back_populates="attributes"
    )


attribute_attribute_value = Table(
    "attribute__attribute_value",
    Base.metadata,
    Column(
        "attribute_id",
        VARCHAR(26),
        ForeignKey("uno.attribute.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"start_vertex": True},
    ),
    Column(
        "attribute_value_id",
        VARCHAR(26),
        ForeignKey("uno.attribute_value.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"end_vertex": True},
    ),
    Index(
        "ix_attribute_id__attribute_value_id",
        "attribute_id",
        "attribute_value_id",
    ),
    schema="uno",
    comment="Association table between Attribute and AttributeValue",
    info={"edge": "HAS_ATTRIBUTE_VALUE", "audited": True},
)


attribute_object_value = Table(
    "attribute__object_value",
    Base.metadata,
    Column(
        "attribute_id",
        VARCHAR(26),
        ForeignKey("uno.attribute.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"start_vertex": True},
    ),
    Column(
        "object_value_id",
        VARCHAR(26),
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        primary_key=True,
        info={"end_vertex": True},
    ),
    Index(
        "ix_attribute_id__object_value_id",
        "attribute_id",
        "object_value_id",
    ),
    schema="uno",
    comment="Association table between Attribute and Object Value (Meta)",
    info={"edge": "HAS_OBJECT_VALUE", "audited": True},
)
