# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_emitter import UnoSQL
from uno.apps.auth.rls_sql_emitters import (
    UserRowLevelSecurity,
)
from uno.apps.auth.sql_emitters import (
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordUserAuditFunction,
)
from uno.db.sql.table_sql_emitters import (
    AlterGrants,
    GeneralSqlEmitter,
    RecordUserAuditFunction,
)
from uno.apps.auth.graph_sql_emitters import (
    UserGraph,
    GroupGraph,
    TenantGraph,
    RoleGraph,
)


class UserSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        UserRowLevelSecurity,
        UserRecordUserAuditFunction,
        UserGraph,
        # UserRole,
    ]
    table_name = "user"


class GroupSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
        GroupGraph,
    ]
    table_name = "group"


class RoleSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        RoleGraph,
    ]
    table_name = "role"


class TenantSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        InsertGroupForTenant,
        TenantGraph,
    ]
    table_name = "tenant"


class PermissionSQL(UnoSQL):
    sql_emitters = [AlterGrants]
    table_name = "permission"
