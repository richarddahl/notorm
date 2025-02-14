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
        label="HAS_OBJECT",
        start_node_label="ObjectType",
        end_node_label="DBObject",
        accessor="db_objects",
    ),
    GraphEdge(
        label="IS_DESCRIBED_BY",
        start_node_label="ObjectType",
        end_node_label="AttributeType",
        accessor="described_attribute_types",
    ),
    GraphEdge(
        label="IS_VALUE_TYPE_FOR",
        start_node_label="ObjectType",
        end_node_label="AttributeType",
        accessor="value_type_attribute_types",
    ),
]


db_object_node = GraphNode(
    table_name="db_object",
    label="DBObject",
)

db_object_edges = [
    GraphEdge(
        label="HAS_ATTRIBUTE",
        start_node_label="DBObject",
        end_node_label="Attribute",
        accessor="attributes",
        secondary_table_name="attribute__dbobject",
    ),
    GraphEdge(
        label="HAS_ATTACHMENT",
        start_node_label="DBObject",
        end_node_label="Attachment",
        accessor="attachments",
        secondary_table_name="attachment__dbobject",
    ),
]

attachment_node = GraphNode(
    table_name="attachment",
    label="Attachment",
)

attachment_edges = [
    GraphEdge(
        label="IS_ATTACHMENT_FOR",
        start_node_label="Attachment",
        end_node_label="DBObject",
        accessor="attachments",
    ),
]
