# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.classes import SQLConfig

from uno.db.sql.tablesql import (
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
    RecordUserAuditFunction,
    RecordStatusFunction,
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordUserAuditFunction,
)
from uno.auth.rlssql import UserRowLevelSecurity
from uno.db.sql.graphsql import GraphSQLEmitter
from uno.auth.models import (
    user__group,
    user__role,
    role__permission,
    UserModel,
    GroupModel,
    ResponsibilityRoleModel,
    RoleModel,
    TenantModel,
    PermissionModel,
)


class UserGroupSQLConfig(SQLConfig):
    table = user__group
    sql_emitters = [
        AlterGrants,
        GraphSQLEmitter,
    ]


class UserRoleSQLConfig(SQLConfig):
    table = user__role
    sql_emitters = [
        AlterGrants,
        GraphSQLEmitter,
    ]


class RolePermisionSQLConfig(SQLConfig):
    table = role__permission
    sql_emitters = [
        AlterGrants,
        GraphSQLEmitter,
    ]


class UserSQLConfig(SQLConfig):
    table = UserModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        UserRowLevelSecurity,
        UserRecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class GroupSQLConfig(SQLConfig):
    table = GroupModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
        GraphSQLEmitter,
    ]


class ResponsibilityRoleSQLConfig(SQLConfig):
    table = ResponsibilityRoleModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class RoleSQLConfig(SQLConfig):
    table = RoleModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class TenantSQLConfig(SQLConfig):
    table = TenantModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        InsertGroupForTenant,
        GraphSQLEmitter,
    ]


class PermissionSQLConfig(SQLConfig):
    table = PermissionModel.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
