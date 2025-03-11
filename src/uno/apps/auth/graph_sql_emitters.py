# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.graph.sql_emitters import EdgeConfig, GraphSQLEmitter


class CreatedByEdge(EdgeConfig):
    column_name: str = "created_by_id"
    label: str = "WAS_CREATED_BY"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    remote_node_label: str = "User"


class ModifiedByEdge(EdgeConfig):
    column_name: str = "modified_by_id"
    label: str = "WAS_MODIFIED_BY"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    remote_node_label: str = "User"


class DeletedByEdge(EdgeConfig):
    column_name: str = "deleted_by_id"
    label: str = "WAS_DELETED_BY"
    remote_table_name: str = "user"
    remote_column_name: str = "id"
    remote_node_label: str = "User"


class TenantEdge(EdgeConfig):
    column_name: str = "tenant_id"
    label: str = "IS_ASSIGNED_TO"
    remote_table_name: str = "tenant"
    remote_column_name: str = "id"
    remote_node_label: str = "Tenant"


class DefaultGroupEdge(EdgeConfig):
    column_name: str = "default_group_id"
    label: str = "HAS_DEFAULT_GROUP"
    remote_table_name: str = "group"
    remote_column_name: str = "id"
    remote_node_label: str = "Group"


class GroupEdge(EdgeConfig):
    column_name: str = "group_id"
    label: str = "IS_MEMBER_OF"
    remote_table_name: str = "group"
    remote_column_name: str = "id"
    remote_node_label: str = "Group"


class UserRole(EdgeConfig):
    column_name: str = "id"
    label: str = "HAS_ROLE"
    secondary_table_name: str = "user__group__role"
    secondary_column_name: str = "user_id"
    secondary_remote_column_name: str = "role_id"
    remote_table_name: str = "role"
    remote_column_name: str = "id"
    remote_node_label: str = "Role"


class UserGraph(GraphSQLEmitter):
    edge_configs = [
        CreatedByEdge,
        ModifiedByEdge,
        DeletedByEdge,
        TenantEdge,
        DefaultGroupEdge,
    ]


class GroupGraph(GraphSQLEmitter):
    edge_configs = [
        CreatedByEdge,
        ModifiedByEdge,
        DeletedByEdge,
        TenantEdge,
    ]


class TenantGraph(GraphSQLEmitter):
    edge_configs = [
        CreatedByEdge,
        ModifiedByEdge,
        DeletedByEdge,
    ]


class RoleGraph(GraphSQLEmitter):
    edge_configs = [
        CreatedByEdge,
        ModifiedByEdge,
        DeletedByEdge,
    ]
