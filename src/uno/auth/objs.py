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
    UnoForeignKey,
    UnoTableDef,
    UnoRelatedModel,
    meta_data,
)
from uno.db.mixins import (
    InsertMetaRecordMixin,
    RecordStatusMixin,
    RecordUserAuditMixin,
    GeneralMixin,
)
from uno.db.enums import SQLOperation
from uno.db.graph import Edge
from uno.db.sql.sql_emitter import SQLEmitter
from uno.meta.objs import MetaRecord, MetaType

# from uno.msg.tables import Message, MessageAddressedTo, MessageCopiedTo
from uno.auth.mixins import UserMixin
from uno.auth.sql_emitters import (
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
)

# from uno.auth.rls_sql_emitters import (
#    RowLevelSecurity,
#    UserRowLevelSecurity,
#    TenantRowLevelSecurity,
# )
from uno.auth.enums import TenantType
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)

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
            Column(
                "tenant_id",
                UnoForeignKey(
                    "tenant.id",
                    related_model=UnoRelatedModel(
                        local_table_name="user",
                        local_column_name="tenant_id",
                        remote_table_name="tenant",
                        remote_column_name="id",
                    ),
                    edge=Edge(
                        source="User",
                        destination="Tenant",
                        label="BELONGS_TO",
                    ),
                ),
                index=True,
            ),
            Column(
                "default_group_id",
                UnoForeignKey(
                    "group.id",
                    related_model=UnoRelatedModel(
                        local_table_name="user",
                        local_column_name="default_group_id",
                        remote_table_name="group",
                        remote_column_name="id",
                    ),
                    edge=Edge(
                        source="User",
                        destination="Group",
                        label="HAS_DEFAULT_GROUP",
                    ),
                ),
                index=True,
            ),
            CheckConstraint(
                """
                is_superuser = 'true'  OR
                is_superuser = 'false' AND
                default_group_id IS NOT NULL AND
                tenant_id IS NOT NULL AND
                created_by_id IS NOT NULL AND
                modified_by_id IS NOT NULL
             """,
                name="ck_user_is_superuser",
            ),
        ],
    )

    display_name = "User"
    display_name_plural = "Users"

    schema_defs = user_schema_defs

    exclude_from_properties = ["is_superuser"]
    graph_properties = []

    email: str
    handle: str
    full_name: str
    is_superuser: bool = False
    tenant_id: Optional[str] = None
    tenant: Optional["Tenant"] = None
    default_group_id: Optional[str] = None
    default_group: Optional["Group"] = None
    id: Optional[str] = None

    def __str__(self) -> str:
        return self.email


class Group(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="group",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column(
                "tenant_id",
                UnoForeignKey(
                    "tenant.id",
                    related_model=UnoRelatedModel(
                        local_table_name="group",
                        local_column_name="tenant_id",
                        remote_table_name="tenant",
                        remote_column_name="id",
                    ),
                    edge=Edge(
                        source="Group",
                        destination="Tenant",
                        label="BELONGS_TO",
                    ),
                ),
                index=True,
            ),
            Column("name", VARCHAR(255), unique=True),
            Index("ix_group_tenant_id_name", "tenant_id", "name"),
            UniqueConstraint("tenant_id", "name"),
        ],
    )
    display_name = "Group"
    display_name_plural = "Groups"

    sql_emitters = [
        ValidateGroupInsert,
        DefaultGroupTenant,
    ]
    schema_defs = group_schema_defs

    name: str
    tenant_id: Optional[str] = None
    tenant: Optional["Tenant"] = None
    id: Optional[str] = None

    roles: list["Role"] = []
    default_users: list["User"] = []

    """
    # Relationships
    edge_defs={"edge": "BELONGS_TO"},
    # group_role_users: Mapped[list[GroupRoleUser]] = relationship(
    #    doc="Users assigned to group roles",
    #    info={"edge": "IS_ASSIGNED_TO"},
    # )
    roles: Mapped[list[Role]] = relationship(
        secondary=GroupRole.__table__,
        doc="Roles assigned to the group",
        info={"edge": "IS_ASSIGNED"},
    )
    default_users: Mapped[list[User]] = relationship(
        viewonly=True,
        foreign_keys="User.default_group_id",
        doc="Users that belong to the group",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )
    """

    def __str__(self) -> str:
        return self.name


class Role(UnoObj, GeneralMixin):
    table_def = UnoTableDef(
        table_name="role",
        meta_data=meta_data,
        args=[
            Column("id", VARCHAR(26), primary_key=True, nullable=True),
            Column(
                "tenant_id",
                UnoForeignKey(
                    "tenant.id",
                    related_model=UnoRelatedModel(
                        local_table_name="role",
                        local_column_name="tenant_id",
                        remote_table_name="tenant",
                        remote_column_name="id",
                    ),
                    edge=Edge(
                        source="Role",
                        destination="Tenant",
                        label="BELONGS_TO",
                    ),
                ),
                index=True,
            ),
            Column("name", VARCHAR(255), unique=True),
            Column("description", VARCHAR),
            Index("ix_role_tenant_id_name", "tenant_id", "name"),
            UniqueConstraint("tenant_id", "name"),
        ],
    )
    display_name = "Role"
    display_name_plural = "Roles"
    schema_defs = role_schema_defs

    # BaseModel fields
    name: str
    tenant_id: Optional[str] = None
    tenant: Optional["Tenant"] = None
    description: Optional[str] = None
    id: Optional[str] = None

    # Relationships
    """
    permissions: Mapped[list[Permission]] = relationship(
        viewonly=True,
        secondary=RolePermission.__table__,
        doc="Permissions assigned to the role",
        info={"edge": "ALLOWS_PERMISSION"},
    )
    tenant: Mapped[Tenant] = relationship(
        viewonly=True,
        foreign_keys="Role.tenant_id",
        doc="Tenants that have this role",
        info={"edge": "BELONGS_TO"},
    )
    group_roles: Mapped[list["GroupRole"]] = relationship(
        doc="Groups that have this role",
        foreign_keys="GroupRole.role_id",
        info={"edge": "IS_ASSIGNED_TO"},
    )
    # users: Mapped[list[GroupRoleUser]] = relationship(
    #    doc="Users that have this role",
    #    info={"edge": "IS_ASSIGNED_TO"},
    # )
    """

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
    display_name = "Tenant"
    display_name_plural = "Tenants"

    sql_emitters = [InsertGroupForTenant]

    schema_defs = tenant_schema_defs
    edge_defs = {
        "users": {"source": "Tenant", "destination": "User", "label": "OWNS"},
        "groups": {"source": "Tenant", "destination": "Group", "label": "OWNS"},
        "roles": {"source": "Tenant", "destination": "Role", "label": "OWNS"},
    }

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

    sql_emitters = []

    # BaseModel fields
    id: int
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
