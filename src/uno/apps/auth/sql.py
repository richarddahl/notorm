# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from uno.db.sql.sql_emitter import UnoSQL
from uno.apps.auth.sql.rls_sql_statements import (
    UserRowLevelSecurity,
)
from uno.apps.auth.sql.sql_statements import (
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


class UserSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        UserRowLevelSecurity,
        UserRecordUserAuditFunction,
    ]
    table_name = "user"


class GroupSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
    ]
    table_name = "group"


class RoleSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
    ]
    table_name = "role"


class TenantSQL(UnoSQL):
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        InsertGroupForTenant,
    ]
    table_name = "tenant"


class PermissionSQL(UnoSQL):
    sql_emitters = [AlterGrants]
    table_name = "permission"
