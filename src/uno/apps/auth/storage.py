# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from pydantic import BaseModel

from uno.record.storage import UnoStorage
from uno.apps.auth.sql.rls_sql_statements import (
    UserRowLevelSecurity,
)
from uno.apps.auth.sql.sql_statements import (
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
    UserRecordAuditFunction,
)
from uno.record.sql.table_sql_statements import (
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
    RecordStatusFunction,
    RecordUserAuditFunction,
    RecordVersionAudit,
    EnableHistoricalAudit,
)
from uno.config import settings


class UserStorage(UnoStorage):
    table_name: Optional[str] = "user"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        UserRowLevelSecurity,
        RecordStatusFunction,
        UserRecordAuditFunction,
    ]


class GroupStorage(UnoStorage):
    table_name: Optional[str] = "group"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordStatusFunction,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
    ]


class RoleStorage(UnoStorage):
    table_name: Optional[str] = "role"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordUserAuditFunction,
        RecordStatusFunction,
    ]


class TenantStorage(UnoStorage):
    table_name: Optional[str] = "tenant"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordUserAuditFunction,
        InsertGroupForTenant,
        RecordStatusFunction,
    ]


class PermissionStorage(UnoStorage):
    table_name: Optional[str] = "permission"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        RecordUserAuditFunction,
        RecordStatusFunction,
    ]
