# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.graphs import GraphNode, GraphEdge

tenant_node = GraphNode(
    table_name="tenant",
    label="Tenant",
)

tenant_edges = [
    GraphEdge(
        table_name="tenant",
        label="EMPLOYS",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdge(
        table_name="tenant",
        label="OWNS",
        destination_table_name="group",
        accessor="groups",
    ),
    GraphEdge(
        table_name="tenant",
        label="OWNS",
        destination_table_name="db_object",
        accessor="db_objects",
    ),
    GraphEdge(
        table_name="tenant",
        label="IS_OWNED_BY",
        destination_table_name="user",
        accessor="owner",
    ),
    GraphEdge(
        table_name="tenant",
        label="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdge(
        table_name="tenant",
        label="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]


user_node = GraphNode(
    table_name="user",
    label="User",
)

user_edges = [
    GraphEdge(
        table_name="user",
        label="WORKS_FOR",
        destination_table_name="tenant",
        accessor="tenant",
    ),
    GraphEdge(
        table_name="user",
        label="HAS_DEFAULT",
        destination_table_name="group",
        accessor="default_group",
    ),
    GraphEdge(
        table_name="user",
        label="IS_OWNED_BY",
        destination_table_name="user",
        accessor="owner",
    ),
    GraphEdge(
        table_name="user",
        label="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdge(
        table_name="user",
        label="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]

role_node = GraphNode(
    table_name="role",
    label="Role",
)

role_edges = [
    GraphEdge(
        table_name="role",
        label="HAS_USER",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdge(
        table_name="role",
        label="HAS_GROUP",
        destination_table_name="group",
        accessor="groups",
    ),
    GraphEdge(
        table_name="role",
        label="HAS_TENANT",
        destination_table_name="tenant",
        accessor="tenants",
    ),
    GraphEdge(
        table_name="role",
        label="IS_OWNED_BY",
        destination_table_name="user",
        accessor="owner",
    ),
    GraphEdge(
        table_name="role",
        label="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdge(
        table_name="role",
        label="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]

group_node = GraphNode(
    table_name="group",
    label="Group",
)

group_edges = [
    GraphEdge(
        table_name="group",
        label="HAS_USER",
        destination_table_name="user",
        accessor="users",
    ),
    GraphEdge(
        table_name="group",
        label="HAS_OBJECT",
        destination_table_name="db_object",
        accessor="db_objects",
    ),
    GraphEdge(
        table_name="group",
        label="IS_OWNED_BY",
        destination_table_name="user",
        accessor="owner",
    ),
    GraphEdge(
        table_name="group",
        label="WAS_LAST_MODIFIED_BY",
        destination_table_name="user",
        accessor="modified_by",
    ),
    GraphEdge(
        table_name="group",
        label="WAS_DELETED_BY",
        destination_table_name="user",
        accessor="deleted_by",
    ),
]
