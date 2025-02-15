# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphNode, GraphEdge


attribute_type_node = GraphNode(
    table_name="attribute_type",
    label="AttributeType",
)

attribute_type_edges = [
    GraphEdge(
        table_name="attribute_type",
        label="IS_CHILD_OF",
        destination_table_name="attribute_type",
        accessor="parent",
    ),
    GraphEdge(
        table_name="attribute_type",
        label="IS_PARENT_OF",
        destination_table_name="attribute_type",
        accessor="children",
    ),
    GraphEdge(
        table_name="attribute_type",
        label="DESCRIBES",
        destination_table_name="object_type",
        accessor="describes",
    ),
    GraphEdge(
        table_name="attribute_type",
        label="HAS_VALUE_TYPE",
        destination_table_name="object_type",
        accessor="values",
    ),
]

attribute_value_node = GraphNode(
    table_name="attribute_value",
    label="AttributeValue",
)


attribute_node = GraphNode(
    table_name="attribute",
    label="Attribute",
)
