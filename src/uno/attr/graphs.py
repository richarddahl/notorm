# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphEdgeDef


attribute_type_edge_defs = [
    GraphEdgeDef(
        name="HAS_ATTRIBUTE",
        destination_table_name="attribute",
        accessor="attributes",
    ),
    GraphEdgeDef(
        name="IS_VALUE_TYPE_FOR",
        destination_table_name="attribute_type",
        accessor="value_type_attribute_types",
    ),
    GraphEdgeDef(
        name="IS_DESCRIBED_BY",
        destination_table_name="attribute_type",
        accessor="described_attribute_types",
    ),
]

attachment_edge_defs = [
    GraphEdgeDef(
        name="IS_ATTACHMENT_FOR",
        destination_table_name="related_object",
        accessor="attachments",
    ),
]
