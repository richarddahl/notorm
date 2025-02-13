# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

import datetime
import textwrap

from typing import Optional
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    Identity,
    text,
)

from sqlalchemy.dialects.postgresql import (
    ENUM,
    ARRAY,
)
from sqlalchemy.orm import relationship, mapped_column, Mapped

from uno.db.base import Base, str_26, str_255
from uno.db.mixins import BaseFieldMixin, DBObjectPKMixin
from uno.db.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL
from uno.objs.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertDBObjectFunctionSQL,
)


from uno.fltrs.enums import (
    FilterType,
    Include,
    Match,
    Lookup,
)


class Node(Base):
    __tablename__ = "node"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "A node in a graph, representing a table in the relational db.",
        },
    )
    verbose_name = "Node"
    verbose_name_plural = "Vertices"
    include_in_graph = False

    sql_emitters = []

    # id: Mapped[int] = mapped_column(
    #    Identity(),
    #    primary_key=True,
    #    unique=True,
    #    index=True,
    #    doc="The id of the node.",
    # )
    id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
        index=True,
        doc="The object type of the node.",
    )
    accessor: Mapped[str] = mapped_column(
        doc="The relational accessor for the node.",
    )
    label: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        doc="The Graph label of the node.",
    )


class Property(Base):
    __tablename__ = "property"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "A property of a node in a graph.",
        },
    )
    verbose_name = "Property"
    verbose_name_plural = "Properties"
    include_in_graph = False

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        doc="The object type of the property.",
    )
    accessor: Mapped[str] = mapped_column(
        doc="The relational accessor for the property.",
    )
    label: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="The Graph label of the Property.",
    )
    data_type: Mapped[str_26] = mapped_column(
        doc="The data type of the property.",
    )


class Edge(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "edge"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "An edge in a graph, representing a relationship between two tables in the relational db.",
        },
    )
    verbose_name = "Edge"
    verbose_name_plural = "Edges"
    include_in_graph = False

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    start_node_id: Mapped[int] = mapped_column(
        ForeignKey("uno.node.id", ondelete="CASCADE"),
        index=True,
        doc="The start node of the edge.",
    )
    end_node_id: Mapped[int] = mapped_column(
        ForeignKey("uno.node.id", ondelete="CASCADE"),
        index=True,
        doc="The end node of the edge.",
    )
    label: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="The Graph label of the edge.",
    )
    accessor: Mapped[str] = mapped_column(
        doc="The relational accessor for the edge.",
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


class Path(Base):
    __tablename__ = "path"
    __table_args__ = (
        UniqueConstraint(
            "start_edge_id",
            "end_edge_id",
            name="uq_start_edge_id_end_edge_id",
        ),
        # CheckConstraint(
        #    textwrap.dedent(
        #        """
        #        parent_path_id IS NOT NULL AND start_edge_id = path.parent_path_id.end_edge_id
        #        """
        #    ),
        #    name="ck_start_edge_id_end_edge_id",
        # ),
        {
            "schema": "uno",
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
        },
    )
    verbose_name = "Path"
    verbose_name_plural = "Paths"
    include_in_graph = False

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    start_edge_id: Mapped[int] = mapped_column(
        ForeignKey("uno.edge.id", ondelete="CASCADE"),
        index=True,
        doc="The start edge of the path.",
    )
    end_edge_id: Mapped[int] = mapped_column(
        ForeignKey("uno.edge.id", ondelete="CASCADE"),
        index=True,
        doc="The end edge of the path.",
    )
    parent_path_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("uno.path.id", ondelete="CASCADE"),
        index=True,
        doc="The parent path of the path.",
    )


class Filter(Base):
    __tablename__ = "filter"
    __table_args__ = (
        # UniqueConstraint(
        #    "start_edge_id",
        #    "end_edge_id",
        #    name="uq_start_edge_id_end_edge_id",
        # ),
        {
            "schema": "uno",
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
        },
    )
    verbose_name = "Filter"
    verbose_name_plural = "Filters"
    include_in_graph = False

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    filter_type: Mapped[FilterType] = mapped_column(
        ENUM(
            FilterType,
            name="filtertype",
            create_type=True,
            schema="uno",
        ),
        default=FilterType.PROPERTY,
    )
    property_id: Mapped[int] = mapped_column(
        ForeignKey("uno.property.id", ondelete="CASCADE"),
        index=True,
        doc="The property associated with the filter.",
    )
    edge_id: Mapped[int] = mapped_column(
        ForeignKey("uno.edge.id", ondelete="CASCADE"),
        index=True,
        doc="The edge associated with the filter.",
    )


class FilterField(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filter_field"
    __table_args__ = (
        # UniqueConstraint(
        #    "label",
        #    # "graph_type",
        #    name="uq_label_graph_type",
        # ),
        {
            "schema": "uno",
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
            "info": {"rls_policy": False, "in_graph": False},
        },
    )
    verbose_name = "Filter Field"
    verbose_name_plural = "Filter Fields"
    include_in_graph = False

    sql_emitters = []

    sql_emitters = [
        AlterGrantSQL,
        RecordVersionAuditSQL,
        InsertObjectTypeRecordSQL,
        InsertDBObjectFunctionSQL,
    ]
    # Columns
    node_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.node.id", ondelete="CASCADE"),
        index=True,
        doc="The node associated with the filter field.",
        info={"edge": "HAS_VERTEX"},
    )
    accessor: Mapped[str_255] = mapped_column()
    label: Mapped[str] = mapped_column()
    data_type: Mapped[str_26] = mapped_column()
    # graph_type: Mapped[GraphType] = mapped_column(
    #    ENUM(
    #        GraphType,
    #        name="graphtype",
    #        create_type=True,
    #        schema="uno",
    #    ),
    #    default=GraphType.PROPERTY,
    # )
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


class FilterFieldObjectType(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filter_field__object_type"
    __table_args__ = (
        # UniqueConstraint(
        #    "filterfield_id",
        #    "object_type_id",
        #    "direction",
        #    name="uq_filterfield_ObjectType_direction",
        # ),
        # Index(
        #    "ix_filterfield_id_object_type_id_direction",
        #    "filterfield_id",
        #    "object_type_id",
        #    #    "direction",
        # ),
        {
            "schema": "uno",
            "comment": "A FilterField associated with a ObjectType.",
            "info": {"rls_policy": False, "in_graph": False},
        },
    )
    verbose_name = "Filter Field ObjectType"
    verbose_name_plural = "Filter Field ObjectTypes"
    include_in_graph = False

    sql_emitters = []

    # Columns
    filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter_field.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterfield associated with a object_type.",
    )

    # direction: Mapped[str_26] = mapped_column(
    #    ENUM(
    #        EdgeDirection,
    #        name="edgedirection",
    #        create_type=True,
    #        schema="uno",
    #    ),
    #    primary_key=True,
    #    # server_default=EdgeDirection.FROM.name,
    #    doc="The direction of the edge.",
    # )


class FilterKey(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filter_key"
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
    verbose_name = "Filter Key"
    verbose_name_plural = "Filter Keys"
    include_in_graph = False

    sql_emitters = []

    # Columns
    from_filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter_field.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterkey from which the filter key starts.",
    )
    to_filterfield_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter_field.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        doc="The filterfield at which the filter key ends.",
    )
    accessor: Mapped[str] = mapped_column(
        index=True,
        primary_key=True,
        doc="The accessor for the filter key.",
    )
    # graph_type: Mapped[GraphType] = mapped_column(
    #    ENUM(
    #        GraphType,
    #        name="graphtype",
    #        create_type=True,
    #        schema="uno",
    #    ),
    #    default=GraphType.PROPERTY,
    # )
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


class FilterValue(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filter_value"
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
    verbose_name = "Filter Value"
    verbose_name_plural = "Filter Values"
    # include_in_graph = False

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    field_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter_field.id", ondelete="CASCADE"),
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
        ForeignKey("uno.db_object.id", ondelete="CASCADE"),
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
    # db_object: Mapped["DBObject"] = relationship(
    #    viewonly=True,
    #    back_populates="filtervalue",
    #    foreign_keys=[object_value_id],
    #    doc="Object value",
    # )
    object_value: Mapped["DBObject"] = relationship(
        back_populates="filter_object_values",
        foreign_keys=[object_value_id],
        doc="Object value",
    )
    """


class Query(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "query"
    __table_args__ = (
        {
            "comment": "User definable queries",
            "schema": "uno",
            "info": {"rls_policy": "default", "audit_type": "history"},
        },
    )
    verbose_name = "Query"
    verbose_name_plural = "Queries"
    # include_in_graph = False

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns

    name: Mapped[str_255] = mapped_column(doc="The name of the query.")
    queries_object_type_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        index=True,
        info={"edge": "QUERIES_ObjectType"},
    )
    show_results_with_object: Mapped[bool] = mapped_column(
        server_default=text("false"),
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
    __tablename__ = "query__filter_value"
    __table_args__ = (
        Index("ix_query_id__filtervalue_id", "query_id", "filtervalue_id"),
        {
            "schema": "uno",
            "comment": "The filter values associated with a query.",
            "info": {"rls_policy": False, "node": False},
        },
    )
    verbose_name = "Query Filter Value"
    verbose_name_plural = "Query Filter Values"
    include_in_graph = False

    sql_emitters = []

    # Columns
    query_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.query.id", ondelete="CASCADE"),
        index=True,
        primary_key=True,
        info={"edge": "IS_QUERIED_THROUGH"},
    )
    filtervalue_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter_value.id", ondelete="CASCADE"),
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
    __tablename__ = "query__subquery"
    __table_args__ = (
        Index("ix_query_id__subquery_id", "query_id", "subquery_id"),
        {
            "schema": "uno",
            "comment": "The subqueries associated with a query",
            "info": {"rls_policy": False, "node": False},
        },
    )
    verbose_name = "Query Subquery"
    verbose_name_plural = "Query Subqueries"
    include_in_graph = False

    sql_emitters = []

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
