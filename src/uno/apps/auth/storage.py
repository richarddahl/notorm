# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from pydantic import BaseModel

from uno.storage.storage import UnoStorage
from uno.apps.auth.rls_sql_emitters import (
    UserRowLevelSecurity,
)
from uno.apps.auth.sql_emitters import (
    ValidateGroupInsert,
    DefaultGroupTenant,
    InsertGroupForTenant,
)
from uno.storage.sql.table_sql_emitters import (
    AlterGrants,
    InsertMetaType,
    InsertMetaRecordTrigger,
)
from uno.config import settings


class UserStorage(UnoStorage):
    table_name: Optional[str] = "user"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        UserRowLevelSecurity,
    ]


class GroupStorage(UnoStorage):
    table_name: Optional[str] = "group"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        ValidateGroupInsert,
        DefaultGroupTenant,
    ]


class RoleStorage(UnoStorage):
    table_name: Optional[str] = "role"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
    ]


class TenantStorage(UnoStorage):
    table_name: Optional[str] = "tenant"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
        InsertGroupForTenant,
    ]


class PermissionStorage(UnoStorage):
    table_name: Optional[str] = "permission"
    sql_emitters: list[BaseModel] = [
        AlterGrants,
        InsertMetaType,
        InsertMetaRecordTrigger,
    ]
