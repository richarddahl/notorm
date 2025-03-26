# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.table_sql_emitters import AlterGrants, InsertMetaType
from uno.db.sql.db_sql_emitters import (
    RecordUserAuditFunction,
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordUserAuditFunction,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
)
from uno.db.sql.sql_config import SQLConfig
from uno.pkgs.auth.rls_sql_emitters import UserRowLevelSecurity
from uno.db.sql.graph_sql_emitter import GraphSQLEmitter
from uno.pkgs.auth.bases import (
    user__group,
    user__role,
    role__permission,
    UserBase,
    GroupBase,
    RoleBase,
    TenantBase,
    PermissionBase,
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
    table = UserBase.__table__
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
    table = GroupBase.__table__
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


class RoleSQLConfig(SQLConfig):
    table = RoleBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        GraphSQLEmitter,
    ]


class TenantSQLConfig(SQLConfig):
    table = TenantBase.__table__
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
    table = PermissionBase.__table__
    sql_emitters = [
        AlterGrants,
        InsertMetaType,
        GraphSQLEmitter,
    ]
