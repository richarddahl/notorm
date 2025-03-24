# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Table, Column, FetchedValue
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.base import UnoBase, str_255, str_26, str_63
from uno.db.mixins import GeneralBaseMixin
from uno.apps.fltr.bases import QueryBase
from uno.apps.meta.bases import MetaTypeBase


attribute__value = Table(
    "attribute__value",
    UnoBase.metadata,
    Column(
        "attribute_id",
        ForeignKey("attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "VALUES"},
    ),
    Column(
        "value_id",
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "ATTRIBUTES"},
    ),
    comment="The relationship between attributes and their values",
)


attribute_type___meta_type = Table(
    "attribute_type__meta_type",
    UnoBase.metadata,
    Column(
        "attribute_type_id",
        ForeignKey("attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "META_TYPES"},
    ),
    Column(
        "meta_type_id",
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "ATTRIBUTE_TYPES"},
    ),
    comment="The relationship between attribute types and the meta_record types they describe",
)


attribute_type__value_type = Table(
    "attribute_type__value_type",
    UnoBase.metadata,
    Column(
        "attribute_type_id",
        ForeignKey("attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "VALUE_TYPES"},
    ),
    Column(
        "meta_type_id",
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "ATTRIBUTE_TYPES"},
    ),
    comment="The relationship between attribute types and the meta_record types that are values for the attribute type",
)


class AttributeBase(GeneralBaseMixin, UnoBase):
    __tablename__ = "attribute"
    __table_args__ = {"comment": "Attributes define characteristics of objects"}

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey(
            "attribute_type.id",
            ondelete="CASCADE",
        ),
        index=True,
        doc="The type of attribute",
        info={
            "edge": "ATTRIBUTE_TYPE",
            "reverse_edge": "ATTRIBUTES",
        },
    )
    comment: Mapped[Optional[str]] = mapped_column(
        doc="A comment about the attribute",
    )
    follow_up_required: Mapped[bool] = mapped_column(
        server_default="false",
        doc="Indicates if follow-up is required",
    )

    # Relationships
    attribute_type: Mapped["AttributeTypeBase"] = relationship(
        foreign_keys=[attribute_type_id],
        doc="The type of attribute",
    )


class AttributeTypeBase(UnoBase, GeneralBaseMixin):
    __tablename__ = "attribute_type"
    __table_args__ = {
        "comment": "Defines the type of attribute that can be associated with an object"
    }

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=True,
        server_default=FetchedValue(),
        doc="Primary Key and Foreign Key to Meta Base",
    )
    name: Mapped[str_255] = mapped_column(unique=True)
    text: Mapped[str] = mapped_column()
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(
            "attribute_type.id",
            ondelete="SET NULL",
        ),
        index=True,
        nullable=True,
        doc="The parent attribute type",
        info={
            "edge": "PARENT",
            "reverse_edge": "CHILDREN",
        },
    )
    description_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("query.id", ondelete="CASCADE"),
        index=True,
        doc="Query that determines which object types are described by Attributes.",
        info={
            "edge": "DESCRIPTION_LIMITING_QUERY",
            "reverse_edge": "DESCRIPTION_LIMITED_ATTRIBUTE_TYPES",
        },
    )
    value_type_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(
            "query.id",
            ondelete="CASCADE",
        ),
        doc="Query that determines which object types are values for Attributes.",
        info={
            "edge": "VALUE_TYPE_LIMITING_QUERY",
            "reverse_edge": "VALUE_TYPE_LIMITED_ATTRIBUTE_TYPES",
        },
    )
    required: Mapped[bool] = mapped_column(
        default=False,
        doc="Indicates the attribute is required",
    )
    multiple_allowed: Mapped[bool] = mapped_column(
        default=False,
        doc="Indicates the attribute may have multiple values",
    )
    comment_required: Mapped[bool] = mapped_column(
        default=False,
        doc="Indicates a comment is required",
    )
    initial_comment: Mapped[Optional[str]] = mapped_column(
        doc="The initial comment for attributes of this type",
    )

    # Relationships
    parent: Mapped["AttributeTypeBase"] = relationship(
        foreign_keys=[parent_id],
        back_populates="children",
        doc="The parent attribute type",
    )
    children: Mapped[list["AttributeTypeBase"]] = relationship(
        back_populates="parent",
        remote_side=[id],
        doc="The child attribute types",
    )
    describes: Mapped[list[MetaTypeBase]] = relationship(
        secondary=attribute_type___meta_type,
        doc="The meta_record types that the attribute type describes.",
    )
    description_limiting_query: Mapped[Optional[QueryBase]] = relationship(
        QueryBase,
        foreign_keys=[description_limiting_query_id],
        doc="The query that determines which meta_record types are applicable to this attribute type.",
    )
    value_types: Mapped[list[MetaTypeBase]] = relationship(
        secondary=attribute_type__value_type,
        doc="The meta_record types that are values for the attribute type",
    )
    attributes: Mapped[list[AttributeBase]] = relationship(
        back_populates="attribute_type",
        doc="The attributes with this attribute type",
    )
    value_type_limiting_query: Mapped[Optional[QueryBase]] = relationship(
        QueryBase,
        foreign_keys=[value_type_limiting_query_id],
        doc="The query that determines which meta_record types are used as values for the attribute type.",
    )
