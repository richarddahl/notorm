# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphNode, GraphEdge


object_type_node = GraphNode(
    table_name="object_type",
    label="ObjectType",
)

object_type_edges = [
    GraphEdge(
        table_name="object_type",
        label="HAS_OBJECT",
        destination_table_name="db_object",
        accessor="db_objects",
    ),
    GraphEdge(
        table_name="object_type",
        label="IS_DESCRIBED_BY",
        destination_table_name="attribute_type",
        accessor="described_attribute_types",
    ),
    GraphEdge(
        table_name="object_type",
        label="IS_VALUE_TYPE_FOR",
        destination_table_name="attribute_type",
        accessor="value_type_attribute_types",
    ),
]


db_object_node = GraphNode(
    table_name="db_object",
    label="DBObject",
)

db_object_edges = [
    GraphEdge(
        table_name="db_object",
        label="HAS_ATTRIBUTE",
        destination_table_name="attribute",
        accessor="attributes",
        secondary_table_name="uno.attribute__object_value",
    ),
    GraphEdge(
        table_name="db_object",
        label="HAS_ATTACHMENT",
        destination_table_name="attachment",
        accessor="attachments",
        secondary_table_name="uno.attachment__db_object",
    ),
]

attachment_node = GraphNode(
    table_name="attachment",
    label="Attachment",
)

attachment_edges = [
    GraphEdge(
        table_name="attachment",
        label="IS_ATTACHMENT_FOR",
        destination_table_name="db_object",
        accessor="attachments",
    ),
]
