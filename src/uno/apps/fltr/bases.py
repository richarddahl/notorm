# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, Any
from sqlalchemy import (
    ForeignKey,
    Index,
    ForeignKey,
    UniqueConstraint,
    Identity,
    text,
    Table,
    Column,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import (
    ENUM,
    VARCHAR,
    BIGINT,
    ARRAY,
    JSONB,
)

from uno.db.base import UnoBase, str_26, str_255, str_63
from uno.db.mixins import GeneralBaseMixin
from uno.db.sql.sql_config import TableSQLConfig
from uno.db.sql.graph_sql_emitters import TableGraphSQLEmitter
from uno.db.enums import SQLOperation
from uno.db.enums import Include, Match
from uno.apps.val.enums import Lookup
from uno.config import settings


"""
query__filter_value = Table(
    "query__filter_value",
    UnoBase.metadata,
    Column(
        "query_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "filter_value_id",
        ForeignKey("filter_value.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Index("ix_query_id__filter_value_id", "query_id", "filter_value_id"),
)


filter__filter_value = Table(
    "filter__filter_value",
    UnoBase.metadata,
    Column(
        "filter_id",
        ForeignKey("filter.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "filter_value_id",
        ForeignKey("filter_value.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Index("ix_filter_id__filter_value_id", "filter_id", "filter_value_id"),
)

query__sub_query = Table(
    "query__sub_query",
    UnoBase.metadata,
    Column(
        "query_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Column(
        "subquery_id",
        ForeignKey("query.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    ),
    Index("ix_query_id__subquery_id", "query_id", "subquery_id"),
)
"""


class FilterBase(UnoBase):
    __tablename__ = "filter"
    __table_args__ = (
        UniqueConstraint(
            "source_table_name",
            "remote_table_name",
            "accessor",
            name="uq_filter__source_table_name__remote_table_name__accessor",
        ),
        {
            "comment": "Used to enable user-defined filtering using the graph vertices and graph_edges.",
        },
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the filter.",
    )
    label: Mapped[str] = mapped_column(
        doc="The edge label or property display of the filter.",
    )
    data_type: Mapped[str] = mapped_column(
        doc="The data type of the filter.",
    )
    source_table_name: Mapped[int] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The source table filtered.",
    )
    remote_table_name: Mapped[int] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        doc="The destination table of the filter.",
    )
    accessor: Mapped[str_255] = mapped_column(
        index=True,
        doc="The relational db accessor for the filter.",
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
        doc="The lookups for the filter.",
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("filter.id", ondelete="CASCADE"),
        index=True,
        doc="The parent filter id.",
    )
    properties: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        doc="The properties of the filter.",
    )


"""

class FilterValue(UnoBase, GeneralBaseMixin):
    __tablename__ = "filter_value"
    __table_args__ = (
        UniqueConstraint(
            "include",
            "match",
            "lookup",
            "value_id",
        ),
        Index(
            "ix_filtervalue__unique_together",
            "include",
            "match",
            "lookup",
            "value_id",
        ),
        {"comment": "User definable values for use in queries."},
    )

    # Columns

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
        ENUM(Match, name="match", create_type=True, schema="uno"),
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
    value_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta.id", ondelete="CASCADE"),
        index=True,
    )

    # Relationships
    queries: Mapped[Optional[list["Query"]]] = relationship(
        secondary=query__filter_value,
        info={"edge": "FILTERS_WITH"},
    )


class Query(UnoBase, GeneralBaseMixin):
    __tablename__ = "query"
    __table_args__ = ({"comment": "User definable queries"},)

    # Columns
    name: Mapped[str_255] = mapped_column(doc="The name of the query.")
    queries_meta_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("meta_type.id", ondelete="CASCADE"),
        index=True,
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
        ENUM(Match, name="match", create_type=True, schema="uno"),
        insert_default=Match.AND,
        doc="Indicate if the query should return records matching all or any of the filter values.",
    )
    include_subqueries: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema=settings.DB_SCHEMA,
        ),
        insert_default=Include.INCLUDE,
        doc="Indicate if the query should return records including or excluding the subqueries results.",
    )
    match_subqueries: Mapped[Match] = mapped_column(
        ENUM(Match, name="match", create_type=True, schema="uno"),
        insert_default=Match.AND,
        doc="Indicate if the query should return records matching all or any of the subquery values.",
    )

    # Relationships
    # filter_values: Mapped[Optional[list[FilterValue]]] = relationship(
    #    secondary=query__filter_value,
    #    secondaryjoin=query__filter_value.query_id == id,
    # )
    # sub_queries: Mapped[Optional[list["Query"]]] = relationship(
    #    foreign_keys=[query__sub_query.query_id],
    #    secondary=query__sub_query,
    #    secondaryjoin=query__sub_query.query_id == id,
    # )
    # queries: Mapped[Optional[list["Query"]]] = relationship(
    #    foreign_keys=[query__sub_query.subquery_id],
    #    secondary=query__sub_query,
    #    secondaryjoin=query__sub_query.subquery_id == id,
    # )
    # attribute_type_applicability: Mapped[Optional["AttributeType"]] = relationship(
    #    primaryjoin="Query.id == AttributeType.description_limiting_query_id",
    # )

"""
