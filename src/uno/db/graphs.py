# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphEdgeDef


object_type_edge_defs = [
    GraphEdgeDef(
        name="HAS_OBJECT",
        destination_table_name="related_object",
        accessor="related_objects",
    ),
    GraphEdgeDef(
        name="IS_DESCRIBED_BY",
        destination_table_name="attribute_type",
        accessor="described_attribute_types",
    ),
    GraphEdgeDef(
        name="IS_VALUE_TYPE_FOR",
        destination_table_name="attribute_type",
        accessor="value_type_attribute_types",
    ),
]


related_object_edge_defs = [
    GraphEdgeDef(
        name="HAS_ATTRIBUTE",
        destination_table_name="attribute",
        accessor="attributes",
        secondary_table_name="uno.attribute__object_value",
    ),
    GraphEdgeDef(
        name="HAS_ATTACHMENT",
        destination_table_name="attachment",
        accessor="attachments",
        secondary_table_name="uno.attachment__related_object",
    ),
]
