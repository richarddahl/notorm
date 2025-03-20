# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.table_sql_emitters import (
    AlterGrants,
    InsertMetaType,
)
from uno.db.sql.db_sql_emitters import (
    RecordUserAuditFunction,
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sql_config import SQLConfig, TableSQLConfig
from uno.db.sql.graph_sql_emitters import TableGraphSQLEmitter
from uno.apps.auth.rls_sql_emitters import UserRowLevelSecurity
from uno.db.sql.graph_sql_emitters import NodeSQLEmitter
from uno.apps.auth.models import User, Group, Role, Tenant, Permission


class UserGroupSQLConfig(TableSQLConfig):
    table_name = "user__group"
    sql_emitters = [
        TableGraphSQLEmitter(
            local_node_label="User",
            column_name="user_id",
            label="IS_MEMBER_OF",
            remote_table_name="group",
            remote_column_name="group_id",
            remote_node_label="Group",
        ),
        TableGraphSQLEmitter(
            local_node_label="Group",
            column_name="group_id",
            label="GRANTS_ACCESS_TO",
            remote_table_name="user",
            remote_column_name="user_id",
            remote_node_label="User",
        ),
    ]


class UserRoleSQLConfig(TableSQLConfig):
    table_name = "user__role"
    sql_emitters = [
        TableGraphSQLEmitter(
            local_node_label="User",
            column_name="user_id",
            label="HAS_ROLE",
            remote_table_name="role",
            remote_column_name="role_id",
            remote_node_label="Role",
        ),
        TableGraphSQLEmitter(
            local_node_label="Role",
            column_name="role_id",
            label="GRANTS_ACCESS_TO",
            remote_table_name="user",
            remote_column_name="user_id",
            remote_node_label="User",
        ),
    ]


class RolePermisionSQLConfig(TableSQLConfig):
    table_name = "role__permission"
    sql_emitters = [
        TableGraphSQLEmitter(
            local_node_label="Role",
            column_name="role_id",
            label="HAS_PERMISSIONS",
            remote_table_name="permission",
            remote_column_name="permission_id",
            remote_node_label="Permission",
        ),
        TableGraphSQLEmitter(
            local_node_label="Permission",
            column_name="permission_id",
            label="HAS_PERMISSIONS_FROM",
            remote_table_name="role",
            remote_column_name="role_id",
            remote_node_label="Role",
        ),
    ]


class UserSQLConfig(SQLConfig):
    table_name = "user"
    model = User
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        UserRowLevelSecurity,
        UserRecordUserAuditFunction,
        NodeSQLEmitter,
    ]


class GroupSQLConfig(SQLConfig):
    table_name = "group"
    model = Group
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
        NodeSQLEmitter,
    ]


class RoleSQLConfig(SQLConfig):
    table_name = "role"
    model = Role
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        NodeSQLEmitter,
    ]


class TenantSQLConfig(SQLConfig):
    table_name = "tenant"
    model = Tenant
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        InsertGroupForTenant,
        NodeSQLEmitter,
    ]


class PermissionSQLConfig(SQLConfig):
    table_name = "permission"
    model = Permission
    sql_emitters = [AlterGrants]
