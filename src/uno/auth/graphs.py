# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphEdgeDef

tenant_edge_defs = [
    GraphEdgeDef(
        name="EMPLOYS",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdgeDef(
        name="OWNS",
        destination_table_name="group",
        accessor="groups",
    ),
    GraphEdgeDef(
        name="OWNS",
        destination_table_name="relatedobject",
        accessor="relatedobjects",
    ),
    GraphEdgeDef(
        name="IS_OWNED_BY",
        destination_table_name="user",
        accessor="created_by",
    ),
    GraphEdgeDef(
        name="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdgeDef(
        name="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]


user_edge_defs = [
    GraphEdgeDef(
        name="WORKS_FOR",
        destination_table_name="tenant",
        accessor="tenant",
    ),
    GraphEdgeDef(
        name="HAS_DEFAULT",
        destination_table_name="group",
        accessor="default_group",
    ),
    GraphEdgeDef(
        name="IS_OWNED_BY",
        destination_table_name="user",
        accessor="created_by",
    ),
    GraphEdgeDef(
        name="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdgeDef(
        name="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]


role_edge_defs = [
    GraphEdgeDef(
        name="HAS_USER",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdgeDef(
        name="HAS_GROUP",
        destination_table_name="group",
        accessor="groups",
    ),
    GraphEdgeDef(
        name="HAS_TENANT",
        destination_table_name="tenant",
        accessor="tenants",
    ),
    GraphEdgeDef(
        name="IS_OWNED_BY",
        destination_table_name="user",
        accessor="created_by",
    ),
    GraphEdgeDef(
        name="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdgeDef(
        name="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]


group_edge_defs = [
    GraphEdgeDef(
        name="HAS_USER",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdgeDef(
        name="HAS_OBJECT",
        destination_table_name="relatedobject",
        accessor="relatedobjects",
    ),
    GraphEdgeDef(
        name="IS_OWNED_BY",
        destination_table_name="user",
        accessor="created_by",
    ),
    GraphEdgeDef(
        name="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdgeDef(
        name="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]
