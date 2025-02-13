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
        label="IS_CHILD_OF",
        start_node_label="AttributeType",
        end_node_label="AttributeType",
        accessor="parent",
    ),
    GraphEdge(
        label="HAS_CHILDREN",
        start_node_label="AttributeType",
        end_node_label="AttributeType",
        accessor="children",
    ),
    GraphEdge(
        label="DESCRIBES",
        start_node_label="AttributeType",
        end_node_label="ObjectType",
        accessor="describes",
    ),
    GraphEdge(
        label="HAS_VALUE_TYPE",
        start_node_label="AttributeType",
        end_node_label="ObjectType",
        accessor="values",
    ),
    # GraphNode(
    #    label="DETERMINES_APPLICABILITY",
    #    start_node_label="AttributeType",
    #    end_node_label="Query",
    #    accessor="determining_query",
    # ),
]

attribute_value_node = GraphNode(
    table_name="attribute_value",
    label="AttributeValue",
)


attribute_node = GraphNode(
    table_name="attribute",
    label="Attribute",
)
