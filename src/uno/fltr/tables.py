# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime

from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    text,
)

from sqlalchemy.dialects.postgresql import (
    ENUM,
    ARRAY,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db.tables import (
    Base,
    RelatedObject,
    BaseMetaMixin,
    RecordUserAuditMixin,
    str_26,
    str_255,
)
from uno.db.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL

from uno.fltr.enums import (
    DataType,
    Include,
    Match,
    Lookup,
)
from uno.config import settings


class Filter(Base):
    __tablename__ = "filter"
    __table_args__ = (
        UniqueConstraint(
            "table_name",
            "name",
            "destination_table_name",
            name="uq_table_name_label_destination_table_name",
        ),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
        },
    )
    display_name = "Filter"
    display_name_plural = "Filters"

    sql_emitters = []

    include_in_graph = False

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    # filter_type: Mapped[FilterType] = mapped_column(
    #    ENUM(
    #        FilterType,
    #        name="filtertype",
    #        create_type=True,
    #        schema="uno",
    #    ),
    #    default=FilterType.PROPERTY,
    # )
    data_type: Mapped[str] = mapped_column(
        # ENUM(
        #    DataType,
        #    name="datatype",
        #    create_type=True,
        #    schema="uno",
        # ),
        doc="The data type of the filter.",
    )
    table_name: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
        index=True,
        doc="The table filtered.",
    )
    destination_table_name: Mapped[str_255] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
        index=True,
        doc="The destination table of the filter.",
    )
    name: Mapped[str_255] = mapped_column(
        doc="The edge label or property name of the filter.",
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
                schema="uno",
            )
        ),
        doc="The lookups for the filter.",
    )


class QueryFilterValue(Base):
    __tablename__ = "query_filtervalue"
    __table_args__ = (
        Index("ix_query_id__filtervalue_id", "query_id", "filtervalue_id"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The filter values associated with a query.",
        },
    )
    display_name = "Query Filter Value"
    display_name_plural = "Query Filter Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.query.id", ondelete="CASCADE"),
        primary_key=True,
    )
    filtervalue_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.filtervalue.id", ondelete="CASCADE"),
        primary_key=True,
    )


class FilterValue(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "filtervalue"
    __table_args__ = (
        UniqueConstraint(
            "filter_id",
            "lookup",
            "include",
            "match",
            "bigint_value",
            "boolean_value",
            "date_value",
            "decimal_value",
            "relatedobject_value_id",
            "string_value",
            "text_value",
            "time_value",
            "timestamp_value",
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "ix_filtervalue__unique_together",
            "filter_id",
            "lookup",
            "include",
            "match",
        ),
        CheckConstraint(
            """
                bigint_value IS NOT NULL
                OR boolean_value IS NOT NULL
                OR date_value IS NOT NULL
                OR decimal_value IS NOT NULL
                OR relatedobject_value_id IS NOT NULL
                OR string_value IS NOT NULL
                OR text_value IS NOT NULL
                OR time_value IS NOT NULL
                OR timestamp_value IS NOT NULL
            """,
            name="ck_filtervalue",
        ),
        {
            "comment": "User definable values for use in queries.",
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Filter Value"
    display_name_plural = "Filter Values"

    sql_emitters = []
    include_in_graph = False

    # Columns
    id: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    filter_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.filter.id", ondelete="CASCADE"),
        index=True,
    )
    lookup: Mapped[Lookup] = mapped_column(
        ENUM(
            Lookup,
            name="lookup",
            create_type=True,
            schema="uno",
        ),
        insert_default=Lookup.EQUAL,
    )
    include: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema="uno",
        ),
        insert_default=Include.INCLUDE,
    )
    match: Mapped[Match] = mapped_column(
        ENUM(Match, name="match", create_type=True, schema="uno"),
        insert_default=Match.AND,
    )
    bigint_value: Mapped[Optional[int]] = mapped_column()
    boolean_value: Mapped[Optional[bool]] = mapped_column()
    date_value: Mapped[Optional[datetime.date]] = mapped_column()
    decimal_value: Mapped[Optional[Decimal]] = mapped_column()
    text_value: Mapped[Optional[str]] = mapped_column()
    time_value: Mapped[Optional[datetime.time]] = mapped_column()
    timestamp_value: Mapped[Optional[datetime.datetime]] = mapped_column()
    string_value: Mapped[Optional[str_255]] = mapped_column()
    relatedobject_value_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(
            f"{settings.DB_SCHEMA}.relatedobject.id",
            ondelete="CASCADE",
        ),
        index=True,
    )

    # Relationships
    queries: Mapped[Optional[list["Query"]]] = relationship(
        back_populates="filter_values",
        secondary=QueryFilterValue.__table__,
        secondaryjoin=QueryFilterValue.filtervalue_id == id,
    )

    __mapper_args__ = {
        "polymorphic_identity": "filtervalue",
        "inherit_condition": id == RelatedObject.id,
    }


class QuerySubquery(Base):
    __tablename__ = "query_subquery"
    __table_args__ = (
        Index("ix_query_id__subquery_id", "query_id", "subquery_id"),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "The subqueries associated with a query",
        },
    )
    display_name = "Query Subquery"
    display_name_plural = "Query Subqueries"
    include_in_graph = False

    sql_emitters = []

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


class Query(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "query"
    __table_args__ = (
        {
            "comment": "User definable queries",
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Query"
    display_name_plural = "Queries"
    include_in_graph = False

    sql_emitters = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(doc="The name of the query.")
    queries_objecttype_name: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
        index=True,
    )
    include_values: Mapped[Include] = mapped_column(
        ENUM(
            Include,
            name="include",
            create_type=True,
            schema="uno",
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
            schema="uno",
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
        back_populates="queries",
        secondary=QueryFilterValue.__table__,
        secondaryjoin=QueryFilterValue.query_id == id,
    )
    sub_queries: Mapped[Optional[list["Query"]]] = relationship(
        back_populates="queries",
        foreign_keys=[QuerySubquery.query_id],
        secondary=QuerySubquery.__table__,
        secondaryjoin=QuerySubquery.query_id == id,
    )
    queries: Mapped[Optional[list["Query"]]] = relationship(
        back_populates="sub_queries",
        foreign_keys=[QuerySubquery.subquery_id],
        secondary=QuerySubquery.__table__,
        secondaryjoin=QuerySubquery.subquery_id == id,
    )
    attribute_type_applicability: Mapped[Optional["AttributeType"]] = relationship(
        back_populates="objecttype_query",
        primaryjoin="Query.id == AttributeType.description_query_id",
    )
    attribute_value_applicability: Mapped[Optional["AttributeType"]] = relationship(
        back_populates="value_type_query",
        primaryjoin="Query.id == AttributeType.value_type_query_id",
    )

    __mapper_args__ = {
        "polymorphic_identity": "query",
        "inherit_condition": id == RelatedObject.id,
    }
