# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import ForeignKey, Table, Column, UniqueConstraint
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.model import UnoModel, PostgresTypes
from uno.meta.objs import MetaTypeModel, MetaRecordModel
from uno.authorization.mixins import DefaultModelMixin
from uno.queries.models import QueryModel


attribute__value = Table(
    "attribute__value",
    UnoModel.metadata,
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
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "ATTRIBUTES"},
    ),
    comment="The relationship between attributes and their values",
    extend_existing=True,
)

attribute__meta = Table(
    "attribute__meta",
    UnoModel.metadata,
    Column(
        "attribute_id",
        ForeignKey("attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "META"},
    ),
    Column(
        "meta_id",
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
        info={"edge": "ATTRIBUTES"},
    ),
    comment="The relationship between attributes and their meta_record values",
    extend_existing=True,
)


attribute_type___meta_type = Table(
    "attribute_type__meta_type",
    UnoModel.metadata,
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
    extend_existing=True,
)


attribute_type__value_type = Table(
    "attribute_type__value_type",
    UnoModel.metadata,
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
    extend_existing=True,
)


class AttributeTypeModel(DefaultModelMixin, UnoModel):
    __tablename__ = "attribute_type"
    __table_args__ = (
        UniqueConstraint(
            "name",
            "group_id",
            name="uqi_attribute_type_name_group_id",
        ),
        {
            "comment": "Defines the type of attribute that can be associated with an object",
            "extend_existing": True
        },
    )

    # Columns
    # ID  necessary on this base as the relationships apparently need it,
    # but it is simply superceding the ID column (it is identical to)
    # of the ModelMixin
    id: Mapped[PostgresTypes.String26] = mapped_column(
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        doc="The unique identifier for the attribute type",
        info={"graph_excludes": True},
    )
    name: Mapped[PostgresTypes.String255] = mapped_column(
        doc="The name of the attribute type",
    )
    text: Mapped[str] = mapped_column(
        doc="The text of the attribute type, usually a question or statement about the meta type it describes",
    )
    parent_id: Mapped[Optional[PostgresTypes.String26]] = mapped_column(
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
    description_limiting_query_id: Mapped[Optional[PostgresTypes.String26]] = (
        mapped_column(
            ForeignKey("query.id", ondelete="CASCADE"),
            index=True,
            doc="Query that determines which object types are described by Attributes.",
            info={
                "edge": "DESCRIPTION_LIMITING_QUERY",
                "reverse_edge": "DESCRIPTION_LIMITED_ATTRIBUTE_TYPES",
            },
        )
    )
    value_type_limiting_query_id: Mapped[Optional[PostgresTypes.String26]] = (
        mapped_column(
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
    display_with_objects: Mapped[bool] = mapped_column(
        default=False,
        doc="Indicates the attribute should be displayed with the objects to which it applies",
    )
    initial_comment: Mapped[Optional[str]] = mapped_column(
        doc="The initial comment for attributes of this type",
    )

    # Relationships
    parent: Mapped["AttributeTypeModel"] = relationship(
        foreign_keys=[parent_id],
        back_populates="children",
        doc="The parent attribute type",
    )
    children: Mapped[list["AttributeTypeModel"]] = relationship(
        back_populates="parent",
        remote_side=[id],
        doc="The child attribute types",
    )
    describes: Mapped[list[MetaTypeModel]] = relationship(
        secondary=attribute_type___meta_type,
        doc="The meta_record types that the attribute type describes.",
    )
    description_limiting_query: Mapped[Optional[QueryModel]] = relationship(
        QueryModel,
        foreign_keys=[description_limiting_query_id],
        doc="The query that determines which meta_record types are applicable to this attribute type.",
    )
    value_types: Mapped[list[MetaTypeModel]] = relationship(
        secondary=attribute_type__value_type,
        doc="The meta_record types that are values for the attribute type",
    )
    value_type_limiting_query: Mapped[Optional[QueryModel]] = relationship(
        QueryModel,
        foreign_keys=[value_type_limiting_query_id],
        doc="The query that determines which meta_record types are used as values for the attribute type.",
    )
    attributes: Mapped[list["AttributeModel"]] = relationship(
        back_populates="attribute_type",
        doc="The attributes with this attribute type",
    )


class AttributeModel(DefaultModelMixin, UnoModel):
    __tablename__ = "attribute"
    __table_args__ = {"comment": "Attributes define characteristics of objects", "extend_existing": True}

    # Columns
    attribute_type_id: Mapped[PostgresTypes.String26] = mapped_column(
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
    attribute_type: Mapped[AttributeTypeModel] = relationship(
        foreign_keys=[attribute_type_id],
        back_populates="attributes",
        doc="The type of attribute",
    )
    values: Mapped[list["MetaRecordModel"]] = relationship(
        secondary=attribute__value,
        doc="The values for the attribute",
    )
    meta_records: Mapped[list["MetaRecordModel"]] = relationship(
        secondary=attribute__meta,
        doc="The meta_record values for the attribute",
    )
