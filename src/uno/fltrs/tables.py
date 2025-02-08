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
    func,
)

from sqlalchemy.dialects.postgresql import (
    ENUM,
    ARRAY,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db.base import Base, str_26, str_255
from uno.db.mixins import BaseFieldMixin, RelatedObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL
from uno.objs.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertRelatedObjectFunctionSQL,
)

from uno.fltrs.enums import (
    GraphType,
    EdgeDirection,
    Include,
    Match,
    Lookup,
)


class FilterField(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filterfield"
    __table_args__ = (
        UniqueConstraint(
            "label",
            "graph_type",
            name="uq_label_graph_type",
        ),
        {
            "schema": "uno",
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
            "info": {"rls_policy": False, "in_graph": False},
        },
    )
    sql_emitters = [
        AlterGrantSQL,
        RecordVersionAuditSQL,
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]
    # Columns
    id: Mapped[str_26] = mapped_column(
        primary_key=True,
        index=True,
        doc="Primary Key",
        server_default=func.generate_ulid(),
    )
    accessor: Mapped[str_255] = mapped_column()
    label: Mapped[str] = mapped_column()
    data_type: Mapped[str_26] = mapped_column()
    graph_type: Mapped[GraphType] = mapped_column(
        ENUM(
            GraphType,
            name="graphtype",
            create_type=True,
            schema="uno",
        ),
        default=GraphType.PROPERTY,
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema="uno",
            )
        )
    )


class FilterFieldObjectType(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filterfield_ObjectType"
    __table_args__ = (
        UniqueConstraint(
            "filterfield_id",
            "object_type_id",
            "direction",
            name="uq_filterfield_ObjectType_direction",
        ),
        Index(
            "ix_filterfield_id_object_type_id_direction",
            "filterfield_id",
            "object_type_id",
            "direction",
        ),
        {
            "schema": "uno",
            "comment": "A FilterField associated with a ObjectType.",
            "info": {"rls_policy": False, "in_graph": False},
        },
    )

    # Columns
    filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filterfield.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterfield associated with a object_type.",
    )
    object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The object_type associated with a filterfield.",
    )
    direction: Mapped[str_26] = mapped_column(
        ENUM(
            EdgeDirection,
            name="edgedirection",
            create_type=True,
            schema="uno",
        ),
        primary_key=True,
        # server_default=EdgeDirection.FROM.name,
        doc="The direction of the edge.",
    )


class FilterKey(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filterkey"
    __table_args__ = (
        UniqueConstraint(
            "from_filterfield_id",
            "to_filterfield_id",
            "accessor",
            name="uq_from_to_accessor",
        ),
        Index(
            "ix_from_filterfield_id_to_filterfield_id_accessor",
            "from_filterfield_id",
            "to_filterfield_id",
            "accessor",
        ),
        {
            "schema": "uno",
            "comment": "A filterable path from one table to itself or another.",
            "info": {"rls_policy": False, "in_graph": False},
        },
    )

    # Columns
    from_filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filterfield.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterkey from which the filter key starts.",
    )
    to_filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filterfield.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterfield at which the filter key ends.",
    )
    accessor: Mapped[str] = mapped_column(
        index=True,
        primary_key=True,
        doc="The accessor for the filter key.",
    )
    graph_type: Mapped[GraphType] = mapped_column(
        ENUM(
            GraphType,
            name="graphtype",
            create_type=True,
            schema="uno",
        ),
        default=GraphType.PROPERTY,
    )
    lookups: Mapped[list[Lookup]] = mapped_column(
        ARRAY(
            ENUM(
                Lookup,
                name="lookup",
                create_type=True,
                schema="uno",
            )
        )
    )


class FilterValue(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filtervalue"
    __table_args__ = (
        UniqueConstraint(
            "field_id",
            "lookup",
            "include",
            "match",
            "bigint_value",
            "boolean_value",
            "date_value",
            "decimal_value",
            "object_value_id",
            "string_value",
            "text_value",
            "time_value",
            "timestamp_value",
            postgresql_nulls_not_distinct=True,
        ),
        Index(
            "ix_filtervalue__unique_together",
            "field_id",
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
                OR object_value_id IS NOT NULL
                OR string_value IS NOT NULL
                OR text_value IS NOT NULL
                OR time_value IS NOT NULL
                OR timestamp_value IS NOT NULL
            """,
            name="ck_filtervalue",
        ),
        {
            "comment": "User definable values for use in queries.",
            "schema": "uno",
            "info": {"rls_policy": "default", "audit_type": "history"},
        },
    )

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        # server_default=func.uno.insert_related_object("uno", "user"),
        doc="Primary Key",
        info={"edge": "HAS_ID"},
    )
    field_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filterfield.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        info={"edge": "FILTERS_FIELD"},
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
    object_value_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        info={"edge": "HAS_OBJECT_VALUE"},
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship(
        viewonly=True,
        doc="The tenant associated with the filter value.",
    )
    """
    fields: Mapped["Field"] = relationship(back_populates="filtervalues")
    # related_object: Mapped["RelatedObject"] = relationship(
    #    viewonly=True,
    #    back_populates="filtervalue",
    #    foreign_keys=[object_value_id],
    #    doc="Object value",
    # )
    object_value: Mapped["RelatedObject"] = relationship(
        back_populates="filter_object_values",
        foreign_keys=[object_value_id],
        doc="Object value",
    )
    """


class Query(Base, RelatedObjectPKMixin, BaseFieldMixin):
    __tablename__ = "query"
    __table_args__ = (
        {
            "comment": "User definable queries",
            "schema": "uno",
            "info": {"rls_policy": "default", "audit_type": "history"},
        },
    )

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.related_object.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
        # server_default=func.uno.insert_related_object("uno", "user"),
        doc="Primary Key",
        info={"edge": "HAS_ID"},
    )
    name: Mapped[str_255] = mapped_column(doc="The name of the query.")
    queries_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "QUERIES_ObjectType"},
    )
    show_results_with_object: Mapped[bool] = mapped_column(
        # server_default=text("false"),
        doc="Indicates if the results of the query should be returned with objects from the queries table type.",
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
    """
    query_filtervalue: Mapped[list["QueryFilterValue"]] = relationship(
        back_populates="query"
    )
    query_sub_query: Mapped[list["QuerySubquery"]] = relationship(
        back_populates="query"
    )
    """


class QueryFilterValue(Base):
    __tablename__ = "query_filtervalue"
    __table_args__ = (
        Index("ix_query_id__filtervalue_id", "query_id", "filtervalue_id"),
        {
            "schema": "uno",
            "comment": "The filter values associated with a query.",
            "info": {"rls_policy": False, "vertex": False},
        },
    )

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        info={"edge": "IS_QUERIED_THROUGH"},
    )
    filtervalue_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filtervalue.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        info={"edge": "QUERIES_FILTERVALUE"},
    )

    # Relationships
    """
    query: Mapped[Query] = relationship(back_populates="query_filtervalue")
    filtervalue: Mapped[FilterValue] = relationship(
        back_populates="query_filtervalue"
    )
    """


class QuerySubquery(Base):
    __tablename__ = "query_subquery"
    __table_args__ = (
        Index("ix_query_id__subquery_id", "query_id", "subquery_id"),
        {
            "schema": "uno",
            "comment": "The subqueries associated with a query",
            "info": {"rls_policy": False, "vertex": False},
        },
    )

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The query the subquery is associated with.",
        info={"edge": "HAS_PARENT_QUERY"},
    )
    subquery_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The subquery associated with the query.",
        info={"edge": "HAS_SUBQUERY"},
    )

    # Relationships
    """
    query: Mapped["Query"] = relationship(back_populates="query_sub_query")
    subquery: Mapped["Query"] = relationship(back_populates="query_sub_query")
    """
