# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from psycopg.sql import SQL

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    UniqueConstraint,
    Identity,
    text,
    Table,
    Column,
)
from sqlalchemy.dialects.postgresql import (
    ENUM,
    BOOLEAN,
    VARCHAR,
    BIGINT,
)

from uno.db.obj import (
    UnoObj,
    UnoTableDef,
    meta_data,
)
from uno.db.mixins import GeneralMixin
from uno.db.enums import SQLOperation
from uno.meta.objs import MetaRecord

# from uno.msg.tables import Message, MessageAddressedTo, MessageCopiedTo
from uno.auth.mixins import UserMixin
from uno.auth.sql_emitters import (
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
)

from uno.auth.rls_sql_emitters import (
    #    RowLevelSecurity,
    UserRowLevelSecurity,
    #    TenantRowLevelSecurity,
)
from uno.auth.enums import TenantType
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)
from uno.auth.rel_objs import user_rel_objs, group_rel_objs

from uno.config import settings


class User(UnoObj, UserMixin):
    table_def = UnoTableDef(
        table_name="user",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column("email", VARCHAR(255), unique=True, index=True),
            Column("handle", VARCHAR(255), unique=True, index=True),
            Column("full_name", VARCHAR(255)),
            Column("is_superuser", BOOLEAN, server_default=text("false"), index=True),
            Column("tenant_id", ForeignKey("tenant.id"), index=True),
            Column("default_group_id", ForeignKey("group.id"), index=True),
        ],
    )

    # Class Variables
    sql_emitters = [UserRowLevelSecurity]
    schema_defs = user_schema_defs
    exclude_from_properties = ["is_superuser"]
    related_objects = user_rel_objs

    # BaseModel Fields
    email: str
    handle: str
    full_name: str
    is_superuser: bool = False
    tenant_id: Optional[str] = None
    tenant: Optional["Tenant"] = None
    default_group_id: Optional[str] = None
    default_group: Optional["Group"] = None
    meta_record: Optional[MetaRecord] = None
    groups: Optional[list["Group"]] = None
    roles: Optional[list["Role"]] = None
    created_objects: Optional[list[MetaRecord]] = None
    modified_objects: Optional[list[MetaRecord]] = None
    deleted_objects: Optional[list[MetaRecord]] = None
    id: Optional[str] = None

    def __str__(self) -> str:
        return self.handle


class Group(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="group",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column("tenant_id", ForeignKey("tenant.id"), index=True),
            Column("name", VARCHAR(255), unique=True),
            Index("ix_group_tenant_id_name", "tenant_id", "name"),
            UniqueConstraint("tenant_id", "name"),
        ],
    )

    # Class Variables
    sql_emitters = [ValidateGroupInsert, DefaultGroupTenant]
    schema_defs = group_schema_defs
    related_objects = group_rel_objs

    # BaseModel Fields
    name: str
    tenant_id: str = None
    tenant: Optional["Tenant"] = None
    roles: list["Role"] = []
    default_users: list[User] = []
    members: list[User] = []
    id: Optional[str] = None

    def __str__(self) -> str:
        return self.name


class Role(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="role",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column("tenant_id", ForeignKey("tenant.id"), index=True),
            Column("name", VARCHAR(255), unique=True),
            Column("description", VARCHAR),
            Index("ix_role_tenant_id_name", "tenant_id", "name"),
            UniqueConstraint("tenant_id", "name"),
        ],
    )
    schema_defs = role_schema_defs

    # BaseModel fields
    name: str
    tenant_id: Optional[str] = None
    tenant: Optional["Tenant"] = None
    description: Optional[str] = None
    id: Optional[str] = None

    def __str__(self) -> str:
        return self.name


class Tenant(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="tenant",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column("name", VARCHAR(255), unique=True),
            Column(
                "tenant_type",
                ENUM(
                    TenantType,
                    name="tenanttype",
                    create_type=True,
                    schema=settings.DB_SCHEMA,
                ),
                server_default=TenantType.INDIVIDUAL.name,
                nullable=False,
            ),
        ],
    )

    # Class Variables

    sql_emitters = [InsertGroupForTenant]
    schema_defs = tenant_schema_defs

    # BaseModel fields
    name: str
    tenant_type: TenantType
    id: Optional[str] = None

    users: list["User"] = []
    groups: list["Group"] = []
    roles: list["Role"] = []

    def __str__(self) -> str:
        return self.name


class Permission(UnoObj):
    table_def = UnoTableDef(
        table_name="permission",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                BIGINT,
                Identity(start=1, cycle=True),
                primary_key=True,
                unique=True,
            ),
            Column(
                "meta_type_id",
                ForeignKey("meta_type.id"),
                primary_key=True,
            ),
            Column(
                "operation",
                ENUM(
                    SQLOperation,
                    name="sqloperation",
                    create_type=True,
                ),
                primary_key=True,
            ),
            UniqueConstraint(
                "meta_type_id", "operation", name="uq_meta_type_operation"
            ),
        ],
    )
    display_name = "Permission"
    display_name_plural = "Permissions"
    include_in_api_docs = False

    # Class Variables
    sql_emitters = []

    # BaseModel Fields
    id: Optional[int]
    meta_type_id: str
    operation: SQLOperation

    def __str__(self) -> str:
        return f"{self.meta_type.name}:  {self.operation}"


Table(
    "user__group__role",
    meta_data,
    Column("user_id", VARCHAR(26), ForeignKey("user.id"), primary_key=True),
    Column("group_id", VARCHAR(26), ForeignKey("group.id"), primary_key=True),
    Column("role_id", VARCHAR(26), ForeignKey("role.id"), primary_key=True),
)


Table(
    "role__permission",
    meta_data,
    Column("role_id", VARCHAR(26), ForeignKey("uno.role.id"), primary_key=True),
    Column("permission_id", BIGINT, ForeignKey("uno.permission.id"), primary_key=True),
)
