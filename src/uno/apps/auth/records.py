# SPDX-FileCopyrightText: 2024-present Richard Dahl <richard@dahl.us>
#
# SPDX-License-Identifier: MIT

from typing import Optional

from psycopg.sql import SQL

from sqlalchemy import (
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

from pydantic import BaseModel
from pydantic.fields import Field

from uno.record.record import UnoRecord, UnoTableDef, meta_data
from uno.record.rel_obj import UnoRelObj
from uno.record.enums import SQLOperation
from uno.record.mixins import GeneralRecordMixin
from uno.apps.meta.records import MetaRecord
from uno.apps.auth.record_mixins import UserMixin
from uno.apps.auth.sql_emitters import (
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
)
from uno.apps.auth.rls_sql_emitters import (
    #    RowLevelSecurity,
    UserRowLevelSecurity,
    #    TenantRowLevelSecurity,
)
from uno.apps.auth.enums import TenantType
from uno.apps.auth.rel_objs import user_rel_objs, group_rel_objs
from uno.config import settings


class UserRecord(UnoRecord, UserMixin):
    table_def = UnoTableDef(
        table_name="user",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
                nullable=True,
                index=True,
            ),
            Column(
                "email",
                VARCHAR(255),
                unique=True,
                index=True,
            ),
            Column(
                "handle",
                VARCHAR(255),
                unique=True,
                index=True,
            ),
            Column(
                "full_name",
                VARCHAR(255),
            ),
            Column(
                "is_superuser",
                BOOLEAN,
                server_default=text("false"),
                index=True,
            ),
            Column(
                "tenant_id",
                ForeignKey("tenant.id"),
                index=True,
                nullable=True,
            ),
            Column(
                "default_group_id",
                ForeignKey("group.id"),
                index=True,
                nullable=True,
            ),
        ],
    )

    # Class Variables
    sql_emitters = [UserRowLevelSecurity]
    related_object_defs = user_rel_objs


class GroupRecord(UnoRecord, GeneralRecordMixin):
    table_def = UnoTableDef(
        table_name="group",
        meta_data=meta_data,
        args=[
            Column(
                "id",
                VARCHAR(26),
                primary_key=True,
                nullable=True,
                index=True,
            ),
            Column(
                "tenant_id",
                ForeignKey("tenant.id"),
                nullable=False,
                index=True,
            ),
            Column(
                "name",
                VARCHAR(255),
                unique=True,
            ),
            UniqueConstraint("tenant_id", "name"),
        ],
    )

    # Class Variables
    sql_emitters = [ValidateGroupInsert, DefaultGroupTenant]
    related_objects = group_rel_objs


class RoleRecord(UnoRecord, GeneralRecordMixin):
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
    sql_emitters = []


class TenantRecord(UnoRecord, GeneralRecordMixin):
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


class PermissionRecord(UnoRecord):
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

    # Class Variables
    sql_emitters = []


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
