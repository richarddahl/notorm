# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphEdgeDef


attribute_type_edge_defs = [
    GraphEdgeDef(
        name="IS_CHILD_OF",
        destination_table_name="attribute_type",
        accessor="parent",
    ),
    GraphEdgeDef(
        name="IS_PARENT_OF",
        destination_table_name="attribute_type",
        accessor="children",
    ),
    GraphEdgeDef(
        name="DESCRIBES",
        destination_table_name="object_type",
        accessor="describes",
    ),
    GraphEdgeDef(
        name="HAS_VALUE_TYPE",
        destination_table_name="object_type",
        accessor="values",
    ),
]
