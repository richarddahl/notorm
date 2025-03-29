# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    ForeignKey,
    UniqueConstraint,
    Table,
    Column,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import ENUM, ARRAY, VARCHAR

from uno.db import UnoBase, str_26, str_255, str_63
from uno.mixins import BaseMixin
from uno.auth.mixins import GroupBaseMixin
from uno.enums import Include, Match, Lookup
from uno.meta.bases import MetaBase
from uno.config import settings

query_value__values = Table(
    "query_value__values",
    UnoBase.metadata,
    Column(
        "query_value_id",
        ForeignKey("query_value.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "FILTER_VALUES"},
    ),
    Column(
        "value_id",
        ForeignKey("meta_record.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "VALUES"},
    ),
    Index("ix_query_value_id__value_id", "query_value_id", "value_id"),
)

query__query_value = Table(
    "query__query_value",
    UnoBase.metadata,
    Column(
        "query_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "FILTER_VALUES"},
    ),
    Column(
        "query_value_id",
        ForeignKey("query_value.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "QUERIES"},
    ),
    Index("ix_query_id__query_value_id", "query_id", "query_value_id"),
)

query__child_query = Table(
    "query__child_query",
    UnoBase.metadata,
    Column(
        "query_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "CHILD_QUERIES"},
    ),
    Column(
        "childquery_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
        info={"edge": "QUERIES"},
    ),
    Index("ix_query_id__child_query_id", "query_id", "childquery_id"),
)


class QueryPathBase(GroupBaseMixin, BaseMixin, UnoBase):
    __tablename__ = "query_path"
    __table_args__ = {"comment": "Enables user-defined filtering via the graph DB."}

    # Columns
    source_meta_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The source node filtered.",
        info={
            "edge": "SOURCE_META_TYPE",
            "reverse_edge": "SOURCE_FILTER_PATHS",
        },
    )
    destination_meta_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The destination node of the filter",
        info={
            "edge": "DESTINATION_META_TYPE",
            "reverse_edge": "DESTINATION_FILTER_PATHS",
        },
    )
    filter_ids: Mapped[list[str_26]] = mapped_column(
        ARRAY(VARCHAR(26)),
        doc="The filters for the filter path",
        info={
            "edge": "FILTER_IDS",
            "reverse_edge": "FILTER_PATHS",
        },
    )
    path: Mapped[str] = mapped_column(
        index=True,
        unique=True,
        nullable=False,
        doc="The path of the filter",
    )
    data_type: Mapped[str] = mapped_column(
        doc="The data type of the filter",
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema=settings.DB_SCHEMA,
            )
        ),
        doc="The lookups for the filter",
    )

    # Relationships
    source_meta_type: Mapped["MetaBase"] = relationship(
        doc="The source meta_record type of the filter",
    )


class QueryValueBase(GroupBaseMixin, BaseMixin, UnoBase):
    __tablename__ = "query_value"
    __table_args__ = (
        UniqueConstraint(
            "query_path_id",
            "include",
            "match",
            "lookup",
        ),
        Index(
            "ix_filtervalue__unique_together",
            "query_path_id",
            "include",
            "match",
            "lookup",
        ),
        {"comment": "User definable values for use in queries."},
    )

    # Columns
    query_path_id: Mapped[str_26] = mapped_column(
        ForeignKey("query_path.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The UnoFilter Path to which the value belongs",
        info={
            "edge": "FILTER_PATH",
            "reverse_edge": "FILTER_VALUES",
        },
    )
    include: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Include.INCLUDE,
    )
    match: Mapped[Match] = mapped_column(
        ENUM(
            Match,
            name="match",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Match.AND,
    )
    lookup: Mapped[Lookup] = mapped_column(
        ENUM(
            Lookup,
            name="lookup",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Lookup.EQUAL,
    )

    # Relationships
    query_path: Mapped[QueryPathBase] = relationship(
        doc="The filter to which the value belongs",
    )
    values: Mapped[list["MetaBase"]] = relationship(
        secondary=query_value__values,
        doc="The value of the filter",
    )
    queries: Mapped[list["QueryBase"]] = relationship(
        secondary=query__query_value,
        doc="The queries that use the filter value",
        back_populates="query_values",
    )


class QueryBase(GroupBaseMixin, BaseMixin, UnoBase):
    __tablename__ = "query"
    __table_args__ = ({"comment": "User definable queries"},)

    # Columns
    name: Mapped[str_255] = mapped_column(
        index=True,
        nullable=False,
        doc="The name of the query.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        doc="The description of the query."
    )
    query_meta_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The type of the query.",
        info={
            "edge": "META_TYPE",
            "reverse_edge": "QUERIES",
        },
    )
    include_values: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Include.INCLUDE,
        doc="Indicate if the query should return records including or excluding the queries results.",
    )
    match_values: Mapped[Match] = mapped_column(
        ENUM(
            Match,
            name="match",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Match.AND,
        doc="Indicate if the query should return records matching all or any of the filter values.",
    )
    include_queries: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Include.INCLUDE,
        doc="Indicate if the query should return records including or excluding the subqueries results.",
    )
    match_queries: Mapped[Match] = mapped_column(
        ENUM(
            Match,
            name="match",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Match.AND,
        doc="Indicate if the query should return records matching all or any of the subquery values.",
    )

    # Relationships
    query_values: Mapped[Optional[list[QueryValueBase]]] = relationship(
        secondary=query__query_value,
        back_populates="queries",
    )
    sub_queries: Mapped[Optional[list["QueryBase"]]] = relationship(
        secondary=query__child_query,
        foreign_keys=[query__child_query.c.query_id],
        back_populates="queries",
    )
    queries: Mapped[Optional[list["QueryBase"]]] = relationship(
        secondary=query__child_query,
        foreign_keys=[query__child_query.c.childquery_id],
        back_populates="sub_queries",
    )
    # attribute_type_applicability: Mapped[Optional["AttributeType"]] = relationship(
    #    primaryjoin="Query.id == AttributeType.description_limiting_query_id",
    # )
