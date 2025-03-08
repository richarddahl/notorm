# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional, ClassVar, Any

from sqlalchemy import ForeignKey, Index, UniqueConstraint

from sqlalchemy.dialects.postgresql import ENUM, ARRAY, JSONB
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.record.db import Base, str_26, str_255
from uno.apps.meta.records import (
    MetaRecord,
    MetaRecordMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
)
from uno.record.sql.sql_emitter import SQLStatement

from uno.apps.fltr.enums import Include, Match
from uno.apps.val.enums import Lookup
from uno.config import settings


class QueryFilterValue(Base):
    __tablename__ = "query__filter_value"
    __table_args__ = (
        Index("ix_query_id__filter_value_id", "query_id", "filter_value_id"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationships between queries and filter values.",
        },
    )
    display_name: ClassVar[str] = "Query Filter Value"
    display_name_plural: ClassVar[str] = "Query Filter Values"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        primary_key=True,
    )
    filter_value_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.filter_value.id", ondelete="CASCADE"),
        primary_key=True,
    )


class FilterFilterValue(Base):
    __tablename__ = "filter__filter_value"
    __table_args__ = (
        Index("ix_filter_id__filter_value_id", "filter_id", "filter_value_id"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationships between filters and filter values.",
        },
    )
    display_name: ClassVar[str] = "Filter Filter Value"
    display_name_plural: ClassVar[str] = "Filter Filter Values"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    # Columns
    filter_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.filter.id", ondelete="CASCADE"),
        primary_key=True,
    )
    filter_value_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.filter_value.id", ondelete="CASCADE"),
        primary_key=True,
    )


class QuerySubquery(Base):
    __tablename__ = "query__sub_query"
    __table_args__ = (
        Index("ix_query_id__subquery_id", "query_id", "subquery_id"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The relationships between queries and subqueries.",
        },
    )
    display_name: ClassVar[str] = "Query Subquery"
    display_name_plural: ClassVar[str] = "Query Subqueries"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        primary_key=True,
        doc="The query the subquery is associated with.",
    )
    subquery_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        primary_key=True,
        doc="The subquery associated with the query.",
    )


class Filter(Base):
    __tablename__ = "filter"
    __table_args__ = (
        UniqueConstraint(
            "source_meta_type",
            "destination_meta_type",
            "accessor",
            name="uq_filter__source_meta_type__destination_meta_type__accessor",
        ),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Used to enable user-defined filtering using the graph vertices and graph_edges.",
        },
    )
    display_name: ClassVar[str] = "Filter"
    display_name_plural: ClassVar[str] = "Filters"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the graph_node.",
    )
    display: Mapped[str] = mapped_column(
        doc="The edge label or property display of the filter.",
    )
    data_type: Mapped[str] = mapped_column(
        doc="The data type of the filter.",
    )
    source_meta_type: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
        doc="The meta_record type table filtered.",
    )
    destination_meta_type: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
        index=True,
        doc="The destination meta_record type table of the filter.",
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
    properties: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSONB,
        doc="The properties of the filter.",
    )


class FilterValue(
    MetaRecord,
    MetaRecordMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
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
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User definable values for use in queries.",
        },
    )
    display_name: ClassVar[str] = "Filter Value"
    display_name_plural: ClassVar[str] = "Filter Values"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    # Columns
    id: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_record.id"), primary_key=True
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
        ForeignKey(
            f"{settings.DB_SCHEMA}.meta_record.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    # Relationships
    queries: Mapped[Optional[list["Query"]]] = relationship(
        # back_populates="filter_values",
        secondary=QueryFilterValue.__table__,
        secondaryjoin=QueryFilterValue.filter_value_id == id,
        info={"edge": "FILTERS_WITH"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "filter_value",
        "inherit_condition": id == MetaRecord.id,
    }


class Query(
    MetaRecord,
    MetaRecordMixin,
    RecordAuditMixin,
    HistoryTableAuditMixin,
):
    __tablename__ = "query"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "User definable queries",
        },
    )
    display_name: ClassVar[str] = "Query"
    display_name_plural: ClassVar[str] = "Queries"

    sql_emitters: ClassVar[list[SQLStatement]] = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_record.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(doc="The name of the query.")
    queries_meta_type_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.meta_type.name", ondelete="CASCADE"),
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
    filter_values: Mapped[Optional[list[FilterValue]]] = relationship(
        # back_populates="queries",
        secondary=QueryFilterValue.__table__,
        secondaryjoin=QueryFilterValue.query_id == id,
    )
    sub_queries: Mapped[Optional[list["Query"]]] = relationship(
        # back_populates="queries",
        foreign_keys=[QuerySubquery.query_id],
        secondary=QuerySubquery.__table__,
        secondaryjoin=QuerySubquery.query_id == id,
    )
    queries: Mapped[Optional[list["Query"]]] = relationship(
        # back_populates="sub_queries",
        foreign_keys=[QuerySubquery.subquery_id],
        secondary=QuerySubquery.__table__,
        secondaryjoin=QuerySubquery.subquery_id == id,
    )
    attribute_type_applicability: Mapped[Optional["AttributeType"]] = relationship(
        # back_populates="description_limiting_query",
        primaryjoin="Query.id == AttributeType.description_limiting_query_id",
    )

    __mapper_args__ = {
        "polymorphic_identity": "query",
        "inherit_condition": id == MetaRecord.id,
    }
