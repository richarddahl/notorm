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
from uno.sql_emitters import RecordVersionAuditSQL, AlterGrantSQL
from uno.obj.sql_emitters import (
    InsertObjectTypeRecordSQL,
    InsertDBObjectFunctionSQL,
)

from uno.fltr.enums import (
    FilterType,
    DataType,
    Include,
    Match,
    Lookup,
)

'''
class Node(Base):
    __tablename__ = "node"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "A node in a graph, representing a table in the relational db.",
        },
    )
    display_name = "Node"
    display_name_plural = "Nodes"

    sql_emitters = []

    object_type_id: Mapped[int] = mapped_column(
        ForeignKey("uno.object_type.id", ondelete="CASCADE"),
        primary_key=True,
        unique=True,
        index=True,
        doc="The object type of the node.",
    )
    accessor: Mapped[str_255] = mapped_column(
        doc="The relational accessor for the node.",
    )
    label: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="The Graph label of the node.",
    )


class Edge(Base):
    __tablename__ = "edge"
    __table_args__ = (
        UniqueConstraint(
            "start_node_label",
            "label",
            "destination_table_name",
            name="uq_start_node_label_label_destination_table_name",
        ),
        Index(
            "ix_start_node_label_label_destination_table_name",
            "start_node_label",
            "label",
            "destination_table_name",
        ),
        {
            "schema": "uno",
            "comment": "An edge in a graph, representing a relationship between two tables in the relational db.",
        },
    )
    display_name = "Edge"
    display_name_plural = "Edges"

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    # object_type_id: Mapped[int] = mapped_column(
    #    ForeignKey("uno.object_type.id", ondelete="CASCADE"),
    #    index=True,
    #    doc="The object type of the node.",
    # )
    start_node_label: Mapped[str_255] = mapped_column(
        ForeignKey("uno.node.label", ondelete="CASCADE"),
        index=True,
        doc="The object type of the start node.",
    )
    label: Mapped[str_255] = mapped_column(
        index=True,
        doc="The Graph label of the edge.",
    )
    destination_table_name: Mapped[str_255] = mapped_column(
        ForeignKey("uno.node.label", ondelete="CASCADE"),
        index=True,
        doc="The object type of the end node.",
    )
    accessor: Mapped[str] = mapped_column(
        doc="The relational accessor for the edge.",
    )


class Property(Base):
    __tablename__ = "property"
    __table_args__ = (
        {
            "schema": "uno",
            "comment": "A property of a node or an edge in a graph.",
        },
    )
    display_name = "Property"
    display_name_plural = "Properties"

    sql_emitters = []

    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        unique=True,
        index=True,
        doc="The id of the node.",
    )
    node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("uno.node.object_type_id", ondelete="CASCADE"),
        index=True,
        doc="The node associated with the property.",
    )
    edge_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("uno.edge.id", ondelete="CASCADE"),
        index=True,
        doc="The edge associated with the property.",
    )
    accessor: Mapped[str] = mapped_column(
        doc="The relational accessor for the property.",
    )
    name: Mapped[str_255] = mapped_column(
        index=True,
        doc="The Graph label of the Property.",
    )
    data_type: Mapped[str_26] = mapped_column(
        doc="The data type of the property.",
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
    display_name = "Path"
    display_name_plural = "Paths"
    # include_in_graph = False

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
'''


class Filter(Base):
    __tablename__ = "filter"
    __table_args__ = (
        UniqueConstraint(
            "table_name",
            "label",
            "destination_table_name",
            name="uq_table_name_label_destination_table_name",
        ),
        {
            "schema": "uno",
            "comment": "Used to enable user-defined filtering using the graph vertices and edges.",
        },
    )
    display_name = "Filter"
    display_name_plural = "Filters"

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
        index=True,
        doc="The table name of the filter.",
    )
    destination_table_name: Mapped[Optional[str_255]] = mapped_column(
        index=True,
        doc="The destination table name of the filter.",
    )
    label: Mapped[str_255] = mapped_column(
        index=True,
        doc="The GraphEdge or GraphProperty label of the filter.",
    )
    accessor: Mapped[str_255] = mapped_column(
        doc="The relational accessor for the filter.",
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
    """
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
    """


class FilterValue(Base, DBObjectPKMixin, BaseFieldMixin):
    __tablename__ = "filter_value"
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
            "object_value_id",
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
        },
    )
    display_name = "Filter Value"
    display_name_plural = "Filter Values"

    sql_emitters = [InsertObjectTypeRecordSQL]

    # Columns
    filter_id: Mapped[str_26] = mapped_column(
        ForeignKey("uno.filter.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
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
    display_name = "Query"
    display_name_plural = "Queries"
    # #include_in_graph = False

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
    display_name = "Query Filter Value"
    display_name_plural = "Query Filter Values"
    # include_in_graph = False

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
    display_name = "Query Subquery"
    display_name_plural = "Query Subqueries"
    # include_in_graph = False

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
