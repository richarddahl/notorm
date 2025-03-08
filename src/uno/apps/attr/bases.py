# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar

from sqlalchemy import ForeignKey, Table, Column
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from uno.db.base import UnoBase, str_255, str_26
from uno.apps.meta.bases import (
    MetaBase,
    MetaTypeBase,
)
from uno.db.sql.sql_emitter import SQLEmitter
from uno.apps.fltr.bases import Query
from uno.config import settings


attribute_value = Table(
    "attribute__value",
    UnoBase.metadata,
    Column(
        "attribute_id",
        ForeignKey(f"{settings.DB_SCHEMA}.attribute.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    ),
    Column(
        "value_id",
        ForeignKey(f"{settings.DB_SCHEMA}.meta_record.id", ondelete="CASCADE"),
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
        ForeignKey(f"{settings.DB_SCHEMA}.attribute_type.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    ),
    Column(
        "meta_type_id",
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        nullable=False,
    ),
    comment="The relationship between attribute types and the meta_record types they describe",
)


class Attribute(UnoBase):
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
        ForeignKey(f"{settings.DB_SCHEMA}.meta_record.id"),
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
        # back_populates="attributes",
        doc="The type of attribute",
        info={"edge": "HAS_ATTRIBUTE_TYPE"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "attribute",
        "inherit_condition": id == MetaBase.id,
    }


class AttributeType(
    MetaBase,
    MetaBaseMixin,
    BaseAuditMixin,
    HistoryTableAuditMixin,
):
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
        ForeignKey(f"{settings.DB_SCHEMA}.meta_record.id"), primary_key=True
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
        doc="The meta_record types that the attribute type describes.",
    )
    description_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        index=True,
        doc="The query that determines which meta_record types are applicable to this attribute type.",
    )
    value_type_name: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        doc="The meta_record types that are values for the attribute type",
    )
    value_type_limiting_query_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
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
    parent: Mapped["AttributeType"] = relationship(
        foreign_keys=[parent_id],
        remote_side=[id],
        # back_populates="children",
        doc="The parent attribute type",
        info={"edge": "IS_PARENT_OF"},
    )
    children: Mapped[list["AttributeType"]] = relationship(
        foreign_keys=[id],
        # back_populates="parent",
        doc="The child attribute types",
        info={"edge": "IS_CHILD_OF"},
    )
    describes: Mapped[list[MetaType]] = relationship(
        primaryjoin=describes_id == MetaType.name,
        secondary=AttributeTypeMetaType.__table__,
        secondaryjoin=AttributeTypeMetaType.attribute_type_id == id,
        doc="The meta_record types that the attribute type describes.",
        info={"edge": "DESCRIBES"},
    )
    description_limiting_query: Mapped[Optional[Query]] = relationship(
        Query,
        # back_populates="attribute_type_applicability",
        primaryjoin=description_limiting_query_id == Query.id,
        doc="The query that determines which meta_record types are applicable to this attribute type.",
        info={"edge": "DETERMINES_APPLICABILITY"},
    )
    value_types: Mapped[list[MetaType]] = relationship(
        primaryjoin=value_type_name == MetaType.name,
        doc="The meta_record types that are values for the attribute type",
        info={"edge": "IS_VALUE_TYPE_FOR"},
    )

    attributes: Mapped[list[Attribute]] = relationship(
        # back_populates="attribute_type",
        foreign_keys=[Attribute.attribute_type_id],
        remote_side=Attribute.attribute_type_id,
        doc="The attributes with this attribute type",
        info={"edge": "HAS_ATTRIBUTE"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "attribute_type",
        "inherit_condition": id == MetaBase.id,
    }
