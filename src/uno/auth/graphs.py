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
        label="HAS_USER",
        start_node_label="Tenant",
        end_node_label="User",
        accessor="users",
    ),
    GraphEdge(
        label="HAS_GROUP",
        start_node_label="Tenant",
        end_node_label="Group",
        accessor="groups",
    ),
    GraphEdge(
        label="HAS_OBJECT",
        start_node_label="Tenant",
        end_node_label="DBObject",
        accessor="db_objects",
    ),
]


user_node = GraphNode(
    table_name="user",
    label="User",
)

user_edges = [
    GraphEdge(
        label="WORKS_FOR",
        start_node_label="User",
        end_node_label="Tenant",
        accessor="tenant",
    ),
    GraphEdge(
        label="HAS_DEFAULT_GROUP",
        start_node_label="User",
        end_node_label="Group",
        accessor="default_group",
    ),
    GraphEdge(
        label="IS_OWNED_BY",
        start_node_label="User",
        end_node_label="User",
        accessor="owner",
    ),
    GraphEdge(
        label="WAS_LAST_MODIFIED_BY",
        start_node_label="User",
        end_node_label="User",
        accessor="modified_by",
    ),
    GraphEdge(
        label="WAS_DELETED_BY",
        start_node_label="User",
        end_node_label="User",
        accessor="deleted_by",
    ),
]

role_node = GraphNode(
    table_name="role",
    label="Role",
)

role_edges = [
    GraphEdge(
        label="HAS_USER",
        start_node_label="Role",
        end_node_label="User",
        accessor="users",
    ),
    GraphEdge(
        label="HAS_GROUP",
        start_node_label="Role",
        end_node_label="Group",
        accessor="groups",
    ),
    GraphEdge(
        label="HAS_TENANT",
        start_node_label="Role",
        end_node_label="Tenant",
        accessor="tenants",
    ),
]

group_node = GraphNode(
    table_name="group",
    label="Group",
)

group_edges = [
    GraphEdge(
        label="HAS_USER",
        start_node_label="Group",
        end_node_label="User",
        accessor="users",
    ),
    GraphEdge(
        label="HAS_OBJECT",
        start_node_label="Group",
        end_node_label="DBObject",
        accessor="db_objects",
    ),
]
