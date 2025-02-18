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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy.dialects.postgresql import ENUM, ARRAY

from uno.db.tables import (
    Base,
    BaseMetaMixin,
    RecordUserAuditMixin,
    RelatedObject,
    ObjectType,
    str_26,
    str_255,
)
from uno.db.enums import SQLOperation
from uno.db.sql_emitters import (
    RecordVersionAuditSQL,
    InsertRelatedObjectFunctionSQL,
    InsertObjectTypeRecordSQL,
)
from uno.auth.sql_emitters import (
    InsertUserRelatedObjectFunctionSQL,
    ValidateGroupInsert,
    InsertGroupForTenant,
    DefaultGroupTenant,
)
from uno.auth.rls_sql_emitters import (
    RLSSQL,
    UserRLSSQL,
    TenantRLSSQL,
)
from uno.auth.enums import TenantType
from uno.auth.schemas import (
    user_schema_defs,
    tenant_schema_defs,
    group_schema_defs,
    role_schema_defs,
)

from uno.config import settings

"""
class GroupRole(Base):
    __tablename__ = "group_role"
    __table_args__ = (
        {
            "comment": "Assigned by admin users to assign roles to groups.",
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Group Permission"
    display_name_plural = "Group Permissions"

    sql_emitters = []
    include_in_graph = False

    # Columns
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.group.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.role.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
"""


class UserGroupRole(Base):
    __tablename__ = "user_group_role"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "User Group Role"
    display_name_plural = "User Group Roles"

    sql_emitters = []

    include_in_graph = False

    # Columns
    user_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        primary_key=True,
    )
    group_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.group.id", ondelete="CASCADE"),
        primary_key=True,
    )
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.role.id", ondelete="CASCADE"),
        primary_key=True,
    )


class Tenant(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "tenant"
    __table_args__ = (
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Application end-user tenants",
        },
    )
    display_name = "Tenant"
    display_name_plural = "Tenants"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
        InsertGroupForTenant,
    ]

    schema_defs = tenant_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    name: Mapped[str_255] = mapped_column(unique=True, doc="Tenant name")
    tenant_type: Mapped[TenantType] = mapped_column(
        ENUM(TenantType, name="tenanttype", create_type=True, schema="uno"),
        server_default=TenantType.INDIVIDUAL.name,
        doc="Tenant type",
    )

    # Relationships
    users: Mapped[list["User"]] = relationship(
        back_populates="tenant",
        foreign_keys="User.tenant_id",
        doc="Users that belong to the tenant",
        info={"edge": "BELONGS_TO"},
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="tenant",
        foreign_keys="Group.tenant_id",
        doc="Groups that belong to the tenant",
        info={"edge": "BELONGS_TO"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="tenant",
        foreign_keys="Role.tenant_id",
        doc="Roles that belong to the tenant",
        info={"edge": "BELONGS_TO"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "tenant",
        "inherit_condition": id == RelatedObject.id,
    }

    def __str__(self) -> str:
        return self.name


class User(RelatedObject, BaseMetaMixin):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint(
            SQL(
                """
                (is_superuser = 'false' AND default_group_id IS NOT NULL) OR 
                (is_superuser = 'true' AND default_group_id IS NULL) AND
            """
            ).as_string(),
            name="ck_user_is_superuser",
        ),
        {
            "schema": settings.DB_SCHEMA,
            "comment": "Application users",
        },
    )
    display_name = "User"
    display_name_plural = "Users"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertUserRelatedObjectFunctionSQL,
        RecordVersionAuditSQL,
    ]
    schema_defs = user_schema_defs

    exclude_from_properties = ["is_superuser"]
    graph_properties = []

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    email: Mapped[str_255] = mapped_column(
        unique=True,
        index=True,
        doc="Email address, used as login ID",
    )
    handle: Mapped[str_255] = mapped_column(
        unique=True, index=True, doc="User's displayed name and alternate login ID"
    )
    full_name: Mapped[str_255] = mapped_column(doc="User's full name")
    tenant_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
        index=True,
        doc="Tenant to which the user belongs.",
    )
    default_group_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.group.id", ondelete="SET NULL"),
        index=True,
        doc="Default group for the user",
    )
    is_superuser: Mapped[bool] = mapped_column(
        server_default=text("false"),
        index=True,
        doc="Superuser status",
    )
    created_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    modified_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    deleted_by_id: Mapped[Optional[str_26]] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.user.id", ondelete="CASCADE"),
        index=True,
    )
    # Relationships
    tenant: Mapped[Optional[Tenant]] = relationship(
        back_populates="users",
        foreign_keys=[tenant_id],
        doc="Tenant the user belongs to",
        info={"edge": "IS_OWNED_BY"},
    )
    groups: Mapped[list["Group"]] = relationship(
        back_populates="users",
        secondary=UserGroupRole.__table__,
        doc="Groups of which the user is a member.",
        info={"edge": "IS_MEMBER_OF"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="users",
        secondary=UserGroupRole.__table__,
        doc="Roles assigned to the user",
        info={"edge": "IS_ASSIGNED"},
    )
    default_group: Mapped[Optional["Group"]] = relationship(
        back_populates="default_users",
        foreign_keys=[default_group_id],
        doc="Default group for the user.",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )
    created_by: Mapped[Optional["User"]] = relationship(
        back_populates="users_created",
        foreign_keys="User.created_by_id",
        doc="User who created this user",
        info={"edge": "CREATED"},
    )
    users_created: Mapped[Optional["User"]] = relationship(
        back_populates="created_by",
        foreign_keys="User.created_by_id",
        remote_side="User.id",
        doc="Users created by this user",
        info={"edge": "CREATED"},
    )

    modified_by: Mapped[Optional["User"]] = relationship(
        back_populates="users_modified",
        foreign_keys="User.modified_by_id",
        doc="User who last modified this user",
        info={"edge": "MODIFIED"},
    )
    users_modified: Mapped[Optional["User"]] = relationship(
        back_populates="modified_by",
        foreign_keys="User.modified_by_id",
        remote_side="User.id",
        doc="Users modified by this user",
        info={"edge": "MODIFIED"},
    )
    deleted_by: Mapped[Optional["User"]] = relationship(
        back_populates="users_deleted",
        foreign_keys="User.deleted_by_id",
        doc="User who deleted this user",
        info={"edge": "DELETED"},
    )
    users_deleted: Mapped[Optional["User"]] = relationship(
        back_populates="deleted_by",
        foreign_keys="User.deleted_by_id",
        remote_side="User.id",
        doc="Users deleted by this user",
        info={"edge": "DELETED"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "user",
        "inherit_condition": id == RelatedObject.id,
    }

    def __str__(self) -> str:
        return self.email


class RolePermission(Base):
    __tablename__ = "role__permission"
    __table_args__ = (
        {
            "comment": """
                Assigned by tenant_admin users to assign roles for groups to users based on organization requirements.
            """,
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Role Permission"
    display_name_plural = "Role Permissions"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        InsertRelatedObjectFunctionSQL,
    ]

    include_in_graph = False

    # Columns
    role_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.role.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Role ID",
    )
    permission_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.permission.id", ondelete="CASCADE"),
        primary_key=True,
        doc="Permission ID",
    )


class Permission(Base):
    __tablename__ = "permission"
    __table_args__ = (
        UniqueConstraint(
            "object_type_name",
            "operation",
            name="uq_objecttype_operation",
        ),
        {
            "comment": """
                Permissions for each table.
                Deleted automatically by the DB via the FK Constraints
                ondelete when a object_type is deleted.
            """,
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Permission"
    display_name_plural = "Permissions"

    sql_emitters = []
    include_in_graph = False

    # Columns
    id: Mapped[int] = mapped_column(
        Identity(),
        primary_key=True,
        doc="The id of the node.",
    )
    object_type_name: Mapped[int] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.objecttype.name", ondelete="CASCADE"),
        primary_key=True,
        doc="Table to which the permission provides access.",
    )
    operation: Mapped[SQLOperation] = mapped_column(
        ENUM(
            SQLOperation,
            name="sqloperation",
            create_type=True,
            schema="uno",
        ),
        primary_key=True,
        doc="Database operation that is permissible.",
    )

    # Relationships
    object_type: Mapped[ObjectType] = relationship(
        back_populates="permissions",
        doc="Table the permission is for",
        info={"edge": "ALLOWS_ACCESS_TO"},
    )
    roles: Mapped[list["Role"]] = relationship(
        back_populates="permissions",
        secondary=RolePermission.__table__,
        doc="Roles that have this permission",
        info={"edge": "ALLOWS_ACCESS_VIA"},
    )

    def __str__(self) -> str:
        return f"{self.object_type.name} - {self.actions}"


class Role(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "role"
    __table_args__ = (
        Index("ix_role_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": """
                Roles, created by end user group admins, enable assignment of group_permissions
                by functionality, department, etc... to users.
            """,
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Role"
    display_name_plural = "Roles"

    sql_emitters = [InsertObjectTypeRecordSQL]
    schema_defs = role_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
        index=True,
        doc="Tenant the role belongs to",
    )
    name: Mapped[str_255] = mapped_column(doc="Role name")
    description: Mapped[str] = mapped_column(doc="Role description")

    # Relationships
    permissions: Mapped[list[Permission]] = relationship(
        back_populates="roles",
        secondary=RolePermission.__table__,
        doc="Permissions assigned to the role",
        info={"edge": "ALLOWS_PERMISSION"},
    )
    tenant: Mapped[Tenant] = relationship(
        back_populates="roles",
        foreign_keys="Role.tenant_id",
        doc="Tenants that have this role",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    users: Mapped[list[User]] = relationship(
        back_populates="roles",
        secondary=UserGroupRole.__table__,
        doc="Users that have this role",
        info={"edge": "IS_ASSIGNED_TO"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "role",
        "inherit_condition": id == RelatedObject.id,
    }

    def __str__(self) -> str:
        return self.name


class Group(RelatedObject, RecordUserAuditMixin):
    __tablename__ = "group"
    __table_args__ = (
        Index("ix_group_tenant_id_name", "tenant_id", "name"),
        UniqueConstraint("tenant_id", "name"),
        {
            "comment": "Application end-user groups",
            "schema": settings.DB_SCHEMA,
        },
    )
    display_name = "Group"
    display_name_plural = "Groups"

    sql_emitters = [
        InsertObjectTypeRecordSQL,
        ValidateGroupInsert,
        DefaultGroupTenant,
        InsertRelatedObjectFunctionSQL,
    ]
    schema_defs = group_schema_defs

    # Columns
    id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.relatedobject.id"), primary_key=True
    )
    tenant_id: Mapped[str_26] = mapped_column(
        ForeignKey(f"{settings.DB_SCHEMA}.tenant.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str_255] = mapped_column(doc="Group name")

    # Relationships
    tenant: Mapped[Tenant] = relationship(
        back_populates="groups",
        foreign_keys="Group.tenant_id",
        doc="Tenant the group belongs to",
        info={"edge": "BELONGS_TO_TENANT"},
    )
    users: Mapped[list[User]] = relationship(
        back_populates="groups",
        secondary=UserGroupRole.__table__,
        doc="Users that belong to the group",
        info={"edge": "IS_MEMBER_OF"},
    )
    default_users: Mapped[list[User]] = relationship(
        back_populates="default_group",
        foreign_keys="User.default_group_id",
        doc="Users that belong to the group",
        info={"edge": "HAS_DEFAULT_GROUP"},
    )

    __mapper_args__ = {
        "polymorphic_identity": "group",
        "inherit_condition": id == RelatedObject.id,
    }

    def __str__(self) -> str:
        return self.name
