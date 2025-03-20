# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.base import UnoBase, str_255, str_26, str_63
from uno.db.mixins import GeneralBaseMixin
from uno.apps.fltr.bases import QueryBase
from uno.apps.meta.bases import MetaTypeBase


attribute_value = Table(
    "attribute__value",
    UnoBase.metadata,
    Column(
        "attribute_id",
        ForeignKey("attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    ),
    Column(
        "value_id",
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
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
    ),
    Column(
        "meta_type_id",
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
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
    ),
    Column(
        "meta_type_id",
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    ),
    comment="The relationship between attribute types and the meta_record types that are values for the attribute type",
)


class AttributeBase(GeneralBaseMixin, UnoBase):
    __tablename__ = "attribute"
    __table_args__ = ({"comment": "Attributes define characteristics of objects"},)

    # Columns
    attribute_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("attribute_type.id", ondelete="CASCADE"),
        index=True,
        doc="The type of attribute",
    )
    comment: Mapped[Optional[str]] = mapped_column(doc="A comment about the attribute")
    follow_up_required: Mapped[bool] = mapped_column(doc="Is follow up required?")

    # Relationships
    attribute_type: Mapped["AttributeTypeBase"] = relationship(
        foreign_keys=[attribute_type_id],
        doc="The type of attribute",
    )


class AttributeTypeBase(UnoBase, GeneralBaseMixin):
    __tablename__ = "attribute_type"
    __table_args__ = (
        {
            "comment": "Defines the type of attribute that can be associated with an object"
        },
    )

    # Columns
    name: Mapped[str_255] = mapped_column(unique=True)
    text: Mapped[str] = mapped_column()
    parent_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("attribute_type.id", ondelete="SET NULL"),
        index=True,
        doc="The parent attribute type",
    )
    description_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("query.id", ondelete="CASCADE"),
        index=True,
        doc="The query that determines which meta_record types are applicable to this attribute type.",
    )
    value_type_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("query.id", ondelete="CASCADE"),
        doc="The query that determines which meta_record types are used as values for the attribute type.",
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
    parent: Mapped["AttributeTypeBase"] = relationship(
        foreign_keys=[parent_id],
        remote_side=[id],
        doc="The parent attribute type",
    )
    children: Mapped[list["AttributeTypeBase"]] = relationship(
        foreign_keys=[id],
        doc="The child attribute types",
    )
    describes: Mapped[list[MetaTypeBase]] = relationship(
        secondary=attribute_type___meta_type,
        doc="The meta_record types that the attribute type describes.",
    )
    description_limiting_query: Mapped[Optional[QueryBase]] = relationship(
        QueryBase,
        doc="The query that determines which meta_record types are applicable to this attribute type.",
    )
    value_types: Mapped[list[MetaTypeBase]] = relationship(
        secondary=attribute_type__value_type,
        doc="The meta_record types that are values for the attribute type",
        info={"edge": "IS_VALUE_TYPE_FOR"},
    )
    attributes: Mapped[list[AttributeBase]] = relationship(
        doc="The attributes with this attribute type",
        info={"edge": "HAS_ATTRIBUTE"},
    )
    value_type_limiting_query: Mapped[Optional[QueryBase]] = relationship(
        QueryBase,
        doc="The query that determines which meta_record types are used as values for the attribute type.",
    )
