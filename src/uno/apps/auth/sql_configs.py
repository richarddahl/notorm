# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_config import SQLConfig

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
from uno.apps.auth.rls_sql_emitters import UserRowLevelSecurity
from uno.db.sql.graph_sql_emitters import NodeSQLEmitter
from uno.apps.auth.models import User, Group, Role, Tenant, Permission


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
