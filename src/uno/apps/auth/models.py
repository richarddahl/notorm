# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional
from pydantic import EmailStr

from uno.db.enums import SQLOperation
from uno.model.schema import UnoSchemaConfig
from uno.model.model import UnoModel, GeneralModelMixin
from uno.apps.auth.enums import TenantType
from uno.apps.auth.mixins import RecordAuditMixin
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
from uno.config import settings


class User(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    table_name = "user"
    schema_configs = {
        "summary_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "handle",
            ],
        ),
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
                "default_group",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "email",
                "handle",
                "full_name",
                "tenant_id",
                "default_group_id",
                "is_superuser",
            ],
        ),
    }
    sql_emitters = [
        GeneralSqlEmitter,
        UserRowLevelSecurity,
        UserRecordUserAuditFunction,
        UserGraph,
        # UserRole,
    ]

    email: EmailStr
    handle: str
    full_name: str
    tenant: Optional["Tenant"] = None
    tenant_id: Optional[str] = None
    default_group: Optional["Group"] = None
    default_group_id: Optional[str] = None
    is_superuser: bool = False

    # roles: Optional[list["Role"]] = None
    # created_objects: Optional[list[MetaBase]] = None
    # modified_objects: Optional[list[MetaBase]] = None
    # deleted_objects: Optional[list[MetaBase]] = None

    def __str__(self) -> str:
        return self.handle


class Group(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    table_name = "group"

    schema_configs = {
        "summary_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "name",
            ],
        ),
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_id",
            ],
        ),
    }
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        ValidateGroupInsert,
        DefaultGroupTenant,
        GroupGraph,
    ]

    # Fields
    id: Optional[str]
    name: str
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    # roles: list["Role"] = []
    # default_users: list[User] = []
    # members: list[User] = []

    def __str__(self) -> str:
        return self.name


class Role(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    table_name = "role"

    schema_configs = {
        "summary_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "name",
            ],
        ),
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
                "tenant",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
            ],
        ),
    }
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        RoleGraph,
    ]

    id: Optional[str]
    name: str
    description: Optional[str]
    tenant_id: Optional[str]
    tenant: Optional["Tenant"]

    def __str__(self) -> str:
        return self.name


class Tenant(UnoModel, GeneralModelMixin, RecordAuditMixin):
    # Class variables
    table_name = "tenant"

    schema_configs = {
        "summary_schema": UnoSchemaConfig(
            include_fields=[
                "id",
                "name",
            ],
        ),
        "view_schema": UnoSchemaConfig(
            exclude_fields=[
                "created_by",
                "modified_by",
                "deleted_by",
            ],
        ),
        "edit_schema": UnoSchemaConfig(
            include_fields=[
                "name",
                "tenant_type",
            ],
        ),
    }
    sql_emitters = [
        GeneralSqlEmitter,
        RecordUserAuditFunction,
        InsertGroupForTenant,
        TenantGraph,
    ]

    id: Optional[str]
    name: str
    tenant_type: TenantType

    # users: list["User"] = []
    # groups: list["Group"] = []
    # roles: list["Role"] = []

    def __str__(self) -> str:
        return self.name


class Permission(UnoModel):
    # Class variables
    table_name = "permission"
    sql_emitters = [AlterGrants]

    id: Optional[int]
    meta_type_id: str
    operation: SQLOperation

    def __str__(self) -> str:
        return f"{self.meta_type.name}:  {self.operation}"
